

在指定窗口分配器时，我们有几种选择：
- `window()`
- `windowAll`
- `timeWindow()`
- `timeWindowAll()`
- `countWindow()`
- `countWindowAll()`



```java
public <W extends Window> WindowedStream<T, KEY, W> window(WindowAssigner<? super T, W> assigner) {
    return new WindowedStream<>(this, assigner);
}
```


```java
public WindowedStream<T, KEY, TimeWindow> timeWindow(Time size) {
    if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
        return window(TumblingProcessingTimeWindows.of(size));
    } else {
        return window(TumblingEventTimeWindows.of(size));
    }
}
```

```java
public WindowedStream<T, KEY, TimeWindow> timeWindow(Time size, Time slide) {
    if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
        return window(SlidingProcessingTimeWindows.of(size, slide));
    } else {
        return window(SlidingEventTimeWindows.of(size, slide));
    }
}
```

在 Flink 1.12 中，默认的流时间特性已更改为 `EventTime`，因此您不再需要调用此方法来启用事件时间支持。 显式使用处理时间窗口和计时器在事件时间模式下工作。 如果您需要禁用水印，请使用 `ExecutionConfig.setAutoWatermarkInterval(long)`。 如果您使用的是 `IngestionTime`，请手动设置适当的 `WatermarkStrategy`。 如果您正在使用通用的“时间窗口”操作（例如基于时间特征改变行为的 `KeyedStream.timeWindow()`，请使用明确指定处理时间或事件时间的等效操作。


### 1. window 与 windowAll

使用窗口我们要做的第一件事就是你的数据流是否根据 `key` 进行分流（分区）。这必须在定义窗口之前使用 `keyBy()` 进行分流。在确定数据流是否根据 `key` 分流之后，下一步就是定义窗口分配器（`WindowAssigners`）。窗口分配器依赖于我们上面做的第一件事，如果在使用 `keyBy()` 的数据流上使用窗口，则调用 `window()` 函数，否则使用 `windowAll()` 函数：
```java
@PublicEvolving
	public <W extends Window> WindowedStream<T, KEY, W> window(WindowAssigner<? super T, W> assigner) {
	return new WindowedStream<>(this, assigner);
}

public <W extends Window> AllWindowedStream<T, W> windowAll(WindowAssigner<? super T, W> assigner) {
	return new AllWindowedStream<>(this, assigner);
}
```



使用 `windowXXX()` 函数需要指定是使用滚动事件时间窗口分配器（`TumblingEventTimeWindows`），滚动处理时间窗口分配器（`TumblingProcessingTimeWindows`），滑动事件时间窗口分配器（`SlidingEventTimeWindows`）还是滑动处理时间窗口分配器（`SlidingProcessingTimeWindows`）。如下示例代码生成基于处理时间的滑动窗口：
```java
stream.keyBy(0).window(SlidingProcessingTimeWindows.of(Time.hours(2), Time.hours(1)))

stream.windowAll(SlidingProcessingTimeWindows.of(Time.hours(2), Time.hours(1)))
```







### 2. timeWindow()与timeWindowAll()

```java
public WindowedStream<T, KEY, TimeWindow> timeWindow(Time size) {
	if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
		return window(TumblingProcessingTimeWindows.of(size));
	} else {
		return window(TumblingEventTimeWindows.of(size));
	}
}

public WindowedStream<T, KEY, TimeWindow> timeWindow(Time size, Time slide) {
	if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
		return window(SlidingProcessingTimeWindows.of(size, slide));
	} else {
		return window(SlidingEventTimeWindows.of(size, slide));
	}
}
```
上述第一个函数是窗口化 `KeyedStream` 数据流为滚动窗口（只有一个参数，窗口大小），第二个函数窗口化为滑动窗口（有两个参数，窗口大小以及滑动大小）。具体是基于事件时间的窗口还是基于处理时间的窗口，取决于你你设置的　`TimeCharacteristic`。例如下面设置为基于事件时间：
```java
environment.setStreamTimeCharacteristic(TimeCharacteristic.EventTime)
```
我们看到 `timeWindow()` 函数是对 `window` 函数的一次封装，封装之后我们不用关心到底是使用滚动事件时间窗口分配器（`TumblingEventTimeWindows`），滚动处理时间窗口分配器（`TumblingProcessingTimeWindows`），滑动事件时间窗口分配器（`SlidingEventTimeWindows`）还是滑动处理时间窗口分配器（`SlidingProcessingTimeWindows`），我们只需要提供至多两个参数即可（窗口大小，如果是滑动窗口再提供滑动大小），这样对我们来说更简洁一些，出错的可能性也更低。

```java
public AllWindowedStream<T, TimeWindow> timeWindowAll(Time size) {
	if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
		return windowAll(TumblingProcessingTimeWindows.of(size));
	} else {
		return windowAll(TumblingEventTimeWindows.of(size));
	}
}

public AllWindowedStream<T, TimeWindow> timeWindowAll(Time size, Time slide) {
	if (environment.getStreamTimeCharacteristic() == TimeCharacteristic.ProcessingTime) {
		return windowAll(SlidingProcessingTimeWindows.of(size, slide));
	} else {
		return windowAll(SlidingEventTimeWindows.of(size, slide));
	}
}
```

我们来看看如何使用：
```java
# Non-Keyed Strem 上滑动窗口
stream.timeWindowAll(Time.hours(2), Time.hours(1))
```

跟上面的类似，`timeWindowAll()` 函数是对 `windowAll` 函数的一次封装。

### 3. countWindow()与countWindowAll()

```java
public WindowedStream<T, KEY, GlobalWindow> countWindow(long size) {
	return window(GlobalWindows.create()).trigger(PurgingTrigger.of(CountTrigger.of(size)));
}

public WindowedStream<T, KEY, GlobalWindow> countWindow(long size, long slide) {
	return window(GlobalWindows.create())
			.evictor(CountEvictor.of(size))
			.trigger(CountTrigger.of(slide));
}

public AllWindowedStream<T, GlobalWindow> countWindowAll(long size) {
	return windowAll(GlobalWindows.create()).trigger(PurgingTrigger.of(CountTrigger.of(size)));
}

public AllWindowedStream<T, GlobalWindow> countWindowAll(long size, long slide) {
	return windowAll(GlobalWindows.create())
			.evictor(CountEvictor.of(size))
			.trigger(CountTrigger.of(slide));
}
```






....
