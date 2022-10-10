---
layout: post
author: sjf0115
title: Spark Streaming 与 Kafka 整合的改进
date: 2018-03-18 11:28:01
tags:
  - Spark

categories: Spark
permalink: improvements-to-kafka-integration-of-spark-streaming
---

Apache Kafka 正在迅速成为最受欢迎的开源流处理平台之一。我们在 Spark Streaming 中也看到了同样的趋势。因此，在 Apache Spark 1.3 中，我们专注于对 Spark Streaming 与 Kafka 集成进行重大改进。主要增加如下：
- 为 Kafka 新增了 Direct API - 这允许每个 Kafka 记录在发生故障时只处理一次，并且不使用 [Write Ahead Logs](https://databricks.com/blog/2015/01/15/improved-driver-fault-tolerance-and-zero-data-loss-in-spark-streaming.html)。这使得 Spark Streaming + Kafka 流水线更高效，同时提供更强大的容错保证。
- 为 Kafka 新增了 Python API - 这样你就可以在 Python 中处理 Kafka 数据。

在本文中，我们将更详细地讨论这些改进。

### 1. Direct API

Spark Streaming 自成立以来一直支持 Kafka，Spark Streaming 与 Kafka 在生产环境中的很多地方一起使用。但是，Spark 社区要求更好的容错保证和更强的可靠性语义。为了满足这一需求，Spark 1.2 引入了 `Write Ahead Logs`（WAL）。它可以确保在发生故障时从任何可靠的数据源（即Flume，Kafka和Kinesis等事务源）接收的数据不会丢失（即至少一次语义）。即使对于像 plain-old 套接字这样的不可靠（即非事务性）数据源，它也可以最大限度地减少数据的丢失。

然而，对于允许从数据流中的任意位置重放数据流的数据源（例如 Kafka），我们可以实现更强大的容错语义，因为这些数据源让 Spark Streaming 可以更好地控制数据流的消费。Spark 1.3 引入了 Direct API 概念，即使不使用 Write Ahead Logs 也可以实现 exactly-once 语义。让我们来看看集成 Apache Kafka 的 Spark Direct API 的细节。

### 2. 我们是如何构建它？

从高层次的角度看，之前的 Kafka 集成与 `Write Ahead Logs`（WAL）一起工作如下：

(1) 运行在 Spark workers/executors 上的 Kafka Receivers 连续不断地从 Kafka 中读取数据，这用到了 Kafka 高级消费者API。

(2) 接收到的数据存储在 Spark 的 worker/executor的内存上，同时写入到 WAL（拷贝到HDFS）上。Kafka Receiver 只有在数据保存到日志后才会更新 Zookeeper中的 Kafka 偏移量。

(3) 接收到的数据及其WAL存储位置信息也可靠地存储。在出现故障时，这些信息用于从故障中恢复，重新读取数据并继续处理。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/improvements-to-kafka-integration-of-spark-streaming-1.png?raw=true)

虽然这种方法可以确保从 Kafka 接收的数据不会丢失，但是在失败的时候，某些记录仍然有可能会被多次被处理（即 at-least-once  语义）。这种情况在一些接收到的数据被可靠地保存到 WAL 中，但是在更新 Zookeeper 中相应的 Kafka 偏移量之前失败时会发生(译者注：即已经保存到WAL，但是还没有来得及更新 Zookeeper 中的 Kafka 偏移量)。从而导致了不一致的情况 - Spark Streaming 认为数据已被接收，但 Kafka 认为数据还未成功发送，因为　Zookeeper　中的偏移未更新。因此，在系统从故障中恢复后，Kafka　会再一次发送数据。

出现这种不一致的原因是两个系统无法对描述已发送内容的信息进行原子更新。为了避免这种情况，只需要一个系统来维护已发送或接收的内容的一致性视图。此外，这个系统需要有从故障中恢复时重放数据流的一切控制权。因此，我们决定所有消费的偏移量信息只保存在 Spark Streaming 中，这些信息可以使用 Kafka 的 [Simple Consumer API](http://kafka.apache.org/documentation.html#simpleconsumerapi) 根据故障需要重放任意偏移量的数据来从故障中恢复。

为了构建这个系统，新的 Direct Kafka API 采用与 Receivers 和 WAL 完全不同的方法。与使用 Receivers 连续接收数据并将其存储在 WAL 中不同，我们只需在给出每个批次开始时要使用的偏移量范围。之后，在执行每个批次的作业时，将从 Kafka 中读取与偏移量范围对应的数据进行处理（与读取HDFS文件的方式类似）。这些偏移量也能可靠地保存（）并用于重新计算数据以从故障中恢复。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/improvements-to-kafka-integration-of-spark-streaming-2.png?raw=true)

