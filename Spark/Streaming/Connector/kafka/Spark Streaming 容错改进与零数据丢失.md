---
layout: post
author: sjf0115
title: Spark Streaming 容错改进与零数据丢失
date: 2018-05-01 20:28:01
tags:
  - Spark

categories: Spark
permalink: spark-streaming-improved-driver-fault-tolerance-and-zero-data-loss
---

实时流处理系统必须可以 7*24 小时工作，因此它需要具备从各种系统故障中恢复的能力。最开始，Spark Streaming 支持从 Driver 和 Worker 故障中恢复。然而，从有些数据源导入数据时可能存在故障恢复以后丢失数据的情况。在 Spark 1.2 版本中，我们已经在 Spark Streaming 中对预写日志作了初步支持，改进了恢复机制，使得更多数据源零数据丢失有了可靠的保证。本文将详细地描述这个特性的工作机制，以及开发者如何在 Spark Streaming 应用中使用这个机制。

## 1. 背景

Spark 以及 RDD 抽象设计旨在无缝处理集群中任何 Worker 节点的故障。鉴于 Spark Streaming 建立于 Spark 之上，因此其 Worker 节点也具备了同样的容错能力。然而，Spark Streaming 这种 7*24 小时长时间运行需要应用程序必须也具备从 Driver 进程（协调各个 Worker 的主要应用进程）故障恢复的能力。使 Spark Driver 具有容错性是件很棘手的事情，因为它可能是任意计算模式实现的用户程序。不过 Spark Streaming 应用程序在计算上有一个固有的结构 - 在每个微批数据上周期性地运行相同的 Spark 计算。这种结构允许把应用的状态（亦称 Checkpoint）周期性地保存到可靠的存储中，并在 Driver 重新启动时恢复该状态。

对于像文件这样的数据源，这种 Driver 恢复机制足以确保零数据丢失，因为所有的数据都保存在了像 HDFS 或 S3 这样容错的文件系统中。然而，对于像 Kafka 和 Flume 这种数据源，一些被缓冲在内存中但尚未处理的接收数据可能会丢失。这是因为 Spark 应用的分布式运行方式。当 Driver 进程失败时，所有在 Standalone/Yarn/Mesos 集群运行的 Executor，连同它们在内存中的所有数据，都被终止。对于 Spark Streaming 来说，从 Kafka 和 Flume 这种数据源接收到数据，在它们处理完成之前，一直都缓存在 Executor 的内存中。即使重新启动 Driver 也无法恢复缓冲中的数据。为了避免这种数据丢失，我们在 Spark 1.2 发布版本中引进了预写日志（Write Ahead Logs）功能。

## 2. 预写日志

预写日志（Write Ahead Logs）通常用于数据库和文件系统中，用来保证数据操作的持久性。这个操作的思想是首先将操作写入一个持久化的日志中，然后才对数据应用这个操作。如果系统在应用操作的过程中发生故障，通过读取持久化日志并重新应用之前打算执行的操作来进行恢复。下面让我们看看如何利用这个功能保证接收到的数据的持久性。

像 Kafka 和 Flume 这样的数据源使用接收器（Receiver）来接收数据。它们作为 Executor 中长驻运行任务，负责从数据源接收数据，并且还在数据源支持时负责确认收到的数据。收到的数据被保存在 Executor 的内存中，然后 Driver 在 Executor 中运行来处理任务。

当启用了预写日志以后，所有接收到的数据同时也会保存到容错文件系统中的日志文件中。因此即使 Spark Streaming 失败，这些接收到的数据也不会丢失。此外，只有在数据被预写到持久化日志以后，接收器才会确认接收到的数据。已经缓存但还没有保存的数据可以在 Driver 重新启动之后由数据源再发送一次。这两个机制确保了零数据丢失，即所有的数据要么从日志中恢复，要么由数据源重发。

## 3. 配置

如果需要启用预写日志功能，可以通过如下实现：
- 通过 `streamingContext.checkpoint(path-to-directory)` 设置检查点的目录。这个目录可以在任何与 Hadoop API 接口兼容的文件系统中设置，既用来保存检查点，又用来保存预写日志。
- 设置 SparkConf 的 `spark.streaming.receiver.writeAheadLog.enable` 参数为 true（默认为 false）。

