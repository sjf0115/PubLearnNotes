---
layout: post
author: sjf0115
title: Spark Spark代码分析
date: 2018-05-27 13:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-spark-code-analysis
---

这篇文章讲述了如何从 Spark 代码中找出哪些代码在 driver 上执行，哪些代码在 executors 上执行。我们以 Spark 中的 [WordCount](http://smartsi.club/2018/03/11/spark-first-application-word-count/) 示例为例，让我们看看如何以及在哪执行，并尝试了解一下 Spark 的序列化。

在 MapReduce 中，Deiver，Mapper 和 Reducer 代码是作为单独的类编写的，很容易找出哪个代码在哪里执行。在 spark 中，Driver 的所有代码，Map Task和 Reduce Task 是一个类的一部分，因此需要了解发生了什么才能理解相同的内容。
- Spark 代码遵循 Java 的所有规则。
- Spark代码根据 Spark 代码中的 Transformation 和 Action 生成的任务DAG提交到框架中。
- Shuffle之前的所有 Transformation 都会在相同任务中。
- 诸如 grouby，reduceByKey，combineByKey，AggregateByKey 之类的 Transformation 都生成 Shuffle，在 stage 中会生成阶段性结果。
- 作业由 stage 组成。stage 的边界是 shuffle 操作。


Code|Executed on  Driver/Executor
---|---
javaSparkContext = getJavaSparkContext|Driver
JavaRDD<String> stringJavaRDD = javaSparkContext.textFile(inputPath);|Results in Data Read operation in all  Executors
.flatMap	|Executor (Map Task)
.mapToPair	|Executor (Map Task)
.reduceByKey	|Executor (Reduce Task)
.repartition|decides parallelism for Num Reduce Task. (if used after Map task, Results in a Shuffle Task on Executors )
.saveAsTextFile(outputPath);	 |saves output from all Reduce Task on Executor
stringJavaRDD.count()	|On Driver , Data Pulled from all tasks to Driver to perform count




























原文：http://bytepadding.com/big-data/spark/spark-code-analysis/
