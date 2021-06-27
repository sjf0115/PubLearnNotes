---
layout: post
author: 彭根禄
title: Spark Streaming 容错的改进与零数据丢失
date: 2018-05-01 20:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-improved-driver-fault-tolerance-and-zero-data-loss
---

实时流处理系统必须可以7*24小时工作，因此它需要具备从各种系统故障中恢复过来的能力。最开始，Spark Streaming就支持从driver和worker故障中恢复。然而，从有些数据源导入数据时可能存在故障恢复以后丢失数据的情况。在Spark 1.2版本中，我们已经在Spark Streaming中对预写日志（也被称为journaling）作了初步支持，改进了恢复机制，使得更多数据源零数据丢失有了可靠的保证。本文将详细地描述这个特性的工作机制，以及开发者如何在Spark Streaming应用中使用这个机制。

### 1. 背景

Spark和它的RDD抽象设计允许无缝地处理集群中任何worker节点的故障。鉴于Spark Streaming建立于Spark之上，因此其worker节点也具备了同样的容错能力。然而，Spark Streaming的长时间正常运行需求需要其应用程序必须也具备从driver进程（协调各个worker的主要应用进程）故障恢复的能力。使Spark driver能够容错是件很棘手的事情，因为它可能是任意计算模式实现的任意用户程序。不过Spark Streaming应用程序在计算上有一个内在的结构 - 在每段micro-batch数据周期性地执行同样的Spark计算。这种结构允许把应用的状态（亦称checkpoint）周期性地保存到可靠的存储空间中，并在driver重新启动时恢复该状态。

对于文件这样的源数据，这个driver恢复机制足以做到零数据丢失，因为所有的数据都保存在了像HDFS或S3这样的容错文件系统中了。但对于像Kafka和Flume等其它数据源，有些接收到的数据还只缓存在内存中，尚未被处理，它们就有可能会丢失。这是由于Spark应用的分布式操作引起的。当driver进程失败时，所有在standalone/yarn/mesos集群运行的executor，连同它们在内存中的所有数据，也同时被终止。对于Spark Streaming来说，从诸如Kafka和Flume的数据源接收到的所有数据，在它们处理完成之前，一直都缓存在executor的内存中。纵然driver重新启动，这些缓存的数据也不能被恢复。为了避免这种数据损失，我们在Spark 1.2发布版本中引进了预写日志（Write Ahead Logs）功能。

### 2. 预写日志

预写日志（也称作journal）通常被用于数据库和文件系统中，用来保证任何数据操作的持久性。这个操作的思想是首先将操作记入一个持久的日志，然后才对数据施加这个操作。假如在施加操作的中间系统失败了，通过读取日志并重新施加前面预定的操作，系统就得到了恢复。下面让我们看看如何利用这样的概念保证接收到的数据的持久性。

像Kafka和Flume这样的数据源使用接收器（Receiver）来接收数据。它们作为长驻运行任务在executor中运行，负责从数据源接收数据，并且在数据源支持时，还负责确认收到的数据。收到的数据被保存在executor的内存中，然后driver在executor中运行来处理任务。

当启用了预写日志以后，所有收到的数据同时还保存到了容错文件系统的日志文件中。因此即使Spark Streaming失败，这些接收到的数据也不会丢失。另外，接收数据的正确性只在数据被预写到日志以后接收器才会确认，已经缓存但还没有保存的数据可以在driver重新启动之后由数据源再发送一次。这两个机制确保了零数据丢失，即所有的数据或者从日志中恢复，或者由数据源重发。

### 3. 配置

如果需要启用预写日志功能，可以通过如下动作实现：
- 通过streamingContext.checkpoint(path-to-directory)设置检查点的目录。这个目录可以在任何与HadoopAPI口兼容的文件系统中设置，它既用作保存流检查点，又用作保存预写日志。
设置SparkConf的属性 spark.streaming.receiver.writeAheadLog.enable为真（默认值是假）。
- 在日志被启用以后，所有接收器都获得了能够从可靠收到的数据中恢复的优势。我们建议禁止内存中的复制机制（in-memory replication）（通过在输入流中设置适当的持久等级(persistence level)），因为用于预写日志的容错文件系统很可能也复制了数据。

