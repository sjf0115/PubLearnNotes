---
layout: post
author: sjf0115
title: Flink DataStream FlinkKafkaProducer 系列 1：快速入门
date: 2024-03-01 10:30:00
tags:
  - Flink
categories: Flink
permalink: /flink/datastream/flink-kafka-producer-quick-start
---

> 基于 Flink 1.13.6 版本源码

Kafka 是 Flink 在生产环境中最常用的下游存储之一，几乎所有 Flink 实时数仓、CDC 数据回流、监控告警等链路最终都会把结果写回 Kafka。Flink 官方提供的 `FlinkKafkaProducer` 既屏蔽了 Kafka Producer 的复杂细节，又通过两阶段提交协议把端到端的 Exactly-Once 一致性带给了用户。

本文是 **FlinkKafkaProducer 系列** 的第 1 篇，定位是"快速入门"，目标是让你在 30 分钟内：
- 搞清楚 `FlinkKafkaProducer` 在数据流中的位置、整体架构与类层次
- 引入正确的 Maven 依赖
- 掌握三个最常用构造器的差别
- 跑通一个最小可用的 Demo
- 理解为什么必须显式设置 `transaction.timeout.ms`
- 在 DataStream 与 SQL Connector 之间做出正确选型

## 1. FlinkKafkaProducer 在 Flink 数据流中的位置

一个典型的 Flink 作业由 Source、若干 Operator、Sink 三部分组成。`FlinkKafkaProducer` 属于 **Sink Operator**，承担把上游算子产生的元素以 Kafka 消息的形式写出到指定 Topic 的职责。

```
+--------+      +-----------+      +--------------------+      +-------+
| Source | ---> | Operators | ---> | FlinkKafkaProducer | ---> | Kafka |
+--------+      +-----------+      +--------------------+      +-------+
```

它的核心职责包括：
- **序列化**：把 Flink 内部的 Java/Scala 对象序列化成 Kafka 可识别的 `byte[]` Key/Value
- **分区路由**：决定每条消息落到目标 Topic 的哪个分区
- **可靠投递**：根据用户选择的语义（At-Most-Once / At-Least-Once / Exactly-Once），与 Checkpoint 协作保证投递一致性
- **故障恢复**：作业失败重启后，重新建立 Producer、提交或回滚未完成的事务

## 2. 类层次结构

> 从 SinkFunction 一路到 FlinkKafkaProducer

`FlinkKafkaProducer` 并不是凭空出现的，它建立在 Flink 一整套 Sink 抽象之上。完整的继承关系如下：
```
SinkFunction<IN>                                    // 顶层接口：定义 invoke()
        ↑
RichSinkFunction<IN>                                // 提供 open()/close()/RuntimeContext
        ↑
TwoPhaseCommitSinkFunction<IN, TXN, CONTEXT>        // 实现两阶段提交骨架
        ↑
FlinkKafkaProducer<IN>                              // 把 TXN 具体化为 KafkaTransactionState
```

每一层都解决一个特定问题：

