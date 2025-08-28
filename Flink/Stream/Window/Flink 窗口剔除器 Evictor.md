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

除了 [WindowAssigner](https://smartsi.blog.csdn.net/article/details/126652876) 和 [Trigger](https://smartsi.blog.csdn.net/article/details/150937517) 之外，Flink 的窗口模型还允许指定一个可选的剔除器 Evictor。Evictor 提供了在使用 [WindowFunction](https://smartsi.blog.csdn.net/article/details/126681922) 之前或者之后从窗口中删除元素的能力。为此，Evictor 接口提供了两个方法：
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
`evictBefore()` 用于在使用窗口函数之前从窗口中删除元素，而 `evictAfter()` 用于在使用窗口函数之后从窗口中删除元素。

### 2. 内置 Evictor

Flink 本身内置实现了三种 Evictor，分别是 CountEvictor、DeltaEvictor 和 TimeEvictor。

> 默认情况下，所有内置的 Evictors 都是在触发窗口函数之前使用。

#### 2.1 CountEvictor

CountEvictor 用于在窗口中保留用户指定数量的元素。如果窗口中的元素超过用户指定的阈值，会从窗口头部开始删除剩余元素。

##### 2.1.1 内部实现

CountEvictor 需要实现 Evictor 接口的 evictBefore 和 evictAfter 方法：
```java
public interface Evictor<T, W extends Window> extends Serializable {
    void evictBefore(Iterable<TimestampedValue<T>> var1, int var2, W var3, EvictorContext var4);
    void evictAfter(Iterable<TimestampedValue<T>> var1, int var2, W var3, EvictorContext var4);
    ...
}
```
以实现调用窗口函数之前和之后的窗口元素删除逻辑：
```java
private final boolean doEvictAfter;
// 在调用窗口函数之前剔除元素
@Override
public void evictBefore(Iterable<TimestampedValue<Object>> elements, int size, W window, EvictorContext ctx) {
    if (!doEvictAfter) {
        evict(elements, size, ctx);
    }
}
// 在调用窗口函数之后剔除元素
@Override
public void evictAfter(Iterable<TimestampedValue<Object>> elements, int size, W window, EvictorContext ctx) {
    if (doEvictAfter) {
        evict(elements, size, ctx);
    }
}
```
从上面代码中可以看出调用窗口函数之前和之后的窗口元素删除逻辑最终都会通过 `evict` 方法实现，需要通过构造 CountEvictor 时传入的 `doEvictAfter` 变量来控制，指定是否在使用窗口函数之后对元素进行删除操作。如果不指定，默认为 false，即在使用窗口函数之前对元素进行删除。不论是 evictBefore，还是 evictAfter，最后都会调用 `evict` 方法：
```java
private void evict(Iterable<TimestampedValue<Object>> elements, int size, EvictorContext ctx) {
    if (size <= maxCount) {
        return;
    } else {
        int evictedCount = 0;
        for (Iterator<TimestampedValue<Object>> iterator = elements.iterator(); iterator.hasNext(); ) {
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
evict 的剔除逻辑是如果当前窗口元素个数小于等于用户指定的阈值则不做删除操作，否则会从窗口迭代器的头部开始删除多余的元素(size - maxCount)。

##### 2.1.2 如何使用

如下代码所示，在触发使用窗口函数之前保留2个元素：
```java
// 单词流
DataStream<WordCountTimestamp> words = source
        // 设置Watermark
        .assignTimestampsAndWatermarks(
                WatermarkStrategy.<WordCountTimestamp>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                        .withTimestampAssigner(new SerializableTimestampAssigner<WordCountTimestamp>() {
                            @Override
                            public long extractTimestamp(WordCountTimestamp wc, long recordTimestamp) {
                                return wc.getTimestamp();
                            }
                        })
        );

DataStream<WordCountTimestamp> result = words.keyBy(new KeySelector<WordCountTimestamp, String>() {
            @Override
            public String getKey(WordCountTimestamp wc) throws Exception {
                return wc.getWord();
            }
        })
        // 事件时间滚动窗口 滚动大小1分钟
        .window(TumblingEventTimeWindows.of(Time.minutes(1)))
        // 在触发使用窗口函数之前保留2个元素
        .evictor(CountEvictor.of(2))
        // 求和
        .reduce(new ReduceFunction<WordCountTimestamp>() {
            @Override
            public WordCountTimestamp reduce(WordCountTimestamp v1, WordCountTimestamp v2) throws Exception {
                int count = v1.getFrequency() + v2.getFrequency();
                String ids = v1.getId() + "," + v2.getId();
                Long timestamp = Math.max(v1.getTimestamp(), v2.getTimestamp());
                LOG.info("id: {}, count: {}, timestamp: {}", ids, count, timestamp);
                return new WordCountTimestamp(ids, v1.getWord(), count, timestamp);
            }
        });
```
> 完整代码请查阅[CountEvictorExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/evictor/CountEvictorExample.java)

实际效果如下所示：
```java
22:40:14,576 INFO  WordCountOutOfOrderSource [] - id: 1, word: a, frequency: 2, eventTime: 1662303772840|2022-09-04 23:02:52
22:40:15,585 INFO  WordCountOutOfOrderSource [] - id: 2, word: a, frequency: 1, eventTime: 1662303770844|2022-09-04 23:02:50
22:40:16,591 INFO  WordCountOutOfOrderSource [] - id: 3, word: a, frequency: 3, eventTime: 1662303773848|2022-09-04 23:02:53
22:40:17,597 INFO  WordCountOutOfOrderSource [] - id: 4, word: a, frequency: 2, eventTime: 1662303774866|2022-09-04 23:02:54
22:40:18,603 INFO  WordCountOutOfOrderSource [] - id: 5, word: a, frequency: 1, eventTime: 1662303777839|2022-09-04 23:02:57
22:40:19,609 INFO  WordCountOutOfOrderSource [] - id: 6, word: a, frequency: 2, eventTime: 1662303784887|2022-09-04 23:03:04
22:40:20,613 INFO  WordCountOutOfOrderSource [] - id: 7, word: a, frequency: 3, eventTime: 1662303776894|2022-09-04 23:02:56
22:40:21,619 INFO  WordCountOutOfOrderSource [] - id: 8, word: a, frequency: 1, eventTime: 1662303786891|2022-09-04 23:03:06
22:40:21,749 INFO  CountEvictorExample  [] - id: 5,7, count: 4, timestamp: 1662303777839
WordCountTimestamp{id='5,7', word='a', frequency=4, timestamp=1662303777839}
22:40:22,623 INFO  WordCountOutOfOrderSource [] - id: 9, word: a, frequency: 5, eventTime: 1662303778877|2022-09-04 23:02:58
22:40:23,626 INFO  WordCountOutOfOrderSource [] - id: 10, word: a, frequency: 4, eventTime: 1662303791904|2022-09-04 23:03:11
22:40:24,633 INFO  WordCountOutOfOrderSource [] - id: 11, word: a, frequency: 1, eventTime: 1662303795918|2022-09-04 23:03:15
22:40:25,635 INFO  WordCountOutOfOrderSource [] - id: 12, word: a, frequency: 6, eventTime: 1662303779883|2022-09-04 23:02:59
22:40:26,639 INFO  WordCountOutOfOrderSource [] - id: 13, word: a, frequency: 2, eventTime: 1662303846254|2022-09-04 23:04:06
22:40:26,729 INFO  CountEvictorExample  [] - id: 10,11, count: 5, timestamp: 1662303795918
WordCountTimestamp{id='10,11', word='a', frequency=5, timestamp=1662303795918}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
```
可以看到窗口第一次触发时，只有 `5` 和 `7` 两个元素参与了计算，`1, 2, 3, 4` 4个元素在窗口触发计算之前被剔除器剔除了。

#### 2.2 DeltaEvictor

根据用户自定的 DeltaFunction 函数来计算窗口中最后一个元素与其余每个元素之间的差值，如果差值大于等于用户指定的阈值就会删除该元素。

##### 2.2.1 内部实现

DeltaEvictor 与 CountEvictor 一样，都需要实现 Evictor 接口的 evictBefore 和 evictAfter 方法，只是最终调用的 `evict()` 函数的内部实现逻辑不一样：
```java
private void evict(Iterable<TimestampedValue<T>> elements, int size, EvictorContext ctx) {
    // 窗口最后一个元素
    TimestampedValue<T> lastElement = Iterables.getLast(elements);
    // 遍历整个窗口，与每一个元素进行比较
    for (Iterator<TimestampedValue<T>> iterator = elements.iterator(); iterator.hasNext(); ) {
        TimestampedValue<T> element = iterator.next();
        if (deltaFunction.getDelta(element.getValue(), lastElement.getValue()) >= this.threshold) {
            iterator.remove();
        }
    }
}
```
> deltaFunction 函数以及 threshold 变量是在构造函数中传入的。

首先获取窗口中的最后一个元素并遍历整个窗口，然后调用用户指定的 deltaFunction 计算与每一个元素的差值。如果差值大于等于用户自定的阈值就删除该元素。

##### 2.2.2 如何使用

如下代码所示，在触发窗口函数计算之前剔除比最后一个元素值小的元素：
```java
// 单词流
DataStream<WordCountTimestamp> words = source
        // 设置Watermark
        .assignTimestampsAndWatermarks(
                WatermarkStrategy.<WordCountTimestamp>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                        .withTimestampAssigner(new SerializableTimestampAssigner<WordCountTimestamp>() {
                            @Override
                            public long extractTimestamp(WordCountTimestamp wc, long recordTimestamp) {
                                return wc.getTimestamp();
                            }
                        })
        );

DataStream<WordCountTimestamp> result = words.keyBy(new KeySelector<WordCountTimestamp, String>() {
            @Override
            public String getKey(WordCountTimestamp wc) throws Exception {
                return wc.getWord();
            }
        })
        // 事件时间滚动窗口 滚动大小1分钟
        .window(TumblingEventTimeWindows.of(Time.minutes(1)))
        // 剔除比最后一个元素值小的元素   (lastElement - element) >= threshold 则剔除
        .evictor(DeltaEvictor.of(1, new DeltaFunction<WordCountTimestamp>() {
            @Override
            public double getDelta(WordCountTimestamp wc, WordCountTimestamp lastWc) {
                return lastWc.getFrequency() - wc.getFrequency();
            }
        }))
        // 求和
        .reduce(new ReduceFunction<WordCountTimestamp>() {
            @Override
            public WordCountTimestamp reduce(WordCountTimestamp v1, WordCountTimestamp v2) throws Exception {
                int count = v1.getFrequency() + v2.getFrequency();
                String ids = v1.getId() + "," + v2.getId();
                Long timestamp = Math.max(v1.getTimestamp(), v2.getTimestamp());
                LOG.info("id: {}, count: {}, timestamp: {}", ids, count, timestamp);
                return new WordCountTimestamp(ids, v1.getWord(), count, timestamp);
            }
        });
```
> 完整代码请查阅 [DeltaEvictorExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/evictor/DeltaEvictorExample.java)

实际效果如下所示：
```java
23:26:17,593 INFO  WordCountOutOfOrderSource [] - id: 1, word: a, frequency: 2, eventTime: 1662303772840|2022-09-04 23:02:52
23:26:18,601 INFO  WordCountOutOfOrderSource [] - id: 2, word: a, frequency: 1, eventTime: 1662303770844|2022-09-04 23:02:50
23:26:19,607 INFO  WordCountOutOfOrderSource [] - id: 3, word: a, frequency: 3, eventTime: 1662303773848|2022-09-04 23:02:53
23:26:20,608 INFO  WordCountOutOfOrderSource [] - id: 4, word: a, frequency: 2, eventTime: 1662303774866|2022-09-04 23:02:54
23:26:21,614 INFO  WordCountOutOfOrderSource [] - id: 5, word: a, frequency: 1, eventTime: 1662303777839|2022-09-04 23:02:57
23:26:22,621 INFO  WordCountOutOfOrderSource [] - id: 6, word: a, frequency: 2, eventTime: 1662303784887|2022-09-04 23:03:04
23:26:23,624 INFO  WordCountOutOfOrderSource [] - id: 7, word: a, frequency: 3, eventTime: 1662303776894|2022-09-04 23:02:56
23:26:24,746 INFO  WordCountOutOfOrderSource [] - id: 8, word: a, frequency: 1, eventTime: 1662303786891|2022-09-04 23:03:06
23:26:24,905 INFO  DeltaEvictorExample  [] - id: 3,7, count: 6, timestamp: 1662303776894
WordCountTimestamp{id='3,7', word='a', frequency=6, timestamp=1662303776894}
23:26:25,751 INFO  WordCountOutOfOrderSource [] - id: 9, word: a, frequency: 5, eventTime: 1662303778877|2022-09-04 23:02:58
23:26:26,756 INFO  WordCountOutOfOrderSource [] - id: 10, word: a, frequency: 4, eventTime: 1662303791904|2022-09-04 23:03:11
23:26:27,760 INFO  WordCountOutOfOrderSource [] - id: 11, word: a, frequency: 1, eventTime: 1662303795918|2022-09-04 23:03:15
23:26:28,766 INFO  WordCountOutOfOrderSource [] - id: 12, word: a, frequency: 6, eventTime: 1662303779883|2022-09-04 23:02:59
23:26:29,771 INFO  WordCountOutOfOrderSource [] - id: 13, word: a, frequency: 2, eventTime: 1662303846254|2022-09-04 23:04:06
23:26:29,874 INFO  DeltaEvictorExample  [] - id: 6,8, count: 3, timestamp: 1662303786891
23:26:29,874 INFO  DeltaEvictorExample  [] - id: 6,8,10, count: 7, timestamp: 1662303791904
23:26:29,874 INFO  DeltaEvictorExample  [] - id: 6,8,10,11, count: 8, timestamp: 1662303795918
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
```

可以看到第一个窗口包含 `1、2、3、4、5、7` 元素，最后一个元素 `7` 值为 `3`，那需要剔除比 `3` 小于的元素，即只保留元素 `3、7`。同理第二个窗口包含 `6、8、10、11`，最后一个元素 `11` 值为 `1`，那需要剔除比 `1` 小于的元素，发现没有比该值还小的元素，即保留全部元素。

#### 2.3 TimeEvictor

以毫秒为单位的时间间隔 windowSize 作为参数，在窗口所有元素中找到最大时间戳 max_ts 并删除所有时间戳小于 `max_ts - windowSize` 的元素。我们可以理解为只保留最新 windowSize 毫秒内的元素。

##### 2.3.1 内部实现

TimeEvictor 与 DeltaEvictor、CountEvictor 一样，都需要实现 Evictor 接口的 evictBefore 和 evictAfter 方法，只是最终调用的 `evict()` 函数的内部实现逻辑不一样：
```java
private void evict(Iterable<TimestampedValue<Object>> elements, int size, EvictorContext ctx) {
    if (!hasTimestamp(elements)) {
        return;
    }
    // 最大时间戳
    long currentTime = getMaxTimestamp(elements);
    // 保留 [max_ts - windowSize, max_ts] 时间间隔内元素
    long evictCutoff = currentTime - windowSize;
    for (Iterator<TimestampedValue<Object>> iterator = elements.iterator(); iterator.hasNext(); ) {
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
    for (Iterator<TimestampedValue<Object>> iterator = elements.iterator(); iterator.hasNext(); ) {
        TimestampedValue<Object> record = iterator.next();
        currentTime = Math.max(currentTime, record.getTimestamp());
    }
    return currentTime;
}
```
首先获取当前窗口中最大的时间戳，减去用户指定时间间隔 windowSize，得到一个 evictCutoff，然后遍历窗口全部元素，删除时间戳小于等于 evictCutoff 的元素。

##### 2.3.2 如何使用

如下代码所示，在触发窗口函数计算之前只保留窗口中与最新元素5s内的元素：
```java
// 单词流
DataStream<WordCountTimestamp> words = source
        // 设置Watermark
        .assignTimestampsAndWatermarks(
                WatermarkStrategy.<WordCountTimestamp>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                        .withTimestampAssigner(new SerializableTimestampAssigner<WordCountTimestamp>() {
                            @Override
                            public long extractTimestamp(WordCountTimestamp wc, long recordTimestamp) {
                                return wc.getTimestamp();
                            }
                        })
        );

DataStream<WordCountTimestamp> result = words.keyBy(new KeySelector<WordCountTimestamp, String>() {
            @Override
            public String getKey(WordCountTimestamp wc) throws Exception {
                return wc.getWord();
            }
        })
        // 事件时间滚动窗口 滚动大小1分钟
        .window(TumblingEventTimeWindows.of(Time.minutes(1)))
        // 保留窗口中与最新元素5s内的元素
        .evictor(TimeEvictor.of(Time.seconds(5)))
        // 求和
        .reduce(new ReduceFunction<WordCountTimestamp>() {
            @Override
            public WordCountTimestamp reduce(WordCountTimestamp v1, WordCountTimestamp v2) throws Exception {
                int count = v1.getFrequency() + v2.getFrequency();
                String ids = v1.getId() + "," + v2.getId();
                Long timestamp = Math.max(v1.getTimestamp(), v2.getTimestamp());
                LOG.info("id: {}, count: {}, timestamp: {}", ids, count, timestamp);
                return new WordCountTimestamp(ids, v1.getWord(), count, timestamp);
            }
        });
```

> 完整代码请查阅[TimeEvictorExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/evictor/TimeEvictorExample.java)

实际效果如下所示：
```java
23:44:31,169 INFO  WordCountOutOfOrderSource [] - id: 1, word: a, frequency: 2, eventTime: 1662303772840|2022-09-04 23:02:52
23:44:32,176 INFO  WordCountOutOfOrderSource [] - id: 2, word: a, frequency: 1, eventTime: 1662303770844|2022-09-04 23:02:50
23:44:33,182 INFO  WordCountOutOfOrderSource [] - id: 3, word: a, frequency: 3, eventTime: 1662303773848|2022-09-04 23:02:53
23:44:34,186 INFO  WordCountOutOfOrderSource [] - id: 4, word: a, frequency: 2, eventTime: 1662303774866|2022-09-04 23:02:54
23:44:35,192 INFO  WordCountOutOfOrderSource [] - id: 5, word: a, frequency: 1, eventTime: 1662303777839|2022-09-04 23:02:57
23:44:36,194 INFO  WordCountOutOfOrderSource [] - id: 6, word: a, frequency: 2, eventTime: 1662303784887|2022-09-04 23:03:04
23:44:37,201 INFO  WordCountOutOfOrderSource [] - id: 7, word: a, frequency: 3, eventTime: 1662303776894|2022-09-04 23:02:56
23:44:38,207 INFO  WordCountOutOfOrderSource [] - id: 8, word: a, frequency: 1, eventTime: 1662303786891|2022-09-04 23:03:06
23:44:38,378 INFO  TimeEvictorExample   [] - id: 1,3, count: 5, timestamp: 1662303773848
23:44:38,378 INFO  TimeEvictorExample   [] - id: 1,3,4, count: 7, timestamp: 1662303774866
23:44:38,379 INFO  TimeEvictorExample   [] - id: 1,3,4,5, count: 8, timestamp: 1662303777839
23:44:38,379 INFO  TimeEvictorExample   [] - id: 1,3,4,5,7, count: 11, timestamp: 1662303777839
WordCountTimestamp{id='1,3,4,5,7', word='a', frequency=11, timestamp=1662303777839}
23:44:39,210 INFO  WordCountOutOfOrderSource [] - id: 9, word: a, frequency: 5, eventTime: 1662303778877|2022-09-04 23:02:58
23:44:40,212 INFO  WordCountOutOfOrderSource [] - id: 10, word: a, frequency: 4, eventTime: 1662303791904|2022-09-04 23:03:11
23:44:41,218 INFO  WordCountOutOfOrderSource [] - id: 11, word: a, frequency: 1, eventTime: 1662303795918|2022-09-04 23:03:15
23:44:42,220 INFO  WordCountOutOfOrderSource [] - id: 12, word: a, frequency: 6, eventTime: 1662303779883|2022-09-04 23:02:59
23:44:43,226 INFO  WordCountOutOfOrderSource [] - id: 13, word: a, frequency: 2, eventTime: 1662303846254|2022-09-04 23:04:06
23:44:43,261 INFO  TimeEvictorExample   [] - id: 10,11, count: 5, timestamp: 1662303795918
WordCountTimestamp{id='10,11', word='a', frequency=5, timestamp=1662303795918}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
```

可以看到第一个窗口包含 `1、2、3、4、5、7` 元素，最大时间戳元素为 `5`，那与该元素 5 秒内的元素为 `1、3、4、5
7`。同理第二个窗口包含 `6、8、10、11`，最大时间戳元素为 `11`，那与该元素 5 秒内的元素为 `10、11`。

参考：
- [Evictors](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/dev/datastream/operators/windows/#evictors)
