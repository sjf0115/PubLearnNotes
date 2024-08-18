---
layout: post
author: sjf0115
title: Spark Streaming 输入 DStream 和 Receivers
date: 2018-04-05 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-input-dstreams-and-receivers
---

> Spark Streaming 版本: 3.1.3

## 1. 输入 DStream 与 Receiver

输入 DStream 表示从数据流 Source 中获取输入数据流的 DStream。在[入门示例](https://smartsi.blog.csdn.net/article/details/127231676)中，lines 是输入 DStream，表示从 netcat 服务器获取的数据流。每一个输入 DStream(除 file stream)都与一个 Receiver (接收器)相关联，接收器从 Source 中获取数据，并将数据存入 Spark 内存中来进行处理。

输入 DStream 表示从数据源获取的原始数据流。Spark Streaming 提供了两类内置的流 Source：
- 基础数据源 Source：在 StreamingContext API 中可以直接使用的数据源。例如：文件系统和 Socket 连接。
- 高级数据源 Source：例如 Kafka，Flume，Kinesis 等数据源可通过额外的工具类获得，但需要额外依赖。

> 我们将稍后讨论这两类数据源。

需要注意的是，如果希望在流应用程序中并行的接收多个数据流，你可以创建多个输入 DStream（在[性能调优](https://smartsi.blog.csdn.net/article/details/127242776)部分中进一步讨论）。这需要创建多个接收器（Receivers）来同时接收多个数据流。但请注意，Spark 的 worker/executor 是一个长期运行的任务，因此会占用分配给 Spark Streaming 应用程序的其中一个核（core）。因此，记住重要的一点，Spark Streaming 应用程序需要分配足够的核（或线程，如果在本地运行）来处理接收的数据以及来运行接收器。

> 备注
- 当在本地运行 Spark Streaming 程序时，不要使用 `local` 或 `local [1]` 作为 master 的 URL。这两个都意味着只会有一个线程用于本地任务运行。如果使用基于接收器（例如套接字，Kafka，Flume等）的输入 DStream，那么唯一的那个线程会用于运行接收器，不会有其他线程来处理接收到的数据。因此，在本地运行时，始终使用 `local [n]` 作为 master 的 URL，其中 `n > 要运行的接收器的数目`。
- 将逻辑扩展到集群上运行，分配给 Spark Streaming 应用程序的核数量必须大于接收器的数量。否则系统将只接收数据，而无法处理。

## 2. 数据源 Source

### 2.1 基础数据源

在[入门实例](https://smartsi.blog.csdn.net/article/details/127231676)中我们已经了解到 `ssc.socketTextStream（...）` 是通过 TCP 套接字连接从数据服务器获取文本数据创建 DStream。除了套接字，StreamingContext API 也提供了把文件作为输入源创建 DStreams 的方法。

#### 2.1.1 File Streams

可以从与 HDFS API 兼容的任何文件系统（即，HDFS，S3，NFS等）上的文件读取数据。可以通过 `StreamingContext.fileStream[KeyClass, ValueClass, InputFormatClass]` 来创建 DStream。对于 Java 来说，具体使用如下语句创建：
```Java
streamingContext.fileStream<KeyClass, ValueClass, InputFormatClass>(dataDirectory);
```
对于 Scala 来说，具体使用如下语句创建：
```scala
streamingContext.fileStream[KeyClass, ValueClass, InputFormatClass](dataDirectory)
```
如果是简单的文本文件，最简单的方法是通过 `StreamingContext.textFileStream(dataDirectory)`。

> 在这需要注意的是文件流不需要运行接收器，因此不需要为接收文件数据分配任何内核。

#### 2.1.2 基于自定义的 Receivers 的流

可以使用通过自定义的接收器接收的数据流创建 DStream。有关详细信息，请参阅[自定义接收器指南](http://spark.apache.org/docs/3.1.3/streaming-custom-receivers.html)。

#### 2.1.3 RDD 队列作为一个流

要使用测试数据测试 Spark Streaming 应用程序，还可以使用 `streamingContext.queueStream（queueOfRDDs）` 基于 RDD 队列创建 DStream。推送到队列中的每个 RDD 将被视为 DStream 中的一批次数据，并像流一样处理。

### 2.2 高级数据源

这类数据源需要使用非 Spark 库的外部接口，其中一些需要复杂依赖（例如，Kafka和Flume）。因此，为了尽量减少依赖的版本冲突问题，这些数据源创建 DStreams 的功能已经转移到单独的类库中，使用时需要通过依赖具体对应的类库来实现。

需要注意的是这些高级数据源在 Spark Shell 中是不可用的，因此基于这些高级数据源的应用程序无法在 shell 中测试。如果你真的想在 Spark shell 中使用它们，那么你必须下载相应的 Maven 组件的JAR及其依赖项，并将其添加到 classpath 中。

介绍一下常用的高级数据源：
- Kafka：Spark Streaming 3.1.3 可以与 Kafka Broker 0.10 版本或者更高版本兼容。有关更多详细信息，请参阅[Kafka集成指南](https://spark.apache.org/docs/3.1.3/streaming-kafka-0-10-integration.html)。
- Kinesis：Spark Streaming 3.1.3 可以与 Kinesis Client Library 1.2.1 兼容。 有关更多详细信息，请参阅[Kinesis集成指南](https://spark.apache.org/docs/3.1.3/streaming-kinesis-integration.html)。

## 3. 自定义数据源

> 在 Python 中还不支持。

输入 DStreams 也可以从自定义数据源中创建。你所需要做的是实现一个自定义接收器（Receiver），这样就可以从自定义数据源接收数据并推送到 Spark。有关详细信息，请参阅[自定义接收器指南](https://spark.apache.org/docs/3.1.3/streaming-custom-receivers.html)。

原文：[Input DStreams and Receivers](https://spark.apache.org/docs/3.1.3/streaming-programming-guide.html#input-dstreams-and-receivers)
