---
layout: post
author: smartsi
title: Flink 窗口触发器 Trigger
date: 2021-06-30 10:28:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-windows-trigger
---

### 1. 简介

窗口触发器(Trigger)决定了窗口（由 WindowAssigner 产生）什么时候调用[窗口处理函数](http://smartsi.club/flink-stream-windows-function.html)。可以根据指定的时间或数据元素条件来决定什么时候触发，比如，可以根据到达的元素个数或者具体获取到的元素值等等。触发器可以访问时间属性以及计时器，并且可以处理状态。因此，它们与处理函数一样强大。例如，我们可以实现特定的触发逻辑来触发，比如窗口接收到一定数量的元素时就会触发，或者当具有特定值的元素到达窗口时，再或者检测到到达窗口中的元素满足一定模式时触发，例如最近5秒内有两个相同类型的事件。

每种类型的窗口都对应不同的窗口触发器，确保保障每一次接入窗口的元素都能够按照规定的触发逻辑进行统计计算。例如，EventTime 类型的窗口对应的触发器是 EventTimeTrigger，其基本原理是判断当前的 Watermark 是否超过窗口结束边界的时间戳时，如果超过则触发对窗口内数据的计算，反之不触发计算。下面是 Flink 内置的窗口触发器，用户可以根据需求选择合适的触发器。

### 2. 内置触发器

![]()

- EventTimeTrigger：通过对比 Watermark 和窗口结束时间戳确定是否触发窗口，如果 Watermark 的时间大于窗口结束时间戳则触发计算，反之不触发计算。
- ProcesTimeTrigger：通过对比 ProcessTime 和窗口结束时间戳确定是否触发窗口，如果 ProcessTime 的时间大于窗口结束时间戳则触发计算，反之不触发计算。
- ContinuousEventTimeTrigger：根据间隔时间周期性触发窗口或者当前 EventTime 大于窗口结束时间戳会触发窗口计算。
- ContinuousProcessTimeTrigger：根据间隔时间周期性触发窗口或者当前 ProcessTime 大于窗口结束时间戳会触发窗口计算。
- CountTrigger：根据接入数据量是否超过设定的阈值来决定是否触发窗口计算。
- DeltaTrigger：根据接入数据量计算出来的 Delta 指标是否超过设定的阈值来决定是否触发窗口计算。
- PurgingTrigger：可以将任意触发器作为参数转为为 Purge 类型触发器，计算完成后数据将被清除。
- ProcessingTimeoutTrigger：可以将任意触发器作为参数转为为 ProcessingTimeout 类型触发器。在第一个元素到达后设置一个超时处理时间。还可以通过指定 resetTimerOnNewRecord 为每个到达的元素重新更新计时器，也可以指定是否应通过 shouldClearOnTimeout 在超时时清理窗口所有数据。

> ProcessingTimeoutTrigger 于 1.12.0 版本引入。

### 3. 自定义触发器

如果已有的触发器不能满足实际需求没用户也可以继承并实现 Trigger 抽象类自定义触发器。如果要自定义触发器需要重写如下几个方法：
```java
public abstract class Trigger<T, W extends Window> implements Serializable {
    public abstract TriggerResult onElement(T element, long timestamp, W window, TriggerContext ctx)
            throws Exception;
    public abstract TriggerResult onProcessingTime(long time, W window, TriggerContext ctx)
            throws Exception;
    public abstract TriggerResult onEventTime(long time, W window, TriggerContext ctx)
            throws Exception;
    public boolean canMerge() {
        return false;
    }
    public void onMerge(W window, OnMergeContext ctx) throws Exception {
        throw new UnsupportedOperationException("This trigger does not support merging.");
    }
    public abstract void clear(W window, TriggerContext ctx) throws Exception;
}
```
- onElement：每个到达窗口中的元素都会调用该方法，以此决定是否触发窗口计算并输出窗口结果。
- onProcessingTime：当使用 TriggerContext 注册的处理时间计时器触发时会调用该方法。
- onEventTime：当使用 TriggerContext 注册的事件时间计时器触发时会调用该方法。
- canMerge：如果触发器支持对触发器状态进行 Merge 并因此可以与 MergingWindowAssigner 一起使用，则返回 true。如果返回 true，必须实现 onMerge 方法。
- onMerge：当 WindowAssigner 将多个窗口合并为一个窗口时会调用该方法，同时会进行状态的合并。
- clear：执行窗口以及状态数据的清除。

每次调用触发器时，触发器都会生成一个 TriggerResult 来确定窗口应该触发什么操作，例如是否应该调用窗口函数，或者应该销毁窗。TriggerResult 分别是：
- CONTINUE：表示当前不触发计算，继续等待。
- FIRE：表示触发计算，但是数据继续保留。如果窗口算子具有 ProcessWindowFunction，则调用该函数并输出计算结果。如果窗口只有一个增量聚合函数（ReduceFunction 或 AggregateFunction），则输出当前聚合结果。窗口状态(State)没有任何改变。
- PURGE：表示窗口内部数据清除，但不触发计算。窗口所有元素被清除，窗口也被销毁(包括所有元数据)。此外，会调用 ProcessWindowFunction.clear() 方法来清除所有自定义窗口状态。
- FIRE_AND_PURGE：表示触发计算并清除数据。首先触发窗口计算(FIRE)，然后清除所有状态和元数据(PURGE)。

> Trigger 虽然返回 FIRE 或者 FIRE_AND_PURGE，但是窗口内没有任何数据，窗口处理函数就不会被调用。




。。。
