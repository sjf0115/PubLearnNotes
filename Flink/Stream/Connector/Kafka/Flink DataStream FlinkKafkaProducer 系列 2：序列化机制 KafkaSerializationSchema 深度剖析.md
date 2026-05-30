---
layout: post
author: sjf0115
title: Flink DataStream FlinkKafkaProducer 系列 2：序列化机制 KafkaSerializationSchema 深度剖析
date: 2024-03-02 10:30:00
tags:
  - Flink
categories: Flink
permalink: /flink/datastream/flink-kafka-producer-serialization-schema
---

> 基于 Flink 1.13.6 版本源码

[上一篇](./flink-kafka-producer-quick-start) 我们用 `SimpleStringSchema` 写出了第一条 Kafka 消息，但仅仅写出 Value 远远满足不了实际生产：分区路由要 Key、链路追踪要 Headers、多租户场景要动态路由 Topic、与下游消费方对齐要严格的 schema 演进策略——这些都依赖一套灵活的序列化机制。

本文聚焦 `FlinkKafkaProducer` 的序列化体系，回答四个问题：

- Flink 提供了哪几种序列化器？为什么是 `KafkaSerializationSchema`？
- 接口契约是什么？如何写入 Key、Value、Headers、动态 Topic？
- `KafkaSerializationSchemaWrapper` 是干什么的？
- JSON / Avro / Protobuf 在工程实践中如何接入？

## 1. 三种序列化器全景

打开 `FlinkKafkaProducer` 的构造器签名，会看到三种 SerSchema 类型反复出现：

| 接口 | 包路径 | 状态 | 能写 Key 吗 | 能写 Headers 吗 | 能动态 Topic 吗 |
|---|---|---|---|---|---|
| `SerializationSchema<T>` | `org.apache.flink.api.common.serialization` | 现役 | 否 | 否 | 否 |
| `KeyedSerializationSchema<T>` | `org.apache.flink.streaming.util.serialization` | **`@Deprecated`** | 是 | 否 | 是（getTargetTopic） |
| `KafkaSerializationSchema<T>` | `org.apache.flink.streaming.connectors.kafka` | 现役（推荐） | 是 | 是 | 是 |

### 1.1 SerializationSchema：最基础的"对象 → byte[]"

```java
public interface SerializationSchema<T> extends Serializable {
    default void open(InitializationContext context) throws Exception {}
    byte[] serialize(T element);
}
```

它是 Flink 通用的数据→字节序列化接口，**不感知 Kafka 的任何概念**。`FlinkKafkaProducer` 拿到这种 Schema 之后，会在内部把它包装成 `KafkaSerializationSchemaWrapper`（见第 5 章）来补齐 Topic、Partition、Headers 这些 Kafka 特有信息。

```java
DataStream<String> stream = ...;
stream.addSink(new FlinkKafkaProducer<>(
        "log-topic",
        new SimpleStringSchema(),     // SerializationSchema<String>
        producerProps));
```

**适用场景**：日志、指标这种"只关心 Value"的简单写入。

### 1.2 KeyedSerializationSchema：已废弃，了解即可

```java
@Deprecated
public interface KeyedSerializationSchema<T> extends Serializable {
    byte[] serializeKey(T element);
    byte[] serializeValue(T element);
    String getTargetTopic(T element);
}
```

它在 Flink 1.x 早期承担着"既能写 Key 又能动态 Topic"的角色，但是在 1.9 之后被官方 `@Deprecated`，原因有二：

1. **缺失 Headers**：随着 Kafka 0.11+ 把 Headers 列为一等公民，`KeyedSerializationSchema` 无法表达
2. **接口职责分散**：Key/Value/Topic 三个独立方法没有一个统一的 ProducerRecord 出口

**建议**：新代码**绝对不要再使用**。如果你接手了老代码，迁移路径是把它换成 `KafkaSerializationSchema`。

### 1.3 KafkaSerializationSchema：唯一推荐的接口

```java
@PublicEvolving
public interface KafkaSerializationSchema<T> extends Serializable {
    default void open(SerializationSchema.InitializationContext context) throws Exception {}
    ProducerRecord<byte[], byte[]> serialize(T element, @Nullable Long timestamp);
}
```

亮点有三个：

