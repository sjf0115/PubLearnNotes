---
layout: post
author: smartsi
title: 在Zeppelin中如何使用Flink
date: 2021-06-12 18:08:01
tags:
  - Zeppelin
  - Flink

categories: Zeppelin
permalink: how-to-use-flink-in-zeppelin
---

> Zeppelin 版本：0.9.0

## 1. 简介

下载适用于 scala 2.11 的 Flink 1.10 版本

当前 Zeppelin 稳定版本为 0.9.0 版本，重构了 Flink Interpreter 以支持最新版本的 Flink。目前仅支持 Flink 1.10+ 版本，不支持旧版本的 Flink。此外也仅支持 scala-2.11，还不支持 scala-2.12。在此 Flink 我们选择适用于 scala-2.11 的 1.12.4 版本。

> 0.9.0 版本不支持 Flink 1.13 版本

本文中我们只介绍如何在 Zeppelin 上设置 flink 并以 3 种不同的执行模式运行基本的 Flink 程序。Zeppelin 的安装可以参考 [Zeppelin 安装与启动](http://smartsi.club/zeppelin-install-and-config.html) 博文，Flink 的安装参考 [Flink 安装与启动](http://smartsi.club/flink-how-to-install-and-run.html) 博文。

## 2. 配置参数

接下来就是进入 Interpreter 设置页面，配置 flink 解释器。在 flink 解释器中可以设置很多属性，现在我们简单了解一下在 Zeppelin 中使用 Flink 所需要的一些配置参数。Flink Interpreter 可以使用 Zeppelin 提供的属性进行配置，如下所示。除此之外也可以添加和设置表中未列出的其他 flink [属性](https://ci.apache.org/projects/flink/flink-docs-master/ops/config.html)。

| 名称 | 默认值 | 描述 |
| :------------- | :------------- | :------------- |
| FLINK_HOME | | Flink 安装的位置. 必填项, 否则无法在 Zeppelin 中 使用 Flink |
| HADOOP_CONF_DIR	| | Hadoop 配置文件的位置(conf), 在 Yarn 模式下是必填项 |
| HIVE_CONF_DIR	| | Hive 配置文件的位置(conf), 如果要连接 Hive Metastore 则为必填项 |
| flink.execution.mode	| local	| Flink 的执行模式, 可以是 local、yarn、remote 其中的一种 |
| flink.execution.remote.host	| | 运行 JobManager 的主机名称. 只有在 remote 模式下是必填项 |
| flink.execution.remote.port	|	| 运行 JobManager 的端口号. 只有在 remote 模式下是必填项 |
| flink.jm.memory	| 1024 | JobManager 的总共内存大小(mb) |
| flink.tm.memory	| 1024 | TaskManager 的总共内存大小(mb) |
| flink.tm.slot |	1	| 每个 TaskManager 的 slot 个数 |
| flink.yarn.appName	| Zeppelin Flink Session	| Yarn app 名称 |
| flink.yarn.queue	| default | yarn app 默认队列名称 |

> 在不同执行模式下使用的配置参数是不一样的

## 3. 执行模式

接下来就需要配置 Flink Interpreter。在 Zeppelin 中可以使用 3 种不同的 Flink 集群模式：
- Local
- Remote
- Yarn

下面将分别说明如何在这 3 种模式下配置 Flink Interpreter。

### 3.1 Local 模式

Local 模式是最简单的 Flink 运行模式，我们只需要下载 Flink 1.10 或更新版本，然后解压缩即可。不需要在 Flink 的 lib 文件下下载任何 connector jar，也不需要修改 flink-conf.xml，我们从最简单的配置开始，以防出现奇怪问题，让问题排查变得复杂。最重要的是指定 FLINK_HOME 以及 设置 flink.execution.mode 为 local 即可：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-1.png?raw=true)

### 3.2 Remote 模式

Flink 的 Remote 模式会连接一个已经创建好的 Flink 集群。我们可以先启动一个 Flink 集群，然后在 Zeppelin 中指定集群的地址。除了配置上面我们说的 FLINK_HOME 以及 flink.execution.mode（唯一不同的是在这里需要指定为 remote ）外，还需要配置 flink.execution.remote.host 和 flink.execution.remote.port （对应 Flink 集群的 rest.port 配置）来指定 JobManager 的 Rest API 地址（Zeppelin是通过这个 Rest API 来提交 Flink Job）：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-2.png?raw=true)

### 3.3 Yarn 模式

