---
layout: post
author: sjf0115
title: Flink DataStream FlinkKafkaProducer 系列 3：分区策略 FlinkKafkaPartitioner 与如何写入指定分区
date: 2024-03-03 10:30:00
tags:
  - Flink
categories: Flink
permalink: /flink/datastream/flink-kafka-producer-partitioner
---

> 基于 Flink 1.13.6 版本源码

[上一篇](./flink-kafka-producer-serialization-schema) 我们解决了"如何把对象变成 Kafka 消息"的问题，本篇接着回答另一个关键问题：**这条消息应该落到目标 Topic 的哪个分区？**

分区决策决定了三件事：

1. **分区内顺序**——同分区严格有序，跨分区不保证
2. **下游消费并行度**——一个分区只能被一个消费组内的消费者拿到
3. **分区热点与倾斜**——分区键选错，单分区被打爆是常见事故

本文聚焦 Flink 提供的分区器抽象，逐行解读默认实现 `FlinkFixedPartitioner` 的源码，并给出几个生产中真正用得上的自定义实现。

## 1. 全景：分区决策的三条路径

`FlinkKafkaProducer` 在向 Kafka 发送一条记录时，分区是如何确定的？答案分三条路径：

```
                +---------------------------------+
                |   KafkaSerializationSchema      |
                |     .serialize(elem, ts)        |
                +-----------+---------------------+
                            | ProducerRecord
                            v
        +-----------------------------------------------+
        | record.partition() != null ?                  |
        +--------+--------------------------+-----------+
                 | 是                       | 否
                 v                          v
        Path 1: 直接写入指定分区     +-----------------+
                                     | FlinkPartitioner|
                                     |     != null ?   |
                                     +---+---------+---+
                                         | 是      | 否
                                         v         v
                                Path 2:           Path 3:
                                Flink 分区器       KafkaProducer
                                决定               默认分区器
```

| 路径 | 触发条件 | 决策者 | 典型场景 |
|---|---|---|---|
| Path 1 | `ProducerRecord.partition()` 非 null | 你自己 | 业务级强路由（按时间窗口写入特定分区） |
| Path 2 | Flink 分区器非 null | `FlinkKafkaPartitioner` | 默认行为，Subtask 与分区固定映射 |
| Path 3 | 显式传 `Optional.empty()` | KafkaProducer 内部（DefaultPartitioner） | 让 Kafka 按 Key hash / 黏性批次决定 |

**理解这三条路径的优先级**，是排查"为什么分区器没生效"的第一步。

## 2. FlinkKafkaPartitioner：抽象类签名

```java
package org.apache.flink.streaming.connectors.kafka.partitioner;

@PublicEvolving
public abstract class FlinkKafkaPartitioner<T> implements Serializable {

    public void open(int parallelInstanceId, int parallelInstances) {}

    public abstract int partition(
            T record,
            byte[] key,
            byte[] value,
            String targetTopic,
            int[] partitions);
}
```

两个方法的契约：

### 2.1 `open(parallelInstanceId, parallelInstances)`

- **生命周期**：Sink Subtask 启动时调用一次
- **`parallelInstanceId`**：当前 Subtask 编号（0 起）
- **`parallelInstances`**：作业并行度
- **典型用法**：缓存 `parallelInstanceId`，避免后续每条记录都从 `RuntimeContext` 取

### 2.2 `partition(record, key, value, targetTopic, partitions)`

- **`record`**：原始 Java 对象（注意，是反序列化前的元素）
- **`key` / `value`**：已经被序列化好的字节数组
- **`targetTopic`**：要写入的 Topic 名
- **`partitions`**：该 Topic 的所有分区 ID 数组（Flink 帮你预先排好序）
- **返回值**：分区 ID，必须落在 `partitions` 数组范围内

**注意细节**：

1. `partitions` 数组在 Sink open 时就被加载，但 Flink 会在新分区被发现时调用 `setPartitions` 刷新——也就是说**动态分区是支持的**
2. `partition()` 方法**不允许**返回 -1 或越界值，否则 KafkaProducer 会抛 `IllegalArgumentException`

## 3. 默认实现：FlinkFixedPartitioner 全文源码

这是 Flink 1.13.6 中 `FlinkKafkaProducer` 的**默认分区器**：

```java
@PublicEvolving
public class FlinkFixedPartitioner<T> extends FlinkKafkaPartitioner<T> {

    private static final long serialVersionUID = -3785320239953858777L;

    private int parallelInstanceId;

    @Override
    public void open(int parallelInstanceId, int parallelInstances) {
        Preconditions.checkArgument(parallelInstanceId >= 0,
                "Id of this subtask cannot be negative.");
        Preconditions.checkArgument(parallelInstances > 0,
                "Number of subtasks must be larger than 0.");
        this.parallelInstanceId = parallelInstanceId;
    }

    @Override
    public int partition(T record, byte[] key, byte[] value,
                         String targetTopic, int[] partitions) {
        Preconditions.checkArgument(partitions != null && partitions.length > 0,
                "Partitions of the target topic is empty.");
        return partitions[parallelInstanceId % partitions.length];
    }
}
```

