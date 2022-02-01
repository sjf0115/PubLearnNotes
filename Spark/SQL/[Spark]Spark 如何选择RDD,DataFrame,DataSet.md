---
layout: post
author: sjf0115
title: Spark 如何选择RDD,DataFrame,DataSet
date: 2018-06-03 15:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-how-to-select-rdds-dataframes-and-datasets
---

Apache Spark 对开发人员的吸引力之一是其易于使用的 API，适用于跨语言的大型数据集：Scala，Java，Python和R。在本博客中，我将探索 Apache Spark 2.2 及更高版本中提供的三套 API- RDD，DataFrame和Datasets；为什么和什么时候使用哪套API；概述其性能和优化效益；并列举何时使用 DataFrames 和 Datasets 而不是 RDD 的场景。大多数情况下，我将关注 DataFrame 和 Datasets，因为在Apache Spark 2.0中，这两个API是统一的。

这次整合背后的动机在于我们希望可以让使用 Spark 变得更简单，方法就是减少你需要掌握的概念的数量，以及提供处理结构化数据的办法。在处理结构化数据时，Spark 可以像针对特定领域的语言所提供的能力一样，提供高级抽象和 API。

### 1. RDD

从一开始 RDD 就是 Spark 面向用户的主要API。RDD 是数据元素的不可变分布式集合，分布在集群中的节点上，可以通过若干提供了 transformations 和 actions 的底层 API 进行并行处理。

#### 1.1 什么时候使用RDD

下面是使用RDD的常用场景和用例：
- 你需要对你的数据集进行低层次的 transformations 与 actions操作和控制时;
- 你的数据是非结构化的，例如媒体流或文本流;
- 你想通过函数式编程来处理你的数据，而不是特定领域内的表达式;
- 你通过名称或列来处理或访问数据属性时并不关心是否指定schema;
- 你可以放弃 DataFrame 和 Datasets 对结构化和半结构化数据的处理所带来的优化和性能优势。

#### 1.2 Spark 2.0中的RDD会发生什么

你可能会问：RDD是否被降级为二等公民？ 他们是否被弃用？答案是否！更重要的是，你可以在下面注意到，你可以通过简单的API方法调用，随意在 DataFrame 或 Dataset 与 RDD 之间进行无缝转换 - DataFrame 和 Datasets 建立在RDD之上。

### 2. DataFrames

像 RDD 一样，DataFrame 是一个不可变的分布式数据集合。与 RDD 不同，数据被组织到命名列中，就像关系数据库中的表一样。DataFrame 旨在使大型数据集的处理更加容易，允许开发人员将结构强加到分布式数据集上，从而实现更高级别的抽象; 它提供了一个特定于领域的语言API来操纵分布式数据; 并使Spark有更广泛的受众群体，而不仅仅是专业的数据工程师。

我们提到在 Spark 2.0 中，DataFrame API 将与 Datasets API 合并，实现跨库的数据处理功能的统一。由于这种统一，开发人员现在只需要记忆更少的概念，并且只需要使用一个名为 Dataset 的高级和类型安全的API。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-select-rdds-dataframes-and-datasets-1.png?raw=true)

### 3. Dataset

从 Spark 2.0 开始，Dataset 具有两种截然不同的API特性：强类型API和无类型API，如下表所示。从概念上讲，将 DataFrame 视为通用对象集合 Dataset[Row] 的别名，其中 Row 是通用的无类型的 JVM 对象。相比之下，DataSet 是强类型 JVM 对象(Scala 中定义的 Case 类或 Java 中的类)的集合。

#### 3.1 有类型和无类型的API


Language|Main Abstraction
---|---
Scala	|Dataset[T] & DataFrame (alias for Dataset[Row])
Java	|Dataset[T]
Python*	|DataFrame
R*	|DataFrame

> 由于Python和R没有编译时类型安全，因此我们只有无类型的API，即DataFrame。

### 4. DataSet API的优势

在 Spark 2.0 里，DataFrame 和 Dataset 的统一 API 会为 Spark 开发者们带来许多方面的好处。

#### 4.1 静态类型和运行时类型安全

