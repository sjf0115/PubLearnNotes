
> Flink 1.13.5

在流处理应用中，数据是连续不断的，因此我们不可能等到所有数据都到了才开始处理。当然我们可以每来一条消息就处理一次，但是有时我们需要做一些聚合类的处理，例如计算在过去 1 分钟内有多少用户点击了我们的网页。在这种情况下，我们必须定义一个窗口，用来收集最近一分钟内的数据，并对这个窗口内的数据进行计算。

窗口本质上是将无界数据流进行有界数据处理的过程，一般来说窗口在无界数据流上定义了一组有限的元素。可以基于时间、元素个数、元素个数和时间的组合或者一些自定义逻辑来将数据分配给不同窗口。在 Flink 的 DataStream API 中窗口使用 Window 来表示：
```java
public abstract class Window {
    public abstract long maxTimestamp();
}
```
Window 是一个表示有界数据流集合的抽象类，只提供了一个抽象方法：
```java
public abstract long maxTimestamp();
```
使用该方法获取一个窗口的最大时间戳。

> 需要注意的是继承 Window 抽象类的子类需要实现 equals 和 hashCode 这两个方法，以便在逻辑上相同的两个 Window 被认为是同一个。

Flink 提供了两个窗口的具体实现：TimeWindow 和 GlobalWindow。

## 1. TimeWindow

### 1.1 定义

就如名字所说的，TimeWindow 根据时间对数据流进行分组，表示一个时间间隔窗口，通过其构造器的两个属性也可以看出：
- start：窗口开始时间戳
- end：窗口结束时间戳
所以 TimeWindow 表示的是 [start, end) 左开右闭区间内的时间间隔。窗口的最大时间戳 maxTimestamp 也自然的返回 end - 1：
```java
public class TimeWindow extends Window {
    // 窗口开始时间戳
    private final long start;
    // 窗口结束时间戳
    private final long end;
    public TimeWindow(long start, long end) {
        this.start = start;
        this.end = end;
    }
    // 窗口的最大时间戳
    @Override
    public long maxTimestamp() {
        return end - 1;
    }
    ...
}
```

### 1.2 equals 和 hashCode

上述中我们说过继承 Window 抽象类的子类需要实现 equals 和 hashCode 这两个方法，TimeWindow 也不例外：
```java
@Override
public boolean equals(Object o) {
    if (this == o) {
        return true;
    }
    if (o == null || getClass() != o.getClass()) {
        return false;
    }
    TimeWindow window = (TimeWindow) o;
    return end == window.end && start == window.start;
}
@Override
public int hashCode() {
    return MathUtils.longToIntWithBitMixing(start + end);
}
```
从上面可以看出拥有相同窗口开始时间戳 start 和窗口结束时间戳 end 的两个 TimeWindow 窗口会被认为是同一个窗口。

### 1.3 序列化

TimeWindow 也在内部实现了序列化器，该序列化器主要针对 start 和 end 两个属性：
```java
public static class Serializer extends TypeSerializerSingleton<TimeWindow> {
    ...
    @Override
    public void serialize(TimeWindow record, DataOutputView target) throws IOException {
        target.writeLong(record.start);
        target.writeLong(record.end);
    }
    @Override
    public TimeWindow deserialize(DataInputView source) throws IOException {
        long start = source.readLong();
        long end = source.readLong();
        return new TimeWindow(start, end);
    }
    ...
}
```

### 1.4 窗口开始时间

此外，TimeWindow 还定义了两个比较有用的工具方法，其中一个是 getWindowStartWithOffset。getWindowStartWithOffset 用来计算一个指定的时间戳所属窗口的开始时间戳：
```java
// timestamp 传入记录的时间戳
// offset 窗口时间偏移量
// windowSize 窗口大小
public static long getWindowStartWithOffset(long timestamp, long offset, long windowSize) {
    return timestamp - (timestamp - offset + windowSize) % windowSize;
}
```
在不指定 offset 的情况下，offset 默认为 0，那么窗口的开始时间戳计算公式简化如下：
```
start = timestamp - (timestamp - offset + windowSize) % windowSize
      = timestamp - (timestamp + windowSize) % windowSize
      = timestamp - timestamp % windowSize
```
窗口的开始时间戳等于记录时间戳减去该时间戳与窗口大小的余数，得到的结果肯定是窗口大小的整数倍。

