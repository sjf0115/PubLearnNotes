https://www.cnblogs.com/Springmoon-venn/p/13405140.html

> Flink 1.13.5

## 1. 提交 Offset

### 1.1 触发提交

> FlinkKafkaConsumerBase

当 Flink 触发的 Checkpoint 完成时，会调用算子的 notifyCheckpointComplete 方法来周知。需要注意的是只有当 Offset 提交模式为 ON_CHECKPOINTS 时，才会在完成 Checkpoint 时提交 Offset，即在 notifyCheckpointComplete 中完成 Offset 的提交：
```java
private final LinkedMap pendingOffsetsToCommit = new LinkedMap();
public final void notifyCheckpointComplete(long checkpointId) throws Exception {
    // 周知 checkpointId 对应的 Checkpoint 完成
    ...
    if (offsetCommitMode == OffsetCommitMode.ON_CHECKPOINTS) {
        try {
            // 获取当前 CheckpointId 在 LinkedMap 中的位置
            final int posInMap = pendingOffsetsToCommit.indexOf(checkpointId);
            if (posInMap == -1) {
                return;
            }
            // 根据位置获取每个分区的 Offset
            Map<KafkaTopicPartition, Long> offsets = (Map<KafkaTopicPartition, Long>) pendingOffsetsToCommit.remove(posInMap);
            // 只保留比当前 CheckpointId 新的 Checkpoint 的 Offset 信息 其他的删除
            for (int i = 0; i < posInMap; i++) {
                pendingOffsetsToCommit.remove(0);
            }
            if (offsets == null || offsets.size() == 0) {
                return;
            }
            // 转交给 fetcher 提交 Offset
            fetcher.commitInternalOffsetsToKafka(offsets, offsetCommitCallback);
        } catch (Exception e) {
            if (running) {
                throw e;
            }
        }
    }
}
```
pendingOffsetsToCommit 是一个 LinkedMap 数据结构，用来存储等待提交的 Offset。首先判断当前指定的 checkpointId 是否有需要提交的 Offset 信息。如果有则从 pendingOffsetsToCommit 中获取对应 checkpointId 下各个分区的 offset 信息，使用 `Map<KafkaTopicPartition, Long>` 数据结构进行存储。删除比指定 checkpointId 更早的 Checkpoint 的 Offset 信息，可能有的 Checkpoint 还没有成功提交 Offset。有了每个分区的 Offset 信息之后，转交给 kafkaFetcher 来提交 Offset 到 Kafka。

> offsetCommitCallback 是一个 Offset 提交回调函数，用来计算 Offset 提交成功和失败的次数：
```java
// 注册 Offset 提交成功 Counter
this.successfulCommits = this.getRuntimeContext()
        .getMetricGroup()
        .counter(COMMITS_SUCCEEDED_METRICS_COUNTER);
// 注册 Offset 提交失败 Counter
this.failedCommits = this.getRuntimeContext()
        .getMetricGroup()
        .counter(COMMITS_FAILED_METRICS_COUNTER);
// 提交 Offset 回调函数
this.offsetCommitCallback = new KafkaCommitCallback() {
    @Override
    public void onSuccess() {
        successfulCommits.inc();
    }
    @Override
    public void onException(Throwable cause) {
        failedCommits.inc();
    }
};
```

### 1.2 等待提交

> KafkaFetcher

