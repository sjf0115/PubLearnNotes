---
layout: post
author: sjf0115
title: Spark SQL 数据源 Load 与 Save 函数
date: 2018-06-10 17:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-load-and-save-functions
---

> Spark 版本：3.1.3

Spark SQL 支持通过 DataFrame 接口操作各种数据源。可以使用关系变换，也可以创建临时视图来操作 DataFrame。将 DataFrame 注册为临时视图可以允许你在其数据上运行 SQL 查询。本节介绍使用 Spark Data Sources 加载和保存数据的通用方法。可以通过 load 方法从文件中加载数据创建 DataFrame，同时也可以使用 save 方法将 DataFrame 中的数据保存到文件中，具体如下所示。

Java版本：
```java
// 如果不指定 format 默认读取的是 parquet 文件
Dataset<Row> usersDF = spark.read().load("spark-example-3.1/src/main/resources/data/users.parquet");
usersDF.show();
// 如果不指定 format 默认保存的是 parquet 文件
usersDF.select("name", "favorite_color").write().save("namesAndFavColors.parquet");
```
Scala版本：
```scala
val usersDF = sparkSession.read.load("spark-example-3.1/src/main/resources/data/users.parquet")
usersDF.select("name", "favorite_color").write.save("namesAndFavColors.parquet")
```
Python版本：
```Python
usersDF = sparkSession.read.load("spark-example-3.1/src/main/resources/data/users.parquet")
usersDF.select("name", "favorite_color").write.save("namesAndFavColors.parquet")
```

> 如果不指定 format 默认读取和保存的是 parquet 文件

## 1. 手动指定选项

你还可以手动指定要使用的是什么数据源，以及想传递给数据源的其他参数。数据源需要指定完全限定名（例如，`org.apache.spark.sql.parquet` ）, 但是对于内置数据源, 你也可以使用它们的简称（例如，json, parquet, jdbc, orc, libsvm, csv, text）。可以将从任何数据源类型加载的 DataFrame 转换为其他类型。

### 1.1 加载 Json 文件

你可以使用如下命令加载 json 文件，如下示例从一个 Json 文件中加载为 DataFrame，然后选择 name 和 favorite_color 列输出为一个 json 文件：

Java版本：
```java
// format 指定为 json 读取的是 json 文件
Dataset<Row> usersDF = spark.read().format("json").load("spark-example-3.1/src/main/resources/data/users.json");
usersDF.show();
// format 指定为 json  保存的是 json 文件
usersDF.select("name", "favorite_color").write().format("json").save("namesAndFavColors.json");
```
Scala版本：
```scala
val usersDF = sparkSession.read.format("json").load("spark-example-3.1/src/main/resources/data/users.json")
usersDF.select("name", "favorite_color").write.format("json").save("namesAndFavColors.json")
```
Python版本：
```Python
usersDF = sparkSession.read.load("spark-example-3.1/src/main/resources/data/users.json", format="json")
usersDF.select("name", "favorite_color").write.save("namesAndFavColors.json", format="json")
```

### 1.2 加载 CSV 文件

你可以使用如下命令加载 CSV 文件，如下示例从一个 CSV 文件中加载为 DataFrame，然后选择 name 和 favorite_color 列输出为一个 json 文件：

Java版本：
```java
// format 指定为 csv 读取的是 csv 文件 指定额外参数 以;分割,有文件头
Dataset<Row> peopleDF = spark.read().format("csv")
        .option("sep", ";")
        .option("inferSchema", "true")
        .option("header", "true")
        .load("spark-example-3.1/src/main/resources/data/people2.csv");
peopleDF.show();

// format 指定为 csv 保存的是 csv 文件 以,分割不保留文件头
peopleDF.select("name", "age").write().format("csv")
        .option("sep", ",")
        .option("header", "false")
        .save("namesAndAges.csv");
```
Scala版本：
```scala
val peopleDF = spark.read.format("csv")
  .option("sep", ";")
  .option("inferSchema", "true")
  .option("header", "true")
  .load("spark-example-3.1/src/main/resources/data/people2.csv")
```
Python版本：
```Python
df = spark.read.load("spark-example-3.1/src/main/resources/data/people2.csv",
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
// 在 parquet 文件上直接运行 SQL
Dataset<Row> parquetDF = spark.sql("SELECT * FROM parquet.`spark-example-3.1/src/main/resources/data/users.parquet`");
parquetDF.show();
// 在 json 文件上直接运行 SQL
Dataset<Row> jsonDF = spark.sql("SELECT * FROM json.`spark-example-3.1/src/main/resources/data/users.json`");
jsonDF.show();
/**
 +------+--------------+----------------+
 |  name|favorite_color|favorite_numbers|
 +------+--------------+----------------+
 |Alyssa|          null|  [3, 9, 15, 20]|
 |   Ben|           red|              []|
 +------+--------------+----------------+
 */
```

