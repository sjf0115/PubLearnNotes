---
layout: post
author: smartsi
title: Flink Savepoints和Checkpoints的3个不同点
date: 2020-12-25 08:16:17
tags:
  - Flink

categories: Flink
permalink: differences-between-savepoints-and-checkpoints-in-flink
---

在本文中，我们将解释什么是 Savepoint，什么会使用它们，并就它们与 Checkpoint 的区别进行对比分析。


### 1. 什么是Savepoint和Checkpoint

Savepoint 是一项可让我们为整个流应用程序生成"某个时间"点快照的能力。快照包含有关您输入源的位置信息，以及数据源读取到的偏移量信息以及整个应用程序状态信息。我们可以使用 Chandy-Lamport 算法的变体在不停止应用程序的情况下获得全部状态的一致性快照。保存点包含两个主要元素：
- 首先，Savepoint 包括一个包含（通常是很大的）二进制文件的目录，该二进制文件表示在 Savepoint和Checkpoint 生成镜像时流应用程序的整个状态
- 一个（相对较小的）元数据文件，包含指向所有文件的指针（路径），这些文件是保存点的一部分，并存储在所选的分布式文件系统或数据存储中。

> 阅读这篇文章之前，你可以阅读一下[Flink 保存点之回溯时间](http://smartsi.club/flink-stream-turning-back-time-savepoints.html)。

上面所有关于 Savepoints 的内容听起来与我们在之前的文章中对 Checkpoints 的介绍非常相似。Checkpoint 是 Apache Flink 用于故障恢复的内部机制，包括应用程序状态快照以及输入源读取到的偏移量。如果程序发生故障，Flink 会通过从 Checkpoint 加载应用程序状态并从恢复的读取偏移量继续读取来恢复应用程序，就像什么也没发生一样。

> 可以阅读之前一篇关于[Flink如何管理Kafka的消费偏移量](http://smartsi.club/how-flink-manages-kafka-consumer-offsets.html)的文章。

### 2. Savepoint和Checkpoint的3个不同点

Savepoint 和 Checkpoint 是 Apache Flink 作为流处理框架所特有的两个功能。Savepoint 和 Checkpoint 的实现看起来也很相似，但是，这两种功能在以下3种方面有所不同，我们具体看一下。

#### 2.1 目标

从概念上讲，Flink 的 Savepoint 和 Checkpoint 的不同之处很像传统数据库中备份与恢复日志之间的区别。Checkpoint 的主要目标是充当 Flink 中的恢复机制，以确保能从潜在的故障中恢复。相反，Savepoint 的主要目标是充当手动备份之后重启、恢复暂停作业的方法。

#### 2.2 实现

Checkpoint 和 Savepoint 在实现上也有不同。Checkpoint 的设计轻量并快速。它们可能（但不一定必须）充分利用底层状态后端的不同功能尽可能快速地恢复数据。基于 RocksDB 的状态后端可以使用 RocksDB 的内部格式，而不是 Flink 的原生格式进行增量 Checkpoint。加速了 RocksDB 的 Checkpoint 过程，从而使它们成为更轻量级的检查点机制的一个实例。相反，Savepoint 的设计重点是数据的可移植性，并支持对作业做任何更改，这些更改会使数据的生产和恢复成本更高。

#### 2.3 生命周期

Checkpoint 是自动和定期的。它们由 Flink 自动，定期地创建和删除，不需与用户进行交互，以确保在作业意外失败的情况下可以恢复。相反，Savepoint 是由用户手动创建和管理的（即，调度、创建、删除）。

### 3. 何时使用 Savepoint ?

尽管流处理应用程序处理的是连续产生的数据（"运动中"的数据），但在某些情况下，应用程序可能需要重新处理以前处理过的数据。Apache Flink 中的 Savepoint 允许您在以下情况下执行此操作：
- 部署新版本的流应用程序，包括上线新功能，修复Bug或更好的机器学习模型。
- 为应用程序引入 A/B 测试，使用相同的源数据流测试程序的不同版本，从相同的时间点开始测试而不用牺牲先前的状态。
- 在需要更多资源的情况下重新对应用程序扩容。
- 将流应用程序迁移到 Flink 的新版本上，或迁移到另一个集群。

### 4. 结论

Checkpoint 和 Savepoint 是 Apache Flink 中的两个不同功能，可以满足不同的需求，以确保一致性，容错能力，并确保在作业意外失败（使用 Checkpoint）以及在升级、修复Bug、迁移或者 A/B 测试（使用 Savepoint）时应用程序状态能够保持不变。这两个功能的结合确保应用程序的状态在不同的情况和环境下都能保持不变。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[3 differences between Savepoints and Checkpoints in Apache Flink](https://www.ververica.com/blog/differences-between-savepoints-and-checkpoints-in-flink)
