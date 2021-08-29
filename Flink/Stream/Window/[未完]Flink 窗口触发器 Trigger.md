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

Trigger(窗口触发器)决定了窗口（由 WindowAssigner 产生）什么时候调用[窗口处理函数](http://smartsi.club/flink-stream-windows-function.html)。可以根据指定的时间或数据元素条件来决定什么时候触发，比如，可以根据到达的元素个数或者具体获取到的元素值等等。Trigger 可以访问时间属性以及计时器，并且可以处理状态。因此，它们与处理函数一样强大。例如，我们可以实现特定的触发逻辑来触发，比如窗口接收到一定数量的元素时就会触发，或者当具有特定值的元素到达窗口时，再或者检测到到达窗口中的元素满足一定模式时触发，例如最近5秒内有两个相同类型的事件。

Trigger 接口有 6 个方法，可以允许 Trigger 对不同的事件做出反应：
- onElement：每个元素到达窗口时都会调用该方法，来决定是否触发窗口计算并输出窗口结果。
- onProcessingTime：当使用 TriggerContext 注册的处理时间 Timer 触发时会调用该方法。
- onEventTime：当使用 TriggerContext 注册的事件时间 Timer 触发时会调用该方法。
- canMerge：如果 Trigger 支持对 Trigger 状态进行 Merge 并因此可以与 MergingWindowAssigner 一起使用，则返回 true。如果返回 true，必须实现 onMerge 方法。
- onMerge：当 WindowAssigner 将多个窗口合并为一个窗口时会调用该方法，同时会进行状态的合并。
- clear：执行窗口以及状态数据的清除。

```java
public abstract class Trigger<T, W extends Window> implements Serializable {
    public abstract TriggerResult onElement(T element, long timestamp, W window, TriggerContext ctx) throws Exception;
    public abstract TriggerResult onProcessingTime(long time, W window, TriggerContext ctx) throws Exception;
    public abstract TriggerResult onEventTime(long time, W window, TriggerContext ctx) throws Exception;
    public boolean canMerge() {
        return false;
    }
    public void onMerge(W window, OnMergeContext ctx) throws Exception {
        throw new UnsupportedOperationException("This trigger does not support merging.");
    }
    public abstract void clear(W window, TriggerContext ctx) throws Exception;
}
```

每次调用 Trigger 时都会生成一个 TriggerResult 来确定窗口应该触发什么操作，例如，是否应该调用窗口函数，或者应该销毁窗。TriggerResult 有如下几种取值：
- CONTINUE：表示当前不触发计算。
- FIRE：表示触发窗口计算，但是数据继续保留。如果窗口算子具有 ProcessWindowFunction，则调用该函数并输出计算结果。如果窗口只有一个增量聚合函数（ReduceFunction 或 AggregateFunction），则输出当前聚合结果。窗口状态(State)没有任何改变。
- PURGE：表示清除窗口内部数据，但不触发窗口计算。窗口所有元素被清除，窗口也被销毁(包括所有元数据)。此外，会调用 ProcessWindowFunction.clear() 方法来清除所有自定义窗口状态。
- FIRE_AND_PURGE：表示触发窗口计算并清除数据。首先触发窗口计算(FIRE)，然后清除所有状态和元数据(PURGE)。

### 2. 内置触发器

#### 2.1 内置触发器

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-trigger-1.png?raw=true)

- EventTimeTrigger：通过对比 Watermark 和窗口结束时间戳确定是否触发窗口，如果 Watermark 的时间大于窗口结束时间戳则触发计算，反之不触发计算。
- ProcesTimeTrigger：通过对比 ProcessTime 和窗口结束时间戳确定是否触发窗口，如果 ProcessTime 的时间大于窗口结束时间戳则触发计算，反之不触发计算。
- ContinuousEventTimeTrigger：根据间隔时间周期性触发窗口或者当前 EventTime 大于窗口结束时间戳会触发窗口计算。
- ContinuousProcessTimeTrigger：根据间隔时间周期性触发窗口或者当前 ProcessTime 大于窗口结束时间戳会触发窗口计算。
- CountTrigger：根据接入数据量是否超过设定的阈值来决定是否触发窗口计算。
- DeltaTrigger：根据接入数据量计算出来的 Delta 指标是否超过设定的阈值来决定是否触发窗口计算。
- PurgingTrigger：可以将任意 Trigger 作为参数转为为 Purge 类型大的 Trigger，计算完成后数据将被清除。
- ProcessingTimeoutTrigger：可以将任意 Trigger 作为参数转为为 ProcessingTimeout 类型的 Trigger。在第一个元素到达后设置一个超时处理时间。还可以通过指定 resetTimerOnNewRecord 为每个到达的元素重新更新计时器，也可以指定是否应通过 shouldClearOnTimeout 在超时时清理窗口所有数据。

> ProcessingTimeoutTrigger 于 1.12.0 版本引入。

#### 2.2 WindowAssigners 的默认触发器

