---
layout: post
author: sjf0115
title: Spark Streaming 核心抽象 DStream
date: 2018-04-04 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-discretized-streams-dstreams
---

> Spark Streaming 版本: 3.1.3

Spark Streaming 为了将 Spark 的分布式计算能力应用到流处理当中，将连续的数据流转换为 Spark 所能驾驭的离散数据集。这里 Spark Streaming 引入了一个新的概念：离散流或者叫 DStream。这是 Spark Streaming 提供的基本抽象，使用基于时间序列的 RDD 来表示一个连续的数据流，其中每个 RDD 由离散的数据块 Block 组成。

从 source 中获取输入流，或者是输入流通过转换算子处理后生成的数据流。在内部，DStream 由一系列连续的 RDD 组成。它是 Spark 中一个不可改变的抽象，分布式数据集的抽象（更多细节参见[Spark编程指南](https://spark.apache.org/docs/3.1.3/rdd-programming-guide.html#resilient-distributed-datasets-rdds)）。DStream 中的每个 RDD 包含来自特定间隔的数据，如下图所示：

![](../../../Image/Spark/spark-streaming-discretized-streams-dstreams-1.png)

对 DStream 应用的任何操作都会转换为对 DStream 底层的 RDD 操作。例如，在之前的[Spark Streaming 第一个程序 WordCount](https://smartsi.blog.csdn.net/article/details/127231676)中将行数据流转换单词数据流，flatMap 操作应用于 lines 这个 DStream 中的每个 RDD，生成 words 这个 DStreams 的 RDD。过程如下图所示：

![](../../../Image/Spark/spark-streaming-discretized-streams-dstreams-2.png)

这些底层的 RDD 转换操作由 Spark 引擎计算。DStream 操作隐藏了大部分细节，并为开发人员提供了更高级别的API以方便使用。这些操作将在后面的章节中详细讨论。


参考：[Discretized Streams (DStreams)](http://spark.apache.org/docs/3.1.3/streaming-programming-guide.html#discretized-streams-dstreams)
