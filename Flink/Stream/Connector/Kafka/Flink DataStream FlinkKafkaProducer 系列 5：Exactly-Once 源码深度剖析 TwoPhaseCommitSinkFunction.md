---
layout: post
author: sjf0115
title: Flink DataStream FlinkKafkaProducer 系列 5：Exactly-Once 源码深度剖析 TwoPhaseCommitSinkFunction
date: 2024-03-05 10:30:00
tags:
  - Flink
categories: Flink
permalink: /flink/datastream/flink-kafka-producer-two-phase-commit
---

> 基于 Flink 1.13.6 版本源码

[上一篇](./flink-kafka-producer-semantic) 我们从行为和配置层面理解了三种交付语义，本篇深入到源码层，把 `EXACTLY_ONCE` 是如何工作的彻底讲清楚。

阅读本文你会拿到：

- `TwoPhaseCommitSinkFunction` 抽象类的设计思想与五个核心钩子
- `FlinkKafkaProducer` 对每个钩子的具体实现
- Producer 池（`availableTransactionalIds`）的工作机制
- `recoverAndCommit` / `recoverAndAbort` 的故障恢复路径
- 与 Checkpoint Barrier 对齐的协作时序

## 1. 整体流程：一张图理解 2PC 在 Flink 中的执行链路

```
时间线 →
                                ┌──────────────── Checkpoint N ────────────────┐
                                v                                             v
   +---------+  +---------+  +─────────+  +──────────────+  +───────+  +─────────────────+
   | invoke  | →| invoke  | →| invoke  | →| snapshotState| →|  ...  | →| notifyCkptDone  |
   +---------+  +---------+  +─────────+  +──────────────+  +───────+  +─────────────────+
        │           │            │              │                            │
        │           │            │              │                            ▼
        ▼           ▼            ▼              ▼                       commit(N) →
  写入 txnA   写入 txnA    写入 txnA       preCommit(txnA)            producer.commitTransaction
                                          flush()
                                          state.add(txnA)
                                          beginTransaction(txnB)
```

关键节点：

1. 每两次 Checkpoint 之间属于**同一个事务**，所有 `invoke` 共用一个 Producer
2. `snapshotState` 时刻：当前事务被 **预提交**（flush），并把 `transactionalId` 写入 Flink 状态
3. `notifyCheckpointComplete` 时刻：才**真正调用** `producer.commitTransaction()`
4. 失败重启：从状态里恢复未提交的 `transactionalId`，调用 `recoverAndCommit`

## 2. TwoPhaseCommitSinkFunction：抽象骨架

> `org.apache.flink.streaming.api.functions.sink.TwoPhaseCommitSinkFunction`：

```java
public abstract class TwoPhaseCommitSinkFunction<IN, TXN, CONTEXT>
        extends RichSinkFunction<IN>
        implements CheckpointedFunction, CheckpointListener {

    // 当前正在写入的事务
    private TransactionHolder<TXN> currentTransactionHolder;

    // 已经预提交、等待 notifyCheckpointComplete 触发提交的事务
    protected final LinkedHashMap<Long, TransactionHolder<TXN>> pendingCommitTransactions =
            new LinkedHashMap<>();

    // 状态：保存所有未提交事务的句柄，用于失败恢复
    protected transient ListState<State<TXN, CONTEXT>> state;

    // ===== 五个核心钩子，子类实现 =====
    protected abstract void invoke(TXN transaction, IN value, Context context) throws Exception;
    protected abstract TXN beginTransaction() throws Exception;
    protected abstract void preCommit(TXN transaction) throws Exception;
    protected abstract void commit(TXN transaction);
    protected abstract void abort(TXN transaction);

    // 故障恢复路径
    protected void recoverAndCommit(TXN transaction) { commit(transaction); }
    protected void recoverAndAbort(TXN transaction) { abort(transaction); }
}
```

### 2.1 核心字段含义

