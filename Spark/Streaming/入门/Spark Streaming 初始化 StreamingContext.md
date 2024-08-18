---
layout: post
author: sjf0115
title: Spark Streaming 初始化 StreamingContext
date: 2018-04-03 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-initializing-streamingcontext
---

> Spark Streaming 版本: 3.1.3

为了初始化 Spark Streaming 程序，必须创建一个 StreamingContext 对象，它是 Spark Streaming 所有流操作的主要入口。StreamingContext 对象可以用 SparkConf 对象创建。对于 Java 来说，可以使用 SparkConf 对象创建 JavaStreamingContext：
```java
SparkConf conf = new SparkConf().setAppName(appName).setMaster(master);
JavaStreamingContext jsc = new JavaStreamingContext(conf, Durations.seconds(seconds));
```
对于 Scala 来说，可以使用 SparkConf 对象创建 StreamingContext：
```scala
import org.apache.spark._
import org.apache.spark.streaming._

val conf = new SparkConf().setAppName(appName).setMaster(master)
val ssc = new StreamingContext(conf, Seconds(1))
```
appName 参数是应用程序在集群 UI 上显示的名称。master 是 Spark，Mesos 或 YARN 集群 URL，或者是以本地模式运行的特殊字符串`local [*]`。

实际上，当在集群上运行时，一般不会在程序中硬编码 master(即在程序中写死)，而是使用 [spark-submit](https://smartsi.blog.csdn.net/article/details/55271395) 启动应用程序时得到 master 的值。对于本地测试和单元测试，你可以传递 `local [*]` 来运行 Spark Streaming 进程。注意，这里内部创建的 JavaSparkContext（所有 Spark 功能的起始点），可以通过 jsc.sparkContext 访问。

除此之外，JavaStreamingContext 对象也可以从已有的 JavaSparkContext 创建：
```java
SparkConf conf = new SparkConf().setAppName("socket-spark-stream").setMaster("local[2]");
JavaSparkContext sparkContext = new JavaSparkContext(conf);
JavaStreamingContext jsc = new JavaStreamingContext(sparkContext, Durations.seconds(seconds));
```
对于 Scala 来说也是一样的：
```scala
import org.apache.spark.streaming._

val sc = ...                // existing SparkContext
val ssc = new StreamingContext(sc, Seconds(1))
```

定义上下文后，你可以执行如下操作来实现一个流处理程序：
- 通过创建输入 DStream 定义输入源
- 通过对 DStream 应用转换操作（transformation）和输出操作（output）来定义流计算
- 可以使用 `streamingContext.start()` 方法接收和处理数据
- 可以使用 `streamingContext.awaitTermination()` 方法等待流计算完成（手动或由于任何错误），来防止应用退出
- 可以使用 `streamingContext.stop()` 手动停止处理。

> 实际案例可以参考:[Spark Streaming 第一个程序 WordCount](https://smartsi.blog.csdn.net/article/details/127231676)

注意点:
- 一旦上下文已经开始，后续不能设置或添加新的流计算。
- 上下文停止后，无法重新启动。
- 在同一时间只有一个 StreamingContext 可以在 JVM 中处于活动状态。
- 在 StreamingContext 上调用 stop() 方法，也会关闭 SparkContext 对象。如果只想关闭 StreamingContext 对象，设置 stop() 的可选参数为 false。
- 一个 SparkContext 可以重复利用创建多个 StreamingContext，只要在创建下一个 StreamingContext 之前停止前一个 StreamingContext（而不停止SparkContext）即可。

原文：[Initializing StreamingContext](http://spark.apache.org/docs/3.1.3/streaming-programming-guide.html#initializing-streamingcontext)
