---
layout: post
author: smartsi
title: Flink State TTL 详解
date: 2022-02-27 14:56:01
tags:
  - Flink

categories: Flink
permalink: state-ttl-for-apache-flink
---

> Flink 1.13 版本

在某些场景下 Flink 用户状态一直在无限增长，一些用例需要能够自动清理旧的状态。例如，作业中定义了超长的时间窗口，或者在动态表上应用了无限范围的 GROUP BY 语句。此外，目前开发人员需要自己完成 TTL 的临时实现，例如使用可能不节省存储空间的计时器服务。还有一个比较重要的点是一些法律法规也要求必须在有限时间内访问数据。

对于这些情况，旧版本的 Flink 并不能很好解决，因此 Apache Flink 1.6.0 版本引入了状态 TTL 特性。该特性可以让 Keyed 状态在一定时间内没有被使用下自动过期。如果配置了 TTL 并且状态已过期，那么会尽最大努力来清理过期状态。

## 1. 用法

可以在 [Flink 官方文档](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/datastream/fault-tolerance/state/#state-time-to-live-ttl)中看到 State TTL 如下使用方式：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.time.Time;

// 状态描述符
ValueStateDescriptor<Long> stateDescriptor = new ValueStateDescriptor<>("LastLoginState", Long.class);
// 设置 TTL
StateTtlConfig ttlConfig = StateTtlConfig
        .newBuilder(Time.minutes(1))
        .setTtlTimeCharacteristic(StateTtlConfig.TtlTimeCharacteristic.ProcessingTime)
        .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
        .setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
        .cleanupFullSnapshot()
        .build();
stateDescriptor.enableTimeToLive(ttlConfig);
```

可以看到，要使用 State TTL 功能，首先要定义一个 StateTtlConfig 对象。StateTtlConfig 对象可以通过构造器模式来创建，典型地用法是传入一个 Time 对象作为 TTL 时间，然后可以设置时间处理语义(TtlTimeCharacteristic)、更新类型(UpdateType)以及状态可见性(StateVisibility)。当创建完 StateTtlConfig 对象，可以在状态描述符中启用 State TTL 功能。

> [完整代码](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/state/StateTTLExample.java)

如下所示设置1分钟的过期时间：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/state-ttl-for-apache-flink-1.png?raw=true)

## 2. 参数说明

### 2.1 过期时间

newBuilder 方法的参数是必需的，表示状态的过期时间，是一个 org.apache.flink.api.common.time.Time 对象。一旦设置了 TTL，那么如果上次访问的时间戳 + TTL 超过了当前时间，则表明状态过期了（这是一个简化的说法，严谨的定义请参考 org.apache.flink.runtime.state.ttl.TtlUtils 类中关于 expired 的实现） 。

### 2.2 时间处理语义

TtlTimeCharacteristic 表示 State TTL 功能可以使用的时间处理语义：
```java
public enum TtlTimeCharacteristic {
    ProcessingTime
}
```
截止到目前 Flink 1.14，只支持 ProcessingTime 时间处理语义。EventTime 处理语义还在开发中，具体可以追踪[FLINK-12005](https://issues.apache.org/jira/browse/FLINK-12005)。

可以通过如下方法显示设置：
```java
setTtlTimeCharacteristic(StateTtlConfig.TtlTimeCharacteristic.ProcessingTime)
```

### 2.3 更新类型

UpdateType 表示状态时间戳(上次访问时间戳)的更新时机：
```java
public enum UpdateType {
    Disabled,
    OnCreateAndWrite,
    OnReadAndWrite
}
```
如果设置为 Disabled，则表示禁用 TTL 功能，状态不会过期；如果设置为 OnCreateAndWrite，那么表示在状态创建或者每次写入时都会更新时间戳；如果设置为 OnReadAndWrite，那么除了在状态创建和每次写入时更新时间戳外，读取状态也会更新状态的时间戳。如果不配置默认为 OnCreateAndWrite。

可以通过如下方法显示设置：
```java
// 等价于 updateTtlOnCreateAndWrite()
setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
// 等价于 updateTtlOnReadAndWrite()
setUpdateType(StateTtlConfig.UpdateType.OnReadAndWrite)
```

### 2.4 状态可见性

StateVisibility 表示状态可见性，在读取状态时是否返回过期值：
```java
public enum StateVisibility {
    ReturnExpiredIfNotCleanedUp,
    NeverReturnExpired
}
```
如果设置为 ReturnExpiredIfNotCleanedUp，那么当状态值已经过期，但还未被真正清理掉，就会返回给调用方；如果设置为 NeverReturnExpired，那么一旦状态值过期了，就永远不会返回给调用方，只会返回空状态。

可以通过如下方法显示设置：
```java
// 等价于 returnExpiredIfNotCleanedUp()
setStateVisibility(StateTtlConfig.StateVisibility.ReturnExpiredIfNotCleanedUp)
// 等价于 neverReturnExpired()
setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
```

## 3. 过期清理策略

从 Flink 1.6.0 版本开始，当生成 Checkpoint 或者 Savepoint 全量快照时会自动删除过期状态。但是，过期状态删除不适用于增量 Checkpoint，必须明确启用全量快照才能删除过期状态。全量快照的大小会减小，但本地状态存储大小并不会减少。只有当用户从快照重新加载其状态到本地时，才会清除用户的本地状态。由于上述这些限制，为了改善用户体验，Flink 1.8.0 引入了两种逐步触发状态清理的策略，分别是针对 Heap StateBackend 的增量清理策略以及针对 RocksDB StateBackend 的压缩清理策略。到目前为止，一共有三种过期清理策略：
- 全量快照清理策略()
- 增量清理策略
- RocksDB 压缩清理策略

### 3.1 全量快照清理策略

我们先看一下全量快照清理策略，这种策略可以在生成全量快照(Snapshot/Checkpoint)时清理过期状态，这样可以大大减小快照存储，但需要注意的是本地状态中过期数据并不会被清理。唯有当作业重启并从上一个快照恢复后，本地状态才会实际减小。如果要在 DataStream 中使用该过期请策略，请参考如下所示代码：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.time.Time;

StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .cleanupFullSnapshot()
    .build();
```
这种过期清理策略对开启了增量检查点的 RocksDB 状态后端无效。

全量快照清理策略(FULL_STATE_SCAN_SNAPSHOT)对应的实现是 EmptyCleanupStrategy：
```java
static final CleanupStrategy EMPTY_STRATEGY = new EmptyCleanupStrategy();
public Builder cleanupFullSnapshot() {
    strategies.put(CleanupStrategies.Strategies.FULL_STATE_SCAN_SNAPSHOT, EMPTY_STRATEGY);
    return this;
}

static class EmptyCleanupStrategy implements CleanupStrategy {
    private static final long serialVersionUID = 1373998465131443873L;
}
```

### 3.2 增量清理策略

我们再来看一下针对 Heap StateBackend 的增量清理策略。这种策略下存储后端会为所有状态条目维护一个惰性全局迭代器。每次触发增量清理时，迭代器都会向前迭代删除已遍历的过期数据。如果要在 DataStream 中使用该过期请策略，请参考如下所示代码：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .cleanupIncrementally(5, false)
    .build();
```
该策略有两个参数：第一个参数表示每次触发清理时需要检查的状态条目数，总是在状态访问时触发。第二个参数定义了在每次处理记录时是否额外触发清理。堆状态后端的默认后台清理每次触发检查 5 个条目，处理记录时不会额外进行过期数据清理。

增量清理策略(INCREMENTAL_CLEANUP)对应的实现是 IncrementalCleanupStrategy：
```java
public Builder cleanupIncrementally(@Nonnegative int cleanupSize, boolean runCleanupForEveryRecord) {
    strategies.put(
        CleanupStrategies.Strategies.INCREMENTAL_CLEANUP,
        new IncrementalCleanupStrategy(cleanupSize, runCleanupForEveryRecord)
    );
    return this;
}

public static class IncrementalCleanupStrategy implements CleanupStrategies.CleanupStrategy {
    static final IncrementalCleanupStrategy DEFAULT_INCREMENTAL_CLEANUP_STRATEGY =
            new IncrementalCleanupStrategy(5, false);
    private final int cleanupSize;
    private final boolean runCleanupForEveryRecord;
    private IncrementalCleanupStrategy(int cleanupSize, boolean runCleanupForEveryRecord) {
        this.cleanupSize = cleanupSize;
        this.runCleanupForEveryRecord = runCleanupForEveryRecord;
    }
    ...
}
```

需要注意的是：
- 如果该状态没有被访问或者没有记录需要处理，那么过期状态会一直存在。
- 增量清理所花费的时间会增加记录处理延迟。
- 目前仅堆状态后端实现了增量清理。为 RocksDB 状态后端设置增量清理不会有任何效果。
- 如果堆状态后端与同步快照一起使用，全局迭代器在迭代时保留所有 Key 的副本，因为它的特定实现不支持并发修改。启用此功能将增加内存消耗。异步快照没有这个问题。
- 对于现有作业，可以随时在 StateTtlConfig 中启用或者停用此清理策略。

### 3.3 RocksDB 压缩清理策略

我们最后再来看一下 RocksDB 压缩清理策略。如果使用 RocksDB StateBackend，则会调用 Flink 指定的压缩过滤器进行后台清理。RocksDB 周期性运行异步压缩来合并状态更新并减少存储。Flink 压缩过滤器使用 TTL 检查状态条目的过期时间戳并删除过期状态值。如果要在 DataStream 中使用该过期请策略，请参考如下所示代码：
```java
import org.apache.flink.api.common.state.StateTtlConfig;

StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .cleanupInRocksdbCompactFilter(1000)
    .build();
```
RocksDB 压缩过滤器在每次处理一定状态条目后，查询当前的时间戳并检查是否过期。频繁地更新时间戳可以提高清理速度，但同样也会降低压缩性能。RocksDB 状态后端的默认每处理 1000 个条目就查询当前时间戳。

RocksDB 压缩清理策略(ROCKSDB_COMPACTION_FILTER)对应的实现是 RocksdbCompactFilterCleanupStrategy：
```java
public Builder cleanupInRocksdbCompactFilter(long queryTimeAfterNumEntries) {
    strategies.put(
        CleanupStrategies.Strategies.ROCKSDB_COMPACTION_FILTER,
        new RocksdbCompactFilterCleanupStrategy(queryTimeAfterNumEntries)
    );
    return this;
}

public static class RocksdbCompactFilterCleanupStrategy implements CleanupStrategies.CleanupStrategy {
    private static final long serialVersionUID = 3109278796506988980L;

    static final RocksdbCompactFilterCleanupStrategy DEFAULT_ROCKSDB_COMPACT_FILTER_CLEANUP_STRATEGY =
                    new RocksdbCompactFilterCleanupStrategy(1000L);

    private final long queryTimeAfterNumEntries;
    private RocksdbCompactFilterCleanupStrategy(long queryTimeAfterNumEntries) {
        this.queryTimeAfterNumEntries = queryTimeAfterNumEntries;
    }
    ...
}
```

> 在压缩期间调用 TTL 过滤器会降低压缩速度。TTL 过滤器必须解析上次访问的时间戳，并检查正在压缩 Key 的每个存储状态条目的到期时间。在集合状态类型（List或 Map）的情况下，还会为每个存储的元素调用检查。

## 4. 注意事项

当从状态中恢复时，之前设置的 TTL 过期时间不会丢失，还会继续生效。如下所示为登录用户设置5分钟的过期时间：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/state-ttl-for-apache-flink-2.png?raw=true)

在状态过期之前取消作业并触发 Savepoint，如下所示：
```
flink cancel -s hdfs://localhost:9000/flink/savepoints/ 3b37dece248dafc7330b854c38bf526d
```
然后再从 Savepoint 中恢复作业：
```
flink run -s hdfs://localhost:9000/flink/savepoints/savepoint-c82ee3-e7ca58626e3b -c com.flink.example.stream.state.state.StateTTLExample flink-example-1.0.jar
```
如果用户在首次登录后5分钟内再次登录，用户的上一次登录时间保持不变，超过5分钟则重新记录首次登录时间：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/state-ttl-for-apache-flink-3.png?raw=true)

当从 Checkpoint/Savepoint 恢复时，TTL 的状态（是否开启）必须和之前保持一致，否则会遇到如下兼容性问题：
```java
2022-03-01 22:34:33
java.lang.RuntimeException: Error while getting state
	at org.apache.flink.runtime.state.DefaultKeyedStateStore.getState(DefaultKeyedStateStore.java:62)
	at org.apache.flink.streaming.api.operators.StreamingRuntimeContext.getState(StreamingRuntimeContext.java:203)
	at com.flink.example.stream.state.state.StateTTLExample$1.open(StateTTLExample.java:82)
	at org.apache.flink.api.common.functions.util.FunctionUtils.openFunction(FunctionUtils.java:34)
	at org.apache.flink.streaming.api.operators.AbstractUdfStreamOperator.open(AbstractUdfStreamOperator.java:102)
	at org.apache.flink.streaming.runtime.tasks.OperatorChain.initializeStateAndOpenOperators(OperatorChain.java:437)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restoreGates(StreamTask.java:574)
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$1.call(StreamTaskActionExecutor.java:55)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restore(StreamTask.java:554)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:756)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:563)
	at java.lang.Thread.run(Thread.java:748)
