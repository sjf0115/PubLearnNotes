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

Flink 中的第二种状态是 Keyed State。与 Operator State 相反，Keyed State 作用于每个 Key，其中 Key 是从每个流事件中提取的。为了说明 Keyed State 与 Operator State 的不同之处，我们使用以下示例。假设我们有一个事件流，其中每个事件都具有 {customer_id：int，value：int} 这样的格式。我们已经知道可以使用 Operator State 计算所有的顾客并输出连续的总和。现在假设我们要稍微修改一下我们的目标需求，我们要为每个顾客计算一个连续的总和。这可以使用 Keyed State 来实现，因为必须为流中的每个唯一键维护一个聚合状态。


















原文:[A Deep Dive into Rescalable State in Apache Flink](https://flink.apache.org/features/2017/07/04/flink-rescalable-state.html)
