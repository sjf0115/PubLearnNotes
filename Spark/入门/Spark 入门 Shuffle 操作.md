---
layout: post
author: sjf0115
title: Spark 入门 Shuffle 操作
date: 2018-03-13 16:13:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-shuffle-operations
---

> Spark版本:3.1.3

Spark 中的某些操作会触发一个称为 `shuffle` 的事件。`shuffle` 是 Spark 重新分配数据的一种机制，以便对不同分区上的数据进行分组。这通常跨 Executors 和机器进行数据复制，使得 `shuffle` 成为一项复杂而代价比较大的操作。

### 1. 背景

为了理解 `shuffle` 过程中发生了什么，我们以 reduceByKey 操作为例子进行说明。reduceByKey 操作生成一个新的 RDD，其中相同键的值都聚合为一个元组 - 键以及与该键相关的所有值执行 reduce 函数的结果。我们面临的挑战是，并非所有键的值都位于同一个分区，或者是同一台机器上，但它们必须位于同一位置时才能计算出结果。

在 Spark 中，数据通常不会为了某一个指定操作跨分区分布在特定的位置。在计算过程中，一个任务只在一个分区上运行 - 因此，为了组织一个 reduceByKey reduce 任务执行的所有数据，Spark需要执行一个 `all-to-all` 操作。必须读取所有分区以找到每个键的所有值，然后将各分区中的值汇总以计算每个键的最终结果 - 这称为 `shuffle`。

虽然重新洗牌后数据上的每个分区中的元素集合都是确定的，因此分区上的数据的排序也是确定的，但是所有分区上的元素的排序是不确定的。如果希望 `shuffle` 之后数据有序，那么可以使用：
- mapPartitions 使用例如 `.sorted` 对每个分区进行排序
- repartitionAndSortWithinPartitions 在重新分区的同时有效地对分区进行排序
- sortBy 生成一个全局有序的 RDD

可能导致 `shuffle` 的操作包括重新分区操作（如 repartition 和 coalesce），'ByKey 操作（不包含 countByKey，例如有 groupByKey 和 reduceByKey），以及 join 操作（如 cogroup 和 join）。

### 2. 性能影响

`shuffle` 是一项代价昂贵的操作，因为它涉及磁盘I/O，数据序列化和网络I/O。为 `shuffle` 组织数据，Spark 生成了一组任务：`map` 任务来组织数据，`reduce` 任务来聚合数据。该命名方式来自 MapReduce，与 Spark 的 `map` 和 `reduce` 操作没有直接的关系。

在内部，来自单个 `map` 任务的结果保存在内存中，直到内存不足存储不下。然后，这些将根据目标分区进行排序并写入单个文件。在 `reduce` 端，任务读取相关的排序块。某些 `shuffle` 操作会消耗大量的堆内存，因为在传输数据之前或之后，使用内存中的数据结构组织记录。具体来说，reduceByKey 和 aggregateByKey 在 `map` 端创建这些结构，`'ByKey` 操作在 `reduce` 端生成这些结构。当数据不能够储在内存中时，Spark 会将这些表溢写到磁盘中，从而导致磁盘I/O的额外开销和增加的垃圾回收。

`shuffle` 还会在磁盘上生成大量中间文件。从 Spark 1.3 开始，这些文件将被保留，直到相应的 RDD 不再使用并被垃圾收集为止。这样做是为了在重新计算时不需要重新创建 `shuffle` 文件。如果应用程序保留对这些 RDD 的引用或者未频繁 GC，垃圾收集可能会在很长一段时间后才会发生。这意味着长时间运行的 Spark 作业可能会消耗大量的磁盘空间。临时存储目录在配置 Spark 上下文时由 `spark.local.dir` 配置参数指定。

`shuffle` 可以通过调整各种配置参数来调整。请参阅 Spark配置指南中的 [Shuffle Behavior](http://spark.apache.org/docs/3.1.3/configuration.html) 部分。

原文: [Shuffle operations](https://spark.apache.org/docs/3.1.3/rdd-programming-guide.html#shuffle-operations)
