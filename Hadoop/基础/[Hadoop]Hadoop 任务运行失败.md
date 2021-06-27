---
layout: post
author: sjf0115
title: Hadoop 任务运行失败
date: 2018-05-21 20:01:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-base-task-failure
---

### 1. 常见情况

任务运行失败最常见的情况是 map 任务或 reduce 任务中的用户代码抛出运行异常。如果发生这种情况，任务 JVM 会在退出之前向其父 application master 发送错误报错。错误报告最后被记入用户日志中。application master 会将此次任务尝试标记为 `failed` (失败)，并释放容器以便资源可以为其他任务使用。

任务运行失败另一种常见情况是任务 JVM 突然退出，可能由于 JVM 软件缺陷而导致 MapReduce 用户代码由于特殊原因造成 JVM 退出。在这种情况下，节点管理器会注意到进程已经退出，并通知 application master 将此次任务尝试标记为失败。

一旦 application master 注意到已经有一段时间没有收到进度的更新，便会将任务标记为失败。在此之后，任务 JVM 进程将被自动杀死。任务被认为失败的超时时间间隔通常为10分钟，可以以作业为基础（或以集群为基础）进行设置，对应的属性为 `mapreduce.task.timeout` ，单位为毫秒。

超时设置为0，将关闭超时判定，所以长时间运行的任务永远不会被标记为失败。在这种情况下，被挂起的任务永远不会释放它的容器并随着时间的推移，最终降低整个集群的效率。因此，尽量避免这种设置。


### 2. 失败重试

application master 被告知一个任务尝试失败后，将重新调度该任务的执行。application master 会试图避免在以前失败过的节点管理器上重新调度该任务。此外，如果一个任务失败过4次，将不会再重试，整个作业都会失败，如下表。

Attempt|State|Node
---|---|---
attempt_1504162679223_24764734_r_000057_0|FAILED|/default-rack/l-hp609.data.cn2:8042
attempt_1504162679223_24764734_r_000057_1|FAILED|/default-rack/l-hp143.data.cn2:8042
attempt_1504162679223_24764734_r_000057_2|FAILED|/default-rack/l-hp618.data.cn2:8042
attempt_1504162679223_24764734_r_000057_3|FAILED|/default-rack/l-hp272.data.cn2:8042

上述作业在任务失败之后会在不同节点管理器上重新调度该任务，如果任务重试４次之后还是失败则整个作业会失败：
```
18/05/21 00:24:52 INFO mapreduce.Job: Job job_1504162679223_24764734 failed with state FAILED due to: Task failed task_1504162679223_24764734_r_000057
Job failed as tasks failed. failedMaps:0 failedReduces:1
```
上面的４次是可以设置的：对于 map 任务，运行任务的最多尝试次数由 `mapreduce.map.maxattempts` 属性控制；对于 reduce 任务，则由 `mapreduce.reduce.maxattempts` 属性控制。默认情况下，如果任何任务失败次数大于４（或最多尝试次数被配置为４），整个作业都会失败。

### 3. 任务失败容忍

对于一些应用程序，我们不希望一旦有少数几个任务失败就终止运行整个作业，因为即使有任务失败，作业的一些结果可能还是可用的。在这种情况下，可以为作业设置在不触发作业的情况下任务失败的最大百分比。针对 map 任务和 reduce 任务的设置可以通过 `mapreduce.map.failures.maxpercent` 和 `mapreduce.reduce.failures.maxpercent` 两个属性来完成。

### 4. Killed任务

任务尝试也是可以终止的（killed），这与失败不同。任务尝试可以被终止是因为它是一个推测执行任务或因为它所处的节点管理器失败，导致
application master 将它上面运行的所有任务尝试标记为 killed 。被中止的任务尝试不会计入任务运行尝试次数（由 `mapreduce.map.maxattempts` 和 `mapreduce.reduce.maxattempts` 属性控制），因为尝试被中止并不是任务的过错。

用户也可以使用 Web UI 或命令行来中止或取消任务尝试。也可以采用相同的机制来中止作业。


来自:Hadoop权威指南
