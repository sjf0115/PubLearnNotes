---
layout: post
author: smartsi
title: Flink 1.11+ 版本如何生成 Watermark
date: 2021-02-27 20:41:17
tags:
  - Flink

categories: Flink
permalink: generating-watermarks-in-flink-1.11
---

> Flink 1.11

在 Flink 1.11 版本之前，Flink 提供了两种生成 Watermark 的策略，分别是 AssignerWithPunctuatedWatermarks 和 AssignerWithPeriodicWatermarks，这两个接口都继承自 TimestampAssigner 接口。用户想使用不同的 Watermark 生成方式，则需要实现不同的接口。为了实现接口的统一，一个接口可以实现不同的 Watermark 生成策略，在 Flink 1.11 中对 Flink 的 Watermark 生成接口进行了重构：WatermarkStrategy。

> Flink 1.10 版本之前如何生成 Watermark 具体可以参阅 [Flink 1.10 版本之前如何生成 Watermark](https://smartsi.blog.csdn.net/article/details/126563487?spm=1001.2014.3001.5502)。

## 1. Watermark 生成策略 WatermarkStrategy

在 Flink 的 DataStream API 中，有一个单独用于生成 Watermark 的方法：assignTimestampsAndWatermarks，主要用来为流中的数据分配时间戳，并生成 Watermark 来指示事件时间：
```java
public SingleOutputStreamOperator<T> assignTimestampsAndWatermarks(WatermarkStrategy<T> watermarkStrategy)
```
具体使用时，直接用 DataStream 调用该方法即可，与普通的 transform 方法完全一样：
```java
stream.assignTimestampsAndWatermarks(<watermark strategy>);
```
在新版本中 assignTimestampsAndWatermarks 方法需要传入一个 WatermarkStrategy 作为参数，这就是所谓的 Watermark 生成策略。WatermarkStrategy 主要用来创建时间戳分配器 TimestampAssigner 和 Watermark 生成器 WatermarkGenerator：
```java
public interface WatermarkStrategy<T> extends TimestampAssignerSupplier<T>, WatermarkGeneratorSupplier<T>{
    @Override
    TimestampAssigner<T> createTimestampAssigner(TimestampAssignerSupplier.Context context);
    @Override
    WatermarkGenerator<T> createWatermarkGenerator(WatermarkGeneratorSupplier.Context context);
}
```
createTimestampAssigner 用来创建时间戳分配器 TimestampAssigner，用来提取数据元素的某个字段作为时间戳。时间戳的提取是生成 Watermark 的基础。而 createWatermarkGenerator 用来创建 Watermark 生成器 WatermarkGenerator，根据指定的策略基于时间戳生成 Watermark。

> 这里可能会有疑惑：不是说数据里已经有时间戳了吗，为什么这里还要创建时间戳分配器来分配时间戳呢？这是因为原始的时间戳只是写入日志数据的一个字段，如果不提取出来并明确告诉 Flink，Flink 是无法知道数据真正产生的时间的。当然，有些时候数据源本身就提供了时间戳信息，比如读取 Kafka 时，我们就可以从 Kafka 数据中直接获取时间戳，而不需要单独提取字段分配了。

## 2. 内置 Watermark 生成器

WatermarkStrategy 是一个生成 Watermark 策略的抽象接口，让我们可以灵活地实现自己的需求；但看起来有些复杂，如果想要自己实现应该还是比较麻烦的。为了充分的给用户提供便利，Flink 预先内置了一些 Watermark 生成器 WatermarkGenerator。不仅开箱即用简化了编程，而且也为我们自定义 Watermark 策略提供了模板。这两个生成器均可以通过调用 WatermarkStrategy 的静态辅助方法来创建。它们都是周期性生成 Watermark，分别对应着处理有序流和乱序流的场景：
```java
// 有序流
static <T> WatermarkStrategy<T> forMonotonousTimestamps() {
  return (ctx) -> new AscendingTimestampsWatermarks<>();
}
// 乱序流
static <T> WatermarkStrategy<T> forBoundedOutOfOrderness(Duration maxOutOfOrderness) {
  return (ctx) -> new BoundedOutOfOrdernessWatermarks<>(maxOutOfOrderness);
}
```
### 2.1 有序流

对于有序流，主要特点是事件按顺序生成，不会出现乱序。这种情况下，时间戳单调增长，所以永远不会出现迟到数据的问题。这是周期性生成 Watermark 的最简单的场景，根据指定字段提取数据中的时间戳，并直接使用当前的时间戳作为 Watermark 就可以了，因为没有更早的时间戳会到达了。在这种场景下直接调用 WatermarkStrategy 的 forMonotonousTimestamps 静态方法即可：
```java
WatermarkStrategy.forMonotonousTimestamps();
```
如下代码所示在有序流场景下使用上述静态方法周期性生成 Watermark 的示例：
```java
SingleOutputStreamOperator<Tuple3<String, Long, Integer>> watermarkStream = stream.assignTimestampsAndWatermarks(
        WatermarkStrategy.<Tuple3<String, Long, Integer>>forMonotonousTimestamps()
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, Long, Integer>>() {
                    @Override
                    public long extractTimestamp(Tuple3<String, Long, Integer> element, long recordTimestamp) {
                        return element.f1;
                    }
                })
);
```
上面代码中我们调用 withTimestampAssigner 方法，将数据中的 f1 字段提取出来作为时间戳分配给数据元素；然后用内置的 Watermark 生成器构造出 Watermark 生成策略。

> 需要注意的是，forMonotonousTimestamps 方法只是创建了 Watermark 生成器，此外还需要我们提供 TimestampAssigner 来提取时间戳，我们可以通过 withTimestampAssigner 提供。

### 2.2 乱序流

由于乱序流中需要等待迟到数据到齐，所以必须设置一个固定量的延迟时间。这时生成 Watermark 的时间戳，就是当前数据流中最大的时间戳减去固定延迟时间的
结果，即 Watermark 滞后于数据流中最大时间戳一个固定的时间量，相当于把表调慢。在这种场景下我们需要事先知道流中可能遇到的最大乱序时间，直接调用 WatermarkStrategy 的 forBoundedOutOfOrderness 静态方法即可：
```java
WatermarkStrategy.forBoundedOutOfOrderness();
```
这个方法需要传入一个 maxOutOfOrderness 参数，表示最大乱序程度，即表示数据流中乱序数据时间戳的最大差值；如果我们能确定乱序程度，那么设置对应时间长度的延迟，就可以等到所有的乱序数据了。

如下代码所示在乱序流下使用上述静态方法周期性生成 Watermark 的示例：
```java
DataStreamSource<Tuple4<Integer, String, Integer, Long>> source = env.addSource(new OutOfOrderSource());
DataStream<Tuple4<Integer, String, Integer, Long>> watermarkStream = source.assignTimestampsAndWatermarks(
        // 允许最大5s的乱序
        WatermarkStrategy.<Tuple4<Integer, String, Integer, Long>>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple4<Integer, String, Integer, Long>>() {
                    @Override
                    public long extractTimestamp(Tuple4<Integer, String, Integer, Long> element, long recordTimestamp) {
                        return element.f3;
                    }
                })
);

// 分组求和
DataStream<Tuple2<String, Integer>> result = watermarkStream
        // 分组
        .keyBy(new KeySelector<Tuple4<Integer,String,Integer,Long>, String>() {
            @Override
            public String getKey(Tuple4<Integer, String, Integer, Long> tuple) throws Exception {
                return tuple.f1;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .window(TumblingEventTimeWindows.of(Time.minutes(1)))
        // 分组求和
        .process(new ProcessWindowFunction<Tuple4<Integer, String, Integer, Long>, Tuple2<String, Integer>, String, TimeWindow>() {
            @Override
            public void process(String key, Context context, Iterable<Tuple4<Integer, String, Integer, Long>> elements, Collector<Tuple2<String, Integer>> out) throws Exception {
                // 单词个数
                int count = 0;
                List<Integer> ids = Lists.newArrayList();
                for (Tuple4<Integer, String, Integer, Long> element : elements) {
                    ids.add(element.f0);
                    count ++;
                }
                // 时间窗口元数据
                TimeWindow window = context.window();
                long start = window.getStart();
                long end = window.getEnd();
                String startTime = DateUtil.timeStamp2Date(start);
                String endTime = DateUtil.timeStamp2Date(end);
                // Watermark
                long watermark = context.currentWatermark();
                String watermarkTime = DateUtil.timeStamp2Date(watermark);
                //  输出日志
                LOG.info("word: {}, count: {}, ids: {}, window: {}, watermark: {}",
                        key, count, ids,
                        "[" + startTime + ", " + endTime + "]",
                        watermark + "|" + watermarkTime
                );
                out.collect(Tuple2.of(key, count));
            }
        });
```
> 完成代码请查阅:[BoundedWatermarkStrategyExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/BoundedWatermarkStrategyExample.java)

上面代码中，我们同样提取了元组 f3 字段作为时间戳，并允许最大 5 秒的乱序时间创建了处理乱序流的 Watermark 生成器。通过 OutOfOrderSource Source 输入如下示例数据：
```
1, a, 2, 1662303772840L
2, a, 1, 1662303770844L
3, a, 3, 1662303773848L
4, a, 2, 1662303774866L
5, a, 1, 1662303777839L
6, a, 2, 1662303784887L
7, a, 3, 1662303776894L
8, a, 1, 1662303786891L
9, a, 5, 1662303778877L
10, a, 4, 1662303791904L
11, a, 1, 1662303795918L
12, a, 6, 1662303779883L
13, a, 2, 1662303846254L
```
实际效果如下：
```
22:57:27,909 INFO  Source      [] - id: 1, word: a, count: 2, eventTime: 1662303772840|2022-09-04 23:02:52
22:57:28,915 INFO  Source      [] - id: 2, word: a, count: 1, eventTime: 1662303770844|2022-09-04 23:02:50
22:57:29,920 INFO  Source      [] - id: 3, word: a, count: 3, eventTime: 1662303773848|2022-09-04 23:02:53
22:57:30,926 INFO  Source      [] - id: 4, word: a, count: 2, eventTime: 1662303774866|2022-09-04 23:02:54
22:57:31,928 INFO  Source      [] - id: 5, word: a, count: 1, eventTime: 1662303777839|2022-09-04 23:02:57
22:57:32,932 INFO  Source      [] - id: 6, word: a, count: 2, eventTime: 1662303784887|2022-09-04 23:03:04
22:57:33,936 INFO  Source      [] - id: 7, word: a, count: 3, eventTime: 1662303776894|2022-09-04 23:02:56
22:57:34,942 INFO  Source      [] - id: 8, word: a, count: 1, eventTime: 1662303786891|2022-09-04 23:03:06
22:57:35,114 INFO  Process     [] - word: a, count: 12, ids: [1, 2, 3, 4, 5, 7], window: [2022-09-04 23:02:00, 2022-09-04 23:03:00], watermark: 1662303781890|2022-09-04 23:03:01
(a,12)
22:57:35,947 INFO  Source      [] - id: 9, word: a, count: 5, eventTime: 1662303778877|2022-09-04 23:02:58
22:57:36,952 INFO  Source      [] - id: 10, word: a, count: 4, eventTime: 1662303791904|2022-09-04 23:03:11
22:57:37,953 INFO  Source      [] - id: 11, word: a, count: 1, eventTime: 1662303795918|2022-09-04 23:03:15
22:57:38,955 INFO  Source      [] - id: 12, word: a, count: 6, eventTime: 1662303779883|2022-09-04 23:02:59
22:57:39,958 INFO  Source      [] - id: 13, word: a, count: 2, eventTime: 1662303846254|2022-09-04 23:04:06
22:57:40,185 INFO  Process     [] - word: a, count: 8, ids: [6, 8, 10, 11], window: [2022-09-04 23:03:00, 2022-09-04 23:04:00], watermark: 1662303841253|2022-09-04 23:04:01
(a,8)
22:57:40,971 INFO  Process     [] - word: a, count: 2, ids: [13], window: [2022-09-04 23:04:00, 2022-09-04 23:05:00], watermark: 9223372036854775807|292278994-08-17 15:12:55
(a,2)
```
当输入 id 为 8 的元素时 Watermark 大于了窗口结束时间，因此触发了 `[2022-09-04 23:02:00, 2022-09-04 23:03:00]` 窗口计算，该窗口包含了 1、2、3、4、5、7 这 5 个元素。窗口计算结果为单词 a 出现了 12 次。同理，id 为 13 的元素的出现触发了 `[2022-09-04 23:03:00, 2022-09-04 23:04:00]` 窗口的计算，该窗口包含了 6、8、10 以及 11 这 4 个元素。等 id 为 13 的元素输出之后，Source 运行结束触发了新窗口的计算。从上面运行结果中我们看到 id 为 9 和 12 的元素并没有得到输出，是因为这两个迟到元素到达时本分配给它们的窗口 `[2022-09-04 23:02:00, 2022-09-04 23:03:00]` 已经计算完毕并销毁，因此出现了丢失。

事实上，有序流的 Watermark 生成器本质上和乱序流是一样的，相当于延迟设为 0 的乱序流 Watermark 生成器，两者完全等同：
```java
WatermarkStrategy.forMonotonousTimestamps()
WatermarkStrategy.forBoundedOutOfOrderness(Duration.ofSeconds(0))
```
此外最需要注意的是，乱序流中生成的 Watermark 真正的时间戳，其实是`当前最大时间戳 - 最大乱序时间 – 1`(单位毫秒)。为什么要减 1 毫秒呢？我们可以回想一下 Watermark 的特点：时间戳为 t 的水位线，表示时间戳 ≤t 的数据全部到齐，不会再来了。如果考虑有序流，也就是延迟时间为 0 的情况，那么时间戳为 7 秒的数据到来时，之后其实是还有可能继续来 7 秒的数据的；所以生成的水位线不是 7 秒，而是 6 秒 999 毫秒，7 秒的数据还可以继续来。

## 3. 自定义 WatermarkStrategy

一般来说，Flink 内置的 Watermark 生成器就可以满足应用需求了。不过有时我们的业务逻辑可能非常复杂，这时对 Watermark 生成的逻辑也有更高的要求，我们就必须自定义实现 Watermark 策略 WatermarkStrategy 了。在 WatermarkStrategy 中，时间戳分配器 TimestampAssigner 都是大同小异的，指定字段提取时间戳就可以了；而不同策略的关键就在于 WatermarkGenerator 接口的实现：
```java
@Public
public interface WatermarkGenerator<T> {
    void onEvent(T event, long eventTimestamp, WatermarkOutput output);
    void onPeriodicEmit(WatermarkOutput output);
}
```
WatermarkGenerator 接口比较简单，主要有两个方法：
- onEvent：每个元素到达都会调用这个方法。这个方法可以让 WatermarkGenerator 从元素中提取事件时间戳。
- onPeriodicEmit：这个方法会周期性被调用，可能会产生新的 Watermark，也可能不会产生新的 Watermark。

整体说来，Flink 有两种不同的生成 Watermark 的方式：一种是周期性的（Periodic），另一种是断点式的（Punctuated）。基于此我们可以实现两种不同的 Watermark 生成器：
- 周期性 Watermark 生成器：通常通过 onEvent() 方法处理传入的事件获取事件时间戳，然后周期性调用 onPeriodicEmit() 来判断是否产生新的 Watermark。
- 断点式 Watermark 生成器：将查看 onEvent() 中的事件数据，等待特殊标记的事件或者携带 Watermark 信息的断点。当获取到一个事件时，将会立即发出 Watermark。通常情况下，断点式 Watermark 生成器不会通过 onPeriodicEmit() 发出 Watermark。

### 3.1 周期性 Watermark 生成器

周期性 Watermark 生成器一般是通过 onEvent 观察输入的每个事件并周期性地调用 onPeriodicEmit 发送 Watermark（可能取决于流元素，或者单纯的基于处理时间）。通过 ExecutionConfig.setAutoWatermarkInterval() 方法定义周期性地发送 Watermark 的时间间隔(单位：毫秒)。生成器的 onPeriodicEmit 方法会周期性调用，如果返回的 Watermark 非空并且大于前一个 Watermark，则会生成一个新的 Watermark。如下代码展示了如何自定义周期性生成 Watermark 的示例：
```java
// 使用自定义 WatermarkStrategy
source.assignTimestampsAndWatermarks(new CustomWatermarkStrategy(Duration.ofSeconds(5)))

// 自定义 WatermarkStrategy
public static class CustomWatermarkStrategy implements WatermarkStrategy<Tuple4<Integer, String, Integer, Long>> {
    private final Duration maxOutOfOrderMillis;
    public CustomWatermarkStrategy(Duration maxOutOfOrderMillis) {
        this.maxOutOfOrderMillis = maxOutOfOrderMillis;
    }
    // 创建 Watermark 生成器
    @Override
    public WatermarkGenerator<Tuple4<Integer, String, Integer, Long>> createWatermarkGenerator(WatermarkGeneratorSupplier.Context context) {
        return new CustomPeriodicGenerator(maxOutOfOrderMillis);
    }
    // 创建时间戳分配器
    @Override
    public TimestampAssigner<Tuple4<Integer, String, Integer, Long>> createTimestampAssigner(TimestampAssignerSupplier.Context context) {
        return new CustomTimestampAssigner();
    }
}

// 自定义周期性 Watermark 生成器
public static class CustomPeriodicGenerator implements WatermarkGenerator<Tuple4<Integer, String, Integer, Long>> {
    // 最大时间戳
    private long maxTimestamp;
    // 最大乱序时间
    private final long outOfOrderMillis;
    public CustomPeriodicGenerator(Duration maxOutOfOrderMillis) {
        this.outOfOrderMillis = maxOutOfOrderMillis.toMillis();
        // 起始最小 Watermark 为 Long.MIN_VALUE.
        this.maxTimestamp = Long.MIN_VALUE + outOfOrderMillis + 1;
    }
    // 最大时间戳
    @Override
    public void onEvent(Tuple4<Integer, String, Integer, Long> event, long eventTimestamp, WatermarkOutput output) {
        maxTimestamp = Math.max(maxTimestamp, event.f3);
    }
    // 周期性生成 Watermark
    @Override
    public void onPeriodicEmit(WatermarkOutput output) {
        output.emitWatermark(new Watermark(maxTimestamp - outOfOrderMillis - 1));
    }
}

// 自定义时间戳分配器
public static class CustomTimestampAssigner implements TimestampAssigner<Tuple4<Integer, String, Integer, Long>> {
    @Override
    public long extractTimestamp(Tuple4<Integer, String, Integer, Long> element, long recordTimestamp) {
        return element.f3;
    }
}
```
我们在 onPeriodicEmit()里调用 output.emitWatermark()，就可以发出 Watermark。这个方法由系统框架周期性地调用，默认 200ms 一次。所以 Watermark 的时间戳是依赖当前已有数据的最大时间戳的（这里的实现与内置生成器类似，也是减去延迟时间再减 1），但具体什么时候生成与数据无关。

> 业务逻辑跟前一个示例 2.2 中一样，完成代码可以查阅:[CustomPeriodicWatermarkStrategyExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/CustomPeriodicWatermarkStrategyExample.java)

或者也可以使用 WatermarkStrategy.forGenerator 复用已有的 WatermarkGeneratorSupplier 来指定 Watermark 生成策略：
```java
// 使用自定义 WatermarkGeneratorSupplier
source.assignTimestampsAndWatermarks(
        WatermarkStrategy.forGenerator(new CustomWatermarkGeneratorSupplier(Duration.ofSeconds(5)))
        .withTimestampAssigner(new SerializableTimestampAssigner<Tuple4<Integer, String, Integer, Long>>() {
            @Override
            public long extractTimestamp(Tuple4<Integer, String, Integer, Long> element, long recordTimestamp) {
                return element.f3;
            }
        })
);

// 自定义 WatermarkGeneratorSupplier
public static class CustomWatermarkGeneratorSupplier implements WatermarkGeneratorSupplier<Tuple4<Integer, String, Integer, Long>> {
    private final Duration maxOutOfOrderMillis;
    public CustomWatermarkGeneratorSupplier(Duration maxOutOfOrderMillis) {
        this.maxOutOfOrderMillis = maxOutOfOrderMillis;
    }
    // 创建 Watermark 生成器
    @Override
    public WatermarkGenerator<Tuple4<Integer, String, Integer, Long>> createWatermarkGenerator(WatermarkGeneratorSupplier.Context context) {
        return new CustomPeriodicGenerator(maxOutOfOrderMillis);
    }
}

// 自定义周期性 Watermark 生成器
public static class CustomPeriodicGenerator implements WatermarkGenerator<Tuple4<Integer, String, Integer, Long>> {
    // 最大时间戳
    private long maxTimestamp;
    // 最大乱序时间
    private final long outOfOrderMillis;
    public CustomPeriodicGenerator(Duration maxOutOfOrderMillis) {
        this.outOfOrderMillis = maxOutOfOrderMillis.toMillis();
        // 起始最小 Watermark 为 Long.MIN_VALUE.
        this.maxTimestamp = Long.MIN_VALUE + outOfOrderMillis + 1;
    }
    // 最大时间戳
    @Override
    public void onEvent(Tuple4<Integer, String, Integer, Long> event, long eventTimestamp, WatermarkOutput output) {
        maxTimestamp = Math.max(maxTimestamp, event.f3);
    }
    // 周期性生成 Watermark
    @Override
    public void onPeriodicEmit(WatermarkOutput output) {
        output.emitWatermark(new Watermark(maxTimestamp - outOfOrderMillis - 1));
    }
}
```

> 业务逻辑跟前一个示例 2.2 中一样，完成代码可以查阅:[WatermarkStrategyGeneratorExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/WatermarkStrategyGeneratorExample.java)

### 3.2 断点式 Watermark 生成器

断点式 Watermark 生成器不停的在观察 onEvent 中的事件流，只要发现带有 Watermark 信息的特殊元素时就会发出 Watermark。一般来说，断点式 Watermark 生成器不会通过 onPeriodicEmit 发出 Watermark。如下所示实现了一个断点式 Watermark 生成器，每当发现带有特殊标记的事件时会发出 Watermark：
```java
// 提取时间戳、生成Watermark
DataStream<MyEvent> watermarkStream = input.assignTimestampsAndWatermarks(new CustomWatermarkStrategy());

// 自定义 WatermarkStrategy
public static class CustomWatermarkStrategy implements WatermarkStrategy<MyEvent> {
    // 创建 Watermark 生成器
    @Override
    public WatermarkGenerator<MyEvent> createWatermarkGenerator(WatermarkGeneratorSupplier.Context context) {
        return new CustomPunctuatedGenerator();
    }
    // 创建时间戳分配器
    @Override
    public TimestampAssigner<MyEvent> createTimestampAssigner(TimestampAssignerSupplier.Context context) {
        return new CustomTimestampAssigner();
    }
}

// 自定义断点式 Watermark 生成器
public static class CustomPunctuatedGenerator implements WatermarkGenerator<MyEvent> {
    @Override
    public void onEvent(MyEvent event, long eventTimestamp, WatermarkOutput output) {
        // 遇到特殊标记的元素就输出Watermark
        if (event.hasWatermarkMarker()) {
            Watermark watermark = new Watermark(eventTimestamp);
            LOG.info("Key: {}, HasWatermarkMarker: {}, EventTimestamp: [{}|{}], Watermark: [{}|{}]",
                    event.getKey(), event.hasWatermarkMarker(), event.getEventTime(), event.getTimestamp(),
                    watermark.getFormattedTimestamp(), watermark.getTimestamp()
            );
            output.emitWatermark(watermark);
        }
    }
    // 周期性生成 Watermark
    @Override
    public void onPeriodicEmit(WatermarkOutput output) {
        // 不需要
    }
}

// 自定义时间戳分配器
public static class CustomTimestampAssigner implements TimestampAssigner<MyEvent> {
    @Override
    public long extractTimestamp(MyEvent element, long recordTimestamp) {
        return element.getTimestamp();
    }
}
```
> 完成代码请查阅:[CustomPunctuatedWatermarkStrategyExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/CustomPunctuatedWatermarkStrategyExample.java)

通过如下输入示例数据，我们可以观察输出的 Watermark 信息：
```
A,false,2021-02-19 12:07:01
B,true,2021-02-19 12:08:01
A,false,2021-02-19 12:14:01
C,false,2021-02-19 12:09:01
C,true,2021-02-19 12:15:01
A,true,2021-02-19 12:08:01
```
实际效果如下：
```
08:27:54,478 Map [] - Key: A, HashWatermark: false, Timestamp: [2021-02-19 12:07:01|1613707621000]
08:27:58,813 Map [] - Key: B, HashWatermark: true, Timestamp: [2021-02-19 12:08:01|1613707681000]
08:27:58,839 Map [] - Key: B, HasWatermarkMarker: true, EventTimestamp: [2021-02-19 12:08:01|1613707681000], Watermark: [2021-02-19 12:08:01.000|1613707681000]
08:29:09,264 Map [] - Key: A, HashWatermark: false, Timestamp: [2021-02-19 12:14:01|1613708041000]
08:29:13,800 Map [] - Key: C, HashWatermark: false, Timestamp: [2021-02-19 12:09:01|1613707741000]
08:29:18,137 Map [] - Key: C, HashWatermark: true, Timestamp: [2021-02-19 12:15:01|1613708101000]
08:29:18,138 Map [] - Key: C, HasWatermarkMarker: true, EventTimestamp: [2021-02-19 12:15:01|1613708101000], Watermark: [2021-02-19 12:15:01.000|1613708101000]
08:29:21,970 Map [] - Key: A, HashWatermark: true, Timestamp: [2021-02-19 12:08:01|1613707681000]
08:29:21,970 Map [] - Key: A, HasWatermarkMarker: true, EventTimestamp: [2021-02-19 12:08:01|1613707681000], Watermark: [2021-02-19 12:08:01.000|1613707681000]
```
