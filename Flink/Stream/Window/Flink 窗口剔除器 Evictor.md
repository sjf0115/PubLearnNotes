---
layout: post
author: smartsi
title: Flink 窗口剔除器 Evictor
date: 2021-09-05 19:30:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-windows-evictor
---

### 1. 简介

除了 [WindowAssigner]() 和 [Trigger]() 之外，Flink 的窗口模型还允许指定一个可选的剔除器 Evictor。Evictor 提供了在使用 [WindowFunction]() 之前或者之后从窗口中删除元素的能力。为此，Evictor 接口提供了两个方法：
```java
public interface Evictor<T, W extends Window> extends Serializable {
  // 在窗口函数调用之前删除元素
  void evictBefore(Iterable<TimestampedValue<T>> elements,
      int size, W window, EvictorContext evictorContext);
  // 在窗口函数调用之后删除元素
  void evictAfter(Iterable<TimestampedValue<T>> elements,
      int size, W window, EvictorContext evictorContext);
  interface EvictorContext {
      // 当前处理时间
      long getCurrentProcessingTime();
      MetricGroup getMetricGroup();
      // 当前Watermark
      long getCurrentWatermark();
  }
}
```
evictBefore() 用于在使用窗口函数之前从窗口中删除元素，而 evictAfter() 用于在使用窗口函数之后从窗口中删除元素。

### 2. 内置 Evictor

Flink 本身内置实现了三种 Evictor，分别是 CountEvictor、DeltaEvictor 和 TimeEvictor。

> 默认情况下，所有内置的 Evictors 都是在触发窗口函数之前使用。

#### 2.1 CountEvictor

CountEvictor 用于在窗口中保留用户指定数量的元素。如果窗口中的元素超过用户指定的阈值，会从窗口头部开始删除剩余元素。

##### 2.1.1 内部实现

CountEvictor 需要实现 Evictor 接口的 evictBefore 和 evictAfter 方法，以实现调用窗口函数之前和之后的窗口元素删除逻辑：
```java
private final boolean doEvictAfter;
@Override
public void evictBefore(
        Iterable<TimestampedValue<Object>> elements, int size, W window, EvictorContext ctx) {
    if (!doEvictAfter) {
        evict(elements, size, ctx);
    }
}

@Override
public void evictAfter(
        Iterable<TimestampedValue<Object>> elements, int size, W window, EvictorContext ctx) {
    if (doEvictAfter) {
        evict(elements, size, ctx);
    }
}
```
doEvictAfter 是在构造 CountEvictor 时传入的一个变量，用以指定是否在使用窗口函数之后对元素进行删除操作。如果不指定，默认为 false，即在使用窗口函数之后不对元素进行删除。从上面代码中可以看出，不论是 evictBefore，还是 evictAfter，最后都会调用 evict() 方法：
```java
private void evict(Iterable<TimestampedValue<Object>> elements, int size, EvictorContext ctx) {
    if (size <= maxCount) {
        return;
    } else {
        int evictedCount = 0;
        for (Iterator<TimestampedValue<Object>> iterator = elements.iterator();
                iterator.hasNext(); ) {
            iterator.next();
            evictedCount++;
            if (evictedCount > size - maxCount) {
                break;
            } else {
                iterator.remove();
            }
        }
    }
}
```
从上面可以看出，如果当前窗口元素个数小于等于用户指定的阈值则不做删除操作，否则会从窗口迭代器的头部开始删除多余的元素(size - maxCount)。

##### 2.1.2 如何使用

如下代码所示，在触发使用窗口函数之前保留2个元素：
```java
DataStream<Tuple2<String, Long>> result = stream
    // 格式转换
    .map(tuple -> Tuple2.of(tuple.f0, tuple.f1)).returns(Types.TUPLE(Types.STRING, Types.LONG))
    // 根据key分组
    .keyBy(new KeySelector<Tuple2<String, Long>, String>() {
        @Override
        public String getKey(Tuple2<String, Long> value) throws Exception {
            return value.f0;
        }
    })
    // 处理时间滚动窗口 滚动大小60s
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    // 在触发使用窗口函数之前保留2个元素
    .evictor(CountEvictor.of(2))
    // 窗口函数
    .process(new ProcessWindowFunction<Tuple2<String, Long>, Tuple2<String, Long>, String, TimeWindow>() {
        @Override
        public void process(String key, Context context, Iterable<Tuple2<String, Long>> elements, Collector<Tuple2<String, Long>> out) throws Exception {
            // Watermark
            long watermark = context.currentWatermark();
            String watermarkTime = DateUtil.timeStamp2Date(watermark);
            // 窗口开始与结束时间
            TimeWindow window = context.window();
            String start = DateUtil.timeStamp2Date(window.getStart());
            String end = DateUtil.timeStamp2Date(window.getEnd());
            // 窗口中元素
            List<Long> values = Lists.newArrayList();
            for (Tuple2<String, Long> element : elements) {
                values.add(element.f1);
            }
            LOG.info("[Process] Key: {}, Watermark: [{}|{}], Window: [{}|{}, {}|{}], Values: {}",
                    key, watermarkTime, watermark, start, window.getStart(), end, window.getEnd(), values
            );
        }
    });
```
> 完整代码请查阅[CountEvictorExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/CountEvictorExample.java)