1. **直接产出 `ProducerRecord`**：用户掌握 Topic、Partition、Key、Value、Timestamp、Headers 的全部决定权
2. **`timestamp` 入参**：Flink 把元素的事件时间传进来，便于把事件时间写入 Kafka
3. **统一出口**：相比 `KeyedSerializationSchema` 的三个独立方法，认知负担更低

**这就是本文聚焦它的原因**——它是 Flink 1.13.6 中唯一现役、能力完备的 Kafka 序列化接口。

## 2. ProducerRecord：理解输出契约

`KafkaSerializationSchema.serialize()` 的返回值是 Kafka 客户端的 `ProducerRecord<byte[], byte[]>`，它的关键字段如下：

```java
public class ProducerRecord<K, V> {
    private final String topic;             // 目标 Topic
    private final Integer partition;        // 目标分区，可为 null（由分区器决定）
    private final Headers headers;          // 消息头
    private final K key;                    // 消息 Key（这里是 byte[]）
    private final V value;                  // 消息 Value（这里是 byte[]）
    private final Long timestamp;           // 消息时间戳
}
```

### 关于字段优先级

| 字段 | 给定 | 行为 |
|---|---|---|
| `partition` | 非 null | **直接写入指定分区**，绕过 Flink/Kafka 分区器 |
| `partition` | null | 走 `FlinkKafkaPartitioner` → 走 KafkaProducer 默认分区器 |
| `timestamp` | 非 null | 即使 `setWriteTimestampToKafka(false)` 也会被发送 |
| `timestamp` | null | 由 KafkaProducer 自动以发送时间填充 |

理解清楚优先级，可以避免"明明设置了分区器为什么不生效"这类经典疑惑。

## 3. 自定义实现：写入 Key + Value + Headers + 动态 Topic

下面是一个生产级例子：把订单流写入 Kafka，要求

- Key 用订单 ID
- Value 用 JSON
- Headers 携带链路追踪字段（trace-id）
- Topic 按业务线动态路由（如 `order-vip` / `order-normal`）

```java
public class OrderKafkaSchema implements KafkaSerializationSchema<Order> {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final String topicPrefix;

    public OrderKafkaSchema(String topicPrefix) {
        this.topicPrefix = topicPrefix;
    }

    @Override
    public ProducerRecord<byte[], byte[]> serialize(Order order, @Nullable Long timestamp) {
        try {
            // 1. 动态 Topic 路由
            String topic = topicPrefix + (order.isVip() ? "-vip" : "-normal");

            // 2. Key/Value 序列化
            byte[] key   = order.getOrderId().getBytes(StandardCharsets.UTF_8);
            byte[] value = MAPPER.writeValueAsBytes(order);

            // 3. 构建 ProducerRecord（partition 留 null 由分区器决定）
            ProducerRecord<byte[], byte[]> record =
                    new ProducerRecord<>(topic, null, timestamp, key, value);

            // 4. 注入 Headers（链路追踪）
            record.headers().add("trace-id",
                    order.getTraceId().getBytes(StandardCharsets.UTF_8));
            record.headers().add("source", "flink-job".getBytes(StandardCharsets.UTF_8));
            return record;
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize order " + order, e);
        }
    }
}
```

使用方式：

```java
FlinkKafkaProducer<Order> producer = new FlinkKafkaProducer<>(
        "order-default",                      // 默认 Topic（实际不用，serialize 内会覆盖）
        new OrderKafkaSchema("order"),
        props,
        FlinkKafkaProducer.Semantic.EXACTLY_ONCE);
orderStream.addSink(producer);
```

### 三个细节

1. **构造器中的 `defaultTopic` 还要传吗？** 必须传——`FlinkKafkaProducer` 在 `open()` 时会调用一次 `producer.partitionsFor(defaultTopic)` 拉取默认 Topic 的元数据。一般传业务最常用 Topic 即可。
2. **动态 Topic 一定要预先存在**，否则 `partitionsFor` 调用会触发自动创建（取决于 Broker `auto.create.topics.enable`）或直接报错。
3. **Headers 中的字符串建议显式 UTF-8 编码**，跨语言消费时省去无数排查时间。

## 4. open 方法：拿到 RuntimeContext 之外的 InitializationContext

`KafkaSerializationSchema` 也支持 `open(InitializationContext context)`，常用于：

- 注册自定义 Metric：`context.getMetricGroup()`
- 在 Schema Registry 上拉一次最新 Schema 缓存

```java
@Override
public void open(SerializationSchema.InitializationContext context) throws Exception {
    Counter c = context.getMetricGroup().counter("recordsSerialized");
    this.recordsSerialized = c;
}
```

