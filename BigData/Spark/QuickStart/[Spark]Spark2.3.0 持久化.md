---
layout: post
author: sjf0115
title: Spark2.3.0 持久化
date: 2018-03-16 11:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-rdd-persistence
---

### 1. 概述

Spark 中最重要的功能之一是在操作之间将数据集持久化(缓存)在内存中。当你持久化一个 RDD 时，每个节点都会保存 RDD 的任意分区，RDD在内存中计算时该数据集（或从其派生的数据集）上的其他 Action 可以重用它。这样可以使后面的 Action 操作执行的更快（通常超过10倍）。缓存是迭代算法和快速交互的关键工具。

可以使用 RDD 上的 `persist()` 或 `cache()` 方法来标记要持久化的 RDD (译者注：执行这两个方法不会立即持久化 RDD)。当 RDD 第一次在 action 操作中计算时，将持久化(缓存)到节点的内存中。Spark 的缓存是可容错的 - 如果 RDD 的任意分区丢失，将使用最初创建的转换操作自动重新计算。

### 2. 存储级别

除此之外，可以使用不同的持久化级别来存储每个持久化的 RDD，从而允许你，例如，将数据集存储在磁盘上，或者以 Java 序列化对象形式存储在内存中(以节省空间)，或者在不同机器节点上进行备份。通过将 StorageLevel 对象传递给 `persist()` 方法来设置持久化级别。`cache()` 方法使用默认存储级别，即 `StorageLevel.MEMORY_ONLY`（将反序列化的对象存储在内存中）。

持久化级别 | 说明
---|---
MEMORY_ONLY|将 RDD 以 Java 对象形式存储在 JVM 中。如果没有足够的内存存储 RDD，则某些分区将不会被缓存，每次需要时都会重新计算。这是默认级别。
MEMORY_AND_DISK | 将 RDD 以 Java 对象形式存储在 JVM 中。如果数据在内存中放不下，则溢写到磁盘上．需要时则会从磁盘上读取
MEMORY_ONLY_SER (Java and Scala) | 此级别与`MEMORY_ONLY`完全相同，但会在存储到内存之前序列化对象。这通常比 Java 对象更具空间效率，特别是在使用[快速序列化器](http://spark.apache.org/docs/2.3.0/tuning.html)的情况下，但是这种方式读取数据会消耗更多的CPU。
MEMORY_AND_DISK_SER (Java and Scala) | 与 `MEMORY_ONLY_SER` 类似，但如果数据在内存中放不下，则溢写到磁盘上，而不是每次需要时重新计算它们。
DISK_ONLY | 将 RDD 分区存储在磁盘上而不是内存上。
MEMORY_ONLY_2, MEMORY_AND_DISK_2等 | 与上面的储存级别相同，只不过将持久化数据存为两份，在两个集群节点上备份每个分区。
OFF_HEAP（实验中）| 与 `MEMORY_ONLY_SER` 类似，但将数据存储在 [堆外内存](http://spark.apache.org/docs/2.3.0/configuration.html#memory-management) 中。 这需要启用堆内存。

> 在 Python 中，存储对象始终使用 `Pickle` 库进行序列化，因此选择什么样的序列化级别是无关紧要的。Python 中的可用存储级别包括`MEMORY_ONLY`，`MEMORY_ONLY_2`，`MEMORY_AND_DISK`，`MEMORY_AND_DISK_2`，`DISK_ONLY`和`DISK_ONLY_2`。


在 Shuffle 操作中(例如，reduceByKey)，即使用户没有主动对调用 `persist`，Spark也会对一些中间数据进行持久化。这样做是为了如果一个节点在 Shuffle 过程中发生故障避免重新计算整个输入。如果要重用，我们仍然建议用户对生成的 RDD 调用 `persist`。

### 3. 选择存储级别

Spark 的存储级别旨在提供内存使用率和CPU效率之间的不同权衡。我们建议通过以下过程来选择一个：
- 如果你的 RDD 适合于默认存储级别（MEMORY_ONLY），那就保持不动。 这是CPU效率最高的选项，允许 RDD 上的操作尽可能快地运行。
- 如果不是，请尝试使用 `MEMORY_ONLY_SER` 并选择一个 [快速的序列化库](http://spark.apache.org/docs/2.3.0/tuning.html)，这种方式更加节省空间，并仍然能够快速访问。  
- 不要溢写到磁盘，除非在数据集上的计算操作成本较高，或者需要过滤大量的数据。否则，重新计算分区可能与从磁盘读取分区一样快。
- 如果要快速故障恢复（例如，使用Spark为Web应用程序提供服务），请使用副本存储级别（例如，`MEMORY_ONLY_2`）。所有存储级别通过重新计算丢失的数据来提供完整的容错能力，但副本数据可让你继续在 RDD 上运行任务，而无需重新计算丢失的分区。

### 4. 清除数据

Spark会自动监视每个节点的缓存使用情况，并以最近最少使用（LRU）方式丢弃旧的数据分区。如果你想手动删除 RDD，而不是等待它自动从缓存中删除，请使用 `RDD.unpersist()` 方法。

> Spark版本: 2.3.0

原文：http://spark.apache.org/docs/2.3.0/rdd-programming-guide.html#rdd-persistence
