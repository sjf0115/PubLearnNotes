

如果要在 IDE 中使用 EmbeddedRocksDBStateBackend 或在 Flink 作业中以编程方式配置它，则必须将以下依赖项添加到 Flink 项目中：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-statebackend-rocksdb_2.11</artifactId>
    <version>1.13.0</version>
    <scope>provided</scope>
</dependency>
```
由于 RocksDB 是默认 Flink 发行版的一部分，如果您没有在作业中使用任何 RocksDB 代码并通过 state.backend 配置状态后端，并在 flink-conf 中进一步检查点和 RocksDB 特定参数，则不需要 flink-conf.yaml。
