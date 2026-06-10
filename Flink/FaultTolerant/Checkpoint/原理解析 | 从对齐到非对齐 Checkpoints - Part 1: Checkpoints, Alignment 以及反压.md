基于 Checkpoint 的容错机制是 Apache Flink 的核心特性之一。由于这种设计，Flink 统一了批处理和流处理，可以轻松扩展到非常小以及非常大的场景，并为许多功能提供了支持，例如在状态变更或回滚下进行状态升级。

尽管有这些优秀的特性，但 Flink Checkpoint 有一个致命弱点：完成 Checkpoint 的速度取决于数据在应用程序中的处理速度。当应用程序出现反压时，Checkpoint 的处理也会受到反压（附录 1 回顾了什么是反压以及为什么反压是有益的）。在这种情况下，Checkpoint 需要更长的时间才能完成，甚至有可能超时。

在 Flink 1.11 中，社区引入了一个名为 'Unaligned Checkpoints' 功能的第一个版本，目的就是为了解决这个问题，Flink 1.12 计划进一步扩展其功能。在这两篇系列博文中，我们将讨论 Flink 的 Checkpoint 机制如何被修改以支持 Unaligned Checkpoints、Unaligned Checkpoints 如何工作，以及这种新模式对 Flink 用户的影响。在第一篇文章中，我们首先回顾 Flink 中原始的 Checkpoint 过程、核心属性以及在反压下的问题。

## 1. 状态

简单说，状态就是需要跨事件记住的信息。即使是最简单的流应用程序通常也是有状态的，因为需要'记住'它们处理数据的确切位置，例如 Kafka 分区 Offset 或文件 Offset。此外，许多应用程序在内部保存状态来支持内部操作，例如窗口、聚合、JOIN。

在本文的剩余部分，我们会使用如下一个由四个算子组成的流式应用程序作为示例，每个算子都会保存一些状态。