从 SQL 的最小约束到 Dataset 的最严格约束，把静态类型和运行时安全想像成一个图谱。例如，在你的 Spark SQL 字符串查询中，直到运行时才会发现语法错误（这样代价比较高），而在 DataFrame 和 Datasets 中，你在编译时就可以捕获错误（这样节省了开发人员时间和成本）。也就是说，如果你在 DataFrame 中调用API之外的函数，编译器会捕获它，发现这个错误。但是，如果你使用了一个不存在的列名，那就要到运行时才能发现错误了。

图谱的另一端是最严格的 Dataset。由于 DataSet API 都用 lambda 函数和 JVM 类型对象表示，因此在编译时会检测到不匹配的类型参数。此外，在使用 DataSet 时，也可以在编译时检测到你的分析错误，从而节省开发人员时间和成本。

所有的这些转换都被解释成关于类型安全的图谱，内容就是你的 Spark 代码里的语法和分析错误。Dataset 是最具有严格约束的，却是对于开发者来说最具有效率的。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-select-rdds-dataframes-and-datasets-2.png?raw=true)

#### 4.2 对结构化和半结构化数据进行高级抽象和自定义视图

DataFrame 作为 DataSet[Row] 的集合，可以为你的半结构化数据呈现结构化的自定义视图。例如，假设你拥有一个巨大的物联网设备事件数据集，用 JSON 格式表示。由于 JSON 是一种半结构化格式，因此它非常适合将 DataSet 作为强类型 DataSet[DeviceIoTData] 的集合。
```
{"device_id": 198164, "device_name": "sensor-pad-198164owomcJZ", "ip": "80.55.20.25", "cca2": "PL", "cca3": "POL", "cn": "Poland", "latitude": 53.080000, "longitude": 18.620000, "scale": "Celsius", "temp": 21, "humidity": 65, "battery_level": 8, "c02_level": 1408, "lcd": "red", "timestamp" :1458081226051}
```
你可以使用 Scala Case 类将每个 JSON 条目表示为 DeviceIoTData（一个自定义对象）。
```scala
case class DeviceIoTData (battery_level: Long, c02_level: Long, cca2: String, cca3: String, cn: String, device_id: Long, device_name: String, humidity: Long, ip: String, latitude: Double, lcd: String, longitude: Double, scale:String, temp: Long, timestamp: Long)
```
接下来，我们可以从JSON文件读取数据。
```scala
// read the json file and create the dataset from the
// case class DeviceIoTData
// ds is now a collection of JVM Scala objects DeviceIoTData
val ds = spark.read.json(“/databricks-public-datasets/data/iot/iot_devices.json”).as[DeviceIoTData]
```
在上面的代码中发生了三件事情：
- Spark 读取 JSON，根据模式推断并创建一组 DataFrame。
- 此时，Spark 会将数据转换为 `DataFrame = Dataset [Row]`，这是一个通用 Row 对象的集合，因为它不知道确切的类型。
- 现在，按照 DeviceIoTData 类的定义，Spark 按照 `DataSet[Row] -> Dataset[DeviceIoTData]` 的转换，转换出类型特定的 Scala JVM 对象。

我们大多数人都用过结构化数据，习惯于以列式方式查看和处理数据或访问对象内的特定属性。将 Dataset 作为 Dataset [ElementType] 有类型对象的集合，你可以很容易地获得强类型 JVM 对象的编译时安全性和自定义视图。从上面的代码中得到的强类型 DataSet[T] 可以很容易地用高级方法显示或处理。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-select-rdds-dataframes-and-datasets-3.png?raw=true)

#### 4.3 易于使用结构化的API

虽然结构化可能会限制 Spark 程序对数据的控制，但它却引入了丰富的语义和一组简单的特定领域内的操作，这些操作可以表示为高级结构。大部分计算都可以使用 Dataset 的高级 API 来完成。例如，通过访问 Dataset 有类型对象的 DeviceIoTData，比使用 RDD 行的数据字段执行 agg，select，sum，avg，map，filter 或 groupBy 操作要简单得多。

