---
layout: post
author: smartsi
title: Flink DataStream 如何实现双流Join
date: 2021-02-06 22:38:17
tags:
  - Flink

categories: Flink
permalink: two-stream-join-with-datastream-in-flink
---

在离线 Hive 中，我们经常会使用 Join 进行多表关联。那么在实时中我们应该如何实现两条流的 Join 呢？Flink DataStream API 为我们提供了3个算子来实现双流 join，分别是：
- join
- coGroup
- intervalJoin

下面我们分别详细看一下这3个算子是如何实现双流 Join 的。

### 1. Join

Join 算子提供的语义为 "Window join"，即按照指定字段和（滚动/滑动/会话）窗口进行内连接(InnerJoin)。Join 将有相同 Key 并且位于同一窗口中的两条流的元素进行关联。

> Join 可以支持处理时间和事件时间两种时间特征。

Join 通用用法如下：
```java
stream.join(otherStream)
    .where(<KeySelector>)
    .equalTo(<KeySelector>)
    .window(<WindowAssigner>)
    .apply(<JoinFunction>)
```
> Join 语义类似与离线 Hive 的 InnnerJoin (内连接)，这意味着如果一个流中的元素在另一个流中没有相对应的元素，则不会输出该元素。

下面我们看一下 Join 算子在不同类型窗口上的具体表现。

#### 1.1 滚动窗口Join

当在滚动窗口上进行 Join 时，所有有相同 Key 并且位于同一滚动窗口中的两条流的元素两两组合进行关联，并最终传递到 JoinFunction 或 FlatJoinFunction 进行处理。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-1.png?raw=true)

如上图所示，我们定义了一个大小为 2 秒的滚动窗口，最终产生 [0,1]，[2,3]，... 这种形式的数据。上图显示了每个窗口中橘色流和绿色流的所有元素成对组合。需要注意的是，在滚动窗口 [6,7] 中，由于绿色流中不存在要与橘色流中元素 6、7 相关联的元素，因此该窗口不会输出任何内容。

下面我们一起看一下如何实现上图所示的滚动窗口 Join：
```java
// 绿色流
DataStream<Tuple3<String, String, String>> greenStream = greenSource.map(new MapFunction<String, Tuple3<String, String, String>>() {
    @Override
    public Tuple3<String, String, String> map(String str) throws Exception {
        String[] params = str.split(",");
        String key = params[0];
        String value = params[1];
        String eventTime = params[2];
        LOG.info("[绿色流] Key: {}, Value: {}, EventTime: {}", key, value, eventTime);
        return new Tuple3<>(key, value, eventTime);
    }
}).assignTimestampsAndWatermarks(
        WatermarkStrategy.<Tuple3<String, String, String>>forBoundedOutOfOrderness(Duration.ofMillis(100))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, String, String>>() {
                    @Override
                    public long extractTimestamp(Tuple3<String, String, String> element, long recordTimestamp) {
                        Long timeStamp = 0L;
                        try {
                            timeStamp = DateUtil.date2TimeStamp(element.f2, "yyyy-MM-dd HH:mm:ss");
                        } catch (ParseException e) {
                            e.printStackTrace();
                        }
                        return timeStamp;
                    }
                })
);

// 橘色流
DataStream<Tuple3<String, String, String>> orangeStream = orangeSource.map(new MapFunction<String, Tuple3<String, String, String>>() {
    @Override
    public Tuple3<String, String, String> map(String str) throws Exception {
        String[] params = str.split(",");
        String key = params[0];
        String value = params[1];
        String eventTime = params[2];
        LOG.info("[橘色流] Key: {}, Value: {}, EventTime: {}", key, value, eventTime);
        return new Tuple3<>(key, value, eventTime);
    }
}).assignTimestampsAndWatermarks(
        WatermarkStrategy.<Tuple3<String, String, String>>forBoundedOutOfOrderness(Duration.ofMillis(100))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, String, String>>() {
                    @Override
                    public long extractTimestamp(Tuple3<String, String, String> element, long recordTimestamp) {
                        Long timeStamp = 0L;
                        try {
                            timeStamp = DateUtil.date2TimeStamp(element.f2, "yyyy-MM-dd HH:mm:ss");
                        } catch (ParseException e) {
                            e.printStackTrace();
                        }
                        return timeStamp;
                    }
                })
);

// 双流合并
DataStream<String> result = orangeStream.join(greenStream)
    .where(tuple -> tuple.f0)
    .equalTo(tuple -> tuple.f0)
    .window(TumblingEventTimeWindows.of(Time.seconds(2)))
    .apply(new JoinFunction<Tuple3<String, String, String>, Tuple3<String, String, String>, String>() {
        @Override
        public String join(Tuple3<String, String, String> first, Tuple3<String, String, String> second) throws Exception {
            LOG.info("[合并流] Key: {}, Value: {}, EventTime: {}",
                    first.f0, first.f1 + "," + second.f1, first.f2 + "," + second.f2
            );
            return first.f1 + "," + second.f1;
        }
    });
```

