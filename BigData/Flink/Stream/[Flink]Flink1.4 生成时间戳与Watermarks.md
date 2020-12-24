---
layout: post
author: sjf0115
title: Flink1.4 生成时间戳与Watermarks
date: 2018-01-15 09:47:01
tags:
  - Flink
  - Flink Stream

categories: Flink
permalink: flink-stream-event-timestamps-and-watermark
---

本节适用于在事件时间上运行的程序。有关事件时间，处理时间和提取时间的介绍，请参阅[Flink1.4 事件时间与处理时间](http://smartsi.club/2018/01/04/Flink/[Flink]Flink1.4%20%E4%BA%8B%E4%BB%B6%E6%97%B6%E9%97%B4%E4%B8%8E%E5%A4%84%E7%90%86%E6%97%B6%E9%97%B4/)。

为了处理事件时间，流处理程序需要相应地设置`TimeCharacteristic`。

Java版本:
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime);
```

Scala版本:
```
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime);
```

### 1. 分配时间戳

为了处理事件时间，Flink需要知道事件的时间戳，这意味着流中的每个元素都需要分配事件时间戳。这通常通过访问/提取元素中某个字段的时间戳来完成。时间戳分配与生成`watermarks`相结合，告诉系统有关事件时间的进度`progress`。分配时间戳和生成`watermarks`有两种方法：
- 直接在数据流源中分配与生成
- 通过时间戳分配器/`watermark`生成器：在`Flink`时间戳分配器中也会定义要发送的`watermarks`

备注:
```
时间戳和watermarks都是从Java历元1970-01-01T00：00：00Z以来的毫秒数。
```

#### 1.1 带有时间戳和watermarks的数据源函数

流数据源还可以直接为它们产生的元素分配时间戳，并且也可以发送`watermarks`。如果数据源分配了时间戳，那么就不需要时间戳分配器。

备注:
```
如果继续使用时间戳分配器，将会覆盖数据源提供的时间戳和watermarks。
```

如果直接向数据源中的元素分配时间戳，数据源必须使用`SourceContext上`的`collectWithTimestamp()`方法。如果要生成`watermarks`，数据源必须调用`emitWatermark（Watermark）`函数。

以下是分配时间戳并生成`watermarks`的源(non-checkpointed)的简单示例：

Java版本:
```java
@Override
public void run(SourceContext<MyType> ctx) throws Exception {
	while (/* condition */) {
		MyType next = getNext();
		ctx.collectWithTimestamp(next, next.getEventTimestamp());

		if (next.hasWatermarkTime()) {
			ctx.emitWatermark(new Watermark(next.getWatermarkTime()));
		}
	}
}
```

Scala版本:
```
override def run(ctx: SourceContext[MyType]): Unit = {
	while (/* condition */) {
		val next: MyType = getNext()
		ctx.collectWithTimestamp(next, next.eventTimestamp)

		if (next.hasWatermarkTime) {
			ctx.emitWatermark(new Watermark(next.getWatermarkTime))
		}
	}
}
```

#### 1.2 时间戳分配器/Watermark生成器

时间戳分配器接收数据流并产生一个新的数据流，包含带有时间戳的元素和`Watermark`。如果原始流已经拥有时间戳或`watermarks`，那么如果使用时间戳分配器将会覆盖它们。

时间戳分配器通常在数据源之后立马指定，但也不是严格遵循这样的原则。例如，一个常见的模式是在时间戳分配器之前需要进行解析(`MapFunction`)和过滤(`FilterFunction`)。无论如何，时间戳分配器都需要在第一个基于事件时间的操作(例如第一个窗口操作)之前被指定。但也有特殊情况，当使用`Kafka`作为流作业的数据源时，`Flink`允许在数据源(消费者)内部定义时间戳分配器/`watermarks`生成器。有关如何执行此操作的更多信息，请参见[Kafka Connector文档](https://ci.apache.org/projects/flink/flink-docs-release-1.3/dev/connectors/kafka.html)。

备注:
```
本节的其余部分介绍了程序员为了创建自己的时间戳提取器/watermarks生成器而必须实现的主要接口。如果要查看Flink内置的执行器，请参阅[Pre-defined Timestamp Extractors / Watermark Emitters](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/event_timestamp_extractors.html)
```

Java版本:
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime);

DataStream<MyEvent> stream = env.readFile(
        myFormat, myFilePath, FileProcessingMode.PROCESS_CONTINUOUSLY, 100,
        FilePathFilter.createDefaultFilter(), typeInfo);

DataStream<MyEvent> withTimestampsAndWatermarks = stream
        .filter( event -> event.severity() == WARNING )
        .assignTimestampsAndWatermarks(new MyTimestampsAndWatermarks());

withTimestampsAndWatermarks
        .keyBy( (event) -> event.getGroup() )
        .timeWindow(Time.seconds(10))
        .reduce( (a, b) -> a.add(b) )
        .addSink(...);
```

