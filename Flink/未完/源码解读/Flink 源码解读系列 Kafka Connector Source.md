


## 1. FlinkKakfaConsumerBase

FlinkKakfaConsumerBase 需要实现 3 个接口 ResultTypeQueryable、CheckpointedFunction、CheckpointListener 以及派生 1 个抽象类 RichParallelSourceFunction。

```java
public FlinkKafkaConsumerBase(List<String> topics, Pattern topicPattern,
        KafkaDeserializationSchema<T> deserializer, long discoveryIntervalMillis, boolean useMetrics) {
    // Topic 描述符
    this.topicsDescriptor = new KafkaTopicsDescriptor(topics, topicPattern);
    // 序列化器
    this.deserializer = checkNotNull(deserializer, "valueDeserializer");
    // 分区发现时间间隔
    this.discoveryIntervalMillis = discoveryIntervalMillis;
    // Metric
    this.useMetrics = useMetrics;
}
```

### 1.1 ResultTypeQueryable

ResultTypeQueryable 接口比较简单，只需要实现 getProducedType 方法返回序列化器的返回值数据类型信息即可：
```java
public TypeInformation<T> getProducedType() {
    return deserializer.getProducedType();
}
```
> deserializer 是 Kafka 的序列化器

### 1.2 CheckpointedFunction

需要实现 CheckpointedFunction 接口如下的两个方法：
```java
public interface CheckpointedFunction {
    void initializeState(FunctionInitializationContext context) throws Exception;
    void snapshotState(FunctionSnapshotContext context) throws Exception;
}
```

#### 1.2.1 initializeState

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

#### 1.2.2 snapshotState

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


### 1.3 CheckpointListener

### 1.4 RichParallelSourceFunction

## 2. FlinkKakfaConsumer




https://mp.weixin.qq.com/s/Y7DxI5qZUlLOr6AR9C4tqQ
https://mp.weixin.qq.com/s/oFpq5phikRIPb5dTbiOZpQ
https://mp.weixin.qq.com/s/oi88IWQ7IKZ_Por6CcQ1LA
https://mp.weixin.qq.com/s/q2uTHqB6em7pxiT_CqBfYA