| 字段 | 含义 |
|---|---|
| `currentTransactionHolder` | 当前正在被 `invoke` 写入的事务句柄（即"开放中"的事务） |
| `pendingCommitTransactions` | 已预提交、等待 commit 的事务列表（按 checkpointId 排序） |
| `state` | Flink ListState，持久化所有未提交事务的元信息（用于重启恢复） |
| `userContext` | 用户自定义的全局上下文（FlinkKafkaProducer 中存放的是 `KafkaTransactionContext`） |

### 2.2 五个钩子的契约

```
beginTransaction() ─┐
                    ├─ 子类必须返回一个 TXN 句柄，标识一个新事务
                    │  在 FlinkKafkaProducer 中，TXN = KafkaTransactionState
                    └─

invoke(TXN, IN, Context) ─┐
                          ├─ 子类把数据写入 TXN 关联的资源
                          │  在 FlinkKafkaProducer 中，调用 producer.send()
                          └─

preCommit(TXN) ─┐
                ├─ Checkpoint 时被调用
                │  子类需要把所有缓冲数据持久化到外部系统，但不可见
                │  在 FlinkKafkaProducer 中，调用 producer.flush()
                └─

commit(TXN) ─┐
             ├─ Checkpoint 全局完成后调用
             │  子类把数据"暴露"给消费者
             │  在 FlinkKafkaProducer 中，调用 producer.commitTransaction()
             └─

abort(TXN) ─┐
            ├─ 异常或超时时调用
            │  子类需要回滚事务、释放资源
            │  在 FlinkKafkaProducer 中，调用 producer.abortTransaction()
            └─
```

## 3. FlinkKafkaProducer 对五个钩子的实现

### 3.1 KafkaTransactionState：事务句柄

`TXN` 类型在 `FlinkKafkaProducer` 中具化为 `KafkaTransactionState`：

```java
@VisibleForTesting
public static class KafkaTransactionState {

    private final transient FlinkKafkaInternalProducer<byte[], byte[]> producer;
    final String transactionalId;        // Kafka 事务 ID
    final long producerId;               // 由 Broker 分配
    final short epoch;                   // 由 Broker 分配，标识 Producer 实例代次

    boolean isTransactional() {
        return transactionalId != null;
    }
}
```

注意 `producer` 字段被标记 `transient`——序列化时不会被持久化。这就引出了一个问题：**如果作业重启，Producer 实例如何恢复？** 答案在 3.6 节 `recoverAndCommit`。

### 3.2 beginTransaction：从池子里拿 transactionalId

```java
@Override
protected KafkaTransactionState beginTransaction() throws FlinkKafkaException {
    switch (semantic) {
        case EXACTLY_ONCE:
            FlinkKafkaInternalProducer<byte[], byte[]> producer = createTransactionalProducer();
            producer.beginTransaction();
            return new KafkaTransactionState(producer.getTransactionalId(), producer);
        case AT_LEAST_ONCE:
        case NONE:
            // 复用同一个 Producer，无事务
            if (currentTransaction() != null && currentTransaction().producer != null) {
                return new KafkaTransactionState(currentTransaction().producer);
            }
            return new KafkaTransactionState(initNonTransactionalProducer(true));
        default:
            throw new UnsupportedOperationException("Not implemented semantic");
    }
}

private FlinkKafkaInternalProducer<byte[], byte[]> createTransactionalProducer()
        throws FlinkKafkaException {
    String transactionalId = availableTransactionalIds.poll();
    if (transactionalId == null) {
        throw new FlinkKafkaException(
                FlinkKafkaErrorCode.PRODUCERS_POOL_EMPTY,
                "Too many ongoing snapshots. Increase kafka producers pool size or "
                        + "decrease number of concurrent checkpoints.");
    }
    FlinkKafkaInternalProducer<byte[], byte[]> producer = initTransactionalProducer(transactionalId, true);
    producer.initTransactions();
    return producer;
}
```

要点：