> 完整代码请查阅:[TumblingWindowJoinExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/join/TumblingWindowJoinExample.java)

如上代码所示为绿色流和橘色流指定 BoundedOutOfOrdernessWatermarks Watermark 策略，设置100毫秒的最大可容忍的延迟时间，同时也会为流分配事件时间戳。假设输入流为 <Key, Value, EventTime> 格式，两条流输入元素如下所示：
```
绿色流：
key,0,2021-03-26 12:09:00
key,1,2021-03-26 12:09:01
key,3,2021-03-26 12:09:03
key,4,2021-03-26 12:09:04
key,9,2021-03-26 12:09:09

橘色流：
key,0,2021-03-26 12:09:00
key,1,2021-03-26 12:09:01
key,2,2021-03-26 12:09:02
key,3,2021-03-26 12:09:03
key,4,2021-03-26 12:09:04
key,5,2021-03-26 12:09:05
key,6,2021-03-26 12:09:06
key,7,2021-03-26 12:09:07
key,9,2021-03-26 12:09:09
```
Join 效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-2.png?raw=true)

#### 1.2 滑动窗口Join

当在滑动窗口上进行 Join 时，所有有相同 Key 并且位于同一滑动窗口中的两条流的元素两两组合进行关联，并最终传递到 JoinFunction 或 FlatJoinFunction 进行处理。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-3.png?raw=true)

如上图所示，我们定义了一个窗口大小为 2 秒、滑动步长为 1 秒的滑动窗口。需要注意的是，一个元素可能会落在不同的窗口中，因此会在不同窗口中发生关联，例如，绿色流中的0元素。当滑动窗口中一个流的元素在另一个流中没有相对应的元素，则不会输出该元素。

下面我们一起看一下如何实现上图所示的滑动窗口 Join：
```java
DataStream<String> result = orangeStream.join(greenStream)
      .where(tuple -> tuple.f0)
      .equalTo(tuple -> tuple.f0)
      .window(SlidingEventTimeWindows.of(Time.seconds(2) /* size */, Time.seconds(1) /* slide */))
      .apply(new JoinFunction<Tuple3<String, String, String>, Tuple3<String, String, String>, String>() {
          @Override
          public String join(Tuple3<String, String, String> first, Tuple3<String, String, String> second) throws Exception {
              LOG.info("[合并流] Key: {}, Value: {}, EventTime: {}",
                      first.f0, first.f1 + "," + second.f1, first.f2 + "," + second.f2
              );
              return first.f1 + "," + second.f1;
          }
      });
```
> 完整代码请查阅:[SlidingWindowJoinExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/join/SlidingWindowJoinExample.java)

假设输入流为 <Key, Value, EventTime> 格式，两条流输入元素如下所示：
```
绿色流：
key,0,2021-03-26 12:09:00
key,3,2021-03-26 12:09:03
key,4,2021-03-26 12:09:04
key,9,2021-03-26 12:09:09

橘色流：
key,0,2021-03-26 12:09:00
key,1,2021-03-26 12:09:01
key,2,2021-03-26 12:09:02
key,3,2021-03-26 12:09:03
key,4,2021-03-26 12:09:04
key,9,2021-03-26 12:09:09
```
Join 效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-4.png?raw=true)

#### 1.3 会话窗口Join

当在会话窗口上进行 Join 时，所有有相同 Key 并且位于同一会话窗口中的两条流的元素两两组合进行关联，并最终传递到 JoinFunction 或 FlatJoinFunction 进行处理。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-5.png?raw=true)

如上图所示，我们定义了一个会话窗口，其中每个会话之间的间隔至少为1秒。上图中一共有三个会话，在前两个会话中，两个流中的元素两两组合传递给 JoinFunction。在第三个会话中，绿色流中没有元素，因此元素 8 和 9 不会发生Join。

