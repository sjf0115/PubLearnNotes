---
layout: post
author: sjf0115
title: Flink DataStream FlinkKafkaProducer 系列 4：三种交付语义 AT_MOST_ONCE AT_LEAST_ONCE EXACTLY_ONCE
date: 2024-03-04 10:30:00
tags:
  - Flink
categories: Flink
permalink: /flink/datastream/flink-kafka-producer-semantic
---

> 基于 Flink 1.13.6 版本源码

[上一篇](./flink-kafka-producer-partitioner) 我们解决了"消息落到哪个分区"的问题，本篇回答另一个常被混淆的问题：**消息究竟会到达几次？**

在 Flink 与 Kafka 这条链路上，"端到端一致性"是反复被提及但又最容易踩坑的话题。本文围绕 `FlinkKafkaProducer.Semantic` 枚举的三种取值，逐项剖析：

- 三种语义在源码层各自做了什么
- 它们与 Checkpoint 的协作关系
- 性能、副作用、配置矩阵的差异
- 真实业务场景下如何选型

## 1. Semantic 枚举

```java
public enum Semantic {

    /**
     * EXACTLY_ONCE：Flink Producer 在 Kafka 事务中写入消息，
     * 事务在 Checkpoint 完成时提交。
     */
    EXACTLY_ONCE,

    /**
     * AT_LEAST_ONCE：Flink Producer 在 Checkpoint 时刻
     * 等待所有未确认的消息被 Kafka Broker ack。
     */
    AT_LEAST_ONCE,

    /**
     * NONE：Flink Producer 仅仅 fire-and-forget 地把消息送出，
     * 不做任何额外的可靠性保证。
     */
    NONE
}
```

注意命名：
- 文档和习惯里我们叫 "AT_MOST_ONCE"，但 **源码枚举值实际叫 `NONE`**
- 文章中为了与社区习惯对齐，下文同时使用"AT_MOST_ONCE / NONE"

## 2. NONE（AT_MOST_ONCE）：fire-and-forget

### 2.1 行为

`Semantic.NONE` 模式下：

- `FlinkKafkaProducer.invoke(value)` → `producer.send(record, callback)`
- **不等待 ack**，不调用 `flush`
- Checkpoint 时 **也不会** 等待未发送的消息完成

### 2.2 后果

- **作业重启**：Checkpoint Barrier 之后但还在 Kafka 客户端缓冲区里的消息可能永久丢失
- **吞吐**：最高，但实际意义有限——KafkaProducer 内部本身就是异步攒批，AT_LEAST_ONCE 与 NONE 的稳态吞吐差距并不大

### 2.3 适用场景

**几乎不应使用**。即使是日志、监控这种"丢一点没事"的场景，AT_LEAST_ONCE 的成本也几乎可以忽略。NONE 唯一合理的场景是**测试环境下要把 Flink 与 Kafka 的可靠性彻底解耦做压测**。

## 3. AT_LEAST_ONCE：默认语义，依赖 Checkpoint flush

### 3.1 关键源码：snapshotState 中的 flush

`FlinkKafkaProducer` 在 AT_LEAST_ONCE 模式下，`snapshotState` 路径上会执行：

```java
@Override
protected void preCommit(KafkaTransactionState transaction) throws FlinkKafkaException {
    switch (semantic) {
        case EXACTLY_ONCE:
        case AT_LEAST_ONCE:
            flush(transaction);     // ← 关键：等待所有未确认消息 ack
            break;
        case NONE:
            break;
    }
    checkErroneous();
}

private void flush(KafkaTransactionState transaction) throws FlinkKafkaException {
    if (transaction.producer != null) {
        transaction.producer.flush();   // 阻塞直到全部消息收到 ack
    }
}
```

`producer.flush()` 是 KafkaProducer 提供的**阻塞调用**——它会一直等到 accumulator 中所有 batch 被发送、所有 in-flight 请求收到 broker 的 ack 才返回。

### 3.2 端到端一致性是如何保证的

```
| Subtask 收到 Checkpoint Barrier  | 此时缓冲区可能还有 100 条消息没 ack
| ↓
| snapshotState() → preCommit() → producer.flush()
| ↓
| 100 条全部 ack 完成
| ↓
| Barrier 向下游传递，Checkpoint 完成
```