Scala版本:
```
val env = StreamExecutionEnvironment.getExecutionEnvironment
env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime)

val stream: DataStream[MyEvent] = env.readFile(
         myFormat, myFilePath, FileProcessingMode.PROCESS_CONTINUOUSLY, 100,
         FilePathFilter.createDefaultFilter());

val withTimestampsAndWatermarks: DataStream[MyEvent] = stream
        .filter( _.severity == WARNING )
        .assignTimestampsAndWatermarks(new MyTimestampsAndWatermarks())

withTimestampsAndWatermarks
        .keyBy( _.getGroup )
        .timeWindow(Time.seconds(10))
        .reduce( (a, b) => a.add(b) )
        .addSink(...)
```

##### 1.2.1 Periodic Watermarks 分配器

`AssignerWithPeriodicWatermarks`分配时间戳并定期生成`Watermarks`(可能取决于流元素，或纯粹基于处理时间)。

通过`ExecutionConfig.setAutoWatermarkInterval()`定义`Watermarks`的时间间隔(每n毫秒)。每次调用分配器的`getCurrentWatermark()`方法，如果返回的`Watermark`非null，并且大于先前的`Watermark`，则会发送(emitted)这个新的`Watermarks`。

以下是带有周期性`Watermark`的时间戳分配器的两个简单示例:

Java版本:
```java
/**
 * This generator generates watermarks assuming that elements arrive out of order,
 * but only to a certain degree. The latest elements for a certain timestamp t will arrive
 * at most n milliseconds after the earliest elements for timestamp t.
 */
public class BoundedOutOfOrdernessGenerator extends AssignerWithPeriodicWatermarks<MyEvent> {

    private final long maxOutOfOrderness = 3500; // 3.5 seconds

    private long currentMaxTimestamp;

    @Override
    public long extractTimestamp(MyEvent element, long previousElementTimestamp) {
        long timestamp = element.getCreationTime();
        currentMaxTimestamp = Math.max(timestamp, currentMaxTimestamp);
        return timestamp;
    }

    @Override
    public Watermark getCurrentWatermark() {
        // return the watermark as current highest timestamp minus the out-of-orderness bound
        return new Watermark(currentMaxTimestamp - maxOutOfOrderness);
    }
}

/**
 * This generator generates watermarks that are lagging behind processing time by a fixed amount.
 * It assumes that elements arrive in Flink after a bounded delay.
 */
public class TimeLagWatermarkGenerator extends AssignerWithPeriodicWatermarks<MyEvent> {

	private final long maxTimeLag = 5000; // 5 seconds

	@Override
	public long extractTimestamp(MyEvent element, long previousElementTimestamp) {
		return element.getCreationTime();
	}

	@Override
	public Watermark getCurrentWatermark() {
		// return the watermark as current time minus the maximum time lag
		return new Watermark(System.currentTimeMillis() - maxTimeLag);
	}
}
```

Scala版本:
```
/**
 * This generator generates watermarks assuming that elements arrive out of order,
 * but only to a certain degree. The latest elements for a certain timestamp t will arrive
 * at most n milliseconds after the earliest elements for timestamp t.
 */
class BoundedOutOfOrdernessGenerator extends AssignerWithPeriodicWatermarks[MyEvent] {

    val maxOutOfOrderness = 3500L; // 3.5 seconds

    var currentMaxTimestamp: Long;

    override def extractTimestamp(element: MyEvent, previousElementTimestamp: Long): Long = {
        val timestamp = element.getCreationTime()
        currentMaxTimestamp = max(timestamp, currentMaxTimestamp)
        timestamp;
    }

    override def getCurrentWatermark(): Watermark = {
        // return the watermark as current highest timestamp minus the out-of-orderness bound
        new Watermark(currentMaxTimestamp - maxOutOfOrderness);
    }
}

/**
 * This generator generates watermarks that are lagging behind processing time by a fixed amount.
 * It assumes that elements arrive in Flink after a bounded delay.
 */
class TimeLagWatermarkGenerator extends AssignerWithPeriodicWatermarks[MyEvent] {

    val maxTimeLag = 5000L; // 5 seconds

    override def extractTimestamp(element: MyEvent, previousElementTimestamp: Long): Long = {
        element.getCreationTime
    }

    override def getCurrentWatermark(): Watermark = {
        // return the watermark as current time minus the maximum time lag
        new Watermark(System.currentTimeMillis() - maxTimeLag)
    }
}
```

