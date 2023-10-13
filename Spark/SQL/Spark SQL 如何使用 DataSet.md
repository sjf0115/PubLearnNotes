---
layout: post
author: sjf0115
title: Spark 如何使用 DataSets
date: 2018-06-03 15:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-how-to-use-datasets-in-spark
---

开发人员一直非常喜欢 Apache Spark，因为它可以提供简单且功能强大的 API，这些特性的组合可以用最少的代码实现复杂的分析。我们通过引入 DataFrames 和 Spark SQL 继续推动 Spark 的可用性和性能。这些是用于处理结构化数据（例如数据库表，JSON文件）的高级 API，这些 API 可让 Spark 自动优化存储和计算。在这些 API 背后，Catalyst 优化器和 Tungsten 执行引擎用 Spark 面向对象（RDD）API 无法实现的方式优化应用程序，例如以原始二进制形式对数据进行操作。

Spark Datasets 是 DataFrame API 的扩展，提供了一个类型安全的，面向对象的编程接口。Spark 1.6 包含 DataSets 的 API 预览版，它们将成为下几个 Spark 版本的开发重点。与 DataFrame 一样，DataSets 通过将表达式和数据字段公开给查询计划器(query planner)来充分利用 Spark 的 Catalyst 优化器。DataSets 还充分利用了 Tungsten 的快速内存编码。DataSets 继承了编译时类型安全性的好处 - 这意味着线上应用程序可以在运行之前检查错误。它们还允许直接对用户自定义的类操作。

从长远来看，我们期望 DataSets 成为编写更高效 Spark 应用程序的强大方式。DataSets 可以与现有的 RDD API 一起使用，但是当数据可以用结构化的形式表示时，可以提高效率。Spark 1.6 首次提出了 Datasets，我们期望在未来的版本中改进它们。

### 1. 使用Datasets

Datasets 是一种强类型，不可变的可以映射到关系性 schema 的对象集合。Datasets API 的核心是一个称为 Encoder 的新概念，它负责在 JVM 对象和表格表示(tabular representation)之间进行转换。表格表示使用 Spark 的内部 Tungsten 二进制格式存储，允许对序列化数据进行操作并提高内存利用率。Spark 1.6 支持自动生成各种类型的 Encoder，包括原始类型（例如String，Integer，Long），Scala Case 类和Java Beans。

使用 RDD 的用户会发现 Dataset API 非常熟悉，因为它提供了许多相同的功能转换（例如map，flatMap，filter）。考虑下面的代码，该代码读取文本文件的行并将它们拆分为单词：
```scala
# RDD
val lines = sc.textFile("/wikipedia")
val words = lines
  .flatMap(_.split(" "))
  .filter(_ != "")

# Datasets
val lines = sqlContext.read.text("/wikipedia").as[String]
val words = lines
  .flatMap(_.split(" "))
  .filter(_ != "")
```
> Spark2.0以上版本，sqlContext 可以使用 SparkSeesion 替换。具体细节请参阅[Spark SparkSession:一个新的入口](http://smartsi.club/2018/06/07/spark-sql-sparksession-new-entry-point/)

这两种API都可以很容易地使用lambda函数表达转换操作。编译器和IDE懂得你正在使用的类型，并且可以在你构建数据管道时提供有用的提示和错误信息。

虽然这个高层次代码在语法上看起来类似，但使用 Datasets，你也可以访问完整关系执行引擎的所有功能。例如，如果你现在要执行聚合（例如计算每个词的出现次数），则可以简单有效地表达该操作，如下所示：
```scala
# RDDs
val counts = words
  .groupBy(_.toLowerCase)
  .map(w => (w._1, w._2.size))

# Datasets
val counts = words
  .groupBy(_.toLowerCase)
  .count()
```
由于 Datasets 版本的 WordCount 可以充分利用内置的聚合计数，所以这种计算不仅可以用较少的代码表示，而且还可以更快地执行。正如你在下面的图表中看到的那样，Datasets 的实现比原始的 RDD 实现要快得多。相反，使用 RDD 获得相同的性能需要用户手动考虑如何以最佳并行化方式表达计算。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-use-datasets-in-spark-1.png?raw=true)

