---
layout: post
author: sjf0115
title: Flink 任务失败重启与恢复策略
date: 2021-01-02 17:22:01
tags:
  - Flink

categories: Flink
permalink: flink-restart-strategy
---

> Flink版本：1.11.0

当任务失败时，Flink 需要重新启动失败的任务以及受到影响的任务，以将作业恢复到正常状态。重新启动策略和故障恢复策略用于控制任务重新启动。重新启动策略决定了是否以及何时重新启动失败/受影响的任务。故障恢复策略决定应重新启动哪些任务以恢复作业。

## 1. 重启策略

Flink 支持不同的重启策略，在作业没有特别指定重启策略时，使用默认的重启策略启动集群。如果在提交作业时指定了重启策略，那么此策略将覆盖集群的默认配置策略。

默认重启策略通过 Flink 的配置文件 flink-conf.yaml 进行配置。配置参数 restart-strategy 决定了采取哪种策略。如果未启用 Checkpoint，那么将使用不重启策略。如果启用了 Checkpoint，但是并没有配置重启策略，那么将使用固定间隔重启策略，其中 Integer.MAX_VALUE 是尝试重启的最大次数。

每个重启策略都有自己的一套控制其行为的参数。这些值也在配置文件中配置。下面看一下有哪些重启策略：

重启策略|值
---|---
固定间隔重启策略| fixeddelay, fixed-delay
失败率重启策略| failurerate, failure-rate
不重启策略| none, off, disable

除了定义一个默认的重启策略之外，还可以为每个 Flink 作业单独指定一个重启策略。可以通过以编程的方式调用 ExecutionEnvironment 上的 setRestartStrategy 方法进行配置。请注意，这也适用于 StreamExecutionEnvironment。

以下示例显示了如何为作业设置固定间隔重启策略。如果作业发生故障，系统将尝试每10s重新启动一次作业，最多重启3次：
```java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
  3, // number of restart attempts
  Time.of(10, TimeUnit.SECONDS) // delay
));
```

### 1.1 固定间隔重启策略

固定间隔重启策略会一直尝试重新启动作业直到到达指定次数。如果超过最大尝试次数，那么作业最终会失败。每次重启之后都会等待一段固定间隔时间。通过在 flink-conf.yaml 中配置如下参数，可以将重启策略默认为固定间隔重启策略：
```
restart-strategy: fixed-delay
```

配置参数|描述|默认值
---|---|---
restart-strategy.fixed-delay.attempts| 最多尝试重启次数 | 1
restart-strategy.fixed-delay.delay | 连续重启的时间间隔 | 1s

Example:
```
restart-strategy.fixed-delay.attempts: 3
restart-strategy.fixed-delay.delay: 10 s
```

固定间隔重启策略也可以通过编程来配置：
```Java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
  3, // number of restart attempts
  Time.of(10, TimeUnit.SECONDS) // delay
));
```

### 1.2 失败率重启策略

失败率重启策略在作业失败后会重新启动作业，只有当每个时间区间内失败次数超过指定次数时，作业才最终会失败。失败率重启策略跟固定间隔重启策略一样，每次重启之后都会等待一段固定间隔时。不同的是失败率重启策略阈值设置了一个时间区间，只有当时间区间内超过指定次数时才失败。通过在 flink-conf.yaml 中配置如下参数，可以将失败率重启策略设置为默认重启策略:
```
restart-strategy: failure-rate
```

配置参数|描述|默认值
---|---|---
restart-strategy.failure-rate.delay | 连续重启的时间间隔 | 1 s
restart-strategy.failure-rate.failure-rate-interval | 计算失败率的时间间隔 | 1 min
restart-strategy.failure-rate.max-failures-per-interval | 指定时间区间内最多尝试重启次数 | 1

Example:
```
restart-strategy.failure-rate.max-failures-per-interval: 3
restart-strategy.failure-rate.failure-rate-interval: 5 min
restart-strategy.failure-rate.delay: 10 s
```
失败率重新启动策略也可以通过编程来设置：
```java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
env.setRestartStrategy(RestartStrategies.failureRateRestart(
  3, // max failures per interval
  Time.of(5, TimeUnit.MINUTES), //time interval for measuring failure rate
  Time.of(10, TimeUnit.SECONDS) // delay
));
```

### 1.3 不重启策略

作业直接失败，不会重启:
```
restart-strategy: none
```

不重启策略也可以通过编程来设置：
```java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
env.setRestartStrategy(RestartStrategies.noRestart());
```

## 2. 故障恢复策略

Flink 支持不同的故障恢复策略，可以通过 Flink 的配置文件 flink-conf.yaml 中的 jobmanager.execution.failover-strategy 配置参数进行配置：
```
jobmanager.execution.failover-strategy: region
```

Failover策略 | 默认值
---|---
重启所有故障恢复策略 | full
重启流水线区域故障恢复策略 | region

### 2.1 重启所有故障恢复策略

此策略会重新启动作业中所有任务以从失败任务中恢复：
```
jobmanager.execution.failover-strategy: full
```

### 2.2 重启流水线区域故障恢复策略

该策略会将作业中的所有 Task 划分为几个 Region。当有 Task 发生故障时，它会尝试找出进行故障恢复需要重启的最小 Region 集合。相比于全部重启的故障恢复策略，这种策略在一定场景下重启的 Task 会少一些。

Region 是指以 Pipelined 形式进行数据交换的 Task 集合。也就是说，Batch 形式的数据交换会构成 Region 的边界。
- DataStream 和 流式 Table/SQL 作业的所有数据交换都是 Pipelined 形式。
- 批处理式 Table/SQL 作业的所有数据交换默认都是 Batch 形式的。
- DataSet 作业中的数据交换形式会根据 ExecutionConfig 中配置的 ExecutionMode 决定。

需要重启的 Region 的判断逻辑如下：
- 出错 Task 所在 Region 需要重启。
- 如果要重启的 Region 需要消费的数据有部分无法访问（丢失或损坏），产出该部分数据的 Region 也需要重启。
- 需要重启的 Region 的下游 Region 也需要重启。这是出于保障数据一致性的考虑，因为一些非确定性的计算或者分发会导致同一个 Result Partition 每次产生时包含的数据都不相同。

原文:[Task Failure Recovery](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/task_failure_recovery.html)
