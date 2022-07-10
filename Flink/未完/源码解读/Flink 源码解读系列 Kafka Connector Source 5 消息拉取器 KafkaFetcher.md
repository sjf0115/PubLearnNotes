
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

```java
if (discoveryIntervalMillis == PARTITION_DISCOVERY_DISABLED) {
    kafkaFetcher.runFetchLoop();
} else {
    runWithPartitionDiscovery();
}
```

## 2. 消费线程 KafkaConsumerThread




https://www.cnblogs.com/Springmoon-venn/p/13614670.html
https://www.jianshu.com/p/5e349967679d










...
