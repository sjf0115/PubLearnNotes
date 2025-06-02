> Flink 1.13.6

Apache Flink 与 Kafka 的深度集成是实时流处理的核心场景之一。在 Flink 1.13.6 中，FlinkKafkaConsumer 和 FlinkKafkaProducer 提供了灵活的 Offset 提交机制，直接关系到 Exactly-Once 语义的实现与系统可靠性。本文将深入解析 Offset 提交模式的工作原理及最佳实践。

## 1. Offset 提交模式的核心作用

在 `Flink` 消费 `Kafka` 数据时，`Offset` 提交模式决定了何时将消费进度（Offset）提交到 Kafka Broker/Zookeeper。其核心目标是：
- 容错恢复：任务重新启动时从提交的 Offset 恢复消费，避免数据丢失或重复。
- 语义保障：与 Flink Checkpoint 机制协作，实现 Exactly-Once 或 At-Least-Once 语义。
- 监控可见性：外部系统（如 Kafka 监控工具）可通过提交的 Offset 实时观测消费进度。

## 2. 工作原理

`Flink` 为我们提供了三种提交模式：
```java
public enum OffsetCommitMode {
    DISABLED,
    ON_CHECKPOINTS,
    KAFKA_PERIODIC;
}
```
这三种模式决定了 `Offset` 如何从外部提交回 Kafka Broker/Zookeeper：
- `ON_CHECKPOINTS`：在开启 `Checkpoint` 时，当 `Checkpoint` 完成时将 `Offset` 提交回 `Kafka`
- `KAFKA_PERIODIC`：使用 `Kafka` 的自动提交功能，定期将 `Offset` 提交回 `Kafka`
- `DISABLED`：完全禁用 `Offset` 提交回 `Kafka`

下面详细介绍 `OffsetCommitMode` 提交模式是如何生成的。`OffsetCommitMode` 提交模式是在 `FlinkKafkaConsumerBase#open` 方法中初始化的：
```java
this.offsetCommitMode = OffsetCommitModes.fromConfiguration(
  getIsAutoCommitEnabled(),
  enableCommitOnCheckpoints,
  ((StreamingRuntimeContext) getRuntimeContext()).isCheckpointingEnabled()
);
```
从上面可以看出 `offsetCommitMode` 由三方面共同决定：
- `getIsAutoCommitEnabled()`
- `enableCommitOnCheckpoints`
- `isCheckpointingEnabled()`

### 2.1 Kafka 是否开启自动提交

提交模式的第一个影响方面 `getIsAutoCommitEnabled()` 方法用来判断 `Kafka` 是否开启了自动提交功能：
```java
protected boolean getIsAutoCommitEnabled() {
    return getBoolean(properties, ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, true)
          && PropertiesUtil.getLong(properties, ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, 5000) > 0;
}
```
> FlinkKafkaConsumer#getIsAutoCommitEnabled

`Kafka` 是否开启自动提交 `Offset` 受 `Kafka` 的两个配置的影响：
- `ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG` 对应 Kafka 的 `enable.auto.commit` 配置参数
- `ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG` 对应 Kafka 的 `auto.commit.interval.ms` 配置参数

只有当 `enable.auto.commit` 为 `true` 并且 `auto.commit.interval.ms` 大于 0 时，`Kafka` 才会启动自动提交 `Offset` 的功能。

### 2.2 Checkpoint 完成时提交 Offset

提交模式的第二个影响方面 `enableCommitOnCheckpoints` 用来判断是否在 `Checkpoint` 完成时提交 `Offset`:
```java
private boolean enableCommitOnCheckpoints = true;
```
这是一个用户配置的参数，默认为 `true`，可以调用 `setCommitOffsetsOnCheckpoints` 方法来设置。需要注意的是这个参数不能决定最终 `Offset` 的提交模式，需要与其他两个方面因素一起来决定。此外只有当作业开启了 `Checkpoint` 时(代码中调用了 `env.enableCheckpointing` 方法)，这个配置才有效。

### 2.3 是否开启了 Checkpoint

提交模式的第三个影响方面 `isCheckpointingEnabled()` 用来判断 `Flink` 作业是否开启了 `Checkpoint`。上面我们说到只有当作业开启了 `Checkpoint` 时(代码中调用了 `env.enableCheckpointing` 方法)，第二个影响方面才会生效。

### 2.4 提交模式如何决定

