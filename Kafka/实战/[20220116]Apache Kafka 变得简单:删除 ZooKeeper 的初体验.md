---
layout: post
author: smartsi
title: Apache Kafka 变得简单:删除 ZooKeeper 的初体验
date: 2022-01-16 17:58:01
tags:
  - Kafka

categories: Kafka
permalink: kafka-without-zookeeper-a-sneak-peek
---

Apache Kafka 的核心是日志，一种使用顺序操作的简单数据结构，与底层硬件配合操作。以日志为中心的设计带来了很多好处，包括高效的磁盘缓冲、CPU缓存使用、预取，零拷贝数据传输等，从而创造了 Kafka 众所周知的高效率和吞吐量特性。对于 Kafka 的新手来说，Topic 以及其作为提交日志的底层实现通常是他们了解的第一件事。但是日志本身的代码在整个系统中只占相对较小的一部分。Kafka 代码库中大部分的代码负责集群多个 Broker 之间分区的安排（即日志）、领导权的分配以及故障处理等等。这些代码使 Kafka 成为一个可靠且值得信赖的分布式系统。

从历史上看，Apache ZooKeeper 是这种分布式代码工作的关键部分。ZooKeeper 提供了保存 Kafka 系统最重要事实的元数据存储：分区所在的位置，哪个副本是领导者等等。但归根结底，ZooKeeper 是一个基于一致性日志的文件系统/触发器 API。Kafka 是基于一致性日志的发布/订阅 API。这会导致操作人员在两个日志实现、两个网络层和两个安全实现上对通信和性能进行调整、配置、监控、保护以及排查，每个实现都有不同的工具和监控 hooks。这变得没有必要地复杂。这种不可避免的复杂性促使一项举措的提出，用一个完全在 Kafka 内部运行的内部仲裁服务来取代 ZooKeeper。

当然，替换 ZooKeeper 是一项工作量相当大的工作，去年 4 月就开始启动了一项社区计划，以加快进度并在准备年底前交付一个可以运行的系统。我们很高兴地说，KIP-500 早期的代码已经合并到主干分支上了，预计将包含在即将发布的 2.8 版本中。你第一次可以在没有 ZooKeeper 的情况下运行 Kafka 了。我们称其为 Kafka Raft 元数据模式，通常缩写为 KRaft（发音为craft）模式。

需要注意的是，早期版本中一些功能是没有的。我们还不支持使用 ACL 以及其他安全功能，事务也是不支持的。此外，KRaft 模式也不支持分区重新分配和 JBOD（预计这些将在后续 Apache Kafka 版本中可用）。因此，考虑到仲裁控制器处于实验阶段，所以我们不建议将其用于生产环境中。但是，如果您尝试使用该功能，您会发现有许多新优势：部署和操作更简单，您可以将整个 Kafka 作为单个进程运行，并且每个集群可以容纳更多的分区。

## 1. 仲裁控制器：事件驱动的共识

如果您选择使用新的仲裁控制器运行 Kafka，那么以前由 Kafka 控制器和 ZooKeeper 承担的所有元数据职责都将合并到这一新服务中，并在 Kafka 集群内部运行。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-without-zookeeper-a-sneak-peek-1.png?raw=true)

仲裁控制器使用新的 KRaft 协议来确保元数据在仲裁中准确复制。该协议与 ZooKeeper 的 ZAB 协议和 Raft 在很多方面都相似，但有一些重要的区别，其中一个比较引人注意的是它使用了事件驱动的架构。仲裁控制器使用事件源（Event-Sourced）存储模型存储状态，从而确保始终可以准确地重新创建内部状态机。存储到状态的事件日志（也称为元数据主题）会定期通过快照进行删减，以确保日志不会无限增长。仲裁中的其他控制器可以通过响应存储在状态中的事件来跟随活跃控制器存。因此，如果一个节点由于分区事件而暂停，那么可以在重新加入时通过访问日志来快速获取它错过的任何事件。这显着减少了不可用窗口，从而缩短了系统的最坏情况恢复时间。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-without-zookeeper-a-sneak-peek-2.png?raw=true)

KRaft 协议的事件驱动特性意味着，与基于 ZooKeeper 的控制器不同，仲裁控制器在激活之前不需要从 ZooKeeper 加载状态。当领导权发生变化时，新的活跃控制器已经在内存中拥有所有提交的元数据记录。更重要的是，在 KRaft 协议中使用的相同的事件驱动机制可以跨集群跟踪元数据。以前使用 RPC 处理的任务现在也受益于事件驱动并可以使用实际日志进行通信。这些让人高兴的变化以及那些非常重要的原始设计让 Kafka 现在可以支持比以前更多的分区。让我们更详细地讨论一下。

