---
layout: post
author: smartsi
title: Flink 窗口之触发器与Evictors
date: 2018-03-01 14:46:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-windows-trigger-and-evictor
---

### 1. 窗口触发器

触发器(`Trigger`)决定了窗口(请参阅[窗口概述](http://smartsi.club/flink-stream-windows-overall.html))博文)什么时候使用[窗口函数](http://smartsi.club/flink-stream-windows-function.html)处理窗口内元素。每个窗口分配器都带有一个默认的触发器。如果默认触发器不能满足你的要求，可以使用 `trigger(...)` 指定自定义的触发器。

触发器接口有五个方法来对不同的事件做出响应：

(1) 当每个元素被添加窗口时调用`onElement()`方法：
```java
public abstract TriggerResult onElement(T element, long timestamp, W window, TriggerContext ctx) throws Exception;
```
(2) 当注册的处理时间计时器被触发时调用`onProcessingTime()`方法：
```java
public abstract TriggerResult onProcessingTime(long time, W window, TriggerContext ctx) throws Exception;
```
(3) 当注册的事件时间计时器被触发时调用`onEventTime()`方法：
```java
public abstract TriggerResult onEventTime(long time, W window, TriggerContext ctx)
```
(4) 在窗口合并时`onMerge()`方法与状态触发器相关，并且合并两个触发器的状态：
```java
public void onMerge(W window, OnMergeContext ctx)
```
(5) 在清除（removal）窗口时调用`clear()` 方法：
```java
public abstract void clear(W window, TriggerContext ctx)
```

以上方法有两件事要注意:

(1) 前三个函数决定了如何通过返回一个 `TriggerResult` 对象来对其调用事件进行操作。`TriggerResult`可以是，`CONTINUE`（什么都不做），`FIRE_AND_PURGE`（触发计算，然后清除窗口中的元素），`FIRE`（触发计算），`PURGE`（清除窗口中的元素）。

(2) 上面任何方法都可以用于注册处理时间计时器或事件时间计时器以供将来的操作使用。

#### 1.1 触发与清除

一旦触发器确定窗口准备好可以处理数据，就将触发，即，它返回 `FIRE` 或 `FIRE_AND_PURGE`。这是窗口算子发出当前窗口结果的信号。给定一个带有 `ProcessWindowFunction` 的窗口，所有的元素都被传递给 `ProcessWindowFunction` (可能在将所有元素传递给 `evictor` 之后)。带有 `ReduceFunction`， `AggregateFunction` 或者 `FoldFunction` 的窗口只是简单地发出他们急切希望得到的聚合结果。

触发器触发时，可以是 `FIRE` 或 `FIRE_AND_PURGE` 。`FIRE` 保留窗口中的内容，`FIRE_AND_PURGE` 会删除窗口中的内容。默认情况下，内置的触发器只返回 `FIRE`，不会清除窗口状态。

> 清除只是简单地删除窗口的内容，并保留窗口的元数据信息以及完整的触发状态。

#### 1.2 窗口分配器的默认触发器

窗口分配器的默认触发器适用于许多情况。例如，所有的事件时间窗口分配器都有一个 `EventTimeTrigger` 作为默认触发器。一旦 `watermark` 到达窗口末尾，这个触发器就会被触发。

> 全局窗口(GlobalWindow)的默认触发器是永不会被触发的 NeverTrigger。因此，在使用全局窗口时，必须自定义一个触发器。

> 通过使用 trigger() 方法指定触发器，将会覆盖窗口分配器的默认触发器。例如，如果你为 TumblingEventTimeWindows 指定 CountTrigger，那么不会再根据时间进度触发窗口，而只能通过计数。目前为止，如果你希望基于时间以及计数进行触发，则必须编写自己的自定义触发器。

#### 1.3 内置触发器和自定义触发器

Flink带有一些内置触发器:
- `EventTimeTrigger` 根据 `watermarks` 度量的事件时间进度进行触发。
- `ProcessingTimeTrigger` 基于处理时间触发。
- `CountTrigger` 一旦窗口中的元素数量超过给定限制就会触发。
- `PurgingTrigger` 将其作为另一个触发器的参数，并将其转换为带有清除功能(transforms it into a purging one)。

如果需要实现一个自定义的触发器，你应该看看[Trigger](https://github.com/apache/flink/blob/master//flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/triggers/Trigger.java)抽象类。请注意，API仍在发展中，在Flink未来版本中可能会发生改变。

### 2. 窗口驱逐器

Flink 窗口模型还允许在窗口分配器和触发器之外指定一个可选的驱逐器(`Evictor`)。可以使用 `evictor(...)` 方法来完成。驱逐器能够在触发器触发之后，窗口函数使用之前或之后从窗口中清除元素。`Evictor` 接口有两种方法：

```java
void evictBefore(Iterable<TimestampedValue<T>> elements, int size, W window, EvictorContext evictorContext);

void evictAfter(Iterable<TimestampedValue<T>> elements, int size, W window, EvictorContext evictorContext);
```

`evictBefore()` 包含驱逐逻辑，在窗口函数之前使用。而 `evictAfter()` 在窗口函数之后使用。在使用窗口函数之前被逐出的元素将不被处理。

Flink带有三种内置驱逐器:
- `CountEvictor`：在窗口维护用户指定数量的元素，如果多于用户指定的数量，从窗口缓冲区的开头丢弃多余的元素。
- `DeltaEvictor`：使用 `DeltaFunction` 和一个阈值，来计算窗口缓冲区中的最后一个元素与其余每个元素之间的差值，并删除差值大于或等于阈值的元素。
- `TimeEvictor`：以毫秒为单位的时间间隔（`interval`）作为参数，对于给定的窗口，找到元素中的最大的时间戳`max_ts`，并删除时间戳小于`max_ts - interval`的所有元素。

默认情况下，所有内置的驱逐器在窗口函数之前使用。指定驱逐器可以避免预聚合(pre-aggregation)，因为窗口内所有元素必须在窗口计算之前传递给驱逐器。Flink 不保证窗口内元素的顺序。这意味着虽然驱逐器可以从窗口开头移除元素，但这些元素不一定是先到的还是后到的。

> Flink版本:1.4

原文: https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/stream/operators/windows.html#triggers
