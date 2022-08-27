---
layout: post
author: sjf0115
title: Flink 窗口分配器 WindowAssigner
date: 2018-02-28 17:17:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-windows-overall
---

Windows(窗口)是处理无限数据流的核心。窗口将流分解成有限大小的"桶"，在上面可以进行各种计算。本文将重点介绍 Flink 中的窗口分配器 WindowAssigner。新建一个窗口算子一般必须要指定两个窗口组件：
- 一个用于决定输入流中的元素如何划分的窗口分配器 WindowAssigner。窗口分配器将元素分配到一个或者多个窗口中。
- 另一个是用于处理分配到窗口中元素的窗口函数 WindowFunction。

如下代码展示了如何在 KeyedStream 和非 KeyedStream 上指定窗口分配器和窗口函数（以及可选的触发器和剔除器，后面文章会具体介绍）的示例：
```java
// keyedStream
keyedStream
       .keyBy(...)          <-  keyed versus non-keyed windows
       .window(...)         <-  必选: 窗口分配器
      [.trigger(...)]       <-  可选: 窗口触发器
      [.evictor(...)]       <-  可选: 窗口剔除器
      [.allowedLateness()]  <-  可选：是否允许延迟
       .reduce/fold/apply() <-  必选: 窗口函数

// 非keyedStream
stream
      .windowAll(...)      <-  必选: 窗口分配器
     [.trigger(...)]       <-  可选: 窗口触发器
     [.evictor(...)]       <-  可选: 窗口剔除器
     [.allowedLateness()]  <-  可选：是否允许延迟
      .reduce/fold/apply() <-  必选: 窗口函数
```

