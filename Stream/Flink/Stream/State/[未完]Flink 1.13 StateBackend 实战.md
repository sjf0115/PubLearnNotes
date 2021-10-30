

为了从概念上更好的理解，我们将弃用类 MemoryStateBackend、FsStateBackend 和 RocksDBStateBackend，改为 HashMapStateBackend 和 EmbeddedRocksDBStateBackend。需要明确的是，我们不会更改任何运行时数据结构以及特性，这些只是面向用户的新 API。

## 2. 新版 StateBackend

Flink 提供的开箱即用的 State Backends：
- HashMapStateBackend
- EmbeddedRocksDBStateBackend

在没有配置的情况下，系统默认使用 HashMapStateBackend。

### 2.1 HashMapStateBackend

```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 设置状态后端
env.setStateBackend(new HashMapStateBackend());
// 设置 Checkpoint
env.enableCheckpointing(1000L);
FileSystemCheckpointStorage checkpointStorage = new FileSystemCheckpointStorage("hdfs://localhost:9000/flink/checkpoint");
env.getCheckpointConfig().setCheckpointStorage(checkpointStorage);
```

### 2.2 EmbeddedRocksDBStateBackend

EmbeddedRocksDBStateBackend 将正在运行中的状态数据保存在 RocksDB 数据库中，默认将数据存储在 TaskManager 的数据目录下。

```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-statebackend-rocksdb_2.11</artifactId>
    <version>1.13.0</version>
    <scope>provided</scope>
</dependency>
```



https://ci.apache.org/projects/flink/flink-docs-master/docs/ops/state/state_backends/
https://xie.infoq.cn/article/0f95865c6e9a0ba5a5da3e18b
https://cwiki.apache.org/confluence/display/FLINK/FLIP-142%3A+Disentangle+StateBackends+from+Checkpointing
