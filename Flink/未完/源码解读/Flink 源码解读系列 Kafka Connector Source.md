


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

```java
public final void initializeState(FunctionInitializationContext context) throws Exception {
    OperatorStateStore stateStore = context.getOperatorStateStore();
    this.unionOffsetStates =
            stateStore.getUnionListState(
                    new ListStateDescriptor<>(
                            OFFSETS_STATE_NAME,
                            createStateSerializer(getRuntimeContext().getExecutionConfig())));

    if (context.isRestored()) {
        restoredState = new TreeMap<>(new KafkaTopicPartition.Comparator());
        for (Tuple2<KafkaTopicPartition, Long> kafkaOffset : unionOffsetStates.get()) {
            restoredState.put(kafkaOffset.f0, kafkaOffset.f1);
        }
        LOG.info(
                "Consumer subtask {} restored state: {}.",
                getRuntimeContext().getIndexOfThisSubtask(),
                restoredState);
    } else {
        LOG.info(
                "Consumer subtask {} has no restore state.",
                getRuntimeContext().getIndexOfThisSubtask());
    }
}
```

#### 1.2.2 snapshotState

### 1.3 CheckpointListener

### 1.4 RichParallelSourceFunction

## 2. FlinkKakfaConsumer




https://mp.weixin.qq.com/s/Y7DxI5qZUlLOr6AR9C4tqQ
https://mp.weixin.qq.com/s/oFpq5phikRIPb5dTbiOZpQ
https://mp.weixin.qq.com/s/oi88IWQ7IKZ_Por6CcQ1LA
https://mp.weixin.qq.com/s/q2uTHqB6em7pxiT_CqBfYA