## 3. SaveMode

保存操作可以选择使用 SaveMode 来指定如何处理现有数据（如果存在）。我们需要知道这些保存模式不使用任何锁并且不是原子的。此外，执行 Overwrite，在写入新数据之前旧数据会被删除。

Scala/Java|Any Language|含义
---|---|---
SaveMode.ErrorIfExists (默认)	|error或者errorifexists (默认)	|将 DataFrame 保存到数据源, 如果数据已经存在, 将会抛出异常。
SaveMode.Append| append |将 DataFrame 保存到数据源时, 如果数据/表已存在, 那么 DataFrame 的内容将被追加到现有数据中。
SaveMode.Overwrite|	overwrite|	Overwrite 模式意味着将 DataFrame 保存到数据源时，如果数据/表已经存在，那么 DataFrame 的内容将覆盖现有数据。
SaveMode.Ignore| ignore| Ignore 模式意味着当将 DataFrame 保存到数据源时，如果数据已经存在，那么保存操作不会保存 DataFrame 的内容, 并且不更改现有数据。这与 SQL 中的 `CREATE TABLE IF NOT EXISTS` 类似。

```java
// format 指定为 json 读取的是 json 文件
Dataset<Row> usersDF = spark.read().format("json").load("spark-example-3.1/src/main/resources/data/users.json");
usersDF.show();
// 使用 SaveMode 指定保存模式
usersDF.select("name", "favorite_color").write().format("json")
        .mode(SaveMode.ErrorIfExists)
        .save("namesAndFavColors.json");
```

## 4. 保存到持久化表中

可以使用 saveAsTable 命令将 DataFrames 以持久化表保存到 Hive Metastore 中。需要注意的是使用此功能不需要部署 Hive。如果没有部署 Hive，Spark 为你创建一个默认的本地 Hive Metastore（使用 Derby ）。与 createOrReplaceTempView 命令不同，saveAsTable 命令会物化 DataFrame 的内容，并创建一个指向 Hive Metastore 中数据的指针。即使你的 Spark 程序重新启动，只要你保持连接的是同一个 Metastore，那么持久化表仍然会存在。可以通过使用表的名称在 SparkSession 上调用 table 方法来创建 DataFrame 的持久化表。

对于基于文件的数据源，例如 text、parquet、json 等，你可以通过 path 选项指定表的路径, 例如 `df.write.option("path", "/some/path").saveAsTable("t")`。当表被删除时，表路径不会被删除并且表数据仍然存在。如果未指定表路径, Spark 会把数据写入 warehouse 目录的默认表路径下。当表被删除时，默认的表路径也会被删除。

从 Spark 2.1 开始, 持久性数据源表可以在 Hive Metastore 中存储分区元数据信息。这会带来了如下几个好处:
- 由于元数据只返回查询的必要分区，因此不再需要对表的第一个查询去发现所有分区。
- Hive DDLs 如 `ALTER TABLE PARTITION ... SET LOCATION` 现在可用于使用 Datasource API 创建的表上。

> 需要注意的是创建外部数据源表(带有 path 选项)时，默认情况下不会收集分区信息。要同步 Metastore 中的分区信息, 你可以调用 `MSCK REPAIR TABLE`。

## 5. 分桶, 排序和分区

对于基于文件的数据源，也可以对输出进行分桶，排序或者分区。分桶和排序仅适用于持久化表：
```java
Dataset<Row> peopleDF = spark.read().format("json").load("spark-example-3.1/src/main/resources/data/people.json");
peopleDF.write().bucketBy(42, "name").sortBy("age").saveAsTable("people_bucketed");
```

在使用 Dataset API 时，分区(partitionBy)可以同时与 save 和 saveAsTable 一起使用：
```java
usersDF.write()
  .partitionBy("favorite_color")
  .format("parquet")
  .save("namesPartByColor.parquet");
```

可以在一个表上同时使用分区和分桶：
```java
peopleDF.write()
  .partitionBy("favorite_color")
  .bucketBy(42, "name")
  .saveAsTable("people_partitioned_bucketed");
```
partitionBy 只是创建一个目录结构。因此对基数较高的列的适用性有限。相反，bucketBy 可以在固定数量的桶中分配数据，并且可以在唯一值无限时使用数据。


原文：[Generic Load/Save Functions](https://spark.apache.org/docs/3.1.3/sql-data-sources-load-save-functions.html)
