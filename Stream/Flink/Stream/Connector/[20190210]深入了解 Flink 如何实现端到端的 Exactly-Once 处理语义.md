---
layout: post
author: sjf0115
title: 深入了解 Flink 如何实现端到端的 Exactly-Once 处理语义
date: 2019-02-10 16:05:01
tags:
  - Flink

categories: Flink
permalink: end-to-end-exactly-once-processing-apache-flink-apache-kafka
---

这篇文章改编自2017年柏林Flink Forward上Piotr Nowojski的[演讲](https://berlin.flink-forward.org/kb_sessions/hit-me-baby-just-one-time-building-end-to-end-exactly-once-applications-with-flink/)。你可以在 Flink Forward Berlin 网站上找到幻灯片和演示文稿。

2017年12月发布的 Apache Flink 1.4.0 为 Flink 的流处理引入了一个叫 TwoPhaseCommitSinkFunction 重要特性（此处为相关的[Jira](https://issues.apache.org/jira/browse/FLINK-7210)），提取了两阶段提交协议的通用逻辑，使得在 Flink 和一系列 Source 和 Sink（包括 Apache Kafka 0.11 版本以及更高版本）之间构建端到端的 Exactly-Once 语义的应用程序成为可能。它提供了一个抽象层，用户只需实现几个方法就可以实现端到端的 Exactly-Once 语义。

如果这就是你需要了解的全部内容，可以去这个[地方](https://nightlies.apache.org/flink/flink-docs-release-1.14/api/java/org/apache/flink/streaming/api/functions/sink/TwoPhaseCommitSinkFunction.html)了解如何使用 TwoPhaseCommitSinkFunction。或者你可以直接去看实现 Exactly-Once 语义的[Kafka 0.11 producer](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/connectors/kafka.html#kafka-011)的文档，这也是在 TwoPhaseCommitSinkFunction 之上实现的。

如果你想了解更多信息，我们将在这篇文章中去深入了解一下新特性以及在 Flink 幕后发生的事情。纵览全篇，有以下几点：
- 描述 Flink 检查点在 Flink 应用程序保证 Exactly-Once 语义的作用。
- 展现 Flink 如何通过两阶段提交协议与 Source 和 Sink 交互，以提供端到端的 Exactly-Once 语义保证。
- 通过一个简单的示例，了解如何使用 TwoPhaseCommitSinkFunction 实现一个 Exactly-Once 语义的文件接收器。

### 1. Flink 应用程序的 Exactly-Once语义

当我们说 Exactly-Once 语义时，我们的意思是每个传入的事件只会对最终结果影响一次。即使机器或软件出现故障，也没有重复数据，也没有丢失数据。Flink 在很久之前就提供了 Exactly-Once 语义。在过去几年中，我们已经深入探讨过 Flink 的[检查点](http://smartsi.club/high-throughput-low-latency-and-exactly-once-stream-processing-with-apache-flink.html)，这是 Flink 提供 Exactly-Once 语义的核心。

在继续之前，我们先对检查点机制进行简要概述，这对我们理解检查点是有必要的。Flink 中的检查点是以下内容的一致快照：
- 应用程序的当前状态
- 输入流中的位置

Flink 以固定的时间间隔（可配置）生成检查点，然后将检查点写入持久存储系统，例如，S3 或 HDFS。将检查点数据写入持久存储是异步发生的，这意味着 Flink 应用程序在写检查点过程中可以继续处理数据。如果发生机器或软件故障重新启动后，Flink 应用程序从最近成功完成的检查点恢复。在处理开始之前，Flink 从检查点恢复应用程序状态并回滚到输入流中的正确位置。这意味着 Flink 的计算结果就好像从未发生过故障一样。

在 Flink 1.4.0 之前，Exactly-Once 语义仅局限于 Flink 应用程序内部，不能扩展到 Flink 数据处理完后发送的外部系统上。Flink 应用程序与各种数据输出端进行交互，开发人员需要有能力自己维护组件的上下文来保证 Exactly-Once 语义。为了提供端到端的 Exactly-Once 语义 - 也就是说，除了 Flink 应用程序之外，这些语义也同样适用于 Flink 写入的外部系统中 - 这些外部系统必须提供提交或回滚的方法，然后通过 Flink 的检查点机制来协调。

在分布式系统中的协调提交和回滚的一种常用方法是[两阶段提交协议](http://smartsi.club/two-phase-commit-of-distributed-transaction.html)。下面我们会讨论 Flink 的 TwoPhaseCommitSinkFunction 是如何利用[两阶段提交协议](http://smartsi.club/two-phase-commit-of-distributed-transaction.html)提供端到端的 Exactly-Once 语义。

### 2. Flink 的端到端 Exactly-Once 语义应用程序

下面我们将介绍[两阶段提交协议](http://smartsi.club/two-phase-commit-of-distributed-transaction.html)以及它如何在一个读取和写入 Kafka 的 Flink 应用程序示例中实现端到端的 Exactly-Once 语义。Kafka 是一个流行的消息中间件系统，经常与 Flink 一起使用。Kafka 在 0.11 版本中添加了对事务的支持。这意味着当你通过 Flink 读写 Kafka时，有必要提供端到端的 Exactly-Once 语义的支持。

Flink 对端到端 Exactly-Once 语义的支持不仅限于 Kafka，可以与任何提供协调机制的 Source/Sink 一起使用。例如，来自 Dell/EMC 的开源流处理存储系统 Pravega 也可以通过 TwoPhaseCommitSinkFunction 提供 Flink 端到端 Exactly-Once 语义。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/end-to-end-exactly-once-processing-apache-flink-apache-kafka-1.png?raw=true)

在我们今天要讨论的 Flink 应用程序示例中，我们有：
- 从 Kafka 读取数据的 Source（在 Flink 为 KafkaConsumer）
- 窗口聚合
- 将数据写回 Kafka 的 Sink（在 Flink 为 KafkaProducer）

要使 Sink 提供 Exactly-Once 语义保证，必须在一个事务中将所有数据写入 Kafka。提交捆绑了两个检查点之间的所有写入数据。这可确保在发生故障时能回滚所有写入的数据。但是，在具有多个并发运行的 Sink 任务的分布式系统中，简单的提交或回滚是远远不够的，因为必须确保所有组件在提交或回滚时一致才能确保一致的结果。Flink 使用[两阶段提交协议](http://smartsi.club/two-phase-commit-of-distributed-transaction.html)及预提交阶段来解决这一问题。

检查点的启动表示我们的[两阶段提交协议](http://smartsi.club/two-phase-commit-of-distributed-transaction.html)的预提交阶段。当检查点启动时，Flink JobManager 会将检查点 Barrier 注入数据流中（将数据流中的记录分为进入当前检查点的集合与进入下一个检查点的集合）。Barrier 在算子之间传递。对于每个算子，它会触发算子状态后端生成状态的快照。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/end-to-end-exactly-once-processing-apache-flink-apache-kafka-2.png?raw=true)

Source 存储 Kafka 的偏移量，完成此操作后将检查点 Barrier 传递给下一个算子。这种方法只适用于算子只有内部状态（Internal state）的情况。内部状态是 Flink 状态可以存储和管理的所有内容 - 例如，第二个算子中的窗口总和。当一个进程只有内部状态时，除了写入到已定义的状态变量之外，不需要在预提交阶段执行任何其他操作。Flink 负责在检查点成功的情况下正确提交这些写入，或者在出现故障时中止这些写入。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/end-to-end-exactly-once-processing-apache-flink-apache-kafka-3.png?raw=true)

但是，当一个进程具有外部状态（External state）时，状态处理会有所不同。外部状态通常以写入外部系统（如Kafka）的形式出现。在这种情况下，为了提供 Exactly-Once 语义保证，外部系统必须支持事务，这样才能和两阶段提交协议集成。

我们示例中的数据接收器具有外部状态，因为它正在向 Kafka 写入数据。在这种情况下，在预提交阶段，除了将其状态写入状态后端之外，数据接收器还必须预先提交其外部事务。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/end-to-end-exactly-once-processing-apache-flink-apache-kafka-4.png?raw=true)

当检查点 Barrier 通过所有算子并且触发的快照回调成功完成时，预提交阶段结束。所有触发的状态快照都被视为该检查点的一部分。检查点是整个应用程序状态的快照，包括预先提交的外部状态。如果发生故障，我们可以回滚到上次成功完成快照的时间点。

下一步是通知所有算子检查点已成功完成。这是两阶段提交协议的提交阶段，JobManager 为应用程序中的每个算子发出检查点完成的回调。

数据源和窗口算子没有外部状态，因此在提交阶段，这些算子不用执行任何操作。但是，数据接收器有外部状态，因此此时应该提交外部事务：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/end-to-end-exactly-once-processing-apache-flink-apache-kafka-5.png?raw=true)

我们总结一下：
- 一旦所有算子完成预提交，就会发出一个提交。
- 如果至少有一个预提交失败，那么所有其他的提交也都会中止，并将回滚到上一个成功完成的检查点。
- 在预提交成功之后，必须保证提交最终成功 - 我们的算子和外部系统都需要保证这点。如果一个提交失败（例如，由于间歇性网络问题），整个 Flink 应用程序将会失败，应用程序将根据用户的重启策略重新启动，并且还会尝试一次提交。这个过程至关重要，因为如果提交最终失败，将会发生数据丢失。

因此，我们要确定所有算子都同意检查点的最终结果：所有算子都同意数据提交或中止提交并回滚。

### 3. 在Flink中实现两阶段提交算子

实现完整的[两阶段提交协议](http://smartsi.club/two-phase-commit-of-distributed-transaction.html)可能有点复杂，这就是 Flink 为什么将两阶段提交协议的通用逻辑提取到 TwoPhaseCommitSinkFunction 抽象类中。

下面我们讨论一下如何在一个简单的基于文件的示例上实现 TwoPhaseCommitSinkFunction。我们只需实现四个函数就能为文件接收器提供 Exactly-Once 语义：
- beginTransaction：在开启事务之前，我们在目标文件系统的临时目录中创建一个临时文件。后面我们在处理数据时将数据写入此文件。
- preCommit：在预提交阶段，刷写（flush）文件，然后关闭文件，之后就不能写入到文件了。我们还将为属于下一个检查点的任何后续写入启动新事务。
- commit：在提交阶段，我们将预提交的文件原子性地移动到真正的目标目录中。请注意，这会增加输出数据可见性的延迟。
- abort：在中止阶段，我们删除临时文件。

我们知道，如果发生故障时，Flink 会将应用程序的状态恢复到最新的成功检查点。有一种极端情况，在成功预提交之后但在提交通知到算子之前发生故障。在这种情况下，Flink 会将我们的算子恢复到已经预提交但尚未提交的状态。

我们必须在检查点状态下保存有关预提交事务的足够信息，以便能够在重新启动后正确中止或提交事务。在我们的示例中，这些信息是临时文件和目标目录的路径。

TwoPhaseCommitSinkFunction 已经将这种情况考虑在内了，当从检查点恢复状态时优先发出一个提交。我们需要以幂等方式实现提交。一般来说，这应该不难。在我们的示例中，我们可以识别出这样的情况：临时文件不在临时目录中，已经移到目标目录中。还有一些其他边缘情况，TwoPhaseCommitSinkFunction 也考虑到了。

### 4. 总结

下面是我们这篇文章的一些要点：
- Flink 检查点是支持[两阶段提交协议](http://smartsi.club/two-phase-commit-of-distributed-transaction.html)并提供端到端的 Exactly-Once 语义的基础。
- 这个方案的一个优点是: Flink 不像其他一些系统那样，通过网络传输存储（materialize）数据 - 不需要像大多数批处理程序那样将计算的每个阶段写入磁盘。
- Flink 新的 TwoPhaseCommitSinkFunction 提取了[两阶段提交协议](http://smartsi.club/two-phase-commit-of-distributed-transaction.html)的通用逻辑，并使构建端到端的 Exactly-Once 语义的应用程序（使用 Flink 和支持事务的外部系统）成为可能。
- 从 Flink 1.4.0 开始，Pravega 和 Kafka 0.11 producer 都提供了 Exactly-Once 语义；在 Kafka 0.11 中首次引入了事务，这使得 Kafka 在 Flink 实现 Exactly-Once producer 成为可能。
- [Kafka 0.11 producer](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/connectors/kafka.html#kafka-011) 是在 TwoPhaseCommitSinkFunction 基础之上实现的，与 At-Least-Once 语义的 Kafka producer 相比，它的开销非常低。

原文：[An Overview of End-to-End Exactly-Once Processing in Apache Flink](https://www.ververica.com/blog/end-to-end-exactly-once-processing-apache-flink-apache-kafka)