下面我们一起看一下如何实现上图所示的滑动窗口 Join：
```java
DataStream<String> result = orangeStream.join(greenStream)
        .where(tuple -> tuple.f0)
        .equalTo(tuple -> tuple.f0)
        .window(EventTimeSessionWindows.withGap(Time.seconds(1)))
        .apply(new JoinFunction<Tuple3<String, String, String>, Tuple3<String, String, String>, String>() {
            @Override
            public String join(Tuple3<String, String, String> first, Tuple3<String, String, String> second) throws Exception {
                LOG.info("[合并流] Key: {}, Value: {}, EventTime: {}",
                        first.f0, first.f1 + "," + second.f1, first.f2 + "," + second.f2
                );
                return first.f1 + "," + second.f1;
            }
        });
```
> 完整代码请查阅:[SessionWindowJoinExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/join/SessionWindowJoinExample.java)

假设输入流为 <Key, Value, EventTime> 格式，两条流输入元素如下所示：
```
绿色流：
key,0,2021-03-26 12:09:00
key,4,2021-03-26 12:09:04
key,5,2021-03-26 12:09:05
key,11,2021-03-26 12:09:11

橘色流：
key,1,2021-03-26 12:09:01
key,2,2021-03-26 12:09:02
key,5,2021-03-26 12:09:05
key,6,2021-03-26 12:09:06
key,8,2021-03-26 12:09:08
key,9,2021-03-26 12:09:09
key,11,2021-03-26 12:09:11
```
Join 效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-6.png?raw=true)

### 2. CoGroup

CoGroup 算子是将两条数据流按照 Key 进行分组，然后将相同 Key 的数据进行处理。要实现 CoGroup 功能需要为两个输入流分别指定 KeySelector 和 WindowAssigner。它的调用方式类似于 Join 算子，但是 CoGroupFunction 比 JoinFunction 更加灵活，可以按照用户指定的逻辑匹配左流或者右流的数据，基于此我们可以实现内连接(InnerJoin)、左连接(LeftJoin)以及右连接(RightJoin)。

> 目前，这些分组中的数据是在内存中保存的，因此需要确保保存的数据量不能太大，否则，JVM 可能会崩溃。

CoGroup 通用用法如下：
```java
stream.coGroup(otherStream)
		.where(<KeySelector>)
		.equalTo(<KeySelector>)
		.window(<WindowAssigner>)
		.apply(<CoGroupFunction>);
```

下面我们看一下如何使用 CoGroup 算子实现内连接(InnerJoin)、左连接(LeftJoin)以及右连接(RightJoin)。

#### 2.1 InnerJoin

下面我们看一下如何使用 CoGroup 实现内连接：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-7.png?raw=true)

如上图所示，我们定义了一个大小为 2 秒的滚动窗口。InnerJoin 只有在两个流对应窗口中都存在元素时，才会输出。

> 我们以滚动窗口为例来实现 InnerJoin

```java
// Join流
CoGroupedStreams coGroupStream = greenStream.coGroup(orangeStream);
DataStream<String> result = coGroupStream
        // 绿色流
        .where(new KeySelector<Tuple3<String, String, String>, String>() {
            @Override
            public String getKey(Tuple3<String, String, String> tuple3) throws Exception {
                return tuple3.f0;
            }
        })
        // 橘色流
        .equalTo(new KeySelector<Tuple3<String, String, String>, String>() {
            @Override
            public String getKey(Tuple3<String, String, String> tuple3) throws Exception {
                return tuple3.f0;
            }
        })
        // 滚动窗口
        .window(TumblingEventTimeWindows.of(Time.seconds(2)))
        .apply(new InnerJoinFunction());

// 内连接
private static class InnerJoinFunction implements CoGroupFunction<Tuple3<String, String, String>, Tuple3<String, String, String>, String> {
    @Override
    public void coGroup(Iterable<Tuple3<String, String, String>> greenIterable, Iterable<Tuple3<String, String, String>> orangeIterable, Collector<String> collector) throws Exception {
        for (Tuple3<String, String, String> greenTuple : greenIterable) {
            for (Tuple3<String, String, String> orangeTuple : orangeIterable) {
                LOG.info("[Join流] Key : {}, Value: {}, EventTime: {}",
                        greenTuple.f0, greenTuple.f1 + ", " + orangeTuple.f1, greenTuple.f2 + ", " + orangeTuple.f2
                );
                collector.collect(greenTuple.f1 + ", " + orangeTuple.f1);
            }
        }
    }
}
```