Flink 的 Yarn 模式会在 Yarn 集群中动态创建一个 Flink Cluster，然后你就可以往这个 Flink Session Cluster 提交 Flink Job 了。除了配置上面我们说的 FLINK_HOME 以及 flink.execution.mode（唯一不同的是在这里需要指定为 yarn）外，还需要配置 HADOOP_CONF_DIR，并且要确保 Zeppelin 这台机器可以访问你的 Hadoop 集群：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-3.png?raw=true)

> 请确保 Hadoop 命令在我们的 PATH 环境变量汇总。因为 Flink 内部会调用 Hadoop CLASSPATH 并在 Flink Interpreter进程中加载所有与 Hadoop 相关的 jar。

## 4. 执行 Flink 程序

配置完 flink Interpreter 后，我们就可以在 Zeppelin 中运行 flink 程序了。flink Interpreter 中有 6 个子解释器，每个子解释器用于不同的场景：

| 名称 | Class | 描述 |
| :------------- | :------------- | :------------- |
| %flink | FlinkInterpreter	| 创建 ExecutionEnvironment / StreamExecutionEnvironment / BatchTableEnvironment / StreamTableEnvironment并提供Scala环境 |
| %flink.pyflink | PyFlinkInterpreter	| 提供 Python 环境 |
| %flink.ipyflink	| IPyFlinkInterpreter	| 提供 ipython 环境 |
| %flink.ssql	| FlinkStreamSqlInterpreter	| 提供 Stream SQL 环境 |
| %flink.bsql	| FlinkBatchSqlInterpreter | 提供 Batch SQL 环境 |

Zeppelin 自带的 demo 程序中默认使用的 %flink。如果使用 SQL 来完成 flink 程序，可以使用 %flink.ssql 或者 %flink.bsql，后面我们会详细讲解如何在 Zeppelin 中使用 Flink SQL。

现在我们分别看一下在不同执行模式下执行 flink 的情况。

### 4.1 Local 模式

如下所示我们运行 flink Streaming WordCount 程序：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-4.png?raw=true)

在这种模式会在本地启动一个 MiniCluster（本地新生成一个集群，会以线程的方式跑在 Flink Interpreter 进程中），不会直接使用我们已经创建的 Flink 集群。

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-5.png?raw=true)

> 停止 Flink Interpreter 会同样销毁 Flink Cluster。

这种情况是由于 MiniCluster 的 JobManager 需要使用 8081 端口作为 Rest API 的端口，如果这个端口被其他进程占用，那么就会碰到如下错误。

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-6.png?raw=true)

一种比较大的可能性是你正好在本地启动了 Flink 的 Standalone cluster。因为 Standalone 模式下的 JobManager 默认也是使用 8081 端口。所以如果是碰到这种错误，那么检查下你是否在本地起了一个 Flink Standalone 集群，或者有没有其他程序使用了8081端口。

> 我一般会修改 Standalone cluster 的默认端口号。

### 4.2 Remote 模式

Remote 模式跟 Local 模式不一样，不是 Zeppelin 帮我们创建的 Cluster，是我们在外部单独启动的 Flink Cluster，停止 Flink Interpreter 并不会销毁 Flink Cluster。如下所示我们运行 flink Streaming WordCount 程序：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-7.png?raw=true)

启动程序之后，在我们单独启动的 Flink Cluster 上就会多一个 flink 作业：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-8.png?raw=true)

### 4.3 Yarn 模式

在 Yarn 模式下，当我们启动 Flink Interpreter 的时候就会在 Yarn 中创建 Yarn Session Cluster，当你停止或者重启 Flink Interpreter 的时候就会销毁这个 Yarn Session Cluster。

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-9.png?raw=true)

如下所示我们运行 flink Streaming WordCount 程序：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-10.png?raw=true)

启动程序之后，在我们 Yarn Session Cluster 上就会多一个 flink 作业：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-11.png?raw=true)

也可以通过 Yarn 中的 ApplicationMaster URL 地址跳转到 Flink UI 上：

![](https://github.com/sjf0115/ImageBucket/blob/main/Zeppelin/how-to-use-flink-in-zeppelin-12.png?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- [Flink interpreter for Apache Zeppelin](https://zeppelin.apache.org/docs/0.9.0/interpreter/flink.html#streamexecutionenvironment-executionenvironment-streamtableenvir)
- [Flink 运行模式](https://www.yuque.com/jeffzhangjianfeng/gldg8w/mwz8rc)