也就是说：**Checkpoint 完成的时刻，所有进入了 Sink 的消息一定已经在 Kafka Broker 上落盘**。如果作业失败重启，Source 从上一个成功的 Checkpoint 恢复 offset，被重放的数据再次写入 Kafka——可能产生重复，但绝对不会丢失。

### 3.3 副作用

唯一副作用就是 **Checkpoint 时延**。如果 Producer 缓冲区里有大批未 ack 的消息，`flush()` 阻塞时间会被 Checkpoint 等待全程吃掉。

排查思路：

- Flink Web UI 看 `currentCheckpoint` 中 Sink Subtask 的 `Sync Duration`
- Kafka 端检查 broker 是否在 GC 抖动、副本同步延迟（`UnderReplicatedPartitions`）
- 客户端 `linger.ms` 太大也会让 flush 一次性提交大量消息

### 3.4 必要配置

```java
props.put(ProducerConfig.ACKS_CONFIG, "all");        // 强一致写
props.put(ProducerConfig.RETRIES_CONFIG, "2147483647");
props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, "5");
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
```

特别强调：**`acks=all`** 是 AT_LEAST_ONCE 真正生效的前提。如果用了默认 `acks=1`，主副本 ack 后立即返回，主副本宕机但还未同步到 follower，数据照样丢——这种情况下 Flink 自认 Checkpoint 成功，但 Kafka 实际丢了消息。

## 4. EXACTLY_ONCE：事务 + 两阶段提交

### 4.1 关键概念

EXACTLY_ONCE 必须依赖 Kafka 0.11+ 的两个新特性：

- **幂等 Producer**（`enable.idempotence=true`）：Producer 给每条消息打 sequence 号，broker 去重
- **事务 Producer**（`transactional.id`）：把多条消息绑成一个事务，提交前对消费者不可见

`FlinkKafkaProducer` 把"两阶段提交"映射到 Kafka 事务上：

| 2PC 阶段 | Flink 钩子 | Kafka 调用 |
|---|---|---|
| 开始事务 | `beginTransaction()` | `producer.beginTransaction()` |
| 写消息 | `invoke()` | `producer.send()` |
| 预提交（Pre-Commit） | `preCommit()` | `producer.flush()`（消息已写入 broker，但事务未提交） |
| 持久化预提交状态 | `snapshotState()` | 把 `transactionalId` 写入 Flink 状态 |
| 提交事务 | `commit()`（在 `notifyCheckpointComplete` 时触发） | `producer.commitTransaction()` |
| 回滚 | `abort()` | `producer.abortTransaction()` |

### 4.2 何时事务对消费者可见？

预提交完成之后，事务里的消息**已经写入 Kafka 的 log**，但所属的 Transaction Marker 还未写入。消费者侧用 `isolation.level` 控制可见性：

| 消费端 isolation.level | 行为 |
|---|---|
| `read_uncommitted`（默认） | 即使事务未提交，消费者也能读到消息（**会读到将来回滚的脏数据**） |
| `read_committed` | 只读取已提交事务的消息 |

**结论**：要实现端到端 Exactly-Once，**消费端必须显式设置 `isolation.level=read_committed`**，否则 Flink 这一侧再严格也是徒劳。

### 4.3 关键源码：commit 与 abort

```java
@Override
protected void commit(KafkaTransactionState transaction) {
    if (transaction.isTransactional()) {
        try {
            transaction.producer.commitTransaction();
        } finally {
            recycleTransactionalProducer(transaction.producer);
        }
    }
}

@Override
protected void abort(KafkaTransactionState transaction) {
    if (transaction.isTransactional()) {
        transaction.producer.abortTransaction();
        recycleTransactionalProducer(transaction.producer);
    }
}
```

`commit()` 在哪里被调用？**`notifyCheckpointComplete(checkpointId)`**——也就是 JobManager 通知所有算子"这次 Checkpoint 全局成功"之后。在此之前，事务一直处于"已预提交但未提交"状态，对 read_committed 的消费者完全不可见。

### 4.4 Producer 池化机制

EXACTLY_ONCE 模式下，Flink **不会**只用一个 Producer 实例，而是维护一个 Producer 池：

```java
private final BlockingDeque<String> availableTransactionalIds = new LinkedBlockingDeque<>();

@Override
protected KafkaTransactionState beginTransaction() throws FlinkKafkaException {
    switch (semantic) {
        case EXACTLY_ONCE:
            FlinkKafkaInternalProducer<byte[], byte[]> producer = createTransactionalProducer();
            producer.beginTransaction();
            return new KafkaTransactionState(producer.getTransactionalId(), producer);
        ...
    }
}
```