逻辑极其简单——**`parallelInstanceId % partitions.length`**——但是它带来的两个特性影响巨大。

### 3.1 特性 1：每个 Subtask 写固定分区，强一致顺序

只要分区数和并行度不变，**Subtask `i` 的所有数据都会进入同一个分区**。配合上游 `keyBy`，可以做到"同一 Key 的数据严格有序进入同一分区"，这对下游做有状态消费非常关键。

### 3.2 特性 2：并行度与分区数不匹配的两种"病态"场景

#### 场景 A：并行度 > 分区数（多对一）

```
Flink Subtask 0 ──┐
Flink Subtask 1 ──┤──> Partition 0
Flink Subtask 2 ──┤
Flink Subtask 3 ──┘
Flink Subtask 4 ──> Partition 1
```

效果：分区分布**不均**，但所有 Subtask 都有目标分区，不会"饿死"。

#### 场景 B：并行度 < 分区数（一对一，部分饿死）

```
Flink Subtask 0 ──> Partition 0
Flink Subtask 1 ──> Partition 1
                   Partition 2  ← 没人写
                   Partition 3  ← 没人写
```

**这是生产事故重灾区**——下游消费者按分区数分配 worker，结果一半 worker 拿不到数据，监控误报"消费延迟为零"，实际上是因为根本没有数据流入。

**解决方法（任选其一）**：

1. **调整并行度**：让 Sink 算子并行度 ≥ 分区数
2. **关闭 Flink 分区器**：传 `Optional.empty()`，让 KafkaProducer 按 Key hash 均匀分布
3. **改用其他分区器**：如下文 `FlinkKafkaShuffleProducer` 风格的 round-robin 自定义实现

## 4. 关闭 Flink 分区器：什么时候应该这么做

```java
new FlinkKafkaProducer<>(
        "topic",
        new SimpleStringSchema(),
        props,
        Optional.empty()        // ← 关闭 Flink 分区器
);
```

传 `Optional.empty()` 后：

