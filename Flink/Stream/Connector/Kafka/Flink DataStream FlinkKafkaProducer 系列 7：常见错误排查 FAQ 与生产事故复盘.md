---
layout: post
author: sjf0115
title: Flink DataStream FlinkKafkaProducer 系列 7：常见错误排查 FAQ 与生产事故复盘
date: 2024-03-07 10:30:00
tags:
  - Flink
categories: Flink
permalink: /flink/datastream/flink-kafka-producer-troubleshooting
---

> 基于 Flink 1.13.6 版本源码

[上一篇](./flink-kafka-producer-production) 我们梳理了生产配置与监控规范，本篇是本系列的收官——把过去几年里踩过的坑、看过的事故工单、社区常见 Issue 整理成一份"故障排查手册"，并附一个真实事故的完整复盘。

文章结构：

- 第 1 ~ 6 章：高频异常的根因与解决
- 第 7 章：故障排查决策树
- 第 8 章：真实事故复盘
- 第 9 章：日常运维 Checklist

## 1. ProducerFencedException

### 1.1 异常表现

```
org.apache.kafka.common.errors.ProducerFencedException:
Producer attempted an operation with an old epoch.
Either there is a newer producer with the same transactionalId,
or the producer's transaction has been expired by the broker.
```

### 1.2 根因

Kafka 端事务由 `(transactionalId, epoch)` 组合唯一标识。同一个 `transactionalId` 每次 `initTransactions()` 调用，broker 都会**自增 epoch** 并 fence 掉旧 epoch。

触发的典型场景：

1. **Flink 作业被外部启了两份**（同一个 jobId、同一组 transactionalId 在两台机器上）
2. **作业拓扑变更**导致 `operatorUniqueId` 改变，新作业以新 transactionalId 启动；老作业残留事务的 transactionalId 在 broker 端被作为"旧 epoch"
3. **Broker 主动 expire**：事务超过 `transaction.max.timeout.ms` 没活动，broker 自动 abort 并 fence

### 1.3 解决方案

| 触发场景 | 解决 |
|---|---|
| 重复启动 | Stop 掉重复实例；用 K8s/Yarn 的"单实例约束"防止 |
| 拓扑变更 | 给 Sink 算子显式 `.uid("kafka-sink-v1")`，避免 hash 漂移 |
| Broker fence | 调高 `transaction.max.timeout.ms` 或缩短 Checkpoint 间隔 |

### 1.4 预防

- 所有 Sink 算子**必须**带 `.uid()`
- 监控告警：Kafka broker `transaction.coord.error.count` > 0 立即关注

## 2. UnknownProducerIdException

### 2.1 异常表现

```
org.apache.kafka.common.errors.UnknownProducerIdException:
This exception is raised by the broker if it could not locate the producer metadata
associated with the producerId in question.
```

### 2.2 根因

Kafka broker 端有 `transactional.id.expiration.ms`，默认 **7 天**。超过这个时间没活动的 transactionalId，broker 会清除其元数据。作业重启后 Producer 用旧 transactionalId 调用 `initTransactions`，broker 找不到旧元数据，但 producer 端 Flink 状态里又记录了 `producerId`/`epoch`，二者不匹配。

### 2.3 解决方案

```
# Broker 端
transactional.id.expiration.ms = 2592000000   # 30 天
```

或者：

- 把作业配置一个**最长允许停机时间**，业务方接受这个上限
- 长期下线后重启，先**清除 Checkpoint** 重新初始化（会丢失停机期间未提交事务的"原子性")

### 2.4 与 ProducerFencedException 的区别

| 异常 | 元数据状态 |
|---|---|
| `ProducerFencedException` | 元数据存在，epoch 已被新实例升级 |
| `UnknownProducerIdException` | 元数据**已被清除**（过期或重建集群） |

## 3. transaction.timeout.ms 启动报错

### 3.1 异常表现

```
The configured timeout 3600000 is larger than the maximum allowed
transaction.timeout.ms 900000 configured in the broker.
```

### 3.2 根因

Flink 1.13 默认 `transaction.timeout.ms = 1 小时`，broker 默认 `transaction.max.timeout.ms = 15 分钟`，启动校验失败。

### 3.3 解决方案

二选一：

```java
// 方案 1：缩小 Producer 端
props.put(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, String.valueOf(15 * 60 * 1000));

// 方案 2：扩大 Broker 端
// server.properties
transaction.max.timeout.ms = 3600000
```

**进阶考虑**：Checkpoint 间隔 + 最长 commit 等待 < transaction.timeout.ms。否则事务在被 commit 前就被 broker 自动 abort。

## 4. Producer 池耗尽

### 4.1 异常表现

```
FlinkKafkaException: Too many ongoing snapshots.
Increase kafka producers pool size or decrease number of concurrent checkpoints.
ErrorCode: PRODUCERS_POOL_EMPTY
```

### 4.2 根因