注意：

- `open()` 只会在每个 Subtask 调用一次，**不要在 serialize 内做重连接、重缓存**
- 不能从 `InitializationContext` 拿到 Subtask 编号；如需此信息，应改用 `KafkaContextAware`（见 4.1）

### 4.1 `KafkaContextAware`：拿到并行实例信息

如果序列化逻辑需要感知"当前 Subtask 编号 / 并行度 / 目标 Topic 的分区数"，可让 Schema 实现 `KafkaContextAware`：

```java
public interface KafkaContextAware<T> {
    default String getTargetTopic(T element) { return null; }
    void setParallelInstanceId(int parallelInstanceId);
    void setNumParallelInstances(int numParallelInstances);
    void setPartitions(int[] partitions);
}
```

`FlinkKafkaProducer` 在 `open` 时会探测自定义 Schema 是否实现了该接口，如果是则把这些上下文注入进去——这是 Flink 1.13 中 Schema 拿到 Subtask 信息的标准方式。

## 5. KafkaSerializationSchemaWrapper：包裹老 Schema 的桥梁

回头看构造器（4.1 形式）：

```java
public FlinkKafkaProducer(
        String topicId,
        SerializationSchema<IN> serializationSchema,   // 旧式 Schema
        Properties producerConfig,
        Optional<FlinkKafkaPartitioner<IN>> customPartitioner)
```

用户传的是 `SerializationSchema`，但 `FlinkKafkaProducer` 内部统一用 `KafkaSerializationSchema`。Flink 通过下面这个包装器把"旧接口"适配成"新接口"：

```java
@Internal
public class KafkaSerializationSchemaWrapper<T>
        implements KafkaSerializationSchema<T>, KafkaContextAware<T> {

    private final FlinkKafkaPartitioner<T> partitioner;
    private final SerializationSchema<T> serializationSchema;
    private final String topic;
    private final boolean writeTimestamp;

    private int[] partitions;
    private int parallelInstanceId;
    private int numParallelInstances;

    @Override
    public ProducerRecord<byte[], byte[]> serialize(T element, @Nullable Long timestamp) {
        byte[] serialized = serializationSchema.serialize(element);
        Integer partition = partitioner == null
                ? null
                : partitioner.partition(element, null, serialized, topic, partitions);
        return new ProducerRecord<>(
                topic,
                partition,
                writeTimestamp ? timestamp : null,
                null,
                serialized);
    }
}
```

它做了三件事：

1. 调用旧 `SerializationSchema.serialize(element)` 得到 Value 字节
2. 调用 `FlinkKafkaPartitioner` 决定分区（系列第 3 篇详细讲）
3. 把 `writeTimestamp` 标志位生效——只有在 `producer.setWriteTimestampToKafka(true)` 时才会把事件时间写入 Kafka

**实现层启示**：

- 如果你只用旧 `SerializationSchema`，所有 Kafka 特性（Key、Headers、动态 Topic）都被这个 Wrapper 强制阉割
- 想要这些能力，必须自己实现 `KafkaSerializationSchema`

## 6. 工程实践：JSON / Avro / Protobuf 三种格式接入

### 6.1 JSON（Jackson）

最简单也最常见的格式。建议把 `ObjectMapper` 设为 `static`，避免每次 `serialize` 都重建：

```java
public class JsonSchema<T> implements KafkaSerializationSchema<T> {
    private static final ObjectMapper MAPPER = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    private final String topic;
    public JsonSchema(String topic) { this.topic = topic; }

    @Override
    public ProducerRecord<byte[], byte[]> serialize(T element, @Nullable Long ts) {
        try {
            return new ProducerRecord<>(topic, null, ts, null, MAPPER.writeValueAsBytes(element));
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }
}
```

### 6.2 Avro（Confluent Schema Registry）

Flink 官方提供了 `flink-avro-confluent-registry`，结合即可：

```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-avro-confluent-registry</artifactId>
    <version>${flink.version}</version>
</dependency>
```

```java
SerializationSchema<Order> avro = ConfluentRegistryAvroSerializationSchema.forSpecific(
        Order.class,
        "order-value",                     // subject 名
        "http://schema-registry:8081"      // Schema Registry 地址
);
```

注意：`ConfluentRegistryAvroSerializationSchema` 返回的是 `SerializationSchema`，**只能写 Value**。如果还要写 Key，自行包一层 `KafkaSerializationSchema` 把 `key`、`headers` 补上。

