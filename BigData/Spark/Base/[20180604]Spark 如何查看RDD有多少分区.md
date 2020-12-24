---
layout: post
author: sjf0115
title: Spark 如何查看RDD有多少分区
date: 2018-06-04 20:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-how-many-partitions-does-an-rdd-have
---

### 1. 使用UI查看分区的任务执行

在 stage 执行阶段，你可以在Spark UI中查看给定 stage 的分区个数。例如，下面简单作业中创建了一个含有4个分区100个元素的RDD，然后在将元素收集回驱动程序之前分发给虚拟的 map 任务：
```
scala> val someRDD = sc.parallelize(1 to 100, 4)
someRDD: org.apache.spark.rdd.RDD[Int] = ParallelCollectionRDD[0] at parallelize at <console>:12

scala> someRDD.map(x => x).collect
res1: Array[Int] = Array(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100)
```
在Spark的应用程序UI中，你可以从以下图中看到"Total Tasks"表示分区数：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-base-how-many-partitions-does-an-rdd-have-1.png?raw=true)

### 2. 使用UI查看缓存的分区

在持久化（缓存）RDD时，有必要了解一下已存储了多少分区。下面的示例与之前的示例相同，只是我们在在处理之前缓存RDD。完成后，我们可以使用UI来了解此操作存储了什么内容。
```
scala> someRDD.setName("toy").cache
res2: someRDD.type = toy ParallelCollectionRDD[0] at parallelize at <console>:12

scala> someRDD.map(x => x).collect
res3: Array[Int] = Array(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100)
```
从下图中注意到缓存了四个分区：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-base-how-many-partitions-does-an-rdd-have-2.png?raw=true)

### 3. 以编程方式检查RDD分区

在Scala API中，RDD保存了其分区数组的引用，你可以使用它来查找有多少分区：
```
scala> val someRDD = sc.parallelize(1 to 100, 30)
someRDD: org.apache.spark.rdd.RDD[Int] = ParallelCollectionRDD[0] at parallelize at <console>:12

scala> someRDD.partitions.size
res0: Int = 30
```
在python API中，有一种显式列出分区数的方法：
```
In [1]: someRDD = sc.parallelize(range(101),30)

In [2]: someRDD.getNumPartitions()
Out[2]: 30
```

> 请注意，在上面的示例中，初始化时有意将分区数设置为30。


原文：https://databricks.gitbooks.io/databricks-spark-knowledge-base/content/performance_optimization/how_many_partitions_does_an_rdd_have.html
