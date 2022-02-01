---
layout: post
author: sjf0115
title: Spark SparkSession:一个新的入口
date: 2018-06-07 17:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-sparksession-new-entry-point
---

在 Spark 1.x 中，使用 HiveContext 作为 DataFrame API 的入口显得并不直观。在 Spark 2.0 引入 SparkSession 作为一个新的入口，并且包含 SQLContext 和 HiveContext 的特性，同时为了向后兼容，两者都保留下来。SparkSession 有很多特性，在这里我们展示一些更重要的特性。

### 1. 创建SparkSession

SparkSession 可以使用建造者模式创建。如果 SparkContext 存在，那么 SparkSession 将会重用它，但是如果不存在就会创建一个 SparkContext。在I/O期间，在 builder 中设置的配置选项会自动传递给 Spark 和 Hadoop。

Java版本：
```java
SparkSession sparkSession = SparkSession
  .builder()
  .master("local[2]")
  .appName("SparkSession Example")
  .config("spark.some.config.option", "config-value")
  .getOrCreate();
```
Scala版本：
```scala
import org.apache.spark.sql.SparkSession
val sparkSession = SparkSession.builder
  .master("local[2]")
  .appName("SparkSession Example")
  .config("spark.some.config.option", "config-value")
  .getOrCreate()

import org.apache.spark.sql.SparkSession
sparkSession: org.apache.spark.sql.SparkSession = org.apache.spark.sql.SparkSession@46d6b87c
```

### 2. 统一读取数据的入口

SparkSession 是读取数据的入口，类似于旧的 SQLContext.read。

Java版本:
```java
Dataset<Row> dataFrame = sparkSession.read().json("src/main/resources/person.json");
```
Scala版本:
```scala
val jsonData = sparkSession.read.json("src/main/resources/person.json")
jsonData: org.apache.spark.sql.DataFrame = [email: string, iq: bigint ... 1 more field]
```
输出:
```
display(jsonData)
```
email|iq|name
---|---|---
matei@databricks.com|180|Matei Zaharia
rxin@databricks.com|80|Reynold Xin

### 3. 运行SQL查询

SparkSession 可以在数据上执行SQL查询，结果以 DataFrame 形式返回（即DataSet[Row]）。
```
display(spark.sql("select * from person"))
```

email|iq|name
---|---|---
matei@databricks.com|180|Matei Zaharia
rxin@databricks.com|80|Reynold Xin

### 4. 使用配置选项

SparkSession 还可以用来设置运行时配置选项，这些选项可以触发性能优化或I/O（即Hadoop）行为。
```
spark.conf.set("spark.some.config", "abcd")
res12: org.apache.spark.sql.RuntimeConfig = org.apache.spark.sql.RuntimeConfig@55d93752

spark.conf.get("spark.some.config")
res13: String = abcd
```
配置选项也可以在 SQL 中使用变量替换：
```
%sql select "${spark.some.config}"
abcd
```
### 5. 直接使用元数据

SparkSession还包含一个 catalog 方法，该方法包含操作 Metastore（即数据目录）的方法。这些方法以 Datasets 形式返回结果，所以你可以在它们上面使用相同的 Datasets API。
```
// To get a list of tables in the current database
val tables = spark.catalog.listTables()
tables: org.apache.spark.sql.Dataset[org.apache.spark.sql.catalog.Table] = [name: string, database: string ... 3 more fields]
```
输出:
```
display(tables)
```
name|database|description|tableType|isTemporary
---|---|---|---|---
person|default|null|MANAGED|false
smart|default|null|MANAGED|false

```
// Use the Dataset API to filter on names
display(tables.filter(_.name contains "son"))
```
name|database|description|tableType|isTemporary
---|---|---|---|---
person|default|null|MANAGED|false

```
// Get the list of columns for a table
display(spark.catalog.listColumns("smart"))
```
name|description|dataType|nullable|isPartition|isBucket
---|---|---|---|---|---
email|null|string|true|false|false
iq|null|bigint|true|false|false
name|null|string|true|false|false

### 6. 访问底层的SparkContext

SparkSession.sparkContext 返回底层的 SparkContext，用于创建 RDD 以及管理集群资源。
```
spark.sparkContext
res17: org.apache.spark.SparkContext = org.apache.spark.SparkContext@2debe9ac
```

原文：https://docs.databricks.com/_static/notebooks/sparksession.html
