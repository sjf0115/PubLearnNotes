---
layout: post
author: sjf0115
title: Hadoop 推测执行
date: 2017-12-07 19:32:17
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: speculative-execution-in-hadoop-mapreduce
---

### 1. 概述

Hadoop 不会去诊断或修复执行慢的任务，相反它会试图检测任务的运行速度是否比预期慢，并启动另一个等效任务作为备份(备份任务称为`推测任务`)。这个过程 在Hadoop 中被称为`推测执行`。

在这篇文章中，我们将讨论`推测执行` - `Hadoop` 中提高效率的一个重要功能，我们有必要去了解 `Hadoop` 中的推测执行是否总是有帮助的，或者我们需要关闭它时如何禁用。

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/speculative-execution-in-hadoop-mapreduce.gif?raw=true)

### 2. 什么是推测执行

在 `Hadoop` 中，`MapReduce` 将作业分解为任务，并且这些任务并行而不是顺序地运行，从而缩短了总体执行时间。这种执行模式对缓慢的任务很敏感(即使他们的数量很少)，因为它们减慢了整个工作的执行速度。

任务执行缓慢的原因可能有各种，包括硬件退化或软件错误配置等，尽管花费的时间超过了预期的时间，但是由于任务仍然有可能成功完成，因此很难检测缓慢的原因。`Hadoop` 不会尝试诊断和修复运行缓慢的任务，而是尝试检测并为其运行一个备份任务。这在 `Hadoop` 中被称为推测执行。这些备份任务在 `Hadoop` 中被称为推测任务。

### 3. 推测执行如何工作

现在让我们看看 `Hadoop` 的推测执行过程。

首先，在 `Hadoop MapReduce` 中启动所有任务。为那些已经运行了一段时间(至少一分钟)且比作业中其他任务平均进度慢的任务启动推测任务。如果原始任务在推测性任务之前完成，那么推测任务将被终止，相反，如果推测性任务在原始任务之前完成，那么原始任务被终止。一个任务成功完成之后，任何正在运行的重复任务都将被终止。

### 4. 推测执行的优势

`Hadoop MapReduce` 推测执行在某些情况下是很有帮助的，因为在具有 100 个节点的 `Hadoop` 集群中，硬件故障或网络拥塞等问题很常见，并行或重复运行任务会更好一些，因为我们不必等到有问题的任务执行之后。但是如果两个重复的任务同时启动，就会造成集群资源的浪费。

### 5. 配置推测执行

推测执行是 `Hadoop MapReduce` 作业中的一种优化技术，默认情况下启用的。你可以在 `mapred-site.xml` 中禁用 `mappers` 和 `reducer` 的推测执行，如下所示：
```xml
<property>
  <name>mapred.map.tasks.speculative.execution</name>
  <value>false</value>
</property>
<property>
  <name>mapred.reduce.tasks.speculative.execution</name>
  <value>false</value>
</property>
```

### 6. 有没有必要关闭推测执行

推测执行的主要目的是减少工作执行时间，但是，由于重复的任务，集群效率受到影响。由于在推测执行中正在执行冗余任务，因此这可能降低整体吞吐量。出于这个原因，一些集群管理员喜欢关闭 `Hadoop` 中的推测执行。

对于 Reduce 任务，关闭推测执行是有益的，因为任意重复的 reduce 任务都必须将取得 map 任务输出作为最先的任务，这可能会大幅度的增加集群上的网络传输。

关闭推测执行的另一种情况是考虑到非幂等任务。然而在很多情况下，将任务写成幂等的并使用 `OutputCommitter` 来提升任务成功时输出到最后位置的速度，这是可行的。

原文:https://data-flair.training/blogs/speculative-execution-in-hadoop-mapreduce/
