---
layout: post
author: sjf0115
title: Flink 监控检查点 Checkpoint
date: 2020-12-13 11:27:17
tags:
  - Flink

categories: Flink
permalink: flink-monitor-checkpoint
---

> Flink 1.11

Flink的 Web 页面中提供了一些页面标签，用于监控作业的检查点 Checkpoint。这些监控统计信息即使在作业终止后也可以看到。Checkpoints 监控页面共有四个不同的 Tab 页签：Overview、History、Summary 和 Configuration，它们分别从不同角度进行了监控，每个页面都包含了与 Checkpoint 相关的指标。

### 1. Overview

Overview 页签宏观的记录了 Flink 应用中 Checkpoint 的数量以及 Checkpoint 的最新记录，包括失败和完成的 Checkpoint 记录。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink-monitor-checkpoint-1.jpg?raw=true)

Overview 页签列出了如下统计信息指标：
- Checkpoint Counts：包括从作业开始以来已触发、正在进行中、已完成、失败、重置的 Checkpoint 个数。
- Latest Completed Checkpoint：记录了最近一次完成的 Checkpoint：包括ID、完成时间点、端到端时长、状态大小、存储路径等。
- Latest Failed Checkpoint：记录了最近一次失败的 Checkpoint。
- Latest Savepoint：记录了最近一次 Savepoint 触发的信息。
- Latest Restore：记录了最近一次重置操作的信息，包括从 Checkpoint 重置和从 Savepoint 重置两种重置操作。

> 需要注意的是，这些统计信息会依赖 JobManager 的存活，如果 JobManager 发生故障关闭或者重置，这些统计信息都会置空。

### 2. History

History 页签保留了最近触发的 Checkpoint 统计信息，包括当前正在进行的 Checkpoint。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink-monitor-checkpoint-2.jpg?raw=true)

Checkpoint 统计信息包括：
- ID：触发的 Checkpoint ID。每个 Checkpoint 的ID从1开始递增。
- Status：当前 Checkpoint 的状态，包括 In Progress（进行中）、Completed（完成）、Failed（失败）。
- Trigger Time：在 JobManager 上触发 Checkpoint 的时间点。
- Latest Acknowledgement：JobManager 收到任何子任务的最新确认的时间（如果尚未收到确认，则为 n/a）。
- End to End Duration：从触发到最后一次确认的持续时间（如果尚未收到确认，则为 n/a）。Checkpoint 一个完整的端到端时长由 Checkpoint 最后一个确认子任务确定。
- Checkpointed Data Size：所有已确认子任务上的 Checkpoint 数据大小。如果启用了增量 Checkpoint，那么此值为 Checkpoint 增量数据大小。

通过点击 `+` 可以查看每个子任务的详细信息：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink-monitor-checkpoint-3.jpg?raw=true)

我们还可以通过如下参数来配置 History 中要保存的最近 Checkpoint 的数量，默认为10个：
```java
# Number of recent checkpoints that are remembered
web.checkpoints.history: 15
```

### 3. Summary

Summary 页签记录了所有完成的 Checkpoint 统计信息的最大值、最小值以及平均值等。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink-monitor-checkpoint-4.jpg?raw=true)

统计信息中包括端到端时长、状态大小以及分配过程中缓冲的数据大小。

### 4. Configuration

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink-monitor-checkpoint-5.jpg?raw=true)

Configuration 页签中包含 Checkpoint 中所有的基本配置信息，如下所示：
- Checkpointing Mode：Exactly-Once 还是 At-Least-Once 处理语义。
- Interval：Checkpoint 触发时间间隔。
- Timeout：Checkpoint 超时时间。超时后，JobManager 会取消当前 Checkpoint 并触发新的 Checkpoint。
- Minimum Pause Between Checkpoints：配置两个 Checkpoint 之间的最小时间间隔。当上一次 Checkpoint 完成后，需要等待该时间间隔才能触发下一次的 Checkpoint，避免触发过多的 Checkpoint 导致系统资源紧张。
- Persist Checkpoints Externally：如果启用 Checkpoint，数据将将持久化到外部存储中。

> 具体如何配置，可以查阅[Flink 启用与配置检查点 Checkpoint](https://smartsi.blog.csdn.net/article/details/127038694)
