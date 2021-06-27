---
layout: post
author: sjf0115
title: Spark和Hadoop中的Shuffle操作
date: 2018-03-16 12:56:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-shuffle-operation-hadoop-spark
---

在本文中我们主要看看 Hadoop 和 Spark 中的 shuffle 操作。Databricks发布了[breaking the Terasort record](https://databricks.com/blog/2014/10/10/spark-petabyte-sort.html)文章 - 关键优化点之一就是 `shuffle`，其他两点是新的排序算法和外部排序服务。

### 1. 背景: Hadoop中的Shuffle操作

Map-Reduce（MR）范例的基本前提是每个 reducer 的输入都将按键排序。确保这一点的过程，即将 map 输出结果以排序形式输送到 reducer 输入的就是 `shuffle` 操作。

#### 1.1 Map Side

map 任务将输出写入一个缓冲区，该缓冲区是一个循环内存缓冲区。缓冲区的大小由参数 `io.sort.mb` 控制（默认值为100mb）。当缓冲区大小超过阈值时，后台线程开始将数据溢写到磁盘。溢出的数据被写入到特定作业的文件夹中，由 `mapred.local.dir` 属性指定。溢出阈值由参数 `io.sort.spill.percent` 指定（默认值为80％）。在溢出之前，后台线程会对数据进行分区，以便每个 reducer 的数据都是在一个独立的分区上。写入缓冲区和写入磁盘的操作都是并行操作。但是如果缓冲区填满，map 将会被阻塞。下图好地说明了这点：

![]()

除此之外，可以将 `mapred.compress.map.output` 参数设置为 `true` 来压缩 map 输出。可以在 `mapred.map.output.compression.codec` 参数中指定适当的压缩库，例如 bzip，gzip 和 LZO 等等。

输出文件分区通过 HTTP 传输到各自的 reducers。

#### 1.2 Reduce Side

Reducer 具有一个复制阶段 - 少量线程从任务跟踪器(task tracker)的相应磁盘上并行拉取 map 输出。线程个数由参数 `mapred.reduce.parallel.copies` 控制（默认值为5）。reducer 知道从哪个任务跟踪器读取分区文件 - 这是在从 map 任务到 tasktracker 的心跳通信中指定的，然后通知 jobtracker。

map 输出被复制到 reducer 端 tasktracker 的内存缓冲区中 - 缓冲区的大小由参数 `mapred.job.shuffle.input.buffer.percent` 控制，这是使用堆的百分比。如果超过参数 `mapred.job.shuffle.merge.percent` 指定的阈值大小或者超过参数 `mapred.inmem.merge.threshold` 指定的 map 输出阈值数量，则缓冲区中的数据溢写到磁盘。后台线程将它们合并成更大的排序文件。压缩的 map 输出必须在此阶段解压缩。

当所有的 map 输出都被复制完后，reducer 进入排序阶段。合并 reduce 输入来保持排序的顺序。合并所需的回合数由 `io.sort.factor` 属性中指定的合并因子（默认值为10）控制。 map 输出的数量除以合并因子就是需要的回合数。

reducer 的最后阶段是 reduce 阶段，它将各回合的输出分别直接输送到 reduce 函数。该函数在排序后的输出中的键上被调用，结果直接写入HDFS。

### 2. Hadoop YARN中的Shuffle操作

Hadoop 中的 Shuffle 操作是由 ShuffleConsumerPlugin 实现。这个接口在执行 MapReduce 程序时使用内置的 `shuffle` handler 或第三方 AuxiliaryService 将MOF（MapOutputFile）文件传输到 reducer。

AuxiliaryService 是一个架构，允许通过 YARN 运行应用程序所需的每个节点的客户服务。 辅助服务由NodeManager管理。 当新应用程序或新容器开始或完成时会通知它。 它还提供了一个句柄来检索Hadoop中的MapReduce服务的元数据。 例如。 元数据可以是映射器和Reducer之间的连接信息，以在MapReduce作业执行期间传输MOF文件。


### 3. Spark中的Shuffle操作

#### 3.1 Map Side

#### 3.2 Reduce Side

### 4. 优化
















































原文: https://analyticsindiamag.com/shuffle-operation-hadoop-spark/
