---
layout: post
author: sjf0115
title: Flink1.4 图解Watermark
date: 2018-01-15 14:47:01
tags:
  - Flink
  - Flink Stream

categories: Flink
permalink: flink-stream-graphic-watermark
---

如果你正在构建实时流处理应用程序，那么事件时间处理是你迟早必须使用的功能之一。因为在现实世界的大多数用例中，消息到达都是无序的，应该有一些方法，通过你建立的系统知道消息可能延迟到达，并且有相应的处理方案。在这篇博文中，我们将看到为什么我们需要事件时间处理，以及我们如何在ApacheFlink中使用它。

`EventTime`是事件在现实世界中发生的时间，`ProcessingTime`是Flink系统处理该事件的时间。要了解事件时间处理的重要性，我们首先要建立一个基于处理时间的系统，看看它的缺点。

我们创建一个大小为10秒的滑动窗口，每5秒滑动一次，在窗口结束时，系统将发送在此期间收到的消息数。 一旦了解了`EventTime`处理在滑动窗口如何工作，那么了解其在滚动窗口中如何工作也就不是难事。所以让我们开始吧。

### 1. 基于处理时间的系统

在这个例子中，我们期望消息具有一定格式的值，时间戳就是消息的那个值，同时时间戳是在源产生此消息的时间。由于我们正在构建基于处理时间的系统，因此以下代码忽略了时间戳部分。

我们需要知道消息中应包含消息产生时间是很重要的。Flink或任何其他系统不是一个魔术盒，可以以某种方式自己生成这个产生时间。稍后我们将看到，事件时间处理提取此时间戳信息来处理延迟消息。

```
val text = senv.socketTextStream("localhost", 9999)
val counts = text.map {(m: String) => (m.split(",")(0), 1) }
    .keyBy(0)
    .timeWindow(Time.seconds(10), Time.seconds(5))
    .sum(1)
counts.print
senv.execute("ProcessingTime processing example")
```

#### 1.1 消息无延迟到达

假设源分别在第13秒产生两个类型a的消息以及在第16秒产生一个消息。(小时和分钟不重要，因为窗口大小只有10秒)。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E5%9B%BE%E8%A7%A3%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8EWatermarks-0.png?raw=true)

这些消息将落入如下所示窗口中。前两个在第13秒产生的消息将落入窗口1`[5s-15s]`和窗口2`[10s-20s]`中，第三个在第16秒产生的消息将落入窗口2`[10s-20s]`和窗口3`[15s-25s]`中。每个窗口得到的最终计数分别为(a，2)，(a，3)和(a，1)。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E5%9B%BE%E8%A7%A3%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8EWatermarks-2.png?raw=true)

该输出跟预期的输出是一样的。现在我们看看当一个消息延迟到达系统时会发生什么。

#### 1.2 消息延迟到达

现在假设其中一条消息(在第13秒产生)可能由于网络拥塞延迟6秒(第19秒到达)。你能猜测出这个消息会落入哪个窗口？

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E5%9B%BE%E8%A7%A3%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8EWatermarks-3.png?raw=true)

延迟的消息落入窗口2和窗口3中，因为19在10-20和15-25之间。窗口2的计算没有任何问题(因为消息本应该落入这个窗口)，但是它影响了窗口1和窗口3的计算结果。现在我们将尝试使用基于`EventTime`处理来解决这个问题。

### 2. 基于EventTime的系统

要使用基于`EventTime`处理，我们需要一个时间戳提取器，从消息中提取事件时间信息。请记住，消息是有格式值，时间戳。 `extractTimestamp`方法获取时间戳并将其作为Long类型返回。现在忽略`getCurrentWatermark`方法，我们稍后会介绍：

```
class TimestampExtractor extends AssignerWithPeriodicWatermarks[String] with Serializable {
  override def extractTimestamp(e: String, prevElementTimestamp: Long) = {
    e.split(",")(1).toLong
  }
  override def getCurrentWatermark(): Watermark = {
      new Watermark(System.currentTimeMillis)
  }
}
```

现在我们需要设置这个时间戳提取器，并将`TimeCharactersistic`设置为`EventTime`。其余的代码与`ProcessingTime`的情况保持一致：

