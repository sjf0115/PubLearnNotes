---
layout: post
author: sjf0115
title: Flink 1.4 内部原理之分布式运行环境
date: 2018-01-03 11:03:01
tags:
  - Flink
  - Flink 内部原理

categories: Flink
permalink: flink-distributed-runtime
---

### 1. 任务链与算子链

在分布式运行中，`Flink`将算子(operator)子任务连接成 `Task`。每个 `Task` 都只由一个线程执行。将算子链接到任务中是一个很有用处的优化：它降低了线程间切换和缓冲的开销，并增加了整体吞吐量，同时降低了延迟。链接行为可以在API中配置。

下图中的示例数据流由五个子任务执行，因此具有五个并行线程。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%88%86%E5%B8%83%E5%BC%8F%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83-1.png?raw=true)

### 2. 作业管理器, 任务管理器, 客户端

Flink运行时(`runtime`)由两种类型的进程组成：

(1) 作业管理器`JobManagers`(也称为`masters`)协调分布式运行。主要功能是调度任务，协调检查点，协调故障恢复等。

至少有一个`JobManager`。高可用配置下将有多个`JobManagers`，其中一个始终是领导者，其他都是备份。

(2) 任务管理器`TaskManagers`(也称为`workers`)执行数据流中的任务(更具体地说是子任务)，并对数据流进行缓冲和交换。

跟`JobManager`一样，也是至少有一个`TaskManager`。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%88%86%E5%B8%83%E5%BC%8F%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83-2.png?raw=true)

`JobManagers`和`TaskManagers`可以以不同方式启动：直接在机器上，在容器中，或者由像`YARN`这样的资源框架来管理。`TaskManagers`与`JobManagers`进行连接，来报告自己可用，并分配工作。

客户端不是运行时和程序执行的一部分，而是用来准备数据流并将其发送到`JobManager`。之后，客户端可以断开连接或保持连接来接收进度报告。客户端作为触发执行的`Java`/`Scala`程序的一部分运行，或者在命令行中运行`./bin/flink`命令来运行....

### 3. 任务槽与资源

每个`worker`(`TaskManager`)都是一个`JVM`进程，可以在不同的线程中执行一个或多个子任务(译者注:一个任务有一个线程执行)。`worker`使用任务槽(至少一个)来控制`worker`能接受多少任务。

每个任务槽代表`TaskManager`的一个固定资源子集。例如，一个拥有三个任务槽的`TaskManager`将为每个任务槽分配`1/3`的内存。资源任务槽化意味着子任务不会与其他作业中的子任务争夺内存，而是任务具有一定数量的保留托管内存。请注意，这里不会对`CPU`进行隔离。目前任务槽只分离任务的托管内存。

通过调整任务槽的数量，用户可以定义子任务与其他子任务进行隔离。如果每个`TaskManager`只拥有一个任务槽意味着每个任务组都会在独立的`JVM`中运行(例如，可以在单独的容器中启动)。如果拥有多个任务槽意味着多个子任务共享同一个`JVM`。同一`JVM`中的任务共享`TCP`连接(通过多路复用)和心跳消息，他们也可以共享数据集和数据结构，从而降低单个任务的开销。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%88%86%E5%B8%83%E5%BC%8F%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83-3.png?raw=true)

默认情况下，`Flink`允许子任务共享任务槽，即使它们是不同任务的子任务，只要它们来自同一个作业。结果是一个任务槽可能会是一个完整的作业管道。允许任务槽共享有两个主要好处：

(1) Flink集群所需的任务槽数与作业中使用的最高并行度数保持一致。不需要计算一个程序总共包含多少个任务(不同任务具有不同的并行度)。

(2) 提高资源利用率。如果没有使用任务槽共享机制，那么非密集的`sour/map()`子任务就会与资源密集型`window`子任务阻塞一样多的资源。在我们的示例中，通过任务槽共享，将基本并行度从两个增加到六个，可以充分利用已分配的资源，同时确保繁重的子任务在`TaskManager`之间公平分配。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%88%86%E5%B8%83%E5%BC%8F%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83-4.png?raw=true)

这些API还包括一个资源组机制，可以避免不合理的任务槽共享。

根据经验来说，默认任务槽数应该设置为`CPU`核的数量。如果使用超线程技术，每个任务槽需要2个或更多的硬件线程上下文(With hyper-threading, each slot then takes 2 or more hardware thread contexts)。

### 4. 后端状态

键/值索引存储的确切数据结构取决于所选的后端状态。一个后端状态将数据存储在内存中`hash map`中，另一个后端状态使用`RocksDB`存储键/值。除了定义保存状态的数据结构之外，后端状态还实现了获取键/值状态的时间点快照逻辑并将该快照存储为检查点的一部分。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%88%86%E5%B8%83%E5%BC%8F%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83-5.png?raw=true)

### 5. 保存点

用`Data Stream API`编写的程序可以从保存点恢复执行。保存点允许更新你的程序和你的Flink集群，而不会丢失任何状态。

保存点是手动触发的检查点，它会捕获程序的快照并将其写入后端状态。他们依赖于常规检查点机制。在执行期间的程序定期在工作节点上生成快照并生成检查点。为了恢复，只需要最后完成的检查点，一旦新的检查点完成，可以安全地丢弃较旧的检查点。

保存点与这些定期检查点类似，只不过它们是由用户触发的，不会在新检查点完成时自动失效。


原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/concepts/runtime.html
