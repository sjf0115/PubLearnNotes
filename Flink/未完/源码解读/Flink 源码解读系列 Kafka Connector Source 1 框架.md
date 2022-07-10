


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

### 1.1 RichParallelSourceFunction

#### 1.1.1 Open

RichParallelSourceFunction 的 Open 方法主要用来初始化如下几个工作：
- 确定 Offset 的提交模式 offsetCommitMode
- 创建 Partition 分区发现器 partitionDiscoverer
- 确定要读取的每个 Partition 的 Offset，存储在 subscribedPartitionsToStartOffsets 数据结构中。Offset 分配策略具体取决于是否是从状态中恢复，下面会具体分析
- 初始化序列化器 deserializer
```java
public void open(Configuration configuration) throws Exception {
    // 1. 确定 Offset 提交模式
    this.offsetCommitMode = OffsetCommitModes.fromConfiguration(
          getIsAutoCommitEnabled(),
          enableCommitOnCheckpoints,
          ((StreamingRuntimeContext) getRuntimeContext()).isCheckpointingEnabled()
    );
    // 2. 创建分区发现器
    this.partitionDiscoverer = createPartitionDiscoverer(
          topicsDescriptor,
          getRuntimeContext().getIndexOfThisSubtask(),
          getRuntimeContext().getNumberOfParallelSubtasks()
    );
    this.partitionDiscoverer.open();

    // 3. 确定读取的 Partition 集合以及初始化读取的 Offset
    subscribedPartitionsToStartOffsets = new HashMap<>();
    final List<KafkaTopicPartition> allPartitions = partitionDiscoverer.discoverPartitions();
    // Offset 分配策略具体取决于是否是从状态中恢复
    if (restoredState != null) {
        // 如果是从状态中恢复
    } else {
        // 如果不是从状态中恢复
    }
    // 4. 序列化器
    this.deserializer.open(
          RuntimeContextInitializationContextAdapters.deserializationAdapter(
                  getRuntimeContext(),
                  metricGroup -> metricGroup.addGroup("user")
          )
    );
}
```
如果是从状态恢复中，那如何确定每个分区要读取的 Offset：
```java
// 如果是新分区则采用 EARLIEST_OFFSET 策略
for (KafkaTopicPartition partition : allPartitions) {
    if (!restoredState.containsKey(partition)) {
        restoredState.put(partition, KafkaTopicPartitionStateSentinel.EARLIEST_OFFSET);
    }
}
// 分区 Partition 分配策略 判断哪些 Partition 分配给该 Task
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
// 默认为 true
if (filterRestoredPartitionsWithCurrentTopicsDescriptor) {
    subscribedPartitionsToStartOffsets.entrySet().removeIf(
        entry -> {
            if (!topicsDescriptor.isMatchingTopic(entry.getKey().getTopic())) {
                return true;
            }
            return false;
        }
    );
}
```
首次运行：
```java
switch (startupMode) {
    case SPECIFIC_OFFSETS:
        if (specificStartupOffsets == null) {
            // 抛出 no specific offsets were specified 异常
        }
        for (KafkaTopicPartition seedPartition : allPartitions) {
            Long specificOffset = specificStartupOffsets.get(seedPartition);
            if (specificOffset != null) {
                // 由于指定的偏移量代表下一条要读取的记录，我们将其减一，以便消费者的初始状态是正确的
                subscribedPartitionsToStartOffsets.put(seedPartition, specificOffset - 1);
            } else {
                // 如果用户提供的特定偏移不包含此分区的值，则默认为 GROUP_OFFSET
                subscribedPartitionsToStartOffsets.put(seedPartition, KafkaTopicPartitionStateSentinel.GROUP_OFFSET);
            }
        }
        break;
    case TIMESTAMP:
        if (startupOffsetsTimestamp == null) {
            // 抛出 no startup timestamp was specified 异常
        }
        for (Map.Entry<KafkaTopicPartition, Long> partitionToOffset : fetchOffsetsWithTimestamp(allPartitions, startupOffsetsTimestamp).entrySet()) {
            Long offset = partitionToOffset.getValue() == null ? KafkaTopicPartitionStateSentinel.LATEST_OFFSET : partitionToOffset.getValue() - 1;
            subscribedPartitionsToStartOffsets.put(partitionToOffset.getKey(), offset);
        }

        break;
    default:
        for (KafkaTopicPartition seedPartition : allPartitions) {
            subscribedPartitionsToStartOffsets.put(seedPartition, startupMode.getStateSentinel());
        }
}

if (!subscribedPartitionsToStartOffsets.isEmpty()) {
    // 打印日志 输出不同 startupMode 下读取的分区 Partition
} else {
    // 打印日志 当前 Task 没有分区可以读取
}
```
#### 1.1.2 run