每种类型的 WindowAssigner 都有不同的默认 Trigger，如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-trigger-2.png?raw=true)

所有基于事件时间的 WindowAssigner 都有一个 EventTimeTrigger 作为默认 Trigger。一旦 Watermark 大于窗口的结束时间戳，这个 Trigger 就会触发。所有基于处理时间的 WindowAssigner 都有一个 ProcessingTimeTrigger 作为默认 Trigger。一旦当前处理时间大于窗口结束时间戳，这个 Trigger 就会触发。除此之外，GlobalWindow 的默认 Trigger 是从不触发的 NeverTrigger。因此，在使用 GlobalWindow 时，我们必须自定义 Trigger。

### 3. 自定义触发器

如果默认 Trigger 不符合我们的需要，用户也可以继承并实现 Trigger 抽象类来实现自定义 Trigger。假设我们有如下场景：当每个文章点击用户达到 N 个用户时，计算每个文章的的总点击次数以及平均点击次数。比如如下输入流：
```
c10,ua,1
c11,ua,2
c10,ub,1
c11,ub,4
c10,uc,3
c12,ua,5
c11,uc,1
c12,ub,2
c12,uc,4
```
> contentId(文章Id)、uid(用户Id)、clickCnt(点击次数)

第一条记录表示用户 ua 对文章 c10 点击了 1 次。等到达第 5 条记录时，文章 c10 被 ua、ub、uc 三个用户点击。此时，该文章总共被点击了 5(1 + 1 + 3) 次。

因为默认 Trigger 不符合我们的需要(要么根据处理时间、事件时间来触发，要么根据到达的元素个数来触发，没有默认 Trigger 能实现根据到达的用户个数触发的)，所以我们需要实现如下自定义 Trigger：
```java
private static class CustomCountTrigger <W extends Window> extends Trigger<Object, W> {
    private Logger LOG = LoggerFactory.getLogger(CustomWindowTriggerExample.class);
    private Long maxCount;
    private ListStateDescriptor<String> stateDescriptor = new ListStateDescriptor<>("UidState", String.class);

    public CustomCountTrigger(Long maxCount) {
        this.maxCount = maxCount;
    }

    @Override
    public TriggerResult onElement(Object element, long timestamp, W window, TriggerContext ctx) throws Exception {
        // 获取uid信息
        Tuple3<String, String, Long> uidTuple = (Tuple3<String, String, Long>) element;
        String key = uidTuple.f0;
        String uid = uidTuple.f1;
        // 获取状态
        ListState<String> uidState = ctx.getPartitionedState(stateDescriptor);
        // 更新状态
        Iterable<String> iterable = uidState.get();
        List<String> uidList = Lists.newArrayList();
        if (!Objects.equals(iterable, null)) {
            uidList = Lists.newArrayList(iterable);
        }
        boolean isContains = uidList.contains(uid);
        if (!isContains) {
            uidList.add(uid);
            uidState.update(uidList);
        }

        // 大于等于3个用户触发计算
        if (uidList.size() >= maxCount) {
            LOG.info("[Trigger] Key: {} 触发计算并清除状态", key);
            uidState.clear();
            return TriggerResult.FIRE;
        }
        return TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onProcessingTime(long time, W window, TriggerContext ctx) throws Exception {
        return TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onEventTime(long time, W window, TriggerContext ctx) throws Exception {
        return TriggerResult.CONTINUE;
    }

    @Override
    public void clear(W window, TriggerContext ctx) throws Exception {
        ctx.getPartitionedState(stateDescriptor).clear();
    }

    public static <W extends Window> CustomCountTrigger<W> of(long maxCount) {
        return new CustomCountTrigger<>(maxCount);
    }
}
```
自定义 Trigger 的核心逻辑都在 onElement 方法中。每次元素到达窗口时都要判断元素对应的用户是否在状态中，如果不在状态中，则更新状态。更新状态之后判断状态中的用户个数，如果达到指定的阈值则触发窗口计算，否则什么都不做。

通过调用 trigger 方法来指定我们的自定义 Trigger：
```java
DataStream<String> result = stream
    // 根据contentId分组
    .keyBy(new KeySelector<Tuple3<String, String, Long>, String>() {
        @Override
        public String getKey(Tuple3<String, String, Long> value) throws Exception {
            return value.f0;
        }
    })
    // 每3个用户一个窗口
    .window(GlobalWindows.create())
    .trigger(CustomCountTrigger.of(3))
    // 求和以及平均值
    .aggregate(new AverageAggregateFunction());
```
> 完整代码请查阅  [CustomWindowTriggerExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/CustomWindowTriggerExample.java)

实际效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-trigger-3.png?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

相关推荐：
- [Flink 窗口之Window机制](http://smartsi.club/introducing-stream-windows-in-apache-flink.html)
- [Flink 窗口分配器 WindowAssigner](http://smartsi.club/flink-stream-windows-overall.html)
- [Flink 窗口处理函数 WindowFunction](http://smartsi.club/flink-stream-windows-function.html)