对于在 KeyedStream 上使用窗口，要做的第一件事就是为数据流指定 key，并且必须在定义窗口之前完成。直接调用 `keyBy()` 方法就可以将无限数据流拆分成 KeyedStream。在 KeyedStream 上，事件的任何属性都可以用作 key，如何指定 key 可以参阅 [Flink 指定 keys 的几种方法](https://smartsi.blog.csdn.net/article/details/126417116?spm=1001.2014.3001.5502)。对于非 KeyedStream，原始数据流不会被拆分成多个逻辑 Keyd 数据流，并且所有窗口逻辑将由单个任务执行，即并行度为1。

在确定数据流是否指定 key 之后，下一步就是定义窗口分配器 WindowAssigners。窗口分配器定义了元素如何分配给窗口，即指定元素分配给哪个窗口。对于 KeyedStream，可以通过在 `window()` 指定你选择的窗口分配器来完成，而非 KeyedStream 则需要使用 `windowAll()`。窗口分配器负责将每个传入的元素分配给一个或多个窗口。Flink 内置了一些用于解决常见问题的窗口分配器，例如，滚动窗口，滑动窗口，会话窗口以及全局窗口等。你还可以通过继承 `WindowAssigner` 类实现自定义窗口分配器。所有内置窗口分配器(全局窗口除外)都会根据时间将元素分配给窗口，可以是处理时间，也可以是事件时间。

> 请参阅[Flink 事件时间与处理时间](https://smartsi.blog.csdn.net/article/details/126554454)，了解处理时间和事件时间之间的差异。

基于时间的窗口会有开始时间戳(闭区间)和结束时间戳(开区间)，它们共同描述了窗口的大小。在代码中，Flink 在使用基于时间的窗口时使用 TimeWindow，该窗口具有用于查询开始和结束时间戳的方法，以及用于返回给定窗口的最大允许时间戳的 maxTimestamp() 方法。

接下来我们将介绍 DataStream API 中的多种内置窗口分配器以及如何使用它们来定义窗口算子。

> 下面分配器运行图中，紫色圆圈表示数据流中的元素，根据某些 key 进行分区（在我们这个例子中为 user1，user2 和 user3），x轴显示时间进度。

## 1. 滚动窗口

滚动窗口分配器将每个元素分配给固定大小且不重叠的窗口。例如，如果指定大小为 10 分钟的滚动窗口，那么每 10 分钟都会启动一个新窗口，如下图所示:

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-overall-1.png?raw=true)

DataStream 针对事件时间和处理时间的滚动窗口分别提供了对应的分配器 TumblingEventTimeWindows 和 TumblingProcessingTimeWindows。


以下代码显示如何使用滚动窗口：
```java
DataStream<T> input = ...;

// 基于事件时间的滚动窗口
input
    .keyBy(<key selector>)
    .window(TumblingEventTimeWindows.of(Time.seconds(5)))
    .<windowed transformation>(<window function>);

// 基于处理时间的滚动窗口
input
    .keyBy(<key selector>)
    .window(TumblingProcessingTimeWindows.of(Time.seconds(5)))
    .<windowed transformation>(<window function>);

// 基于事件时间的每日滚动窗口会-8小时的偏移。
input
    .keyBy(<key selector>)
    .window(TumblingEventTimeWindows.of(Time.days(1), Time.hours(-8)))
    .<windowed transformation>(<window function>);
```

也可以通过使用 `Time.milliseconds(x)`， `Time.seconds(x)`， `Time.minutes(x)` 来指定时间间隔。

如上面例子中所示，滚动窗口分配器还可以使用一个可选的偏移量参数，用来改变窗口的对齐方式。例如，没有偏移量的情况下，窗口大小为1小时的滚动窗口与 `epoch` （指的是一个特定的时间：`1970-01-01 00:00:00 UTC`）对齐，那么你将获得如`1:00:00.000 - 1:59:59.999`，`2:00:00.000 - 2:59:59.999` 之类的窗口。如果你想改变，可以给一个偏移量。以15分钟的偏移量为例，那么你将获得`1:15:00.000 - 2:14:59.999`，`2:15:00.000 - 3:14:59.999` 之类的窗口。偏移量的一个重要应用是将窗口调整为 `timezones` 而不是 `UTC-0`。例如，在中国，你必须指定 `Time.hours(-8)` 的偏移量。

## 2. 滑动窗口

滑动窗口分配器将每个元素分配给固定窗口大小的窗口。与滚动窗口分配器类似，窗口的大小由 `window size` 参数配置。还有一个`window slide`参数用来控制滑动窗口的滑动大小。因此，如果滑动大小小于窗口大小，则滑动窗口会重叠。在这种情况下，一个元素会被分配到多个窗口中。

例如，窗口大小为10分钟，滑动大小为5分钟的窗口。这样，每5分钟会生成一个窗口，每个窗口包含最后10分钟内到达的事件，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-overall-2.png?raw=true)

Java版本:
```java
DataStream<T> input = ...;

// 基于事件时间的滑动窗口
input
    .keyBy(<key selector>)
    .window(SlidingEventTimeWindows.of(Time.seconds(10), Time.seconds(5)))
    .<windowed transformation>(<window function>);

// 基于处理时间的滑动窗口
input
    .keyBy(<key selector>)
    .window(SlidingProcessingTimeWindows.of(Time.seconds(10), Time.seconds(5)))
    .<windowed transformation>(<window function>);

// 基于处理时间的滑动窗口 偏移量-8
input
    .keyBy(<key selector>)
    .window(SlidingProcessingTimeWindows.of(Time.hours(12), Time.hours(1), Time.hours(-8)))
    .<windowed transformation>(<window function>);
```

Scala版本:
```scala
val input: DataStream[T] = ...

// sliding event-time windows
input
    .keyBy(<key selector>)
    .window(SlidingEventTimeWindows.of(Time.seconds(10), Time.seconds(5)))
    .<windowed transformation>(<window function>)

// sliding processing-time windows
input
    .keyBy(<key selector>)
    .window(SlidingProcessingTimeWindows.of(Time.seconds(10), Time.seconds(5)))
    .<windowed transformation>(<window function>)

// sliding processing-time windows offset by -8 hours
input
    .keyBy(<key selector>)
    .window(SlidingProcessingTimeWindows.of(Time.hours(12), Time.hours(1), Time.hours(-8)))
    .<windowed transformation>(<window function>)
```

## 3. 会话窗口

