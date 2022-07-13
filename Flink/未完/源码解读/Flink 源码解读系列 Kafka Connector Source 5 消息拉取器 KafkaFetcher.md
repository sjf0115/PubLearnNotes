
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
调用 FlinkKafkaConsumer 的 createFetcher：
```java
protected AbstractFetcher<T, ?> createFetcher(
        SourceContext<T> sourceContext,
        Map<KafkaTopicPartition, Long> assignedPartitionsWithInitialOffsets,
        SerializedValue<WatermarkStrategy<T>> watermarkStrategy,
        StreamingRuntimeContext runtimeContext,
        OffsetCommitMode offsetCommitMode,
        MetricGroup consumerMetricGroup,
        boolean useMetrics)
        throws Exception {

    adjustAutoCommitConfig(properties, offsetCommitMode);

    return new KafkaFetcher<>(
            sourceContext,
            assignedPartitionsWithInitialOffsets,
            watermarkStrategy,
            runtimeContext.getProcessingTimeService(),
            runtimeContext.getExecutionConfig().getAutoWatermarkInterval(),
            runtimeContext.getUserCodeClassLoader(),
            runtimeContext.getTaskNameWithSubtasks(),
            deserializer,
            properties,
            pollTimeout,
            runtimeContext.getMetricGroup(),
            consumerMetricGroup,
            useMetrics
    );
}
```
## 1.1 构造器

```java
public KafkaFetcher(
        SourceFunction.SourceContext<T> sourceContext,
        Map<KafkaTopicPartition, Long> assignedPartitionsWithInitialOffsets,
        SerializedValue<WatermarkStrategy<T>> watermarkStrategy,
        ProcessingTimeService processingTimeProvider,
        long autoWatermarkInterval,
        ClassLoader userCodeClassLoader,
        String taskNameWithSubtasks,
        KafkaDeserializationSchema<T> deserializer,
        Properties kafkaProperties,
        long pollTimeout,
        MetricGroup subtaskMetricGroup,
        MetricGroup consumerMetricGroup,
        boolean useMetrics)
        throws Exception {
    super(
            sourceContext,
            assignedPartitionsWithInitialOffsets,
            watermarkStrategy,
            processingTimeProvider,
            autoWatermarkInterval,
            userCodeClassLoader,
            consumerMetricGroup,
            useMetrics);

    this.deserializer = deserializer;
    this.handover = new Handover();

    this.consumerThread =
            new KafkaConsumerThread(
                    LOG,
                    handover,
                    kafkaProperties,
                    unassignedPartitionsQueue,
                    getFetcherName() + " for " + taskNameWithSubtasks,
                    pollTimeout,
                    useMetrics,
                    consumerMetricGroup,
                    subtaskMetricGroup);
    this.kafkaCollector = new KafkaCollector();
}
```

```java
protected AbstractFetcher(
        SourceContext<T> sourceContext,
        Map<KafkaTopicPartition, Long> seedPartitionsWithInitialOffsets,
        SerializedValue<WatermarkStrategy<T>> watermarkStrategy,
        ProcessingTimeService processingTimeProvider,
        long autoWatermarkInterval,
        ClassLoader userCodeClassLoader,
        MetricGroup consumerMetricGroup,
        boolean useMetrics)
        throws Exception {
    this.sourceContext = checkNotNull(sourceContext);
    this.watermarkOutput = new SourceContextWatermarkOutputAdapter<>(sourceContext);
    this.watermarkOutputMultiplexer = new WatermarkOutputMultiplexer(watermarkOutput);
    this.checkpointLock = sourceContext.getCheckpointLock();
    this.userCodeClassLoader = checkNotNull(userCodeClassLoader);

    // Metric 指标
    this.useMetrics = useMetrics;
    this.consumerMetricGroup = checkNotNull(consumerMetricGroup);
    this.legacyCurrentOffsetsMetricGroup = consumerMetricGroup.addGroup(LEGACY_CURRENT_OFFSETS_METRICS_GROUP);
    this.legacyCommittedOffsetsMetricGroup = consumerMetricGroup.addGroup(LEGACY_COMMITTED_OFFSETS_METRICS_GROUP);
    // Watermark 策略
    this.watermarkStrategy = watermarkStrategy;
    if (watermarkStrategy == null) {
        timestampWatermarkMode = NO_TIMESTAMPS_WATERMARKS;
    } else {
        timestampWatermarkMode = WITH_WATERMARK_GENERATOR;
    }

    this.unassignedPartitionsQueue = new ClosableBlockingQueue<>();


    // initialize subscribed partition states with seed partitions
    this.subscribedPartitionStates =
            createPartitionStateHolders(
                    seedPartitionsWithInitialOffsets,
                    timestampWatermarkMode,
                    watermarkStrategy,
                    userCodeClassLoader);
    // check that all seed partition states have a defined offset
    for (KafkaTopicPartitionState<?, ?> partitionState : subscribedPartitionStates) {
        if (!partitionState.isOffsetDefined()) {
            throw new IllegalArgumentException(
                    "The fetcher was assigned seed partitions with undefined initial offsets.");
        }
    }

    // all seed partitions are not assigned yet, so should be added to the unassigned partitions
    // queue
    for (KafkaTopicPartitionState<T, KPH> partition : subscribedPartitionStates) {
        unassignedPartitionsQueue.add(partition);
    }

    // register metrics for the initial seed partitions
    if (useMetrics) {
        registerOffsetMetrics(consumerMetricGroup, subscribedPartitionStates);
    }

    // if we have periodic watermarks, kick off the interval scheduler
    if (timestampWatermarkMode == WITH_WATERMARK_GENERATOR && autoWatermarkInterval > 0) {
        PeriodicWatermarkEmitter<T, KPH> periodicEmitter =
                new PeriodicWatermarkEmitter<>(
                        checkpointLock,
                        subscribedPartitionStates,
                        watermarkOutputMultiplexer,
                        processingTimeProvider,
                        autoWatermarkInterval);

        periodicEmitter.start();
    }
}
```


