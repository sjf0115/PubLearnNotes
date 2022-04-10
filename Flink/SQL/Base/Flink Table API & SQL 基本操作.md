---
layout: post
author: sjf0115
title: Flink Table API & SQL 基本操作
date: 2022-04-10 22:34:01
tags:
  - Flink

categories: Flink
permalink: flink-table-api-sql-common-api
---

> Flink 版本：1.13.5

本文主要展示了 Table API 和 SQL 程序的常见结构，如何创建注册 Table，查询 Table，以及如何输出 Table。

## 1. Table API & SQL 程序结构

在 Flink 中，Table API 和 SQL 可以看作联结在一起的一套 API，这套 API 的核心概念是一个可以用作 Query 输入和输出的表 Table。在我们程序中，输入数据可以定义成一张表，然后对这张表进行查询得到一张新的表，最后还可以定义一张用于输出的表，负责将处理结果写入到外部系统。

我们可以看到，程序的整体处理流程与 DataStream API 非常相似，也可以分为读取数据源(Source)、转换(Transform)、输出数据(Sink)三部分。只不过这里的输入输出操作不需要额外定义，只需要将用于输入和输出的表 Table 定义出来，然后进行转换查询就可以了。

SQL 程序基本架构如下：
```java
// 创建执行环境 TableEnvironment
EnvironmentSettings settings = EnvironmentSettings
        .newInstance()
        .inStreamingMode()
        .useBlinkPlanner()
        .build();
TableEnvironment tableEnv = TableEnvironment.create(settings);

// 创建输入表
String sourceSql = "CREATE TABLE datagen_table (\n" +
        "    word STRING,\n" +
        "    frequency int\n" +
        ") WITH (\n" +
        "  'connector' = 'datagen',\n" +
        "  'rows-per-second' = '1',\n" +
        "  'fields.word.kind' = 'random',\n" +
        "  'fields.word.length' = '1',\n" +
        "  'fields.frequency.min' = '1',\n" +
        "  'fields.frequency.max' = '9'\n" +
        ")";
tableEnv.executeSql(sourceSql);

// 创建输出表
String sinkSql = "CREATE TABLE print_table (\n" +
        "  word STRING,\n" +
        "  frequency INT\n" +
        ") WITH (\n" +
        "  'connector' = 'print'\n" +
        ")";
tableEnv.executeSql(sinkSql);

// 执行计算并输出
String sql = "INSERT INTO print_table\n" +
        "SELECT word, SUM(frequency) AS frequency\n" +
        "FROM datagen_table\n" +
        "GROUP BY word";
tableEnv.executeSql(sql);
```
Table API 程序基本架构如下：
```java
// 执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);

// 读取数据创建 DataStream
DataStream<WordCount> inputStream = env.fromElements(
        new WordCount("Hello", 1L),
        new WordCount("Ciao", 1L),
        new WordCount("Hello", 1L));

// DataStream 转 Table
Table table = tEnv.fromDataStream(inputStream);

// 执行查询
Table resultTable = table
        .groupBy($("word"))
        .select($("word"), $("frequency").sum().as("frequency"))
        .as("word, frequency");

// Table 转 DataStream
DataStream<Tuple2<Boolean, WordCount>> result = tEnv.toRetractStream(resultTable, WordCount.class);
result.print();

// 执行
env.execute();
```

## 2. 创建 TableEnvironment

TableEnvironment 是用来创建 Table & SQL 程序的上下文执行环境，也是 Table & SQL 程序的入口，Table & SQL 程序的所有功能都是围绕 TableEnvironment 这个核心类展开的。TableEnvironment 的主要职能包括：
- 注册 Catlog
- 在内部 Catlog 中注册表
- 加载可插拔模块
- 执行 SQL 查询
- 注册用户自定义函数
- DataStream 和 Table 之间的转换（在 StreamTableEnvironment 的情况下）
- 提供更详细的配置选项