那么这三个影响方面是如何决定最终的提交模式呢？下面我们看一下 `OffsetCommitModes.fromConfiguration` 是如何根据传入的三个参数来初始化提交模式`offsetCommitMode`：
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
- 如果在代码中开启了 `Checkpoint`，那么 `Offset` 的提交模式取决于是否开启了在 `Checkpoint` 时自动提交 `Offset`。如果开启了则提交模式为 `ON_CHECKPOINTS`，否则为 `DISABLED`。
- 如果在代码中没有开启 `Checkpoint`，那么 `Offset` 的提交模式取决于 Kafka 属性中是否配置了自动提交 `Offset` 参数。如果配置了 `enable.auto.commit=true` 并且 `auto.commit.interval.ms > 0` 那么提交模式就是 `KAFKA_PERIODIC`，否则就是 `DISABLED`。

## 3. 提交模式详解

| 提交模式 | 触发条件 | 控制方 | 典型语义 |
| :------------- | :------------- | :------------- | :------------- |
| ON_CHECKPOINTS | Checkpoint 成功时提交 | Flink 框架 | Exactly-Once |
| KAFKA_PERIODIC | Kafka 客户端周期性自动提交 | Kafka Consumer | At-Least-Once |
| DISABLED | 不提交 Offset | 无 | 无保障 |

### 3.1 Checkpoint 成功时提交模式

`ON_CHECKPOINTS` 模式是在 `Checkpoint` 成功时提交 `Offset`，其前提条件是开启了 `Checkpoint` 并在 `Checkpoint` 完成时自动提交 `Offset`：
- 开启 `Checkpoint`：`env.enableCheckpointing(5*1000);`
- 配置在 `Checkpoint` 时自动提交 Offset：
  - 默认为在 `Checkpoint` 时自动提交 `Offset`
  - 可以通过 `consumer.setCommitOffsetsOnCheckpoints(true);` 手动调整

```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 开启 Checkpoint 用于容错 每30s触发一次Checkpoint 实际不用设置的这么大
env.enableCheckpointing(30*1000);

// Kafka Consumer 配置
Properties consumerProps = new Properties();
consumerProps.put("bootstrap.servers", "localhost:9092");
consumerProps.put("group.id", "word-count");
// 关闭 Kafka 自动提交
consumerProps.put("enable.auto.commit", "false");

// 创建 Kafka Consumer
String consumerTopic = "word";
FlinkKafkaConsumer<String> consumer = new FlinkKafkaConsumer<>(consumerTopic, new SimpleStringSchema(), consumerProps);
// 默认为 true 可以不设置
consumer.setCommitOffsetsOnCheckpoints(true);

DataStreamSource<String> sourceStream = env.addSource(consumer);
```

工作原理：
- `Checkpoint` 触发时：Flink 将当前消费的所有分区的 Offset 保存到状态后端。
- `Checkpoint` 完成时：通过 `CheckpointListener.notifyCheckpointComplete()` 异步提交 `Offset` 到 `Kafka`。
- 故障恢复时：从最近成功的 `Checkpoint` 中恢复 `Offset`，保证数据精确一次处理。

优点：
- `Exactly-Once` 语义：`Offset` 提交与 `Checkpoint` 严格对齐。
- 外部可见性：提交的 `Offset` 反映实际处理进度（适合监控）。
- 低重复风险：仅在 `Checkpoint` 成功时提交，避免中间状态泄露。

缺点：
- 外部可见性延迟：Offset 提交间隔等于 Checkpoint 间隔（默认分钟级）。
- 性能开销：频繁 Checkpoint 可能影响吞吐量。

### 2.2 Kafka 周期性自动提交模式

> 生产环境不建议使用

周期性自动提交 `KAFKA_PERIODIC` 模式的前提条件是未开启 `Checkpoint` 并在 `Kafka` 属性参数中配置了自动提交 `Offset` 的参数（`enable.auto.commit=true` 并且 `auto.commit.interval.ms > 0`）。配置如下所示：
```java
Properties consumerProps = new Properties();
consumerProps.setProperty("bootstrap.servers", "localhost:9092");
consumerProps.setProperty("group.id", "word-count");
consumerProps.setProperty("enable.auto.commit", "true");
consumerProps.setProperty("auto.commit.interval.ms", "5000"); // 每 5 秒提交一次
```

工作原理：
- Kafka 客户端后台线程定期提交 `Offset`（与 Flink Checkpoint 无关）。
- 依赖 Kafka 客户端自动提交（auto.commit.interval.ms 控制间隔）
- 任务失败时，可能从最后一次自动提交的 `Offset` 恢复，导致数据重复或丢失。

