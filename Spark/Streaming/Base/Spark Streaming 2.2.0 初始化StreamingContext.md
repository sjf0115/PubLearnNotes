---
layout: post
author: sjf0115
title: Spark Streaming 2.2.0 初始化 StreamingContext
date: 2018-04-03 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-initializing-streamingcontext
---

> Spark Streaming 版本: 2.2.0

为了初始化 Spark Streaming 程序，必须创建一个 StreamingContext 对象，它是 Spark Streaming 所有流操作的主要入口。StreamingContext 对象可以用 SparkConf 对象创建。可以使用 SparkConf 对象创建 JavaStreamingContext 对象：
```java
SparkConf conf = new SparkConf().setAppName(appName).setMaster(master);
JavaStreamingContext jsc = new JavaStreamingContext(conf, Durations.seconds(seconds));
```
对于 Scala 语言来说，需要创建 StreamingContext 对象：
```scala
import org.apache.spark._
import org.apache.spark.streaming._

val conf = new SparkConf().setAppName(appName).setMaster(master)
val ssc = new StreamingContext(conf, Seconds(1))
```
appName 参数是应用程序在集群 UI 上显示的名称。master 是 Spark，Mesos 或 YARN 集群 URL，或者是以本地模式运行的特殊字符串`local [*]`。

实际上，当在集群上运行时，如果你不想在程序中硬编码 master(即在程序中写死)，而是希望使用 spark-submit 启动应用程序时得到 master 的值。对于本地测试和单元测试，你可以传递 `local [*]` 来运行 Spark Streaming 进程。注意，这里内部创建的 JavaSparkContext（所有 Spark 功能的起始点），可以通过 jsc.sparkContext 访问。

JavaStreamingContext 对象也可以从现有的 JavaSparkContext 创建：
```java
SparkConf conf = new SparkConf().setAppName("socket-spark-stream").setMaster("local[2]");
JavaSparkContext sparkContext = new JavaSparkContext(conf);
JavaStreamingContext jsc = new JavaStreamingContext(sparkContext, Durations.seconds(seconds));
```
对于 Scala 来说，StreamingContext对象也可以从现有的 SparkContext 创建：
```scala
import org.apache.spark.streaming._

val sc = ...                // existing SparkContext
val ssc = new StreamingContext(sc, Seconds(1))
```

批处理间隔必须根据应用程序和可用群集资源的延迟要求进行设置。

定义上下文后，您必须执行以下操作：
- 通过创建输入 DStreams 定义输入源
- 通过对 DStreams 应用转换操作（transformation）和输出操作（output）来定义流计算
- 可以使用 streamingContext.start() 方法接收和处理数据
- 可以使用 streamingContext.awaitTermination() 方法等待流计算完成（手动或由于任何错误），来防止应用退出
- 可以使用 streamingContext.stop() 手动停止处理。

注意点:
- 一旦上下文已经开始，则不能设置或添加新的流计算。
- 上下文停止后，无法重新启动。
- 在同一时间只有一个 StreamingContext 可以在 JVM 中处于活动状态。
- 在 StreamingContext 上调用 stop() 方法，也会关闭 SparkContext 对象。如果只想关闭 StreamingContext 对象，设置 stop() 的可选参数为 false。
- 一个 SparkContext 可以重复利用创建多个 StreamingContext，只要在创建下一个 StreamingContext 之前停止前一个 StreamingContext（而不停止SparkContext）即可。

原文：http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#initializing-streamingcontext