用特定领域内 API 表达你的计算远比关系代数类型表达式（在RDD中）简单和容易。例如，下面的代码用　filter（）　和　map（）　创建另一个不可变的 Dataset。
```scala
// Use filter(), map(), groupBy() country, and compute avg()
// for temperatures and humidity. This operation results in
// another immutable Dataset. The query is simpler to read,
// and expressive

val dsAvgTmp = ds.filter(d => {d.temp > 25}).map(d => (d.temp, d.humidity, d.cca3)).groupBy($"_3").avg()

//display the resulting dataset
display(dsAvgTmp)
```

#### 4.4 性能和优化

除了所有上述优点外，你不能忽视使用 DataFrame 和 Dataset API 时所带来的空间效率和性能提升。原因如下：

首先，由于 DataFrame 和 Dataset API 构建在 Spark SQL 引擎之上，因此它使用 Catalyst 来生成优化的逻辑和物理查询计划。 在 R，Java，Scala 或 Python DataFrame / Dataset API 中，所有关系类型查询都使用相同的代码优化器，提供空间和速度效率。 DataSet[T] 有类型的 API 针对数据工程任务进行了优化，但无类型的 DataSet[Row]（DataFrame的别名）却更快，更适用于交互式分析。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-select-rdds-dataframes-and-datasets-4.png?raw=true)

其次，Spark 作为一个编译器，它理解 Dataset 类型的 JVM 对象，因此它使用 Encoders 将特定于类型的 JVM 对象映射到 Tungsten 的内部的内存表示。因此，Tungsten Encoders 可以高效地对 JVM 对象进行序列化/反序列化，并生成压缩的字节码，这样执行效率就非常高了。

#### 4.5 什么时候使用DataFrame或Dataset

- 如果你需要丰富的语义、高级抽象和特定领域专用的 API，那就使用 DataFrame 或 Dataset；
- 如果你的处理需要对半结构化数据进行高级处理，如 filter、map、aggregation、average、sum、SQL 查询、列式访问或对半结构化数据使用 lambda 函数，那就使用 DataFrame 或 Dataset；
- 如果你想在编译时具有更高的类型安全，想要有类型的 JVM 对象，使用 Catalyst 优化，并从 Tungsten 高效的代码生成中获益，那就使用 Dataset；
- 如果你想在不同的 Spark 库之间使用一致和简化的 API，那就使用 DataFrame 或 Dataset；
- 如果你是 R 语言使用者，就用 DataFrame；
- 如果你是 Python 语言使用者，就用 DataFrame，在需要更细致的控制时则使用 RDD；

请注意，通过简单的调用 `.rdd` 方法，你可以轻松地将 DataFrame 和 Dataset 与 RDD 进行转换。例如，
```scala
// select specific fields from the Dataset, apply a predicate
// using the where() method, convert to an RDD, and show first 10
// RDD rows
val deviceEventsDS = ds.select($"device_name", $"cca3", $"c02_level").where($"c02_level" > 1300)
// convert to RDDs and take the first 10 rows
val eventsRDD = deviceEventsDS.rdd.take(10)
```

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-sql-how-to-select-rdds-dataframes-and-datasets-5.png?raw=true)

### 5. 整合在一起

总之，何时使用 RDD，DataFrame 或 DataSet 看起来很明显。前者为你提供低级别的函数和控制，后者则允许自定义视图和结构，提供高级别和特定领域的操作，节省空间并以更快的速度运行。

在我们回顾从早期版本的 Spark 中学到的经验之后，我们如何为开发人员简化 Spark，如何优化并提高性能 - 我们决定将低级 RDD API 提升为高级抽象，如 DataFrame 和 Dataset，并且在 Catalyst 优化器和 Tungsten 之上构建这种统一的数据抽象。

从 DataFrames 或 Dataset 或 RDDs API 选择一个可以满足你需求一个即可，当你像大多数开发者一样对数据进行结构化或半结构化的处理时，我不会有丝毫惊讶。

原文：https://databricks.com/blog/2016/07/14/a-tale-of-three-apache-spark-apis-rdds-dataframes-and-datasets.html
