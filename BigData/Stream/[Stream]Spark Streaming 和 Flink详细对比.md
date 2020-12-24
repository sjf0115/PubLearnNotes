---
layout: post
author: 浪尖
title: Spark Streaming 和 Flink 详细对比
date: 2018-04-25 18:28:01
tags:
  - Stream

categories: Stream
permalink: stream-spark-streaming-vs-flink
---

本文从编程模型、任务调度、时间机制、Kafka 动态分区的感知、容错及处理语义、背压等几个方面对比 Spark Stream  与 Flink，希望对有实时处理需求业务的企业端用户在框架选型有所启发。

### 1. 编程模型

#### 1.1 运行角色

Spark Streaming 运行时的角色(standalone 模式)主要有：
- Master:主要负责整体集群资源的管理和应用程序调度；
- Worker:负责单个节点的资源管理，driver 和 executor 的启动等；
- Driver:用户入口程序执行的地方，即 SparkContext 执行的地方，主要是 DGA 生成、stage 划分、task 生成及调度；
- Executor:负责执行 task，反馈执行状态和执行结果。

Flink 运行时的角色(standalone 模式)主要有:
- Jobmanager: 协调分布式执行，他们调度任务、协调 checkpoints、协调故障恢复等。至少有一个 JobManager。高可用情况下可以启动多个 JobManager，其中一个选举为 leader，其余为 standby；
- Taskmanager: 负责执行具体的 tasks、缓存、交换数据流，至少有一个 TaskManager；
- Slot: 每个 task slot 代表 TaskManager 的一个固定部分资源，Slot 的个数代表着 taskmanager 可并行执行的 task 数。


















原文：[Spark Streaming 和 Flink 详细对比](https://mp.weixin.qq.com/s/jllAegJMYh_by95FhHt0jA)