EXACTLY_ONCE 模式下，每个 Checkpoint 占用一个 transactionalId。如果 `notifyCheckpointComplete` 迟迟不来（JobManager GC、网络抖动），事务一直处于"待 commit"状态，池中可用 ID 越来越少，最终被新 Checkpoint 请求耗尽。

### 4.3 解决方案

按照源码注释建议四选一：

1. **降低并发 Checkpoint**：`maxConcurrentCheckpoints = 1`（默认就是）
2. **加快 Checkpoint 完成**：检查存储后端、网络
3. **加大间隔**：`enableCheckpointing(longer)`
4. **扩大池子**：构造 `FlinkKafkaProducer` 时指定 `kafkaProducersPoolSize`

```java
new FlinkKafkaProducer<>(
        "topic", schema, props,
        Optional.empty(),
        FlinkKafkaProducer.Semantic.EXACTLY_ONCE,
        10                  // 默认 5，扩大到 10
);
```

## 5. 数据"卡住"——下游消费不到

### 5.1 现象

- Flink 作业一切正常，Kafka 端 Topic 大小在涨
- 下游消费者却看不到新数据

### 5.2 根因

99% 是消费端没设 `isolation.level=read_committed`。EXACTLY_ONCE 模式下消息以"已写入但未提交"状态存在 Kafka log，对 `read_uncommitted` 也是可见的——但是消费者通常要等 commit marker 才能放心拉取，导致表现像"卡住"。

实际上，问题往往是：

- Checkpoint 间隔过长（5 分钟）→ 下游延迟 5 分钟
- Checkpoint 失败 → 下游一直看不到这一段数据

### 5.3 解决

```java
// 消费端
consumerProps.put("isolation.level", "read_committed");
```

并且把 Checkpoint 间隔调到业务可接受的延迟内。

## 6. 序列化失败

### 6.1 异常表现

```
RuntimeException: Failed to serialize element ...
    at com.example.OrderKafkaSchema.serialize(...)
```

### 6.2 影响

`serialize()` 抛异常 → Sink Subtask 失败 → 触发重启 → Source 重放 → 同样的脏数据再次抛异常 → 死循环。

### 6.3 解决

```java
@Override
public ProducerRecord<byte[], byte[]> serialize(Order order, @Nullable Long ts) {
    try {
        byte[] value = MAPPER.writeValueAsBytes(order);
        return new ProducerRecord<>("order", null, ts, order.idBytes(), value);
    } catch (JsonProcessingException e) {
        // 1. 记录指标
        invalidRecordCounter.inc();
        // 2. 投递到死信 Topic
        return new ProducerRecord<>("order-dlq", null, ts,
                order.idBytes(), e.getMessage().getBytes());
        // 3. 或返回 null，FlinkKafkaProducer 会跳过这条记录
    }
}
```

**返回 null 在 FlinkKafkaProducer 1.13.6 中是合法的**：

```java
ProducerRecord<byte[], byte[]> record = kafkaSchema.serialize(next, ts);
if (record == null) return;
```

## 7. 故障排查决策树

```
作业异常退出，看 Flink Web UI 异常栈：

├── ProducerFencedException
│    └─→ 第 1 章：检查重复启动 / uid / 超时
│
├── UnknownProducerIdException
│    └─→ 第 2 章：调高 transactional.id.expiration.ms
│
├── timeout is larger than maximum allowed
│    └─→ 第 3 章：调整 transaction.timeout.ms
│
├── PRODUCERS_POOL_EMPTY
│    └─→ 第 4 章：降并发或扩池
│
├── IllegalStateException: Pending record count must be zero
│    └─→ KafkaProducer 内部异常，看 callback：网络或权限
│
├── TimeoutException: Topic xxx not present in metadata
│    └─→ 检查 Topic 是否存在 / bootstrap.servers 网络是否通
│
└── 其它：业务序列化异常
     └─→ 第 6 章：try-catch + DLQ
```

下游侧问题：

```
下游消费不到数据：
├── 消费端 lag = 0 但下游缺数据
│    └─→ 第 5 章：isolation.level=read_committed 没设
│
├── 消费端 lag 持续涨
│    └─→ Producer 的 Checkpoint 间隔设的太大
│
└── 下游分区数据不均
     └─→ 系列第 3 篇：FlinkFixedPartitioner 并行度 < 分区数
```

## 8. 真实事故复盘：写偏分区导致下游 OOM

### 8.1 事故现象

- 某天凌晨监控告警：Kafka 某 Topic 0 号分区 LAG 暴涨，3-7 号分区 LAG = 0
- 下游 Spark Streaming 消费 0 号分区的 Worker 内存溢出，整个 Job 重启循环

### 8.2 关键参数

| 项 | 值 |
|---|---|
| Kafka 分区数 | 8 |
| Flink Sink 并行度 | 4 |
| 分区器 | 默认 `FlinkFixedPartitioner` |
| 上游业务 | 增加了一个 keyBy（hash 大量集中到少数 key） |

### 8.3 根因分析

回顾系列第 3 篇 `FlinkFixedPartitioner` 的核心逻辑：

