---
layout: post
author: sjf0115
title: Flink1.4 Table与SQL的概念以及常见API
date: 2018-03-12 11:29:01
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-table-and-sql-concepts-common-api
---

Table API 和 SQL 集成在一个联合API中。这个API的核心概念是一个用作输入和输出查询的表。这篇文章展示了使用 Table API 和 SQL 查询程序的常见结构，如何注册表，如何查询表以及如何发出表。


### 1. Table API 和 SQL 查询程序的常见结构

批处理和流式处理的所有 Table API 和 SQL 程序遵循相同的模式。以下代码示例显示了 Table API 和 SQL 程序的常见结构。

Java版本:
```java
// for batch programs use ExecutionEnvironment instead of StreamExecutionEnvironment
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

// create a TableEnvironment
// for batch programs use BatchTableEnvironment instead of StreamTableEnvironment
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// register a Table
tableEnv.registerTable("table1", ...)            // or
tableEnv.registerTableSource("table2", ...);     // or
tableEnv.registerExternalCatalog("extCat", ...);

// create a Table from a Table API query
Table tapiResult = tableEnv.scan("table1").select(...);
// create a Table from a SQL query
Table sqlResult  = tableEnv.sqlQuery("SELECT ... FROM table2 ... ");

// emit a Table API result Table to a TableSink, same for SQL result
tapiResult.writeToSink(...);

// execute
env.execute();
```
Scala版本:
```scala
// for batch programs use ExecutionEnvironment instead of StreamExecutionEnvironment
val env = StreamExecutionEnvironment.getExecutionEnvironment

// create a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// register a Table
tableEnv.registerTable("table1", ...)           // or
tableEnv.registerTableSource("table2", ...)     // or
tableEnv.registerExternalCatalog("extCat", ...)

// create a Table from a Table API query
val tapiResult = tableEnv.scan("table1").select(...)
// Create a Table from a SQL query
val sqlResult  = tableEnv.sqlQuery("SELECT ... FROM table2 ...")

// emit a Table API result Table to a TableSink, same for SQL result
tapiResult.writeToSink(...)

// execute
env.execute()
```
> 备注

