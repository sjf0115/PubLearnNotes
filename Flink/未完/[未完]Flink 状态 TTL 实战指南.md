---
layout: post
author: smartsi
title: Flink State TTL 详解
date: 2022-02-27 14:56:01
tags:
  - Flink

categories: Flink
permalink: state-ttl-for-apache-flink-how-to-limit-the-lifetime-of-state
---

> Flink 1.14 版本

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

默认情况下，过期状态值会在读取时显式删除，例如 ValueState#value，如果配置的状态后端支持，也可以在后台定期回收。也可以在 StateTtlConfig 中禁用后台清理：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .disableCleanupInBackground()
    .build();
```
为了对后台的一些特殊清理进行更细粒度的控制，您可以按如下所述单独配置。目前，堆状态后端依赖增量清理，RocksDB 后端使用压缩过滤器进行后台清理。

### 3.1 全量快照清理策略

我们可以在生成全量快照(Snapshot/Checkpoint)时清理过期状态，这可以大大减小快照存储，但是本地状态中过期数据不会被清理。唯有当作业重启并从上一个快照恢复后，本地状态才会实际减小，因此可能仍然不能解决内存压力的问题。如果要使用该过期请策略，请参考如下所示代码：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.time.Time;

StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .cleanupFullSnapshot()
    .build();
```
这种过期清理策略对开启了增量检查点的 RocksDB 状态后端无效。

> 对于现有作业，可以随时在 StateTtlConfig 中启用或停用该清理策略，例如从保存点重新启动后。

全量快照清理策略对应的实现是 EmptyCleanupStrategy：
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

在 Flink 1.6.0 版本中，当生成 Checkpoint 或者 Savepoint 全量快照时会自动删除过期状态。需要注意的是：
- 过期状态删除不适用于增量 Checkpoint，必须明确启用全量快照才能删除过期状态。
- 全量快照的大小会减小，但本地状态存储大小保持不变。只有当用户从快照重新加载其状态到本地时，才会清除用户的本地状态。

由于上述这些限制，为了改善用户体验，Flink 1.8.0 引入了两种逐步触发状态清理的策略，分别是针对 Heap StateBackend 的 INCREMENTAL_CLEANUP（对应 IncrementalCleanupStrategy 实现）以及针对 RocksDB StateBackend 的 ROCKSDB_COMPACTION_FILTER（对应 RocksdbCompactFilterCleanupStrategy 实现）。

#### 3.2.1 INCREMENTAL_CLEANUP

我们先看一下针对 Heap StateBackend 的 INCREMENTAL_CLEANUP。如果使用此清理策略，那么存储后端会为所有状态条目维护一个惰性全局迭代器。每次触发增量清理时，迭代器都会前进。检查遍历的状态条目并清除过期的条目。


如果要使用该过期请策略，请参考如下所示代码：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .cleanupIncrementally(5, false)
    .build();
```
该策略有两个参数：第一个参数是每次触发清理时检查的状态条目数，总是在状态访问时触发。第二个参数定义了在每次处理记录时是否额外触发清理。堆状态后端的默认后台清理每次触发检查 5 个条目，处理记录时不会额外进行过期数据清理。

```java
public Builder cleanupIncrementally(@Nonnegative int cleanupSize, boolean runCleanupForEveryRecord) {
    strategies.put(
        CleanupStrategies.Strategies.INCREMENTAL_CLEANUP,
        new IncrementalCleanupStrategy(cleanupSize, runCleanupForEveryRecord)
    );
    return this;
}
```

注意：
- 如果该状态没有被访问或者没有记录需要处理，那么过期状态会一直存在。
- 增量清理所花费的时间会增加记录处理延迟。
- 目前仅堆状态后端实现了增量清理。为 RocksDB 设置增量清理不会有任何效果。
- 如果堆状态后端与同步快照一起使用，全局迭代器在迭代时保留所有 Key 的副本，因为它的特定实现不支持并发修改。启用此功能将增加内存消耗。异步快照没有这个问题。
- 对于现有作业，可以随时在 StateTtlConfig 中激活或停用此清理策略。

#### 3.3 RocksDB 压缩时清理

如果使用 RocksDB 状态后端，则会调用 Flink 特定的压缩过滤器进行后台清理。RocksDB 定期运行异步压缩以合并状态更新并减少存储。Flink 压缩过滤器使用 TTL 检查状态条目的过期时间戳并排除过期值。这个特性可以在 StateTtlConfig 中配置：
```java
import org.apache.flink.api.common.state.StateTtlConfig;

StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .cleanupInRocksdbCompactFilter(1000)
    .build();
```
RocksDB 压缩过滤器会在每次处理一定数量的状态条目后从 Flink 查询当前时间戳，用于检查过期时间。您可以更改并将自定义值传递给 StateTtlConfig.newBuilder(...).cleanupInRocksdbCompactFilter(long queryTimeAfterNumEntries) 方法。更频繁地更新时间戳可以提高清理速度，但会降低压缩性能，因为它使用来自本机代码的 JNI 调用。RocksDB 状态后端的默认后台清理每处理 1000 个条目就查询当前时间戳。我们也可以通过激活 FlinkCompactionFilter 的调试级别来从 RocksDB 过滤器的本机代码激活调试日志：
```
log4j.logger.org.rocksdb.FlinkCompactionFilter=DEBUG
```

```java
public Builder cleanupInRocksdbCompactFilter(long queryTimeAfterNumEntries) {
    strategies.put(
        CleanupStrategies.Strategies.ROCKSDB_COMPACTION_FILTER,
        new RocksdbCompactFilterCleanupStrategy(queryTimeAfterNumEntries)
    );
    return this;
}
```


注意：
- 在压缩期间调用 TTL 过滤器会降低压缩的速度。TTL 过滤器必须解析上次访问的时间戳，并检查正在压缩 Key 的每个存储状态条目的到期时间。在集合状态类型（列表或映射）的情况下，还会为每个存储的元素调用检查。
- 如果此功能与具有非固定字节长度的元素的列表状态一起使用，则本机 TTL 过滤器必须在每个状态条目上通过 JNI 额外调用元素的 Flink java 类型序列化器，其中至少第一个元素已过期才能确定下一个未过期元素的偏移量。
- 对于现有作业，可以随时在 StateTtlConfig 中激活或停用此清理策略。

## 4. 注意事项

当从状态中恢复时，如果之前没有开启 TTL 功能，现在尝试启用 TTL 时，会导致兼容性失败以及 StateMigrationException。

状态后端将上次修改的时间戳与值一起存储，这意味着启用此功能会增加状态存储。堆状态后端存储一个额外的 Java 对象，其中包含对用户状态对象的引用和内存中的原始 long 值。 RocksDB 状态后端为每个存储值、列表条目或映射条目添加 8 个字节。

TTL 配置不是检查点或保存点的一部分，而是 Flink 处理当前运行作业的一种方式。

仅当用户值序列化器可以处理 NULL 值时，具有 TTL 的 Map 状态才支持 NULL 值。如果序列化器不支持 NULL 值，则可以使用 NullableSerializer 进行封装，但需要以序列化形式增加一个字节的代价。

PyFlink DataStream API 仍然不支持状态 TTL。
。。。
