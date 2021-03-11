---
layout: post
author: smartsi
title: 深入了解Apache Flink中的可伸缩状态
date: 2021-03-09 08:44:01
tags:
  - Flink

categories: Flink
permalink: a-deep-dive-into-rescalable-state-in-apache-flink
---



## 3. 重新分配Operator State

首先，我们讨论在调整并发时如何为 Operator State 重新分配状态。在 Flink 中，Operator State 一个常用场景是维护 Kafka Source 中 Kafka 分区的当前偏移量。每个 Kafka Source 实例都会维护一个 <PartitionID，Offset> 键值对存储在 Operator State 中，Kafka Source 正在读取的每个 Kafka 分区都会有这么一个键值对。调整并发后，如何为 Operator State 重新分配状态呢？理想情况下，我们希望在重新调整后，以轮询的方式从检查点中重新为所有并行算子实例分配所有的 <PartitionID，Offset> 键值对。

我们知道 Kafka 分区偏移量的含义，并且我们知道可以将它们视为独立的可再分配的状态单元。下图A说明了 Flink 中对 Operator State 进行 Checkpoint 的先前接口。在快照上，每个 Operator 实例都会返回一个代表其完整状态的对象。对于 Kafka Source 来说，此对象是分区偏移量的列表。然后将此快照对象写入分布式存储。还原时，再从分布式存储中读取该对象，并将其作为还原时的参数传递给 Operator 实例。

这种方法在重新调整并发时存在问题：Flink 如何将 Operator State 分解为有意义，可重新分配的分区呢？尽管 Kafka Source 上的状态确实时是分区偏移量的列表，但先前接口返回的状态对象对 Flink 来说时一个黑匣子，无法重新分配。

解决此黑盒问题的一个通用方法是，我们对 Checkpointing 接口进行了一些修改，称为 ListCheckpointed。下图B显示了新的 Checkpoint 接口，该接口返回并接收状态分区列表。引入列表而不是单个对象可以对状态进行有意义的划分：列表中的每个子项对 Flink 来说仍然是一个黑匣子，但可以认为是 Operator State 的可独立重分配的原子部分。

![](2)

我们的方法提供了一个简单的API，实现者可以使用该API编码有关如何划分和合并状态单元的特定于域的知识。借助我们新的 Checkpoint 接口，Kafka Source 可以使各个分区偏移量更加一目了然，并且状态重新分配变得与拆分和合并列表一样容易。
```java
public class FlinkKafkaConsumer<T> extends RichParallelSourceFunction<T> implements CheckpointedFunction {
	 // ...

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


## 4. 重新分配Keyed State

Flink 中的第二种状态是 Keyed State。与 Operator State 相反，Keyed State 作用于每个 Key，其中 Key 是从每个流事件中提取的。为了说明 Keyed State 与 Operator State 的不同之处，我们使用以下示例。假设我们有一个事件流，其中每个事件都具有 {customer_id：int，value：int} 这样的格式。我们已经知道可以使用 Operator State 计算所有的顾客并输出连续的总和。现在假设我们要稍微修改一下我们的目标需求，我们要为每个顾客计算一个连续的总和。这可以使用 Keyed State 来实现，因为必须为流中的每个唯一 Key 维护一个聚合状态。

需要注意的是，Keyed State 仅适用于通过 keyBy() 算子创建的 Keyed Stream。keyBy() 算子指定了如何从每个事件中提取 Key，并且确保具有相同 Key 的事件始终由相同的并行算子实例处理。所有 Keyed State 也可以绑定到一个并行算子实例上，因为对于每个 Key 来说，确实只有一个算子实例处理。从 Key 到算子的映射是通过 Key 上的哈希分区计算的。

我们可以看到，在进行重新调整并发时，Keyed State 比 Operator State 有一个明显的优势：我们可以轻松地弄清楚如何在并行算子实例之间正确分割和重新分配状态。状态重新分配仅在对 Keyed State 进行分区之后。调整后，必须将每个 Key 的状态重新分配给现在负责该 Key 的算子实例上，到底分配到哪个实例由 Keyed Stream 的哈希分区确定。尽管这可以解决在调整后将状态逻辑映射到子任务的问题，但还有一个实际问题需要解决：我们如何才能有效地将状态转移到子任务的本地？毕竟在重新分配之后，会出现状态与算子实例不具有本地性。

当我们不调整并发时，每个子任务都可以简单地一次性顺序读取前一个实例写入检查点的整个完整状态。但是，在重新调整并发的场景下，这不再可能。每个子任务的状态现在可能分散在其他所有子任务写入的文件中。我们已在下图A中说明了此问题。在此示例中，我们展示了如何使用 identity 作为哈希函数将并行度从3扩容到4，Key 范围从0到20。

一个很自然的想法是从所有子任务的检查点中读取所有先前实例的子任务状态，并过滤出每个子任务相匹配的 Key。尽管此方法实现了顺序读取，但是每个子任务可能读取大量不相关的状态数据，并且分布式文件系统接收了大量并行读取请求。另一种方法是建立一个索引，以跟踪检查点中每个 Key 的状态位置。 通过这种方法，所有子任务都可以非常针对性地定位和读取匹配的 Key。这种方法可以避免读取无关的状态数据，但是它有两个主要缺点。所有 Key 的物化索引（即 key 到读取偏移的映射）可能会变得非常大。此外，这种方法还会引入大量的随机I/O（当为单个 Key 寻找数据时，请参见下图A），这通常在分布式文件系统中带来非常差的性能。

Flink 的方法介于这两者之间，通过引入 KeyGroup 作为状态分配的基本单位。这是如何实现的呢？必须在开始作业之前确定键组的数量，并且（在当前情况之后）不能更改键组的数量。 由于密钥组是状态分配的基本单位，因此这也意味着密钥组的数量是并行性的上限。 简而言之，键组为我们提供了一种在重新缩放的灵活性（通过设置并行度的上限）与索引和还原状态所涉及的最大开销之间进行权衡的方法。












原文:[A Deep Dive into Rescalable State in Apache Flink](https://flink.apache.org/features/2017/07/04/flink-rescalable-state.html)
