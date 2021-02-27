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

> Flink 1.10版本之前是如何生成 Watermark 的，具体可以参阅 [Flink 在1.10版本之前如何生成Watermark](http://smartsi.club/flink-stream-event-timestamp-and-extractors.html)。

### 1. WatermarkStrategy介绍

为了使用事件时间，Flink 需要知道事件时间戳，这意味着流中的每个元素都需要为其分配事件时间戳。一般都是通过使用 TimestampAssigner 从元素中的某些字段提取时间戳来完成。Watermark 的生成一般与时间戳分配一起进行，Watermark 会告诉系统事件时间的进度。我们可以通过指定 WatermarkGenerator 进行配置。

在新版本中 Flink API 提供了一个同时包含 TimestampAssigner 和 WatermarkGenerator 的 WatermarkStrategy 接口：
```java
public interface WatermarkStrategy<T> extends TimestampAssignerSupplier<T>, WatermarkGeneratorSupplier<T>{
    @Override
    TimestampAssigner<T> createTimestampAssigner(TimestampAssignerSupplier.Context context);
    @Override
    WatermarkGenerator<T> createWatermarkGenerator(WatermarkGeneratorSupplier.Context context);
}
```
我们通常不用自己实现这个接口，使用 WatermarkStrategy 上的静态方法就可以实现常见的 Watermark 生成策略。除此之外我们也可以自定义 TimestampAssigner 与 WatermarkGenerator 实现自己的 Watermark 生成策略。例如，如下代码所示使用 BoundedOutOfOrderness 生成 Watermark 以及使用 Lambda 函数作为时间戳分配器：
```java
WatermarkStrategy
        .<Tuple2<Long, String>>forBoundedOutOfOrderness(Duration.ofSeconds(20))
        .withTimestampAssigner((event, timestamp) -> event.f0);
```
TimestampAssigner 是可选的，在大多数情况下，我们并不需要指定。例如，当使用 Kafka 或 Kinesis 时，我们可以直接从 Kafka/Kinesis 记录中获得时间戳。

### 2. 内置WatermarkStrategy

为了简化我们生成 Watermark 的编程工作，Flink 预先内置了一些 Watermark 生成策略，通常不需要我们自己实现上面的接口。我们使用 WatermarkStrategy 上的静态方法就可以实现常见的 Watermark 生成策略。Flink 为我们内置了两种 Watermark 生成策略：单调递增时间戳场景策略，固定时延场景策略：
```java
static <T> WatermarkStrategy<T> forMonotonousTimestamps() {
  return (ctx) -> new AscendingTimestampsWatermarks<>();
}

static <T> WatermarkStrategy<T> forBoundedOutOfOrderness(Duration maxOutOfOrderness) {
  return (ctx) -> new BoundedOutOfOrdernessWatermarks<>(maxOutOfOrderness);
}
```
#### 2.1 单调递增时间戳场景策略

周期性生成 Watermark 的一个最简单场景就是给定数据源中数据的时间戳升序出现。在这种情况下，根据指定字段提取数据中的时间戳，并始终用当前的时间戳作为 Watermark，因为没有更早的时间戳会到达了。这种方式比较适合于事件按顺序生成，没有乱序的情况。单调递增时间戳场景下生成 Watermark 只需调用 WatermarkStrategy 上的如下静态方法即可：
```java
WatermarkStrategy.forMonotonousTimestamps();
```
如下代码所示在时间戳单调递增场景下使用上述静态方法周期性生成 Watermark 的示例：
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
> 完成代码请查阅:[WatermarkStrategyExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/WatermarkStrategyExample.java)

需要注意的是，只需要保证数据源每个单独并行任务的时间戳递增即可。例如，如果在特定设置下，一个并行数据源实例只读取一个 Kafka 分区，那么只需要每个 Kafka 分区内时间戳递增即可。Flink 的 Watermark 合并机制即使在并行数据流进行 shuffle，union，连接或合并时，也能生成正确的 Watermark。

#### 2.2 固定时延场景策略

周期性生成 Watermark 的另一个示例是 Watermark 滞后于数据流中最大（事件时间）时间戳一个固定的时间量。这种场景下我们事先知道流中可能遇到的最大延迟，例如，在测试场景下我们会创建元素带有时间戳的自定义数据源。对于这种场景，Flink 提供了 BoundedOutOfOrdernessWatermarks 生成器，该生成器有一个 maxOutOfOrderness 参数，表示在计算给定窗口的最终结果时可以允许元素最大延迟时间，如果超过这个时间将会被丢弃。固定时延场景下生成 Watermark 只需调用 WatermarkStrategy 上的如下静态方法即可：
```java
WatermarkStrategy.forBoundedOutOfOrderness(Duration.ofSeconds(10));
```
如下代码所示在固定时延场景下使用上述静态方法周期性生成 Watermark 的示例：
```java
// 分配时间戳与设置Watermark
SingleOutputStreamOperator<Tuple3<String, Long, Integer>> watermarkStream = stream.assignTimestampsAndWatermarks(
        WatermarkStrategy.<Tuple3<String, Long, Integer>>forBoundedOutOfOrderness(Duration.ofMinutes(10))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, Long, Integer>>() {
                    @Override
                    public long extractTimestamp(Tuple3<String, Long, Integer> element, long recordTimestamp) {
                        return element.f1;
                    }
                })
);
```
> 完成代码请查阅:[WatermarkStrategyExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/WatermarkStrategyExample.java)

### 3. 自定义WatermarkStrategy

有时候上述内置 WatermarkStrategy 不满足我们的业务需求，这时候就需要自定义实现 WatermarkStrategy。 自定义 WatermarkStrategy 需要借助 WatermarkGenerator 接口实现事件时间戳提取以及 Watermark 生成。WatermarkGenerator 的编写要相对复杂一些，我们将在接下来的两节中介绍如何实现此这个目标。如下所示是 WatermarkGenerator 接口：
```java
@Public
public interface WatermarkGenerator<T> {
    void onEvent(T event, long eventTimestamp, WatermarkOutput output);
    void onPeriodicEmit(WatermarkOutput output);
}
```
这个接口比较简单，主要有两个方法：
- onEvent：每个元素到达都会调用这个方法。这个方法可以让 WatermarkGenerator 从元素中提取事件时间戳。
- onPeriodicEmit：这个方法会周期性被调用，可能会产生新的 Watermark，也可能不会产生新的 Watermark。

基于此我们可以实现两种不同的 Watermark Generator：Periodic Generator 和 Punctuated Generator：
- Periodic Generator：通常通过 onEvent() 方法处理传入的事件获取事件时间戳，然后周期性调用 onPeriodicEmit() 来判断是否产生新的 Watermark。
- Punctuated Generator：将查看 onEvent() 中的事件数据，等待特殊标记的事件或者携带 Watermark 信息的断点。当获取到一个事件时，它将会立即发出 Watermark。通常情况下，Punctuated Generator 不会通过 onPeriodicEmit() 发出 Watermark。

#### 3.1 Periodic WatermarkGenerator

Periodic 生成器处理流的每一个元素并周期性地生成 Watermark（可能取决于流元素，或者单纯的基于处理时间）。通过 ExecutionConfig.setAutoWatermarkInterval() 方法定义生成 Watermark 的时间间隔(单位：毫秒)。生成器的 onPeriodicEmit() 方法会周期性调用，如果返回的 Watermark 非空并且大于前一个 Watermark，则会生成一个新的 Watermark。

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

#### 4.2 Punctuated WatermarkGenerator

Punctuated 生成器将观察事件流，只要看到带有 Watermark 信息的特殊元素时就会发出 Watermark。如下所示实现了一个 Punctuated 生成器，每当发现带有特殊标记的事件时会发出 Watermark：
```java
// 提取时间戳、生成Watermark
DataStream<MyEvent> watermarkStream = input.assignTimestampsAndWatermarks(
        new WatermarkStrategy<MyEvent>() {
            @Override
            public WatermarkGenerator<MyEvent> createWatermarkGenerator(WatermarkGeneratorSupplier.Context context) {
                return new MyPunctuatedWatermarkGenerator();
            }
        }
        .withTimestampAssigner(new SerializableTimestampAssigner<MyEvent>() {
            @Override
            public long extractTimestamp(MyEvent element, long recordTimestamp) {
                return element.getTimestamp();
            }
        })
);

/**
 * 自定义 Punctuated WatermarkGenerator
 */
public static class MyPunctuatedWatermarkGenerator implements WatermarkGenerator<MyEvent> {
    @Override
    public void onEvent(MyEvent event, long eventTimestamp, WatermarkOutput output) {
        // 遇到特殊标记的元素就输出Watermark
        if (event.hasWatermarkMarker()) {
            Watermark watermark = new Watermark(eventTimestamp);
            LOG.info("[Watermark] Key: {}, HasWatermarkMarker: {}, EventTimestamp: [{}|{}], Watermark: [{}|{}]",
                    event.getKey(), event.hasWatermarkMarker(), event.getEventTime(), event.getTimestamp(),
                    watermark.getFormattedTimestamp(), watermark.getTimestamp()
            );
            output.emitWatermark(watermark);
        }
    }
    @Override
    public void onPeriodicEmit(WatermarkOutput output) {
        // 不使用该函数
    }
}
```
> 完成代码请查阅:[PunctuatedWatermarkGeneratorExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/watermark/PunctuatedWatermarkGeneratorExample.java)

通过如下输入示例数据，我们可以观察输出的Watermark信息：
```
A,false,2021-02-19 12:07:01
B,true,2021-02-19 12:08:01
A,false,2021-02-19 12:14:01
C,false,2021-02-19 12:09:01
C,true,2021-02-19 12:15:01
A,true,2021-02-19 12:08:01
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/generating-watermarks-in-flink-1.11-2.jpg?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

推荐订阅：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-jk.jpeg?raw=true)