```
senv.setStreamTimeCharacteristic(TimeCharacteristic.EventTime)
val text = senv.socketTextStream("localhost", 9999)
                .assignTimestampsAndWatermarks(new TimestampExtractor)
val counts = text.map {(m: String) => (m.split(",")(0), 1) }
      .keyBy(0)
      .timeWindow(Time.seconds(10), Time.seconds(5))
      .sum(1)
counts.print
senv.execute("EventTime processing example")
```
运行上述代码的结果如下图所示：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E5%9B%BE%E8%A7%A3%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8EWatermarks-4.png?raw=true)

结果看起来更好一些，窗口2和3现在是正确的结果，但是窗口1仍然是有问题的。Flink没有将延迟的消息分配给窗口3，是因为在当前检查消息的事件时间，知道它不应该出现在窗口3中。但是为什么没有将消息分配给窗口1？原因是当延迟的信息到达系统时(第19秒)，窗口1的评估(
evaluation)已经完成了(第15秒)。现在让我们尝试通过使用`Watermark`来解决这个问题。

### 3. Watermark

`Watermark`是一个非常重要概念，我将尽力给你一个简短的概述。如果你有兴趣了解更多信息，你可以从`Google`中观看这个[演讲](https://www.youtube.com/watch?v=3UfZN59Nsk8)，还可以从`dataArtisans`那里阅读此[博客](https://data-artisans.com/blog/how-apache-flink-enables-new-streaming-applications-part-1)。 `Watermark`本质上是一个时间戳。当`Flink`中的算子(operator)接收到`Watermark`时，它明白它不会再看到比该时间戳更早的消息。因此`Watermark`也可以被认为是告诉`Flink`在`EventTime`中多远的一种方式。

在这个例子的目的，就是把`Watermark`看作是告诉`Flink`一个消息可能延迟多少的方式。在上一次尝试中，我们将`Watermark`设置为当前系统时间。因此，期望消息没有任何的延迟。现在我们将`Watermark`设置为当前时间减去5秒，这就告诉`Flink`我们期望消息最多延迟5秒钟，这是因为每个窗口仅在`Watermark`通过时被评估。由于我们的`Watermark`是当前时间减去5秒，所以第一个窗口`[5s-15s]`将会在第20秒被评估。类似地，窗口`[10s-20s]`将会在第25秒进行评估，依此类推(译者注:窗口延迟评估)。

```
override def getCurrentWatermark(): Watermark = {
      new Watermark(System.currentTimeMillis - 5000)
}
```
这里我们假定事件时间比当前系统时间晚5秒，但事实并非总是如此(有可能6秒，7秒等等)。在许多情况下，最好保留迄今为止收到的最大时间戳(从消息中提取)。使用迄今为止收到的最大时间戳减去预期的延迟时间来代替用当前系统时间减去预期的延迟时间。

进行上述更改后运行代码的结果是：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E5%9B%BE%E8%A7%A3%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8EWatermarks-5.png?raw=true)


最后我们得到了正确的结果，所有窗口都按照预期输出计数，(a，2)，(a，3)和(a，1)。

### 4. Allowed Lateness

我们也可以使用`AllowedLateness`功能设置消息的最大允许延迟时间来解决这个问题。

在我们之前使用`Watermark - delay`的方法中，只有当`Watermark`超过`window_length + delay`时，窗口才会被触发计算。如果你想要适应延迟事件，并希望窗口按时触发，则可以使用`Allowed Lateness`。 如果设置了允许延迟，`Flink`不会丢弃消息，除非它超过了`window_end_time + delay`的延迟时间。一旦收到一个延迟消息，`Flink`会提取它的时间戳并检查是否在允许的延迟时间内，然后检查是否触发窗口(按照触发器设置)。 因此，请注意，在这种方法中可能会多次触发窗口，如果你仅需要一次处理，你需要使你的`sink`具有幂等性。

### 5. 结论

实时流处理系统的重要性日益增长，延迟消息的处理是你构建任何此类系统的一部分。在这篇博文中，我们看到延迟到达的消息会影响系统的结果，以及如何使用ApacheFlink的事件时间功能来解决它们。


原文:http://vishnuviswanath.com/flink_eventtime.html
