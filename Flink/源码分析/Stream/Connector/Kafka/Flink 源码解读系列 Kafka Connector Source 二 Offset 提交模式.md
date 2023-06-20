
> Flink 1.13.5

这一篇文章我们主要聊一下 Flink Offset 是如何提交的。Flink 为我们提供了三种提交模式：
```java
public enum OffsetCommitMode {
    DISABLED,
    ON_CHECKPOINTS,
    KAFKA_PERIODIC;
}
```
OffsetCommitMode 提供的这三种模式将 Offset 从外部提交回 Kafka brokers / Zookeeper：
- DISABLED：开启 Checkpoint 但关闭 Offset 的自动提交
- ON_CHECKPOINTS：在开启 Checkpoint 时，当 Checkpoint 完成时提交 Offset
- KAFKA_PERIODIC：使用内部 Kafka 客户机的自动提交功能，定期将 Offset 提交回 Kafka

## 1. 初始化

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

提交模式的第一个影响参数 `getIsAutoCommitEnabled()` 方法用来判断 Kafka 是否开启了自动提交功能：
```java
protected boolean getIsAutoCommitEnabled() {
return getBoolean(properties, ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, true)
      && PropertiesUtil.getLong(properties, ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, 5000) > 0;
}
```
Kafka 是否自动提交 Offset 受 Kafka 的两个配置的影响：
- enable.auto.commit，对应 ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG
- auto.commit.interval.ms，对应 ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG
只有当 ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG 为 true 并且 ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG 大于 0 时，Kafka 才会启动自动提交 Offset 的功能。

提交模式的第二个影响参数 `enableCommitOnCheckpoints` 用来判断是否在 Checkpoint 时提交 Offset。这是一个用户配置的参数，这个参数不代表最终 Offset 的提交模式，需要与其他两个因素一起来决定。这个默认为 true，可以调用 `setCommitOffsetsOnCheckpoints` 方法来设置这个值。需要注意的是只有当作业开启了 Checkpoint 时(代码中调用了 env.enableCheckpointing 方法)，这个配置才有效。

提交模式的第三个影响参数 `isCheckpointingEnabled()` 用来判断 Flink 作业是否开启了 Checkpoint。上面我们说到只有当作业开启了 Checkpoint 时(代码中调用了 env.enableCheckpointing 方法)，第二个影响因素才会生效。

那么这三个影响参数是如何决定最终的提交模式呢？下面我们看一下 OffsetCommitModes.fromConfiguration 是如何根据传入的三个参数来初始化 offsetCommitMode：
```java
public static OffsetCommitMode fromConfiguration(boolean enableAutoCommit, boolean enableCommitOnCheckpoint, boolean enableCheckpointing) {
    if (enableCheckpointing) {
        return (enableCommitOnCheckpoint)
                ? OffsetCommitMode.ON_CHECKPOINTS
                : OffsetCommitMode.DISABLED;
    } else {
        return (enableAutoCommit) ? OffsetCommitMode.KAFKA_PERIODIC : OffsetCommitMode.DISABLED;
    }
}
```
可以看到：
- 如果在代码中开启了 Checkpoint，那么 Offset 的提交模式取决于是否开启了在 Checkpoint 时自动提交 Offset。如果是则提交模式为 `ON_CHECKPOINTS`，否则为 `DISABLED`。
- 如果在代码中没有开启 Checkpoint，那么 Offset 的提交模式取决于 Kafka 属性中是否配置了自动提交 Offset 参数。如果配置了 `enable.auto.commit=true` 并且 `auto.commit.interval.ms > 0` 那么提交模式就是 `KAFKA_PERIODIC`，否则就是 `DISABLED`。

| 开启 Checkpoint | 开启 Checkpoint 提交 Offset | Kafka 自动提交 Offset | 是否提交 Offset | 提交模式 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| 是 | 是 | 无所谓 | 是 | ON_CHECKPOINTS |
| 是 | 否 | 无所谓 | 否 | DISABLED |
| 否 | 无所谓 | 是 | 是 | KAFKA_PERIODIC |
| 否 | 无所谓 | 否 | 否 | DISABLED |

## 2. 提交模式

### 2.1 ON_CHECKPOINTS

从上面我们知道 ON_CHECKPOINTS 提交模式的前提条件是开启了 Checkpoint 并在 Checkpoint 时自动提交 Offset：
- 开启 Checkpoint：`env.enableCheckpointing(5*1000);`
- 配置在 Checkpoint 时自动提交 Offset：`consumer.setCommitOffsetsOnCheckpoints(true);`

### 2.2 KAFKA_PERIODIC

从上面我们知道 KAFKA_PERIODIC 提交模式的前提条件是未开启 Checkpoint 并在 Kafka 属性参数中配置了自动提交 Offset 的参数（`enable.auto.commit=true` 并且 `auto.commit.interval.ms > 0`）。

### 2.3 DISABLED

通过上面的分析，如果 enable.auto.commit = false，那么 offsetCommitMode 就是 DISABLED 。

kafka 官方文档中，提到当 enable.auto.commit=false 时候需要手动提交 offset，也就是需要调用 consumer.commitSync(); 方法提交。

但是在 flink 中，非 checkpoint 模式下，不会调用 consumer.commitSync();， 一旦关闭自动提交，意味着 kafka 不知道当前的 consumer group 每次消费到了哪。


#### 2.3.1 开启 Checkpoint

开启了 Checkpoint 但提交模式为 `DISABLED`，是由于未配置在 Checkpoint 时自动提交 Offset。


#### 2.3.2 未开启 Checkpoint

未开启 Checkpoint 下提交模式为 `DISABLED`，是由于在 Kafka 属性参数中没有配置自动提交 Offset 的参数（`enable.auto.commit=true` 并且 `auto.commit.interval.ms > 0`）。




...