为什么要池化？因为 Kafka 事务**不允许**一个 Producer 同时跑两个事务，但是 Flink 允许多个 Checkpoint 并发——上一个 Checkpoint 还没收到 `notifyCheckpointComplete`、还没 commit，下一个 Checkpoint 已经开始 `beginTransaction`。这时就需要从池中拿出另一个 `transactionalId` 启动新事务。

池大小由两个因素决定：

- 默认池里至少有 5 个 transactionalId，可以通过 `FlinkKafkaProducer.KAFKA_PRODUCERS_POOL_SIZE` 调
- transactionalId 的命名：`{taskName}-{subtaskId}-{generation}`

详细的 Producer 池源码会在系列第 5 篇详细展开。

### 4.5 关键陷阱：transaction.timeout.ms

Kafka 事务最长寿命由 `transaction.timeout.ms` 决定。Flink 1.13 默认 1 小时，但 Broker `transaction.max.timeout.ms` 默认只有 15 分钟，**Flink 启动时如果发现超过 Broker 上限，直接报错**：

```
Configured 'transaction.timeout.ms' (3600000) is larger than maximum
allowed by the broker (900000).
```

正确做法：

```java
props.put(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, String.valueOf(15 * 60 * 1000));
```

或者反过来调高 Broker：

```
transaction.max.timeout.ms=3600000
```

进一步的考虑：**Checkpoint 间隔 + 最长 commit 等待时间 < transaction.timeout.ms**，否则事务在 commit 前已超时被自动 abort，数据丢失。

## 5. 三种语义对比表

| 维度 | NONE (AT_MOST_ONCE) | AT_LEAST_ONCE（默认） | EXACTLY_ONCE |
|---|---|---|---|
| 是否依赖 Checkpoint | 否 | 是 | 是 |
| Producer 个数 | 1 | 1 | 池化（默认 5） |
| flush 阻塞 Checkpoint | 否 | 是 | 是 |
| 是否使用 Kafka 事务 | 否 | 否 | 是 |
| `transactional.id` 必填 | 否 | 否 | 是（Flink 自动生成） |
| 消费端要求 | 无 | 无 | `isolation.level=read_committed` |
| Broker 版本要求 | ≥ 0.10 | ≥ 0.10 | **≥ 0.11** |
| 重启数据是否会重复 | 不一定（可能丢） | **会重复** | **不会重复** |
| 重启数据是否会丢失 | 会 | 不会 | 不会 |
| 吞吐相对值 | 100 | 95 | 70~85（看事务大小） |
| 配置复杂度 | 低 | 中 | 高 |

## 6. 配置矩阵

| 配置项 | NONE | AT_LEAST_ONCE | EXACTLY_ONCE |
|---|---|---|---|
| `acks` | 任意 | **`all`** | `all`（事务模式强制） |
| `enable.idempotence` | 任意 | 推荐 `true` | **强制 `true`** |
| `transactional.id` | 不设 | 不设 | Flink 自动生成 |
| `transaction.timeout.ms` | 无意义 | 无意义 | **必须 ≤ Broker 上限** |
| `max.in.flight.requests.per.connection` | 任意 | ≤ 5（开幂等时） | **≤ 5（强制）** |
| Checkpoint 配置 | 可选 | **必开** | **必开 + 长间隔** |
| 消费端 `isolation.level` | 任意 | 任意 | **`read_committed`** |

`max.in.flight.requests.per.connection` 这个限制在 1.13.6 源码 `FlinkKafkaProducer` 启动时会校验：

```java
// 简化逻辑：开启 idempotence 时，max.in.flight 必须 ≤ 5
if (idempotenceEnabled && maxInFlight > 5) {
    throw new IllegalArgumentException(...);
}
```

## 7. 选型决策树

```
是否能容忍数据丢失？
 ├── 能（监控、压测）        → NONE / AT_LEAST_ONCE
 │
 └── 不能 → 是否能容忍重复？
            ├── 业务幂等（如 upsert 主键、状态覆盖） → AT_LEAST_ONCE
            │
            └── 业务非幂等（如计数、扣费、对账）   → EXACTLY_ONCE
```

### 7.1 业务幂等：AT_LEAST_ONCE 足够

下游消费者把 Kafka 数据写到带主键的存储（MySQL upsert / Redis SET）：重复消息再写一遍，结果一样。这种场景没必要付出 EXACTLY_ONCE 的额外复杂度。