notifyCheckpointComplete 方法中提交 Offset 的工作转交给了 AbstractFetcher 的 commitInternalOffsetsToKafka 来提交：
```java
public final void commitInternalOffsetsToKafka(Map<KafkaTopicPartition, Long> offsets, @Nonnull KafkaCommitCallback commitCallback) throws Exception {
    doCommitInternalOffsetsToKafka(filterOutSentinels(offsets), commitCallback);
}
```
而 AbstractFetcher.doCommitInternalOffsetsToKafka 最终由 KafkaFetcher.doCommitInternalOffsetsToKafka 实现：
```java
protected void doCommitInternalOffsetsToKafka(Map<KafkaTopicPartition, Long> offsets, @Nonnull KafkaCommitCallback commitCallback) throws Exception {
    @SuppressWarnings("unchecked")
    // 获取订阅的分区
    List<KafkaTopicPartitionState<T, TopicPartition>> partitions = subscribedPartitionStates();
    // 每个分区待提交的 Offset 与元数据信息
    Map<TopicPartition, OffsetAndMetadata> offsetsToCommit = new HashMap<>(partitions.size());
    for (KafkaTopicPartitionState<T, TopicPartition> partition : partitions) {
        // 分区对应要提交的 Offset
        Long lastProcessedOffset = offsets.get(partition.getKafkaTopicPartition());
        if (lastProcessedOffset != null) {
            checkState(lastProcessedOffset >= 0, "Illegal offset value to commit");
            // 通过 KafkaConsumer 提交的 Offset 为当前 Offset + 1
            long offsetToCommit = lastProcessedOffset + 1;
            offsetsToCommit.put(partition.getKafkaPartitionHandle(), new OffsetAndMetadata(offsetToCommit));
            partition.setCommittedOffset(offsetToCommit);
        }
    }
    consumerThread.setOffsetsToCommit(offsetsToCommit, commitCallback);
}
```
首先获取订阅的 Topic 分区，根据这些分区获取对应的要提交的 Offset。在这需要注意的是提交给 Kafka 的 Offset 为当前 Offset + 1，即告诉 Kafka 下一个需要处理的 Offset。从代码中可以看出存储 Offset 的数据结构从 Flink 的 `Map<KafkaTopicPartition, Long>` 转换为适用于 Kafka 的 `Map<TopicPartition, OffsetAndMetadata>`。因为我们要将待提交的 Offset 提交给 Kafka 来进行处理，即通过 KafkaConsumerThread 的 setOffsetsToCommit 方法来设置要提交的 Offset。

> KafkaTopicPartition 是 Flink 用来描述 Kafka Topic 分区；而 TopicPartition 是 Kafkfa 用来描述分区信息，OffsetAndMetadata 描述偏移量 Offset 元数据信息。

### 1.3 真正提交

> KafkaConsumerThread

上面说到通过 KafkaConsumerThread 的 setOffsetsToCommit 方法来设置要提交的 Offset，首先将待提交的 offset 存储到 Kafka 消费线程中待提交队列 nextOffsetsToCommit 中，需要等到下一个消费循环开始才会提交：
```java
void setOffsetsToCommit(Map<TopicPartition, OffsetAndMetadata> offsetsToCommit, @Nonnull KafkaCommitCallback commitCallback) {
    // 设置新的偏移量并返回旧的偏移量
    if (nextOffsetsToCommit.getAndSet(Tuple2.of(offsetsToCommit, commitCallback)) != null) {
        // 打印提示日志
        // 如果有没有提交的 Offset 则跳过 提交最新 Checkpoint 的 Offset
    }
    // 如果 consumer 阻塞在 poll() 或 handover 操作中，唤醒它以尽快提交
    handover.wakeupProducer();
    synchronized (consumerReassignmentLock) {
        if (consumer != null) {
            consumer.wakeup();
        } else {
            hasBufferedWakeup = true;
        }
    }
}
```
> nextOffsetsToCommit 是 `Map<TopicPartition, OffsetAndMetadata>` 和 `KafkaCommitCallback` 二元组的原子引用 AtomicReference

需要注意的是向 Kafka 提交偏移量 Offset 可能需要比检查点间隔更长的时间。如果之前的偏移量未提交则跳过，只需要提交最新的偏移量即可，因为有更新的完整检查点偏移量可用。如果 consumer 阻塞在 poll() 或 handover 操作中，唤醒它以尽快提交偏移量。

然后就到了 kafka 消费的线程，KafkaConsumerThread.run 方法中：  这里是消费 kafka 数据的地方，也提交对应消费组的offset

```java
public void run() {
  ...
  // 获取 Kafka 消费者 consumer
  this.consumer = getConsumer(kafkaProperties);
  ...
  try {
      ...
      while (running) {
          // 检查是否有需要提交的
          if (!commitInProgress) {
              final Tuple2<Map<TopicPartition, OffsetAndMetadata>, KafkaCommitCallback> commitOffsetsAndCallback = nextOffsetsToCommit.getAndSet(null);
              if (commitOffsetsAndCallback != null) {
                  commitInProgress = true;
                  // 异步提交 Offset
                  consumer.commitAsync(commitOffsetsAndCallback.f0, new CommitCallback(commitOffsetsAndCallback.f1));
              }
          }
      }
  }
}
```
nextOffsetsToCommit 是消费线程存储下一个要提交 Offset 的数据结构 AtomicReference：
```java
AtomicReference<Tuple2<Map<TopicPartition, OffsetAndMetadata>, KafkaCommitCallback>> nextOffsetsToCommit;
```



...
