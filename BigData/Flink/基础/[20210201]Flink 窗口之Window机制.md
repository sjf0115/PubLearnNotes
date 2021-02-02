---
layout: post
author: smartsi
title: Flink 窗口之Window机制
date: 2021-02-01 16:40:01
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

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/introducing-stream-windows-in-apache-flink-1.png?raw=true)

如果现在我们想知道有多少辆车经过这个位置，我们只需简单的将每15秒统计的数量相加即可。但是，传感器流的本质是连续产生数据。像这样的流永远都不会结束，更不可能计算出可以返回的最终和。换一种思路，我们可以滚动计算总和，即为每个输入事件返回一个更新的总和记录。这就会产生新的部分和流：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/introducing-stream-windows-in-apache-flink-2.png?raw=true)

但是，部分求和流可能不是我们想要的，因为它会不断更新计数，更重要的是，某些信息（例如随时间变化）会丢失。因此，我们需要想改一下我们的问题：每分钟通过该位置的汽车数量。这要求我们将流的元素分组为有限的集合，每个集合对应于60秒。此操作称为滚动窗口操作。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/introducing-stream-windows-in-apache-flink-3.png?raw=true)

滚动窗口将流离散化为不重叠的窗口。对于某些应用程序，重要的是窗口不可分离，因为应用程序可能需要平滑的聚合。例如，我们可以每30秒计算最后一分钟通过的汽车数量。这种窗口称为滑动窗口。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/introducing-stream-windows-in-apache-flink-4.png?raw=true)

如上所述，在数据流上定义窗口是非并行操作。这是因为流的每个元素必须由同一窗口算子处理，决定每个元素应归属到哪个窗口中。一个完整流上的 Windows 在 Flink 中称为 AllWindows。对于许多应用程序，数据流可以拆分为多个逻辑流，每个逻辑流都可以应用窗口算子。例如，考虑统计来自多个交通传感器（而不是像前面的示例中的一个传感器）的车辆计，其中每个传感器都会监控一个不同的位置。通过按传感器ID对流进行分组，我们可以并行计算每个位置的窗口流量统计。在 Flink 中，我们将这种分区的窗口简称为 Windows，因为它们是分布式流的常见情况。下图显示了在 (sensorId, count) 流上的滚动窗口。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/introducing-stream-windows-in-apache-flink-5.png?raw=true)

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

Flink 的内置 Time Windows 和 Count Windows 覆盖了各种常见的窗口用例。但是，有些应用程序还是需要实现自定义窗口逻辑，而 Flink 的内置窗口无法解决这些逻辑。为了同时也支持定制的窗口语义的应用程序，DataStream API 公开了窗口机制内部的接口。这些接口可以非常精细地控制窗口的创建和触发。

下图描述了 Flink 的窗口机制，并介绍了其中涉及的组件。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/introducing-stream-windows-in-apache-flink-6.png?raw=true)

到达窗口算子的元素将传递给 WindowAssigner。 WindowAssigner 将元素分配给一个或多个窗口，也可能会创建新窗口。窗口本身只是一系列元素的标识符，并且可以提供一些可选的元信息，例如，在使用 TimeWindow 时的开始和结束时间。请注意，可以将元素添加到多个窗口中，这也意味着可以同时存在多个窗口。

每个窗口都有一个 Trigger，决定了何时触发计算或清除该窗口。当先前注册的计时器到点时，对于分配到窗口中的每个元素都会调用 Trigger。对于每个事件，Trigger 都可以决定触发，清除（清除窗口并丢弃其内容），或者触发并清除窗口。仅触发的 Trigger 会计算窗口并保持其原样，即所有元素都保留在窗口中，并在下次触发时再次计算（不删除元素）。一个窗口可以被触发多次计算，并且一直存在直到清除为止。请注意，在清除窗口之前，窗口会一值消耗内存。

触发 Trigger 时，可以将窗口元素列表提供给可选的 Evictor。Evictor 遍历列表，可以决定从列表的开头删除一些元素，即删除一些首先进入窗口的元素。其它元素则提供给窗口计算函数。如果没有定义 Evictor，则 Trigger 直接将所有窗口元素交给窗口计算函数。

窗口计算函数接收一个窗口的元素（可能先由 Evictor 进行过滤），并为该窗口计算一个或多个结果元素。DataStream API 可以接受不同类型的计算函数，包括预定义的聚合函数，例如，sum()，min()，max() 以及 ReduceFunction，FoldFunction 或 WindowFunction。WindowFunction 是最通用的窗口计算函数，接收窗口对象（即窗口的元数据），窗口元素列表以及窗口键（如果是 Keyed Window）作为参数。

这些是构成 Flink 的窗口机制的组件。

## 5. 结论

对于现代流处理器来说，在连续数据流上支持各种类型的窗口是必不可少的。Apache Flink 是一种流处理器，具有非常强大的功能，其中就包括一种非常灵活的机制来构建和计算连续数据流上的窗口。Flink 为常见用例提供了内置的窗口算子，以及允许用户自定义窗口逻辑。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

推荐订阅：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-jk.jpeg?raw=true)

原文：[Introducing Stream Windows in Apache Flink](https://flink.apache.org/news/2015/12/04/Introducing-windows.html)
