


可以将生存时间 (TTL) 分配给任何类型的 Keyed State。如果配置了 TTL 并且状态值已过期，则将尽最大努力清理存储的值。

所有状态集合类型都支持每个条目的 TTL。 这意味着列表元素和映射条目独立过期。

为了使用状态 TTL，必须首先构建一个 StateTtlConfig 配置对象。通过给状态描述符传递配置来启用 TTL 功能：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.time.Time;

StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
    .setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
    .build();

ValueStateDescriptor<String> stateDescriptor = new ValueStateDescriptor<>("state", String.class);
stateDescriptor.enableTimeToLive(ttlConfig);
```
TTL 配置需要注意一下几个事项：
- newBuilder 方法的第一个参数是必需的，表示 Time 类型过期时间。
- 状态 TTL 需要刷新时，需要配置更新类型参数(UpdateType，默认为 OnCreateAndWrite)
  - StateTtlConfig.UpdateType.OnCreateAndWrite - 仅在状态创建以及写入更新状态时更新 TTL
  - StateTtlConfig.UpdateType.OnReadAndWrite - 同上，不过读取状态时也更新 TTL
- 状态可见性配置在读取状态时是否返回过期值（如果还没有清除，默认值为 NeverReturnExpired）：
  - StateTtlConfig.StateVisibility.NeverReturnExpired：永远不会返回过期值
  - StateTtlConfig.StateVisibility.ReturnExpiredIfNotCleanedUp：如果还没有清除则返回

状态后端将上次修改的时间戳与值一起存储，这意味着启用此功能会增加状态存储。堆状态后端存储一个额外的 Java 对象，其中包含对用户状态对象的引用和内存中的原始 long 值。 RocksDB 状态后端为每个存储值、列表条目或映射条目添加 8 个字节。

当前仅支持与处理时间相关的 TTL。

如果尝试启用 TTL 来恢复之前没有配置 TTL 的状态将导致兼容性失败和 StateMigrationException，反之亦然。

TTL 配置不是检查点或保存点的一部分，而是 Flink 处理当前运行作业的一种方式。

仅当用户值序列化器可以处理 NULL 值时，具有 TTL 的 Map 状态才支持 NULL 值。如果序列化器不支持 NULL 值，则可以使用 NullableSerializer 进行封装，但需要以序列化形式增加一个字节的代价。

PyFlink DataStream API 仍然不支持状态 TTL。

### 2. 清除过期状态

默认情况下，过期值会在读取时显式删除，例如 ValueState#value，如果配置的状态后端支持，则在后台定期垃圾回收。也可以在 StateTtlConfig 中禁用后台清理：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .disableCleanupInBackground()
    .build();
```
为了对后台的一些特殊清理进行更细粒度的控制，您可以按如下所述单独配置它。目前，堆状态后端依赖增量清理，RocksDB 后端使用压缩过滤器进行后台清理。

#### 2.1 完整快照中的清理

我们可以在生成完整状态快照时激活清理，这将大大减小存储。在当前实现下，本地状态不会被清除，但如果从之前的快照恢复时，不会包括已删除的过期状态。如下所示在 StateTtlConfig 中配置：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.time.Time;

StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .cleanupFullSnapshot()
    .build();
```
此选项不适用于 RocksDB 状态后端的增量检查点。

> 对于现有作业，可以随时在 StateTtlConfig 中激活或停用此清理策略，例如从保存点重新启动后。

#### 2.2 增量清理

另一种选择是逐步触发一些状态条目的清理。触发器可以是每个状态访问或每个记录处理的回调。如果某个状态使用此清理策略，那么存储后端会为所有状态条目维护一个惰性全局迭代器。每次触发增量清理时，迭代器都会前进。检查遍历的状态条目并清除过期的条目。这个特性可以在 StateTtlConfig 中配置：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.seconds(1))
    .cleanupIncrementally(10, true)
    .build();
```
该策略有两个参数。第一个是每次触发清除的检查状态条目数。它总是按每个状态访问触发。第二个参数定义是否在每次记录处理时额外触发清理。堆状态后端的默认后台清理检查 5 个条目，记录处理时不进行清理。

注意：
- 如果该状态没有被访问或者没有记录需要处理，那么过期状态会一直存在。
- 增量清理所花费的时间会增加记录处理延迟。
- 目前仅堆状态后端实现了增量清理。为 RocksDB 设置增量清理不会有任何效果。
- 如果堆状态后端与同步快照一起使用，全局迭代器在迭代时保留所有 Key 的副本，因为它的特定实现不支持并发修改。启用此功能将增加内存消耗。异步快照没有这个问题。
- 对于现有作业，可以随时在 StateTtlConfig 中激活或停用此清理策略。

#### 2.3 RocksDB 压缩期间的清理

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
注意：
- 在压缩期间调用 TTL 过滤器会降低压缩的速度。TTL 过滤器必须解析上次访问的时间戳，并检查正在压缩 Key 的每个存储状态条目的到期时间。在集合状态类型（列表或映射）的情况下，还会为每个存储的元素调用检查。
- 如果此功能与具有非固定字节长度的元素的列表状态一起使用，则本机 TTL 过滤器必须在每个状态条目上通过 JNI 额外调用元素的 Flink java 类型序列化器，其中至少第一个元素已过期才能确定下一个未过期元素的偏移量。
- 对于现有作业，可以随时在 StateTtlConfig 中激活或停用此清理策略。



。。。
