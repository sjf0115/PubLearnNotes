---
layout: post
author: smartsi
title: Flink 事件时间与Watermarks
date: 2018-01-04 17:57:01
tags:
  - Flink

categories: Flink
permalink: flink-stream-event-time-and-watermark
---

> Flink版本：1.11

### 1. watermark

Flink 实现了数据流模型(`Dataflow Model`)中许多技术。如果想对事件时间(`event time`)和`watermarks`更详细的了解，请参阅下面的文章:
- [The world beyond batch: Streaming 101
](https://www.oreilly.com/ideas/the-world-beyond-batch-streaming-101)
- [The Dataflow Model](http://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf)

通常情况下，由于网络或者系统等外部因素影响，事件数据往往不能及时传输至 Flink 系统中，导致数据乱序到达或者延迟到达，因此需要一种机制能控制数据处理的过程和进度，比如创建基于事件时间的窗口，它需要知道如何确定属于该窗口的数据元素已经全部到达。如果数据全部到达，就可以对窗口的所有数据做窗口计算操作，如果数据没有全部到达，就可以继续等待窗口中的数据全部到达才开始处理。

支持事件时间的流处理器需要一种方法来衡量事件时间的进度。例如，一个构建小时窗口的窗口算子，当事件时间超过一小时边界时需要告知窗口算子，以便算子可以结束正在进行的窗口。

事件时间可以独立于处理时间来运行。例如，在一个程序中，算子的当前事件时间可以略微落后于处理时间(考虑到接收事件的延迟)，而两者以相同的速度继续运行。另一方面，另一个流式处理程序处理几个星期的事件时间只需几秒钟就可以，通过快速浏览缓存在`Kafka Topic`中历史数据。

`Flink`中测量事件时间进度的机制是`watermarks`。`watermarks`会作为数据流的一部分进行流动，并带有一个时间戳`t`。`Watermark(t)`表示数据流中的事件时间已达到时间`t`，意思就是说数据流之后不再有时间戳`t‘<= t`的元素(即带时间戳的事件老于或等于`watermark`)。

下图显示了具有时间戳(逻辑上)的事件流以及内嵌的`watermark`。在这个例子中，事件是有序的(相对于它们的时间戳)，这意味着`watermark`只是数据流中的周期性标记。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8EWatermarks-1.png?raw=true)

`watermark`对于乱序数据流至关重要，如下图所示，事件并未按照时间戳进行排序。通常，`watermark`表示在数据流中那个时刻小于时间戳的所有事件都已经到达。一旦`watermark`到达算子，算子就可以将其内部的事件时间提到`watermark`的那个值。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8EWatermarks-2.png?raw=true)


### 2. 数据流中的并行Watermarks

`watermarks`是直接通过数据源函数(source functions)生成的或在数据源函数之后生成的。源函数的每个并行子任务通常独立生成`watermarks`。这些`watermarks`在指定并行数据源上定义事件时间。

`watermarks`贯穿整个流处理程序，他们会在`watermark`到达的算子时将事件时间提前(advance)。每当算子提前事件时间时，它都会为下游的后续算子生成一个新的`watermarks`(Whenever an operator advances its event time, it generates a new watermark downstream for its successor operators.)。

一些算子消耗多个输入流；例如，union操作，或者算子后面跟着`keyBy(...)`函数或者`partition(...)函数`。这样的算子的当前事件时间是其输入流的所有事件时间中的最小值。随着输入流更新事件时间，算子也会更新事件。

下图显示了事件和`watermarks`流经并行流的的示例，以及跟踪事件时间的算子:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8EWatermarks-3.png?raw=true)

### 3. 延迟元素

某些元素可能违反`watermarks`条件，这意味着即使出现`watermarks(t)`，但是还是会出现很多的时间戳`t'<= t`的元素。事实上，在现实世界中，某些元素可能被任意地延迟，因此指定一个时间，带有事件时间戳的所有事件在此之前出现是不可能的。此外，即使延迟时间是有限制的，也不希望延迟太多的`watermarks`，因为它会在事件时间窗口的评估中导致太多的延迟。

因此，流处理程序中可能会明确的知道会有延迟元素。延迟元素是那些系统事件时钟(由`watermark`所示)已经超过了延迟元素的时间戳的那些元素。有关如何处理事件时间窗口中的延迟元素的更多信息，请参阅[Allowed Lateness](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/stream/operators/windows.html#allowed-lateness)。

### 4. 调试Watermarks

请参阅[调试Windows和事件时间](https://ci.apache.org/projects/flink/flink-docs-release-1.3/monitoring/debugging_event_time.html)部分，以便在运行时调试Watermarks。



原文:[Event Time and Watermarks](https://ci.apache.org/projects/flink/flink-docs-release-1.12/concepts/timely-stream-processing.html#event-time-and-watermarks)