优点：
- 实时可见性：`Offset` 高频更新，便于监控工具追踪。
- 低延迟提交：适合对消费延迟敏感的监控场景。

缺点：
- 只能提供 `At-Least-Once` 语义：已提交 `Offset` 可能超前于实际处理进度，导致故障时重复消费。
- 提交与处理进度脱节：Flink 恢复的 `Offset` 可能比 `Kafka` 提交的旧。

### 2.3 DISABLED 模式

通过上面的分析，有两种情况下会出现 DISABLED 模式：
- 一种是在开启 `Checkpoint` 情况下显式关闭 `Checkpoint` 完成时自动提交
- 一种是在未开启 `Checkpoint` 情况下关闭自动提交

#### 2.3.1 开启 Checkpoint

在开启 `Checkpoint` 情况下，如果未配置 `Checkpoint` 完成时自动提交 `Offset`，那么 Flink 不会将 `Offset` 提交回 `Kafka`。这种情况是由于户手动设置了 `setCommitOffsetsOnCheckpoints(false)` 显式关闭 `Checkpoint` 完成时自动提交。配置如下所示:
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 开启 Checkpoint
env.enableCheckpointing(30*1000);

// Kafka Consumer 配置
Properties consumerProps = new Properties();
consumerProps.setProperty("bootstrap.servers", "localhost:9092");
consumerProps.setProperty("group.id", "word-count");

// 创建 Kafka Consumer
String consumerTopic = "word";
FlinkKafkaConsumer<String> consumer = new FlinkKafkaConsumer<>(consumerTopic, new SimpleStringSchema(), consumerProps);
// 显式关闭 `Checkpoint` 完成时自动提交
consumer.setCommitOffsetsOnCheckpoints(false);
```

#### 2.3.2 未开启 Checkpoint

在未开启 `Checkpoint` 情况下，如果 `Kafka` 属性参数中没有配置自动提交 `Offset` 的参数（`enable.auto.commit=true` 并且 `auto.commit.interval.ms > 0`），即关闭了自动提交，那么 `Flink` 不会将 `Offset` 提交回 `Kafka`。配置如下所示：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

// Kafka Consumer 配置
Properties consumerProps = new Properties();
consumerProps.setProperty("bootstrap.servers", "localhost:9092");
consumerProps.setProperty("group.id", "word-count");
consumerProps.setProperty("enable.auto.commit", "false");

// 创建 Kafka Consumer
String consumerTopic = "word";
FlinkKafkaConsumer<String> consumer = new FlinkKafkaConsumer<>(consumerTopic, new SimpleStringSchema(), consumerProps);
```

kafka 官方文档中，提到当 `enable.auto.commit=false` 时候需要手动提交 `offset`，也就是需要调用 `consumer.commitSync();` 方法提交。但是在 `flink` 中，非 `checkpoint` 模式下，不会调用 `consumer.commitSync();`， 这意味着一旦关闭自动提交，kafka 不知道当前的 consumer group 每次消费到了哪。

## 3. 最佳实践

在生产环境 Exactly-Once 场景推荐配置如下所示:
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 开启 Checkpoint 用于容错 每30s触发一次Checkpoint 实际不用设置的这么大
env.enableCheckpointing(30*1000);
// EXACTLY_ONCE 语义
env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);

// 配置失败重启策略：失败后最多重启3次 每次重启间隔10s
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(3, 10000));

// Kafka Consumer 配置
Properties consumerProps = new Properties();
consumerProps.put("bootstrap.servers", "localhost:9092");
consumerProps.put("group.id", "word-count");
// 关闭 Kafka 自动提交
consumerProps.put("enable.auto.commit", "false");

// 创建 Kafka Consumer
String consumerTopic = "word";
FlinkKafkaConsumer<String> consumer = new FlinkKafkaConsumer<>(consumerTopic, new SimpleStringSchema(), consumerProps);
// 默认为 true 可以不设置
consumer.setCommitOffsetsOnCheckpoints(true);
```



### 3.2 关键参数调优

| 参数 | 建议值 | 说明 |
| -------- | -------- | -------- |
| checkpointing.interval | 1-5 分钟 | 根据吞吐量调整，避免过频影响性能 |
| auto.commit.interval.ms | 禁用（false）| 确保不与 Checkpoint 提交冲突 |
| transaction.timeout.ms | ≥ Checkpoint 间隔| 防止 Kafka 事务超时 |
