
## 1. Table API & SQL 程序结构

在 Flink 中，Table API 和 SQL 可以看作联结在一起的一套 API，这套 API 的核心概念是一个可以用作 Query 输入和输出的表 Table。在我们程序中，输入数据可以定义成一张表，然后对这张表进行查询得到一张新的表，最后还可以定义一张用于输出的表，负责将处理结果写入到外部系统。

我们可以看到，程序的整体处理流程与 DataStream API 非常相似，也可以分为读取数据源(Source)、转换(Transform)、输出数据(Sink)三部分。只不过这里的输入输出操作不需要额外定义，只需要将用于输入和输出的表 Table 定义出来，然后进行转换查询就可以了。程序基本架构如下:
```java
import org.apache.flink.table.api.*;
import org.apache.flink.connector.datagen.table.DataGenOptions;

// Create a TableEnvironment for batch or streaming execution.
// See the "Create a TableEnvironment" section for details.
TableEnvironment tableEnv = TableEnvironment.create(/*…*/);

// Create a source table
tableEnv.createTemporaryTable("SourceTable", TableDescriptor.forConnector("datagen")
    .schema(Schema.newBuilder()
      .column("f0", DataTypes.STRING())
      .build())
    .option(DataGenOptions.ROWS_PER_SECOND, 100)
    .build())

// Create a sink table (using SQL DDL)
tableEnv.executeSql("CREATE TEMPORARY TABLE SinkTable WITH ('connector' = 'blackhole') LIKE SourceTable");

// Create a Table object from a Table API query
Table table2 = tableEnv.from("SourceTable");

// Create a Table object from a SQL query
Table table3 = tableEnv.sqlQuery("SELECT * FROM SourceTable");

// Emit a Table API result Table to a TableSink, same for SQL result
TableResult tableResult = table2.executeInsert("SinkTable");
```

## 2. 创建 TableEnvironment

```java
EnvironmentSettings settings = EnvironmentSettings
        .newInstance()
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

表 Table 是在关系型数据库中我们非常熟悉的一个概念，是数据存储的基本形式，也是 SQL 执行的基本对象。Flink 中的表 Table 概念也并不特殊，是由多个'行' Row 数据构成的，每行又可以定义好多的列 Column 字段。

为了方便查询表 Table，TableEnvironment 会维护一个目录 Catalog 和表 Table 的映射关系。所以表 Table 都是通过 Catalog 来进行注册创建的。每个表 Table 都有一个唯一的 ID，由三部分组成：目录(Catalog)名称，数据库(Database)名称 以及表(Table)名。在默认情况下，目录 Catalog 名称为 default_catalog，数据库 Database 名称为 default_database。如果我们有一个表 Table 叫作 MyTable，它完整的 ID 就是 default_catalog.default_database.MyTable。

表 Table 有两种类型的表，一种是连接器表(Connector Tables) Table，一种是虚拟表(Virtual Tables) VIEW。连接器表一般用来描述外部数据，例如文件、数据库表或者消息队列。虚拟表通常是 Table API 或 SQL 查询的结果，可以基于现有的连接器表 Table 对象来创建。

### 3.1 连接器表

创建 Table 最直观的方式，就是通过连接器(Connector)连接到一个外部系统，然后定义出对应的表结构。例如我们可以连接到 Kafka 或者文件系统，将存储在这些外部系统的数据以表 Table 的形式定义出来，这样对表 Table 的读写就可以通过连接器转换成对外部系统的读写。

Connector Tables 可以直接使用 Table API 创建，也可以通过 SQL DDL 创建：
```java
// Using table descriptors
final TableDescriptor sourceDescriptor = TableDescriptor.forConnector("datagen")
    .schema(Schema.newBuilder()
    .column("f0", DataTypes.STRING())
    .build())
    .option(DataGenOptions.ROWS_PER_SECOND, 100)
    .build();

tableEnv.createTable("SourceTableA", sourceDescriptor);
tableEnv.createTemporaryTable("SourceTableB", sourceDescriptor);

