---
layout: post
author: sjf0115
title: Spark Streaming 2.2.0 Input DStreams和Receivers
date: 2018-04-05 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-input-dstreams-and-receivers
---

### 1. 输入DStream与Receiver

输入 DStreams 表示从 source 中获取输入数据流的 DStreams。在[入门示例](http://smartsi.club/2018/04/02/spark-streaming-first-example/)中，lines 表示输入DStream，它代表从netcat服务器获取的数据流。每一个输入DStream(除 file stream)都与一个 Receiver (接收器)相关联，接收器从 source 中获取数据，并将数据存入 Spark 内存中来进行处理。
输入 DStreams 表示从数据源获取的原始数据流。Spark Streaming 提供了两类内置的流源（streaming sources）：
- 基础数据源(Basic sources)：在 StreamingContext API 中可以直接使用的数据源。例如：文件系统(file system)和套接字连接(socket connections)。
- 高级数据源(Advanced sources)：例如 Kafka，Flume，Kinesis 等数据源可通过额外的utility classes获得。这些需要额外依赖。

我们将稍后讨论这两类数据源。

请注意，如果希望在流应用程序中并行的接收多个数据流，你可以创建多个输入 DStream（在[性能调优](http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#level-of-parallelism-in-data-receiving)部分中进一步讨论）。这需要创建多个接收器（Receivers），来同时接收多个数据流。但请注意，Spark 的 worker/executor 是一个长期运行的任务，因此会占用分配给 Spark Streaming 应用程序的其中一个核（core）。因此，记住重要的一点，Spark Streaming 应用程序需要分配足够的核（或线程，如果在本地运行）来处理接收的数据，以及来运行接收器。

>备注
- 当在本地运行 Spark Streaming 程序时，不要使用 `local` 或 `local [1]` 作为 master 的 URL。这两个都意味着只会有一个线程用于本地任务运行。如果使用基于接收器（例如套接字，Kafka，Flume等）的输入 DStream，那么唯一的那个线程会用于运行接收器，不会有其他线程来处理接收到的数据。因此，在本地运行时，始终使用 `local [n]` 作为 master 的 URL，其中 `n > 要运行的接收器的数目`。
- 将逻辑扩展到集群上运行，分配给 Spark Streaming 应用程序的核数量必须大于接收器的数量。否则系统将只接收数据，而无法处理。

### 2. 源

#### 2.1 基础数据源

在[入门实例](http://smartsi.club/2018/04/02/spark-streaming-first-example/)中我们已经了解到 `ssc.socketTextStream（...）`，它通过 TCP 套接字连接从数据服务器获取文本数据创建 DStream。除了套接字，StreamingContext API 也提供了把文件作为输入源创建 DStreams 的方法。

##### 2.1.1 File Streams

可以从与 HDFS API 兼容的任何文件系统（即，HDFS，S3，NFS等）上的文件读取数据，DStream 可以使用如下命令创建：

Java:
```Java
streamingContext.fileStream<KeyClass, ValueClass, InputFormatClass>(dataDirectory);
```
Scala:
```scala
streamingContext.fileStream[KeyClass, ValueClass, InputFormatClass](dataDirectory)
```
Spark Streaming 会监视 dataDirectory 目录并处理在该目录中创建的任何文件（不支持嵌套目录中写入的文件）。

>备注
- 所有文件必须具有相同的数据格式
- 通过原子地移动或重命名它们到数据目录中，来在dataDirectory目录下创建文件。
- 一旦移动到dataDirectory目录后，不能进行更改。因此，如果文件被连续追加数据，新的数据将不会被读取。

对于简单的文本文件，有一个更简单的方法：
```java
streamingContext.textFileStream（dataDirectory）
```
文件流不需要运行接收器（Receiver），因此不需要分配核。

> fileStream 在 Python API 中不可用，只有 textFileStream 可用。

##### 2.1.2 基于自定义的Receivers的流

可以使用通过自定义的接收器接收的数据流创建 DStream。有关详细信息，请参阅[自定义接收器指南](http://spark.apache.org/docs/2.2.0/streaming-custom-receivers.html)。

##### 2.1.3 RDD队列作为一个流

要使用测试数据测试 Spark Streaming 应用程序，还可以使用 `streamingContext.queueStream（queueOfRDDs）` 基于 RDD 队列创建 DStream。 推送到队列中的每个 RDD 将被视为 DStream 中的一批次数据，并像流一样处理。

#### 2.2 高级数据源

这类数据源需要使用非Spark库的外部接口，其中一些需要复杂依赖（例如，Kafka和Flume）。因此，为了尽量减少依赖的版本冲突问题，这些数据源本身不能创建 DStream 的功能，它是通过 依赖 单独的类库实现创建 DStream 的功能。

请注意，这些高级源在 Spark Shell 中不可用，因此基于这些高级数据源的应用程序无法在 shell 中测试。如果你真的想在 Spark shell 中使用它们，那么你必须下载相应的 Maven 组件的JAR及其依赖项，并将其添加到 classpath 中。

介绍一下常用的高级数据源：
- Kafka：Spark Streaming 2.1.0与Kafka代理版本0.8.2.1或更高版本兼容。 有关更多详细信息，请参阅[Kafka集成指南](http://spark.apache.org/docs/2.2.0/streaming-kafka-integration.html)。
- Flume：Spark Streaming 2.1.0与Flume 1.6.0兼容。 有关更多详细信息，请参阅[Flume集成指南](http://spark.apache.org/docs/2.2.0/streaming-flume-integration.html)。
- Kinesis：Spark Streaming 2.1.0与Kinesis Client Library 1.2.1兼容。 有关更多详细信息，请参阅[Kinesis集成指南](http://spark.apache.org/docs/2.2.0/streaming-kinesis-integration.html)。


### 3. 自定义数据源

这在Python中还不支持。

输入DStreams也可以从自定义数据源中创建。如果你这样做，需要实现一个自定义接收器（Receiver），可以从自定义数据源接收数据，并推送到Spark。有关详细信息，请参阅[自定义接收器指南](http://spark.apache.org/docs/2.2.0/streaming-custom-receivers.html)。

### 4. Receiver的可靠性

基于Receiver的可靠性，可以分为两种数据源。如Kafka和Flume之类的数据源允许传输的数据被确认。如果从这些可靠源接收数据，并且被确认正确的接收数据，则可以确保不会由于任何种类的故障而丢失数据。这样就出现了两种接收器（Receiver）：
- 可靠的接收器 - 当数据被接收并存储在Spark中，同时备份副本，可靠的接收器正确地向可靠的源发送确认。
- 不可靠的接收器 - 不可靠的接收器不会向数据源发送确认。这可以用在不支持确认机制的数据源上，或者甚至是可靠的数据源当你不想或者不需要进行复杂的确认的时候。

> Spark Streaming 版本: 2.2.0

原文：http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#input-dstreams-and-receivers
