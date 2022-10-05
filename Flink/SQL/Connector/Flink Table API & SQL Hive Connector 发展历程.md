
### 1.9

Apache Hive 是 Hadoop 生态圈中广泛用于存储和查询海量结构化数据的系统。Hive 除了是一个查询处理器外，还提供了一个叫做 Metastore 的 catalog 来管理和组织大数据集。查询处理器的一个常见集成点是与 Hive 的 Metastore 集成，以便能够利用 Hive 管理的数据。

最近，社区开始为 Flink Table API 和 SQL 实现一个连接到 Hive Metastore 的外部 catalog。在 Flink 1.9 中，用户能够查询和处理存储在 Hive 中多种格式的数据。Hive 集成还包括支持在 Flink Table API / SQL 中使用 Hive 的 UDF。有关详细信息，请参见 FLINK-10556。

在以前，Table API / SQL 中定义的表一直是临时的。新的 catalog 连接器允许在 Metastore 中持久化存储那些使用 SQL DDL 语句创建的表（参见上文）。这意味着可以直接连接到 Metastore 并注册一个表，例如，Kafka topic 的表。从现在开始，只要 catalog 连接到 Metastore，就可以查询该表。

请注意 Flink 1.9 中提供的 Hive 支持目前还是实验性的，下一个版本中将稳定这些功能，期待大家的反馈。


- FLINK-10556