请注意，Spark Streaming 可以在失败以后重新读取和处理来自 Kafka 的流片段以从故障中恢复。但是，由于 RDD 转换的  exactly-once 语义，最终重新计算的结果与在没有失败的结果完全相同。

因此，Direct API 消除了对 Kafka 的 WAL 和 Receivers 的依赖，同时确保每个 Kafka 记录都被 Spark Streaming 有效地接收一次。这允许我们用端到端的 exactly-once  语义将 Spark Streaming 与 Kafka 进行整合。总的来说，它使得这样的流处理流水线更加容错，高效并且更易于使用。

### 3. 如何来使用

新的API相比之前的更加容易使用：
```scala
// Define the Kafka parameters, broker list must be specified
val kafkaParams = Map("metadata.broker.list" -> "localhost:9092,anotherhost:9092")

// Define which topics to read from
val topics = Set("sometopic", "anothertopic")

// Create the direct stream with the Kafka parameters and topics
val kafkaStream = KafkaUtils.createDirectStream[String, String, StringDecoder, StringDecoder](streamingContext, kafkaParams, topics)
```
由于这种 Direct API 没有使用 Receivers，因此你不必担心如何创建多个输入 DStream 来创建多个 Receivers。你也不需要考虑每个 Receiver 消费的 Kafka partition 的数量。每个 Kafka partition 将自动的并行读取。此外，每个 Kafka partition 与 RDD partition 一一对应，从而简化了并行模型。

除了新的流处理API之外，我们还引入了 KafkaUtils.createRDD()，它可用于在 Kafka 数据上运行批处理作业。

```scala
// Define the offset ranges to read in the batch job
val offsetRanges = Array(

  OffsetRange("some-topic", 0, 110, 220),
  OffsetRange("some-topic", 1, 100, 313),
  OffsetRange("another-topic", 0, 456, 789)

)

// Create the RDD based on the offset ranges
val rdd = KafkaUtils.createRDD[String, String, StringDecoder, StringDecoder](sparkContext, kafkaParams, offsetRanges)
```
如果你想了解更多关于API和它如何实现的细节，请看下面的内容:
- [Spark Streaming + Kafka Integration Guide](http://spark.apache.org/docs/latest/streaming-kafka-integration.html)
- [Exactly-once Spark Streaming from Kafka](https://github.com/koeninger/kafka-exactly-once/blob/master/blogpost.md)
- Direct API 完整 word count example: [Scala](https://github.com/apache/spark/blob/master/examples/src/main/scala/org/apache/spark/examples/streaming/DirectKafkaWordCount.scala) 和 [Java](https://github.com/apache/spark/blob/master/examples/src/main/java/org/apache/spark/examples/streaming/JavaDirectKafkaWordCount.java)
- [Fault-tolerance Semantics in Spark Streaming Programming Guide](http://spark.apache.org/docs/latest/streaming-programming-guide.html#fault-tolerance-semantics)

### 4. Python 中的 Kafka API

在 Spark 1.2 中，添加了 Spark Streaming 的基本 Python API，因此开发人员可以使用 Python 编写分布式流处理应用程序。在 Spark 1.3 中，扩展了 Python API 来包含Kafka。借此，在 Python 中使用 Kafka 编写流处理应用程序变得轻而易举。这是一个示例代码。
```python
kafkaStream = KafkaUtils.createStream(streamingContext,

"zookeeper-server:2181", "consumer-group", {"some-topic": 1})

lines = kafkaStream.map(lambda x: x[1])
```
查看完整的[示例](https://github.com/apache/spark/blob/master/examples/src/main/python/streaming/kafka_wordcount.py)和 [python文档](http://spark.apache.org/docs/latest/api/python/pyspark.streaming.html#pyspark-streaming-kafka-module)。运行该示例的说明可以在 Kafka 集成指南中找到。请注意，对于使用 Kafka API 运行示例或任何 python 应用程序，你必须将 Kafka Maven 依赖关系添加到路径中。这可以在 Spark 1.3 中轻松完成，因为你可以直接将 Maven 依赖关系添加到 spark-submit （推荐的方式来启动Spark应用程序）。


原文：https://databricks.com/blog/2015/03/30/improvements-to-kafka-integration-of-spark-streaming.html