- EXACTLY_ONCE 路径从 `availableTransactionalIds` 队列里取一个 ID
- 拿不到 ID 抛 `PRODUCERS_POOL_EMPTY`——这是 Producer 池耗尽的典型异常
- AT_LEAST_ONCE / NONE 路径**只用一个长期存活的 Producer**

### 3.3 invoke：把消息发出去

```java
@Override
public void invoke(KafkaTransactionState transaction, IN next, Context context) throws Exception {
    checkErroneous();   // 检查异步 Callback 是否已经记录过错误

    ProducerRecord<byte[], byte[]> record;
    if (keyedSchema != null) {
        // 旧 KeyedSerializationSchema 路径
        ...
    } else if (kafkaSchema != null) {
        // 推荐路径：KafkaSerializationSchema
        if (kafkaSchema instanceof KafkaContextAware) {
            @SuppressWarnings("unchecked")
            KafkaContextAware<IN> contextAwareSchema = (KafkaContextAware<IN>) kafkaSchema;
            String targetTopic = contextAwareSchema.getTargetTopic(next);
            if (targetTopic == null) targetTopic = defaultTopicId;
            // ... partitions, parallelInstanceId 注入
        }
        record = kafkaSchema.serialize(next, context.timestamp());
    } else {
        throw new RuntimeException(
                "We have neither KafkaSerializationSchema nor KeyedSerializationSchema, "
                + "this is a bug.");
    }

    // 发送（异步，回调记录失败）
    pendingRecords.incrementAndGet();
    transaction.producer.send(record, callback);
}
```

注意 `pendingRecords`——它是一个 `AtomicLong` 计数器，记录尚未收到 ack 的消息数。`flush()` 完成后会归零，是判断 flush 是否真的彻底的关键。

### 3.4 preCommit：flush 等待 ack

```java
@Override
protected void preCommit(KafkaTransactionState transaction) throws FlinkKafkaException {
    switch (semantic) {
        case EXACTLY_ONCE:
        case AT_LEAST_ONCE:
            flush(transaction);
            break;
        case NONE:
            break;
        default:
            throw new UnsupportedOperationException("Not implemented semantic");
    }
    checkErroneous();
}

private void flush(KafkaTransactionState transaction) throws FlinkKafkaException {
    if (transaction.producer != null) {
        transaction.producer.flush();
    }
    long pendingRecordsCount = pendingRecords.get();
    if (pendingRecordsCount != 0) {
        throw new IllegalStateException(
                "Pending record count must be zero at this point: " + pendingRecordsCount);
    }
    checkErroneous();
}
```

`flush()` 之后还要再校验一次 `pendingRecords == 0`，这是一个防御性检查——防止 Callback 内部状态错乱。任何不一致都直接抛 `IllegalStateException` 让作业失败重启，**绝不允许"看起来 flush 完了但其实有消息没 ack"**。

### 3.5 commit：在 notifyCheckpointComplete 中触发

```java
@Override
public void notifyCheckpointComplete(long checkpointId) throws Exception {
    super.notifyCheckpointComplete(checkpointId);   // 父类负责调用 commit(txn)
}
```

父类 `TwoPhaseCommitSinkFunction.notifyCheckpointComplete`：

```java
@Override
public final void notifyCheckpointComplete(long checkpointId) throws Exception {
    Iterator<Map.Entry<Long, TransactionHolder<TXN>>> pendingTxnIter =
            pendingCommitTransactions.entrySet().iterator();
    while (pendingTxnIter.hasNext()) {
        Map.Entry<Long, TransactionHolder<TXN>> e = pendingTxnIter.next();
        Long pendingTxnCheckpointId = e.getKey();
        TransactionHolder<TXN> pendingTxn = e.getValue();
        if (pendingTxnCheckpointId > checkpointId) break;

        logWarningIfTimeoutAlmostReached(pendingTxn);
        commit(pendingTxn.handle);
        pendingTxnIter.remove();
    }
}
```

这段代码的设计极其精妙：