那窗口时间偏移量 offset 什么时候需要指定呢？如果您希望创建一个每小时的窗口，但窗口必须从每小时的第 15 分钟开始，那您可以指定 15 分钟的偏移量来分配创建窗口，例如使用 TumblingProcessingTimeWindows.of(Time.hours(1), Time.minutes(15)) 创建基于处理时间的滚动窗口。那么您将获的从 0:15:00、1:15:00、2:15:00 等开始的时间窗口。此外，如果您住在不使用 UTC±00:00 时间的地区，例如使用 UTC+08:00 的中国，如果您要一个大小为一天的时间窗口，并且窗口从当地时间的 00:00:00 开始，您可以使用 of(Time.days(1),Time.hours(-8)) 来分配创建窗口。offset 的参数是 Time.hours(-8) 是因为 UTC+08:00 比 UTC+08:00 早 8 小时 UTC 时间。

### 1.5 窗口合并

TimeWindow 定义的另一个比较有用的工具方法就是 mergeWindows。mergeWindows 用来合并两个重叠的 TimeWindow：
```java
public static void mergeWindows(Collection<TimeWindow> windows, MergingWindowAssigner.MergeCallback<TimeWindow> c) {
    List<TimeWindow> sortedWindows = new ArrayList<>(windows);
    Collections.sort(
            sortedWindows,
            new Comparator<TimeWindow>() {
                @Override
                public int compare(TimeWindow o1, TimeWindow o2) {
                    return Long.compare(o1.getStart(), o2.getStart());
                }
            });

    List<Tuple2<TimeWindow, Set<TimeWindow>>> merged = new ArrayList<>();
    Tuple2<TimeWindow, Set<TimeWindow>> currentMerge = null;

    for (TimeWindow candidate : sortedWindows) {
        if (currentMerge == null) {
            currentMerge = new Tuple2<>();
            currentMerge.f0 = candidate;
            currentMerge.f1 = new HashSet<>();
            currentMerge.f1.add(candidate);
        } else if (currentMerge.f0.intersects(candidate)) {
            currentMerge.f0 = currentMerge.f0.cover(candidate);
            currentMerge.f1.add(candidate);
        } else {
            merged.add(currentMerge);
            currentMerge = new Tuple2<>();
            currentMerge.f0 = candidate;
            currentMerge.f1 = new HashSet<>();
            currentMerge.f1.add(candidate);
        }
    }
    if (currentMerge != null) {
        merged.add(currentMerge);
    }
    for (Tuple2<TimeWindow, Set<TimeWindow>> m : merged) {
        if (m.f1.size() > 1) {
            c.merge(m.f1, m.f0);
        }
    }
}
```

## 2. GlobalWindow

### 2.1 定义

和 TimeWindow 直观上最大的不同是，TimeWindow 定义了起止时间(start 和 end)，有明确的时间范围。而 GlobalWindow 是一个全局窗口，将具有相同 Key 的元素分配给同一个全局窗口。因此实现为单例模式：
```java
public class GlobalWindow extends Window {
    private static final GlobalWindow INSTANCE = new GlobalWindow();
    private GlobalWindow() {}
    public static GlobalWindow get() {
        return INSTANCE;
    }
    @Override
    public long maxTimestamp() {
        return Long.MAX_VALUE;
    }
    ...
}
```

GlobalWindow 的 maxTimestamp 的实现与 TimeWindow 的不同。TimeWindow 是一个有明确时间范围的时间间隔窗口，每个窗口的最大时间戳比较明确，maxTimestamp 方法返回窗口的上限 end - 1；而 GlobalWindow 比较特殊，没有起始时间和结束时间，相同 Key 的元素会进到同一个全局窗口中计算，因此 maxTimestamp 方法返回的是 Long 的最大值 Long.MAX_VALUE。

### 2.2 equals 和 hashCode

GlobalWindow 也需要重新实现 equals 和 hashCode 这两个方法，通过下面可以看到所有的全局窗口都是相同的：
```java
@Override
public boolean equals(Object o) {
    return this == o || !(o == null || getClass() != o.getClass());
}

@Override
public int hashCode() {
    return 0;
}
```

### 2.3 序列化

GlobalWindow 也在内部实现了全局窗口的序列化器：
```java
public static class Serializer extends TypeSerializerSingleton<GlobalWindow> {
    ...
    @Override
    public void serialize(GlobalWindow record, DataOutputView target) throws IOException {
        target.writeByte(0);
    }
    @Override
    public GlobalWindow deserialize(DataInputView source) throws IOException {
        source.readByte();
        return GlobalWindow.INSTANCE;
    }
    ...
}
```