这个新的 Datasets API 的另一个好处是减少了内存使用量。由于 Spark 了解 Datasets 中数据的结构，因此可以在缓存 Datasets 时在内存中创建更优化的布局。在下面的例子中，我们对比使用 Datasets 和 RDD 来在内存中缓存几百万个字符串。在这两种情况下，缓存数据都可以显着提高后续查询的性能。但是，由于 Datasets Encoder 向 Spark 提供有关正在存储数据的更多信息，因此优化后缓存会减少 4.5x 的空间。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-use-datasets-in-spark-2.png?raw=true)

### 2. 使用Encoder进行快速序列化

Encoder 经过高度优化，并使用运行时代码生成来构建用于序列化和反序列化的自定义字节码(use runtime code generation to build custom bytecode for serialization and deserialization)。因此，它们可以比 Java 或 Kryo 序列化更快地运行。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-use-datasets-in-spark-3.png?raw=true)

除了速度之外，由此产生的编码数据的序列化大小也明显更小（高达2倍），从而降低了网络传输的成本。此外，序列化的数据已经是　Tungsten　二进制格式，这意味着许多操作可以在原地完成，而不需要物化一个对象。Spark内置支持自动生成原始类型（如String，Integer，Long），Scala Case 类和 Java Beans 的 Encoder。

### 3. 无缝支持半结构化数据

Encoder 的功能不仅仅在性能方面。它们还可以作为半结构化格式（例如JSON）和类型安全语言（如Java和Scala）之间的桥梁。例如，考虑以下有关大学的数据集：
```
{"name": "UC Berkeley", "yearFounded": 1868, numStudents: 37581}
{"name": "MIT", "yearFounded": 1860, numStudents: 11318}
…
```
你可以简单地定义一个具有预期结构的类并将输入数据映射到它，而不是手动提取字段并将其转换为所需类型。列按名称自动排列，并保留类型。
```scala
case class University(name: String, numStudents: Long, yearFounded: Long)

val schools = sqlContext.read.json("/schools.json").as[University]

schools.map(s => s"${s.name} is ${2015 – s.yearFounded} years old")
```
Encoder 检查你的数据与预期的模式是否匹配，在尝试错误地处理TB大小数据之前提供有用的错误消息。例如，如果我们尝试使用太小的数据类型，例如转换为对象会导致截断（即numStudents大于一个字节，最大值为255），分析器将发出AnalysisException。
```scala
case class University(numStudents: Byte)
val schools = sqlContext.read.json("/schools.json").as[University]
org.apache.spark.sql.AnalysisException: Cannot upcast yearFounded from bigint to smallint as it may truncate
```
执行映射时，Encoder 自动处理复杂类型，包括嵌套类，数组和 map。

### 4. Java和Scala统一API

DataSets API 的另一个目标是提供可在 Scala 和 Java 中使用的统一接口。这种统一对于 Java 用户来说是个好消息，因为它确保了他们的API不会落后于 Scala 接口，代码示例可以很容易地在两种语言中使用，而库不再需要处理两种稍微不同的输入类型。Java 用户唯一的区别是他们需要指定要使用的 Encoder，因为编译器不提供类型信息。 例如，如果想要使用Java处理json数据，你可以这样做：
```java
public class University implements Serializable {
    private String name;
    private long numStudents;
    private long yearFounded;

    public void setName(String name) {...}
    public String getName() {...}
    public void setNumStudents(long numStudents) {...}
    public long getNumStudents() {...}
    public void setYearFounded(long yearFounded) {...}
    public long getYearFounded() {...}
}

class BuildString implements MapFunction {
    public String call(University u) throws Exception {
        return u.getName() + " is " + (2015 - u.getYearFounded()) + " years old.";
    }
}

Dataset schools = context.read().json("/schools.json").as(Encoders.bean(University.class));
Dataset strings = schools.map(new BuildString(), Encoders.STRING());
```


原文：https://databricks.com/blog/2016/01/04/introducing-apache-spark-datasets.html
