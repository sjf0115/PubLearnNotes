在 Flink 1.13 版本之前，StateBackend 提供了三个开箱即用的 StateBackend：MemoryStateBackend、FsStateBackend 以及 RocksDBStateBackend。该版本下的 StateBackend 把状态存储(如何在 TM 上本地存储和访问状态)和 Checkpoint 持久化(Checkpoint 如何持久化状态)笼统的混在一起，导致初学者对此感觉很混乱，很难理解。

为了解决这种混乱的问题，Flink 1.13 版本将之前的 StateBackend 拆分成新的 StateBackend 和 CheckpointStorage 两个功能：
- 新的 StateBackend 的概念变窄，只描述状态访问和存储，定义状态在 TM 本地存储的位置和方式。
- CheckpointStorage 描述了 Checkpoint 行为，定义 Checkpoint 的存储位置和方式以进行故障恢复。

为了更好的理解，我们弃用了老的 MemoryStateBackend、FsStateBackend 和 RocksDBStateBackend。StateBackend 的状态存储功能使用 HashMapStateBackend 和 EmbeddedRocksDBStateBackend 代替，Checkpoint 持久化功能使用 FileSystemCheckpointStorage 和 JobManagerCheckpointStorage 来代替。
> 详细请查阅[Flink 1.13 StateBackend 与 CheckpointStorage 拆分](https://smartsi.blog.csdn.net/article/details/123057769)

| Flink 1.13 之后     | Flink 1.13 之前     |
| :------------- | :------------- |
| HashMapStateBackend（默认）       | MemoryStateBackend（默认）      |
| EmbeddedRocksDBStateBackend | RocksDBStateBackend|
| | FsStateBackend |

在这篇文章中我们重点介绍新版本的 StateBackend。Flink 中提供了两种不同的实现，一种是哈希表状态后端 HashMapStateBackend，另一种是内嵌 RocksDB 状态后端 EmbeddedRocksDBStateBackend。如果没有特别配置，系统默认的状态后端是 HashMapStateBackend。

## 1. StateBackend

### 1.1 HashMapStateBackend

这种方式会把状态存放在内存里。具体实现上，HashMapStateBackend 在内部会直接把状态当作对象(Object)保存在 TaskManager 的 JVM 堆(heap)上。普通的状态，以及窗口中收集的数据和触发器(Triggers)，都会以键值对的形式存储起来，所以底层是一个哈希表(HashMap)，这种状态后端也因此得名。

HashMapStateBackend 是将本地状态全部放入内存中，这样可以获得最快的读写速度，使计算性能达到最佳，代价则是内存的占用。HashMapStateBackend 适用于具有大状态、长窗口、大键值状态的作业，对高可用方案也是有效的。

### 1.2 EmbeddedRocksDBStateBackend

RocksDB 是一种内嵌的 KV 存储数据库，可以把数据持久化到本地硬盘。配置 EmbeddedRocksDBStateBackend 后，会将处理中的数据全部放入 RocksDB 数据库中，RocksDB 默认存储在 TaskManager 的本地数据目录里。

与 HashMapStateBackend 直接在堆内存中存储对象不同，这种方式下状态主要是放在 RocksDB 中，可以保留非常大的状态(相比 HashMapStateBackend)。在 EmbeddedRocksDBStateBackend 中保留的状态大小仅受可用磁盘空间量的限制。数据被存储为序列化的字节数组(Byte Arrays)，读写操作需要序列化/反序列化，因此状态的访问性能要差一些。另外，因为做了序列化，key 的比较也会按照字节进行，而不是直接调用 hashCode()和 equals() 方法。

EmbeddedRocksDBStateBackend 始终执行的是异步快照，也就是不会因为保存检查点而阻塞数据的处理，同时也是目前唯一提供增量检查点的状态后端。EmbeddedRocksDBStateBackend 适用于状态非常大、窗口非常长、键/值状态很大的应用场景，也非常适合高可用方案。

## 2. 如何正确的选择 StateBackend

如何正确的选择 StateBackend，就需要知道 HashMapStateBackend 和 EmbeddedRocksDBStateBackend 两种状态后端的区别。最大的区别就在于本地状态存放在哪里：前者存放在内存中，后者存放在 RocksDB 中。在实际应用中，选择哪种状态后端，主要是需要根据业务需求在处理性能和应用扩展性上做一个权衡。

HashMapStateBackend 每次状态访问和更新都是对 Java 堆上的对象进行操作，因此读写速度非常快；但是，状态的大小会受到集群可用内存的限制，如果应用的状态随着时间不停地增长，就会耗尽内存资源。而 EmbeddedRocksDBStateBackend 是基于 RocksDB 存储，所以可以根据可用磁盘空间进行扩展，而且是唯一支持增量检查点的状态后端，所以非常适合非常大状态的存储。但是由于每次状态访问和更新都需要做序列化/反序列化，而且可能需要直接从磁盘读取数据，这就会导致性能的降低，平均读写性能要比 HashMapStateBackend 慢一个数量级。

如果处理状态不是很大并追求处理的高性能，可以选择 HashMapStateBackend；如果处理的状态非常大可以选择 EmbeddedRocksDBStateBackend。

## 3. 配置 StateBackend

### 3.1 配置全局默认状态后端

在不做配置的时候，应用程序使用的默认状态后端是由集群配置文件 flink-conf.yaml 中指定的，配置的 Key 名称为 state.backend。这个默认配置对集群上运行的所有作业都有效，我们可以通过更改配置值来改变默认的状态后端。

需要注意的是 flink-conf.yaml 中关于 'state.backend' 的值和注释还是老版本的说明并没有更新：
```
# Supported backends are 'jobmanager', 'filesystem', 'rocksdb', or the
# <class-name-of-factory>.
#
# state.backend: filesystem
```
> 具体可以查阅 [FLINK-25601](https://issues.apache.org/jira/browse/FLINK-25601)，目前还没有明确说明在哪个版本修复

实际应该如下所示：
```
# Supported backends are 'hashmap', 'rocksdb', or the
# <class-name-of-factory>.
#
# state.backend: hashmap
```
> 'jobmanager', 'filesystem', 'rocksdb' 三种值是 Flink 1.13.0 之前老版本的状态后端配置。新版本中对应拆分为 state.backend 和 state.checkpoint-storage 两个配置选项。具体查阅[state.backend](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/deployment/config/#state-backend) 和 [state.checkpoint-storage](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/deployment/config/#state-checkpoint-storage) 配置说明。

目前 state.backend 只支持 'hashmap' 和 'rocksdb' 两种快捷方式名称，分别对应 HashMapStateBackend 和 EmbeddedRocksDBStateBackend 状态后端。如果想配置 HashMapStateBackend 为默认状态后端，只需要将 state.backend 配置为 hashmap 即可：
```
# 默认状态后端
state.backend: hashmap
# 存放检查点的文件路径
state.checkpoints.dir: hdfs://namenode:40010/flink/checkpoints
```
> 这里的 state.checkpoints.dir 配置项，定义了状态后端将检查点和元数据写入的目录。

除了可以指定快捷方式名称，此外你还可以指定一个实现了状态后端工厂 StateBackendFactory 的类的完全限定类名。

### 3.2 配置作业状态后端

除了配置全局默认的状态后端后，你还可以在代码中为当前作业单独配置状态后端，这个配置会覆盖掉集群配置文件的默认值。

每个作业独立的状态后端，可以在代码中，基于作业的执行环境直接设置。如下代码所示，使用 HashMapStateBackend：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new HashMapStateBackend());
```
> 完整代码示例请查阅[HashMapStateBackendExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/statebackend/HashMapStateBackendExample.java)

上面代码设置的是 HashMapStateBackend，如果想要设置 EmbeddedRocksDBStateBackend，可以用下面的配置方式:
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new EmbeddedRocksDBStateBackend());
```
> 完整代码示例请查阅[EmbeddedRocksDBStateBackendExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/statebackend/EmbeddedRocksDBStateBackendExample.java)

需要注意，如果想在 IDE 中使用 EmbeddedRocksDBStateBackend，需要为 Flink 项目添加如下依赖:
```xml
<dependency>
   <groupId>org.apache.flink</groupId>
<artifactId>flink-statebackend-rocksdb_${scala.binary.version}</artifactId>
   <version>1.13.5</version>
</dependency>
```
而由于 Flink 发行版中默认就包含了 RocksDB，所以只要我们的代码中没有使用 RocksDB 的相关内容，就不需要引入这个依赖。即使我们在 flink-conf.yaml 配置文件中设定了 state.backend 为 rocksdb，也可以直接正常运行。
