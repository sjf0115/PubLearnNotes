---
layout: post
author: sjf0115
title: Spark SQL 数据源 加载与保存函数
date: 2018-06-10 17:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-load-and-save-functions
---

> Spark 版本：3.1.3

Spark SQL 支持通过 DataFrame 接口操作各种数据源。可以使用关系变换，也可以创建临时视图来操作 DataFrame。将 DataFrame 注册为临时视图可以允许你在其数据上运行 SQL 查询。本节介绍使用 Spark Data Sources 加载和保存数据的通用方法。



最简单的，默认数据源（parquet，除非通过 `spark.sql.sources.default` 重新配置)，可以使用所有的操作。

Java版本：
```java
Dataset<Row> usersDF = sparkSession.read().load("src/main/resources/users.parquet");
usersDF.select("name", "favorite_color").write().save("namesAndFavColors.parquet");
```
Scala版本：
```scala
val usersDF = sparkSession.read.load("src/main/resources/users.parquet")
usersDF.select("name", "favorite_color").write.save("namesAndFavColors.parquet")
```
Python版本：
```Python
df = sparkSession.read.load("src/main/resources/users.parquet")
df.select("name", "favorite_color").write.save("namesAndFavColors.parquet")
```
## 1. 手动指定选项

你还可以手动指定要使用的是什么数据源，以及想传递给数据源的其他参数。数据源需要指定完全限定名（例如，`org.apache.spark.sql.parquet` ）, 但是对于内置数据源, 你也可以使用它们的简称（例如，json, parquet, jdbc, orc, libsvm, csv, text）。可以将从任何数据源类型加载的 DataFrame 转换为其他类型。

### 1.1 加载 Json 文件

你可以使用如下命令加载 json 文件，如下示例从一个 Json 文件中加载为 DataFrame，然后转换为一个 parquet 文件：

Java版本：
```java
Dataset<Row> peopleDF = sparkSession.read().format("json").load("src/main/resources/person.json");
peopleDF.select("name", "age").write().format("parquet").save("namesAndAges.parquet");
```
Scala版本：
```scala
val peopleDF = sparkSession.read.format("json").load("src/main/resources/person.json")
peopleDF.select("name", "age").write.format("parquet").save("namesAndAges.parquet")
```
Python版本：
```Python
df = sparkSession.read.load("src/main/resources/person.json", format="json")
df.select("name", "age").write.save("namesAndAges.parquet", format="parquet")
```

### 1.2 加载 CSV 文件

你可以使用如下命令加载 CSV 文件：

Java版本：
```java
Dataset<Row> peopleDFCsv = sparkSession.read().format("csv")
  .option("sep", ";")
  .option("inferSchema", "true")
  .option("header", "true")
  .load("src/main/resources/people.csv");
```
Scala版本：
```scala
val peopleDFCsv = spark.read.format("csv")
  .option("sep", ";")
  .option("inferSchema", "true")
  .option("header", "true")
  .load("src/main/resources/people.csv")
```
Python版本：
```Python
df = spark.read.load("examples/src/main/resources/people.csv",
  format="csv", sep=":", inferSchema="true", header="true")
```

### 1.3 保存 ORC 文件

这些扩展选项参数也可以在写操作中使用。例如，你可以为 ORC 数据源控制布隆过滤器和字典编码。

Java版本：
```java
usersDF.write().format("orc")
  .option("orc.bloom.filter.columns", "favorite_color")
  .option("orc.dictionary.key.threshold", "1.0")
  .option("orc.column.encoding.direct", "name")
  .save("users_with_options.orc");
```
Scala版本：
```scala
usersDF.write.format("orc")
  .option("orc.bloom.filter.columns", "favorite_color")
  .option("orc.dictionary.key.threshold", "1.0")
  .option("orc.column.encoding.direct", "name")
  .save("users_with_options.orc")
```
Python版本：
```python
df = spark.read.orc("examples/src/main/resources/users.orc")
(df.write.format("orc")
    .option("orc.bloom.filter.columns", "favorite_color")
    .option("orc.dictionary.key.threshold", "1.0")
    .option("orc.column.encoding.direct", "name")
    .save("users_with_options.orc"))
```
SQL 版本：
```sql
CREATE TABLE users_with_options (
  name STRING,
  favorite_color STRING,
  favorite_numbers array<integer>
) USING ORC
OPTIONS (
  orc.bloom.filter.columns 'favorite_color',
  orc.dictionary.key.threshold '1.0',
  orc.column.encoding.direct 'name'
)
```

## 2. 在文件上直接运行SQL

除了使用 read API 将文件加载到 DataFrame 中然后对其进行查询外，还可以使用 SQL 直接查询该文件。

Java版本：
```java
Dataset<Row> sqlDF = sparkSession.sql("SELECT * FROM parquet.`src/main/resources/users.parquet`");
sqlDF.show();
/**
 +------+--------------+----------------+
 |  name|favorite_color|favorite_numbers|
 +------+--------------+----------------+
 |Alyssa|          null|  [3, 9, 15, 20]|
 |   Ben|           red|              []|
 +------+--------------+----------------+
 */
```
Scala版本：
```scala
val sqlDF = sparkSession.sql("SELECT * FROM parquet.`src/main/resources/users.parquet`")
```
Python版本：
```python
df = sparkSession.sql("SELECT * FROM parquet.`src/main/resources/users.parquet`")
```

