---
layout: post
author: smartsi
title: 深入了解 Flink 的可扩展性状态
date: 2021-10-27 11:44:01
tags:
  - Flink

categories: Flink
permalink: a-deep-dive-into-rescalable-state-in-apache-flink
---

## 1. 有状态流

从高层次上讲，我们可以将流处理中的状态视为算子中的内存，该内存可以记住有关过去输入的信息，并可以作用于将来输入的处理。相反，无状态流处理中的算子仅关注当前输入，不关注上下文以及过去的输入。用一个简单的示例来说明这种差异：假设我们有一个数据流，输出 `{event_id：int，event_value：int}` 格式的事件。我们的目标是提取每个事件的 event_value 并输出。我们可以通过简单的 source-map-sink 管道轻松实现，其中 map 函数从事件中提取 event_value 并将其发送到下游的 Sink。这是一个无状态流处理的实例。

如果我们仅在当前事件中 event_value 大于上一个事件时才输出，这该怎么办？在这种情况下，我们的 map 函数显然需要某种方式来记住上一个事件的 event_value，因此这是一个有状态流处理的实例。

## 2. 状态

Apache Flink 是一个大规模并行分布式处理系统，可以进行大规模的有状态流处理。为了实现扩展性，Flink 作业在逻辑上分解为算子图，并且每个算子在物理执行上分解为多个并行算子实例。从概念上讲，Flink 中的每个并行算子实例都是一个独立的任务，可以在自己的机器上进行调度（Shared-Nothing 架构有网络连接的集群中）。

为了实现高吞吐量和低延迟，必须最小化任务之间的网络通信。在 Flink 中，用于流处理的网络通信仅发生在作业算子图中的相邻接边（垂直方向），因此流数据可以从上游算子传输到下游算子。但是，在算子的并行实例之间（水平方向）没有通信。为了避免此类网络通信，数据本地性在 Flink 中至关重要，会影响状态的存储和访问方式。

> 也就是上下游算子之间有网络通信，算子并行实例之间没有网络通信。

出于数据本地性考虑，Flink 中的所有状态数据总是与运行相应并行算子实例的任务绑定，并且与该任务在同一台机器上。通过这种设计，所有状态数据对任务来说都是本地的，状态访问不需要任务之间的网络通信。避免这种流量对于像 Flink 这样的大规模并行分布式系统的可扩展性至关重要。

对于 Flink 的状态流处理，我们区分两种不同类型的状态：Operator State 和 Keyed State。Operator State 的作用域是每个算子的并行实例（子任务），Keyed State 可以被认为是分区的 Operator State，每个 Key 具有一个状态分区。

## 3. 有状态流处理作业的扩展性

在无状态数据流中更改并行度（即修改算子的并行子任务的数量）非常容易。只需要启动或停止无状态算子的并行实例，并与上游和下游算子断开或者连接即可，如下图所示。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/a-deep-dive-into-rescalable-state-in-apache-flink-1.png?raw=true)

相反，改变有状态算子的并行度涉及比较多，因为我们必须以一致，正确的方式重新分配先前的算子状态。在 Flink Shared-Nothing 架构中，所有状态对于运行并行算子实例的任务来说都是本地的，并且在作业运行时并行算子实例之间不会进行网络通信。但是，在 Flink 中存在一种机制可以允许在任务之间以一致、Exactly-Once 语义保证的方式交换算子状态，这就是 Flink 的 Checkpoint 机制。简而言之，当 Checkpoint 协调器将特殊事件（所谓的 Checkpoint Barrier）注入流中时，就会触发 Checkpoint。Checkpoint Barrier 跟随事件流从 Source 向下游 Sink 流动，并且每当算子实例收到 Barrier 时，算子实例都会立即将其当前状态快照到分布式存储系统（例如，HDFS）。在作业恢复时，作业的新任务（现在可能在不同的机器上运行）可以再次从分布式存储系统中获取状态数据。我们可以在 Checkpoint 上搭载状态作业的扩缩容，如下图所示。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/a-deep-dive-into-rescalable-state-in-apache-flink-1.png?raw=true)