### 6.3 Protobuf

Protobuf 没有官方内置，但实现非常直接：

```java
public class ProtobufSchema<T extends MessageLite>
        implements KafkaSerializationSchema<T> {
    private final String topic;
    public ProtobufSchema(String topic) { this.topic = topic; }

    @Override
    public ProducerRecord<byte[], byte[]> serialize(T msg, @Nullable Long ts) {
        return new ProducerRecord<>(topic, null, ts, null, msg.toByteArray());
    }
}
```

如果对接 Confluent Schema Registry 的 Protobuf，参考 `KafkaProtobufSerializer` 自行集成。

## 7. 常见问题答疑

**Q1：为什么我设置了 `setWriteTimestampToKafka(true)`，Kafka 看到的时间还是发送时间？**

`setWriteTimestampToKafka` 只对 `KafkaSerializationSchemaWrapper` 这条**旧 Schema 路径**生效。如果你用的是自定义 `KafkaSerializationSchema`，是否写入时间戳完全由你 `new ProducerRecord(..., timestamp, ...)` 决定。

**Q2：动态 Topic 一定能成功吗？需要预创建吗？**

需要。`FlinkKafkaProducer.open()` 期间会调用 `producer.partitionsFor(defaultTopic)` 拉默认 Topic 元数据，但**不会预先 partitionsFor 所有可能的动态 Topic**。每条记录第一次写入新 Topic 时由 KafkaProducer 触发元数据请求，未预创建则取决于 Broker 的 `auto.create.topics.enable`。生产环境建议**手工建好 Topic**。

**Q3：能不能在 serialize 中根据元素决定 partition？**

可以。`ProducerRecord` 第 2 个参数即 `Integer partition`，不为空时绕过所有分区器。

**Q4：序列化失败时怎么处理？**

`serialize()` 抛异常会触发 Sink Subtask 失败，进而触发 Checkpoint 重启。生产中建议：

- 已知格式异常 → `try { ... } catch { metric.inc(); return null }`，并配合一个 dead-letter Topic
- `KafkaSerializationSchema` 中 `return null` 会让 `FlinkKafkaProducer` 跳过这条记录（源码中有 `if (record == null) return;` 判断）

**Q5：多个 Schema 共享一个 ObjectMapper / Avro Schema 缓存安全吗？**

`ObjectMapper` 线程安全，可以静态共享。Avro 的 `SpecificDatumWriter` 不是线程安全，但 Flink Sink Subtask 是单线程调用 serialize，所以"每个 Subtask 持有一份"也是安全的。

## 8. 本篇小结

序列化是 Sink 的"输入门"。一句话总结：

> **新代码只用 `KafkaSerializationSchema`；旧代码以 `KafkaSerializationSchemaWrapper` 为兼容路径；`KeyedSerializationSchema` 一律不再使用。**

掌握 `ProducerRecord` 的字段优先级，能让你随心所欲地控制 Topic、分区、Key、Value、Headers、Timestamp。下一篇我们将深入 **分区策略** ——`FlinkFixedPartitioner` 为什么能保证强一致顺序？为什么并行度 < 分区数时部分分区会饿死？敬请期待。

## 系列文章导航

| 序号 | 文章 |
|---|---|
| 第 1 篇 | Flink DataStream FlinkKafkaProducer 系列 1：快速入门 |
| 第 2 篇 | Flink DataStream FlinkKafkaProducer 系列 2：序列化机制 KafkaSerializationSchema 深度剖析（本文） |
| 第 3 篇 | Flink DataStream FlinkKafkaProducer 系列 3：分区策略 FlinkKafkaPartitioner 与如何写入指定分区 |
| 第 4 篇 | Flink DataStream FlinkKafkaProducer 系列 4：三种交付语义 AT_MOST_ONCE / AT_LEAST_ONCE / EXACTLY_ONCE |
| 第 5 篇 | Flink DataStream FlinkKafkaProducer 系列 5：Exactly-Once 源码深度剖析 TwoPhaseCommitSinkFunction |
| 第 6 篇 | Flink DataStream FlinkKafkaProducer 系列 6：生产实战 性能调优 监控指标与高可用部署 |
| 第 7 篇 | Flink DataStream FlinkKafkaProducer 系列 7：常见错误排查 FAQ 与生产事故复盘 |