## 3. SaveMode

保存操作可以选择使用 SaveMode 来指定如何处理现有数据（如果存在）。我们需要知道这些保存模式不使用任何锁并且不是原子的。此外，执行 Overwrite，在写入新数据之前旧数据会被删除。

Scala/Java|Any Language|含义
---|---|---
SaveMode.ErrorIfExists (默认)	|error或者errorifexists (默认)	|将 DataFrame 保存到数据源, 如果数据已经存在, 将会抛出异常。
SaveMode.Append| append |将 DataFrame 保存到数据源时, 如果数据/表已存在, 那么 DataFrame 的内容将被追加到现有数据中。
SaveMode.Overwrite|	overwrite|	Overwrite 模式意味着将 DataFrame 保存到数据源时，如果数据/表已经存在，那么 DataFrame 的内容将覆盖现有数据。
SaveMode.Ignore| ignore| Ignore 模式意味着当将 DataFrame 保存到数据源时，如果数据已经存在，那么保存操作不会保存 DataFrame 的内容, 并且不更改现有数据。这与 SQL 中的 `CREATE TABLE IF NOT EXISTS` 类似。


## 4. 保存到持久化表中

可以使用 saveAsTable 命令将 DataFrames 以持久化表保存到 Hive 元数据中。请注意, 需要使用此功能，并不一定部署 Hive。如果没有部署 Hive ，Spark 将为你创建默认的本地 Hive 元数据（使用 Derby ）。与 createOrReplaceTempView 命令不同， saveAsTable 将 materialize （实现） DataFrame 的内容，并创建一个指向 Hive 元数据中数据的指针。即使你的 Spark 程序重新启动, 持久化表仍然会存在，只要你保持与同一个元数据连接。可以通过使用表的名称在 SparkSession 上调用 table 方法来创建持久化表的 DataFrame。

对于基于文件的数据源，例如 text, parquet，json等，你可以通过 path 选项指定自定义表路径, 例如 `df.write.option("path", "/some/path").saveAsTable("t")`。当表被删除时,自定义表路径不会被删除, 并且表数据仍然存在。如果未指定自定义表路径, Spark 将把数据写入 warehouse 目录下的默认表路径。当表被删除时, 默认的表路径也将被删除。

从 Spark 2.1 开始, 持久性数据源表将每个分区的元数据存储在 Hive 元数据中。这带来了几个好处:
- 由于元数据只返回查询的必要分区, 因此不再需要发现第一个查询上的所有分区。
- Hive DDLs 如 `ALTER TABLE PARTITION ... SET LOCATION` 现在可用于使用 Datasource API 创建的表上。

请注意, 创建外部数据源表(带有 path 选项)时, 默认情况下不会收集分区信息。要同步元数据中的分区信息, 你可以调用 `MSCK REPAIR TABLE`。

## 5. 分桶, 排序和分区

对于基于文件的数据源, 也可以对输出进行分桶，排序或者分区。分桶和排序仅适用于持久化表:

Java版本：
```java
peopleDF.write().bucketBy(42, "name").sortBy("age").saveAsTable("people_bucketed");
```
Scala版本：
```scala
peopleDF.write.bucketBy(42, "name").sortBy("age").saveAsTable("people_bucketed")
```
Python版本：
```Python
df.write.bucketBy(42, "name").sortBy("age").saveAsTable("people_bucketed")
```

在使用 Dataset API 时, 分区可以同时与 save 和 saveAsTable 一起使用：

Java版本：
```java
usersDF
  .write()
  .partitionBy("favorite_color")
  .format("parquet")
  .save("namesPartByColor.parquet");
```
Scala版本：
```scala
usersDF.write.partitionBy("favorite_color").format("parquet").save("namesPartByColor.parquet")
```
Python版本：
```python
df.write.partitionBy("favorite_color").format("parquet").save("namesPartByColor.parquet")
```

可以在单个表上使用分区和分桶:

Java版本：
```java
peopleDF
  .write()
  .partitionBy("favorite_color")
  .bucketBy(42, "name")
  .saveAsTable("people_partitioned_bucketed");
```
Scala版本：
```scala
peopleDF
  .write
  .partitionBy("favorite_color")
  .bucketBy(42, "name")
  .saveAsTable("people_partitioned_bucketed")
```
Python版本：
```python
df = spark.read.parquet("examples/src/main/resources/users.parquet")
(df
    .write
    .partitionBy("favorite_color")
    .bucketBy(42, "name")
    .saveAsTable("people_partitioned_bucketed"))
```

partitionBy 创建一个目录结构, 如 [Partition Discovery](http://spark.apache.org/docs/latest/sql-programming-guide.html#partition-discovery) 部分所述. 因此, 对基数较高的列的适用性有限。相反, bucketBy 可以在固定数量的桶中分配数据, 并且可以在唯一值无限时使用数据。

原文：http://spark.apache.org/docs/2.3.1/sql-programming-guide.html#generic-loadsave-functions
