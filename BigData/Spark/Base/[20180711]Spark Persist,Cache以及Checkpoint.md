---
layout: post
author: sjf0115
title: Spark Persist,Cache以及Checkpoint
date: 2018-07-11 12:55:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-persist-cache-checkpoint
---

### 1. 概述

要重用RDD（弹性分布式数据集），Apache Spark提供了许多选项，包括：
- Persisting
- Caching
- Checkpointing

下面我们将了解每一个的用法。重用意味着将计算和数据存储在内存中，并在不同的算子中多次重复使用。通常，在处理数据时，我们需要多次使用相同的数据集。例如，许多机器学习算法（如K-Means）在生成模型之前会对数据进行多次迭代。如果处理过程中的中间结果没有持久存储在内存中，这意味着你需要将中间结果存储在磁盘上，这会降低整体性能，因为与RAM相比，从磁盘访问数据就像是从隔壁或从其他国家获取内容。下面我们看一下在不同存储设备上的访问时间：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-base-persist-cache-checkpoint-1.jpg?raw=true)

注意硬盘访问时间和RAM访问时间。这就是为什么Hadoop MapReduce与Spark相比速度慢的原因，因为每个MapReduce迭代都会在磁盘上读取或写入数据。Spark在内存中处理数据，如果使用不当将导致作业在执行期间性能下降。让我们首先从持久化RDD到内存开始，但首先我们需要看看为什么我们需要持久化。

假设我们执行以下Spark语句：
```scala
val textFile = sc.textFile("file:///c://fil.txt")
textFile.first()
textFile.count()
```
第一行读取内存中的文件内容，读取操作是Transformation操作，因此不会有任何作业执行。Spark直到遇到Action操作才会惰性地执行DAG。接下来的两行是Action操作，它们为每个Action操作生成一个单独的作业。第二行得到RDD的第一个文本行并打印出来。第三行计算RDD中的行数。这两个Action操作都会产生结果，其内部发生的事情是Spark为每个Action生成一个单独的作业，因此RDD计算了两次。现在让我们执行以下语句：
```scala
val textFile = sc.textFile("file:///c://fil.txt")
textFile.cache()
textFile.first()
textFile.count()
// again execute the same set of commands
textFile.first()
textFile.count()
```
我们来看看Shell应用程序UI界面。如果你正在运行Spark Shell，那么默认情况下，可以通过URL `http://localhost:4040` 访问此接口：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-base-persist-cache-checkpoint-2.jpg?raw=true)

每个Action都会在Spark中生成一个单独的作业。我们从上图的底部开始看（按照时间发生顺序看），前两组记录是first（）和count（）Action操作执行的作业。中间两个记录也是前面两个Action操作产生的作业，但在此之前，RDD持久存储在RAM中。由于Spark必须在第一个语句中重新计算RDD，因此Duration时间没有得到改善。但请注意最上面的2个作业，是在RDD持久化存储在RAM后执行的，这次完成每个作业的Duration时间明显减少，这是因为Spark没有从磁盘中获取数据重新计算RDD，而是处理持久化存储在RAM中的RDD，并且与访问硬盘相比访问RAM时间会更少，我们完成相同工作的时间也会更短。现在让我们关注 Persist，Cache 和 Checkpoint。

### 2. Persist

Persist 意味着将计算出的RDD保存在RAM中并在需要时重复使用它。有几种不同级别的持久化：

