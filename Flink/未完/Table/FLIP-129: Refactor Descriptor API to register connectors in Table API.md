
## 1. 目标

在 Flink 1.5.0 中引入了 TableEnvironment#connect API，用于实例化以及配置 Table Source 和 Sink。在这个时候，SQL DDL 还一直处于开发和优化中。随着 SQL DDL 功能变得越来越强大，其中许多功能无法在 connect API 实现。此外，该 API 也显现出如下几个缺点：
- Connector 必须实现对应的描述符，例如 `new Kafka()`，这会增加维护的工作量以及重复信息。
- SQL DDL 和 Connector 的底层实现不同，需要维护不同的代码路径。
- Descriptor API 有很多已知问题：[FLINK-17548](https://issues.apache.org/jira/browse/FLINK-17548)、[FLINK-17186](https://issues.apache.org/jira/browse/FLINK-17186)、[FLINK-15801](https://issues.apache.org/jira/browse/FLINK-15801)、[FLINK-15943](https://issues.apache.org/jira/browse/FLINK-15943)。

因此，connect 在 Flink 1.11 版本中被废弃。在这个 FLIP 中，我们提出一个新的 API 以编程的方式在 Table API 上的定 Source 和 Sink，无需切换到 SQL DDL。

## 2. Connect API

```
tableEnv.connect(
        new Kafka() // can be replaced by new Connector("kafka-0.11")
            .version("0.11")
            .topic("myTopic")
            .property("bootstrap.servers", "localhost:9092")
            .property("group.id", "test-group")
            .scanStartupModeEarliest()
            .sinkPartitionerRoundRobin()
            .format(new Json().ignoreParseErrors(false))
    .schema(
        new Schema()
            .column("user_id", DataTypes.BIGINT())
            .column("user_name", DataTypes.STRING())
            .column("score", DataTypes.DECIMAL(10, 2))
            .column("log_ts", DataTypes.TIMESTAMP(3))
            .column("part_field_0", DataTypes.STRING())
            .column("part_field_1", DataTypes.INT())
            .column("proc", proctime())
            .column("my_ts", toTimestamp($("log_ts"))
            .watermarkFor("my_ts", $("my_ts").minus(lit(3).seconds())))
            .primaryKey("user_id")
    .partitionedBy("part_field_0", "part_field_1")
    .createTemporaryTable("MyTable");
```

使用 connect() 方法可能会让用户感到困惑，调用 connect() 并不会连接到外部系统，它只是连接到外部系统的一个入口。在调用 `createTemporaryTable` 方法后才会连接到外部系统。

connect() 方法在 TableEnvironment 的方法中看起来很奇怪，因为所有其他方法都是跟 SQL 兼容的。因此，我们认为 `tEnv#createTemporaryTable(path, descriptor)` 是比 `connect()` 更好的入口。

`TableEnvironment#createTemporaryTable(path, descriptor)` 将描述符和表的注册实现了解耦。我们可以轻松地支持更多功能，例如 `TableEnvironment#from(descriptor)` 和 `Table#executeInsert(descriptor)` 具有相同描述符接口/类。



## 2. Public Interfaces

| Interface     | 变更  |
| :------------- | :------------- |
| TableEnvironment.connect                                      | 在 Flink 1.11 中废弃 |
| TableEnvironment.createTable(path, TableDescriptor)	          | 在 Flink 1.14 中引入 |
| TableEnvironment.createTemporaryTable(path, TableDescriptor)	| 在 Flink 1.14 中引入 |
| TableEnvironment.from(TableDescriptor)	                      | 在 Flink 1.14 中引入 |
| Table.executeInsert(TableDescriptor)	                        | 在 Flink 1.14 中引入 |
| StatementSet.addInsert(TableDescriptor, Table)	              | 在 Flink 1.14 中引入 |
| ConnectTableDescriptor	                                      | 在 Flink 1.11 中废弃 |
| BatchTableDescriptor	                                        | 在 Flink 1.11 中废弃 |
| StreamTableDescriptor	                                        | 在 Flink 1.11 中废弃 |
| ConnectorDescriptor	                                          | 在 Flink 1.11 中废弃 |
| TableDescriptor	                                              | 在 Flink 1.14 中重构 |
| Rowtime	                                                      | 在 Flink 1.11 中废弃 |

### 2.1 TableEnvironment#createTable & TableEnvironment#createTemporaryTable

为了让用户可以通过 Table API 注册 Source 和 Sink，在 TableEnvironment 中引入了如下两个新方法：
```java
// 根据指定的表描述符创建一个表
void createTable(String path, TableDescriptor descriptor);
// 根据指定的表描述符创建一个临时表
void createTemporaryTable(String path, TableDescriptor descriptor);
```
TableDescriptor 接口是在 SQL DDL 和 CatalogTable 中使用通用结构。通过引用 ConfigOption 实例（首选）或字符串来指定属性选项。对于不通过 ConfigOption 实例表示的选项，例如包含 `field.#.min` 之类的占位符，可以使用字符串模式。该接口还提供了用于指定格式的生命质量方法，例如前缀格式选项由描述符本身处理，这允许将 ConfigOption 实例用于格式选项。
```java
TableDescriptor {
  static TableDescriptorBuilder forConnector(String connector);
  Optional<Schema> getSchema();
  Map<String, String> getOptions();
  Optional<String> getComment();
  List<String> getPartitionKeys();
  Optional<TableLikeDescriptor> getLikeDescriptor();
}

TableDescriptorBuilder<SELF> {
  SELF schema(Schema schema);
  SELF comment(String comment);
  SELF option<T>(ConfigOption<T> configOption, T value);
  SELF option(String key, String value);
  SELF format(String format);
  SELF format(ConfigOption<?> formatOption, String format);
  SELF format(FormatDescriptor formatDescriptor);
  SELF format(ConfigOption<?> formatOption, FormatDescriptor formatDescriptor);
  SELF partitionedBy(String... partitionKeys);
  SELF like(String tableName, LikeOption... likeOptions);
  TableDescriptor build();
}

TableLikeDescriptor {
  String getTableName();
  List<TableLikeOption> getLikeOptions();
}

FormatDescriptor {
  static FormatDescriptorBuilder forFormat(String format);
  String getFormat();
  Map<String, String> getOptions();
}

FormatDescriptorBuilder<SELF> {
  SELF option<T>(ConfigOption<T> configOption, T value);
  SELF option(String key, String value);
  FormatDescriptor build();
}

interface LikeOption {
    enum INCLUDING implements LikeOption {
        ALL,
        CONSTRAINTS,
        GENERATED,
        OPTIONS,
        PARTITIONS,
        WATERMARKS
    }

    enum EXCLUDING implements LikeOption {
        ALL,
        CONSTRAINTS,
        GENERATED,
        OPTIONS,
        PARTITIONS,
        WATERMARKS
    }

    enum OVERWRITING implements LikeOption {
        GENERATED,
        OPTIONS,
        WATERMARKS
    }
}
```
如下示例演示了如何使用这些 API：
```java
tEnv.createTable(
  "cat.db.MyTable",

  TableDescriptor.forConnector("kafka")
    .comment("This is a comment")
    .schema(Schema.newBuilder()
      .column("f0", DataTypes.BIGINT())
      .columnByExpression("f1", "2 * f0")
      .columnByMetadata("f3", DataTypes.STRING())
      .column("t", DataTypes.TIMESTAMP(3))
      .watermark("t", "t - INTERVAL '1' MINUTE")
      .primaryKey("f0")
      .build())
    .partitionedBy("f0")
    .option(KafkaOptions.TOPIC, topic)
    .option("properties.bootstrap.servers", "…")
    .format("json")
    .build()
);

tEnv.createTemporaryTable(
  "MyTemporaryTable",

  TableDescriptor.forConnector("kafka")
    // …
    .like("cat.db.MyTable")
);
```
### 2.2 TableEnvironment#from

在 TableEnvironment 中引入 from 方法以便根据指定的描述符创建表：
```java
Table from(TableDescriptor descriptor);
```

### 2.3 Table#executeInsert

在 Table 中引入 executeInsert 方法以便直接写入由描述符定义的 Sink 中：
```java
TableResult executeInsert(TableDescriptor descriptor);
```

### 2.4 StatementSet#addInsert

与 Table#executeInsert 类似，扩展 StatementSet#addInsert 方法获取返回的描述符：
```java
StatementSet addInsert(TableDescriptor descriptor, Table table);
```
## 3. Package 结构

新的描述符 API 放在 flink-table-api-java 模块下的 org.apache.flink.table.descriptors 包中。

为了更容易发现 ConfigOption 实例，将 `*Options` 类从所有内置 Connector（例如 KafkaOptions，...）移动到一个公共包中。对于任何 Connector 都可以轻松地在当前类路径上发现这些类。由于这涉及将这些类声明为公共（不断发展的）API，因此需要进行少量重构以确保它们不包含任何内部结构。

## 4. 兼容性、弃用和迁移计划

删除现有的 API，并将其替换为新的、不兼容的 API。 然而，旧的 API 自 Flink 1.11 起已被弃用，并且缺乏对许多功能的支持，因此我们预计这不会影响到许多用户，因为目前的建议是切换到 SQL DDL。 对于受影响的用户，迁移需要相对较小的更改，并且可以涵盖所有现有功能。





原文:[FLIP-129: Refactor Descriptor API to register connectors in Table API](https://cwiki.apache.org/confluence/display/FLINK/FLIP-129%3A+Refactor+Descriptor+API+to+register+connectors+in+Table+API)
