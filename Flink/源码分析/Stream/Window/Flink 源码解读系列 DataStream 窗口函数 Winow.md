
## 1. 如何指定窗口分配器

在指定窗口分配器时，Flink 为我们提供了如下几种选择。如果是在 KeyedStream 上使用窗口，我们可以使用如下三个方法指定窗口分配器：
- window()
- timeWindow()
- countWindow()

如果是在 DataStream 上使用窗口，我们可以使用如下三个方法指定窗口分配器：
- windowAll
- timeWindowAll()
- countWindowAll()

### 1.1 window

使用窗口我们要做的第一件事就是你的数据流是否根据 key 进行分流（分区）。这必须在定义窗口之前使用 keyBy() 进行分流。在确定数据流是否根据 key 分流之后，下一步就是定义窗口分配器（WindowAssigners）。窗口分配器依赖于我们上面做的第一件事，如果在使用 keyBy() 的数据流上使用窗口，则调用 window() 函数，否则使用 windowAll() 函数：

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



上述第一个函数是窗口化 `KeyedStream` 数据流为滚动窗口（只有一个参数，窗口大小），第二个函数窗口化为滑动窗口（有两个参数，窗口大小以及滑动大小）。具体是基于事件时间的窗口还是基于处理时间的窗口，取决于你你设置的　`TimeCharacteristic`。例如下面设置为基于事件时间：
```java
environment.setStreamTimeCharacteristic(TimeCharacteristic.EventTime)
```

滚动时间窗口：
```java
// KeyedStream
public WindowedStream<T, KEY, TimeWindow> timeWindow(Time size) {
    if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
        return window(TumblingProcessingTimeWindows.of(size));
    } else {
        return window(TumblingEventTimeWindows.of(size));
    }
}
// DataStream
public AllWindowedStream<T, TimeWindow> timeWindowAll(Time size) {
	if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
		return windowAll(TumblingProcessingTimeWindows.of(size));
	} else {
		return windowAll(TumblingEventTimeWindows.of(size));
	}
}
```

滑动时间窗口：
```java
// KeyedStream
public WindowedStream<T, KEY, TimeWindow> timeWindow(Time size, Time slide) {
    if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
        return window(SlidingProcessingTimeWindows.of(size, slide));
    } else {
        return window(SlidingEventTimeWindows.of(size, slide));
    }
}
// DataStream
public AllWindowedStream<T, TimeWindow> timeWindowAll(Time size, Time slide) {
    if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
    	return windowAll(SlidingProcessingTimeWindows.of(size, slide));
    } else {
    	return windowAll(SlidingEventTimeWindows.of(size, slide));
    }
}
```
从上面代码中可以看到 timeWindow 函数只是对 window 函数的一次封装，封装之后我们不用关心到底是使用滚动事件时间窗口分配器 TumblingEventTimeWindows、滚动处理时间窗口分配器 TumblingProcessingTimeWindows、滑动事件时间窗口分配器 SlidingEventTimeWindows 还是滑动处理时间窗口分配器 SlidingProcessingTimeWindows。timeWindow 会根据你设置的时间特性 TimeCharacteristic 以及是否有滑动步长来自选选择对应的窗口分配器。例如时间特性为事件时间 EventTime，只有窗口大小没有滑动步长，timeWindow 会你提供滚动事件时间窗口分配器 TumblingEventTimeWindows。这样方式更简洁一些，出错的可能性也更低，不需要记住各种不同的窗口分配器。

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
```

```java
public Collection<TimeWindow> assignWindows(Object element, long timestamp, WindowAssignerContext context) {
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


### 2.3 SlidingEventTimeWindows

### 2.4 SlidingProcessingTimeWindows

### 2.5 GlobalWindows

### 2.6 MergingWindowAssigner



....
