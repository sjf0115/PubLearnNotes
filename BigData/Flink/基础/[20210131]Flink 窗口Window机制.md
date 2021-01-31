---
layout: post
author: smartsi
title: Flink 窗口Window机制
date: 2021-01-31 16:40:01
tags:
  - Flink

categories: Flink
permalink: introducing-stream-windows-in-apache-flink
---

数据分析场景见证了批处理到流处理的演变过程。尽管批处理可以作为流处理的一种特殊情况来处理，但分析永无止境的流数据通常需要转变一种思维方式，并使用它自己的专门术语，例如，窗口、At-Least-Once 或者 Exactly-Once 处理语义。

对于刚刚接触流处理的人来说，这种思维方式的转变以及新的专业术语可能会让我们感到非常困惑。但是，Apache Flink 作为一个为生产环境而生的流处理器，具有易于使用并且表达能力很强的 API 来定义高级流分析程序。 Flink 的 API 在数据流上有非常灵活的窗口定义，使其能在其他开源流处理器中脱颖而出。

在这篇文章中，我们主要讨论用于流处理的窗口的概念，介绍 Flink 的内置窗口，并说明其对自定义窗口语义的支持。

## 1. 什么是窗口？它们有什么用？

我们拿交通传感器的例子来说明，传感器每15秒统计通过某个位置的车辆数量。结果流看起来像如下所示：

![](1)

如果现在我们想知道有多少辆车经过这个位置，我们只需简单的将每15秒统计的数量相加即可。但是，传感器流的本质是连续产生数据。像这样的流永远都不会结束，更不可能计算出可以返回的最终和。换一种思路，我们可以滚动计算总和，即为每个输入事件返回一个更新的总和记录。这就会产生新的部分和流：

![](2)

但是，部分求和流可能不是我们想要的，因为它会不断更新计数，更重要的是，某些信息（例如随时间变化）会丢失。因此，我们需要想改一下我们的问题：每分钟通过该位置的汽车数量。这要求我们将流的元素分组为有限的集合，每个集合对应于60秒。此操作称为滚动窗口操作。

![](3)

滚动窗口将流离散化为不重叠的窗口。对于某些应用程序，重要的是窗口不可分离，因为应用程序可能需要平滑的聚合。例如，我们可以每30秒计算最后一分钟通过的汽车数量。这种窗口称为滑动窗口。

![](4)

如上所述，在数据流上定义窗口是非并行操作。这是因为流的每个元素必须由同一窗口算子处理，决定每个元素应归属到哪个窗口中。一个完整流上的 Windows 在 Flink 中称为 AllWindows。对于许多应用程序，数据流可以拆分为多个逻辑流，每个逻辑流都可以应用窗口算子。例如，考虑统计来自多个交通传感器（而不是像前面的示例中的一个传感器）的车辆计，其中每个传感器都会监控一个不同的位置。通过按传感器ID对流进行分组，我们可以并行计算每个位置的窗口流量统计。在 Flink 中，我们将这种分区的窗口简称为 Windows，因为它们是分布式流的常见情况。下图显示了在 (sensorId, count) 流上的滚动窗口。

![](5)

一般来说，窗口在无界流上定义了一组有限的元素。该集合可以基于时间（如我们之前的示例中所示），元素个数，元素个数和时间的组合或一些自定义逻辑将元素分配给窗口。Flink 的 DataStream API 为最常见的窗口操作提供了简洁的算子，并提供了一种通用的窗口机制，该机制允许用户自定义窗口逻辑。在下面的内容中，我们将介绍 Flink 的 Time Windows 和 Count Windows，然后再详细讨论其窗口机制。


## 2. Time Windows

顾名思义，Time Windows（时间窗口）按时间对流元素进行分组。例如，窗口大小为一分钟的滚动窗口将收集一分钟内的元素，并在一分钟后将函数应用于窗口中的所有元素。在 Apache Flink 中定义滚动和滑动时间窗口非常简单：
```java
// Stream of (sensorId, carCnt)
DataStream<Tuple2<String, Long>> vehicleCnt ...

// 滚动窗口
DataStream<Tuple2<String, Long>> tumblingCnt = vehicleCnt
        // 根据sensorId分组
        .keyBy(0)
        // 窗口大小为1分钟的滚动窗口
        .timeWindow(Time.minutes(1))
        // 求和
        .sum(1);

// 滑动窗口
DataStream<Tuple2<String, Long>> slidingCnt = vehicleCnt
        // 根据sensorId分组
        .keyBy(0)
        // 窗口大小为1分钟、滑动步长为30秒的滑动窗口
        .timeWindow(Time.minutes(1), Time.seconds(30))
        // 求和
        .sum(1);
```

我们还没有讨论过 '收集一分钟内的元素' 的确切含义，也可以归结为'流处理器如何解释时间？'这一问题。

Apache Flink 具有三种不同的时间概念，即处理时间，事件时间和摄取时间。具体的可以参阅[Flink 事件时间与处理时间](http://smartsi.club/flink-stream-event-time-and-processing-time.html)。

## 3. Count Windows

除了 Time Windows 外，Apache Flink 还具有 Count Windows（计数窗口）。一个大小为100的滚动计数窗口，将会在一个窗口中收集100个元素，并在添加第100个元素时触发窗口计算。

在 Flink 的 DataStream API 中，滚动和滑动计数窗口如下定义：
```java
// Stream of (sensorId, carCnt)
DataStream<Tuple2<String, Long>> vehicleCnt ...

// 滚动窗口
DataStream<Tuple2<String, Long>> tumblingCnt = vehicleCnt
        // 根据sensorId分组
        .keyBy(0)
        // 100个元素大小的滚动计数窗口
        .countWindow(100)
        // 求和
        .sum(1);

// 滑动窗口
DataStream<Tuple2<String, Long>> slidingCnt = vehicleCnt
        // 根据sensorId分组
        .keyBy(0)
        // 100个元素大小、步长为10个元素的滑动计数窗口
        .countWindow(100, 10)
        // 求和
        .sum(1);
```

## 4. 剖析Flink的窗口机制









原文：[Introducing Stream Windows in Apache Flink](https://flink.apache.org/news/2015/12/04/Introducing-windows.html)
