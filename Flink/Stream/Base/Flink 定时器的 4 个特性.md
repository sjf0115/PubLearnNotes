---
layout: post
author: smartsi
title: Flink 定时器的 4 个特性
date: 2021-06-13 20:17:21
tags:
  - Flink

categories: Flink
permalink: 4-characteristics-of-timers-in-apache-flink
---

本文介绍了在 Flink 中使用定时器的一些基本概念和注意事项。开发人员可以使用 Flink 的 ProcessFunction 算子来注册自己的定时器，该算子可以访问流应用程序的一些基本构建块，例如：
- 事件（流元素）
- 状态（容错，一致性，仅在 KeyedStream 上应用）
- 定时器（事件时间和处理时间，仅在 KeyedStream 上应用）

有关 Flink ProcessFunction 的更多信息，请参考 [Flink 如何使用 ProcessFunction](http://smartsi.club/how-to-user-process-function-of-flink.html)。

### 1. 什么是定时器

定时器可以让 Flink 流处理程序对处理时间和事件时间的变化作出反应。我们之前的一篇[文章](https://smartsi.blog.csdn.net/article/details/126554454)比较详细地介绍了 Flink 中不同概念的时间以及说明了处理时间、事件时间以及摄入时间之间的差异。在使用定时器处理事件流，每次调用 processElement() 时，我们可以借助 Context 对象访问元素的事件时间戳和 TimerService。然后我们使用 TimerService 为将来的事件时间/处理时间实例注册回调。这样之后，一旦到达定时器的指定时刻，就会调用 onTimer() 方法。

onTimer() 回调函数可能会在不同时间点被调用，这首先取决于使用处理时间还是事件时间来注册定时器。特别是：
- 使用处理时间注册定时器时，当服务器的系统时间到达定时器的时间戳时，就会调用 onTimer() 方法。
- 使用事件时间注册定时器时，当算子的 Watermark 到达或超过定时器的时间戳时，就会调用 onTimer() 方法。

与 processElement() 方法类似，onTimer() 回调函数中对状态的访问也仅局限于当前 key（即注册定时器的那个 key）。值得注意的是，onTimer() 和 processElement() 调用都是同步调用，因此同时在 onTimer() 和 processElement() 方法中访问状态以及进行修改都是安全的。

### 2. 四个基本特征

下面我们讨论 Flink 中定时器的4个基本特征，在使用它们之前应该记住这些特征：

#### 2.1 定时器只在 KeyedStream 上注册

由于定时器是按 key 注册和触发的，因此 KeyedStream 是任何操作和函数使用定时器的先决条件。

#### 2.2 定时器进行重复数据删除

TimerService 会自动对定时器进行重复数据的删除，因此每个 key 和时间戳最多只能有一个定时器。这意味着当为同一个 key 或时间戳注册多个定时器时，onTimer() 方法只会调用一次。

#### 2.3 对定时器Checkpoint

定时器也会进行Checkpoint，就像任何其他 Managed State 一样。从 Flink 检查点或保存点恢复作业时，在状态恢复之前就应该触发的定时器会被立即触发。

#### 2.4 删除定时器

从 Flink 1.6 开始，就可以对定时器进行暂停以及删除。如果你使用的是比 Flink 1.5 更早的 Flink 版本，那么由于有许多定时器无法删除或停止，所以可能会遇到检查点性能不佳的问题。

![](img-4-characteristics-of-timers-in-apache-flink-1.png)

你可以使用如下命令停止一个处理时间定时器：
```java
long timestampOfTimerToStop = ... 
ctx.timerService().deleteProcessingTimeTimer(timestampOfTimerToStop);
```
你还可以使用如下命令停止一个事件时间定时器：
```java
long timestampOfTimerToStop = ...
ctx.timerService().deleteEventTimeTimer(timestampOfTimerToStop);
```
值得一提的是，如果没有给指定时间戳注册定时器，那么停止定时器不会起任何效果。

英译对照:
- 定时器: Timers
- 状态: state
- 摄入时间: Ingestion Time
- 检查点: checkpoint
- 保存点: savepoint

原文:[4 characteristics of Timers in Apache Flink to keep in mind](https://www.ververica.com/blog/4-characteristics-of-timers-in-apache-flink)