每个 Table 和 SQL 的执行，都必须绑定在一个表环境 TableEnvironment 中：
```java
EnvironmentSettings settings = EnvironmentSettings
        .newInstance()
        .useBlinkPlanner()
        .inStreamingMode()
        .build();
TableEnvironment tableEnv = TableEnvironment.create(settings);
```
或者，可以基于现有的 StreamExecutionEnvironment 创建 StreamTableEnvironment 来与 DataStream API 进行相互转换：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);
```

## 3. 创建 Table

表 Table 是在关系型数据库中非常熟悉的一个概念，是数据存储的基本形式，也是 SQL 执行的基本对象。Flink 中的表 Table 概念也并不特殊，是由多个行 Row 数据构成的，每行又可以定义好多的列 Column 字段。

为了方便查询表 Table，TableEnvironment 会维护一个目录 Catalog 和表 Table 的映射关系。所以表 Table 都是通过 Catalog 来进行注册创建的。每个表 Table 都有一个唯一的 ID，由三部分组成：目录(Catalog)名称，数据库(Database)名称 以及表(Table)名。在默认情况下，目录 Catalog 名称为 default_catalog，数据库 Database 名称为 default_database。如果我们有一个表 Table 叫作 MyTable，那么完整的 ID 就是 default_catalog.default_database.MyTable。

表 Table 有两种类型的表，一种是连接器表(Connector Tables) Table，一种是虚拟表(Virtual Tables) VIEW。连接器表一般用来描述外部数据，例如文件、数据库表或者消息队列。虚拟表通常是 Table API 或 SQL 查询的结果，可以基于现有的连接器表 Table 对象来创建。

### 3.1 连接器 Connector 表

创建 Table 最直观的方式，就是通过连接器(Connector)连接到一个外部系统，然后定义出对应的表结构。例如我们可以连接到 Kafka 或者文件系统，将存储在这些外部系统的数据以表 Table 的形式定义出来，这样对表 Table 的读写就可以通过连接器转换成对外部系统的读写。连接器表可以直接通过 SQL DDL 方式创建：
```java
EnvironmentSettings settings = EnvironmentSettings
        .newInstance()
        .inStreamingMode()
        .useBlinkPlanner()
        .build();
TableEnvironment tableEnv = TableEnvironment.create(settings);

// Using SQL DDL
String sql = "CREATE TABLE kafka_source_table (\n" +
        "  word STRING COMMENT '单词',\n" +
        "  frequency BIGINT COMMENT '次数'\n" +
        ") WITH (\n" +
        "  'connector' = 'kafka',\n" +
        "  'topic' = 'word',\n" +
        "  'properties.bootstrap.servers' = 'localhost:9092',\n" +
        "  'properties.group.id' = 'kafka-connector-word-sql',\n" +
        "  'scan.startup.mode' = 'earliest-offset',\n" +
        "  'format' = 'json',\n" +
        "  'json.ignore-parse-errors' = 'true',\n" +
        "  'json.fail-on-missing-field' = 'false'\n" +
        ")";
tableEnv.executeSql(sql);
```
> [完整代码Github](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/connectors/KafkaConnectorSQLExample.java)

在 Flink 1.14 版本中除了可以通过 SQL DDL 方式创建，还可以通过 Table API 方式创建：
```java
// Schema
Schema schema = Schema.newBuilder()
        .column("word", DataTypes.STRING())
        .column("frequency", DataTypes.BIGINT())
        .build();

// Kafka Source TableDescriptor
TableDescriptor kafkaDescriptor = TableDescriptor.forConnector("kafka")
        .comment("kafka source table")
        .schema(schema)
        .option(KafkaConnectorOptions.TOPIC, Lists.newArrayList("word"))
        .option(KafkaConnectorOptions.PROPS_BOOTSTRAP_SERVERS, "localhost:9092")
        .option(KafkaConnectorOptions.PROPS_GROUP_ID, "kafka-table-descriptor")
        .option("scan.startup.mode", "earliest-offset")
        .format("json")
        .build();

// 注册 Kafka Source 表
tEnv.createTemporaryTable("kafka_source_table", kafkaDescriptor);
```
> [完整代码Github](https://github.com/sjf0115/data-example/blob/master/flink-example-1.14/src/main/java/com/flink/example/table/connectors/KafkaConnectorTableExample.java)

### 3.2 虚拟表

假设我们现在有一个 Table 对象 inputTable，如果我们希望直接在 SQL 中查询这个 Table，我们该怎么做呢?由于 inputTable 是一个 Table 对象，并没有在 TableEnvironment 中注册，所以不能直接使用。如果要在 SQL 中直接使用，需要在 TableEnvironment 中注册，如下所示：
```java
// 创建流和表执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);
// 创建 DataStream
DataStream<String> dataStream = env.fromElements("Alice", "Bob", "John");
// DataStream 转换为 Table
Table inputTable = tableEnv.fromDataStream(dataStream, $("f0"));

// 将 Table 注册为虚拟表
tableEnv.createTemporaryView("input_table_view", inputTable);

// 执行查询并输出
Table upperTable = tableEnv.sqlQuery("SELECT UPPER(f0) FROM input_table_view");
DataStream<Row> upperStream = tableEnv.toDataStream(upperTable);
upperStream.print("U");
```
> [完整代码 Github](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/table/VirtualTableCreateExample.java)

这里的注册其实是创建了一个虚拟表(Virtual Table)，这与 SQL 语 法中的视图(View)非常类似，所以调用的方法也叫作创建虚拟视图(createTemporaryView)。视图之所以是虚拟的，是因为我们并不会直接保存这个表的内容。注册为虚拟表之后，我们就可以在 SQL 中直接使用 input_table_view 进行查询了。

除了可以将 Table 对象注册为虚拟表之外，我们也可以将 DataStream 直接注册为一个虚拟表：
```java
// 创建流和表执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);
// 创建 DataStream
DataStream<String> dataStream = env.fromElements("Alice", "Bob", "John");

