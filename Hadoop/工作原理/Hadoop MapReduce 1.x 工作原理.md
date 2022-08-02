---
layout: post
author: sjf0115
title: Hadoop MapReduce 1.x 工作原理
date: 2017-12-14 13:03:01
tags:
  - Hadoop
  - Hadoop 内部原理

categories: Hadoop
permalink: hadoop-mapReduce1.x-working-principle
---

下面解释一下作业在经典的 MapReduce 1.0 中运行的工作原理。最顶层包含4个独立的实体:
- 客户端：提交 MapReduce 作业。
- JobTracker：协调作业的运行。JobTracker 是一个Java应用程序，它的主类是 JobTracker。
- TaskTracker：运行作业划分后的任务。TaskTracker 是一个 Java 应用程序，它的主类是 TaskTracker。
- 分布式文件系统(一般为HDFS)：用来在其他实体间共享作业文件。

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-mapReduce1.x-working-principle-1.png?raw=true)

### 1. 作业提交

Job 的 submit() 方法创建一个内部的 JobSunmmiter 实例，并且调用其 submitJobInternal() 方法。提交作业后，waitForCompletion() 每秒轮询作业的进度，如果发现自上次报告后有改变，便把进度报告到控制台。作业完成后，如果成功，就显示作业计数器。如果失败，导致作业失败的错误被记录到控制台。

JobSunmmiter 所实现的作业提交过程如下:
- 通过调用 JobTracker 的 getNewJobId() 方法向 JobTracker 请求一个新的作业ID。参见上图步骤2。
- 检查作业的输出。例如，如果没有指定输出目录或者输出目录已经存在，作业就不提交，错误抛回给 MapReduce 程序。
- 计算作业的输入分片。如果分片无法计算，比如因为输入路径不存在，作业不会提交，错误返回给 MapReduce 程序。
- 将运行作业所需要的资源(包括作业 JAR 文件、配置文件和计算所得的输入分片）复制到一个以作业 ID 命名的目录下的文件系统中。作业 JAR 中副本较多(由mapred.submit.replication属性控制，默认值为10)，因此在运行作业的任务时，集群中有很多个副本可供 tasktracker 访问。参见上图步骤3.
- 告知 jobtracker 作业准备执行(通过调用 JobTracker 的 submitJob() 方法实现)。参见上图步骤4.

### 2. 作业初始化

当 JobTracker 接收到其 submitJob() 方法的调用后，会把此调用放入一个内部队列中，交由作业调度器进行调度，并对其进行初始化。初始化包括创建一个表示正在运行作业的对象，用于封装任务和记录信息，以便跟踪任务的状态和进程(参见上图步骤 5)。

为了创建任务运行列表，作业调度器首先从共享文件系统中获取 JobClient 已计算好的输入分片信息(参见上图步骤6)。然后为每个分片创建一个 Map 任务。创建的 Reduce 任务的数量由 JobConf 的 mapred.reduce.task 属性决定，通过 setNumReduceTasks() 方法来设置，然后调度器创建相应数量的 reduce 任务。任务在此时被指定 ID。

除了 Map 任务和 Reduce 任务，还会创建两个任务：作业创建和作业清理。这两个任务在 TaskTracker 中执行，在 Map 任务之前运行代码来创建作业，并且在所有 Reduce 任务完成之后完成清理工作。配置项 OutputCommitter 属性能设置运行的代码。默认值是 FileOutputCommitter。作业创建为作业创建输出路径和临时工作空间。作业清理清除作业运行过程中的临时目录。

### 3. 任务分配

Tasktracker 运行一个简单的循环来定期发送心跳(heartbeat)给 Jobtracker。心跳向 Jobtracker 表明 Tasktracker 是否还存活，同时也充当两者之间的消息通道。作为心跳的一部分，Tasktracker 会指明它是否已经准备好运行新的任务，如果是，Jobtracker 会为它分配一个任务，并使用心跳的返回值与 Tasktracker 进行通信(参见上图步骤7)。

在 Jobtracker 为 Tasktracker 选择任务之前，Jobtracker 必须先选定任务所在的作业。一旦选择好作业，Jobtracker 就可以为该作业选定一个任务。

对于 Map 任务和 Reduce 任务，Tasktracker 有固定数量的任务槽。例如，一个 Tasktracker 可以同时运行两个 Map 任务和两个 Reduce 任务。具体数量由 Tasktracker 的数据和内存大小来决定。默认调度器在处理 Reduce 任务槽之前，会填满空闲的 Map 任务槽，因此，如果 Tasktracker 至少有一个空闲的 Map 任务槽，Jobtracker 会为它选择一个 Map 任务，否则选择一个 Reduce 任务。

为了选择一个 Reduce 任务，Jobtracker 简单地从待运行的 Reduce 任务列表中选取下一个来执行，用不着考虑数据的本地化。然而，对于一个 Map 任务，Jobtracker 会考虑 Tasktracker 的网络设置，并选取一个距离其输入分片最近的 Tasktracker。在最理想的情况下，任务是数据本地化的(data-local)，也就是任务运行在输入分片所在的节点上。同样，任务也可能是机架本地化的(rack-local)：任务和输入分片在所同一机架，但不在同一节点上。一些任务即不是数据本地化的，也不是机架本地化的，而是从与它们自身运行的不同机架上检索数据。可以通过查看作业的计数器得知每类任务的比例。

### 4. 任务执行

现在，Tasktracker 已经被分配了一个任务，下一步是运行该任务。第一步，通过从共享文件系统把作业的 JAR 文件复制到 Tasktracker 所在的文件系统，从而实现作业的 JAR 文件本地化。同时，Tasktracker 将应用程序所需要的全部文件从分布式缓存复制到本地磁盘(参见上图步骤8)。第二步，Tasktracker 为任务新建一个本地工作目录，并把 JAR 文件中的内容解压到这个文件夹下。第三步，Tasktracker 新建一个 TaskRunner 实例来运行该任务。

TaskRunner 启动一个新的 JVM (参见上图步骤9)来运行每个任务(参见上图步骤10)，以便用户定义的 map 和 reduce 函数的任务软件问题都不会影响到 Tasktracker(例如导致崩溃或挂起等）。但在不同的任务之前重用JVM还是可能的。

### 5. 进度和状态的更新

MapReduce 作业是长时间运行的批处理作业，运行时间范围从数分钟到数小时。这是一个很长的时间段，所以对于用户而言，能够知道进展是很重要的。一个作业和它的每个任务都有一个状态(status)，包括：作业或任务的状态(比如，运行状态，成功完成，失败状态)，map 和 reduce 的进度，作业计数器的值，状态消息或描述。

### 6. 作业完成

当 Jobtracker 收到作业最后一个任务已完成的通知后(这是一个特定的作业清理任务)，便把作业的状态设置为'成功'。然后，在 Job 查询状态时，便知道任务已成功完成，于是 Job 打印一条消息告知用户，然后从 waitForCompletion() 方法返回。Job 的统计信息和计数值也在这是输出到控制台。

最后，Jobtracker 清空作业的工作状态，Tasktracker 也清空作业的工作状态(如删除中间输出)。

来源于: Hadoop 权威指南