首先，触发 Checkpoint 并发送到分布式存储系统上。接下来，更改并行度重新启动作业，并从分布式存储上访问先前状态的一致性快照。虽然这解决了在机器之间重新分配一致性状态的问题，但仍然存在一个问题：如果先前状态与新的并行算子实例之间不是 1：1 关系，我们如何正确的分配状态？我们可以再次将先前的 map_1 和 map_2 的状态分配给新的 map_1 和 map_2。但这样 map_3 就没有状态。这种幼稚的方法可能造成低效或者错误的结果，具体取决于作业状态类型和具体的语义。

在下一节中，我们将说明如何解决 Flink 中高效，正确的状态重新分配问题。Flink 有两种状态（Operator State和 Keyed State），需要不同的状态分配方法。

### 3.1 Operator State

首先，我们讨论如何为 Operator State 重新分配状态。Operator State 的一个常用场景是维护 Kafka Source 中 Kafka 分区的当前偏移量。每个 Kafka Source 实例都会维护一个 `<PartitionID，Offset>` 键值对，Kafka Source 正在读取的每个 Kafka 分区都会有这么一个键值对。调整并发后，如何为 Operator State 重新分配状态呢？理想情况下，我们希望在重新调整后，以轮询的方式从 Checkpoint 中重新为所有并行算子实例分配所有的 `<PartitionID，Offset>` 键值对。

作为使用者，我们知道 Kafka 分区偏移量的含义，并且可以作为独立的可再分配的状态单元。下图展示了 Flink 中对 Operator State 进行 Checkpoint 的旧接口。在生成快照时，每个 Operator 实例都会返回一个代表其完整状态的对象。对于 Kafka Source 来说，此对象是分区偏移量的列表。然后将此快照对象写入分布式存储。恢复时，再从分布式存储中读取该对象，并将其作为参数传递给 Operator 实例。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/a-deep-dive-into-rescalable-state-in-apache-flink-3.png?raw=true)

这种方法在重新调整并发时存在问题：Flink 如何将 Operator State 拆分为正确，可重新分配的分区呢？尽管 Kafka Source 上的状态确实时是分区偏移量的列表，但旧接口返回的状态对象对 Flink 来说是一个黑匣子，无法感知对象内的数据结构，所以也无法重新分配。为了解决这个黑盒问题，我们对 Checkpointing 接口进行了一些修改，称为 ListCheckpointed。下图展示了新的 Checkpoint 接口，该接口返回并接收状态分区 List。使用 List 来代替单个 Oobject 对象可以对状态进行正确的分区：虽然 List 中的每个子项对 Flink 来说仍然是一个黑匣子，但可以认为是 Operator State 独立可重分配的原子单元。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/a-deep-dive-into-rescalable-state-in-apache-flink-4.png?raw=true)

借助我们新的 Checkpoint 接口，Kafka Source 可以使各个分区偏移量更加一目了然，并且状态重新分配变得与拆分和合并 List 一样容易：
```java
public class FlinkKafkaConsumer<T> extends RichParallelSourceFunction<T> implements CheckpointedFunction {
   private transient ListState<Tuple2<KafkaTopicPartition, Long>> offsetsOperatorState;
   @Override
   public void initializeState(FunctionInitializationContext context) throws Exception {
      OperatorStateStore stateStore = context.getOperatorStateStore();
      // register the state with the backend
      this.offsetsOperatorState = stateStore.getSerializableListState("kafka-offsets");
      // if the job was restarted, we set the restored offsets
      if (context.isRestored()) {
         for (Tuple2<KafkaTopicPartition, Long> kafkaOffset : offsetsOperatorState.get()) {
            // ... restore logic
         }
      }
   }
   @Override
   public void snapshotState(FunctionSnapshotContext context) throws Exception {
      this.offsetsOperatorState.clear();
      // write the partition offsets to the list of operator states
      for (Map.Entry<KafkaTopicPartition, Long> partition : this.subscribedPartitionOffsets.entrySet()) {
         this.offsetsOperatorState.add(Tuple2.of(partition.getKey(), partition.getValue()));
      }
   }
   // ...
}
```

##¥# 3.2 Keyed State

