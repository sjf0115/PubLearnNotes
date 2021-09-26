---
layout: post
author: sjf0115
title: Spark 性能调优之避免使用GroupByKey
date: 2018-03-14 11:33:01
tags:
  - Spark
  - Spark 优化

categories: Spark
permalink: spark-performance-avoid-groupbykey
---


让我们看两种不同的计算WordCount的方法，一种使用`reduceByKey`，另一种使用`groupByKey`：
```
val words = Array("one", "two", "two", "three", "three", "three")
val wordPairsRDD = sc.parallelize(words).map(word => (word, 1))

val wordCountsWithReduce = wordPairsRDD
  .reduceByKey(_ + _)
  .collect()

val wordCountsWithGroup = wordPairsRDD
  .groupByKey()
  .map(t => (t._1, t._2.sum))
  .collect()
```
虽然这两个函数都会产生正确的结果，但是 `reduceByKey` 在大型数据集上的效果要更好一些。这是因为Spark在对数据进行 shuffle 之前对每个分区上的输出根据相同的key合并在一起。

请看下图来了解 `reduceByKey` 执行时发生了什么。注意一下在数据 shuffle 之前，同一台机器上具有相同 key 的键值对如何根据相同的 key 进行合并的（通过使用传递给 `reduceByKey` 的lamdba函数）。然后再次调用lamdba函数来聚合每个分区的所有值以产生一个最终结果。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-performance-avoid-groupbykey-1.png?raw=true)

另一方面，当调用 `groupByKey` 时 - 所有的键值对都会进行 shuffle。通过网络传输大量不确定的数据。

为了确定 shuffle 到哪一台机器，Spark会在该键值对的 key 上调用分区函数。当有很多数据 shuffle 到单个 Executor 但不能装载进内存时（内存不足），Spark会将数据溢出到磁盘上。但是，Spark 一次只将一个 key 的数据刷新到磁盘 - 因此，如果单个 key 的键值对大于内存时，则会发生OOM异常。这将会在更高版本的Spark中更优雅地处理，作业仍然可以继续运行，但是我们仍应避免这种情况 - 当Spark需要溢出到磁盘时，性能会受到严重影响。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-performance-avoid-groupbykey-2.png?raw=true)

以下是比groupByKey更喜欢的函数：
- 可以在合并元素但返回类型与输入值类型不同时使用combineByKey。
- foldByKey使用关联函数和中性“零值”合并每个 key 的值。

原文：https://databricks.gitbooks.io/databricks-spark-knowledge-base/content/best_practices/prefer_reducebykey_over_groupbykey.html