> 完整代码请查阅:[CoGroupJoinExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/join/CoGroupJoinExample.java)

如上代码所示，我们实现了 CoGroupFunction 接口，重写 coGroup 方法。一个流中有相同 Key 并且位于同一窗口的元素都会保存在同一个迭代器(Iterable)，本示例中绿色流为 greenIterable，橘色流为 orangeIterable，如果要实现 InnerJoin ，只需要两个迭代器中的元素两两组合即可。两条流输入元素如下所示：
```
绿色流：
key,0,2021-03-26 12:09:00
key,1,2021-03-26 12:09:01
key,2,2021-03-26 12:09:02
key,4,2021-03-26 12:09:04
key,5,2021-03-26 12:09:05
key,8,2021-03-26 12:09:08
key,9,2021-03-26 12:09:09
key,11,2021-03-26 12:09:11

橘色流：
key,0,2021-03-26 12:09:00
key,1,2021-03-26 12:09:01
key,2,2021-03-26 12:09:02
key,3,2021-03-26 12:09:03
key,4,2021-03-26 12:09:04
key,6,2021-03-26 12:09:06
key,7,2021-03-26 12:09:07
key,11,2021-03-26 12:09:11
```
Join 效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-8.png?raw=true)

#### 2.2 LeftJoin

下面我们看一下如何使用 CoGroup 实现左连接：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-9.png?raw=true)

如上图所示，我们定义了一个大小为 2 秒的滚动窗口。LeftJoin 只要绿色流窗口中有元素时，就会输出。即使在橘色流对应窗口中没有相对应的元素。

> 我们以滚动窗口为例来实现 LeftJoin

```java
// Join流
CoGroupedStreams coGroupStream = greenStream.coGroup(orangeStream);
DataStream<String> result = coGroupStream
        // 绿色流
        .where(new KeySelector<Tuple3<String, String, String>, String>() {
            @Override
            public String getKey(Tuple3<String, String, String> tuple3) throws Exception {
                return tuple3.f0;
            }
        })
        // 橘色流
        .equalTo(new KeySelector<Tuple3<String, String, String>, String>() {
            @Override
            public String getKey(Tuple3<String, String, String> tuple3) throws Exception {
                return tuple3.f0;
            }
        })
        // 滚动窗口
        .window(TumblingEventTimeWindows.of(Time.seconds(2)))
        .apply(new LeftJoinFunction());

// 左连接
private static class LeftJoinFunction implements CoGroupFunction<Tuple3<String, String, String>, Tuple3<String, String, String>, String> {
    @Override
    public void coGroup(Iterable<Tuple3<String, String, String>> greenIterable, Iterable<Tuple3<String, String, String>> orangeIterable, Collector<String> collector) throws Exception {
        for (Tuple3<String, String, String> greenTuple : greenIterable) {
            boolean noElements = true;
            for (Tuple3<String, String, String> orangeTuple : orangeIterable) {
                noElements = false;
                LOG.info("[Join流] Key : {}, Value: {}, EventTime: {}",
                        greenTuple.f0, greenTuple.f1 + ", " + orangeTuple.f1, greenTuple.f2 + ", " + orangeTuple.f2
                );
                collector.collect(greenTuple.f1 + ", " + orangeTuple.f1);
            }
            if (noElements){
                LOG.info("[Join流] Key : {}, Value: {}, EventTime: {}",
                        greenTuple.f0, greenTuple.f1 + ", null", greenTuple.f2 + ", null"
                );
                collector.collect(greenTuple.f1 + ", null");
            }
        }
    }
}
```
> 完整代码请查阅:[CoGroupJoinExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/join/CoGroupJoinExample.java)

如上代码所示，我们实现了 CoGroupFunction 接口，重写 coGroup 方法。一个流中有相同 Key 并且位于同一窗口的元素都会保存在同一个迭代器(Iterable)，本示例中绿色流为 greenIterable，橘色流为 orangeIterable，如果要实现 LeftJoin ，需要保证 orangeIterable 中没有元素，greenIterable 中的元素也能输出。因此我们定义了一个 noElements 变量来判断 orangeIterable 是否有元素，如果 orangeIterable 中没有元素，单独输出 greenIterable 中的元素即可。Join 效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-10.png?raw=true)

#### 2.3 RightJoin

下面我们看一下如何使用 CoGroup 实现左连接：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-11.png?raw=true)

