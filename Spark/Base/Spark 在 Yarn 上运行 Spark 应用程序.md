---
layout: post
author: sjf0115
title: Spark 在 Yarn 上运行 Spark 应用程序
date: 2018-05-31 19:01:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-running-spark-applications-on-yarn
---

在 Yarn 上运行 Spark 提供了与其他 Hadoop 组件最紧密的集成，也是在已有 Hadoop 集群上使用 Spark 的最简单的方法。为了在 Yarn 上运行 Spark 应用程序，Spark 提供了两种部署模式：Client 模式和 Cluster 模式。Client 模式的 Driver 在客户端运行，而 Cluster 模式的 Driver 在 Yarn 的 Application Master 上运行。

对于具有任何交互式组件的程序（例如，spark-shell，pyspark）都必须使用 Client 模式。Client 模式在构建 Spark 应用程序时也很有用，因为任何调试输出都是立即可见的。Cluster 模式适用于生产作业，因为整个应用在集群上运行，这样做更容易保留日志文件（包括来自 Driver 的日志文件）以供日后的异常检查。

### 1. 部署模式

在 YARN 中，每个应用程序实例都有一个 ApplicationMaster 进程，该进程是为该应用程序启动的第一个容器。应用程序负责从 ResourceManager 上请求资源。一旦分配了资源，应用程序将指示 NodeManagers 启动容器。ApplicationMasters 消除了对活跃客户端的依赖：启动应用程序的进程可以终止，并且从在集群上由 YARN 管理的进程继续协作运行。

有关指定部署模式的选项，请参阅[Spark 应用程序部署工具 spark-submit](https://smartsi.blog.csdn.net/article/details/55271395)。

#### 1.1 Cluster 部署模式

在 Cluster 模式下，Spark Driver 在集群主机上的 ApplicationMaster 上运行，它负责向 YARN 申请资源，并监督作业的运行状况。当用户提交了作业之后，就可以关掉 Client，作业会继续在 YARN 上运行。

spark-submit 客户端将会启动 Yarn 应用（如步骤1），但是它不会运行任何用户代码。除了 ApplicationMaster 在为 Executor 分配资源（如步骤4）之前先启动 Driver 程序（如步骤3b）外，其他过程均与 Client 模式相同：

![](https://github.com/sjf0115/ImageBucket/blob/main/Spark/spark-base-running-spark-applications-on-yarn-2.png?raw=true)

Cluster 模式不太适合使用 Spark 进行交互式操作。需要用户输入（如spark-shell和pyspark）的 Spark 应用程序需要 Spark Driver 在启动 Spark 应用程序的 Client 进程内运行。

#### 1.2 Client 部署模式

在 Client 模式下，Spark Driver 在提交作业的主机上运行。ApplicationMaster 仅负责从 YARN 中请求 Executor 容器。在容器启动后，Client 与容器通信以调度工作。

当 Driver 构建新的 SparkContext 实例时就启动了与 Yarn 之间的交互（如步骤1）。Context 向 Yarn 资源管理器 ResouceManager 提交了一个 Yarn 应用（如步骤2），Yarn 资源管理器 ResouceManager 则启动集群节点管理器 NodeManager 上的 Yarn 容器 Container，并在其中运行一个名为 SparkExecutorLauncher 的 ApplicationMaster（如步骤3）。ExecutorLauncher 的任务就是启动 Yarn 容器 Container 中的 Executor，为了做到这一点，ExecutorLauncher　要向资源管理器 ResouceManager 请求资源（如步骤4），然后启动 ExecutorBackend 进程作为分配给它的容器 Container（如步骤5）：

![](https://github.com/sjf0115/ImageBucket/blob/main/Spark/spark-base-running-spark-applications-on-yarn-1.png?raw=true)

每个 Executor 在启动时都会连接回 SparkContext，并注册自身。这就向 SparkContext 提供了关于可用于运行任务的 Executor 的数量以及位置的信息。启动的 Executor 的数量在 spark-shell，spark-submit 中设置（如果未设置，默认为2个），同时还设置每个 Executor 的内核数（默认为1）以及内存量（默认为1024MB）。

### 1.3 区别

模式 | Client 模式| Cluster 模式
---|---|---
Driver在哪运行| Client	|ApplicationMaster
请求资源	|ApplicationMaster	|ApplicationMaster
启动 executor 进程	|YARN NodeManager	|YARN NodeManager
持久化服务	|YARN ResourceManager 和 NodeManagers	|YARN ResourceManager 和 NodeManagers
是否支持Spark Shell	|Yes	|No

### 2. 运行作业

### 2.1 在 YARN 上运行 Spark Shell 应用程序

要在 YARN 上运行 spark-shell 或 pyspark 客户端，在启动应用程序时需要使用 `--master yarn --deploy-mode client` 参数，即以 Client 部署模式提交到 Yarn 上。Cluster 模式不支持 spark-shell 或 pyspark 客户端。

### 2.2 提交 Spark 应用程序到 Yarn 上

要向 YARN 提交应用程序，需要使用 spark-submit 脚本并指定 `--master yarn` 参数，部署模式 deploy-mode 可以根据自己的需求选择。有关其他 spark-submit 参数选项，请参阅 [Spark 应用程序部署工具 spark-submit](https://smartsi.blog.csdn.net/article/details/55271395) 参数。

### 3. Example

#### 3.1 以 Cluster 模式运行

下面这个例子展示了如何使用 Cluster 模式在 Yarn 上运行具有 4 个 Executor 的应用程序，每个 Executor 使用 1 个内核和 2G 内存：
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
该命令会打印状态，直到作业完成或按下 `control-C`。在 Cluster 模式下终止 spark-submit 进程不会像在 Client 模式下那样终止 Spark 应用程序。要监视正在运行的应用程序的状态，请运行 `yarn application -list`。

#### 3.2 以 Client 模式运行

下面这个例子展示了如何使用 Client 模式在 Yarn 上运行具有 4 个 Executor 的应用程序，每个 Executor 使用 1 个内核和 2G 内存：
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

参考：
- https://www.cloudera.com/documentation/enterprise/5-14-x/topics/cdh_ig_running_spark_on_yarn.html
- Hadoop权威指南
