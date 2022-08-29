---
layout: post
author: sjf0115
title: Flink 源码解读系列 DataStream 窗口分配器 WinowAssigner
date: 2022-08-29 14:47:01
tags:
  - Flink

categories: Flink
permalink: flink-stream-code-window-assigner
---


在前一篇文章 [Flink 源码解读系列 DataStream 窗口 Window 实现](https://smartsi.blog.csdn.net/article/details/126574164) 中，我们了解到 Flink 窗口 Window 有两种具体实现，一个是 TimeWindow，一个是 GlobalWindow。有了窗口之后，我们如何将元素分配给窗口呢？在这篇文章中我们重点了解一下窗口分配器 WindowAssigner 是如何将输入流中的元素划分给窗口的。

## 1. 如何指定窗口分配器

在了解窗口分配器 WindowAssigner 内部实现之前，我们先看一下如何为窗口算子指定窗口分配器。Flink 为我们提供了几种指定窗口分配器的方式，具体取决于输入流是不是 KeyedStream。如果是在 KeyedStream 上使用窗口，可以使用如下三个方法指定窗口分配器：
- window()
- timeWindow()
- countWindow()

如果是在 DataStream 上使用窗口，可以使用如下三个方法指定窗口分配器：
- windowAll
- timeWindowAll()
- countWindowAll()

> 在 KeyedStream 和 DataStream 上使用窗口的方式基本一致。

### 1.1 window

在 KeyedStream 上可以通过 window 方法指定窗口分配器，而对于 DataStream 则需要使用 windowAll 方法指定：
```java
// KeyedStream 上使用
public <W extends Window> WindowedStream<T, KEY, W> window(WindowAssigner<? super T, W> assigner) {
    return new WindowedStream<>(this, assigner);
}
// DataStream 上使用
public <W extends Window> AllWindowedStream<T, W> windowAll(WindowAssigner<? super T, W> assigner) {
	return new AllWindowedStream<>(this, assigner);
}
```

### 1.2 timeWindow

> Flink 1.12 版本中标记为弃用，推荐使用 window 方法

除了使用 window(或者 windowAll) 方法来指定窗口分配器之外，也可以使用 timeWindow(或者 timeWindowAll) 来指定窗口分配器。这种方式需要与时间特性配合使用，具体是基于事件时间的窗口还是基于处理时间的窗口，取决于你设置的 TimeCharacteristic：
```java
// KeyedStream 滚动时间窗口
public WindowedStream<T, KEY, TimeWindow> timeWindow(Time size) {
    if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
        return window(TumblingProcessingTimeWindows.of(size));
    } else {
        return window(TumblingEventTimeWindows.of(size));
    }
}
// KeyedStream 滑动时间窗口
public WindowedStream<T, KEY, TimeWindow> timeWindow(Time size, Time slide) {
    if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
        return window(SlidingProcessingTimeWindows.of(size, slide));
    } else {
        return window(SlidingEventTimeWindows.of(size, slide));
    }
}

// DataStream 滚动时间窗口
public AllWindowedStream<T, TimeWindow> timeWindowAll(Time size) {
	if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
		return windowAll(TumblingProcessingTimeWindows.of(size));
	} else {
		return windowAll(TumblingEventTimeWindows.of(size));
	}
}
// DataStream 滑动时间窗口
public AllWindowedStream<T, TimeWindow> timeWindowAll(Time size, Time slide) {
    if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
    	return windowAll(SlidingProcessingTimeWindows.of(size, slide));
    } else {
    	return windowAll(SlidingEventTimeWindows.of(size, slide));
    }
}
```
从上面代码中可以看到 timeWindow 函数只是对 window 函数的一次封装，封装之后我们不用关心到底是使用滚动事件时间窗口分配器 TumblingEventTimeWindows、滚动处理时间窗口分配器 TumblingProcessingTimeWindows、滑动事件时间窗口分配器 SlidingEventTimeWindows 还是滑动处理时间窗口分配器 SlidingProcessingTimeWindows。timeWindow 会根据你设置的时间特性 TimeCharacteristic 以及是否有滑动步长来自选选择对应的窗口分配器。例如时间特性为事件时间 EventTime，只有窗口大小没有滑动步长，timeWindow 会你提供滚动事件时间窗口分配器 TumblingEventTimeWindows。这样方式更简洁一些，出错的可能性也更低，不需要记住各种不同的窗口分配器。

需要注意的是在 Flink 1.12 版本中，DataStream API 中的 timeWindow() 方法已经标注为 `@Deprecated`。Flink 社区推荐使用带 TumblingEventTimeWindows、SlidingEventTimeWindows、TumblingProcessingTimeWindows 或 SlidingProcessingTimeWindows 的 window(WindowAssigner) 方法。主要原因是在这个版本中弃用了 DataStream API 中的时间特性，从而导致无法继续基于时间特性来判断是基于处理时间的窗口还是基于事件时间的窗口。

> [FLINK-19318](FLINK-19318)

### 1.3 countWindow

对于使用全局窗口 GlobalWindow 实现计数的话，Flink 提供了便捷方法 countWindow 实现：
```java
// KeyedStream
public WindowedStream<T, KEY, GlobalWindow> countWindow(long size) {
	return window(GlobalWindows.create())
      .trigger(PurgingTrigger.of(CountTrigger.of(size)));
}
public WindowedStream<T, KEY, GlobalWindow> countWindow(long size, long slide) {
	return window(GlobalWindows.create())
			.evictor(CountEvictor.of(size))
			.trigger(CountTrigger.of(slide));
}

// DataStream
public AllWindowedStream<T, GlobalWindow> countWindowAll(long size) {
	return windowAll(GlobalWindows.create()).trigger(PurgingTrigger.of(CountTrigger.of(size)));
}
public AllWindowedStream<T, GlobalWindow> countWindowAll(long size, long slide) {
	return windowAll(GlobalWindows.create())
			.evictor(CountEvictor.of(size))
			.trigger(CountTrigger.of(slide));
}
```

## 2. 窗口分配器实现

上面我们了解了指定窗口分配器 WindowAssigner 的几种方式，那 WindowAssigner 具体是如何实现的呢？Flink 提供了一个 WindowAssigner 抽象类，抽象了几个实现 WindowAssigner 必须要实现的几个方法：
```java
public abstract class WindowAssigner<T, W extends Window> implements Serializable {
    public abstract Collection<W> assignWindows(T element, long timestamp, WindowAssignerContext context);
    public abstract Trigger<T, W> getDefaultTrigger(StreamExecutionEnvironment env);
    public abstract TypeSerializer<W> getWindowSerializer(ExecutionConfig executionConfig);
    public abstract boolean isEventTime();
    public abstract static class WindowAssignerContext {
        public abstract long getCurrentProcessingTime();
    }
}
```
抽象类有 4 个方法：
- assignWindows：将带有时间戳 timestamp 的元素 element 分配给一个或多个窗口，并返回分配的窗口集合
- getDefaultTrigger：窗口分配器默认的触发器 Trigger
- getWindowSerializer 窗口分配器的序列化器，用来序列化窗口
- isEventTime：是否是基于 EventTime 来分配窗口

Flink 针对生产环境使用比较多的场景内置实现了几种窗口分配器：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-code-window-assigner-1.png?raw=true)