Flink 中的第二种状态是 Keyed State。与 Operator State 相反，Keyed State 作用于每个 Key，其中 Key 从每个流事件中提取。为了说明 Keyed State 与 Operator State 的不同之处，我们使用以下示例。假设我们有一个事件流，每个事件都具有 `{customer_id：int，value：int}` 的格式。我们知道可以使用 Operator State 计算并输出所有顾客的连续总和。现在假设我们要稍微修改一下我们的目标需求，我们要为每个顾客计算一个连续总和。这可以使用 Keyed State 来实现，因为必须为流中的每个 Key 维护一个聚合状态。

需要注意的是，Keyed State 仅适用于通过 keyBy() 算子创建的 Keyed Stream。keyBy() 算子指定了如何从每个事件中提取 Key，并且确保具有相同 Key 的事件始终由相同的并行算子实例处理。因为对于每个 Key 来说，确实只有一个并行算子实例来处理，因此，Keyed State 也会绑定到这一并行算子实例上。从 Key 到算子的映射是根据 Key 的哈希值计算的。

我们可以看到，在重新扩缩容时，Keyed State 比 Operator State 有一个明显的优势：我们可以轻松地弄清楚如何在并行算子实例之间正确拆分和重新分配状态。调整并发后，必须将每个 Key 的状态重新分配给现在负责该 Key 的算子实例上，到底分配到哪个实例由 Keyed Stream 的哈希分区确定。尽管这可以解决在调整后状态与子任务逻辑映射的问题，但还有一个实际问题需要解决：如何高效地将状态转移到子任务的本地？毕竟在重新分配之后，会导致状态与算子实例不在同一台机器上。

当我们没有扩缩容时，每个子任务都可以简单地一次性顺序读取前一个实例写入 Checkpoint 的整个完整状态。但是，当扩缩容时不能再这样。每个子任务的状态现在可能分散在其他所有子任务写入的文件中。如下图所示，我们展示了如何使用 identity 作为哈希函数将并行度从 3 扩容到 4，Key 范围从 0 到 20。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/a-deep-dive-into-rescalable-state-in-apache-flink-5.png?raw=true)

一个很自然的想法是从所有子任务的 Checkpoint 中读取先前实例的子任务状态，并过滤出每个子任务相匹配的 Key。尽管此方法实现了顺序读取，但是每个子任务可能读取大量不相关的状态数据，并且分布式文件系统接收了大量并行读取请求。另一种方法是建立一个索引，来跟踪 Checkpoint 中每个 Key 的状态位置。通过这种方法，所有子任务都可以非常准确地定位并读取匹配的 Key。这种方法可以避免读取无关的状态数据，但是有两个缺点：所有 Key 的物化索引（即 key 到读取偏移的映射）可能会非常大；此外，这种方法还会引入大量的随机 I/O（当为单个 Key 寻找数据时，请参见上图），这会给分布式文件系统中带来非常差的性能。

Flink 的方法介于这两者之间，通过引入 KeyGroup 作为状态分配的基本单位。这是如何实现的呢？必须在开始作业之前确定 KeyGroup 的数量，并且之后不能更改。由于 KeyGroup 是状态分配的基本单位，因此这也意味着 KeyGroup 的数量是最大并行度。简而言之，KeyGroup 为我们提供了一种扩所容的灵活性（通过设置最大并行度）与索引以及还原状态最大开销之间进行权衡的方法。

我们将连续的 KeyGroup 分配给子任务。这使得在恢复时不仅可以在 KeyGroup 中顺序读取，而且可以跨多个 KeyGroup 顺序读取。另一个好处是：KeyGroup 到子任务分配的元数据非常小。我们不需要维护 KeyGroup 的列表，因为跟踪范围边界就足够了。

如下图所示，展示了并行度从 3 到 4 的过程（10 个 KeyGroup）。我们可以看到，通过引入 KeyGroup 以及范围重分配的方式极大的提升了访问效率。下图中的计算公式 2 和计算公式 3 还详细的说明了 KeyGroup 的计算和分配过程。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/a-deep-dive-into-rescalable-state-in-apache-flink-6.png?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文:[A Deep Dive into Rescalable State in Apache Flink](https://flink.apache.org/features/2017/07/04/flink-rescalable-state.html)
