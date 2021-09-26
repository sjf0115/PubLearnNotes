---
layout: post
author: sjf0115
title: Spark 运行在Yarn上Spark
date: 2018-08-02 19:01:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-running-spark-applications-on-yarn
---

在 Yarn 上运行 Spark 提供了与其他 Hadoop 组件最紧密的集成，也是在已有 Hadoop 集群上使用 Spark 的最简单的方法。为了在 Yarn 上运行，Spark 提供了两种部署模式：客户端模式和集群模式。客户端模式的 Driver 在客户端运行，而集群模式的 Driver 在 Yarn 的 Application Master 集群上运行。

对于具有任何交互式组件的程序（例如，spark-shell，pyspark）都必须使用客户端模式。客户端模式在构建 Spark 程序时也很有用，因为任何调试输出都是立即可见的。

集群模式适用于生成作业，因为整个应用在集群上运行，这样做更容易保留日志文件（包括来自 Driver 的日志文件）以供稍后检查。

### 1. 客户端模式

在客户端模式下，当 Driver 构建新的 SparkContext 实例时就启动了与 Yarn 之间的交互（如步骤1）。该 Context 向 Yarn 资源管理器提交了一个 Yarn 应用（如步骤2），Yarn 资源管理器则启动集群节点管理器上的 Yarn 容器，并在其中运行一个名为 SparkExecutorLauncher 的 application master（如步骤3）。ExecutorLauncher 的工作就是启动 Yarn 容器中的 Executor，为了做到这一点，ExecutorLauncher　要向资源管理器请求资源（如步骤4），然后启动 ExecutorBackend 进程作为分配给它的容器（如步骤5）。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/spark-base-running-spark-applications-on-yarn-1.png?raw=true)

每个 Executor 在启动时都会连接回 SparkContext，并注册自身。这就向 SparkContext 提供了关于可用于运行任务的 Executor 的数量以及位置的信息。启动的 Executor 的数量在 spark-shell，spark-submit 中设置（如果未设置，默认为2个），同时还设置每个 Executor 的内核数（默认为1）以及内存量（默认为1024MB）。

下面这个例子显示了如何在 Yarn 上运行具有4个 Executor 且每个 Executor 使用1个内核和2G内存的 spark-submit：
```
spark-submit \
--class com.sjf.example.batch.WordCount \
--master yarn \
--deploy-mode client \
--executor-memory 2g \
--num-executors 4 \
--executor-cores 1 \
${RUN_HOME}/spark-example-jar-with-dependencies.jar \
${input_path} ${output_path}
```

### 2. 集群模式

在集群模式下，用户的 Driver 程序在 Yarn 的 application master 的进程中运行。使用 spark-submit 命令时需要输入：
```
spark-submit --master yarn --deploy-mode cluster
```
所有其他参数都与客户端模式相同。

spark-submit 客户端将会启动 Yarn 应用（如步骤1），但是它不会运行任何用户代码。剩余过程与客户端模式相同，除了 application master 在为 Executor 分配资源（如步骤4）之前先启动 Driver 程序（如步骤3b）外。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/spark-base-running-spark-applications-on-yarn-2.png?raw=true)

下面这个例子显示了如何在 Yarn 上运行具有4个 Executor 且每个 Executor 使用1个内核和2G内存的 spark-submit：
```
spark-submit \
--class com.sjf.example.batch.WordCount \
--master yarn \
--deploy-mode cluster \
--executor-memory 2g \
--num-executors 4 \
--executor-cores 1 \
${RUN_HOME}/spark-example-jar-with-dependencies.jar \
${input_path} ${output_path}
```

在这两种模式下，Executor 都是在还没有任何本地数据位置信息之前先启动的，因此最终有可能会导致 Executor 与存有作业所有希望访问文件的 DataNode 并不在一起。对于交互式会话，这是可以接受的，特别是因为会话开始之前可能并不知道需要访问哪些数据集。但是对于生成作业来说，情况并非如此，所以 Spark 提供了一种方法，可以在 Yarn 集群模式下运行时提供了一些有关位置的提示，以提高数据本地性。

参考：Hadoop权威指南