##### 1.2.2 Punctuated Watermarks 分配器

每当某个事件表明一个新的`Watermarks`可能要生成时，需要调用`AssignerWithPunctuatedWatermarks`方法来生成`Watermarks`(To generate watermarks whenever a certain event indicates that a new watermark might be generated, use AssignerWithPunctuatedWatermarks)。对于这个类，`Flink`首先调用`extractTimestamp()`方法为元素分配时间戳，然后立即调用该元素上的`checkAndGetNextWatermark()`方法。

把在`extractTimestamp()`方法中分配的时间戳传递给`checkAndGetNextWatermark()`方法，并且可以决定是否要生成`Watermarks`。只要`checkAndGetNextWatermark()`方法返回非null的`Watermark`，并且该`Watermark`比以前最新的`Watermark`都大，则会发送这个新的`Watermark`。

Java版本:
```java
public class PunctuatedAssigner extends AssignerWithPunctuatedWatermarks<MyEvent> {

	@Override
	public long extractTimestamp(MyEvent element, long previousElementTimestamp) {
		return element.getCreationTime();
	}

	@Override
	public Watermark checkAndGetNextWatermark(MyEvent lastElement, long extractedTimestamp) {
		return lastElement.hasWatermarkMarker() ? new Watermark(extractedTimestamp) : null;
	}
}
```

Scala版本:
```
class PunctuatedAssigner extends AssignerWithPunctuatedWatermarks[MyEvent] {

	override def extractTimestamp(element: MyEvent, previousElementTimestamp: Long): Long = {
		element.getCreationTime
	}

	override def checkAndGetNextWatermark(lastElement: MyEvent, extractedTimestamp: Long): Watermark = {
		if (lastElement.hasWatermarkMarker()) new Watermark(extractedTimestamp) else null
	}
}
```
备注:
```
可以在每个单独的事件上生成Watermark。但是，由于每个Watermark在下游引起一些计算，所以过多的Watermark会降低性能。
```

### 2. 每个Kafka分区一个时间戳

当使用`Apache Kafka`作为数据源时，每个`Kafka`分区都可能有一个简单的事件时间模式(时间戳按升序递增或有界无序)。然而，当消费`Kafka`中的流时，多个分区通常并行消费，来自多个分区的事件会交叉在一起，破坏每个分区模式。

在这种情况下，你可以使用`Flink`的`Kafka`分区感知`Watermark`的生成(Kafka-partition-aware watermark generation)。使用该特性，在`Kafka`消费者中，每个`Kafka`分区都生成`watermark`，并且每个分区的`watermark`的合并方式与在数据流`shuffle`上合并方式相同(the per-partition watermarks are merged in the same way as watermarks are merged on stream shuffles.)。

例如，如果在每个`Kafka`分区中的事件时间戳严格递增，则使用[递增时间戳`watermark`](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/event_timestamp_extractors.html#assigners-with-ascending-timestamps)生成器生成每个分区的`watermark`，在整体`watermark`上产生的结果也非常好。

下图显示了如何使用每个`Kafka`分区生成`watermark`，以及在这种情况下`watermark`如何通过流数据流进行传播:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/%E7%94%9F%E6%88%90%E6%97%B6%E9%97%B4%E6%88%B3%E4%B8%8EWatermarks-1.png?raw=true)

Java版本:
```java
FlinkKafkaConsumer09<MyType> kafkaSource = new FlinkKafkaConsumer09<>("myTopic", schema, props);
kafkaSource.assignTimestampsAndWatermarks(new AscendingTimestampExtractor<MyType>() {

    @Override
    public long extractAscendingTimestamp(MyType element) {
        return element.eventTimestamp();
    }
});

DataStream<MyType> stream = env.addSource(kafkaSource);
```

Scala版本:
```
val kafkaSource = new FlinkKafkaConsumer09[MyType]("myTopic", schema, props)
kafkaSource.assignTimestampsAndWatermarks(new AscendingTimestampExtractor[MyType] {
    def extractAscendingTimestamp(element: MyType): Long = element.eventTimestamp
})

val stream: DataStream[MyType] = env.addSource(kafkaSource)
```

备注:
```
Flink版本:1.4
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/event_timestamps_watermarks.html