- 遍历**所有 ≤ 当前 checkpointId** 的待提交事务，逐个 commit
- 这是**幂等**的——即使 JobManager 重发 `notifyCheckpointComplete`，已经 commit 过的事务从 map 中被移除，不会重复
- 如果 commit 抛异常会怎样？源码里 `recoverAndCommit` 的兜底逻辑会在重启时再来一次

而 `FlinkKafkaProducer.commit` 实现：

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

private void recycleTransactionalProducer(FlinkKafkaInternalProducer<byte[], byte[]> producer) {
    availableTransactionalIds.add(producer.getTransactionalId());
    producer.flush();
    producer.close(Duration.ofSeconds(0));   // 立即关闭，下次拿到 ID 再创建新 Producer
}
```

注意：commit 完成后，`transactionalId` 被**回收到池里**——所以 Producer 池实际上是 transactionalId 的池，而不是 Producer 实例的池。

### 3.6 recoverAndCommit / recoverAndAbort：故障恢复

**最关键的源码**——决定 Exactly-Once 是否真正落地。

#### 故障场景

```
Checkpoint N 完成（事务已 preCommit）
    │
    ▼
notifyCheckpointComplete 还未到达就宕机
    │
    ▼
作业从 Checkpoint N 恢复
    │
    ▼
recoverAndCommit(txnN) ← 必须执行 commit！
```

实现：

```java
@Override
protected void recoverAndCommit(KafkaTransactionState transaction) {
    if (transaction.isTransactional()) {
        FlinkKafkaInternalProducer<byte[], byte[]> producer = null;
        try {
            // 用同一个 transactionalId 重建 Producer
            producer = initTransactionalProducer(transaction.transactionalId, false);
            producer.resumeTransaction(transaction.producerId, transaction.epoch);
            producer.commitTransaction();
        } catch (InvalidTxnStateException | ProducerFencedException ex) {
            // 事务已经被另一个实例提交或回滚，这次跳过即可
            LOG.warn("Encountered error in recoverAndCommit", ex);
        } finally {
            if (producer != null) producer.close(Duration.ofSeconds(0));
        }
    }
}
```

精彩之处：

1. **使用相同的 `transactionalId`**：因为 Kafka 通过 `transactionalId` 唯一标识事务上下文，相同 ID 即可"接管"同一个事务
2. **`resumeTransaction`**：通过保存的 `producerId` 和 `epoch` 直接进入"已开放事务"的状态，**绕过 `initTransactions`**
3. **容忍 `InvalidTxnStateException`**：这意味着事务可能已经被其他流程 commit/abort 过——直接放过

而 `recoverAndAbort` 略简单：

```java
@Override
protected void recoverAndAbort(KafkaTransactionState transaction) {
    if (transaction.isTransactional()) {
        FlinkKafkaInternalProducer<byte[], byte[]> producer = null;
        try {
            producer = initTransactionalProducer(transaction.transactionalId, false);
            producer.initTransactions();    // 注意这里和 commit 不一样
        } finally {
            if (producer != null) producer.close(Duration.ofSeconds(0));
        }
    }
}
```

`initTransactions()` 自带"清理上一个未完成事务"的副作用——只要新 Producer 用相同 `transactionalId` 调用 `initTransactions`，Broker 会主动 abort 旧事务。

## 4. transactionalId 的生成规则

```java
String transactionalId = ...
    String.format("%s-%s-%d-%d", taskName, operatorUniqueId, subtaskIndex, generation);
```

- `taskName`：算子名（默认是 `Sink: <name>`）
- `operatorUniqueId`：算子的 hash UID（保证作业拓扑变更时 ID 不冲突）
- `subtaskIndex`：当前 Subtask 编号
- `generation`：池中第几个 Producer

**为什么这样设计？**

- 跨作业重启**保持稳定**——同一个 Subtask 重启后会用同样的 `transactionalId`，从而能通过 `resumeTransaction` 接管旧事务
- 跨 Subtask **不冲突**——每个 Subtask 有自己的命名空间

**一个常被忽视的坑**：如果你**给作业改名（taskName 变了）**或修改算子拓扑导致 `operatorUniqueId` 变化，旧事务的 `transactionalId` 与新作业不再匹配，恢复时会报：

```
ProducerFencedException: Producer attempted an operation with an old epoch.
```

详见系列第 7 篇。

## 5. Producer 池：availableTransactionalIds 详解

```java
private transient BlockingDeque<String> availableTransactionalIds;

