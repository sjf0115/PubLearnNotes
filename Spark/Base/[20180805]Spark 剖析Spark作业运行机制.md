---
layout: post
author: sjf0115
title: Spark 剖析Spark作业运行机制
date: 2018-08-05 17:01:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-anatomy-of--spark-job-run
---



在最高层，它有两个独立的实体：Driver 和 Executor。Driver 负责托管应用（SparkContext）并为作业调度任务。Executor 专属于应用，它在应用运行期间运行，并执行该应用的任务。

### 1. 作业提交

下图描述了 Spark 运行作业的过程。当对 RDD 执行一个 Action （比如，Count()）时，会自动提交一个 Spark 作业。从内部看，它导致对 SparkContext 调用 runJob()（如步骤1）。





































。。