![](https://flink.apache.org/img/blog/2020-10-15-from-aligned-to-unaligned-checkpoints-part-1/from-aligned-to-unaligned-checkpoints-part-1-1.png)

## 2. 通过 Checkpoint 的状态持久化

流处理应用程序是长期运行的，它们不可避免地会遇到硬件或者软件的故障。但理想情况下，即使发生故障，它们也应该从外部看起来好像从未发生过故障一样。由于应用程序是长期运行的，并且可能累积了非常大的状态，因此在失败后重新计算部分结果可能需要相当长的时间，因此我们需要一种方法来持久化和恢复（可能非常大）应用程序状态。

Flink 依靠其状态 Checkpoint 和恢复机制来实现这样的行为，如下图所示。周期性 Checkpoint 将应用程序状态的快照存储在某些存储（通常是对象存储或分布式文件系统，如 S3、HDFS、GCS、Azure Blob 存储等）上。当检测到故障时，应用程序受影响的部分将重置为最新 Checkpoint 的状态（通过本地重置或从 Checkpoint 存储加载状态）。

![](https://flink.apache.org/img/blog/2020-10-15-from-aligned-to-unaligned-checkpoints-part-1/from-aligned-to-unaligned-checkpoints-part-1-2.png)

Flink 基于 Checkpoint 的方法不同于其他流处理系统采用的方法，例如将状态保存在分布式数据库中或将状态更改写入日志中。基于 Checkpoint 的方法具有一些不错的优点，如下所述，这使其成为 Flink 的绝佳选择。
- Checkpoint 具有非常简单的外部依赖性：无论是对象存储还是分布式文件系统一般是最易使用且最易于管理的服务。因为这些在所有公共云提供商上都可以使用，并且是第一批在本地提供的系统，所以 Flink 非常适合云原生堆栈。此外，与分布式数据库、键/值存储或事件代理相比，这些存储系统要便宜一个数量级（GB/月）。
- Checkpoint 是不可变的并且具有版本：输入不可变和版本化的结合（本质上是输入流），Checkpoint 可以支持存储不可变的应用程序快照，用来回滚、调试、测试。
- Checkpoint 将'流传输'与持久化机制解耦：'流传输'是指算子之间如何交换数据（例如，在 shuffle 期间）。这种解耦是 Flink 在一个系统中实现流批统一的关键，因为这样可以允许 Flink 实现一种数据传输，可以采用低延迟流式交换或解耦批处理数据交换的形式。

## 3. Checkpoint 机制

Checkpoint 算法解决的最基本的挑战是在不暂停事件连续处理的情况下生成流应用程序不断变化的状态快照。因为总是有事件在处理中（在网络上、在 I/O 缓冲区中等），所以上游和下游算子可以处理来自不同时间的事件：Sink 可能开始写入 11:04 的数据，而 Source 已经开始读取 11:06 的数据。理想情况下，所有快照数据应该属于相同的时间点，就好像输入被暂停，我们等到所有正在处理的数据都被处理完（即管道变得空闲）才生成快照。

为了实现这一点，Flink 在 Source 端将 Checkpoint Barrier 注入到流中，这些流穿过整个拓扑并最终到达 Sink。这些 Barrier 将流分为 pre-checkpoint epoch（所有事件持久化到状态中或者已经发送到 sinks）和 post-checkpoint epoch（未反映在 state 中的事件，在从 checkpoint 恢复时重新处理）。

下图展示了当 Barrier 到达算子时发生的事情：

![](https://flink.apache.org/img/blog/2020-10-15-from-aligned-to-unaligned-checkpoints-part-1/from-aligned-to-unaligned-checkpoints-part-1-3.png)

算子需要确保准确地执行了 Checkpoint（所有 pre-checkpoint 事件被处理，post-checkpoint 事件不会被处理）。当第一个 Barrier 到达输入缓冲区队列的头部并被算子消费时，算子进入所谓的对齐阶段。在这个阶段，算子不会消费已经接收到 Barrier 的通道中的数据，直到算子所有输入通道中都接收到 Barrier。

一旦收到所有 Barrier，算子会生成状态快照，将 Barrier 转发到输出，并结束对齐阶段，这会解除所有输入的阻塞。算子状态快照被写入 Checkpoint 存储。一旦所有算子都成功地将他们的状态快照写入 Checkpoint 存储，Checkpoint 就成功完成并可以用来故障恢复。

这里要注意的一件重要的事情是，Barrier 会随着事件流动。在没有反压下，Barrier 会在几毫秒内流动并对齐。Checkpoint 持续时间主要取决于将状态快照写入 Checkpoint 存储所需的时间，使用增量检查点会变得更快。如果事件在反压下缓慢流动，Barrier 也会如此。这意味着 Barrier 从 Source 流到 Sink 可能需要很长时间，从而导致对齐阶段需要更长的时间才能完成。

## 4. 恢复

当算子从 Checkpoint 重新启动（自动恢复或者使用 Savepoint 手动恢复）时，算子首先从 Checkpoint 存储恢复状态，然后再恢复事件流处理。

![](https://flink.apache.org/img/blog/2020-10-15-from-aligned-to-unaligned-checkpoints-part-1/from-aligned-to-unaligned-checkpoints-part-1-4.png)

由于 Source 与 Checkpoint 中保存的 Offset 绑定，因此恢复时间通常计算为恢复过程的时间以及处理系统故障之前剩余数据所需的额外时间的总和。当应用程序遇到反压时，恢复时间还包括从恢复过程开始到完全消除发压的总时间。

## 5. 一致性保证

只有 Exactly-Once 处理语义的 Checkpoint 才需要对齐阶段。如果应用程序以 At-Least-Once 处理语义运行，那么 Checkpoint 在对齐阶段不会阻塞任何通道，这会在恢复算子时因复制当时未阻塞的事件而产生额外成本。

不要与在 Sink 中的 At-Least-Once 语义相混淆，这是许多 Flink 用户在事务 Sink 上的选择，因为许多 Sink 算子是幂等的或收敛到相同的结果（如输入/输出到键/值存储）。在中间算子状态下拥有 At-Least-Once 语义通常不是幂等的（例如简单的计数聚合），因此对于大多数 Flink 用户来说，最好使用 Exactly-Once 语义的 Checkpoint。

## 6. 结论

这篇博文回顾了 Flink 的容错机制（基于对齐的 Checkpoint）是如何工作的，以及为什么 Checkpoint 是一种适合容错流处理器的机制。Checkpoint 机制随着时间的推移进行了优化，使 Checkpoint 更快、更便宜（异步和增量 Checkpoint）和更快的恢复（本地缓存），但基本概念（Barrier、对齐、算子状态快照）仍然与原始版本一样。

下一篇将深入探讨一项对原始机制的重大突破——避免对齐阶段的最近引入的 'Unaligned Checkpoints'。敬请期待第二篇，我们将解释 Unaligned Checkpoints 的工作原理以及如何在反压下保证一致的 Checkpoint 时间。

## 附录 1：关于反压

反压是指当接收方（例如数据/请求的接收方）处理速度较慢时，让发送方减速以避免压垮接收方的行为，否则可能导致丢弃正在处理的部分数据或请求。这是对于完整性/正确性至关重要的系统中一种关键且非常理想的行为。反压隐式地实现在许多分布式通信的基本构建模块中，如 TCP 流量控制、有界（阻塞）I/O 队列、基于 poll 的消费者等。

Apache Flink 在整个数据流图中实现了反压。一个（暂时）无法跟上数据速率的 Sink 会导致 Source 连接器减速，从而更慢地从源系统拉取数据。我们认为这是一种好的且理想的行为，因为反压不仅是为了避免压垮接收方（线程）的内存，还可以防止流应用程序的不同阶段之间漂移得太远。

考虑下面的例子：

我们有一个 Source（假设从 Apache Kafka 读取数据）、解析数据、按 Key 分组和聚合数据，以及写入到 Sink 系统（某个数据库）。应用程序需要在解析和分组/聚合步骤之间按 Key 重新分组数据。

假设我们使用一种非反压的方法，例如将数据写入日志/消息队列以进行网络上的数据重新分组（Kafka Streams 使用的方法）。如果 Sink 现在比流应用程序的其余部分慢（这很容易发生），第一阶段（Source 和解析）仍然会尽可能快地从源拉取数据、解析并放入用于 Shuffle 的日志中。这个中间日志会累积大量数据，意味着它需要大量的存储容量，在最坏的情况下可能需要保存输入数据的完整副本，否则会导致数据丢失（当漂移超过保留时间时）。

通过反压，Source/解析阶段会减速以匹配 Sink 的速度，使应用程序的两个部分在处理数据的进度上保持更接近，从而避免了需要预配大量中间存储容量的问题。

> 原文: [From Aligned to Unaligned Checkpoints - Part 1: Checkpoints, Alignment, and Backpressure](https://flink.apache.org/2020/10/15/from-aligned-to-unaligned-checkpoints-part-1-checkpoints-alignment-and-backpressure/)