假如输入流如下所示，我们一起看看输出效果：
```
A,1,2021-08-30 12:07:20
A,2,2021-08-30 12:07:22
A,3,2021-08-30 12:07:33
A,4,2021-08-30 12:07:44
A,5,2021-08-30 12:07:55
A,6,2021-08-30 12:08:34
A,7,2021-08-30 12:08:45
A,8,2021-08-30 12:08:56
A,9,2021-08-30 12:09:30
A,10,2021-08-30 12:09:35
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-evictor-1.png?raw=true)

#### 2.2 DeltaEvictor

根据用户自定的 DeltaFunction 函数来计算窗口中最后一个元素与其余每个元素之间的差值，如果差值大于等于用户指定的阈值就会删除该元素。

##### 2.2.1 内部实现

DeltaEvictor 与 CountEvictor 一样，都需要实现 Evictor 接口的 evictBefore 和 evictAfter 方法，只是最终调用的 evict() 函数的内部实现逻辑不一样：
```java
private void evict(Iterable<TimestampedValue<T>> elements, int size, EvictorContext ctx) {
    // 窗口最后一个元素
    TimestampedValue<T> lastElement = Iterables.getLast(elements);
    // 遍历整个窗口，与每一个元素进行比较
    for (Iterator<TimestampedValue<T>> iterator = elements.iterator(); iterator.hasNext(); ) {
        TimestampedValue<T> element = iterator.next();
        if (deltaFunction.getDelta(element.getValue(), lastElement.getValue())
                >= this.threshold) {
            iterator.remove();
        }
    }
}
```
> deltaFunction 函数以及 threshold 变量是在构造函数中传入的。

首先获取窗口中的最后一个元素并遍历整个窗口，然后调用用户指定的 deltaFunction 计算与每一个元素的差值。如果差值大于等于用户自定的阈值就删除该元素。

##### 2.2.2 如何使用

如下代码所示，在触发窗口函数计算之前剔除与最后一个元素值差大于等于1的元素：
```java
DataStream<Tuple2<String, Long>> result = stream
    // 格式转换
    .map(tuple -> Tuple2.of(tuple.f0, tuple.f1)).returns(Types.TUPLE(Types.STRING, Types.LONG))
    // 根据key分组
    .keyBy(new KeySelector<Tuple2<String, Long>, String>() {
        @Override
        public String getKey(Tuple2<String, Long> value) throws Exception {
            return value.f0;
        }
    })
    // 处理时间滚动窗口 滚动大小60s
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    // 剔除与最后一个元素值差大于1的元素
    .evictor(DeltaEvictor.of(1, new DeltaFunction<Tuple2<String, Long>>() {
        @Override
        public double getDelta(Tuple2<String, Long> oldDataPoint, Tuple2<String, Long> newDataPoint) {
            return oldDataPoint.f1 - newDataPoint.f1;
        }
    }))
    // 窗口函数
    .process(new ProcessWindowFunction<Tuple2<String, Long>, Tuple2<String, Long>, String, TimeWindow>() {
        @Override
        public void process(String key, Context context, Iterable<Tuple2<String, Long>> elements, Collector<Tuple2<String, Long>> out) throws Exception {
            // Watermark
            long watermark = context.currentWatermark();
            String watermarkTime = DateUtil.timeStamp2Date(watermark);
            // 窗口开始与结束时间
            TimeWindow window = context.window();
            String start = DateUtil.timeStamp2Date(window.getStart());
            String end = DateUtil.timeStamp2Date(window.getEnd());
            // 窗口中元素
            List<Long> values = Lists.newArrayList();
            for (Tuple2<String, Long> element : elements) {
                values.add(element.f1);
            }
            LOG.info("[Process] Key: {}, Watermark: [{}|{}], Window: [{}|{}, {}|{}], Values: {}",
                    key, watermarkTime, watermark, start, window.getStart(), end, window.getEnd(), values
            );
        }
    });
```
> 完整代码请查阅 [DeltaEvictorExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/DeltaEvictorExample.java)

假如输入流如下所示，我们一起看看输出效果：
```
A,4,2021-08-30 12:07:20
A,1,2021-08-30 12:07:22
A,3,2021-08-30 12:07:33
A,6,2021-08-30 12:07:44
A,3,2021-08-30 12:07:55
A,6,2021-08-30 12:08:34
A,5,2021-08-30 12:08:45
A,1,2021-08-30 12:08:56
A,6,2021-08-30 12:09:30
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-evictor-2.png?raw=true)

