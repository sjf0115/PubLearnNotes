
> Flink 版本：1.13.6

Apache Flink 提供了两个关系型 API：Table API 和 SQL，用于统一的流和批处理。Table API 是用于 Java、Scala 和 Python 的集成语言查询 API，可以以非常直观的方式组合不同关系运算符（例如 SELECT、FILTER 以及 JOIN）构建复杂查询。Flink SQL 基于 Apache Calcite 实现。无论输入是无界的（流式）还是有界的（批处理），任意查询都具有相同的语义并输出相同的结果。Table API 和 SQL 可以与 Flink 的 DataStream API 无缝集成。

## 1. 依赖

### 1.1 Planner

从 Flink 1.9 开始，Flink 提供了两种不同的 Planner 实现来执行 Table & SQL API 程序：
- Blink Planner：Flink 1.9+
- Old Planner：Flink 1.9 之前

从 Flink 1.13.0 版本开始，Old Planner 标记为 Deprecated。Blink Planner 已成为一些版本的默认 Planner，以后也将是唯一的一个 Planner。在 1.14 版本中，Old Planner 被移除，Blink Planner 将成为 Planner 的唯一实现。

### 1.2 依赖项

根据你使用的编程语言，需要将 Java 或者 Scala API 添加到项目中，以便能使用 Table API 和 SQL 来定义作业流：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-api-java-bridge_2.11</artifactId>
  <version>1.13.6</version>
  <scope>provided</scope>
</dependency>
```
> 在这我们使用 Java 语言。

此外，如果你想在 IDE 中本地运行 Table API 或者 SQL 程序，那么必须添加如下依赖：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner-blink_2.11</artifactId>
  <version>1.13.6</version>
  <scope>provided</scope>
</dependency>
```
在内部实现上，Table 生态系统的一部分是基于 Scala 实现的。因此，需要确保为批处理和流式应用程序添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-streaming-scala_2.11</artifactId>
  <version>1.13.6</version>
  <scope>provided</scope>
</dependency>
```
如果要实现自定义格式(Format)或连接器(Connector)序列化或者反序列化行或一组用户定义函数，则需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-common</artifactId>
  <version>1.13.6</version>
  <scope>provided</scope>
</dependency>
```

## 2. WordCount 示例

下面通过两个简单的 WordCount 的例子来体验一下 Flink Table & SQL 的代码是如何编写的。我们分别从 Table API 和 SQL 实现方式介绍如何开发一个简单的 WordCount 例子。

### 2.1 Table API 版 WordCount

第一步创建流处理的执行环境，Flink 1.13 版本 Old Planner 标记为 Deprecated。Blink Planner 已成为的默认 Planner：
```java
EnvironmentSettings settings = EnvironmentSettings
        .newInstance()
        .inStreamingMode()
        .build();
TableEnvironment tEnv = TableEnvironment.create(settings);
```
由于我们不需要 Table 和 DataStream 转换，所以不需要使用 StreamTableEnvironment，使用 TableEnvironment 即可。

第二步创建 datagen Connector 输入表 `source_table`，并指定两个字段 word 和 frequency：
```java
tEnv.createTemporaryTable("source_table",
        TableDescriptor.forConnector("datagen")
                .schema(Schema.newBuilder()
                        .column("word", DataTypes.STRING())
                        .column("frequency", DataTypes.BIGINT())
                        .build()
                )
                .option(DataGenConnectorOptions.ROWS_PER_SECOND, 1L)
                .option("fields.word.kind", "random")
                .option("fields.word.length", "1")
                .option("fields.frequency.min", "1")
                .option("fields.frequency.max", "9")
                .build()
);
```
通过 option 设置 Connector 的一些行为：
- fields.word.kind：指定 word 字段 kind 为 random，表示随机生成
- fields.word.length：指定 word 字段为一个字符长度
- fields.frequency.min：指定 frequency 字段最小值为 1
- fields.frequency.max：指定 frequency 字段最大值为 9

第三步执行聚合查询计算每个 word 的出现次数 frequency：
```java
Table resultTable = tEnv.from("source_table")
    .groupBy($("word"))
    .select($("word"), $("frequency").sum().as("frequency"));
```
第四步创建 Print Connector 输出表 `sink_table`，并指定两个字段 word 和 frequency：
```java
tEnv.createTemporaryTable(
        "sink_table",
        TableDescriptor.forConnector("print")
                .schema(Schema.newBuilder()
                        .column("word", DataTypes.STRING())
                        .column("frequency", DataTypes.BIGINT())
                        .build()
                )
                .build()
);
```
第五步查询结果 resultTable 输出到 Print 表 `sink_table` 中：
```java
resultTable.executeInsert("sink_table");
```