### 7.2 业务非幂等：必须 EXACTLY_ONCE

财务结算、广告计费、流量统计——一条消息消费两次会直接造成业务错误。此时必须：

1. Flink Sink 端 `Semantic.EXACTLY_ONCE`
2. Kafka 消费端 `isolation.level=read_committed`
3. Checkpoint 间隔合理（建议 30s ~ 1min），太短会让事务过多导致 Producer 池耗尽

### 7.3 一个常被忽略的真相

> 如果你下游消费端是 Flink 自己（用 `FlinkKafkaConsumer`），它**默认不会**设置 `isolation.level=read_committed`，需要你在 properties 里显式加。

```java
consumerProps.setProperty("isolation.level", "read_committed");
```

否则上游再严格的 EXACTLY_ONCE 也只是"半套方案"——下游会读到将来回滚的脏数据。

## 8. 常见问题答疑

**Q1：开了 EXACTLY_ONCE 但下游还是看到重复，为啥？**

99% 是消费端没设 `isolation.level=read_committed`，或者下游本身的处理是非幂等的。

**Q2：Checkpoint 间隔越短，EXACTLY_ONCE 越好吗？**

恰恰相反。每个 Checkpoint 都会发起一个新事务，间隔太短意味着：

- Producer 池消耗快
- `transaction.timeout.ms` 限制下，剩余事务窗口紧张
- 大量小事务在 Broker 端造成元数据压力

经验值：30 秒 ~ 5 分钟。

**Q3：能在 EXACTLY_ONCE 模式下手动 commit/abort 吗？**

不行。事务的 begin / commit / abort 完全由 `TwoPhaseCommitSinkFunction` 框架接管，用户代码不应介入。

**Q4：从 EXACTLY_ONCE 切回 AT_LEAST_ONCE 安全吗？**

不安全。如果旧 Checkpoint 里还有未提交事务，需要先在 EXACTLY_ONCE 模式下完成清理才能切换，否则可能有挂起事务永远不释放。生产中建议**重命名 transactional.id 前缀**或**重置作业状态**后再切换。

**Q5：AT_LEAST_ONCE 模式下，作业 OOM 重启会丢数据吗？**

只要 Checkpoint 已经完成，那个 Checkpoint 之前的所有数据都已经 flush 到 Kafka，**绝对不会丢**。会丢失的只是 Checkpoint 之后但还没 ack 的窗口——这部分会被 Source 重放，所以最终也不会丢。

## 9. 本篇小结

- `Semantic.NONE` 几乎不该使用，AT_LEAST_ONCE 是默认且足够大多数场景
- AT_LEAST_ONCE 通过 Checkpoint 时 `producer.flush()` 阻塞等待 ack 实现"不丢"
- EXACTLY_ONCE 通过 Kafka 事务 + Flink 两阶段提交实现"不丢不重"，但有 Producer 池、`transaction.timeout.ms`、消费端 `isolation.level` 等一系列配套
- 选型核心问题：业务是否幂等

下一篇我们将进入**源码深度剖析**——`TwoPhaseCommitSinkFunction` 究竟是怎么做到 Exactly-Once 的？`KafkaTransactionState`、`recoverAndCommit`、Producer 池又是如何工作的？

## 系列文章导航

| 序号 | 文章 |
|---|---|
| 第 1 篇 | Flink DataStream FlinkKafkaProducer 系列 1：快速入门 |
| 第 2 篇 | Flink DataStream FlinkKafkaProducer 系列 2：序列化机制 KafkaSerializationSchema 深度剖析 |
| 第 3 篇 | Flink DataStream FlinkKafkaProducer 系列 3：分区策略 FlinkKafkaPartitioner 与如何写入指定分区 |
| 第 4 篇 | Flink DataStream FlinkKafkaProducer 系列 4：三种交付语义 AT_MOST_ONCE / AT_LEAST_ONCE / EXACTLY_ONCE（本文） |
| 第 5 篇 | Flink DataStream FlinkKafkaProducer 系列 5：Exactly-Once 源码深度剖析 TwoPhaseCommitSinkFunction |
| 第 6 篇 | Flink DataStream FlinkKafkaProducer 系列 6：生产实战 性能调优 监控指标与高可用部署 |
| 第 7 篇 | Flink DataStream FlinkKafkaProducer 系列 7：常见错误排查 FAQ 与生产事故复盘 |