#### 2.3 TimeEvictor

以毫秒为单位的时间间隔 windowSize 作为参数，在窗口所有元素中找到最大时间戳 max_ts 并删除所有时间戳小于 max_ts - windowSize 的元素。我们可以理解为只保留最新 windowSize 毫秒内的元素。

##### 2.3.1 内部实现

TimeEvictor 与 DeltaEvictor、CountEvictor 一样，都需要实现 Evictor 接口的 evictBefore 和 evictAfter 方法，只是最终调用的 evict() 函数的内部实现逻辑不一样：
```java
private void evict(Iterable<TimestampedValue<Object>> elements, int size, EvictorContext ctx) {
    if (!hasTimestamp(elements)) {
        return;
    }
    // 最大时间戳
    long currentTime = getMaxTimestamp(elements);
    // windowSize 保留元素的时间间隔
    long evictCutoff = currentTime - windowSize;
    for (Iterator<TimestampedValue<Object>> iterator = elements.iterator();
            iterator.hasNext(); ) {
        TimestampedValue<Object> record = iterator.next();
        if (record.getTimestamp() <= evictCutoff) {
            iterator.remove();
        }
    }
}
// 第一个元素是否有时间戳
private boolean hasTimestamp(Iterable<TimestampedValue<Object>> elements) {
    Iterator<TimestampedValue<Object>> it = elements.iterator();
    if (it.hasNext()) {
        return it.next().hasTimestamp();
    }
    return false;
}
// 窗口中最大时间戳
private long getMaxTimestamp(Iterable<TimestampedValue<Object>> elements) {
    long currentTime = Long.MIN_VALUE;
    for (Iterator<TimestampedValue<Object>> iterator = elements.iterator();
            iterator.hasNext(); ) {
        TimestampedValue<Object> record = iterator.next();
        currentTime = Math.max(currentTime, record.getTimestamp());
    }
    return currentTime;
}
```
首先获取当前窗口中最大的时间戳，减去用户指定时间间隔 windowSize，得到一个 evictCutoff，然后遍历窗口全部元素，删除时间戳小于等于 evictCutoff 的元素。

##### 2.3.2 如何使用

如下代码所示，在触发窗口函数计算之前只保留最近10s内的元素：
```java
DataStream<Tuple2<String, Long>> result = stream
    // 格式转换
    .map(tuple -> Tuple2.of(tuple.f0, tuple.f1)).returns(Types.TUPLE(Types.STRING, Types.LONG))
    // 根据key分组
    .keyBy(new KeySelector<Tuple2<String, Long>, String>() {
        @Override
        public String getKey(Tuple2<String, Long> value) throws Exception {
            return value.f0;
        }
    })
    // 处理时间滚动窗口 滚动大小60s
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    // 保留窗口中最近10s内的元素
    .evictor(TimeEvictor.of(Time.seconds(10)))
    // 窗口函数
    .process(new ProcessWindowFunction<Tuple2<String, Long>, Tuple2<String, Long>, String, TimeWindow>() {
        @Override
        public void process(String key, Context context, Iterable<Tuple2<String, Long>> elements, Collector<Tuple2<String, Long>> out) throws Exception {
            // Watermark
            long watermark = context.currentWatermark();
            String watermarkTime = DateUtil.timeStamp2Date(watermark);
            // 窗口开始与结束时间
            TimeWindow window = context.window();
            String start = DateUtil.timeStamp2Date(window.getStart());
            String end = DateUtil.timeStamp2Date(window.getEnd());
            // 窗口中元素
            List<Long> values = Lists.newArrayList();
            for (Tuple2<String, Long> element : elements) {
                values.add(element.f1);
            }
            LOG.info("[Process] Key: {}, Watermark: [{}|{}], Window: [{}|{}, {}|{}], Values: {}",
                    key, watermarkTime, watermark, start, window.getStart(), end, window.getEnd(), values
            );
        }
    });
```

> 完整代码请查阅[TimeEvictorExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/TimeEvictorExample.java)

假如输入流如下所示，我们一起看看输出效果：
```
A,1,2021-08-30 12:07:20
A,2,2021-08-30 12:07:22
A,3,2021-08-30 12:07:44
A,4,2021-08-30 12:07:55
A,5,2021-08-30 12:07:54
A,6,2021-08-30 12:08:34
A,7,2021-08-30 12:08:45
A,8,2021-08-30 12:08:56
A,9,2021-08-30 12:09:30
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-evictor-3.png?raw=true)

参考：
- [Evictors](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/dev/datastream/operators/windows/#evictors)
