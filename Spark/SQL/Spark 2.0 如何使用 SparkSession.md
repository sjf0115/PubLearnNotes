---
layout: post
author: sjf0115
title: Spark 2.0 如何使用 SparkSession
date: 2018-06-07 17:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-how-to-use-sparksession-in-spark-2-0
---

除了有时限的交互之外，SparkSession 提供了一个单一的入口来与底层的 Spark 功能进行交互，并允许使用 DataFrame 和 Dataset API 对 Spark 进行编程。最重要的是减少了开发人员在与 Spark 进行交互时必须了解和构造概念的数量。

在这篇文章中我们将探讨 Spark 2.0 中的 SparkSession 的功能。

### 1. 探索 SparkSession 的统一功能

首先，我们将检查 Spark 应用程序 [SparkSessionZipsExample](https://github.com/dmatrix/examples/blob/master/spark/databricks/apps/scala/2.x/src/main/scala/zips/SparkSessionZipsExample.scala)，该应用程序从 JSON 文件读取邮政编码，并使用 DataFrame API 执行一些分析，然后运行 Spark SQL 查询，而无需访问 SparkContext，SQLContext 或 HiveContext。

#### 1.1 创建SparkSession

在Spark2.0版本之前，必须创建 SparkConf 和 SparkContext 来与 Spark 进行交互，如下所示：
```scala
//set up the spark configuration and create contexts
val sparkConf = new SparkConf().setAppName("SparkSessionZipsExample").setMaster("local")
// your handle to SparkContext to access other context like SQLContext
val sc = new SparkContext(sparkConf).set("spark.some.config.option", "some-value")
val sqlContext = new org.apache.spark.sql.SQLContext(sc)
```
而在 Spark 2.0 中，通过 SparkSession 可以实现相同的效果，而不用显式创建 SparkConf，SparkContext或 SQLContext，因为它们都被封装在 SparkSession 中。使用建造者模式，实例化 SparkSession 对象（如果不存在的话）以及相关的基础上下文。
```scala
// Create a SparkSession. No need to create SparkContext
// You automatically get it as part of the SparkSession
val warehouseLocation = "file:${system:user.dir}/spark-warehouse"
val spark = SparkSession
   .builder()
   .appName("SparkSessionZipsExample")
   .config("spark.sql.warehouse.dir", warehouseLocation)
   .enableHiveSupport()
   .getOrCreate()
```
到这个时候，你可以在 Spark 作业期间通过 `spark` 这个变量（作为实例对象）访问其公共方法和实例。

#### 1.2 配置Spark的运行时属性

一旦 SparkSession 被实例化，你就可以配置 Spark 的运行时配置属性。例如，在下面这段代码中，我们可以改变已经存在的运行时配置选项。configMap 是一个集合，你可以使用 Scala 的 iterable 方法来访问数据。
```scala
//set new runtime options
spark.conf.set("spark.sql.shuffle.partitions", 6)
spark.conf.set("spark.executor.memory", "2g")
//get all settings
val configMap:Map[String, String] = spark.conf.getAll()
```
#### 1.3 访问Catalog元数据

通常，你可能需要访问和浏览底层的目录元数据。SparkSession 将 catalog 作为一个公开的公共实例，该实例包含可以操作该元数据的方法。这些方法以 DataSets 形式返回，因此可以使用 DataSets API 访问或查看数据。在下面代码中，我们访问所有的表和数据库。
```scala
//fetch metadata data from the catalog
spark.catalog.listDatabases.show(false)
spark.catalog.listTables.show(false)
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-use-sparksession-in-spark-2-0-1.png?raw=true)

#### 1.4 创建DataSets和DataFrame

使用 SparkSession API 创建 DataSets 和 DataFrame 方法有许多。

快速生成 DataSets 的一种方法是使用 `spark.range` 方法。在学习如何操作 DataSets API 时，这种方法非常有用。
```scala
//create a Dataset using spark.range starting from 5 to 100, with increments of 5
val numDS = spark.range(5, 100, 5)
// reverse the order and display first 5 items
numDS.orderBy(desc("id")).show(5)
//compute descriptive stats and display them
numDs.describe().show()
// create a DataFrame using spark.createDataFrame from a List or Seq
val langPercentDF = spark.createDataFrame(List(("Scala", 35), ("Python", 30), ("R", 15), ("Java", 20)))
//rename the columns
val lpDF = langPercentDF.withColumnRenamed("_1", "language").withColumnRenamed("_2", "percent")
//order the DataFrame in descending order of percentage
lpDF.orderBy(desc("percent")).show(false)
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-use-sparksession-in-spark-2-0-2.png?raw=true)