| 层 | 关键能力 | 关键源码 |
|---|---|---|
| `SinkFunction` | 定义最基础的 `invoke(value, context)` | [`SinkFunction.java`](https://github.com/apache/flink/blob/release-1.13/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/functions/sink/SinkFunction.java) |
| `RichSinkFunction` | 引入生命周期方法和 `RuntimeContext`，使 Sink 可以拿到子任务编号、并行度、Metric 等运行时信息 | [`RichSinkFunction.java`](https://github.com/apache/flink/blob/release-1.13/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/functions/sink/RichSinkFunction.java) |
| `TwoPhaseCommitSinkFunction` | 实现 2PC（Two-Phase Commit）骨架：`beginTransaction` / `invoke` / `preCommit` / `commit` / `abort` | [`TwoPhaseCommitSinkFunction.java`](https://github.com/apache/flink/blob/release-1.13/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/functions/sink/TwoPhaseCommitSinkFunction.java) |
| `FlinkKafkaProducer` | 把抽象 `TXN` 具化为 `KafkaTransactionState`（持有 `transactionalId` 与底层 Producer），把 `commit` 映射为 `producer.commitTransaction()` | [`FlinkKafkaProducer.java`](https://github.com/apache/flink/blob/release-1.13/flink-connectors/flink-connector-kafka/src/main/java/org/apache/flink/streaming/connectors/kafka/FlinkKafkaProducer.java) |

正是这种"接口—骨架—实现"的分层设计，让 Flink 的 Exactly-Once 语义可以在 Kafka、文件系统、HBase 等多种 Sink 之间复用一套两阶段提交框架。

## 3. Maven 依赖

Flink 1.13.6 的 Kafka Connector 已经合入主仓库，直接引入即可：
```xml
<properties>
    <flink.version>1.13.6</flink.version>
    <scala.binary.version>2.12</scala.binary.version>
</properties>

<dependencies>
    <!-- Flink Streaming -->
    <dependency>
        <groupId>org.apache.flink</groupId>
        <artifactId>flink-streaming-java_${scala.binary.version}</artifactId>
        <version>${flink.version}</version>
    </dependency>

    <!-- Flink Kafka Connector -->
    <dependency>
        <groupId>org.apache.flink</groupId>
        <artifactId>flink-connector-kafka_${scala.binary.version}</artifactId>
        <version>${flink.version}</version>
    </dependency>
</dependencies>
```

Flink 1.13 之后官方维护的是 **单一 Universal Kafka Connector**（基于 Kafka Client 2.4.1 编译），不再像早期那样区分 `flink-connector-kafka-0.10`、`flink-connector-kafka-0.11`。它向后兼容到 Kafka Broker 0.10+，绝大多数生产场景直接使用即可。

## 4. 三个最常用的构造器

打开 `FlinkKafkaProducer` 源码，会发现重载非常多（共有 10 余个），但生产场景里真正高频使用的是下面三个：

### 4.1 最简形式：仅指定 Topic + ValueSchema

```java
public FlinkKafkaProducer(String topicId, SerializationSchema<IN> serializationSchema, Properties producerConfig)
```

- 默认语义：**AT_LEAST_ONCE**
- 默认分区器：**`FlinkFixedPartitioner`**。将每个 Sink 子任务映射到单个 Kafka 分区（即，由一个 Sink 子任务接收的所有记录最终都会进入同一个 Kafka 分区）。
- 仅写入 Value，不写入 Kafka 消息 Key

适用于"把字符串日志一股脑写到一个固定 Topic"这类最简单的场景。

### 4.2 自定义分区器

```java
public FlinkKafkaProducer(
        String topicId,
        SerializationSchema<IN> serializationSchema,
        Properties producerConfig,
        Optional<FlinkKafkaPartitioner<IN>> customPartitioner)
```

通过 `Optional.empty()` 可以 **关闭** Flink 自带分区器，回退到 KafkaProducer 默认的 hash 分区行为。这点常常被忽略——传 `null` 是不行的，必须用 `Optional.empty()`。

### 4.3 完整形式：支持 Exactly-Once 与 KafkaSerializationSchema

```java
public FlinkKafkaProducer(
        String defaultTopic,
        KafkaSerializationSchema<IN> serializationSchema,
        Properties producerConfig,
        FlinkKafkaProducer.Semantic semantic)
```

- **`KafkaSerializationSchema`**：可以自定义 Key、Value、Headers 甚至动态决定 Topic（详见本系列第 2 篇）
- **`Semantic`**：枚举三选一 `NONE` / `AT_LEAST_ONCE` / `EXACTLY_ONCE`（详见本系列第 4 篇）

生产环境中如果要追求 Exactly-Once 或者写入复杂消息结构，几乎都会用这个构造器。

## 5. 第一个示例：5 分钟跑通端到端写入

下面这个例子模拟一个有界数据源，每秒产生一条字符串，使用 `FlinkKafkaProducer` 写入到 Kafka 的 `flink-quickstart` Topic：
```java
public class KafkaProducerQuickStart {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(2);
        env.enableCheckpointing(60_000L);

        // 1. 数据源：每秒一条字符串
        DataStream<String> stream = env.addSource(new SourceFunction<String>() {
            private volatile boolean running = true;
            @Override
            public void run(SourceContext<String> ctx) throws Exception {
                long i = 0;
                while (running) {
                    ctx.collect("msg-" + (i++));
                    Thread.sleep(1000L);
                }
            }
            @Override
            public void cancel() { running = false; }
        });

        // 2. 配置 Kafka Producer
        Properties props = new Properties();
        props.setProperty(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        // 注意：这里只是 AT_LEAST_ONCE 的最小例子，EXACTLY_ONCE 还需要更多配置
        // 见本文 6.2 章节

        // 3. 构建 FlinkKafkaProducer
        FlinkKafkaProducer<String> producer = new FlinkKafkaProducer<>(
                "flink-quickstart",
                new SimpleStringSchema(),
                props
        );

        stream.addSink(producer).name("kafka-sink");
        env.execute("KafkaProducerQuickStart");
    }
}
```

启动作业后，在 Kafka 消费端检查：

```bash
kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic flink-quickstart --from-beginning
```

应当能看到持续产出的 `msg-0`、`msg-1`、`msg-2` ……

## 6. 必填配置项与隐藏陷阱

入门看似简单，但真正在生产环境跑起来，下面两个配置是绕不开的"必填项"。

### 6.1 `bootstrap.servers`：唯一一个 Connector 强校验的属性

`FlinkKafkaProducer` 在构造时会校验 `Properties` 是否至少包含 `bootstrap.servers`。如果没设，作业会在初始化阶段抛出：

```
IllegalArgumentException: bootstrap.servers must be supplied in the producer config.
```

### 6.2 `transaction.timeout.ms`：Exactly-Once 的"隐形必填"

很多用户在切换到 EXACTLY_ONCE 时遇到过这样的报错：

```
The configured timeout is larger than the maximum allowed transaction.timeout.ms
configured in the broker (default 900000ms).
```

这是因为：

- Kafka Broker 端 `transaction.max.timeout.ms` 默认 **15 分钟（900000ms）**
- Flink 侧 `FlinkKafkaProducer` 默认把 `transaction.timeout.ms` 设为 **1 小时（3600000ms）**

二者冲突，作业启动即失败。生产中通常这样配置：

```java
props.setProperty(
    ProducerConfig.TRANSACTION_TIMEOUT_CONFIG,
    String.valueOf(15 * 60 * 1000));  // 15 分钟，与 Broker 上限对齐
```

或反向调高 Broker 的 `transaction.max.timeout.ms`。这一点的根源会在系列第 5、第 7 篇详细展开。

### 6.3 其它常见但非必填的配置

| 配置项 | 默认值 | 推荐值 | 说明 |
|---|---|---|---|
| `acks` | `1`（普通模式）/ `all`（事务模式强制） | `all` | 控制副本确认级别 |
| `retries` | `2147483647` | 默认即可 | Producer 内部失败重试次数 |
| `enable.idempotence` | `false` / 事务模式下强制 `true` | `true` | 幂等 Producer，防止重试导致重复 |
| `compression.type` | `none` | `lz4` / `zstd` | 网络与磁盘成本敏感场景必开 |
| `batch.size` | `16384` | `65536` 起 | 高吞吐场景适当调大 |
| `linger.ms` | `0` | `5~50` | 攒批等待时间 |

详细调优方法会在第 6 篇展开。

## 7. 与 SQL Kafka Connector 的对比定位

很多团队会困惑：业务用 SQL Connector 一行 `INSERT INTO kafka_sink SELECT *` 就能搞定，为什么还要用 `FlinkKafkaProducer`？

| 维度 | DataStream `FlinkKafkaProducer` | SQL `kafka` Connector |
|---|---|---|
| 编程模型 | Java/Scala API，灵活 | Flink SQL DDL，声明式 |
| 自定义序列化 | 任意（`KafkaSerializationSchema`） | 局限于内置 Format（json/csv/avro/debezium-json…） |
| 自定义分区策略 | 任意 | 通过 `sink.partitioner` 配置（fixed/round-robin/自定义类全限定名） |
| Exactly-Once | 通过 `Semantic.EXACTLY_ONCE` | 通过 `sink.semantic = exactly-once` |
| 动态 Topic 路由 | 在 `KafkaSerializationSchema.serialize` 内决定 | 受限，需要 SQL 函数/表达式 |
| 调试与排错 | 直接读源码、断点 | 包了一层 Planner，链路较长 |
| 适用场景 | 复杂 ETL、自定义事务/状态、动态写入 | 标准化的 SQL 数仓、低代码 |

**经验法则**：

- 业务表结构稳定、能用 SQL 表达 → 优先选择 SQL Connector
- 需要动态决定 Topic、动态写 Headers、与第三方框架做复杂交互 → 选 DataStream `FlinkKafkaProducer`

## 8. 本篇小结

通过本篇你应该已经具备：

1. 用最少的代码把 Flink 数据写入 Kafka 的能力
2. 对 `FlinkKafkaProducer` 类层次的整体认知
3. 知道 `transaction.timeout.ms` 与 Broker 上限对齐的重要性
4. 在 DataStream 与 SQL Connector 之间做合理选型

但是要把它真正用好，还有 **序列化、分区、语义、源码、实战、排错** 五个层次的内容等着我们逐篇展开。

## 系列文章导航

| 序号 | 文章 |
|---|---|
| 第 1 篇 | Flink DataStream FlinkKafkaProducer 系列 1：快速入门（本文） |
| 第 2 篇 | Flink DataStream FlinkKafkaProducer 系列 2：序列化机制 KafkaSerializationSchema 深度剖析 |
| 第 3 篇 | Flink DataStream FlinkKafkaProducer 系列 3：分区策略 FlinkKafkaPartitioner 与如何写入指定分区 |
| 第 4 篇 | Flink DataStream FlinkKafkaProducer 系列 4：三种交付语义 AT_MOST_ONCE / AT_LEAST_ONCE / EXACTLY_ONCE |
| 第 5 篇 | Flink DataStream FlinkKafkaProducer 系列 5：Exactly-Once 源码深度剖析 TwoPhaseCommitSinkFunction |
| 第 6 篇 | Flink DataStream FlinkKafkaProducer 系列 6：生产实战 性能调优 监控指标与高可用部署 |
| 第 7 篇 | Flink DataStream FlinkKafkaProducer 系列 7：常见错误排查 FAQ 与生产事故复盘 |