如上图所示，我们定义了一个大小为 2 秒的滚动窗口。LeftJoin 只要橘色流窗口中有元素时，就会输出。即使在绿色流对应窗口中没有相对应的元素。

> 我们以滚动窗口为例来实现 RightJoin

```java
// Join流
CoGroupedStreams coGroupStream = greenStream.coGroup(orangeStream);
DataStream<String> result = coGroupStream
        // 绿色流
        .where(new KeySelector<Tuple3<String, String, String>, String>() {
            @Override
            public String getKey(Tuple3<String, String, String> tuple3) throws Exception {
                return tuple3.f0;
            }
        })
        // 橘色流
        .equalTo(new KeySelector<Tuple3<String, String, String>, String>() {
            @Override
            public String getKey(Tuple3<String, String, String> tuple3) throws Exception {
                return tuple3.f0;
            }
        })
        // 滚动窗口
        .window(TumblingEventTimeWindows.of(Time.seconds(2)))
        .apply(new RightJoinFunction());

// 右连接
private static class RightJoinFunction implements CoGroupFunction<Tuple3<String, String, String>, Tuple3<String, String, String>, String> {
    @Override
    public void coGroup(Iterable<Tuple3<String, String, String>> greenIterable, Iterable<Tuple3<String, String, String>> orangeIterable, Collector<String> collector) throws Exception {
        for (Tuple3<String, String, String> orangeTuple : orangeIterable) {
            boolean noElements = true;
            for (Tuple3<String, String, String> greenTuple : greenIterable) {
                noElements = false;
                LOG.info("[Join流] Key : {}, Value: {}, EventTime: {}",
                        greenTuple.f0, greenTuple.f1 + ", " + orangeTuple.f1, greenTuple.f2 + ", " + orangeTuple.f2
                );
                collector.collect(greenTuple.f1 + ", " + orangeTuple.f1);
            }
            if (noElements) {
                LOG.info("[Join流] Key : {}, Value: {}, EventTime: {}",
                        orangeTuple.f0, "null, " + orangeTuple.f1, "null, " + orangeTuple.f2
                );
                collector.collect("null, " + orangeTuple.f2);
            }
        }
    }
}
```
> 完整代码请查阅:[CoGroupJoinExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/join/CoGroupJoinExample.java)

如上代码所示，我们实现了 CoGroupFunction 接口，重写 coGroup 方法。一个流中有相同 Key 并且位于同一窗口的元素都会保存在同一个迭代器(Iterable)，本示例中绿色流为 greenIterable，橘色流为 orangeIterable，如果要实现 RightJoin，实现原理跟 LeftJoin 一样，需要保证 greenIterable 中没有元素，orangeIterable 中的元素也能输出。因此我们定义了一个 noElements 变量来判断 greenIterable 是否有元素，如果 greenIterable 中没有元素，单独输出 orangeIterable 中的元素即可。Join 效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-12.png?raw=true)

### 3. Interval Join

Flink 中基于 DataStream 的 Join，只能实现在同一个窗口的两个数据流进行 Join，但是在实际中常常会存在数据乱序或者延时的情况，导致两个流的数据进度不一致，就会出现数据跨窗口的情况，那么数据就无法在同一个窗口内 Join。Flink 基于 KeyedStream 提供的 Interval Join 机制可以对两个 keyedStream 进行 Join, 按照相同的 key 在一个相对数据时间的时间段内进行 Join。按照指定字段以及右流相对左流偏移的时间区间进行关联：
```
b.timestamp ∈ [a.timestamp + lowerBound, a.timestamp + upperBound]
```
或者
```
a.timestamp + lowerBound <= b.timestamp <= a.timestamp + upperBound
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-13.png?raw=true)

> 其中a和b分别是上图中绿色流和橘色流中的元素，并且有相同的 key。只需要保证 lowerBound 永远小于等于 upperBound 即可，均可以为正数或者负数。

从上面可以看出绿色流可以晚到 lowerBound（lowerBound为负的话）时间，也可以早到 upperBound（upperBound为正的话）时间。也可以理解为橘色流中的每个元素可以和绿色流指中定区间的元素进行 Join。需要注意的是 Interval Join 当前仅支持事件时间：
```java
public IntervalJoined<T1, T2, KEY> between(Time lowerBound, Time upperBound) {
			if (timeBehaviour != TimeBehaviour.EventTime) {
				throw new UnsupportedTimeCharacteristicException("Time-bounded stream joins are only supported in event time");
			}
}
```

下面我们具体看看如何实现一个 Interval Join：
```java
// 绿色流
DataStream<Tuple3<String, String, String>> greenStream = greenSource.map(new MapFunction<String, Tuple3<String, String, String>>() {
    @Override
    public Tuple3<String, String, String> map(String str) throws Exception {
        String[] params = str.split(",");
        String key = params[0];
        String eventTime = params[2];
        String value = params[1];
        LOG.info("[绿色流] Key: {}, Value: {}, EventTime: {}", key, value, eventTime);
        return new Tuple3<>(key, value, eventTime);
    }
}).assignTimestampsAndWatermarks(
        // 需要指定Watermark
        WatermarkStrategy.<Tuple3<String, String, String>>forBoundedOutOfOrderness(Duration.ofMillis(100))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, String, String>>() {
                    @Override
                    public long extractTimestamp(Tuple3<String, String, String> element, long recordTimestamp) {
                        Long timeStamp = null;
                        try {
                            timeStamp = DateUtil.date2TimeStamp(element.f2, "yyyy-MM-dd HH:mm:ss");
                        } catch (ParseException e) {
                            e.printStackTrace();
                        }
                        return timeStamp;
                    }
                })
);

