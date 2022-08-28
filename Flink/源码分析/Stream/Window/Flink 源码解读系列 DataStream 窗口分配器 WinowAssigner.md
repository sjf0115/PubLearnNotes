在前一篇文章 [Flink 源码解读系列 DataStream 窗口 Window 实现](https://smartsi.blog.csdn.net/article/details/126574164) 中，我们了解到 Flink 窗口 Window 有两种具体实现，一个是 TimeWindow，一个是 GlobalWindow。有了窗口之后，我们如何将元素分配给窗口呢？在这篇文章中我们重点了解一下窗口分配器 WindowAssigner 是如何将输入流中的元素划分给窗口的。

## 1. 如何指定窗口分配器

在了解窗口分配器 WindowAssigner 内部实现之前，我们先看一下如何为窗口算子指定窗口分配器的。Flink 为我们提供了几种指定窗口分配器的方式，这还需要取决于输入流是不是 KeyedStream。如果是在 KeyedStream 上使用窗口，我们可以使用如下三个方法指定窗口分配器：
- window()
- timeWindow()
- countWindow()

如果是在 DataStream 上使用窗口，我们可以使用如下三个方法指定窗口分配器：
- windowAll
- timeWindowAll()
- countWindowAll()

无论是 KeyedStream 还是 DataStream，实现的基本原理基本一致。

### 1.1 window

对于 KeyedStream，可以通过 window 方法指定你选择的窗口分配器，而对于 DataStream 则需要使用 windowAll 方法指定：
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

需要注意的是在 Flink 1.12 版本中，DataStream API 中的 timeWindow() 方法已经标注为 `@Deprecated`。Flink 社区推荐使用带 TumblingEventTimeWindows、SlidingEventTimeWindows、TumblingProcessingTimeWindows 或 SlidingProcessingTimeWindows 的 window(WindowAssigner) 方法。主要原因是在这个版本中弃用了 DataStream API 中的时间特性，从而导致无法继续基于时间特性来判断是基于处理时间的窗口还是基于事件时间的窗口，有关详细信息，请参阅 []()。

> [FLINK-19318](FLINK-19318)

### 1.3 countWindow

```java
// KeyedStream
public WindowedStream<T, KEY, GlobalWindow> countWindow(long size) {
	return window(GlobalWindows.create()).trigger(PurgingTrigger.of(CountTrigger.of(size)));
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

### 2.1 TumblingEventTimeWindows



### 2.2 TumblingProcessingTimeWindows

滚动处理时间窗口分配器 TumblingProcessingTimeWindows 根据当前系统时间将元素分配到滚动窗口中。Flink 为我们提供了两个便捷方法 of 来创建滚动处理时间窗口分配器，其中一个只指定窗口大小，另一个指定窗口大小和时间偏移量(时间偏移量可以更好的控制窗口的开始时间)：
```java
public class TumblingProcessingTimeWindows extends WindowAssigner<Object, TimeWindow> {
    // 窗口大小
    private final long size;
    // 窗口偏移量
    private final long offset;
    private TumblingProcessingTimeWindows(long size, long offset) {
        if (Math.abs(offset) >= size) {
            // 偏移量不能大于窗口的大小
            throw new IllegalArgumentException(xxx);
        }
        this.size = size;
        this.offset = offset;
    }
    ...
}
// 创建一个滚动处理时间窗口分配器 只指定窗口大小
public static TumblingProcessingTimeWindows of(Time size) {
    return new TumblingProcessingTimeWindows(size.toMilliseconds(), 0);
}
// 创建一个滚动处理时间窗口分配器 指定窗口大小和时间偏移量
public static TumblingProcessingTimeWindows of(Time size, Time offset) {
    return new TumblingProcessingTimeWindows(size.toMilliseconds(), offset.toMilliseconds());
}
```
如果您希望创建一个每小时的窗口，但窗口必须从每小时的第 15 分钟开始，那您可以使用 of(Time.hours(1), Time.minutes(15)) 来分配创建窗口，那么您将获取从 0:15:00、1:15:00、2:15:00 等开始的时间窗口。此外，如果您住在不使用 UTC±00:00 时间的地方，例如使用 UTC+08:00 的中国，你想要一个大小为一天的时间窗口，并且窗口从当地时间的每 00:00:00 开始，您可以使用 of(Time.days(1),Time.hours(-8))。offset 的参数是 Time.hours(-8) 因为 UTC+08:00 比 UTC+08:00 早 8 小时 UTC 时间。

窗口分配器最核心的目标就是将元素分配到窗口中，具体分配到哪个窗口需要通过 assignWindows 方法实现：
```java
public Collection<TimeWindow> assignWindows(Object element, long timestamp, WindowAssignerContext context) {
    // 当前处理时间
    final long now = context.getCurrentProcessingTime();
    // 窗口的开始时间
    long start = TimeWindow.getWindowStartWithOffset(now, offset, size);
    // 分配到的具体窗口
    return Collections.singletonList(new TimeWindow(start, start + size));
}

// 计算窗口的开始时间
public static long getWindowStartWithOffset(long timestamp, long offset, long windowSize) {
    return timestamp - (timestamp - offset + windowSize) % windowSize;
}
```
> 滚动窗口分配器在一个时间点只能将一个元素分配到一个窗口中

此外窗口分配器还提供了默认的触发器 ProcessingTimeTrigger 来决定窗口计算的触发时机：
```java
public Trigger<Object, TimeWindow> getDefaultTrigger(StreamExecutionEnvironment env) {
    return ProcessingTimeTrigger.create();
}
```

### 2.3 SlidingEventTimeWindows



### 2.4 SlidingProcessingTimeWindows

滑动处理时间窗口分配器 SlidingProcessingTimeWindows 根据当前系统时间将元素分配到滑动窗口中。Flink 为我们提供了两个便捷方法 of 来创建滚动处理时间窗口分配器，其中一个只指定窗口大小，另一个指定窗口大小和时间偏移量(时间偏移量可以更好的控制窗口的开始时间)：
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
// 创建一个滑动处理时间窗口分配器 指定窗口大小和滑动步长
public static SlidingProcessingTimeWindows of(Time size, Time slide) {
    return new SlidingProcessingTimeWindows(size.toMilliseconds(), slide.toMilliseconds(), 0);
}
// 创建一个滑动处理时间窗口分配器 指定窗口大小滑动步长以及时间偏移量
public static SlidingProcessingTimeWindows of(Time size, Time slide, Time offset) {
    return new SlidingProcessingTimeWindows(size.toMilliseconds(), slide.toMilliseconds(), offset.toMilliseconds());
}
```
跟滚动窗口分配器一样，如果您希望创建一个每小时的窗口，但窗口必须从每小时的第 15 分钟开始，那您可以使用窗口偏移量 offset 来指定 15分钟的偏移量：
```java
of(Time.hours(1), Time.minutes(15))
```

无论哪种分配器，窗口分配器最核心的目标就是将元素分配到窗口中。具体分配到哪个窗口需要通过 assignWindows 方法实现：
```java
public Collection<TimeWindow> assignWindows(Object element, long timestamp, WindowAssignerContext context) {
    // 当前处理时间
    timestamp = context.getCurrentProcessingTime();
    // 分配的窗口个数
    List<TimeWindow> windows = new ArrayList<>((int) (size / slide));
    // 最后一个窗口的开始时间
    long lastStart = TimeWindow.getWindowStartWithOffset(timestamp, offset, slide);
    for (long start = lastStart; start > timestamp - size; start -= slide) {
        windows.add(new TimeWindow(start, start + size));
    }
    return windows;
}

// 计算窗口的开始时间
public static long getWindowStartWithOffset(long timestamp, long offset, long windowSize) {
    return timestamp - (timestamp - offset + windowSize) % windowSize;
}
```

滑动窗口分配器在一个时间点可以将一个元素分配到一个或者多个窗口中。

此外窗口分配器还提供了默认的触发器 ProcessingTimeTrigger 来决定窗口计算的触发时机：
```java
public Trigger<Object, TimeWindow> getDefaultTrigger(StreamExecutionEnvironment env) {
    return ProcessingTimeTrigger.create();
}
```

### 2.5 GlobalWindows

### 2.6 MergingWindowAssigner



....