## 2. Kafka 扩展：支持数百万个分区

Kafka 集群可以支持的分区数量由两个属性决定：每个节点的分区数上限和整个集群的分区数上限。到目前为止，集群分区数上限一直是元数据管理的主要瓶颈。之前的 Kafka 改进提案 (KIP) 已经改进了每个节点的上限，但 Kafka 的可扩展性主要通过添加节点以获得更多容量来实现。这就是为什么集群上限变得如此重要的原因，因为它定义了整个系统可扩展性的上限。

新的仲裁控制器设计可以为每个集群处理更多的分区。为了评估这一点，我们运行了与 2018 年评估的类似测试，以评估 [Kafka 的分区上限](https://www.confluent.io/blog/apache-kafka-supports-200k-partitions-per-cluster/)[1]。这些测试测量了停机和恢复所花费的时间，对于旧控制器来说是 O(#partitions) 时间复杂度。正是这个时间复杂度为 Kafka 在单个集群中可以支持的分区数量设置了上限。

正如 Jun Rao 在上面引用的博文中解释的那样，之前的实现可以实现 200K 个分区，限制因素是在 ZooKeeper 和 Kafka 控制器之间移动大量元数据所花费的时间。使用新的仲裁控制器，这两个角色都由同一个组件提供服务。事件驱动的方法意味着控制器故障转移现在几乎是即时的。以下是在我们实验室执行有 200 万个分区（之前上限的 10 倍）的集群的测试数据：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-without-zookeeper-a-sneak-peek-3.png?raw=true)

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-without-zookeeper-a-sneak-peek-4.png?raw=true)

受控和非受控停机的测量都很重要。受控停机影响的常见场景，例如滚动重启：部署软件更改的标准程序，同时保持整个过程的可用性。从不受控制的停机中恢复更为重要，因为它设置了系统的恢复时间目标 (RTO)，例如，在发生意外故障后，例如 VM 或 pod 崩溃或数据中心变得不可用。虽然这些措施只是更宽泛系统性能指标，但它们直接衡量了 ZooKeeper 使用所带来的众所周知的瓶颈。请注意，受控测量和非受控测量不能直接比较。不受控制的停机包括选举新领导人所需的时间，而受控的不包括。这种差异是为了使受控停机与饶俊最初的测量保持一致。

## 3. 减轻 Kafka：将 Kafka 作为单个进程

Kafka 通常被认为是重量级组件，管理 ZooKeeper（第二个独立的分布式系统）的复杂性是这种看法存在的重要原因。这通常会导致项目在开始时选择更轻量级的消息队列，比如 ActiveMQ 或 RabbitMQ 这样的传统队列，并在达到一定规模时迁移到 Kafka。这种想法是不对的，因为 Kafka 提供的抽象是围绕日志提交的，它即适用于初创公司的小规模工作负载，也同样适用于像 Netflix 或 Instagram 这样高吞吐量的工作负载。此外，如果要添加流处理，无论是选择 Kafka Streams，ksqlDB 还是其他流处理框架，都需要 Kafka 及其提交日志抽象。但是由于管理两个独立的系统（Kafka和Zookeeper）的复杂性，用户经常感到他们必须在规模还是入门之间做出选择。

现在这种情况不会再出现了。KIP-500 和 KRaft 模式提供了一种更出色的轻量级方式来使用 Kafka，并可以用作 ActiveMQ 或 RabbitMQ 等的替代方案。轻量级的单进程部署也更适合边缘场景和使用轻量级硬件的场景。

## 4. 尝试无 ZooKeeper 的 Kafka

新的仲裁控制器在主干分支中以实验功能提供，包含在 Apache Kafka 2.8 版本中发布。那么你能用它做什么呢？ 如前所述，一个简单但非常酷的新功能是能够创建单个进程 Kafka 集群。原文中的简短演示可以请点击[1]查看。

当然，如果您想扩展以支持更高的吞吐量并添加复制以实现容错，您只需要添加新的 broker 进程。如您所知，这是基于 KRaft 的仲裁控制器的早期版本。请不要将其用于关键工作中。

[1]: https://www.confluent.io/blog/apache-kafka-supports-200k-partitions-per-cluster/

原文:[Apache Kafka Made Simple: A First Glimpse of a Kafka Without ZooKeeper](https://www.confluent.io/blog/kafka-without-zookeeper-a-sneak-peek/)
