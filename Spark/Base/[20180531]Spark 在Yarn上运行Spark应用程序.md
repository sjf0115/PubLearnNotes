---
layout: post
author: sjf0115
title: Spark 在Yarn上运行Spark应用程序
date: 2018-05-31 19:01:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-running-spark-applications-on-yarn
---

### 1. 部署模式

在 YARN 中，每个应用程序实例都有一个 ApplicationMaster 进程，该进程是为该应用程序启动的第一个容器。应用程序负责从 ResourceManager 上请求资源。一旦分配了资源，应用程序将指示 NodeManagers 启动容器。ApplicationMasters 消除了对活跃客户端的依赖：启动应用程序的进程可以终止，并且从在集群上由 YARN 管理的进程继续协作运行。

有关指定部署模式的选项，请参阅[spark-submit选项](http://smartsi.club/2018/04/07/spark-base-launching-applications-with-spark-submit/)。

#### 1.1 Cluster部署模式

在 Cluster 模式下，Spark Driver 在集群主机上的 ApplicationMaster 上运行，它负责向 YARN 申请资源，并监督作业的运行状况。当用户提交了作业之后，就可以关掉 Client，作业会继续在 YARN 上运行。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-running-spark-applications-on-yarn-1.png?raw=true)

Cluster 模式不太适合使用 Spark 进行交互式操作。需要用户输入的 Spark 应用程序（如spark-shell和pyspark）需要 Spark Driver 在启动 Spark 应用程序的 Client 进程内运行。

#### 1.2 Client部署模式

在 Client 模式下，Spark Driver 在提交作业的主机上运行。ApplicationMaster 仅负责从 YARN 中请求 Executor 容器。在容器启动后，Client 与容器通信以调度工作。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-running-spark-applications-on-yarn-2.png?raw=true)

模式|Client模式|Cluster模式
---|---|---
Driver在哪运行| Client	|ApplicationMaster
请求资源	|ApplicationMaster	|ApplicationMaster
启动 executor 进程	|YARN NodeManager	|YARN NodeManager
持久化服务	|YARN ResourceManager 和 NodeManagers	|YARN ResourceManager 和 NodeManagers
是否支持Spark Shell	|Yes	|No

### 2. 在YARN上运行Spark Shell应用程序

要在 YARN 上运行 spark-shell 或 pyspark 客户端，请在启动应用程序时使用 `--master yarn --deploy-mode client` 标志。

### 3. Example

#### 3.1 以Cluster模式运行

以Cluster模式运行WordCount:
```
spark-submit \
--class com.sjf.example.batch.WordCount \
--master yarn \
--deploy-mode cluster \
--driver-memory 10g \
--executor-memory 12g \
--num-executors 20 \
--executor-cores 2 \
${RUN_HOME}/spark-example-jar-with-dependencies.jar \
${input_path} ${output_path}
```
该命令会打印状态，直到作业完成或按下 `control-C`。在 Cluster 模式下终止 spark-submit 进程不会像在 Client 模式下那样终止 Spark 应用程序。要监视正在运行的应用程序的状态，请运行 `yarn application -list`。

#### 3.2 以Client模式运行

```
spark-submit \
--class com.sjf.example.batch.WordCount \
--master yarn \
--deploy-mode client \
--driver-memory 10g \
--executor-memory 12g \
--num-executors 20 \
--executor-cores 2 \
${RUN_HOME}/spark-example-jar-with-dependencies.jar \
${input_path} ${output_path}
```

原文：https://www.cloudera.com/documentation/enterprise/5-14-x/topics/cdh_ig_running_spark_on_yarn.html
