
### 1. Offset提交模式

```java
public enum OffsetCommitMode {
    DISABLED,
    ON_CHECKPOINTS,
    KAFKA_PERIODIC;
}
```
OffsetCommitMode 提供了三种 Offset 从外部提交回 Kafka brokers / Zookeeper 的模式：
- DISABLED：开启 Checkpoint 但关闭 Offset 的自动提交
- ON_CHECKPOINTS：开启 Checkpoint，在完成 Checkpoint 时提交 Offset
- KAFKA_PERIODIC：使用内部Kafka客户机的自动提交功能，定期将偏移量提交回Kafka

在 FlinkKafkaConsumerBase#open 方法中初始化 offsetCommitMode：
```java
this.offsetCommitMode = OffsetCommitModes.fromConfiguration(
  getIsAutoCommitEnabled(),
  enableCommitOnCheckpoints,
  ((StreamingRuntimeContext) getRuntimeContext()).isCheckpointingEnabled()
);
```
从上面可以看出 offsetCommitMode 受到三个参数的影响：
- getIsAutoCommitEnabled()
- enableCommitOnCheckpoints
- isCheckpointingEnabled()

```java
protected boolean getIsAutoCommitEnabled() {
return getBoolean(properties, ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, true)
        && PropertiesUtil.getLong(
                        properties, ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, 5000)
                > 0;
}
```
从上面可以看出 ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG(对应 kafka 参数 enable.auto.commit) 为 true 并且 ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG(对应 kafka 参数 auto.commit.interval.ms) >0 这个方法才会返回 true。

enableCommitOnCheckpoints 默认为 true，可以调用 setCommitOffsetsOnCheckpoints 方法改变这个值。

当代码中调用了env.enableCheckpointing方法，isCheckpointingEnabled才会返回true








...
