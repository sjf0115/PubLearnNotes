
### 1. 简介

Trigger(窗口触发器)决定了窗口（由 [WindowAssigner](https://smartsi.blog.csdn.net/article/details/126652876) 产生）什么时候调用[窗口处理函数](https://smartsi.blog.csdn.net/article/details/126681922)。可以根据指定的时间或数据元素条件来决定什么时候触发，比如，可以根据到达的元素个数或者具体获取到的元素值等等。Trigger 可以访问时间属性以及计时器，并且可以处理状态。因此，它们与处理函数一样强大。例如，我们可以实现特定的触发逻辑来触发，比如窗口接收到一定数量的元素时就会触发，或者当具有特定值的元素到达窗口时，再或者检测到到达窗口中的元素满足一定模式时触发，例如最近5秒内有两个相同类型的事件。

Trigger 接口中有 6 个方法，其中有 3 个是用来应对不同事件做出响应，如下所示：
```java
public abstract class Trigger<T, W extends Window> implements Serializable {
    public abstract TriggerResult onElement(T element, long timestamp, W window, TriggerContext ctx) throws Exception;
    public abstract TriggerResult onProcessingTime(long time, W window, TriggerContext ctx) throws Exception;
    public abstract TriggerResult onEventTime(long time, W window, TriggerContext ctx) throws Exception;
}
```
每当有元素添加到窗口中就会调用 onElement，来决定是否触发窗口计算并输出窗口结果。该方法是针对元素做出的响应，还有两个是针对时间做出的响应。当使用 TriggerContext(下面会介绍)注册的处理时间计时器 Timer 触发时会调用 onProcessingTime 方法，而当注册的事件时间计时器 Timer 触发时会调用 onEventTime 方法。

上述方法被调用时都会生成一个 TriggerResult 对象来表示窗口应该如何响应，例如是否触发窗口计算还是销毁窗口。针对不同的使用场景，TriggerResult 提供了如下几种响应：
- CONTINUE：什么都不做，即不触发计算
- FIRE：触发窗口计算并输出窗口结果。只是触发计算并不会清除窗口，因此还会保留所有元素。如果窗口算子配置了 ProcessWindowFunction，则调用该函数并输出计算结果；如果窗口只有一个增量聚合函数（ReduceFunction 或 AggregateFunction），则直接输出当前聚合结果。窗口状态没有任何改变。
- PURGE：完全清除窗口(窗口中的所有元素、窗口自身及其元数据)。窗口中所有的元素会被清除，窗口本身也被销毁(包括所有元数据)，但不会触发窗口计算，更不会输出任何元素。此外，会调用 ProcessWindowFunction.clear() 方法来清除所有自定义窗口状态。
- FIRE_AND_PURGE：触发窗口计算并同时完全清除窗口。首先触发窗口计算(FIRE)，然后完全清除窗口(PURGE)。


在触发器中清除那些为给定窗口保存的状态时会调用 clear 方法，该方法会在清除窗口时被调用：
```java
public abstract void clear(W window, TriggerContext ctx) throws Exception;
```

在窗口合并时，不仅仅需要合并窗口中的状态，可能还需要合并窗口依赖的触发器。因此提供了如下两个方法来支持触发器的合并：
```java
// 是否支持合并触发器状态
public boolean canMerge() {
    return true;
}

// 合并逻辑
public void onMerge(TimeWindow window, Trigger.OnMergeContext ctx) {
    long windowMaxTimestamp = window.maxTimestamp();
    if (windowMaxTimestamp > ctx.getCurrentWatermark()) {
        ctx.registerEventTimeTimer(windowMaxTimestamp);
    }
}
```
如果触发器支持合并触发器状态，并可以与 MergingWindowAssigner 一起使用，那么 canMerge 返回 true，否则返回 false。如果触发器不支持合并，则无法与 MergingWindowAssigner 组合使用。当多个窗口需要合并为一个窗口，并且还需要合并触发器状态时会调用 onMerge 进行触发器状态的合并。需要注意的是，如果 canMerge 返回 true，那么必须实现 onMerge 方法。

```java
public interface TriggerContext {
    // 返回当前处理时间
    long getCurrentProcessingTime();
    // 返回当前 Watermark
    long getCurrentWatermark();
    // 注册一个处理时间计时器
    void registerProcessingTimeTimer(long time);
    // 注册一个事件时间计时器
    void registerEventTimeTimer(long time);
    // 删除一个处理时间计时器
    void deleteProcessingTimeTimer(long time);
    // 删除一个事件时间计时器
    void deleteEventTimeTimer(long time);
    // Metric 组
    MetricGroup getMetricGroup();
    // 获取一个与容错状态交互的状态对象，作用域为触发器调用的 Key 以及当前窗口
    <S extends State> S getPartitionedState(StateDescriptor<S, ?> stateDescriptor);
}

public interface OnMergeContext extends TriggerContext {
    <S extends MergingState<?, ?>> void mergePartitionedState(StateDescriptor<S, ?> stateDescriptor);
}
```

## 2. ProcessingTimeTrigger

ProcessingTimeTrigger 是一个完全基于机器系统时间的触发器。实现原理比较简单，一旦当前系统处理时间超过了窗口结束的时间戳时，`ProcessingTimeTrigger` 触发器就会触发：
- 首次到达的元素：当第一个元素进入窗口时，onElement 方法会注册一个处理时间定时器，定时器的时间戳为窗口的结束时间 `window.maxTimestamp()`。
- 定时器触发：当系统时间达到窗口结束时间时，onProcessingTime 方法被调用，触发窗口计算。

```java
public class ProcessingTimeTrigger extends Trigger<Object, TimeWindow> {

    // 元素处理
    @Override
    public TriggerResult onElement(Object element, long timestamp, TimeWindow window, TriggerContext ctx) {
        // 为当前窗口注册一个定时器，触发时间是窗口的结束时间  只注册不触发
        ctx.registerProcessingTimeTimer(window.maxTimestamp());
        return TriggerResult.CONTINUE;
    }

    // 当一个基于事件时间的定时器（由Watermark驱动）触发时调用
    @Override
    public TriggerResult onEventTime(long time, TimeWindow window, TriggerContext ctx) throws Exception {
        // 处理时间触发器不关心事件时间 不触发
        return TriggerResult.CONTINUE;
    }

    // 当一个基于处理时间的定时器触发时调用
    @Override
    public TriggerResult onProcessingTime(long time, TimeWindow window, TriggerContext ctx) {
        // 当处理时间到达窗口结束时，触发窗口计算
        return TriggerResult.FIRE;
    }

    // 当窗口被清除时执行删除定时器操作
    public void clear(TimeWindow window, Trigger.TriggerContext ctx) throws Exception {
        ctx.deleteProcessingTimeTimer(window.maxTimestamp());
    }

    // 支持窗口触发器合并
    public boolean canMerge() {
        return true;
    }

    // 窗口触发器合并
    public void onMerge(TimeWindow window, Trigger.OnMergeContext ctx) {
        long windowMaxTimestamp = window.maxTimestamp();
        if (windowMaxTimestamp > ctx.getCurrentProcessingTime()) {
            ctx.registerProcessingTimeTimer(windowMaxTimestamp);
        }
    }
}
```

## 3. EventTimeTrigger

EventTimeTrigger 是一个基于事件时间（由 Watermark 驱动）的触发器。它是处理乱序事件流、保证计算结果准确性的核心。实现原理：
- 注册结束时间定时器：当第一个元素进入窗口时，onElement 方法会注册一个事件时间定时器，定时器的时间戳同样是窗口的结束时间 `window.maxTimestamp()`。
- 等待 Watermark：系统会不断生成和推进 Watermark。
- 定时器触发：当 Watermark >= 窗口结束时间时，onEventTime 方法被调用，触发窗口计算。

```java
public class EventTimeTrigger extends Trigger<Object, TimeWindow> {
    private static final long serialVersionUID = 1L;

    private EventTimeTrigger() {
    }

    public TriggerResult onElement(Object element, long timestamp, TimeWindow window, Trigger.TriggerContext ctx) throws Exception {
        if (window.maxTimestamp() <= ctx.getCurrentWatermark()) {
            // 如果 Watermark 已经超过了窗口的结束时间，则不再注册定时器，直接触发
            return TriggerResult.FIRE;
        } else {
            // 为当前窗口注册一个事件时间定时器，触发时间是窗口的结束时间
            ctx.registerEventTimeTimer(window.maxTimestamp());
            return TriggerResult.CONTINUE;
        }
    }

    public TriggerResult onEventTime(long time, TimeWindow window, Trigger.TriggerContext ctx) {
        // 只有当定时器时间等于窗口结束时间时才触发
        return time == window.maxTimestamp() ? TriggerResult.FIRE : TriggerResult.CONTINUE;
    }

    public TriggerResult onProcessingTime(long time, TimeWindow window, Trigger.TriggerContext ctx) throws Exception {
        // 事件时间触发器不关心处理时间
        return TriggerResult.CONTINUE;
    }

    ...
}
```
事件时间触发器与处理时间触发器实现上有一个不同点在于，onElement 中的 `window.maxTimestamp() <= ctx.getCurrentWatermark()` 判断：当一个元素到达时，如果 Watermark 已经超过了窗口的结束时间，直接触发。