// 2. 将 DataStream 注册为虚拟表
// 2.1 自动派生所有列
tableEnv.createTemporaryView("input_stream_view", dataStream);
// 2.2 自动派生所有列 但使用表达式方式指定提取的字段以及位置
//tableEnv.createTemporaryView("input_stream_view2", dataStream, $("f0"));
// 2.3 手动定义列
/*Schema schema = Schema.newBuilder()
        .column("f0", DataTypes.STRING())
        .build();
tableEnv.createTemporaryView("input_stream_view3", dataStream, schema);*/
Table lowerTable = tableEnv.sqlQuery("SELECT LOWER(f0) FROM input_stream_view");
DataStream<Row> lowerStream = tableEnv.toDataStream(lowerTable);
lowerStream.print("L");
```
> [完整代码 Github](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/table/VirtualTableCreateExample.java)

## 4. 查询 Table

创建好了表，接下来自然就是对表进行查询转换了。

### 4.1 通过 SQL 查询

查询 Table 最简单的方式就是通过 SQL 语句来查询了。Flink 基于 Apache Calcite 来提供对 SQL 的支持。在代码中，我们只需要调用 TableEnvironment 的 sqlQuery() 方法，并传入一个字符串的 SQL 查询语句就可以了，返回值是一个 Table 对象：
```java
// 创建流和表执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);
// 创建 DataStream
DataStream<Row> dataStream = env.fromElements(
        Row.of("Alice", 12),
        Row.of("Bob", 10),
        Row.of("Alice", 100),
        Row.of("Lucy", 50)
);
// 将 DataStream 转换为 Table
Table inputTable = tableEnv.fromDataStream(dataStream).as("name", "score");

// 注册虚拟表 通过SQL查询
tableEnv.createTemporaryView("input_table", inputTable);
Table resultTable1 = tableEnv.sqlQuery("SELECT name, SUM(score) AS score_sum\n" +
    "FROM input_table\n" +
    "WHERE name <> 'Lucy'\n" +
    "GROUP BY name");

// Table 转 Changelog DataStream
DataStream<Row> resultStream1 = tableEnv.toChangelogStream(resultTable1);
// 输出
resultStream1.print("R1");
```
> [完整代码 Github](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/table/TableQueryExample.java)

Table 对象不注册为虚拟表，也可以直接在 SQL 中使用，即使用字符串拼接的方式：
```java
Table resultTable2 = tableEnv.sqlQuery("SELECT name, SUM(score) AS score_sum\n" +
    "FROM " + inputTable +
    " WHERE name <> 'Lucy'\n" +
    "GROUP BY name");
```
> [完整代码 Github](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/table/TableQueryExample.java)

这其实是一种简略的写法，我们将 Table 对象名 inputTable 直接以字符串拼接的形式添加到 SQL 语句中，在解析时会自动注册一个同名的虚拟表到环境中，这样就省略了创建虚拟表的过程。

目前 Flink 支持标准 SQL 中的绝大部分用法，并提供了丰富的计算函数。这样我们可以像在 MySQL、Hive 中那样直接通过编写 SQL 实现自己的需求，从而大大降低了 Flink 上手的难度。

### 4.2 通过 Table API 查询

另外一种查询方式是通过调用 Table API 实现。Table API 是嵌入在 Java 和 Scala 语言内的查询 API。相比 SQL，查询不需要指定查询 SQL 字符串，而是使用宿主语言一步步链式调用。可以通过 fromDataStream 得到表的 Table 对象。得到 Table 对象之后，就可以调用 API 进行各种转换操作了。每个方法的返回都是一个新的 Table 对象，表示对输入 Table 应用关系操作的结果。一些关系操作是由多个方法调用组成的，例如 table.groupBy(...).select(...)，其中 groupBy(...) 指定了 table 的分组，select(...) 指定了在分组表上的投影。如下示例展示了一个简单的 Table API 聚合查询：
```java
// 创建流和表执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);
// 创建 DataStream
DataStream<Row> dataStream = env.fromElements(
        Row.of("Alice", 12),
        Row.of("Bob", 10),
        Row.of("Alice", 100),
        Row.of("Lucy", 50)
);
// 将 DataStream 转换为 Table
Table inputTable = tableEnv.fromDataStream(dataStream).as("name", "score");

// 执行聚合计算
Table resultTable3 = inputTable
    .filter($("name").isNotEqual("Lucy"))
    .groupBy($("name"))
    .select($("name"), $("score").sum().as("score_sum"));