持久化级别 | 说明
---|---
MEMORY_ONLY|将 RDD 以 Java 对象的形式存储在 JVM 中。如果没有足够的内存存储 RDD，则某些分区将不会被缓存，每次需要时都会重新计算。这是默认级别。如果你知道数据大小可以装载进内存中，可以使用此选项，否则会重新计算某些分区，会显着降低整体作业的性能。
MEMORY_AND_DISK | 将 RDD 以 Java 对象的形式存储在 JVM 中。如果数据在内存中放不下，则溢写到磁盘上。需要时则会从磁盘上读取，但与重新计算不能放进内存的分区相比，花费的时间会少得多。
MEMORY_ONLY_SER | 此级别与`MEMORY_ONLY`完全相同，但会在存储到内存之前序列化对象。这通常比 Java 对象更具空间效率，但是这种方式读取数据会消耗更多的CPU。
MEMORY_AND_DISK_SER | 与 `MEMORY_ONLY_SER` 类似，但如果数据在内存中放不下，则溢写到磁盘上，而不是每次需要时重新计算它们。
DISK_ONLY | 将 RDD 分区存储在磁盘上而不是内存上。
OFF_HEAP| 分区可以存储在堆外内存上。需要启用堆外内存才能使此存储级别正常工作。与堆上相比，从堆外内存访问数据有点慢，但仍然比磁盘上访问好得多。

以下是使用上述存储级别持久保存RDD的代码。如上所述可以更改存储级别：
```
textFile.persist(StorageLevel.MEMORY_ONLY)
```
### 3. Cache

Cache 与 MEMORY_ONLY 的持久化级别相同，如以下代码所示：
```
textFile.cache()
// is same as MEMORY_ONLY storage level in persist
textFile.persist(StorageLevel.MEMORY_ONLY)
```

### 4. Checkpoint

最后一个是Checkpoint，这是在作业执行期间发生故障时对RDD分区的一种重用。在具有数百个节点的集群环境中运行时，节点故障很有可能发生。即使在正常计算期间，JVM 进程也可能由于多种原因而失败。无论是什么故障，重新计算丢失的分区是一种昂贵的操作。最佳策略是在出现故障时从某个 Checkpoint 恢复故障。Checkpoint 将 RDD 的某些 stage 保存在磁盘上并打破DAG的执行链条。DAG 是应用在 RDD 上的Transformations序列，并且在每个Transformation中执行一些计算。有时这些计算很昂贵，如果出现故障，则需要从头开始重新计算丢失的分区。但是如果我们将DAG某个时间点的RDD stage 保存在磁盘上，则不需要重新从头进行计算，而是将检查点作为重新计算的起点。虽然Spark具有弹性并可以通过重新计算丢失的分区从故障中恢复，但是有时重新执行非常长的转换序列代价非常昂贵，如果我们在某个时刻点对RDD进行 Checkpoint 并使用该 Checkpoint 作为起点来重新计算丢失的分区，这样可以提高性能。我们来看下图：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-base-persist-cache-checkpoint-3.jpg?raw=true)

此作业从Spark开始并经历 stage 1到5。第一个 stage 从磁盘读取数据文件，然后stage 2到5在RDD上执行一些昂贵且复杂的计算。假设我们没有在第3个 stage 上进行 Checkpoint，并且在第4个 stege 或第5个 stage 上发生了一些故障。由于Spark具有弹性并且可以从故障中恢复，但是因为我们没有在第三个 stage 上进行 Checkpoint，所以需要从第1个 stage 开始来重新计算分区。就整体作业的性能而言，代价非常昂贵的。现在假设我们在第3个 stage 上进行 Checkpoint。Spark做的是将第3个 stage 的RDD状态保存在某些可靠的介质上，如HDFS。Checkpoint 会打破DAG执行链条，并将 Checkpoint 视为新的基线。这意味着如果在stage 4或5中发生任何节点或分区故障，不是从第一个 stage 开始计算丢失的分区，而是从 Checkpoint 开始计算。这种策略会极大地提高Spark作业在由于任何原因可能发生故障的环境中的性能。将 Checkpoint 视为新的基线，在分区或 stage 失败时会从此基线执行所有计算。

本文介绍了重用RDD的不同策略，正确使用这些策略将大大提高Spark作业的整体性能。


原文：https://www.linkedin.com/pulse/persist-cache-checkpoint-apache-spark-shahzad-aslam/
