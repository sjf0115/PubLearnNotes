

和大多数有状态的算子一样，为了容错和更容易的进行水平扩展，它也实现了 CheckpointedFunction，CheckpointListener 接口，当 checkpoint 开启时，snapshotState 方法会被周期性的调用，就会将当前 fetcher 提交的 KafkaTopicPartition 信息和 Offset 定期的存储到状态存储 ListState 上，并在所有任务都成功 checkpoint 时，notifyCheckpointComplete 方法将会被调用，并将等待提交的 offset，从 pendingOffsetsToCommit 取出，并提交到 Kafka 上。


需要实现 CheckpointedFunction 接口如下的两个方法：
```java
public interface CheckpointedFunction {
    void initializeState(FunctionInitializationContext context) throws Exception;
    void snapshotState(FunctionSnapshotContext context) throws Exception;
}
```

## 1. 初始化状态 initializeState

使用 UnionListState 存储 Kafka 每个 Partition 的 Offset 信息。如果是从故障中恢复，则从 UnionListState 中获取故障前存储的所有 Offset 信息，并存储在 TreeMap 数据结构中。如果是首次运行，不需要从状态中恢复，只是打印一条日志说明没有状态恢复：
```java
public final void initializeState(FunctionInitializationContext context) throws Exception {
    OperatorStateStore stateStore = context.getOperatorStateStore();
    // 获取存储 Offset 的 UnionListState
    this.unionOffsetStates = stateStore.getUnionListState(
        new ListStateDescriptor<>(
              OFFSETS_STATE_NAME,
              // 创建 UnionListState 的序列化器
              createStateSerializer(getRuntimeContext().getExecutionConfig())
        )
    );
    // 如果是从状态中恢复
    if (context.isRestored()) {
        restoredState = new TreeMap<>(new KafkaTopicPartition.Comparator());
        for (Tuple2<KafkaTopicPartition, Long> kafkaOffset : unionOffsetStates.get()) {
            restoredState.put(kafkaOffset.f0, kafkaOffset.f1);
        }
    } else {
        // 无状态可恢复
        // 打印日志 no restore state
    }
}
```
UnionListState 的序列化器：
```java
static TupleSerializer<Tuple2<KafkaTopicPartition, Long>> createStateSerializer(ExecutionConfig executionConfig) {
    TypeSerializer<?>[] fieldSerializers =
            new TypeSerializer<?>[] {
                new KryoSerializer<>(KafkaTopicPartition.class, executionConfig),
                LongSerializer.INSTANCE
            };
    @SuppressWarnings("unchecked")
    Class<Tuple2<KafkaTopicPartition, Long>> tupleClass = (Class<Tuple2<KafkaTopicPartition, Long>>) (Class<?>) Tuple2.class;
    return new TupleSerializer<>(tupleClass, fieldSerializers);
}
```

## 2. 生成快照 snapshotState

```java
public final void snapshotState(FunctionSnapshotContext context) throws Exception {
    if (!running) {
        LOG.debug("snapshotState() called on closed source");
    } else {
        // 清空 UnionOffsetState
        unionOffsetStates.clear();
        final AbstractFetcher<?, ?> fetcher = this.kafkaFetcher;
        if (fetcher == null) {
            for (Map.Entry<KafkaTopicPartition, Long> subscribedPartition : subscribedPartitionsToStartOffsets.entrySet()) {
                unionOffsetStates.add(Tuple2.of(subscribedPartition.getKey(), subscribedPartition.getValue()));
            }
            // Kafka 提交模式为 Checkpoint 时提交
            if (offsetCommitMode == OffsetCommitMode.ON_CHECKPOINTS) {
                pendingOffsetsToCommit.put(context.getCheckpointId(), restoredState);
            }
        } else {
            HashMap<KafkaTopicPartition, Long> currentOffsets = fetcher.snapshotCurrentState();
            if (offsetCommitMode == OffsetCommitMode.ON_CHECKPOINTS) {
                pendingOffsetsToCommit.put(context.getCheckpointId(), currentOffsets);
            }
            for (Map.Entry<KafkaTopicPartition, Long> kafkaTopicPartitionLongEntry : currentOffsets.entrySet()) {
                unionOffsetStates.add(Tuple2.of(kafkaTopicPartitionLongEntry.getKey(), kafkaTopicPartitionLongEntry.getValue()));
            }
        }

        if (offsetCommitMode == OffsetCommitMode.ON_CHECKPOINTS) {
            while (pendingOffsetsToCommit.size() > MAX_NUM_PENDING_CHECKPOINTS) {
                pendingOffsetsToCommit.remove(0);
            }
        }
    }
}
```

## 3. Checkpoint 完成通知

```java

```

## 4. Checkpoint 取消通知