// Table 转 Changelog DataStream
DataStream<Row> resultStream3 = tableEnv.toChangelogStream(resultTable3);
// 输出
resultStream3.print("R3");
```
> [完整代码 Github](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/table/TableQueryExample.java)

### 4.3 Table API 和 SQL 混合使用

可以发现，无论是调用 Table API 还是执行 SQL，得到的结果都是一个 Table 对象，所以这两种 API 的查询可以很方便地结合在一起：
- 可以在 SQL 查询返回的 Table 对象上定义 Table API 查询：通过 Table 对象链式调用 Table API 方法。
- 可以在 Table API 查询返回的 Table 对象上定义 SQL 查询：通过在 TableEnvironment 中注册表并在 SQL 查询的 FROM 子句中引用。

两种 API 殊途同归，实际应用中可以按照自己的习惯任意选择。不过由于结合使用容易引起混淆，而 Table API 功能相对较少、通用性较差，所以企业项目中往往会直接选择 SQL 的方式来实现需求。

## 5. 输出 Table

表的创建和查询分别对应流处理中的读取数据源(Source)和转换(Transform)，而表的输出则写入数据源(Sink)，也就是将结果数据输出到外部系统。

### 5.1 通过 SQL 输出

输出一张表 Table 最直接的方法，就是通过 SQL 的 INSERT INTO SELECT 语句来完成：
```java
// 创建流和表执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);
// 创建 DataStream
DataStream<Row> dataStream = env.fromElements(
        Row.of("Alice", 12),
        Row.of("Bob", 10),
        Row.of("Alice", 100),
        Row.of("Lucy", 50)
);
// 将 DataStream 转换为 Table
Table inputTable = tableEnv.fromDataStream(dataStream).as("name", "score");
// 输入表: 注册虚拟表
tableEnv.createTemporaryView("input_table", inputTable);

// 1. 通过 SQL 方式实现
// 输出表: 创建 Print Connector 表
tableEnv.executeSql("CREATE TEMPORARY TABLE print_sql_sink (\n" +
        "  name STRING,\n" +
        "  score BIGINT\n" +
        ") WITH (\n" +
        "  'connector' = 'print',\n" +
        "  'print-identifier' = 'SQL'\n" +
        ")");
// 聚合计算并输出
tableEnv.executeSql("INSERT INTO print_sql_sink\n" +
        "SELECT name, SUM(score) AS score_sum\n" +
        "FROM input_table\n" +
        "GROUP BY name");
```
> [完整代码 Github](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/table/TableOutputExample.java)

### 5.2 通过 Table API 方式输出

此外，还可以调用 Table 的方法 executeInsert() 方法将一个 Table 写入到注册过的表中(print_sink_table)，方法传入的参数就是注册的表名：
```java
Table outputTable = inputTable
        .filter($("name").isNotEqual("Lucy"))
        .groupBy($("name"))
        .select($("name"), $("score").sum().as("score_sum"));
// Flink 1.13 版本推荐使用 DDL 方式创建输出表 1.14 版本可以用 Table API 创建
tableEnv.executeSql("CREATE TEMPORARY TABLE print_table_sink (\n" +
        "  name STRING,\n" +
        "  score BIGINT\n" +
        ") WITH (\n" +
        "  'connector' = 'print',\n" +
        "  'print-identifier' = 'Table'\n" +
        ")");
outputTable.executeInsert("print_table_sink");
```
> [完整代码 Github](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/table/TableOutputExample.java)

Flink 1.14 版本开始，可以通过 Table API 来创建 Connector 表
```java
// 创建流和表执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);

// 创建 DataStream
DataStream<Row> dataStream = env.fromElements(
        Row.of("Alice", 12),
        Row.of("Bob", 10),
        Row.of("Alice", 100),
        Row.of("Lucy", 50)
);
// 将 DataStream 转换为 Table
Table inputTable = tableEnv.fromDataStream(dataStream).as("name", "score");

// 聚合计算
Table outputTable = inputTable
        .filter($("name").isNotEqual("Lucy"))
        .groupBy($("name"))
        .select($("name"), $("score").sum().as("score_sum"));

// 创建 Print Connector 表
tableEnv.createTemporaryTable(
        "print_sink_table",
        TableDescriptor.forConnector("print")
        .schema(Schema.newBuilder()
                .column("name", DataTypes.STRING())
                .column("score_sum", DataTypes.BIGINT())
                .build()
        )
        .build()
);
// 输出
outputTable.executeInsert("print_sink_table");
```
> [完整代码 Github](https://github.com/sjf0115/data-example/blob/master/flink-example-1.14/src/main/java/com/flink/example/table/table/TableOutputExample.java)

[Concepts & Common API](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/table/common/)