#### 1.5 使用SparkSession API读取JSON数据

和任何Scala对象一样，你可以使用 spark，SparkSession 对象来访问其公共方法和实例字段。我可以读取 JSON 或 CVS 或 TXT 文件，或者我可以读取 parquet 表。例如，在下面这段代码中，我们将读取一个邮政编码的 JSON 文件，该文件返回一个 DataFrame，Rows的集合。
```scala
// read the json file and create the dataframe
val jsonFile = args(0)
val zipsDF = spark.read.json(jsonFile)
//filter all cities whose population > 40K
zipsDF.filter(zipsDF.col("pop") > 40000).show(10)
```

#### 1.6 在SparkSession中使用Spark SQL

通过 SparkSession，你可以像通过 SQLContext 一样访问所有 Spark SQL 功能。在下面的代码示例中，我们创建了一个表，并在其上运行 SQL 查询。
```scala
// Now create an SQL table and issue SQL queries against it without
// using the sqlContext but through the SparkSession object.
// Creates a temporary view of the DataFrame
zipsDF.createOrReplaceTempView("zips_table")
zipsDF.cache()
val resultsDF = spark.sql("SELECT city, pop, state, zip FROM zips_table")
resultsDF.show(10)
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-use-sparksession-in-spark-2-0-3.png?raw=true)

#### 1.7 使用SparkSession保存和读取Hive表

接下来，我们将创建一个 Hive 表，并使用 SparkSession 对象对其进行查询，就像使用 HiveContext 一样。
```scala
//drop the table if exists to get around existing table error
spark.sql("DROP TABLE IF EXISTS zips_hive_table")
//save as a hive table
spark.table("zips_table").write.saveAsTable("zips_hive_table")
//make a similar query against the hive table
val resultsHiveDF = spark.sql("SELECT city, pop, state, zip FROM zips_hive_table WHERE pop > 40000")
resultsHiveDF.show(10)
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-use-sparksession-in-spark-2-0-4.png?raw=true)

正如你所看到的，输出中的结果通过使用 DataFrame API，Spark SQL和Hive查询运行完全相同。其次，让我们把注意力转向 SparkSession 自动为你创建的两个Spark开发人员环境。

### 2. SparkSession封装SparkContext

最后，对于历史上下文，让我们简单了解一下 SparkContext 的底层功能。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-use-sparksession-in-spark-2-0-5.png?raw=true)

如图所示，SparkContext 是一个访问 Spark 所有功能的入口；每个 JVM 仅存在一个 SparkContext。Spark Driver 使用它连接到集群管理器进行通信，提交 Spark 作业并知道要与之通信的资源管理器（YARN，Mesos或Standalone）。它允许你配置 Spark 参数。通过 SparkContext，Driver 可以访问其他上下文，如SQLContext，HiveContext和 StreamingContext 来编程Spark。

但是，在 Spark 2.0，SparkSession 可以通过单一统一的入口访问前面提到的所有 Spark 功能。除了使访问 DataFrame 和 Dataset API 更简单外，它还包含底层的上下文以操作数据。

以前通过 SparkContext，SQLContext 或 HiveContext 在早期版本的 Spark 中提供的所有功能现在均可通过 SparkSession 获得。从本质上讲，SparkSession 是一个统一的入口，用 Spark 处理数据，最大限度地减少要记住或构建的概念数量。因此，如果你使用更少的编程结构，你更可能犯的错误更少，并且你的代码可能不那么混乱。

原文：https://databricks.com/blog/2016/08/15/how-to-use-sparksession-in-apache-spark-2-0.html