Caused by: org.apache.flink.util.StateMigrationException: For heap backends, the .new state serializer (org.apache.flink.runtime.state.ttl.TtlStateFactory$TtlSerializer@724383d2) must not be incompatible with the old state serializer (org.apache.flink.api.common.typeutils.base.LongSerializer@13921758).
  	at org.apache.flink.runtime.state.heap.HeapKeyedStateBackend.tryRegisterStateTable(HeapKeyedStateBackend.java:214)
  	at org.apache.flink.runtime.state.heap.HeapKeyedStateBackend.createInternalState(HeapKeyedStateBackend.java:279)
  	at org.apache.flink.runtime.state.ttl.TtlStateFactory.createTtlStateContext(TtlStateFactory.java:211)
  	at org.apache.flink.runtime.state.ttl.TtlStateFactory.createValueState(TtlStateFactory.java:146)
  	at org.apache.flink.runtime.state.ttl.TtlStateFactory.createState(TtlStateFactory.java:133)
  	at org.apache.flink.runtime.state.ttl.TtlStateFactory.createStateAndWrapWithTtlIfEnabled(TtlStateFactory.java:70)
  	at org.apache.flink.runtime.state.AbstractKeyedStateBackend.getOrCreateKeyedState(AbstractKeyedStateBackend.java:301)
  	at org.apache.flink.runtime.state.AbstractKeyedStateBackend.getPartitionedState(AbstractKeyedStateBackend.java:352)
  	at org.apache.flink.runtime.state.DefaultKeyedStateStore.getPartitionedState(DefaultKeyedStateStore.java:115)
  	at org.apache.flink.runtime.state.DefaultKeyedStateStore.getState(DefaultKeyedStateStore.java:60)
  	... 11 more
```
建议使用状态的时候最好就先加上 StateTtlConfig，如果不需要过期清理，可以先设置为 StateTtlConfig.disableCleanupInBackground()，如果后续需要过期清理，再配置过期时间以及清理策略。
