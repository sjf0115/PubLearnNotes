---
layout: post
author: smartsi
title: Flink 1.11版本如何生成Watermark
date: 2021-02-27 20:41:17
tags:
  - Flink

categories: Flink
permalink: generating-watermarks-in-flink-1.11
---

> Flink 1.11

在 Flink 1.11 版本之前，Flink 提供了两种生成 Watermark 的策略，分别是 AssignerWithPunctuatedWatermarks 和 AssignerWithPeriodicWatermarks，这两个接口都继承自 TimestampAssigner 接口。用户想使用不同的 Watermark 生成方式，则需要实现不同的接口。为了实现接口的统一，一个接口可以实现不同的 Watermark 生成策略，在 Flink 1.11 中对 Flink 的 Watermark 生成接口进行了重构：WatermarkStrategy。

> Flink 1.10 版本之前如何生成 Watermark 具体可以参阅 [Flink 1.10 版本之前如何生成 Watermark](https://smartsi.blog.csdn.net/article/details/126563487?spm=1001.2014.3001.5502)。

### 1. Watermark 生成策略 WatermarkStrategy

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

### 2. 内置 Watermark 生成器

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
#### 2.1 有序流

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

#### 2.2 乱序流

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
> 完成代码请查阅:[WatermarkStrategyExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/WatermarkStrategyExample.java)

上面代码中，我们同样提取了元组 f3 字段作为时间戳，并允许最大5 秒的乱序时间创建了处理乱序流的 Watermark 生成器。事实上，有序流的 Watermark 生成器本质上和乱序流是一样的，相当于延迟设为 0 的乱序流 Watermark 生成器，两者完全等同：
```java
WatermarkStrategy.forMonotonousTimestamps()
WatermarkStrategy.forBoundedOutOfOrderness(Duration.ofSeconds(0))
```
此外最需要注意的是，乱序流中生成的 Watermark 真正的时间戳，其实是`当前最大时间戳 - 最大乱序时间 – 1`(单位毫秒)。为什么要减 1 毫秒呢？我们可以回想一下 Watermark 的特点：时间戳为 t 的水位线，表示时间戳 ≤t 的数据全部到齐，不会再来了。如果考虑有序流，也就是延迟时间为 0 的情况，那么时间戳为 7 秒的数据到来时，之后其实是还有可能继续来 7 秒的数据的；所以生成的水位线不是 7 秒，而是 6 秒 999 毫秒，7 秒的数据还可以继续来。

### 3. 自定义 WatermarkStrategy

一般来说，Flink 内置的 Watermark 生成器就可以满足应用需求了。不过有时我们的业务逻辑可能非常复杂，这时对 Watermark 生成的逻辑也有更高的要求，我们就必须自定义实现 Watermark 策略 WatermarkStrategy 了。在 WatermarkStrategy 中，时间戳分配器 TimestampAssigner 都是大同小异的，指定字段提
取时间戳就可以了；而不同策略的关键就在于 WatermarkGenerator 接口的实现：
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

#### 3.1 周期性 Watermark 生成器

周期性 Watermark 生成器一般是通过 onEvent 观察输入的每个事件并周期性地调用 onPeriodicEmit 发送 Watermark（可能取决于流元素，或者单纯的基于处理时间）。通过 ExecutionConfig.setAutoWatermarkInterval() 方法定义周期性地发送 Watermark 的时间间隔(单位：毫秒)。生成器的 onPeriodicEmit 方法会周期性调用，如果返回的 Watermark 非空并且大于前一个 Watermark，则会生成一个新的 Watermark。

如下代码展示了使用 Periodic WatermarkGenerator 的简单示例。请注意，Flink 内置的 BoundedOutOfOrdernessWatermarks 是一个 WatermarkGenerator，其工作原理与下面显示的 BoundedOutOfOrdernessGenerator 相似：
```java
// 提取时间戳、生成Watermark
DataStream<Tuple3<String, Long, Integer>> watermarkStream = input.assignTimestampsAndWatermarks(
        new WatermarkStrategy<Tuple3<String, Long, Integer>>() {
            @Override
            public WatermarkGenerator<Tuple3<String, Long, Integer>> createWatermarkGenerator(WatermarkGeneratorSupplier.Context context) {
                return new MyBoundedOutOfOrdernessGenerator();
            }
        }.withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, Long, Integer>>() {
            @Override
            public long extractTimestamp(Tuple3<String, Long, Integer> element, long recordTimestamp) {
                return element.f1;
            }
        })

);

/**
 * 自定义 Periodic WatermarkGenerator
 */
private static class MyBoundedOutOfOrdernessGenerator implements WatermarkGenerator<Tuple3<String, Long, Integer>> {

    private final long maxOutOfOrderness = 600000; // 10分钟
    private long currentMaxTimestamp = Long.MIN_VALUE + maxOutOfOrderness + 1;
    // 前一个Watermark时间戳
    private long preWatermarkTimestamp = Long.MIN_VALUE;

    @Override
    public void onEvent(Tuple3<String, Long, Integer> event, long eventTimestamp, WatermarkOutput output) {
        currentMaxTimestamp = Math.max(currentMaxTimestamp, eventTimestamp);
        String currentTime = DateUtil.timeStamp2Date(eventTimestamp, "yyyy-MM-dd HH:mm:ss");
        String currentMaxTime = DateUtil.timeStamp2Date(currentMaxTimestamp, "yyyy-MM-dd HH:mm:ss");

        LOG.info("[INFO] Key: {}, CurrentTimestamp: [{}|{}], CurrentMaxTimestamp: [{}|{}]",
                event.f0, currentTime, eventTimestamp, currentMaxTime, currentMaxTimestamp
        );
    }

    @Override
    public void onPeriodicEmit(WatermarkOutput output) {
        Watermark watermark = new Watermark(currentMaxTimestamp - maxOutOfOrderness - 1);
        Long watermarkTimestamp = watermark.getTimestamp();
        // Watermark发生变化才输出Log
        if(watermarkTimestamp > preWatermarkTimestamp) {
            LOG.info("[INFO] Watermark: [{}|{}]", watermark.getFormattedTimestamp(), watermark.getTimestamp());
        }
        preWatermarkTimestamp = watermarkTimestamp;
        // 输出Watermark
        output.emitWatermark(watermark);
    }
}
```
> 必须指定TimestampAssigner否则报错。

> 完成代码请查阅:[PeriodicWatermarkGeneratorExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/PeriodicWatermarkGeneratorExample.java)

通过如下输入数据，我们可以观察输出的Watermark信息：
```
A,2021-02-14 12:07:01,9
B,2021-02-14 12:08:01,5
A,2021-02-14 12:14:01,3
C,2021-02-14 12:09:01,2
C,2021-02-14 12:15:01,5
A,2021-02-14 12:08:01,4
B,2021-02-14 12:13:01,6
B,2021-02-14 12:21:01,1
D,2021-02-14 12:04:01,3
B,2021-02-14 12:26:01,2
B,2021-02-14 12:17:01,7
D,2021-02-14 12:09:01,8
C,2021-02-14 12:30:01,1
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/generating-watermarks-in-flink-1.11-1.png?raw=true)

#### 4.2 断点式 Watermark 生成器

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
> 完成代码请查阅:[PunctuatedWatermarkGeneratorExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/CustomPunctuatedWatermarkStrategyExample.java)

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

推荐订阅：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-jk.jpeg?raw=true)