```java
return partitions[parallelInstanceId % partitions.length];
```

并行度 4，分区数 8，映射关系：

```
Subtask 0 → Partition 0
Subtask 1 → Partition 1
Subtask 2 → Partition 2
Subtask 3 → Partition 3
Partition 4-7 → 永远没人写
```

加之上游 `keyBy` 后数据热点全部集中到 Subtask 0（hash 不均），结果**所有数据都涌入 0 号分区**。

下游消费者按分区数 8 启动 8 个 Worker，0 号 Worker 单挑全部数据，OOM。

### 8.4 修复

短期：

- 把 Sink 并行度调到 8（= 分区数）
- 重启作业，数据均匀写入

长期：

- 关闭 Flink 分区器：传 `Optional.empty()`，让 KafkaProducer 默认 hash 接管
- 上游 `keyBy` 字段调整，hash 分布更均匀

事后总结：

> **`FlinkFixedPartitioner` 适用条件：Sink 并行度 = Kafka 分区数，且并行度内数据分布均匀。任一条件不满足，立刻换分区器。**

### 8.5 防御性配置

在 `open()` 阶段做断言：

```java
@Override
public void open(int parallelInstanceId, int parallelInstances) {
    super.open(parallelInstanceId, parallelInstances);
    // 自定义 partitioner 在初始化时主动校验
}
```

或者在监控里加规则：**Kafka 同一 Topic 的分区 LAG 标准差 > 阈值** → 立即告警。

## 9. 日常运维 Checklist

### 9.1 部署阶段

- [ ] Sink 算子 `.uid()` 显式指定
- [ ] `bootstrap.servers` 配 3 个以上 broker，覆盖不同机架
- [ ] `transaction.timeout.ms` 与 broker 上限对齐
- [ ] EXACTLY_ONCE 时下游消费者 `isolation.level=read_committed`
- [ ] Kafka Topic 分区数 ≤ Sink 并行度

### 9.2 上线后

- [ ] Grafana 看板：`numRecordsOutPerSecond`、`currentSendTime`、`record-error-rate`、`bufferpool-wait-ratio`
- [ ] 告警：error-rate > 0、send-time > 1s、buffer wait > 0.1
- [ ] 巡检：每周确认 transactional.id 数量没在 broker 端膨胀

### 9.3 故障演练

- [ ] 模拟单 broker 宕机：Producer 应自动重连，无丢数
- [ ] 模拟全 broker 短暂离线：Checkpoint 失败但作业不退出，恢复后继续
- [ ] 模拟事务超时：调小 `transaction.timeout.ms` 配合慢 Checkpoint，验证 abort 路径

## 10. 系列总结：你应该掌握的 7 个能力

走完这 7 篇，你应该具备：

| 能力 | 来源 |
|---|---|
| 把数据写入 Kafka | 第 1 篇 |
| 自定义 Key/Value/Headers/动态 Topic | 第 2 篇 |
| 选择并实现合适的分区策略 | 第 3 篇 |
| 在三种语义之间做出正确选型 | 第 4 篇 |
| 看懂 Exactly-Once 的源码实现 | 第 5 篇 |
| 调优 + 监控 + 高可用部署 | 第 6 篇 |
| 快速定位和修复线上故障 | 第 7 篇（本文） |

## 11. 后续延伸

- 想了解 Source 端：参考站内已有的 [Flink Kafka Connector Source 系列](./)
- 想升级到 Flink 1.14+ 的新 `KafkaSink`：核心思路相同（仍是两阶段提交），但 API 重构为 SinkV2，下次另开系列
- 想理解端到端 Exactly-Once 的更底层：建议读 [Two-Phase Commit Protocol on Streaming Pipelines](https://flink.apache.org/news/2018/02/28/an-overview-of-end-to-end-exactly-once-processing-in-apache-flink.html)

## 系列文章导航

| 序号 | 文章 |
|---|---|
| 第 1 篇 | Flink DataStream FlinkKafkaProducer 系列 1：快速入门 |
| 第 2 篇 | Flink DataStream FlinkKafkaProducer 系列 2：序列化机制 KafkaSerializationSchema 深度剖析 |
| 第 3 篇 | Flink DataStream FlinkKafkaProducer 系列 3：分区策略 FlinkKafkaPartitioner 与如何写入指定分区 |
| 第 4 篇 | Flink DataStream FlinkKafkaProducer 系列 4：三种交付语义 AT_MOST_ONCE / AT_LEAST_ONCE / EXACTLY_ONCE |
| 第 5 篇 | Flink DataStream FlinkKafkaProducer 系列 5：Exactly-Once 源码深度剖析 TwoPhaseCommitSinkFunction |
| 第 6 篇 | Flink DataStream FlinkKafkaProducer 系列 6：生产实战 性能调优 监控指标与高可用部署 |
| 第 7 篇 | Flink DataStream FlinkKafkaProducer 系列 7：常见错误排查 FAQ 与生产事故复盘（本文） |