> 当然，如果内置的窗口分配器不能满足你的需求，可以自己实现自定义的窗口分配器

下面我们会重点介绍我们比较常用的 TumblingEventTimeWindows、TumblingProcessingTimeWindows、SlidingEventTimeWindows、SlidingProcessingTimeWindows、GlobalWindows。

### 2.1 TumblingEventTimeWindows

滚动事件时间窗口分配器 TumblingEventTimeWindows 根据元素的事件时间戳将元素分配到滚动窗口中。创建 TumblingEventTimeWindows 需要提供窗口大小 size、窗口偏移量 offset 以及窗口错峰策略 windowStagger 三个参数：
```java
public class TumblingEventTimeWindows extends WindowAssigner<Object, TimeWindow> {
    // 窗口大小
    private final long size;
    // 窗口偏移量
    private final long globalOffset;
    // 窗口错峰策略
    private final WindowStagger windowStagger;
    protected TumblingEventTimeWindows(long size, long offset, WindowStagger windowStagger) {
        if (Math.abs(offset) >= size) {
            throw new IllegalArgumentException(xxx);
        }
        this.size = size;
        this.globalOffset = offset;
        this.windowStagger = windowStagger;
    }
    ...
}
```
Flink 为我们提供了三个便捷方法 of 来创建滚动事件时间窗口分配器，一个只需要指定窗口大小，一个只需要指定窗口大小和窗口时间偏移量 offset(时间偏移量可以更好的控制窗口的开始时间)，另一个指定窗口大小和时间偏移量之外还需要指定窗口错峰策略：
```java
// 创建一个滚动事件时间窗口分配器 只指定窗口大小
public static TumblingEventTimeWindows of(Time size) {
    return new TumblingEventTimeWindows(size.toMilliseconds(), 0, WindowStagger.ALIGNED);
}
// 创建一个滚动事件时间窗口分配器 指定窗口大小和时间偏移量
public static TumblingEventTimeWindows of(Time size, Time offset) {
    return new TumblingEventTimeWindows(
            size.toMilliseconds(), offset.toMilliseconds(), WindowStagger.ALIGNED);
}
// 创建一个滚动事件时间窗口分配器 指定窗口大小、时间偏移量以及窗口错峰策略
public static TumblingEventTimeWindows of(Time size, Time offset, WindowStagger windowStagger) {
    return new TumblingEventTimeWindows(
            size.toMilliseconds(), offset.toMilliseconds(), windowStagger);
}
```
> WindowStagger 是 Flink 1.12 版本新添加的一个新特性，为了解决同一时间触发大量的窗口计算造成的性能问题，具体可以查阅 [FLINK-12855](https://issues.apache.org/jira/browse/FLINK-12855)

了解了滚动事件时间窗口分配器如何创建之后，我们一起看一下窗口分配器是如何将元素分配到窗口中的。具体分配到哪个窗口需要通过 assignWindows 方法实现：
```java
public Collection<TimeWindow> assignWindows(Object element, long timestamp, WindowAssignerContext context) {
    if (timestamp > Long.MIN_VALUE) {
        // 设置窗口错峰策略偏移量 错峰触发窗口
        if (staggerOffset == null) {
            staggerOffset = windowStagger.getStaggerOffset(context.getCurrentProcessingTime(), size);
        }
        // 窗口开始时间
        long start = TimeWindow.getWindowStartWithOffset(
              timestamp, (globalOffset + staggerOffset) % size, size
        );
        // 分配到的具体窗口
        return Collections.singletonList(new TimeWindow(start, start + size));
    } else {
        // 没有指定时间戳提取器
        throw new RuntimeException(xxx);
    }
}
```
如果你使用的是事件时间并指定了时间戳提取 assignTimestampsAndWatermarks，元素的时间戳肯定是大于 Long.MIN_VALUE，否则需要检查你写的代码是否有问题。staggerOffset 默认值是空的，会根据选择的窗口错峰策略 WindowStagger 设置偏移量，然后根据元素事件时间戳 timestamp 和 size 计算出窗口的开始时间，最后返回一个存储 TimeWindow 的单例集合。计算窗口开始时间的详细逻辑可以参阅 [Flink 源码解读系列 DataStream 窗口 Window 实现](https://smartsi.blog.csdn.net/article/details/126574164?spm=1001.2014.3001.5502)。

> 滚动窗口分配器只能将一个元素分配到一个窗口中

如果没有指定窗口错峰策略 WindowStagger，默认为 WindowStagger.ALIGNED，那么 staggerOffset 为 0，窗口计算开始时间与如下代码等价：
```java
TimeWindow.getWindowStartWithOffset(now, globalOffset, size);
```

此外窗口分配器还提供了默认的触发器 EventTimeTrigger 来决定窗口计算的触发时机：
```java
public Trigger<Object, TimeWindow> getDefaultTrigger(StreamExecutionEnvironment env) {
    return EventTimeTrigger.create();
}
```

### 2.2 TumblingProcessingTimeWindows

滚动处理时间窗口分配器 TumblingProcessingTimeWindows 根据当前系统时间将元素分配到滚动窗口中。创建 TumblingProcessingTimeWindows 需要提供窗口大小 size、窗口偏移量 offset 以及窗口错峰策略 windowStagger 三个参数：
```java
public class TumblingProcessingTimeWindows extends WindowAssigner<Object, TimeWindow> {
    // 窗口大小
    private final long size;
    // 窗口偏移量
    private final long globalOffset;
    // 窗口错峰策略
    private final WindowStagger windowStagger;
    private TumblingProcessingTimeWindows(long size, long offset, WindowStagger windowStagger) {
        if (Math.abs(offset) >= size) {
            throw new IllegalArgumentException(xxx);
        }
        this.size = size;
        this.globalOffset = offset;
        this.windowStagger = windowStagger;
    }
    ...
}
```
Flink 为我们提供了三个便捷方法 of 来创建滚动事件时间窗口分配器，一个只需要指定窗口大小，一个只需要指定窗口大小和窗口偏移量 offset(时间偏移量可以更好的控制窗口的开始时间)，另一个指定窗口大小和时间偏移量之外还需要指定窗口错峰策略：
```java
// 创建一个滚动处理时间窗口分配器 只指定窗口大小
public static TumblingProcessingTimeWindows of(Time size) {
    return new TumblingProcessingTimeWindows(size.toMilliseconds(), 0, WindowStagger.ALIGNED);
}
// 创建一个滚动处理时间窗口分配器 指定窗口大小和时间偏移量
public static TumblingProcessingTimeWindows of(Time size, Time offset) {
    return new TumblingProcessingTimeWindows(
            size.toMilliseconds(), offset.toMilliseconds(), WindowStagger.ALIGNED);
}
// 创建一个滚动处理时间窗口分配器 指定窗口大小、时间偏移量以及窗口错峰策略
public static TumblingProcessingTimeWindows of(
        Time size, Time offset, WindowStagger windowStagger) {
    return new TumblingProcessingTimeWindows(
            size.toMilliseconds(), offset.toMilliseconds(), windowStagger);
}
```
现在看一下滚动处理时间窗口分配器将元素分配到哪个窗口中：
```java
public Collection<TimeWindow> assignWindows(Object element, long timestamp, WindowAssignerContext context) {
    // 当前处理时间
    final long now = context.getCurrentProcessingTime();
    // 窗口错峰偏移量
    if (staggerOffset == null) {
        staggerOffset = windowStagger.getStaggerOffset(context.getCurrentProcessingTime(), size);
    }
    // 窗口的开始时间
    long start = TimeWindow.getWindowStartWithOffset(now, (globalOffset + staggerOffset) % size, size);
    // 分配到的具体窗口
    return Collections.singletonList(new TimeWindow(start, start + size));
}
```
staggerOffset 默认值是空的，会根据选择的窗口错峰策略 WindowStagger 设置偏移量，然后根据 timestamp 和 size 计算出窗口的开始时间，最后返回一个存储 TimeWindow 的单例集合。跟滚动事件时间窗口不同的是，计算窗口开始时间使用的时间戳不是元素本身的事件时间戳 timestamp，而是当前处理时间。滚动处理时间窗口分配器会根据当前处理时间将元素分配到滚动窗口中。

如果没有指定窗口错峰策略，默认为 WindowStagger.ALIGNED，staggerOffset 为 0，窗口计算开始时间与如下代码等价：
```java
TimeWindow.getWindowStartWithOffset(now, globalOffset, size);
```

此外窗口分配器还提供了默认的触发器 ProcessingTimeTrigger 来决定窗口计算的触发时机：
```java
public Trigger<Object, TimeWindow> getDefaultTrigger(StreamExecutionEnvironment env) {
    return ProcessingTimeTrigger.create();
}
```

### 2.3 SlidingEventTimeWindows

滑动处理时间窗口分配器 SlidingEventTimeWindows 根据元素的事件时间戳将元素分配到滑动窗口中。创建 SlidingEventTimeWindows 需要提供窗口大小 size、窗口滑动步长 slide 以及窗口偏移量 offset 三个参数：
```java
public class SlidingEventTimeWindows extends WindowAssigner<Object, TimeWindow> {
    // 窗口大小
    private final long size;
    // 滑动步长
    private final long slide;
    // 窗口偏移量
    private final long offset;
    protected SlidingEventTimeWindows(long size, long slide, long offset) {
        if (Math.abs(offset) >= slide || size <= 0) {
            throw new IllegalArgumentException(xxx);
        }
        this.size = size;
        this.slide = slide;
        this.offset = offset;
    }
}
```
Flink 为我们提供了两个便捷方法 of 来创建滑动事件时间窗口分配器，其中一个只指定窗口大小，另一个指定窗口大小和时间偏移量(时间偏移量可以更好的控制窗口的开始时间)：
```java
// 创建一个滑动事件时间窗口分配器 指定窗口大小和滑动步长
public static SlidingEventTimeWindows of(Time size, Time slide) {
    return new SlidingEventTimeWindows(size.toMilliseconds(), slide.toMilliseconds(), 0);
}
// 创建一个滑动事件时间窗口分配器 指定窗口大小滑动步长以及时间偏移量
public static SlidingEventTimeWindows of(Time size, Time slide, Time offset) {
    return new SlidingEventTimeWindows(
            size.toMilliseconds(), slide.toMilliseconds(), offset.toMilliseconds());
}
```
现在看一下滑动事件时间窗口分配器将元素分配到哪个窗口中：
```java
public Collection<TimeWindow> assignWindows(Object element, long timestamp, WindowAssignerContext context) {
    if (timestamp > Long.MIN_VALUE) {
        // 窗口个数 size / slide
        List<TimeWindow> windows = new ArrayList<>((int) (size / slide));
        // 最后一个窗口的开始时间戳
        long lastStart = TimeWindow.getWindowStartWithOffset(timestamp, offset, slide);
        // 分配的每个窗口
        for (long start = lastStart; start > timestamp - size; start -= slide) {
            windows.add(new TimeWindow(start, start + size));
        }
        return windows;
    } else {
        throw new RuntimeException(xxx);
    }
}
```
如果你使用的是事件时间并指定了时间戳提取 assignTimestampsAndWatermarks，元素的时间戳肯定是大于 Long.MIN_VALUE，否则需要检查你写的代码是否有问题。跟滚动事件时间窗口一样都是根据元素本身的事件时间戳 timestamp 来计算窗口的开始时间戳，需要注意的是在这滑动窗口指定滑动步长来计算窗口的开始时间戳。如下图所示，计算出 lastStart 是最后一个窗口的开始时间戳，每减去一个滑动步长就是前一个窗口的开始时间戳。滑动窗口最终将一个元素分配给 `(int) (size / slide)` 个窗口。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-code-window-assigner-2.png?raw=true)

此外窗口分配器还提供了默认的触发器 EventTimeTrigger 来决定窗口计算的触发时机：
```java
public Trigger<Object, TimeWindow> getDefaultTrigger(StreamExecutionEnvironment env) {
    return EventTimeTrigger.create();
}
```

### 2.4 SlidingProcessingTimeWindows

滑动处理时间窗口分配器 SlidingProcessingTimeWindows 根据当前系统时间将元素分配到滑动窗口中。创建 SlidingProcessingTimeWindows 需要提供窗口大小 size、窗口滑动步长 slide 以及窗口偏移量 offset 三个参数：
```java
public class SlidingProcessingTimeWindows extends WindowAssigner<Object, TimeWindow> {
    // 窗口大小
    private final long size;
    // 窗口偏移量
    private final long offset;
    // 滑动步长
    private final long slide;
    private SlidingProcessingTimeWindows(long size, long slide, long offset) {
        if (Math.abs(offset) >= slide || size <= 0) {
            throw new IllegalArgumentException(xxx);
        }
        this.size = size;
        this.slide = slide;
        this.offset = offset;
    }
    ...
}
```
Flink 为我们提供了两个便捷方法 of 来创建滚动处理时间窗口分配器，其中一个只指定窗口大小，另一个指定窗口大小和时间偏移量(时间偏移量可以更好的控制窗口的开始时间)：
```java
// 创建一个滑动处理时间窗口分配器 指定窗口大小和滑动步长
public static SlidingProcessingTimeWindows of(Time size, Time slide) {
    return new SlidingProcessingTimeWindows(size.toMilliseconds(), slide.toMilliseconds(), 0);
}
// 创建一个滑动处理时间窗口分配器 指定窗口大小滑动步长以及时间偏移量
public static SlidingProcessingTimeWindows of(Time size, Time slide, Time offset) {
    return new SlidingProcessingTimeWindows(size.toMilliseconds(), slide.toMilliseconds(), offset.toMilliseconds());
}
```

现在看一下滑动处理时间窗口分配器将元素分配到哪个窗口中：
```java
public Collection<TimeWindow> assignWindows(Object element, long timestamp, WindowAssignerContext context) {
    // 当前处理时间
    timestamp = context.getCurrentProcessingTime();
    // 分配的窗口个数 (size / slide)
    List<TimeWindow> windows = new ArrayList<>((int) (size / slide));
    // 最后一个窗口的开始时间
    long lastStart = TimeWindow.getWindowStartWithOffset(timestamp, offset, slide);
    for (long start = lastStart; start > timestamp - size; start -= slide) {
        windows.add(new TimeWindow(start, start + size));
    }
    return windows;
}
```
滑动处理时间窗口分配器的分配窗口逻辑跟滑动事件时间窗口一样，不同点就是计算窗口开始时间使用的时间戳不是元素本身的事件时间戳 timestamp，而是当前处理时间。滑动处理时间窗口分配器会根据当前处理时间将元素分配到滑动窗口中。

此外窗口分配器还提供了默认的触发器 ProcessingTimeTrigger 来决定窗口计算的触发时机：
```java
public Trigger<Object, TimeWindow> getDefaultTrigger(StreamExecutionEnvironment env) {
    return ProcessingTimeTrigger.create();
}
```

### 2.5 GlobalWindows

全局窗口分配器 GlobalWindows 将所有元素分配到同一个全局窗口 GlobalWindow 中。Flink 提供了一个 create 方法来创建 GlobalWindows，不需要提供任何参数：
```java
public class GlobalWindows extends WindowAssigner<Object, GlobalWindow> {
    private GlobalWindows() {}
    public static GlobalWindows create() {
        return new GlobalWindows();
    }
}
```
全局窗口分配器将所有元素分配到同一个全局窗口 GlobalWindow 中，通过 GlobalWindow 的单例模式获取同一个全局窗口：
```java
public Collection<GlobalWindow> assignWindows(Object element, long timestamp, WindowAssignerContext context) {
    return Collections.singletonList(GlobalWindow.get());
}
```
此外窗口分配器还提供的默认的触发器是内部自定义实现的 NeverTrigger：
```java
public Trigger<Object, GlobalWindow> getDefaultTrigger(StreamExecutionEnvironment env) {
    return new NeverTrigger();
}
```
默认实现的 NeverTrigger 永远都不会触发窗口计算，因此如果要使用全局窗口需要借助其他 Trigger 来触发计算，如果不对全局窗口指定 Trigger，窗口不会触发计算。
