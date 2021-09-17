
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

getIsAutoCommitEnabled() 方法实现如下：
```java
protected boolean getIsAutoCommitEnabled() {
return getBoolean(properties, ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, true)
        && PropertiesUtil.getLong(
                        properties, ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, 5000)
                > 0;
}
```
从上面可以看出 ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG(对应 kafka 参数 enable.auto.commit) 为 true 并且 ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG(对应 kafka 参数 auto.commit.interval.ms) > 0 时，这个方法才会返回 true。

enableCommitOnCheckpoints 默认为 true，可以调用 setCommitOffsetsOnCheckpoints 方法改变这个值。当代码中调用了 env.enableCheckpointing 方法时，isCheckpointingEnabled 才会返回true。

下面我们看一下 OffsetCommitModes.fromConfiguration 是如何根据传入的三个参数来初始化 offsetCommitMode：
```java
public static OffsetCommitMode fromConfiguration(
        boolean enableAutoCommit,
        boolean enableCommitOnCheckpoint,
        boolean enableCheckpointing) {
    if (enableCheckpointing) {
        // if checkpointing is enabled, the mode depends only on whether committing on
        // checkpoints is enabled
        return (enableCommitOnCheckpoint)
                ? OffsetCommitMode.ON_CHECKPOINTS
                : OffsetCommitMode.DISABLED;
    } else {
        // else, the mode depends only on whether auto committing is enabled in the provided
        // Kafka properties
        return (enableAutoCommit) ? OffsetCommitMode.KAFKA_PERIODIC : OffsetCommitMode.DISABLED;
    }
}
```
- 如果在代码中开启了 Checkpoint，那么 Offset 的提交模式只取决于在 Checkpoint 时是否开启了自动提交 Offset。如果是提交模式为 ON_CHECKPOINTS，否则为 DISABLED。
- 如果在代码中没有开启 Checkpoint，那么 Offset 的提交模式只取决于 Kafka 属性中是否配置了自动提交 Offset。如果配置了 enable.auto.commit=true 并且 auto.commit.interval.ms > 0 那么提交模式就是 KAFKA_PERIODIC，否则就是 DISABLED。

| 开启 Checkpoint | 开启 Checkpoint 时提交 Offset | Kafka 自动提交 Offset | 是否提交 Offset | 提交模式 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| 是 | 是 | 无所谓 | 是 | ON_CHECKPOINTS |
| 是 | 否 | 无所谓 | 否 | DISABLED |
| 否 | 无所谓 | 是 | 是 | KAFKA_PERIODIC |
| 否 | 无所谓 | 否 | 否 | DISABLED |

### 2. 未开启 Checkpoint 下 Offset 提交

未开启 Checkpoint 下，OffsetCommitMode 提交模式只取决于：
```java
(enableAutoCommit) ? OffsetCommitMode.KAFKA_PERIODIC : OffsetCommitMode.DISABLED
```
如果配置了 enable.auto.commit=true 并且 auto.commit.interval.ms > 0 那么提交模式就是 KAFKA_PERIODIC，否则就是 DISABLED。

#### 2.1 DISABLED

通过上面的分析，如果 enable.auto.commit = false，那么 offsetCommitMode 就是 DISABLED 。

kafka 官方文档中，提到当 enable.auto.commit=false 时候需要手动提交 offset，也就是需要调用 consumer.commitSync(); 方法提交。

但是在 flink 中，非 checkpoint 模式下，不会调用 consumer.commitSync();， 一旦关闭自动提交，意味着 kafka 不知道当前的 consumer group 每次消费到了哪。


#### 2.2 KAFKA_PERIODIC



...
