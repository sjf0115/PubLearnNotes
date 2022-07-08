
如果要判断 Task 读取的 Partition 以及具体的 Offset，首先需要知道该 Topic 有哪些 Partition。通过分区发现器 partitionDiscoverer 可以获取所有可用的分区：
```java
final List<KafkaTopicPartition> allPartitions = partitionDiscoverer.discoverPartitions();
```

```java
for (Map.Entry<KafkaTopicPartition, Long> restoredStateEntry : restoredState.entrySet()) {
    //
    int subTaskIndex = KafkaTopicPartitionAssigner.assign(
        restoredStateEntry.getKey(),
        getRuntimeContext().getNumberOfParallelSubtasks()
    );
    if (subTaskIndex == getRuntimeContext().getIndexOfThisSubtask()) {
        subscribedPartitionsToStartOffsets.put(restoredStateEntry.getKey(), restoredStateEntry.getValue());
    }
}
```
Partition 具体分配到哪个 Task，需要取决于 KafkaTopicPartitionAssigner 的 assign 方法中的分配策略：
```java
public static int assign(KafkaTopicPartition partition, int numParallelSubtasks) {
    int startIndex = ((partition.getTopic().hashCode() * 31) & 0x7FFFFFFF) % numParallelSubtasks;
    return (startIndex + partition.getPartition()) % numParallelSubtasks;
}
```
这里假设 Kafka 分区 Partition 的 id 总是从 0 开始递增，因此可以直接作为从起始索引的偏移量。计算当前的分区 Partition 应该属于哪个 Subtask。例如：一共有 20 个 Subtask，算出来的起始位置是 5，Partition Id 是 3，那么得出的 SubTask 编号为 8 = (5 + 3) % 20 = 8，因此该 Partition 应该分给 8 号的 Subtask。

为什么不能只使用分区 Partition Id 作为索引偏移量，还添加上一个开始偏移量 startIndex 呢？如果只使用分区 Partition Id 作为索引偏移量，我们来看看具体是什么情况。假设有 3 个 Topic，9 个任务：
- 第 1 个 Topic 3 个 Partition：
  - Partition 0 分配给 0 号 SubTask
  - Partition 1 分配给 1 号 SubTask
  - Partition 2 分配给 2 号 SubTask
- 第 2 个 Topic 2 个 Partition：
  - Partition 0 分配给 0 号 SubTask
  - Partition 1 分配给 1 号 SubTask
- 第 3 个 Topic 4 个 Partition：
  - Partition 0 分配给 0 号 SubTask
  - Partition 1 分配给 1 号 SubTask
  - Partition 2 分配给 2 号 SubTask
  - Partition 3 分配给 3 号 SubTask
综上：
- 0 号 SubTask 分配了 3 个 Partition
- 1 号 SubTask 分配了 3 个 Partition
- 2 号 SubTask 分配了 2 个 Partition
- 3 号 SubTask 分配了 1 个 Partition
- 其他 5 个 SubTask 均没有得到 Partition
- 序号越后的 SubTask 越得不到 Partition



。。。。
