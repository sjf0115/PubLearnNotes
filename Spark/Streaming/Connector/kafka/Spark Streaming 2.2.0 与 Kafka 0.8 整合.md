---
layout: post
author: sjf0115
title: Spark Streaming 与 Kafka 0.8 整合
date: 2018-03-16 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-kafka-0-8-integration
---

> Spark 版本 2.2.0
> Kafka版本：0.8

在这篇文章我们主要讲解一下如何配置 Spark Streaming 来接收 Kafka 的数据，一共有两种方法：
- 一种是使用 Receivers 和 Kafka 高级API的旧方法
- 另一种是不使用 Receivers 的新方法（在 Spark 1.3 中引入）

它们具有不同的编程模型，性能特征和语义保证。就目前的 Spark 版本而言，这两种方法都被为稳定的API。

> Kafka 0.8 在 Spark 2.3.0　版本中已经被弃用

## 1. 基于 Receiver 的方法

第一种方法是使用 Receiver 来接收 Kafka 中的数据，通过 Kafka 的高级消费者 API 实现的。与所有接收方一样，通过 Receiver 从 Kafka 接收的数据存储在 Spark Executors 中，然后由 Spark Streaming 启动的作业处理数据。但是，在默认配置下，这种方法可能会在失败时丢失数据（请参阅[接收器的可靠性](http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#receiver-reliability)）。为确保数据不丢失，必须启用 Spark Streaming 中的预写日志 `Write Ahead Logs` 功能（在 Spark 1.2 中引入）。将所有收到的 Kafka 数据保存在分布式文件系统（例如 HDFS）的预写日志中，以便在发生故障时恢复所有数据。有关 `Write Ahead Logs` 的更多详细信息，请参阅流编程指南中的[部署](http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#deploying-applications)章节。

接下来，我们将讨论如何在流应用程序中使用这种方法。

### 1.1 引入

对于使用 Maven 的 Scala/Java 应用程序，需要引入如下依赖：
```xml
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-streaming-kafka-0-8_2.11</artifactId>
    <version>2.2.0</version>
</dependency>
```

### 1.2 编程

在流应用程序代码中，导入 KafkaUtils 并创建一个输入 DStream，如下所示：
```java
import org.apache.spark.streaming.kafka.*;

JavaPairReceiverInputDStream<String, String> kafkaStream =
    KafkaUtils.createStream(streamingContext,
    [ZK quorum], [consumer group id], [per-topic number of Kafka partitions to consume]);
```

默认情况下，Python API 会将 Kafka 数据解码为 UTF8 编码的字符串。你可以指定自定义解码函数，将 Kafka 记录中的字节数组解码为任意任意数据类型。 查看[API文档](http://spark.apache.org/docs/2.2.0/api/python/pyspark.streaming.html#pyspark.streaming.kafka.KafkaUtils)。

在这需要记住的是:
- Kafka 中的 Topic 分区与 Spark Streaming 中生成的 RDD partition 没有关系。因此增加 KafkaUtils.createStream() 中特定 topic partition 的数量仅仅增加了在单个接收器中消费 topic 使用的线程数。但是这并没有增加 Spark 在处理数据的并行度。
- 可以用不同的 groups 和 topics 来创建多个 Kafka 输入 DStream，用于使用多个接收器并行接收数据。之后可以利用 union 来合并成一个 Dstream。
- 如果你使用 HDFS 等副本文件系统去启用 `Write Ahead Logs`，那么接收到的数据已经在日志中备份。因此，输入流的存储级别为 StorageLevel.MEMORY_AND_DISK_SER（即使用KafkaUtils.createStream（...，StorageLevel.MEMORY_AND_DISK_SER））。

### 1.3 部署

与任何 Spark 应用程序一样，spark-submit 用于启动你的应用程序。但是，Scala/Java　应用程序和 Python 应用程序的细节略有不同。对于 Scala 和 Java 应用程序，如果你使用 SBT 或 Maven 进行项目管理，需要将 `spark-streaming-kafka-0-8_2.11` 及其依赖项打包到应用程序 JAR 中。同时确保 `spark-core_2.11` 和 `spark-streaming_2.11` 被标记为 provided 依赖关系，因为这些已经存在 Spark 的安装中。最后使用 spark-submit 启动你的应用程序。

对于缺乏　SBT/Maven 项目管理的 Python 应用程序，可以使用 `--packages` 直接将 `spark-streaming-kafka-0-8_2.11` 及其依赖添加到 spark-submit 中，如下所示：
```
./bin/spark-submit --packages org.apache.spark:spark-streaming-kafka-0-8_2.11:2.3.0 ...
```
或者，你也可以从 Maven 仓库中下载 spark-streaming-kafka-0-8-assembly 的JAR，并将其添加到 `spark-submit -jars` 中。

> spark-submit 详细使用方法请查阅 [Spark 应用程序部署工具spark-submit](https://smartsi.blog.csdn.net/article/details/55271395)

## 2. 不使用 Receiver 的方法

这种新的没有接收器的 "直接" 方法已在 Spark 1.3 中引入，以确保更强大的端到端保证。这个方法不使用接收器接收数据，而是定期查询 Kafka 每个 topic+partition 中的最新偏移量，并相应地定义了要在每个批次中要处理的偏移量范围。当处理数据的作业启动后，使用 Kafka 的简单消费者 API 从 Kafka 中读取定义的偏移量范围（类似于从文件系统读取文件）。请注意，此特征是在 Spark 1.3 中为 Scala 和 Java API 引入的，Python API 在 Spark 1.4 中引入。

与基于 Receiver 的方法相比，该方法具有以下优点：
- 简化并行：不需要创建多个 Kafka 输入 Stream 然后将其合并。使用 directStream，Spark Streaming 可以创建与 Kafka partition 一样多的 RDD partition，这些 partition 将全部从 Kafka 并行读取数据。因此，Kafka 和 RDD partition 之间有一对一的映射关系，这更易于理解和调整。
- 效率：在第一种方法中实现零数据丢失需要将数据存储在 `Write Ahead Log` 中，这会进行数据的拷贝。这样效率比较低下，因为数据被复制了两次：一次是 Kafka 进行的，另一次是通过 Write Ahead Log 进行的。因为没有 Receiver，所以第二种方法不存在这个问题，因此不需要 `Write Ahead Log`。只要我们 Kafka 的数据保留足够长的时间，就可以从 Kafka 恢复信息。
- Exactly-once 语义：第一种方法使用 Kafka 的高级 API 在 Zookeeper 中存储消费的偏移量。这是从　Kafka　中消费数据的传统方式。尽管这种方法（结合 `Write Ahead Log` 使用）可以确保零数据丢失（即 At-Least Once 语义），但在某些失败情况下，有一些记录可能会消费两次。发生这种情况是因为 Spark Streaming 可靠接收的数据与 Zookeeper 跟踪的偏移之间不一致。因此，在第二种方法中，我们使用简单 Kafka API，不再依赖 Zookeeper。在其检查点内，Spark Streaming 跟踪偏移量。这消除了 Spark Streaming 和 Zookeeper/Kafka 之间的不一致性，因此 Spark Streaming 每条记录在即使发生故障时也可以确切地收到一次。为了实现输出结果的 exactly-once 语义，将数据保存到外部数据存储区的输出操作必须是幂等的，或者是保存结果和偏移量的原子事务（请参阅主程序中[输出操作的语义指南](https://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#semantics-of-output-operations)获取更多信息）。

请注意，这种方法的一个缺点是它不会更新 Zookeeper 中的偏移量，因此基于 Zookeeper 的 Kafka 监控工具不会显示进度。但是，你可以在每个批次中访问由此方法处理的偏移量，并自己更新　Zookeeper（请参见下文）。

接下来，我们将讨论如何在流应用程序中使用这种方法。

### ２.1 引入

对于使用 SBT/Maven 项目定义的 Scala/Java 应用程序，请引入如下依赖：
```xml
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-streaming-kafka-0-8_2.11</artifactId>
    <version>2.2.0</version>
</dependency>
```
### ２.2 编程

在流应用程序代码中，导入 KafkaUtils 并创建一个输入 DStream，如下所示：
```java
import org.apache.spark.streaming.kafka.*;

JavaPairInputDStream<String, String> directKafkaStream =
    KafkaUtils.createDirectStream(streamingContext,
        [key class], [value class], [key decoder class], [value decoder class],
        [map of Kafka parameters], [set of topics to consume]);
```

你还可以将 messageHandler 传递给 createDirectStream 来访问 MessageAndMetadata，其包含了当前消息的元数据，并可以将其转换为任意所需的类型。在 Kafka 参数中，必须指定 metadata.broker.list 或 bootstrap.servers。默认情况下，它将从每个 Kafka 分区的最新偏移量开始消费。如果你将 Kafka 参数中的 `auto.offset.reset` 配置为 `smallest`，那么它将从最小偏移量开始消费。

你也可以使用 KafkaUtils.createDirectStream 的其他变体从任意偏移量开始消费。此外，如果你想访问每个批次中消费的偏移量，你可以执行以下操作：
```java
// Hold a reference to the current offset ranges, so it can be used downstream
AtomicReference<OffsetRange[]> offsetRanges = new AtomicReference<>();

directKafkaStream.transformToPair(rdd -> {    OffsetRange[] offsets = ((HasOffsetRanges) rdd.rdd()).offsetRanges();    offsetRanges.set(offsets);    return rdd;
}).map(
  ...
).foreachRDD(rdd -> {    for (OffsetRange o : offsetRanges.get()) {
System.out.println(
  o.topic() + " " + o.partition() + " " + o.fromOffset() + " " + o.untilOffset()
);    }    ...
});
```

如果你希望基于 Zookeeper 的 Kafka 监视工具显示流应用程序的进度，你可以使用上面来更新 Zookeeper。

请注意，HasOffsetRanges 的类型转换只有在 directKafkaStream 的第一个方法调用中使用才会成功，而不是放在后面的方法链中。你可以使用 transform() 替换 foreachRDD() 作为调用的第一个方法来访问偏移量，然后再调用其他的Spark方法。但是，请注意，RDD partition 与 Kafka partition 之间的一对一映射经过任意 shuffle 或重新分区的方法（例如， reduceByKey（）或window（）之后不会保留。

另外需要注意的是，由于此方法不使用 Receivers，因此与 receiver 相关的配置（即 `spark.streaming.receiver.*` 形式的配置）将不再适用于由此方法创建的输入DStream（将应用于其他输入DStreams）。相反，使用 `spark.streaming.kafka.*` 配置。一个重要的配置是 `spark.streaming.kafka.maxRatePerPartition`，每个 Kafka partition 使用 direct API 读取的最大速率（每秒消息数）。

### 2.3 部署

这与第一种方法相同。

原文：[Spark Streaming + Kafka Integration Guide (Kafka broker version 0.8.2.1 or higher)](https://spark.apache.org/docs/2.2.0/streaming-kafka-0-8-integration.html)
