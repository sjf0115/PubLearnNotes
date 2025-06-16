## 1. 架构

不同 Kafka 版本实现的 FlinkKafkaConsumer 都基于 FlinkKafkaConsumerBase 这个抽象类。在 FlinkKafkaConsumerBase 中，它的主要负责初始化一些列对象来构建KafkaFetcher，用于获取 Kafka 上面的数据，如果开启了 Partition Discoverer 功能，则启动 DiscoveryLoopThread 定期获取 KafkaTopicPartition 信息。并将这些信息更新到 KafkaFetcher 中，从而获取新的 Topic 或 Partition 数据。

在 KafkaFetcher 里，它并没有直接使用 KafkaClient 进行直接的数据读取，它通过创建了一条 KafkaConsumerThread 线程定时 ( flink.poll-timeout, default 100ms) 的从 Kafka 拉取数据, 并调用 Handover.produce 将获取到的 Records 放到 Handover中，对于 Handover 来说，它相当于一个阻塞对列，KafkaFetcher 线程和 KafkaConsumerThread 线程通过 Handover 进行通信，KafkaFetcher 线程的 run 方法中轮询 handover.pollNext 获取来自KafkaConsumerThread 的数据，否则则阻塞，如果获取到数据，则通过 SourceContext 将数据 emit 到下游

### 1.1 FlinkKafkaConsumer

```java
public class FlinkKafkaConsumer<T> extends FlinkKafkaConsumerBase<T> {
  //
}
```

### 1.2 FlinkKafkaConsumerBase

`FlinkKakfaConsumerBase` 需要实现 3 个接口 `ResultTypeQueryable`、`CheckpointedFunction`、`CheckpointListener` 以及派生 1 个抽象类 `RichParallelSourceFunction`：

```java
public class FlinkKafkaConsumerBase<T> extends RichParallelSourceFunction<T>  implements CheckpointListener, CheckpointedFunction, ResultTypeQueryable<T> {
    // 1. 构造器
    public FlinkKafkaConsumerBase2(List<String> topics, Pattern topicPattern,
            KafkaDeserializationSchema<T> deserializer, long discoveryIntervalMillis, boolean useMetrics) {
        //
    }

    // 2. ResultTypeQueryable
    @Override
    public TypeInformation<T> getProducedType() {
        // 返回类型
        return null;
    }

    // 3. RichParallelSourceFunction
    @Override
    public void open(Configuration parameters) throws Exception {
        // 初始化资源
    }

    @Override
    public void close() throws Exception {
        // 释放资源
    }

    @Override
    public void run(SourceContext<T> ctx) throws Exception {
        // 拉取数据
    }

    @Override
    public void cancel() {
        // 取消拉取数据
    }

    // 4. CheckpointListener
    @Override
    public void notifyCheckpointComplete(long checkpointId) throws Exception {
        // 通知检查点完成
    }

    @Override
    public void notifyCheckpointAborted(long checkpointId) throws Exception {
        // 通知检查点取消
    }

    // 5. CheckpointedFunction
    @Override
    public void snapshotState(FunctionSnapshotContext context) throws Exception {
        // 快照状态
    }
    @Override
    public void initializeState(FunctionInitializationContext context) throws Exception {
        // 初始化状态
    }
}
```



## 2. 核心实现

### 2.1 构造器

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

### 2.2 ResultTypeQueryable

`ResultTypeQueryable` 接口比较简单，只需要实现 `getProducedType` 方法返回序列化器的返回值数据类型信息即可：
```java
// 用于 Kafka 字节消息与 Flink 对象之间转换的序列化器
protected final KafkaDeserializationSchema<T> deserializer;

public TypeInformation<T> getProducedType() {
    return deserializer.getProducedType();
}
```
> deserializer 是 Kafka 的序列化器，再构造函数中传入。


### 2.3 RichParallelSourceFunction

生命周期管理与数据拉取。

#### 2.3.1 Open

`RichParallelSourceFunction` 的 `Open` 方法主要用来初始化如下几个工作：
- 确定 Offset 的提交模式 `offsetCommitMode`
- 创建 Partition 分区发现器 `partitionDiscoverer`
- 根据启动模式以及是否是状态恢复来确定消费位点 Offset

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

#### 2.3.2 close

```java
// 1. 取消数据拉取
cancel();

// 2.
joinDiscoveryLoopThread();

// 3. 关闭分区发现器
if (partitionDiscoverer != null) {
    try {
        partitionDiscoverer.close();
    } catch (Exception e) {
        exception = e;
    }
}
```

#### 2.3.3 cancel

```java
// 1. 取消数据拉取
running = false;

// 2.
if (discoveryLoopThread != null) {
    if (partitionDiscoverer != null) {
        partitionDiscoverer.wakeup();
    }
    discoveryLoopThread.interrupt();
}

// 3. 取消消息拉取器
if (kafkaFetcher != null) {
    kafkaFetcher.cancel();
}
```

#### 2.3.4 run

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


### 2.4 CheckpointedFunction

需要实现 CheckpointedFunction 接口如下的两个方法：
```java
public interface CheckpointedFunction {
    void initializeState(FunctionInitializationContext context) throws Exception;
    void snapshotState(FunctionSnapshotContext context) throws Exception;
}
```

#### 2.4.1 initializeState

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

#### 2.4.2 snapshotState

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


### 2.5 CheckpointListener

#### 2.5.1

```java
public final void notifyCheckpointComplete(long checkpointId) throws Exception {
if (!running) {
LOG.debug("notifyCheckpointComplete() called on closed source");
return;
}

final AbstractFetcher<?, ?> fetcher = this.kafkaFetcher;
if (fetcher == null) {
LOG.debug("notifyCheckpointComplete() called on uninitialized source");
return;
}

if (offsetCommitMode == OffsetCommitMode.ON_CHECKPOINTS) {
// only one commit operation must be in progress
if (LOG.isDebugEnabled()) {
LOG.debug(
"Consumer subtask {} committing offsets to Kafka/ZooKeeper for checkpoint {}.",
getRuntimeContext().getIndexOfThisSubtask(),
checkpointId);
}

try {
final int posInMap = pendingOffsetsToCommit.indexOf(checkpointId);
if (posInMap == -1) {
LOG.warn(
"Consumer subtask {} received confirmation for unknown checkpoint id {}",
getRuntimeContext().getIndexOfThisSubtask(),
checkpointId);
return;
}

@SuppressWarnings("unchecked")
Map<KafkaTopicPartition, Long> offsets =
(Map<KafkaTopicPartition, Long>) pendingOffsetsToCommit.remove(posInMap);

// remove older checkpoints in map
for (int i = 0; i < posInMap; i++) {
pendingOffsetsToCommit.remove(0);
}

if (offsets == null || offsets.size() == 0) {
LOG.debug(
"Consumer subtask {} has empty checkpoint state.",
getRuntimeContext().getIndexOfThisSubtask());
return;
}

fetcher.commitInternalOffsetsToKafka(offsets, offsetCommitCallback);
} catch (Exception e) {
if (running) {
throw e;
}
// else ignore exception if we are no longer running
}
}
}
```