private void initProducerPool() {
    for (int i = 0; i < kafkaProducersPoolSize; i++) {
        availableTransactionalIds.add(generateTransactionalId(i));
    }
}
```

池大小由 `kafkaProducersPoolSize` 控制，默认值 5。

为什么需要池？因为 Flink 允许并发 Checkpoint：

```
Checkpoint A: txnA.preCommit ──→ 还没收到 notifyCheckpointComplete
                                 │
                                 ▼
Checkpoint B: 已经 begin 了 txnB ← 需要新的 transactionalId
                                 │
                                 ▼
Checkpoint C: 已经 begin 了 txnC ← 又需要一个
```

如果池太小：

```
FlinkKafkaException: Too many ongoing snapshots.
Increase kafka producers pool size or decrease number of concurrent checkpoints.
```

**调优建议**：

- 默认 5 适用于"max concurrent checkpoints = 1"（即 Flink 默认配置）
- 如果开了多 Checkpoint 并发（罕见），需要把池调大
- 池太大也有副作用：每个 transactionalId 在 Broker 端都有元数据，过多会拖累事务协调器

## 6. snapshotState 全流程串起来

```java
@Override
public void snapshotState(FunctionSnapshotContext context) throws Exception {
    // 1. preCommit 当前事务
    long checkpointId = context.getCheckpointId();
    preCommit(currentTransactionHolder.handle);

    // 2. 把当前事务挪到 pendingCommit
    pendingCommitTransactions.put(checkpointId, currentTransactionHolder);

    // 3. 开启下一个事务
    currentTransactionHolder = beginTransactionInternal();

    // 4. 持久化所有未提交事务到 Flink 状态
    state.clear();
    state.add(new State<>(
            this.currentTransactionHolder,
            new ArrayList<>(pendingCommitTransactions.values()),
            userContext));
}
```

四步要点：

1. **preCommit**：把当前事务推到"已预提交"状态（Kafka 事务消息已经写入 broker log，但事务标记未提交）
2. **挪到 pendingCommit**：等待 commit 通知
3. **beginTransaction**：紧接着开新事务，承接后续 invoke
4. **state.clear + add**：把所有未完成事务一次性持久化到 Flink ListState

**state 中持久化的是哪些信息？** 关键是 `transactionalId`、`producerId`、`epoch`——三者足以让重启后的 Producer 通过 `resumeTransaction` 接管旧事务。

## 7. 与 Checkpoint Barrier 的协作时序

```
            Subtask 1            Subtask 2
              │                     │
   Barrier N ─┤                     ├── Barrier N
              │                     │
        snapshotState        snapshotState
              │                     │
        preCommit(flush)     preCommit(flush)
              │                     │
              ▼                     ▼
         状态发到 JobManager
              │                     │
              └──┬──────────┬───────┘
                 ▼          ▼
              JM 确认 Checkpoint N 完成
                      │
              ┌───────┴───────┐
              ▼               ▼
   notifyCheckpointComplete(N)（每个 Subtask）
              │               │
       commit(txnN)     commit(txnN)
