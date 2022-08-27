---
layout: post
author: sjf0115
title: Flink 事件时间与处理时间
date: 2018-01-04 16:47:01
tags:
  - Flink
  - Flink Stream

categories: Flink
permalink: flink-stream-event-time-and-processing-time
---

> Flink版本：1.11

Flink 在数据流中支持几种不同概念的时间。

### 1. 处理时间

`Processing Time`(处理时间)是指执行相应操作的机器系统时间，是操作算子在计算过程中获取所在主机的系统时间。当用户选择使用处理时间时，所有和时间相关的算子，例如 Windows 计算，在当前任务中所有的算子直接使用所在主机的系统时间。例如，一个基于处理时间按小时进行处理的时间窗口将处理一个小时内（以系统时间为标准）到达指定算子的所有的记录。

处理时间是最简单的一个时间概念，不需要在数据流和机器之间进行协调。具有最好的性能和最低的延迟。然而，在分布式或者异步环境中，处理时间具有不确定性，因为容易受到记录到达系统速度的影响(例如，从消息队列到达的记录)，还会受到系统内记录在不同算子之间的流动速度的影响。对数据乱序的处理，处理时间不是一种最优的选择。

总之，处理时间适用于时间计算精度要求不是特别高的计算场景。

### 2. 事件时间

`Event Time`(事件时间)是每个事件在产生它的设备上发生的时间。在进入 Flink 之前，事件时间通常要嵌入到记录中，并且事件时间也可以从记录中提取出来。对于事件时间，时间的进度取决于数据，而不是系统时钟。基于事件时间的程序必须指定如何生成事件时间的`Watermarks`，这是表示事件时间进度的机制。

在理想情况下，事件时间处理将产生完全一致且确定的结果，无论事件何时到达以及以什么样的顺序到达。但是，除非已知事件是按顺序（按时间戳）到达，否则事件时间处理在等待无序事件时产生一定的延迟。由于只能等待有限的时间，因此这限制了事件时间应用程序的确定性。

假定所有数据都已到达，事件时间算子将按预期方式运行，即使在处理无序、迟到事件或重新处理历史数据时，也会产生正确且一致的结果。例如，每小时事件时间窗口将将处理事件时间在这一小时之内所有的记录，不管它们何时到达，以及它们以什么顺序到达。

按事件时间处理往往会导致一定的延迟，因为它要等待延迟事件和无序事件一段时间。因此，事件时间程序通常与处理时间操作相结合使用。

### 3. 摄入时间

`Ingestion Time`(摄入时间)是事件进入Flink的时间。在 Source 算子中，每个记录将 Source 的当前时间记为时间戳，基于时间的操作(如时间窗口)会使用该时间戳。

摄入时间在概念上处于事件时间和处理时间之间。与处理时间相比，摄入时间的成本稍微更高一些，但是可以提供更可预测的结果。因为摄入时间的时间戳比较稳定(在 Source 处只记录一次)，同一数据在流经不同窗口操作时将使用相同的时间戳，然而对于处理时间，每个窗口算子可能将记录分配给不同的窗口(基于本地系统时钟以及传输延迟)。与事件时间相比，摄入时间程序无法处理任何无序事件或延迟事件，但程序不必指定如何生成`watermarks`。

在内部，摄入时间与事件时间非常相似，但事件时间会自动分配时间戳以及自动生成`watermark`。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-event-time-and-processing-time.png?raw=true)

### 4. 选择时间特性

当你指定一个窗口来收集每分钟的记录时，如何判定每个窗口中需要包含哪些事件呢？在 Flink DataStream API 中，你可以使用时间特性来告知 Flink 在创建窗口时如何定义时间。时间特性是 StreamExecutionEnvironment 的一个属性，目前可以接收如下三种值，分别对应上述三种类型的时间类型：
```java
public enum TimeCharacteristic {
    // 处理时间
    ProcessingTime,
    // 摄入时间
    IngestionTime,
    // 事件时间
    EventTime
}
```
可以通过 StreamExecutionEnvironment 的 setStreamTimeCharacteristic 方法来设置时间特性：
```java
public void setStreamTimeCharacteristic(TimeCharacteristic characteristic) {
    this.timeCharacteristic = Preconditions.checkNotNull(characteristic);
    if (characteristic == TimeCharacteristic.ProcessingTime) {
        getConfig().setAutoWatermarkInterval(0);
    } else {
        getConfig().setAutoWatermarkInterval(200);
    }
}
```
通过上述代码可以看到设置时间特性其本质是设置 Watermark 的时间间隔。如果设置的是 ProcessingTime 则 Watermark 的时间间隔为 0；如果设置的是 EventTime 和 IngestionTime，则设置为 200 毫秒。当然这是一个默认值，如果默认值不适用于您的应用程序，可以通过 ExecutionConfig 的 setAutoWatermarkInterval(long) 方法重新修改。

如下展示了一个使用处理时间计算每分钟单词个数的示例，注意的是窗口的行为会与时间特性相匹配：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 设置Checkpoint
env.enableCheckpointing(1000L);
// 设置事件时间特性 处理时间
env.setStreamTimeCharacteristic(TimeCharacteristic.ProcessingTime);

DataStream<String> source = env.socketTextStream("localhost", 9100, "\n");

// Stream of (word, count)
DataStream<Tuple2<String, Long>> words = source
        .flatMap(new FlatMapFunction<String, Tuple2<String, Long>>() {
            @Override
            public void flatMap(String str, Collector<Tuple2<String, Long>> collector) throws Exception {
                String[] words = str.split("\\s+");
                for (String word : words) {
                    collector.collect(Tuple2.of(word, 1L));
                }
            }
        });

// 滚动窗口
DataStream<Tuple2<String, Long>> tumblingTimeWindowStream = words
        // 根据单词分组
        .keyBy(new KeySelector<Tuple2<String,Long>, String>() {
            @Override
            public String getKey(Tuple2<String, Long> tuple2) throws Exception {
                return tuple2.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .timeWindow(Time.minutes(1))
        // 求和
        .sum(1);
```


在 Flink 1.12 中，默认的时间特性已更改为 `EventTime`，因此您不再需要调用此方法来启用事件时间支持。 显式使用处理时间窗口和计时器在事件时间模式下工作。 如果您需要禁用水印，请使用 `ExecutionConfig.setAutoWatermarkInterval(long)`。 如果您使用的是 `IngestionTime`，请手动设置适当的 `WatermarkStrategy`。 如果您正在使用通用的“时间窗口”操作（例如基于时间特征改变行为的 `KeyedStream.timeWindow()`，请使用明确指定处理时间或事件时间的等效操作。





原文:[Timely Stream Processing](https://ci.apache.org/projects/flink/flink-docs-release-1.11/concepts/timely-stream-processing.html)
