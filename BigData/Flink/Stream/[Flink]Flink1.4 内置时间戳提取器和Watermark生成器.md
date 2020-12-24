---
layout: post
author: sjf0115
title: Flink1.4 内置的时间戳提取器和Watermark生成器
date: 2018-01-16 16:30:17
tags:
  - Flink
  - Flink Stream

categories: Flink
permalink: flink-stream-event-timestamp-and-extractors
---

如[Flink1.4 生成时间戳与Watermarks](http://smartsi.club/2018/01/15/Flink/[Flink]Flink1.4%20%E7%94%9F%E6%88%90%E6%97%B6%E9%97%B4%E6%88%B3%E4%B8%8EWatermarks/)所介绍的，`Flink`提供了一个抽象类，允许程序员可以分配自己的时间戳并发送`Watermark`。更具体地说，可以通过`AssignerWithPeriodicWatermarks`或`AssignerWithPunctuatedWatermarks`接口来实现，具体实现取决于用户具体情况。第一个接口将周期性的发送`Watermark`，第二个则基于传入记录的某些属性发送`Watermark`，例如，当在流中遇到特殊元素时。

为了进一步缓解这些任务的编程工作，`Flink`带有一些内置的时间戳分配器。除了开箱即用的功能外，它们的实现也可以作为自定义实现的一个例子。

### 1. 递增时间戳分配器

周期性生成`Watermark`最简单的例子是给定数据源任务中的时间戳会递增顺序出现。在这种情况下，由于没有时间戳比当前时间戳还早到达的，所以当前时间戳可以始终充当`Watermark`。

请注意，每个并行数据源任务的时间戳必须是升序的。例如，如果在特定设置中，一个并行数据源实例读取一个`Kafka`分区，那么只需要确保在每个`Kafka`分区内时间戳是升序的即可。每当并行数据流被`shuffle`，`union`，连接或合并时，`Flink`的`Watermark`合并机制能够产生正确的`watermarks`。

Java版本:
```java
DataStream<MyEvent> stream = ...

DataStream<MyEvent> withTimestampsAndWatermarks =
    stream.assignTimestampsAndWatermarks(new AscendingTimestampExtractor<MyEvent>() {

        @Override
        public long extractAscendingTimestamp(MyEvent element) {
            return element.getCreationTime();
        }
});
```

Scala版本:
```
val stream: DataStream[MyEvent] = ...

val withTimestampsAndWatermarks = stream.assignAscendingTimestamps( _.getCreationTime )
```

### 2. 允许固定数量延迟的分配器

周期性生成`Watermark`的另一个例子是当`Watermark`落后于数据流中看到的最大时间戳(事件时间)一固定数量时间(a fixed amount of time)。这种情况涵盖了事先知道流中可能遇到的最大延迟的场景，例如，当创建一个测试用的自定义数据源时，其上每个元素的时间戳分布在一个固定时间段内。对于这些情况，`Flink`提供了`BoundedOutOfOrdernessTimestampExtractor`，带有一个`maxOutOfOrderness`参数，即在计算给定窗口最终结果一个元素在被忽略之前允许延迟的最大时间。延迟对应于`t-t_w`的结果，其中`t`是元素的(事件时间)时间戳，`t_w`是前一个`Watermark`时间戳。如果延迟大于0，则该元素被认为是迟到的，并且在计算其相应窗口的作业结果时默认为忽略该元素。

Java版本:
```java
DataStream<MyEvent> stream = ...

DataStream<MyEvent> withTimestampsAndWatermarks =
    stream.assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor<MyEvent>(Time.seconds(10)) {

        @Override
        public long extractTimestamp(MyEvent element) {
            return element.getCreationTime();
        }
});
```

Scala版本:
```
val stream: DataStream[MyEvent] = ...

val withTimestampsAndWatermarks = stream.assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor[MyEvent](Time.seconds(10))( _.getCreationTime ))
```


原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/event_timestamp_extractors.html