会话窗口分配器通过活动会话对元素进行分组。与滚动窗口和滑动窗口相比，会话窗口不会重叠，也没有固定的开始和结束时间。当会话窗口在一段时间内没有接收到元素时会关闭。会话窗口分配器需要配置一个会话间隙，定义了所需的不活动时长。当此时间段到期时，当前会话关闭，后续元素被分配到新的会话窗口。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-overall-3.png?raw=true)

Java版本:
```java
DataStream<T> input = ...;

// 基于事件时间的会话窗口
input
    .keyBy(<key selector>)
    .window(EventTimeSessionWindows.withGap(Time.minutes(10)))
    .<windowed transformation>(<window function>);

// 基于处理时间的会话窗口
input
    .keyBy(<key selector>)
    .window(ProcessingTimeSessionWindows.withGap(Time.minutes(10)))
    .<windowed transformation>(<window function>);
```

Scala版本:
```scala
val input: DataStream[T] = ...

// event-time session windows
input
    .keyBy(<key selector>)
    .window(EventTimeSessionWindows.withGap(Time.minutes(10)))
    .<windowed transformation>(<window function>)

// processing-time session windows
input
    .keyBy(<key selector>)
    .window(ProcessingTimeSessionWindows.withGap(Time.minutes(10)))
    .<windowed transformation>(<window function>)
```

由于会话窗口没有固定的开始时间和结束时间，因此它们的执行与滚动窗口和滑动窗口不同。在内部，会话窗口算子为每个到达记录创建一个新窗口，如果它们之间的距离比定义的间隙要小，那么窗口会合并在一起。为了能合并，会话窗口算子需要一个合并触发器和合并窗口函数，例如，ReduceFunction 、AggregateFunction 或 ProcessWindowFunction。

## 4. 全局窗口

全局窗口分配器将具有相同 key 的所有元素分配给同一个全局窗口。仅当我们指定自定义触发器时，窗口才起作用。否则，不会执行任何计算，因为全局窗口没有我们可以处理聚合元素的自然结束的点（译者注：即本身自己不知道窗口的大小，计算多长时间的元素）。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-overall-4.png?raw=true)

Java版本:
```java
DataStream<T> input = ...;

input
    .keyBy(<key selector>)
    .window(GlobalWindows.create())
    .<windowed transformation>(<window function>);
```

Scala版本:
```scala
val input: DataStream[T] = ...

input
    .keyBy(<key selector>)
    .window(GlobalWindows.create())
    .<windowed transformation>(<window function>)
```

### 1. 窗口生命周期

一旦属于这个窗口的第一个元素到达，就会创建该窗口，当时间(事件时间或处理时间)到达规定结束时间加上用户指定的可允许延迟的时间后，窗口将会被删除。举个例子，使用基于事件时间的窗口策略，每隔5分钟创建一个滚动窗口，并且允许可以有1分钟的延迟时间。当第一个带有时间戳的元素位于 12:00 至 12:05 之间时，Flink 创建一个 12:00 至 12:05 的新窗口，当时间戳到达 12:06 时，窗口将被删除。Flink 仅保证对基于时间的窗口进行删除，并不适用于其他类型的窗口，例如，全局窗口。

除此之外，每个窗口都有一个触发器(Trigger)和一个函数(例如 `WindowFunction`， `ReduceFunction` 或 `FoldFunction`)。函数用于窗口的计算，而触发器决定了窗口什么时候调用该函数。触发策略可能类似于"当窗口中元素个数大于4时" 或 "当 `watermark` 到达窗口末尾时"。触发器还可以决定在什么时候清除窗口内容（创建窗口以及删除窗口之间的任何时间点）。在这里，清除仅指清除窗口中的元素，而不是窗口（窗口元数据）。这意味着新数据仍然可以添加到窗口中。

除此之外，你还可以指定一个 Evictor 来删除窗口中的元素（在触发器触发之后以及在使用该函数之前或之后）。










原文：[Windows](https://ci.apache.org/projects/flink/flink-docs-release-1.12/dev/stream/operators/windows.html#windows)