```

要点：

- **预提交**发生在 Barrier 流过时（每个 Subtask 各自）
- **真正提交**发生在 JobManager 全局确认 Checkpoint 完成之后
- 任意一个 Subtask 在 preCommit 阶段失败 → 整个 Checkpoint 失败 → 所有事务由 `recoverAndAbort` 回滚

## 8. 容易踩的源码级陷阱

### 8.1 transaction.timeout.ms ≤ Broker 上限

Broker `transaction.max.timeout.ms` 默认 15 分钟，启动时 `FlinkKafkaProducer` 会与 Broker 协商，超过即报错。详见第 1 篇 6.2 节。

### 8.2 transactional.id.expiration.ms

Broker 端有 `transactional.id.expiration.ms`（默认 7 天）：超过这个时间没活动的 transactionalId 会被清除。如果你的作业停了一周再启动，所有 transactionalId 失效，重启会抛：

```
UnknownProducerIdException
```

解决：把 Broker 端 `transactional.id.expiration.ms` 调大到能覆盖最长停机时间。

### 8.3 max.in.flight.requests.per.connection ≤ 5

Kafka 幂等 Producer 内部用 sequence number 去重，要求**同一连接上未完成请求数 ≤ 5**。`FlinkKafkaProducer` 启动时如果发现 idempotence 开启但 `max.in.flight > 5`，会拒绝启动。

### 8.4 拓扑变更导致 transactionalId 失效

修改算子链、给算子加 `uid` 都可能让 `operatorUniqueId` 变化，旧 Checkpoint 的 transactionalId 在新作业里"找不到对应 Subtask"，进而报 `ProducerFencedException`。生产建议：

```java
sink.uid("kafka-sink-v1");        // 显式 uid
```

## 9. 完整源码导读路径

```
FlinkKafkaProducer.java
 ├── enum Semantic
 ├── inner class KafkaTransactionState
 ├── inner class KafkaTransactionContext
 │
 ├── invoke()                  → 写消息
 ├── beginTransaction()        → 取 transactionalId 起新事务
 ├── preCommit()               → flush
 ├── commit()                  → commitTransaction + 回收 ID
 ├── abort()                   → abortTransaction
 ├── recoverAndCommit()        → resumeTransaction + commit
 ├── recoverAndAbort()         → initTransactions（隐式 abort）
 │
 └── createTransactionalProducer / initTransactionalProducer

TwoPhaseCommitSinkFunction.java
 ├── snapshotState()           → preCommit + persist state
 ├── initializeState()         → 恢复 state，逐个 recoverAndCommit
 ├── notifyCheckpointComplete()→ 遍历 pendingCommit 调 commit
 └── inner class TransactionHolder
```

## 10. 本篇小结

- **2PC 在 Flink 中的实现**：preCommit（flush）→ snapshotState 持久化 → notifyCheckpointComplete 触发 commit
- **故障恢复**：`recoverAndCommit` 用相同 `transactionalId` + `resumeTransaction` 接管旧事务
- **Producer 池**：本质是 transactionalId 池，承载并发 Checkpoint
- **transactionalId 命名规则**：`{taskName}-{operatorUid}-{subtask}-{generation}`，拓扑变更会导致失配

下一篇我们将从源码走出来，进入**生产实战**——性能调优、监控指标、高可用部署的完整套路。

## 系列文章导航

| 序号 | 文章 |
|---|---|
| 第 1 篇 | Flink DataStream FlinkKafkaProducer 系列 1：快速入门 |
| 第 2 篇 | Flink DataStream FlinkKafkaProducer 系列 2：序列化机制 KafkaSerializationSchema 深度剖析 |
| 第 3 篇 | Flink DataStream FlinkKafkaProducer 系列 3：分区策略 FlinkKafkaPartitioner 与如何写入指定分区 |
| 第 4 篇 | Flink DataStream FlinkKafkaProducer 系列 4：三种交付语义 AT_MOST_ONCE / AT_LEAST_ONCE / EXACTLY_ONCE |
| 第 5 篇 | Flink DataStream FlinkKafkaProducer 系列 5：Exactly-Once 源码深度剖析 TwoPhaseCommitSinkFunction（本文） |
| 第 6 篇 | Flink DataStream FlinkKafkaProducer 系列 6：生产实战 性能调优 监控指标与高可用部署 |
| 第 7 篇 | Flink DataStream FlinkKafkaProducer 系列 7：常见错误排查 FAQ 与生产事故复盘 |
