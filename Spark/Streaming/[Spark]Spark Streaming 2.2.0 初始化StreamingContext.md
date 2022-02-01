---
layout: post
author: sjf0115
title: Spark Streaming 2.2.0 初始化StreamingContext
date: 2018-04-03 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-initializing-streamingcontext
---

为了初始化 Spark Streaming 程序，必须创建一个 StreamingContext 对象，它是 Spark Streaming 所有流操作的主要入口。StreamingContext 对象可以用 SparkConf 对象创建。

可以使用SparkConf对象创建JavaStreamingContext对象（对于Scala和Python语言来说，创建 StreamingContext对象）：

Java版本:
```java
SparkConf conf = new SparkConf().setAppName(appName).setMaster(master);
JavaStreamingContext jsc = new JavaStreamingContext(conf, Durations.seconds(seconds));
```
Scala版本:
```scala
import org.apache.spark._
import org.apache.spark.streaming._

val conf = new SparkConf().setAppName(appName).setMaster(master)
val ssc = new StreamingContext(conf, Seconds(1))
```
Python:
```python
from pyspark import SparkContext
from pyspark.streaming import StreamingContext

sc = SparkContext(master, appName)
ssc = StreamingContext(sc, 1)
```

appName 参数是应用程序在集群UI上显示的名称。master 是Spark，Mesos或YARN集群URL，或者是以本地模式运行的特殊字符串`local [*]`。

实际上，当在集群上运行时，如果你不想在程序中硬编码 master(即在程序中写死)，而是希望使用 spark-submit 启动应用程序时得到 master 的值。对于本地测试和单元测试，你可以传递 `local [*]` 来运行 Spark Streaming 进程。注意，这里内部创建的 JavaSparkContext（所有Spark功能的起始点），可以通过 jsc.sparkContext 访问。

JavaStreamingContext对象也可以从现有的JavaSparkContext创建。对于Scala来说，StreamingContext对象也可以从现有的 SparkContext 创建：

Java版本:
```java
SparkConf conf = new SparkConf().setAppName("socket-spark-stream").setMaster("local[2]");

JavaSparkContext sparkContext = new JavaSparkContext(conf);
JavaStreamingContext jsc = new JavaStreamingContext(sparkContext, Durations.seconds(seconds));
```
Scala版本:
```scala
import org.apache.spark.streaming._

val sc = ...                // existing SparkContext
val ssc = new StreamingContext(sc, Seconds(1))
```

批处理间隔必须根据应用程序和可用群集资源的延迟要求进行设置。 有关更多详细信息，请参阅“性能调优”部分。

定义上下文后，您必须执行以下操作：
- 通过创建输入DStreams定义输入源
- 通过对DStreams应用转换操作（transformation）和输出操作（output）来定义流计算
- 可以使用streamingContext.start()方法接收和处理数据
- 可以使用streamingContext.awaitTermination()方法等待流计算完成（手动或由于任何错误），来防止应用退出
- 可以使用streamingContext.stop（）手动停止处理。

注意点:
- 一旦上下文已经开始，则不能设置或添加新的流计算。
- 上下文停止后，无法重新启动。
- 在同一时间只有一个StreamingContext可以在JVM中处于活动状态。
- 在StreamingContext上调用stop()方法，也会关闭SparkContext对象。如果只想关闭StreamingContext对象，设置stop()的可选参数为false。
- 一个SparkContext可以重复利用创建多个StreamingContext，只要在创建下一个StreamingContext之前停止前一个StreamingContext（而不停止SparkContext）即可。


> Spark Streaming 版本: 2.2.0

原文：http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#initializing-streamingcontext