### 1.2 runFetchLoop

```java
if (discoveryIntervalMillis == PARTITION_DISCOVERY_DISABLED) {
    kafkaFetcher.runFetchLoop();
} else {
    runWithPartitionDiscovery();
}
```

```java
try {
    // (1) 启动消费者线程 KafkaConsumerThread 底层本质是一个Kafka消费者
    consumerThread.start();
    // (2) 循环轮询
    while (running) {
        // 从 Handover 中获取 Kafka 消息 如果没有消息会被阻塞
        final ConsumerRecords<byte[], byte[]> records = handover.pollNext();

        // get the records for each topic partition
        for (KafkaTopicPartitionState<T, TopicPartition> partition : subscribedPartitionStates()) {
            List<ConsumerRecord<byte[], byte[]>> partitionRecords = records.records(partition.getKafkaPartitionHandle());
            partitionConsumerRecordsHandler(partitionRecords, partition);
        }
    }
} finally {
    // 退出消费者线程
    consumerThread.shutdown();
}
try {
    consumerThread.join();
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
}
```

### 1.3 runWithPartitionDiscovery


## 2. 消费线程 KafkaConsumerThread

### 2.1 run

第一个重要的事情是根据 Kafka 配置文件创建 Kafka 消费者 KafkaConsumer：
```java
try {
    this.consumer = getConsumer(kafkaProperties);
} catch (Throwable t) {
    handover.reportError(t);
    return;
}

KafkaConsumer<byte[], byte[]> getConsumer(Properties kafkaProperties) {
    return new KafkaConsumer<>(kafkaProperties);
}
```
第二件事情是注册 Kafka 监控指标到 Flink 中：
```java
if (useMetrics) {
    // 获取 Kafka 所有 Metric
    Map<MetricName, ? extends Metric> metrics = consumer.metrics();
    if (metrics == null) {
        // 没有只打印日志
        log.info("Consumer implementation does not support metrics");
    } else {
        // 有进行注册
        for (Map.Entry<MetricName, ? extends Metric> metric : metrics.entrySet()) {
            consumerMetricGroup.gauge(metric.getKey().name(), new KafkaMetricWrapper(metric.getValue()));
        }
    }
}
```
最核心的一件事情就是循环拉取 Kafka 中的消息：
```java
while (running) {
    // (1) 是否需要提交 Offset
    // (2) 是否分配 Partition，重新确认里分配的分区
    // (3) 从 Kafka 消费者中批量拉取消息并存储在 Handover 中
}
```
检查是否有需要提交 Offset：
```java
if (!commitInProgress) {
    // 每次获取并重置 确保每次不会提交相同的内容
    // nextOffsetsToCommit 是一个原子引用 AtomicReference
    final Tuple2<Map<TopicPartition, OffsetAndMetadata>, KafkaCommitCallback> commitOffsetsAndCallback = nextOffsetsToCommit.getAndSet(null);
    // 判断是否提交
    if (commitOffsetsAndCallback != null) {
        // 顺序很重要！首先设置标志，然后发送提交命令
        commitInProgress = true;
        consumer.commitAsync(commitOffsetsAndCallback.f0, new CommitCallback(commitOffsetsAndCallback.f1));
    }
}
```
CommitCallback 是一个回调函数，再提交 Offset 之后，设置标志位 commitInProgress 为 false，表示没有可以提交的 Offset。如果提交 Offset 时出现异常，调用 KafkaCommitCallback 的 onException 方法，如果没有异常则调用 onSuccess 方法。

重新确立分配的分区：
```java
try {
    if (hasAssignedPartitions) {
        // 如果有则取出所有元素
        newPartitions = unassignedPartitionsQueue.pollBatch();
    } else {
        // 如果没有则阻塞直到有一个元素
        newPartitions = unassignedPartitionsQueue.getBatchBlocking();
    }
    // 重新确立分配的分区。重新分配的分区由提供的新分区和之前已经分配给消费者的分区组成
    if (newPartitions != null) {
        reassignPartitions(newPartitions);
    }
} catch (AbortedReassignmentException e) {
    continue;
}

if (!hasAssignedPartitions) {
    // Without assigned partitions KafkaConsumer.poll will throw an exception
    continue;
}
```
从 Kafka 消费者中批量拉取消息，存储在 Handover 中间缓存中：
```java
if (records == null) {
    try {
        records = consumer.poll(pollTimeout);
    } catch (WakeupException we) {
        continue;
    }
}

try {
    handover.produce(records);
    // 注意 置 null，根据这个字段判断是否需要拉取消息
    records = null;
} catch (Handover.WakeupException e) {
    // fall through the loop
}
```
### 2.2 shutdown

```java
public void shutdown() {
    running = false;
    // wake up all blocking calls on the queue
    unassignedPartitionsQueue.close();
    // 不能在 KafkaConsumer 上调用 close()，因为如果有并发正在调用，会抛出异常
    // 调用 wakeupProducer 中断 produce 线程
    handover.wakeupProducer();
    // this wakes up the consumer if it is blocked in a kafka poll
    synchronized (consumerReassignmentLock) {
        if (consumer != null) {
            consumer.wakeup();
        } else {
            hasBufferedWakeup = true;
        }
    }
}
```

### 2.3

https://www.cnblogs.com/Springmoon-venn/p/13614670.html
https://www.jianshu.com/p/5e349967679d










...
