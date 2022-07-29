---
layout: post
author: sjf0115
title: Spark 通过可视化来了解Spark应用程序
date: 2018-07-29 15:33:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-understanding-your-spark-application-through-visualization
---

在过去，Spark UI一直是用户应用程序调试的帮手。而在最新版本的Spark 1.4中，我们很高兴地宣布，一个新的因素被注入到Spark UI——数据可视化。在此版本中，可视化带来的提升主要包括三个部分：
- Spark Events 时间轴视图
- Execution DAG
- Spark Streaming 统计数字可视化

我们会通过一个系列的两篇博文来介绍上述特性，本次则主要分享前两个部分——Spark events时间轴视图和Execution DAG。Spark Streaming统计数字可视化将在下一篇博文中解释。

### 1. Spark Events 时间轴视图

从 Spark 初期版本至今，Spark Events 一直是面向用户API的一部分。在最新的1.4版本，Spark UI 将会把这些 Events 在一个时间轴中显示，让用户可以一眼区别相对和交叉顺序。

时间轴视图可以覆盖3个等级：所有Job，指定的某个Job，以及指定的某个stage。在下图中，时间轴显示了横跨一个应用程序所有作业中的Spark Events。

![]()

这里的 Events 顺序相对简单，在所有 Executors 注册后，在应用程序并行运行的4个job中，有一个失败，其余成功。当所有工作完成，并在应用程序退出后，Executors 同样被移除。下面不妨点击关注其中的一个job：

![]()

该job在3个文件中做word count，最后join并输出结果。从时间轴上看，很明显， 3个 word count stages 并行运行，因为它们不互相依赖。同时，最后一个阶段需要依赖前3个文件word count的结果，所以相应阶段一直等到所有先行阶段完成后才开始。下面着眼单个stage：

![]()

这个 stage 被切分为20个partitions，分别在4台主机上完成（图片并没有完全显示）。每段代表了这个阶段的一个单一任务。从这个时间轴来看，我们可以得到这个stage上的几点信息。

首先，partitions在机器中的分布状态比较乐观。其次，大部分的任务执行时间分配在原始的计算上，而不是网络或I/ O开销。这并不奇怪，因为传输的数据很少。最后，我们可以通过给executors分配更多的核心来提升并行度；从目前来看，每个executors可以同时执行不超过两个任务。

借此机会展示一下Spark通过该时间轴获得的另一个特性——动态分配。该特性允许Spark基于工作负载来动态地衡量executors 的数量，从而让集群资源更有效地共享。不妨看向下张图表：


























原文：https://databricks.com/blog/2015/06/22/understanding-your-spark-application-through-visualization.html

译文：https://www.csdn.net/article/2015-07-08/2825162