第一件事情就是初始化 Offset 提交 Metric 以及 Offset 回调方法：
```java
// 提交成功 Metric
this.successfulCommits = this.getRuntimeContext().getMetricGroup().counter(COMMITS_SUCCEEDED_METRICS_COUNTER);
// 提交失败 Metric                
this.failedCommits = this.getRuntimeContext().getMetricGroup().counter(COMMITS_FAILED_METRICS_COUNTER);
// Offset 提交回调
this.offsetCommitCallback =
        new KafkaCommitCallback() {
            @Override
            public void onSuccess() {
                // 提交成功
                successfulCommits.inc();
            }
            @Override
            public void onException(Throwable cause) {
                // 提交失败
                failedCommits.inc();
            }
        };
```
判断订阅 Partitin 是否有开始消费位置 Offset。如果没有，则会直接抛出异常；如果为空，则会将 SubTask 标记为暂时空闲，一旦该 SubTask 发现新分区并开始收集记录时，SubTask 的状态将自动触发回到活跃状态：
```java
if (subscribedPartitionsToStartOffsets == null) {
    throw new Exception("The partitions were not set for the consumer");
}

if (subscribedPartitionsToStartOffsets.isEmpty()) {
    sourceContext.markAsTemporarilyIdle();
}
```
创建 kafkaFetcher：
```java
this.kafkaFetcher = createFetcher(
      sourceContext,
      subscribedPartitionsToStartOffsets,
      watermarkStrategy,
      (StreamingRuntimeContext) getRuntimeContext(),
      offsetCommitMode,
      getRuntimeContext().getMetricGroup().addGroup(KAFKA_CONSUMER_METRICS_GROUP),
      useMetrics);
```
判断是否开启了动态发现新分区
```java
if (discoveryIntervalMillis == PARTITION_DISCOVERY_DISABLED) {
    kafkaFetcher.runFetchLoop();
} else {
    runWithPartitionDiscovery();
}
```



### 1.2 ResultTypeQueryable

ResultTypeQueryable 接口比较简单，只需要实现 getProducedType 方法返回序列化器的返回值数据类型信息即可：
```java
public TypeInformation<T> getProducedType() {
    return deserializer.getProducedType();
}
```
> deserializer 是 Kafka 的序列化器

### 1.3 CheckpointedFunction

需要实现 CheckpointedFunction 接口如下的两个方法：
```java
public interface CheckpointedFunction {
    void initializeState(FunctionInitializationContext context) throws Exception;
    void snapshotState(FunctionSnapshotContext context) throws Exception;
}
```

#### 1.3.1 initializeState

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

#### 1.3.2 snapshotState

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


### 1.4 CheckpointListener



## 2. FlinkKakfaConsumer




https://mp.weixin.qq.com/s/Y7DxI5qZUlLOr6AR9C4tqQ
https://mp.weixin.qq.com/s/oFpq5phikRIPb5dTbiOZpQ
https://mp.weixin.qq.com/s/oi88IWQ7IKZ_Por6CcQ1LA
https://mp.weixin.qq.com/s/q2uTHqB6em7pxiT_CqBfYA