完整代码如下：
```java
// 执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setParallelism(1);
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);
// 创建输入表
tEnv.createTemporaryTable("source_table",
        TableDescriptor.forConnector("datagen")
                .schema(Schema.newBuilder()
                        .column("word", DataTypes.STRING())
                        .column("frequency", DataTypes.BIGINT())
                        .build()
                )
                .option(DataGenConnectorOptions.ROWS_PER_SECOND, 1L)
                .option("fields.word.kind", "random")
                .option("fields.word.length", "1")
                .option("fields.frequency.min", "1")
                .option("fields.frequency.max", "9")
                .build()
);
// 聚合查询
Table resultTable = tEnv.from("source_table")
        .groupBy($("word"))
        .select($("word"), $("frequency").sum().as("frequency"));
// 创建输出表
tEnv.createTemporaryTable(
        "sink_table",
        TableDescriptor.forConnector("print")
                .schema(Schema.newBuilder()
                        .column("word", DataTypes.STRING())
                        .column("frequency", DataTypes.BIGINT())
                        .build()
                )
                .build()
);
// 输出
resultTable.executeInsert("sink_table");
```

> [github](https://github.com/sjf0115/data-example/blob/master/flink-example-1.14/src/main/java/com/flink/example/table/base/StreamTableWordCount.java)

### 2.2 SQL 版 WordCount

第一步跟 Table API 版一样，第二步通过 SQL 的方式创建 datagen Connector 输入表 `source_table`，并指定两个字段 word 和 frequency：：
```java
String sourceSql = "CREATE TABLE source_table (\n" +
        "    word STRING,\n" +
        "    frequency BIGINT\n" +
        ") WITH (\n" +
        "  'connector' = 'datagen',\n" +
        "  'rows-per-second' = '1',\n" +
        "  'fields.word.kind' = 'random',\n" +
        "  'fields.word.length' = '1',\n" +
        "  'fields.frequency.min' = '1',\n" +
        "  'fields.frequency.max' = '9'\n" +
        ")";
tEnv.executeSql(sourceSql);
```
第三步通过 SQL 创建 Print Connector 输出表 `sink_table`，并指定两个字段 word 和 frequency：
```java
String sinkSql = "CREATE TABLE sink_table (\n" +
        "  word STRING,\n" +
        "  frequency BIGINT\n" +
        ") WITH (\n" +
        "  'connector' = 'print'\n" +
        ")";
tEnv.executeSql(sinkSql);
```
第四步执行聚合查询计算每个 word 的出现次数 frequency，并输出到 Print 表 `sink_table` 中：
```java
String querySql = "INSERT INTO sink_table\n" +
        "SELECT word, SUM(frequency) AS frequency\n" +
        "FROM source_table\n" +
        "GROUP BY word";
tEnv.executeSql(querySql);
```

完整代码如下：
```java
// TableEnvironment
EnvironmentSettings settings = EnvironmentSettings
        .newInstance()
        .inStreamingMode()
        .build();
TableEnvironment tEnv = TableEnvironment.create(settings);

// 创建输入表
String sourceSql = "CREATE TABLE source_table (\n" +
        "    word STRING,\n" +
        "    frequency BIGINT\n" +
        ") WITH (\n" +
        "  'connector' = 'datagen',\n" +
        "  'rows-per-second' = '1',\n" +
        "  'fields.word.kind' = 'random',\n" +
        "  'fields.word.length' = '1',\n" +
        "  'fields.frequency.min' = '1',\n" +
        "  'fields.frequency.max' = '9'\n" +
        ")";
tEnv.executeSql(sourceSql);

// 创建输出表
String sinkSql = "CREATE TABLE sink_table (\n" +
        "  word STRING,\n" +
        "  frequency BIGINT\n" +
        ") WITH (\n" +
        "  'connector' = 'print'\n" +
        ")";
tEnv.executeSql(sinkSql);

// 聚合查询并输出
String querySql = "INSERT INTO sink_table\n" +
        "SELECT word, SUM(frequency) AS frequency\n" +
        "FROM source_table\n" +
        "GROUP BY word";
tEnv.executeSql(querySql);
```

> 源码：[PureSQLWordCount](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/sql/base/PureSQLWordCount.java)
