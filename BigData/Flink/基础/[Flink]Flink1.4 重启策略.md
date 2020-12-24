---
layout: post
author: sjf0115
title: Flink1.4 重启策略
date: 2018-01-04 16:36:01
tags:
  - Flink
  - Flink 基础

categories: Flink
permalink: flink-restart-strategy
---

`Flink`支持不同的重启策略，重启策略控制在作业失败后如何重启。可以使用默认的重启策略启动集群，这个默认策略在作业没有特别指定重启策略时使用。如果在提交作业时指定了重启策略，那么此策略将覆盖集群的默认配置策略。

### 1. 概述

默认的重启策略通过`Flink`的配置文件`flink-conf.yaml`进行设置。配置参数`restart-strategy`定义了采取哪种策略。如果未启用检查点，那么将使用`不重启`策略。如果启用检查点且重启策略尚未配置，则固定延迟重启策略与`Integer.MAX_VALUE`一起使用进行尝试重启。请参阅下面可用的重启策略列表以了解支持哪些值。

每个重启策略都有自己的一套控制其行为的参数。这些值也在配置文件中配置。每个重启策略的描述都包含有关各个配置值的更多信息。

重启策略|值
---|---
固定延迟重启策略|fixed-delay
失败率重启策略|failure-rate
不重启策略|none

除了定义一个默认的重启策略之外，还可以为每个`Flink`作业定义一个指定的重启策略。此重启策略通过调用`ExecutionEnvironment`上的`setRestartStrategy`方法以编程的方式进行设置。请注意，这也适用于`StreamExecutionEnvironment`。

以下示例显示了如何为作业设置固定延迟重启策略。如果发生故障，系统将尝试每10s重新启动一次作业，最多重启3次。

Java版本:
```java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
  3, // number of restart attempts
  Time.of(10, TimeUnit.SECONDS) // delay
));
```

Scala版本:
```
val env = ExecutionEnvironment.getExecutionEnvironment()
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
  3, // number of restart attempts
  Time.of(10, TimeUnit.SECONDS) // delay
))
```

### 2. 重启策略

下面介绍几种重启策略的配置选项。

#### 2.1 固定延迟重启策略

固定延迟重启策略尝试一定次数来重新启动作业。如果超过最大尝试次数，那么作业最终将失败。在两次连续的尝试重启之间，重启策略会等待一段固定的时间(译者注:连续重启时间间隔)。

通过在`flink-conf.yaml`中设置以下配置参数，可以将此策略默认启用：
```
restart-strategy: fixed-delay
```

配置参数|描述|默认值
---|---|---
`restart-strategy.fixed-delay.attempts`|在声明作业失败之前，`Flink`重试执行的次数|1或者如果启用检查点，则为`Integer.MAX_VALUE`
`restart-strategy.fixed-delay.delay`|延迟重试意味着在执行失败后，重新执行不会立即开始，而只会在某个延迟之后开始。当程序与外部系统进行交互时，延迟重试会很有帮助|`akka.ask.timeout`，或10s(如果通过检查点激活)

Example:
```
restart-strategy.fixed-delay.attempts: 3
restart-strategy.fixed-delay.delay: 10 s
```
固定延迟重启策略也可以通过编程来设置：

Java版本:
```Java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
  3, // number of restart attempts
  Time.of(10, TimeUnit.SECONDS) // delay
));
```
Scala版本:
```
val env = ExecutionEnvironment.getExecutionEnvironment()
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(
  3, // number of restart attempts
  Time.of(10, TimeUnit.SECONDS) // delay
))
```

#### 2.2 失败率重启策略

失败率重启策略在失败后重新启动作业，但当超过失败率(每个时间间隔的失败)时，作业最终会失败。在两次连续的重启尝试之间，重启策略会等待一段固定的时间。

通过在`flink-conf.yaml`中设置以下配置参数，可以将此策略默认启用:

配置参数|描述|默认值
---|---|---
`restart-strategy.failure-rate.max-failures-per-interval`|在一个作业声明失败之前，在给定时间间隔内最大的重启次数|1
`restart-strategy.failure-rate.failure-rate-interval`|计算失败率的时间间隔|1分钟
`restart-strategy.failure-rate.delay`|两次连续重启尝试之间的时间间隔|`akka.ask.timeout`

Example:
```
restart-strategy.failure-rate.max-failures-per-interval: 3
restart-strategy.failure-rate.failure-rate-interval: 5 min
restart-strategy.failure-rate.delay: 10 s
```
失败率重新启动策略也可以通过编程来设置：

Java版本:
```java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
env.setRestartStrategy(RestartStrategies.failureRateRestart(
  3, // max failures per interval
  Time.of(5, TimeUnit.MINUTES), //time interval for measuring failure rate
  Time.of(10, TimeUnit.SECONDS) // delay
));
```
Scala版本:
```
val env = ExecutionEnvironment.getExecutionEnvironment()
env.setRestartStrategy(RestartStrategies.failureRateRestart(
  3, // max failures per unit
  Time.of(5, TimeUnit.MINUTES), //time interval for measuring failure rate
  Time.of(10, TimeUnit.SECONDS) // delay
))
```

#### 2.3 不重启策略

作业直接失败，不会尝试重新启动:
```
restart-strategy: none
```
不重启策略也可以通过编程来设置：

Java版本:
```java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
env.setRestartStrategy(RestartStrategies.noRestart());
```
Scala版本:
```
val env = ExecutionEnvironment.getExecutionEnvironment()
env.setRestartStrategy(RestartStrategies.noRestart())
```

#### 2.4 回退重启策略

使用集群定义的重启策略(The cluster defined restart strategy is used. )。这有助于启用检查点的流式传输程序。默认情况下，如果没有定义其他重启策略，则选择固定延时重启策略。

备注:
```
Flink版本:1.4
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/restart_strategies.html