- Flink 不再干预分区
- 真正生效的是 `KafkaProducer` 的 `org.apache.kafka.clients.producer.internals.DefaultPartitioner`
  - **有 Key**：按 `murmur2(key) % numPartitions` 取分区（同 Key 同分区）
  - **无 Key**：使用 [Sticky Partitioner](https://cwiki.apache.org/confluence/display/KAFKA/KIP-480%3A+Sticky+Partitioner)（黏性分区），尽量打满一个 batch 再换分区，提高吞吐

**适用场景**：

- 并行度 < 分区数，希望均匀分布
- 上游已经按 Kafka Key 做过 keyBy，希望 Key 同分区
- 数据无 Key 且不要求顺序，追求最高吞吐（Sticky Partitioner 性能极佳）

## 5. 自定义分区器实战

### 5.1 按业务字段路由（如按租户 ID）

```java
public class TenantPartitioner extends FlinkKafkaPartitioner<Order> {
    @Override
    public int partition(Order order, byte[] key, byte[] value,
                         String targetTopic, int[] partitions) {
        // 把租户 ID hash 到分区
        return partitions[
                (order.getTenantId().hashCode() & Integer.MAX_VALUE)
                        % partitions.length];
    }
}
```

注意 `& Integer.MAX_VALUE` 是为了把负数变成非负数——`hashCode()` 可能返回 `Integer.MIN_VALUE`，直接 `Math.abs(...)` 在该值上**会溢出**仍是负数，导致负数下标。这是一个经典的低级陷阱。

### 5.2 按时间窗口轮转

```java
public class TimeWindowPartitioner extends FlinkKafkaPartitioner<Event> {
    @Override
    public int partition(Event evt, byte[] key, byte[] value,
                         String targetTopic, int[] partitions) {
        // 每 10 秒切换一次分区，便于下游按时间分片消费
        long bucket = evt.getEventTime() / 10_000L;
        return partitions[(int) (bucket % partitions.length)];
    }
}
```

### 5.3 完全 round-robin

```java
public class RoundRobinPartitioner<T> extends FlinkKafkaPartitioner<T> {
    private int counter = 0;
    @Override
    public int partition(T record, byte[] key, byte[] value,
                         String targetTopic, int[] partitions) {
        int idx = counter++ % partitions.length;
        if (counter < 0) counter = 0;     // 防止溢出
        return partitions[idx];
    }
}
```

注意：**round-robin 会让批次小、网络连接多**，吞吐反而不如 Sticky Partitioner。除非有强分布要求，否则不推荐。

## 6. 在 ProducerRecord 中显式指定 partition：最强优先级

如第 1 章所述，如果你**真的有业务级强需求**直接写入指定分区，可以在 `KafkaSerializationSchema.serialize` 内构造 `ProducerRecord`：

```java
return new ProducerRecord<>(topic, /* partition */ 3, ts, key, value);
```

此时 `FlinkKafkaPartitioner.partition()` **不会被调用**——优先级最高。常见用法：

- 把控制流和数据流分别落到固定分区
- 在测试环境强制把所有数据写到 0 号分区，便于排查

## 7. 分区器与 Exactly-Once 的协作关系

很多用户问："启用 Exactly-Once 后，分区器还按原来的方式工作吗？"

**完全一样**。分区决策完全发生在 `serialize` → `partition` 这一层，与事务无关；事务的边界由 `TwoPhaseCommitSinkFunction` 用 Checkpoint 隔离，不会影响分区路由。

唯一的间接影响是：Exactly-Once 模式下，Flink 会维护一个 **Producer 池**，每个事务对应池中一个 Producer。但每个 Producer 内部的分区器依然是同一个 `FlinkFixedPartitioner` 或者你的自定义实现。

## 8. 常见问题答疑

**Q1：我用了 `keyBy(key)`，下游 Sink 还需要分区器吗？**

`keyBy` 决定的是 Flink **算子之间**的数据路由（哪个 Subtask 收到哪条数据），与 Kafka 分区无关。Sink 端仍需要分区器把数据写到 Kafka 分区。

如果想"同一 Flink Key 写到同一 Kafka 分区"，最简单的做法是：

1. 上游 `keyBy(getKey)`
2. Sink 用默认 `FlinkFixedPartitioner`
3. 保证 Sink 并行度 = Kafka 分区数

这样 Subtask 与分区一一对应，自然就保证了 Key→Partition 的稳定映射。

**Q2：`FlinkFixedPartitioner` 在动态分区扩容时会怎样？**

Kafka 增加分区后，Flink 会通过 `KafkaSerializationSchemaWrapper.setPartitions(int[])` 更新分区数组。下次 `partition()` 调用时新分区即生效。但已经在飞行中的事务不会重新路由。

**Q3：能不能让 Flink 分区器知道 Subtask 编号？**

可以，`open(int parallelInstanceId, int parallelInstances)` 直接给。如果是自定义 `KafkaSerializationSchema` 想拿到这个信息，请实现 `KafkaContextAware`（详见第 2 篇 4.1）。

**Q4：`Optional.empty()` vs `null`**

构造器 `Optional<FlinkKafkaPartitioner<IN>> customPartitioner` 形参，**只能传 `Optional.empty()` 或 `Optional.of(xxx)`**。传 `null` 会触发 `NullPointerException`。这是 Flink 1.13 一个不太友好的 API 设计。

**Q5：是不是所有分区器都要 `Serializable`？**

是。Flink Sink 算子会被序列化分发到 TaskManager，所有持有的字段（包括分区器）必须可序列化。如果在分区器里持有 `static final ObjectMapper` 是 OK 的，但是持有 `KafkaProducer` 这种就会报错。

## 9. 决策树：如何为你的场景选对分区器

```
是否需要"同一业务 Key → 同一 Kafka 分区"？
 ├── 是 → 是否在上游做了 keyBy？
 │        ├── 是 → 让 Sink 并行度 = Kafka 分区数 + 默认 FlinkFixedPartitioner
 │        └── 否 → 关闭 Flink 分区器（Optional.empty），用 KafkaProducer 默认 hash
 └── 否 → 是否有热点风险（部分 Key 数据极多）？
          ├── 是 → 自定义随机/round-robin 分区器
          └── 否 → 默认 FlinkFixedPartitioner 即可
```

## 10. 本篇小结

- 分区决策的三条路径：`ProducerRecord.partition` > Flink 分区器 > KafkaProducer 默认分区器
- 默认 `FlinkFixedPartitioner` 极简但有"并行度 < 分区数 → 分区饿死"的陷阱
- 关闭 Flink 分区器（`Optional.empty()`）让 Kafka 默认 Sticky Partitioner 接管，吞吐最优
- 自定义分区器要注意 `hashCode()` 负数陷阱、序列化、`partitions` 边界

下一篇我们将进入"语义"主题——三种 `Semantic` 究竟做了什么、付出多少代价、如何选型。

## 系列文章导航

| 序号 | 文章 |
|---|---|
| 第 1 篇 | Flink DataStream FlinkKafkaProducer 系列 1：快速入门 |
| 第 2 篇 | Flink DataStream FlinkKafkaProducer 系列 2：序列化机制 KafkaSerializationSchema 深度剖析 |
| 第 3 篇 | Flink DataStream FlinkKafkaProducer 系列 3：分区策略 FlinkKafkaPartitioner 与如何写入指定分区（本文） |
| 第 4 篇 | Flink DataStream FlinkKafkaProducer 系列 4：三种交付语义 AT_MOST_ONCE / AT_LEAST_ONCE / EXACTLY_ONCE |
| 第 5 篇 | Flink DataStream FlinkKafkaProducer 系列 5：Exactly-Once 源码深度剖析 TwoPhaseCommitSinkFunction |
| 第 6 篇 | Flink DataStream FlinkKafkaProducer 系列 6：生产实战 性能调优 监控指标与高可用部署 |
| 第 7 篇 | Flink DataStream FlinkKafkaProducer 系列 7：常见错误排查 FAQ 与生产事故复盘 |