当预写日志功能被启用以后，所有接收器都从恢复可靠接收的数据中获益。我们建议禁止内存中的复制机制（in-memory replication）（通过在输入流中设置适当的持久等级实现），因为用于预写日志的容错文件系统很可能也复制了数据。

此外，如果希望恢复缓冲中的数据，需要使用支持 ACK 的数据源，例如 Kafka、Flume，并且实现了一个可靠的接收器，在数据可靠地保存到日志以后才向数据源正确确认。内置的 Kafka 和 Flume 轮询接收器已经是可靠接收器。

最后，请注意在启用了预写日志以后，数据接收吞吐率会有轻微的降低。由于所有数据都被写入容错文件系统，文件系统的写入吞吐率以及用于数据复制的网络带宽都可能成为潜在的瓶颈。在这种情况下，最好创建多个接收器来增加数据接收的并行度、或者使用更好的硬件以增加容错文件系统的吞吐率。

## 4. 实现细节

让我们更深入地探讨一下这个问题，弄清预写日志到底是如何工作的。首先，我们重温一下常用的 Spark Streaming 的架构。当 Spark Streaming 应用启动时，也就是 Driver 启动时，相关的 StreamingContext（所有流功能的基础）使用 SparkContext 启动接收器成为长驻运行任务。这些接收器接收并保存流数据到 Spark 内存中以供处理。用户传送数据的生命周期如下图所示：
- 接收数据（蓝色箭头）：接收器将数据流拆分成一系列的 Block 并存储到 Executor 内存中。另外，在启用预写日志以后，数据同时还写入到容错文件系统的预写日志中。
- 通知 Driver（绿色箭头）：接收到的 Block 元数据被发送到 Driver 的 StreamingContext。元数据包括：
  - 定位 Block 数据在 Executor 内存中位置的 reference id
  - 如果启用了预写日志，Block 数据在预写日志中的偏移信息。
- 处理数据（红色箭头）：StreamingContext 使用 Block 信息在每批次间隔产生弹性分布数据集 RDD 以及它们的作业 Job。StreamingContext 通过运行任务处理 Executor 内存中的 Block 来执行作业。
- 周期性地设置检查点（橙色箭头）：为了恢复的需要，流计算（换句话说，即 StreamingContext 提供的 DStreams）周期性地设置检查点，并保存到同一个容错文件系统中另外的一组文件中。

![](https://github.com/sjf0115/ImageBucket/blob/main/Spark/spark-streaming-improved-driver-fault-tolerance-and-zero-data-loss-1.png?raw=true)

当失败的 Driver 重启时会执行：
- 恢复计算（橙色箭头）：使用检查点信息重启 Driver，重新构造上下文并重启接收器。
- 恢复 Block 元数据（绿色箭头）：恢复需要继续处理的 Block 的元数据。
- 重新生成未完成的作业（红色箭头）：由于失败而没有处理完成的批次，将使用恢复的元数据再次产生 RDD 以及对应的作业。
- 读取保存在预写日志中的 Block（蓝色箭头）：在这些作业执行时，Block 数据直接从预写日志中读出。这将恢复可靠存储在预写日志中的所有数据。
- 重发尚未确认的数据（紫色箭头）：失败时没有保存到预写日志中的缓存数据将由数据源再次发送。因为接收器尚未对其确认。

![](https://github.com/sjf0115/ImageBucket/blob/main/Spark/spark-streaming-improved-driver-fault-tolerance-and-zero-data-loss-2.jpg?raw=true)

因此通过预写日志和可靠的接收器，Spark Streaming 就可以保证没有输入数据会由于 Driver 的失败（或换言之，任何失败）而丢失。

原文：[Improved Fault-tolerance and Zero Data Loss in Spark Streaming](https://databricks.com/blog/2015/01/15/improved-driver-fault-tolerance-and-zero-data-loss-in-spark-streaming.html)
