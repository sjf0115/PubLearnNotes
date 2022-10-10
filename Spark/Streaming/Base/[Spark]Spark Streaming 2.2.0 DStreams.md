---
layout: post
author: sjf0115
title: Spark Streaming 2.2.0 DStreams
date: 2018-04-04 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-discretized-streams-dstreams
---

离散流或者 DStreams 是 Spark Streaming 提供的基本抽象，它代表一个连续的数据流。从 source 中获取输入流，或者是输入流通过转换算子处理后生成的数据流。在内部，DStreams 由一系列连续的 RDD 组成。它是 Spark 中一个不可改变的抽象，分布式数据集的抽象（更多细节参见[Spark编程指南](http://spark.apache.org/docs/2.2.0/rdd-programming-guide.html)）。DStream 中的每个 RDD 包含来自特定间隔的数据，如下图所示：

![image](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-discretized-streams-dstreams-1.png?raw=true)

对 DStream 应用的任何操作都会转换为对 DStream 底层的 RDD 操作。例如，在之前的[示例](http://smartsi.club/2018/04/02/spark-streaming-first-example/)中将行数据流转换单词数据流，flatMap 操作应用于 lines 这个 DStreams 中的每个 RDD，生成 words 这个 DStreams 的 RDD。过程如下图所示：

![image](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-discretized-streams-dstreams-2.png?raw=true)

这些底层的 RDD 转换操作由 Spark 引擎计算。DStream 操作隐藏了大部分细节，并为开发人员提供了更高级别的API以方便使用。这些操作将在后面的章节中详细讨论。

> Spark Streaming 版本: 2.2.0

原文：http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#discretized-streams-dstreams