// Using SQL DDL
tableEnv.executeSql("CREATE [TEMPORARY] TABLE MyTable (...) WITH (...)")
```

### 3.2 虚拟表

Table API 对象对应于 SQL 术语中的 VIEW（虚拟表），封装了一个逻辑查询计划。可以在 Catalog 中创建，如下所示：
```java
// 创建 TableEnvironment
TableEnvironment tableEnv = ...;

//
Table projTable = tableEnv.from("X").select(...);

// register the Table projTable as table "projectedTable"
tableEnv.createTemporaryView("projectedTable", projTable);
```

## 4. 查询 Table

### 4.1 通过 Table API 查询

Table API 是用于 Scala 和 Java 集成语言查询 API。与 SQL 相比，查询不指定为字符串，而是使用宿主语言一步步链式调用。

Table API 的核心是表示表（流式或批处理）的 Table 类，并提供可以使用关系操作的方法。每个方法的返回都是一个新的 Table 对象，表示对输入 Table 应用关系操作的结果。一些关系操作是由多个方法调用组成的，例如 table.groupBy(...).select()，其中 groupBy(...) 指定了 table 的分组，select(...) 指定了在分组表上的投影。如下示例展示了一个简单的 Table API 聚合查询：
```java
// get a TableEnvironment
TableEnvironment tableEnv = ...; // see "Create a TableEnvironment" section

// register Orders table

// scan registered Orders table
Table orders = tableEnv.from("Orders");
// compute revenue for all customers from France
Table revenue = orders
  .filter($("cCountry").isEqual("FRANCE"))
  .groupBy($("cID"), $("cName"))
  .select($("cID"), $("cName"), $("revenue").sum().as("revSum"));

// emit or convert Table
// execute query
```
### 4.2 通过 SQL 查询

Flink SQL 基于 Apache Calcite 集成，实现了标准 SQL。SQL 查询被指定为常规字符串。如下示例展示如何指定查询并将结果作为表返回。
```java
// get a TableEnvironment
TableEnvironment tableEnv = ...; // see "Create a TableEnvironment" section

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
如下示例展示一个更新查询如何将结果插入已注册的表中：
```java
// get a TableEnvironment
TableEnvironment tableEnv = ...; // see "Create a TableEnvironment" section

// register "Orders" table
// register "RevenueFrance" output table

// compute revenue for all customers from France and emit to "RevenueFrance"
tableEnv.executeSql(
    "INSERT INTO RevenueFrance " +
    "SELECT cID, cName, SUM(revenue) AS revSum " +
    "FROM Orders " +
    "WHERE cCountry = 'FRANCE' " +
    "GROUP BY cID, cName"
  );
```

### 4.3 Mixing Table API and SQL

## 5. 输出 Table

通过将 Table 写入 TableSink 来输出 Table。TableSink 是一个通用接口，支持多种文件格式（例如 CSV、Apache Parquet、Apache Avro）、存储系统（例如 JDBC、Apache HBase、Apache Cassandra、Elasticsearch）或消息系统（例如 Apache Kafka、 兔MQ）。

批处理 Table 只能写入 BatchTableSink，而流 Table 需要一个 AppendStreamTableSink、RetractStreamTableSink 或者 UpsertStreamTableSink。

Table.executeInsert(String tableName) 方法将 Table 发送到已注册的 TableSink 上。该方法通过名称从 Catalog 中查找 TableSink，并验证 Table 的 Schema 与 TableSink 的 Schema 是否相同。如下示例展示了如何输出表：
```java
// get a TableEnvironment
TableEnvironment tableEnv = ...; // see "Create a TableEnvironment" section

// create an output Table
final Schema schema = Schema.newBuilder()
    .column("a", DataTypes.INT())
    .column("b", DataTypes.STRING())
    .column("c", DataTypes.BIGINT())
    .build();

tableEnv.createTemporaryTable("CsvSinkTable", TableDescriptor.forConnector("filesystem")
    .schema(schema)
    .option("path", "/path/to/file")
    .format(FormatDescriptor.forFormat("csv")
        .option("field-delimiter", "|")
        .build())
    .build());

// compute a result Table using Table API operators and/or SQL queries
Table result = ...

// emit the result Table to the registered TableSink
result.executeInsert("CsvSinkTable");
```


## 6. Translate and Execute a Query



## 7. Query Optimization

## 8. Explaining a Table





[Concepts & Common API](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/table/common/)