> Table API 和 SQL 查询可以轻松集成并嵌入到DataStream或DataSet程序中。查看[与DataStream和DataSet API的集成](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/table/common.html#integration-with-datastream-and-dataset-api)部分，了解如何将DataStream和DataSet转换为表格，反之亦然。

### 2. 创建 TableEnvironment

`TableEnvironment` 是 Table API 和 SQL 集成的核心概念。它负责：
- 在内部目录中注册一个 Table
- 注册外部目录
- 执行SQL查询
- 注册一个用户自定义（`scalar`, `table`, 或者 `aggregation`）函数
- 将 `DataStream` 或 `DataSet` 转换为 Table
- 保存对 `ExecutionEnvironment` 或 `StreamExecutionEnvironment` 的引用

Table 总是与特定的 `TableEnvironment` 绑定。无法在同一个查询中组合来自不同 `TableEnvironments` 的表，例如，`join` 或者 `union`。

`TableEnvironment` 通过调用静态方法 `TableEnvironment.getTableEnvironment()` 来创建，参数为 `StreamExecutionEnvironment` 或 `ExecutionEnvironment` 以及可选的 `TableConfig`。 `TableConfig` 可用于配置 `TableEnvironment` 或自定义查询优化和转换过程（请参阅查询优化部分）。

Java版本:
```java
// STREAMING QUERY
StreamExecutionEnvironment sEnv = StreamExecutionEnvironment.getExecutionEnvironment();
// create a TableEnvironment for streaming queries
StreamTableEnvironment sTableEnv = TableEnvironment.getTableEnvironment(sEnv);

// BATCH QUERY
ExecutionEnvironment bEnv = ExecutionEnvironment.getExecutionEnvironment();
// create a TableEnvironment for batch queries
BatchTableEnvironment bTableEnv = TableEnvironment.getTableEnvironment(bEnv);
```
Scala版本:
```scala
// STREAMING QUERY
val sEnv = StreamExecutionEnvironment.getExecutionEnvironment
// create a TableEnvironment for streaming queries
val sTableEnv = TableEnvironment.getTableEnvironment(sEnv)

// BATCH QUERY
val bEnv = ExecutionEnvironment.getExecutionEnvironment
// create a TableEnvironment for batch queries
val bTableEnv = TableEnvironment.getTableEnvironment(bEnv)
```

### 3. 在目录中注册 Table

`TableEnvironment` 维护一个按名称注册的表的目录。有两种类型的表，输入表和输出表。输入表可以在 Table API 和 SQL 查询中引用并提供输入数据。输出表可用于将 Table API 或 SQL 查询的结果发送到外部系统中。

输入表可以从各种数据源注册：
- 一个存在的 Table 对象，通常是 Table API 或 SQL 查询的结果。
- 一个 TableSource，用于访问外部数据，如文件，数据库或消息系统。
- 来自 DataStream 或 DataSet 程序的 DataStream 或 DataSet。

输出表可以使用 TableSink 注册。

#### 3.1 注册 Table

在 TableEnvironment 中注册 Table 如下所示:

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// Table is the result of a simple projection query
Table projTable = tableEnv.scan("X").project(...);

// register the Table projTable as table "projectedX"
tableEnv.registerTable("projectedTable", projTable);
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// Table is the result of a simple projection query
val projTable: Table = tableEnv.scan("X").project(...)

// register the Table projTable as table "projectedX"
tableEnv.registerTable("projectedTable", projTable)
```

> 备注

> 注册表的处理方式与关系数据库系统中我们熟知的 VIEW 类似，即，定义 Table 的查询没有经过优化，但是当另一个查询引用已注册的表时，将会进行内联。如果多个查询引用相同的注册表，那么它将针对每个引用查询进行内联，并执行多次，即不会共享注册表的结果。

#### 3.2 注册 TableSource

TableSource 提供访问存储在存储系统（例如数据库（MySQL，HBase，...）），具有特定编码的文件（CSV，Apache [Parquet，Avro，ORC]，...）或消息系统（Apache Kafka，RabbitMQ，...）中的外部数据的能力。

Flink 目的是为常见数据格式和存储系统提供 TableSources。请查看[Table Sources and Sinks](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/table/sourceSinks.html)以获取支持的 TableSources 列表以及如何构建自定义 TableSource 的说明。

在 TableEnvironment 中注册 TableSource 如下所示:

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// create a TableSource
TableSource csvSource = new CsvTableSource("/path/to/file", ...);

// register the TableSource as table "CsvTable"
tableEnv.registerTableSource("CsvTable", csvSource);
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// create a TableSource
val csvSource: TableSource = new CsvTableSource("/path/to/file", ...)

// register the TableSource as table "CsvTable"
tableEnv.registerTableSource("CsvTable", csvSource)
```

#### 3.3 注册 TableSink

已注册的 TableSink 可用于将 Table API 或 SQL 查询的结果输出到外部存储系统中，例如数据库，key-value存储系统，消息队列或文件系统（以不同的编码方式，例如CSV，Apache [ Parquet，Avro，ORC]，...）。

Flink 目的是为常见的数据格式和存储系统提供 TableSinks。有关可用接收器以及如何实现自定义TableSink的的详细信息，请参阅[Table Sources and Sinks](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/table/sourceSinks.html)。

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// create a TableSink
TableSink csvSink = new CsvTableSink("/path/to/file", ...);

// define the field names and types
String[] fieldNames = {"a", "b", "c"};
TypeInformation[] fieldTypes = {Types.INT, Types.STRING, Types.LONG};

// register the TableSink as table "CsvSinkTable"
tableEnv.registerTableSink("CsvSinkTable", fieldNames, fieldTypes, csvSink);
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// create a TableSink
val csvSink: TableSink = new CsvTableSink("/path/to/file", ...)

// define the field names and types
val fieldNames: Array[String] = Array("a", "b", "c")
val fieldTypes: Array[TypeInformation[_]] = Array(Types.INT, Types.STRING, Types.LONG)

// register the TableSink as table "CsvSinkTable"
tableEnv.registerTableSink("CsvSinkTable", fieldNames, fieldTypes, csvSink)
```

### 4. 注册外部目录

外部目录可以提供有关外部数据库和表的信息，例如它们的名称，schema，统计信息以及有关如何访问存储在外部数据库，表或文件中的数据的信息。

外部目录可以通过实现 ExternalCatalog 接口来创建，并在 TableEnvironment 中注册如下：

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// create an external catalog
ExternalCatalog catalog = new InMemoryExternalCatalog();

// register the ExternalCatalog catalog
tableEnv.registerExternalCatalog("InMemCatalog", catalog);
```
Scala版本：
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// create an external catalog
val catalog: ExternalCatalog = new InMemoryExternalCatalog

// register the ExternalCatalog catalog
tableEnv.registerExternalCatalog("InMemCatalog", catalog)
```
一旦在 TableEnvironment 中注册，可以通过指定其完整路径（如catalog.database.table）从 Table API 或 SQL 查询中访问 ExternalCatalog 中定义的所有表。

目前，Flink 提供用于演示和测试目的的 InMemoryExternalCatalog。 但是，ExternalCatalog 接口也可用于将 HCatalog 或 Metastore 等目录连接到 Table API。

### 5. 查询 Table

#### 5.1 Table API

Table API 是用于 Scala 和 Java 的集成语言查询API。与SQL相比，查询不是以字符串形式指定的，而是以宿主语言逐步编写的。

该 API 基于表示表（流或批处理）的 `Table` 类，并提供了应用关系性操作的方法。这些方法返回一个新的 Table 对象，表示在输入表上应用关系性操作的结果。一些关系性操作由多个方法调用组成，如 table.groupBy（...）.select（），其中 groupBy（...） 指定表的分组， select（...） 指定在分组表上的投影。

[Table API](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/table/tableApi.html) 文档描述了在流和批处理表上支持的所有 Table API 操作。以下示例显示了一个简单的 Table API 聚合查询：

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// register Orders table

// scan registered Orders table
Table orders = tableEnv.scan("Orders");
// compute revenue for all customers from France
Table revenue = orders
  .filter("cCountry === 'FRANCE'")
  .groupBy("cID, cName")
  .select("cID, cName, revenue.sum AS revSum");

// emit or convert Table
// execute query
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// register Orders table

// scan registered Orders table
Table orders = tableEnv.scan("Orders")
// compute revenue for all customers from France
Table revenue = orders
  .filter('cCountry === "FRANCE")
  .groupBy('cID, 'cName)
  .select('cID, 'cName, 'revenue.sum AS 'revSum)

// emit or convert Table
// execute query
```

#### 5.2 SQL

Flink 的 SQL 集成基于 Apache Calcite，其实现了 SQL 标准。SQL查询被指定为常规字符串。[SQL](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/table/sql.html) 文档描述了 Flink 对流和批处理表的 SQL 支持。以下示例显示如何指定查询并将结果作为表返回。

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// register Orders table

// compute revenue for all customers from France
Table revenue = tableEnv.sqlQuery(
    "SELECT cID, cName, SUM(revenue) AS revSum " +
    "FROM Orders " +
    "WHERE cCountry = 'FRANCE' " +
    "GROUP BY cID, cName"
  );

// emit or convert Table
// execute query
```

Scala版本：
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// register Orders table

// compute revenue for all customers from France
Table revenue = tableEnv.sqlQuery("""
  |SELECT cID, cName, SUM(revenue) AS revSum
  |FROM Orders
  |WHERE cCountry = 'FRANCE'
  |GROUP BY cID, cName
  """.stripMargin)

// emit or convert Table
// execute query
```
以下示例展示了如何指定将其结果插入注册表的更新查询：

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// register "Orders" table
// register "RevenueFrance" output table

// compute revenue for all customers from France and emit to "RevenueFrance"
tableEnv.sqlUpdate(
    "INSERT INTO RevenueFrance " +
    "SELECT cID, cName, SUM(revenue) AS revSum " +
    "FROM Orders " +
    "WHERE cCountry = 'FRANCE' " +
    "GROUP BY cID, cName"
  );

// execute query
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// register "Orders" table
// register "RevenueFrance" output table

// compute revenue for all customers from France and emit to "RevenueFrance"
tableEnv.sqlUpdate("""
  |INSERT INTO RevenueFrance
  |SELECT cID, cName, SUM(revenue) AS revSum
  |FROM Orders
  |WHERE cCountry = 'FRANCE'
  |GROUP BY cID, cName
  """.stripMargin)

// execute query
```

#### 5.3 Table API 与 SQL 混合使用‘

Table API 和 SQL 查询可以轻松混合使用，因为它们都返回 Table 对象：
- Table API 查询可以在 SQL 查询返回的 Table 对象上定义。
- SQL 查询可以通过在 TableEnvironment 中注册结果表并在 SQL 查询的 FROM 子句中引用它，在 Table API 查询的结果上定义。

### 6. 输出 Table

通过将表写入 TableSink 来输出表。TableSink 是一个通用接口，支持多种文件格式（例如 CSV，Apache Parquet，Apache Avro），存储系统（例如 JDBC，Apache HBase，Apache Cassandra，Elasticsearch）或消息系统（例如Apache Kafka，RabbitMQ的）。

批处理表只能写入 BatchTableSink，而流表只能写入 AppendStreamTableSink，RetractStreamTableSink 或 UpsertStreamTableSink。

有两种方法可以输出表：
- Table.writeToSink（TableSink sink）方法使用提供的 TableSink 输出表以及使用输出表的 schema 自动配置 Sink。
- Table.insertInto（String sinkTable）方法在 TableEnvironment 的目录中根据提供的名称查找使用特定 schema 注册的 TableSink。要输出的表的 schema 根据已注册 TableSink 的 schema 进行验证。

以下示例显示如何输出表：

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// compute a result Table using Table API operators and/or SQL queries
Table result = ...

// create a TableSink
TableSink sink = new CsvTableSink("/path/to/file", fieldDelim = "|");

// METHOD 1:
//   Emit the result Table to the TableSink via the writeToSink() method
result.writeToSink(sink);

// METHOD 2:
//   Register the TableSink with a specific schema
String[] fieldNames = {"a", "b", "c"};
TypeInformation[] fieldTypes = {Types.INT, Types.STRING, Types.LONG};
tableEnv.registerTableSink("CsvSinkTable", fieldNames, fieldTypes, sink);
//   Emit the result Table to the registered TableSink via the insertInto() method
result.insertInto("CsvSinkTable");

// execute the program
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// compute a result Table using Table API operators and/or SQL queries
val result: Table = ...

// create a TableSink
val sink: TableSink = new CsvTableSink("/path/to/file", fieldDelim = "|")

// METHOD 1:
//   Emit the result Table to the TableSink via the writeToSink() method
result.writeToSink(sink)

// METHOD 2:
//   Register the TableSink with a specific schema
val fieldNames: Array[String] = Array("a", "b", "c")
val fieldTypes: Array[TypeInformation] = Array(Types.INT, Types.STRING, Types.LONG)
tableEnv.registerTableSink("CsvSinkTable", fieldNames, fieldTypes, sink)
//   Emit the result Table to the registered TableSink via the insertInto() method
result.insertInto("CsvSinkTable")

// execute the program
```

### 7. 转换与执行查询

Table API 和 SQL 查询被转换成 DataStream 或 DataSet 程序，具体取决于它们的输入是流式还是批量输入。查询在内部表示为逻辑查询计划，并分为两个阶段：
- 逻辑计划的优化，
- 转换成 DataStream 或 DataSet 程序。

在下列情况下会转换 Table API 或 SQL查询：
- Table 被发送到 TableSink，即当 Table.writeToSink（） 或 Table.insertInto（） 被调用时。
- 指定 SQL 更新查询，即调用 TableEnvironment.sqlUpdate（） 时。
- Table 被转换成 DataStream 或 DataSet。

转换完成后，Table API 或 SQL 查询将像常规 DataStream 或 DataSet 程序一样处理，并在调用 StreamExecutionEnvironment.execute（） 或 ExecutionEnvironment.execute（） 时执行。

### 8. 与DataStream和DataSet API集成

Table API 和 SQL 查询可以轻松集成并嵌入到 DataStream 和 DataSet 程序中。例如，可以查询外部表（例如，从RDBMS），执行一些预处理，例如筛选，投影，聚合或加入元数据，然后使用 DataStream 或 DataSet API（以及在这些API之上构建的任何库，例如 CEP 或 Gelly）进一步进行处理。相反，Table API 或 SQL 查询也可以应用于 DataStream 或 DataSet 程序的结果上。

这种交互可以通过将 DataStream 或 DataSet 转换为 Table 来实现，反之亦然。在本节中，我们将介绍如何完成这些转换。

#### 8.1 Scala的隐式转换

Scala Table API 具有 DataSet，DataStream 和 Table 类的隐式转换功能。对于 Scala DataStream API 除了导入 org.apache.flink.api.scala._ 外，还可以导入org.apache.flink.table.api.scala._ 来启用转换。

#### 8.2 将DataStream或DataSet注册为Table

DataStream 或 DataSet 可以在 TableEnvironment 中注册为 Table。结果表的 schema 取决于注册的 DataStream 或 DataSet 的数据类型。有关详细信息，请查阅 [数据类型与表 schema 的映射]()。

Java版本:
```java
// get StreamTableEnvironment
// registration of a DataSet in a BatchTableEnvironment is equivalent
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

DataStream<Tuple2<Long, String>> stream = ...

// register the DataStream as Table "myTable" with fields "f0", "f1"
tableEnv.registerDataStream("myTable", stream);

// register the DataStream as table "myTable2" with fields "myLong", "myString"
tableEnv.registerDataStream("myTable2", stream, "myLong, myString");
```
Scala版本:
```scala
// get TableEnvironment
// registration of a DataSet is equivalent
val tableEnv = TableEnvironment.getTableEnvironment(env)

val stream: DataStream[(Long, String)] = ...

// register the DataStream as Table "myTable" with fields "f0", "f1"
tableEnv.registerDataStream("myTable", stream)

// register the DataStream as table "myTable2" with fields "myLong", "myString"
tableEnv.registerDataStream("myTable2", stream, 'myLong, 'myString)
```

> 注意：DataStream表的名称不能与 `^_DataStreamTable_ [0-9]+` 模式匹配，并且 DataSet 表的名称不能与 `^_DataSetTable_ [0-9]+` 模式匹配。 这些模式仅供内部使用。

### 8.3 将DataStream或DataSet转换为Table

除了在 TableEnvironment 中注册 DataStream 或 DataSet，也可以直接转换为 Table。如果想在 Table API 查询中使用 Table，这很方便。

Java版本:
```java
// get StreamTableEnvironment
// registration of a DataSet in a BatchTableEnvironment is equivalent
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

DataStream<Tuple2<Long, String>> stream = ...

// Convert the DataStream into a Table with default fields "f0", "f1"
Table table1 = tableEnv.fromDataStream(stream);

// Convert the DataStream into a Table with fields "myLong", "myString"
Table table2 = tableEnv.fromDataStream(stream, "myLong, myString");
```
Scala版本:
```scala
// get TableEnvironment
// registration of a DataSet is equivalent
val tableEnv = TableEnvironment.getTableEnvironment(env)

val stream: DataStream[(Long, String)] = ...

// convert the DataStream into a Table with default fields '_1, '_2
val table1: Table = tableEnv.fromDataStream(stream)

// convert the DataStream into a Table with fields 'myLong, 'myString
val table2: Table = tableEnv.fromDataStream(stream, 'myLong, 'myString)
```

#### 8.4 将Table转换为DataStream或DataSet

Table 可以转换成 DataStream 或 DataSet。通过这种方式，可以在 Table API 或 SQL 查询的结果上运行自定义的 DataStream 或 DataSet程序。

将 Table 转换为 DataStream 或 DataSet 时，需要指定结果 DataStream 或 DataSet 的数据类型，即 Table 中行将被转换成的数据类型。通常最方便的转换类型是 Row。以下列表描述了不同选项的功能：
- Row：字段按位置映射，支持任意数量的字段，支持空值，无类型安全访问。
- POJO：字段按名称映射（POJO字段必须命名为Table字段），支持任意数量的字段，支持空值，类型安全访问。
- Case Class：字段按位置映射，不支持空值，类型安全访问。
- Tuple：字段按位置映射，限制为22（Scala）或25（Java）个字段，不支持空值，类型安全访问。
- Atomic：表必须只有一个字段，不支持空值，类型安全的访问。

##### 8.4.1 将Table转换为DataStream

作为流式查询结果的 Table 将被动态更新，即当新的记录到达查询的输入流时它将发生变化。因此，动态查询转换到的 DataStream 需要对 Table 的更新进行编码。

有两种模式可以将 Table 转换为 DataStream：
- 追加模式：只有在动态表格通过 INSERT 更改进行修改时才能使用此模式，即只能追加且以前输出的结果不会更新。
- 撤回模式：任何时候都可以使用此模式。它使用布尔标志对 INSERT 和 DELETE 更改进行编码。

Java版本:
```java
// get StreamTableEnvironment.
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// Table with two fields (String name, Integer age)
Table table = ...

// convert the Table into an append DataStream of Row by specifying the class
DataStream<Row> dsRow = tableEnv.toAppendStream(table, Row.class);

// convert the Table into an append DataStream of Tuple2<String, Integer>
//   via a TypeInformation
TupleTypeInfo<Tuple2<String, Integer>> tupleType = new TupleTypeInfo<>(
  Types.STRING(),
  Types.INT());
DataStream<Tuple2<String, Integer>> dsTuple =
  tableEnv.toAppendStream(table, tupleType);

// convert the Table into a retract DataStream of Row.
//   A retract stream of type X is a DataStream<Tuple2<Boolean, X>>.
//   The boolean field indicates the type of the change.
//   True is INSERT, false is DELETE.
DataStream<Tuple2<Boolean, Row>> retractStream =
  tableEnv.toRetractStream(table, Row.class);
```
Scala版本:
```scala
// get TableEnvironment.
// registration of a DataSet is equivalent
val tableEnv = TableEnvironment.getTableEnvironment(env)

// Table with two fields (String name, Integer age)
val table: Table = ...

// convert the Table into an append DataStream of Row
val dsRow: DataStream[Row] = tableEnv.toAppendStream[Row](table)

// convert the Table into an append DataStream of Tuple2[String, Int]
val dsTuple: DataStream[(String, Int)] dsTuple =
  tableEnv.toAppendStream[(String, Int)](table)

// convert the Table into a retract DataStream of Row.
//   A retract stream of type X is a DataStream[(Boolean, X)].
//   The boolean field indicates the type of the change.
//   True is INSERT, false is DELETE.
val retractStream: DataStream[(Boolean, Row)] = tableEnv.toRetractStream[Row](table)
```

> 关于动态表及其属性的详细讨论在 [Streaming Queries](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/table/streaming.html)文档中给出。

#### 8.4.2 将Table转换为DataSet

Table 被转换成 DataSet，如下所示：

Java版本:
```java
// get BatchTableEnvironment
BatchTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// Table with two fields (String name, Integer age)
Table table = ...

// convert the Table into a DataSet of Row by specifying a class
DataSet<Row> dsRow = tableEnv.toDataSet(table, Row.class);

// convert the Table into a DataSet of Tuple2<String, Integer> via a TypeInformation
TupleTypeInfo<Tuple2<String, Integer>> tupleType = new TupleTypeInfo<>(
  Types.STRING(),
  Types.INT());
DataStream<Tuple2<String, Integer>> dsTuple =
  tableEnv.toAppendStream(table, tupleType);
```
Scala版本:
```scala
// get TableEnvironment
// registration of a DataSet is equivalent
val tableEnv = TableEnvironment.getTableEnvironment(env)

// Table with two fields (String name, Integer age)
val table: Table = ...

// convert the Table into a DataSet of Row
val dsRow: DataSet[Row] = tableEnv.toDataSet[Row](table)

// convert the Table into a DataSet of Tuple2[String, Int]
val dsTuple: DataSet[(String, Int)] = tableEnv.toDataSet[(String, Int)](table)
```

#### 8.5 数据类型与Table Schema的映射

Flink 的 DataStream 和 DataSet API 支持多种类型，如 Tuples（内置Scala和Flink Java元组），POJO，Case Class和 原子类型。在下文中，我们将描述 Table API 如何将这些类型转换为内部 row 表示形式并显示将 DataStream 转换为 Table 的示例。

##### 8.5.1 原子类型

Flink 将原始类型（Integer，Double，String）或泛型类型（无法分析和分解的类型）视为原子类型。原子类型的 DataStream 或 DataSet 被转换为具有单个属性的 Table。属性的类型是从原子类型推断的，并且必须指定属性的名称。

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

DataStream<Long> stream = ...
// convert DataStream into Table with field "myLong"
Table table = tableEnv.fromDataStream(stream, "myLong");
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

val stream: DataStream[Long] = ...
// convert DataStream into Table with field 'myLong
val table: Table = tableEnv.fromDataStream(stream, 'myLong)
```

##### 8.5.2 元组（Scala和Java）和Case Classes（仅适用于Scala）

Flink 支持 Scala 的内置元组，并为Java 提供自己的元组类。这两种元组的 DataStreams 和 DataSet 都可以转换成 Table。可以通过为所有字段提供名称（基于位置的映射）来重命名字段。如果未指定字段名称，则使用默认字段名称。

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

DataStream<Tuple2<Long, String>> stream = ...

// convert DataStream into Table with field names "myLong", "myString"
Table table1 = tableEnv.fromDataStream(stream, "myLong, myString");

// convert DataStream into Table with default field names "f0", "f1"
Table table2 = tableEnv.fromDataStream(stream);
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

val stream: DataStream[(Long, String)] = ...

// convert DataStream into Table with field names 'myLong, 'myString
val table1: Table = tableEnv.fromDataStream(stream, 'myLong, 'myString)

// convert DataStream into Table with default field names '_1, '_2
val table2: Table = tableEnv.fromDataStream(stream)

// define case class
case class Person(name: String, age: Int)
val streamCC: DataStream[Person] = ...

// convert DataStream into Table with default field names 'name, 'age
val tableCC1 = tableEnv.fromDataStream(streamCC)

// convert DataStream into Table with field names 'myName, 'myAge
val tableCC1 = tableEnv.fromDataStream(streamCC, 'myName, 'myAge)
```

##### 8.5.3 POJO（Java和Scala）

Flink 支持 POJO 作为复合类型。[这里](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/api_concepts.html#pojos)描述了决定 POJO 的规则。

将 POJO DataStream 或 DataSet 转换为 Table 且不指定字段名称时，将使用 POJO 原始字段名称。重命名 POJO 原始字段需要关键字，因为 POJO 字段没有固有顺序。名称映射需要原始名称，不能通过位置定位。

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// Person is a POJO with fields "name" and "age"
DataStream<Person> stream = ...

// convert DataStream into Table with field names "name", "age"
Table table1 = tableEnv.fromDataStream(stream);

// convert DataStream into Table with field names "myName", "myAge"
Table table2 = tableEnv.fromDataStream(stream, "name as myName, age as myAge");
```
Scala版本:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// Person is a POJO with field names "name" and "age"
val stream: DataStream[Person] = ...

// convert DataStream into Table with field names 'name, 'age
val table1: Table = tableEnv.fromDataStream(stream)

// convert DataStream into Table with field names 'myName, 'myAge
val table2: Table = tableEnv.fromDataStream(stream, 'name as 'myName, 'age as 'myAge)
```
##### 8.5.4 Row

Row 数据类型支持任意数量的字段以及支持空值字段。可以通过 RowTypeInfo 指定字段名称，或者将 Row DataStream 或 DataSet 转换为Table（基于位置）。

Java版本:
```java
// get a StreamTableEnvironment, works for BatchTableEnvironment equivalently
StreamTableEnvironment tableEnv = TableEnvironment.getTableEnvironment(env);

// DataStream of Row with two fields "name" and "age" specified in `RowTypeInfo`
DataStream<Row> stream = ...

// convert DataStream into Table with field names "name", "age"
Table table1 = tableEnv.fromDataStream(stream);

// convert DataStream into Table with field names "myName", "myAge"
Table table2 = tableEnv.fromDataStream(stream, "myName, myAge");
```
Scala版本n:
```scala
// get a TableEnvironment
val tableEnv = TableEnvironment.getTableEnvironment(env)

// DataStream of Row with two fields "name" and "age" specified in `RowTypeInfo`
val stream: DataStream[Row] = ...

// convert DataStream into Table with field names 'name, 'age
val table1: Table = tableEnv.fromDataStream(stream)

// convert DataStream into Table with field names 'myName, 'myAge
val table2: Table = tableEnv.fromDataStream(stream, 'myName, 'myAge)
```

### 9. 查询优化

Apache Flink 利用 Apache Calcite 来优化和转换查询。当前执行的优化包括投影和过滤器下推，子查询相关以及其他类型的查询重写。Flink 尚未优化连接的顺序，但是可以按照查询中定义的顺序（FROM 子句中的 Table 的顺序或 WHERE 子句中的 join 的顺序）执行它们。

通过提供一个 CalciteConfig 对象，可以调整一组在不同阶段应用的优化规则。这可以通过调用 CalciteConfig.createBuilder（） 的构建器创建，并通过调用 tableEnv.getConfig.setCalciteConfig（calciteConfig） 提供给TableEnvironment。

#### 9.1 Explaining Table

Table API 提供了一种机制来 explain 逻辑和优化查询计划来计算 Table。这是通过 TableEnvironment.explain（table） 方法完成的。它返回一个描述三个计划的字符串：
- 关系查询的抽象语法树，即未优化的逻辑查询计划，
- 优化的逻辑查询计划
- 物理执行计划。

以下代码显示了一个示例和相应的输出：

Java版本:
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tEnv = TableEnvironment.getTableEnvironment(env);

DataStream<Tuple2<Integer, String>> stream1 = env.fromElements(new Tuple2<>(1, "hello"));
DataStream<Tuple2<Integer, String>> stream2 = env.fromElements(new Tuple2<>(1, "hello"));

Table table1 = tEnv.fromDataStream(stream1, "count, word");
Table table2 = tEnv.fromDataStream(stream2, "count, word");
Table table = table1
  .where("LIKE(word, 'F%')")
  .unionAll(table2);

String explanation = tEnv.explain(table);
System.out.println(explanation);
```
Scala版本:
```scala
val env = StreamExecutionEnvironment.getExecutionEnvironment
val tEnv = TableEnvironment.getTableEnvironment(env)

val table1 = env.fromElements((1, "hello")).toTable(tEnv, 'count, 'word)
val table2 = env.fromElements((1, "hello")).toTable(tEnv, 'count, 'word)
val table = table1
  .where('word.like("F%"))
  .unionAll(table2)

val explanation: String = tEnv.explain(table)
println(explanation)
```

输出:
```
== Abstract Syntax Tree ==
LogicalUnion(all=[true])
  LogicalFilter(condition=[LIKE($1, 'F%')])
    LogicalTableScan(table=[[_DataStreamTable_0]])
  LogicalTableScan(table=[[_DataStreamTable_1]])

== Optimized Logical Plan ==
DataStreamUnion(union=[count, word])
  DataStreamCalc(select=[count, word], where=[LIKE(word, 'F%')])
    DataStreamScan(table=[[_DataStreamTable_0]])
  DataStreamScan(table=[[_DataStreamTable_1]])

== Physical Execution Plan ==
Stage 1 : Data Source
  content : collect elements with CollectionInputFormat

Stage 2 : Data Source
  content : collect elements with CollectionInputFormat

  Stage 3 : Operator
    content : from: (count, word)
    ship_strategy : REBALANCE

    Stage 4 : Operator
      content : where: (LIKE(word, 'F%')), select: (count, word)
      ship_strategy : FORWARD

      Stage 5 : Operator
        content : from: (count, word)
        ship_strategy : REBALANCE
```

> Flink版本:1.4


原文: https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/table/common.html#create-a-tableenvironment