此外，如果希望可以恢复缓存的数据，就需要使用支持acking的数据源（就像Kafka，Flume和Kinesis一样），并且实现了一个可靠的接收器，它在数据可靠地保存到日志以后，才向数据源确认正确。内置的Kafka和Flume轮询接收器已经是可靠的了。

最后，请注意在启用了预写日志以后，数据接收吞吐率会有轻微的降低。由于所有数据都被写入容错文件系统，文件系统的写入吞吐率和用于数据复制的网络带宽，可能就是潜在的瓶颈了。在此情况下，最好创建更多的接收器增加接收的并行度，和/或使用更好的硬件以增加容错文件系统的吞吐率。

### 4. 实现细节

让我们更深入地探讨一下这个问题，弄清预写日志到底是如何工作的。首先，我们重温一下常用的Spark Streaming的架构。

在一个Spark Streaming应用开始时（也就是driver开始时），相关的StreamingContext（所有流功能的基础）使用SparkContext启动接收器成为长驻运行任务。这些接收器接收并保存流数据到Spark内存中以供处理。用户传送数据的生命周期如下图所示（请参考下列图示）。
- 接收数据（蓝色箭头）——接收器将数据流分成一系列小块，存储到executor内存中。另外，在启用以后，数据同时还写入到容错文件系统的预写日志。
- 通知driver（绿色箭头）——接收块中的元数据（metadata）被发送到driver的StreamingContext。这个元数据包括：（i）定位其在executor内存中数据位置的块reference id，（ii）块数据在日志中的偏移信息（如果启用了）。
- 处理数据（红色箭头）——每批数据的间隔，流上下文使用块信息产生弹性分布数据集RDD和它们的作业（job）。StreamingContext通过运行任务处理executor内存中的块来执行作业。
- 周期性地设置检查点（橙色箭头）——为了恢复的需要，流计算（换句话说，即 StreamingContext提供的DStreams ）周期性地设置检查点，并保存到同一个容错文件系统中另外的一组文件中。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-improved-driver-fault-tolerance-and-zero-data-loss-1.png?raw=true)

当一个失败的driver重启时，下列事情出现（参考下一个图示）。
- 恢复计算（橙色箭头）——使用检查点信息重启driver，重新构造上下文并重启接收器。
- 恢复元数据块（绿色箭头）——为了保证能够继续下去所必备的全部元数据块都被恢复。
- 未完成作业的重新形成（红色箭头）——由于失败而没有处理完成的批处理，将使用恢复的元数据再次产生RDD和对应的作业。
- 读取保存在日志中的块数据（蓝色箭头）——在这些作业执行时，块数据直接从预写日志中读出。这将恢复在日志中可靠地保存的所有必要数据。
- 重发尚未确认的数据（紫色箭头）——失败时没有保存到日志中的缓存数据将由数据源再次发送。因为接收器尚未对其确认。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-improved-driver-fault-tolerance-and-zero-data-loss-2.jpg?raw=true)

因此通过预写日志和可靠的接收器，Spark Streaming就可以保证没有输入数据会由于driver的失败（或换言之，任何失败）而丢失。

### 5. 未来的发展方向

有关预写日志的某些未来发展方向包括：

类似Kafka这样的系统可以通过复制数据保持可靠性。允许预写日志两次高效地复制同样的数据：一次由Kafka，而另一次由Spark Streaming。Spark未来版本将包含Kafka容错机制的原生支持，从而避免第二个日志。
预写日志写入性能的改进（尤其是吞吐率）。

### 6. 进一步研究的参考

关于检查点和预写日志更多的信息，请参考Spark Streaming Programming Guide
Spark的Meetup talk中有关的主题
JIRA – SPARK-3129

译文：https://www.csdn.net/article/2015-03-03/2824081
原文：https://databricks.com/blog/2015/01/15/improved-driver-fault-tolerance-and-zero-data-loss-in-spark-streaming.html
