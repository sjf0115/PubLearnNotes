
状态后端 StateBackend 是一个'开箱即用'的组件，可以在不改变应用程序逻辑的情况下独立配置。Flink 中提供了两种不同的 StateBackend，一种是哈希表状态后端 HashMapStateBackend，另一种是内嵌 RocksDB 状态后端 EmbeddedRocksDBStateBackend。如果没有特别配置，系统默认的状态后端是 HashMapStateBackend。

### 1.1 StateBackend 分类

#### 1.1.1 HashMapStateBackend

这种方式会把状态存放在内存里。具体实现上，HashMapStateBackend 在内部会直接把状态当作对象(objects)保存在 TaskManager 的 JVM 堆(heap)上。普通的状态，以及窗口中收集的数据和触发器(Triggers)，都会以键值对的形式存储起来，所以底层是一个哈希表(HashMap)，这种状态后端也因此得名。

HashMapStateBackend 是将本地状态全部放入内存中，这样可以获得最快的读写速度，使计算性能达到最佳，代价则是内存的占用。HashMapStateBackend 适用于具有大状态、长窗口、大键值状态的作业，对所有高可用性设置也是有效的。

#### 1.1.2 EmbeddedRocksDBStateBackend

RocksDB 是一种内嵌的 KV 存储数据库，可以把数据持久化到本地硬盘。配置 EmbeddedRocksDBStateBackend 后，会将处理中的数据全部放入 RocksDB 数据库中，RocksDB 默认存储在 TaskManager 的本地数据目录里。

与 HashMapStateBackend 直接在堆内存中存储对象不同，这种方式下状态主要是放在 RocksDB 中。数据被存储为序列化的字节数组(Byte Arrays)，读写操作需要序列化/反序列化，因此状态的访问性能要差一些。另外，因为做了序列化，key 的比较也会按照字节进行，而不是直接调用 hashCode()和 equals() 方法。

EmbeddedRocksDBStateBackend 始终执行的是异步快照，也就是不会因为保存检查点而阻塞数据的处理；EmbeddedRocksDBStateBackend 适用于状态非常大、窗口非常长、 键/值状态很大的应用场景，同样对所有高可用性设置有效。

### 1.2 如何选择正确的 StateBackend

HashMap 和 RocksDB 两种状态后端最大的区别，就在于本地状态存放在哪里：前者是内存，后者是 RocksDB。在实际应用中，选择那种状态后端，主要是需要根据业务需求在处理性能和应用的扩展性上做一个选择。

HashMapStateBackend 是内存计算，读写速度非常快；但是，状态的大小会受到集群可用内存的限制，如果应用的状态随着时间不停地增长，就会耗尽内存资源。而 RocksDB 是硬盘存储，所以可以根据可用的磁盘空间进行扩展，而且是唯一支持增量检查点的状态后端，所以它非常适合于超级海量状态的存储。不过由于每个状态的读写都需要做序列化/反序列化，而且可能需要直接从磁盘读取数据，这就会导致性能的降低，平均读写性能要比 HashMapStateBackend 慢一个数量级。

### 1.3 StateBackend 的配置

在不做配置的时候，应用程序使用的默认状态后端是由集群配置文件 flink-conf.yaml 中指定的，配置的键名称为 state.backend。这个默认配置对集群上运行的所有作业都有效，我们可以通过更改配置值来改变默认的状态后端。另外，我们还可以在代码中为当前作业单独配置状态后端，这个配置会覆盖掉集群配置文件的默认值。

(1)配置默认的状态后端

在 flink-conf.yaml 中，可以使用 state.backend 来配置默认状态后端。配置项的可以是 hashmap，这样配置的就是 HashMapStateBackend；也可以是 rocksdb，这样配置的就是 EmbeddedRocksDBStateBackend。另外，也可以是一个实现了状态后端工厂 StateBackendFactory 的类的完全限定类名。
```
# 默认状态后端
state.backend: hashmap
# 存放检查点的文件路径
state.checkpoints.dir: hdfs://namenode:40010/flink/checkpoints
```
这里的 state.checkpoints.dir 配置项，定义了状态后端将检查点和元数据写入的目录。

(2) 为每个作业(Per-job)单独配置状态后端
每个作业独立的状态后端，可以在代码中，基于作业的执行环境直接设置。代码如下:
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new HashMapStateBackend());
```
上面代码设置的是 HashMapStateBackend，如果想要设置 EmbeddedRocksDBStateBackend，可以用下面的配置方式:
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new EmbeddedRocksDBStateBackend());
```
需要注意，如果想在 IDE 中使用 EmbeddedRocksDBStateBackend，需要为 Flink 项目添加 依赖:
```xml
<dependency>
   <groupId>org.apache.flink</groupId>
<artifactId>flink-statebackend-rocksdb_${scala.binary.version}</artifactId>
   <version>1.13.0</version>
</dependency>
```
而由于 Flink 发行版中默认就包含了 RocksDB，所以只要我们的代码中没有使用 RocksDB 的相关内容，就不需要引入这个依赖。即使我们在 flink-conf.yaml 配置文件中设定了 state.backend 为 rocksdb，也可以直接正常运行，并且使用 RocksDB 作为状态后端。


...
