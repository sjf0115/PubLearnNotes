---
layout: post
author: sjf0115
title: Spark 入门 弹性分布式数据集(RDD)
date: 2018-03-12 19:13:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-build-resilient-distributed-datasets
---

> Spark版本: 3.1.3

Spark 的核心概念是弹性分布式数据集（RDD），RDD 是一个可容错、并行操作的分布式元素集合。有两种方法可以创建 RDD 对象：
- 在 Driver 中并行化操作已存在集合来创建 RDD
- 从外部存储系统中引用数据集（如：共享文件系统、HDFS、HBase 或者其他 Hadoop 支持的数据源）。

### 1. 并行化集合

在你 Driver 的现有集合上调用 `JavaSparkContext` 的 `parallelize` 方法创建并行化集合(Parallelized collections)。集合的元素被复制来创建可以并行操作的分布式数据集。下面展示了如何创建一个包含数字 1 到 5 的并行化集合：
```java
// 1. Java 版本
List<Integer> list = Arrays.asList(1,2,3,4,5);
JavaRDD<Integer> rdd = sc.parallelize(list);

// 2. Scala 版本
val data = Array(1, 2, 3, 4, 5)
val distData = sc.parallelize(data)
```

RDD 一旦创建，分布式数据集（distData）就可以并行操作。例如，我们可以调用 `distData.reduce((a, b) -> a + b)` 来实现对列表元素求和。后面文章中我们会介绍分布式数据集的具体操作。

并行化集合的一个重要参数是分区个数(将数据集分割成多少个分区)。Spark 集群中每个分区可以运行一个任务(Task)。典型场景下，一般为每个 CPU 分配 2－4 个分区。但通常而言，Spark 会根据你集群的情况，自动设置分区数。当然，你可以给 `parallelize` 方法传递第二个参数来手动设置分区数（如：`sc.parallelize(data, 10)`）。

> Spark代码里有些地方仍然使用分片（slice）这个术语(分区的同义词)，主要为了保持向后兼容。

### 2. 外部数据集

Spark 可以从 Hadoop 支持的任何存储数据源创建分布式数据集，包括本地文件系统，HDFS，Cassandra，HBase，Amazon S3等。Spark 也支持文本文件，SequenceFiles 以及任何其他 Hadoop InputFormat。

文本文件 RDD 可以使用 `SparkContext` 的 `textFile` 方法创建。该方法根据 URL 获取文件（机器的本地路径，或 `hdfs://` ，`s3n://` 等等），并按行读取。下面是一个示例调用：
```java
// 1. Java 版本
JavaRDD<String> distFile = sc.textFile("data.txt");
// 2. Scala 版本
scala> val distFile = sc.textFile("data.txt")
distFile: org.apache.spark.rdd.RDD[String] = data.txt MapPartitionsRDD[10] at textFile at <console>:26
```

一旦创建完成，就可以在 distFiile 上做数据集操作。例如，我们可以用下面的方式使用 map 和 reduce 操作将所有行的长度相加：
```java
distFile.map(s -> s.length()).reduce((a, b) -> a + b);
```

需要注意的是 Spark 读文件的一些注意事项：
- 如果使用本地文件系统路径，在所有 Worker 节点上该文件必须都能用相同的路径访问到。要么能复制文件到所有的 Worker 节点，要么能使用网络的方式共享文件系统。
- Spark 所有基于文件的输入方法，包括 `textFile`，能很好地支持文件目录，压缩文件和通配符。例如，你可以使用:
```java
textFile("/my/directory")
textFile("/my/directory/*.txt")
textFile("/my/directory/*.gz")
```
- `textFile` 方法也可以选择第二个可选参数来控制文件分区数目。默认情况下，Spark 为每一个文件块创建一个分区（HDFS中分块大小默认为128MB），你也可以通过传递一个较大数值来请求更多分区。注意的是，分区数目不能少于分块数目。

除了文本文件，Spark 的 Java API 还支持其他几种数据格式：
-  `JavaSparkContext.wholeTextFiles` 可以读取包含多个小文本文件的目录，并将它们以（文件名，内容）键值对返回。这与 textFile 相反，textFile 将在每个文件中每行返回一条记录。
```java
JavaPairRDD<String, String> rdd = sc.wholeTextFiles("/home/xiaosi/wholeText");
List<Tuple2<String, String>> list = rdd.collect();
for (Tuple2<?, ?> tuple : list) {
    System.out.println(tuple._1() + ": " + tuple._2());
}
```
- 对于 SequenceFiles，可以使用 SparkContext 的 `sequenceFile[K，V]` 方法，其中 K 和 V 是文件中的键和值的类型。这些应该是 Hadoop 的 Writable 接口的子类，如 IntWritable 和 Text。
- 对于其他 Hadoop InputFormats，你可以使用 `JavaSparkContext.hadoopRDD` 方法，该方法采用任意 JobConf 和输入格式类，键类和值类。将这些设置与使用输入源的 Hadoop 作业相同。你还可以使用基于“新” MapReduce API（org.apache.hadoop.mapreduce）的 InputFormats 的 `JavaSparkContext.newAPIHadoopRDD`。
- `JavaRDD.saveAsObjectFile` 和 `SparkContext.objectFile` 支持保存一个 RDD，保存格式是一个简单的 Java 对象序列化格式。这是一种效率不高的专有格式，如 Avro，它提供了简单的方法来保存任何一个 RDD。


原文：[Resilient Distributed Datasets (RDDs)](https://spark.apache.org/docs/3.1.3/rdd-programming-guide.html#resilient-distributed-datasets-rdds)