// 橘色流
DataStream<Tuple3<String, String, String>> orangeStream = orangeSource.map(new MapFunction<String, Tuple3<String, String, String>>() {
    @Override
    public Tuple3<String, String, String> map(String str) throws Exception {
        String[] params = str.split(",");
        String key = params[0];
        String value = params[1];
        String eventTime = params[2];
        LOG.info("[橘色流] Key: {}, Value: {}, EventTime: {}", key, value, eventTime);
        return new Tuple3<>(key, value, eventTime);
    }
}).assignTimestampsAndWatermarks(
        // 需要指定Watermark
        WatermarkStrategy.<Tuple3<String, String, String>>forBoundedOutOfOrderness(Duration.ofMillis(100))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, String, String>>() {
                    @Override
                    public long extractTimestamp(Tuple3<String, String, String> element, long recordTimestamp) {
                        Long timeStamp = null;
                        try {
                            timeStamp = DateUtil.date2TimeStamp(element.f2, "yyyy-MM-dd HH:mm:ss");
                        } catch (ParseException e) {
                            e.printStackTrace();
                        }
                        return timeStamp;
                    }
                })
);

KeySelector<Tuple3<String, String, String>, String> keySelector = new KeySelector<Tuple3<String, String, String>, String>() {
    @Override
    public String getKey(Tuple3<String, String, String> value) throws Exception {
        return value.f0;
    }
};

// 双流合并
DataStream result = orangeStream
    .keyBy(keySelector)
    .intervalJoin(greenStream.keyBy(keySelector))
    .between(Time.seconds(-2), Time.seconds(1))
    .process(new ProcessJoinFunction<Tuple3<String, String, String>, Tuple3<String, String, String>, String>() {
        @Override
        public void processElement(Tuple3<String, String, String> left,
                                   Tuple3<String, String, String> right,
                                   Context ctx, Collector<String> out) throws Exception {
            LOG.info("[合并流] Key: {}, Value: {}, EventTime: {}",
                    left.f0, "[" + left.f1 + ", " + right.f1 + "]",
                    "[" + right.f2 + "|" + ctx.getRightTimestamp() + ", " + right.f2 + "|" + ctx.getLeftTimestamp() + "]"
            );
            out.collect(left.f1 + ", " + right.f1);
        }
    });
```
需要注意的是 Interval Join 当前仅支持事件时间，所以需要为流指定事件时间戳。

> 完整代码请查阅:[IntervalJoinExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/join/IntervalJoinExample.java)

两条流输入元素如下所示：
```
绿色流：
c,0,2021-03-23 12:09:00
c,1,2021-03-23 12:09:01
c,6,2021-03-23 12:09:06
c,7,2021-03-23 12:09:07

橘色流：
c,0,2021-03-23 12:09:00
c,2,2021-03-23 12:09:02
c,3,2021-03-23 12:09:03
c,4,2021-03-23 12:09:04
c,5,2021-03-23 12:09:05
c,7,2021-03-23 12:09:07
```
Join 效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/two-stream-join-with-datastream-in-flink-14.png?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

推荐订阅：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-jk.jpeg?raw=true)

参考:
- [Joining](https://ci.apache.org/projects/flink/flink-docs-release-1.12/dev/stream/operators/joining.html)
- Flink核心技术与实战
