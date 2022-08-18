---
layout: post
author: sjf0115
title: Flink 如何使用算子
date: 2018-02-28 10:25:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-operators-overall
---

> Flink版本：1.11

算子(`Operator`)可以将一个或多个 DataStream 转换为一个新的 DataStream。程序可以将多个 Transformations 组合成复杂的数据流拓扑。

### 1. DataStream Transformations

#### 1.1 Map  

```
DataStream → DataStream
```

输入一个元素并生成一个对应的元素。如下所示将输入流的值加倍的 map 函数：

Java版本：
```Java
DataStream<Integer> dataStream = //...
dataStream.map(new MapFunction<Integer, Integer>() {
    @Override
    public Integer map(Integer value) throws Exception {
        return 2 * value;
    }
});
```

scala版本：
```scala
dataStream.map { x => x * 2 }
```

#### 1.2 FlatMap

```
DataStream → DataStream
```
输入一个元素不生成元素，或者生成一个、多个元素。如下所示将句子按空格拆分为单词的 flatMap 函数：

Java版本：
```java
dataStream.flatMap(new FlatMapFunction<String, String>() {
    @Override
    public void flatMap(String value, Collector<String> out)
        throws Exception {
        for(String word: value.split(" ")){
            out.collect(word);
        }
    }
});
```
Scala版本:
```scala
dataStream.flatMap { str => str.split(" ") }
```

#### 1.3 Filter

```
DataStream → DataStream
```

为每一个元素计算布尔值并保留返回 true 的那些元素。如下所示过滤非零值的 filter 函数：

Java版本:
```java
dataStream.filter(new FilterFunction<Integer>() {
    @Override
    public boolean filter(Integer value) throws Exception {
        return value != 0;
    }
});
```
Scala版本:
```scala
dataStream.filter { _ != 0 }
```

#### 1.4 KeyBy

```
DataStream → KeyedStream
```

逻辑上将一个流分成不相交的不同分区，每个分区包含相同键的元素。在内部，这是通过哈希分区实现的。参阅博文[Flink 定义keys的几种方法](http://smartsi.club/flink-how-to-specifying-keys.html)来了解如何指定键。这个转换返回一个 KeyedStream。

Java版本:
```java
dataStream.keyBy("someKey") // Key by field "someKey"
dataStream.keyBy(0) // Key by the first element of a Tuple
```

Scala版本:
```scala
dataStream.keyBy("someKey") // Key by field "someKey"
dataStream.keyBy(0) // Key by the first element of a Tuple
```

> 备注

> 在以下情况，不能指定为key：
> - POJO类型，但没有覆盖hashCode()方法并依赖于Object.hashCode()实现。
> - 任意类型的数组。

#### 1.5 Reduce

```
KeyedStream → DataStream
```

在 Keyed Stream 上的"滚动"Reduce。将当前元素与上一个 Reduce 后的值进行 Reduce，并生成一个新值。如下所示创建求和的 reduce 函数：

Java版本:
```java
keyedStream.reduce(new ReduceFunction<Integer>() {
    @Override
    public Integer reduce(Integer value1, Integer value2)
    throws Exception {
        return value1 + value2;
    }
});
```

Scala版本:
```scala
keyedStream.reduce { _ + _ }
```

#### 1.6 Aggregations

```
KeyedStream → DataStream
```
在 Keyded Stream 上滚动聚合。min 和 minBy 的区别是 min 返回最小值，而 minBy 返回在该字段上具有最小值的元素（max 和 maxBy 同理）。

Java版本:
```java
keyedStream.sum(0);
keyedStream.sum("key");
keyedStream.min(0);
keyedStream.min("key");
keyedStream.max(0);
keyedStream.max("key");
keyedStream.minBy(0);
keyedStream.minBy("key");
keyedStream.maxBy(0);
keyedStream.maxBy("key");
```

Scala版本:
```scala
keyedStream.sum(0)
keyedStream.sum("key")
keyedStream.min(0)
keyedStream.min("key")
keyedStream.max(0)
keyedStream.max("key")
keyedStream.minBy(0)
keyedStream.minBy("key")
keyedStream.maxBy(0)
keyedStream.maxBy("key")
```

#### 1.7 Window

```
KeyedStream → WindowedStream
```

可以在已经分区的 KeyedStream 上定义窗口。窗口根据某些特性（例如，在最近5秒内到达的数据）对每个键的数据进行分组。请参阅[Flink中的窗口是什么](http://smartsi.club/flink-stream-windows-overall.html)以获取窗口的详细说明。

Java版本:
```java
dataStream
  .keyBy(0)
  .window(TumblingEventTimeWindows.of(Time.seconds(5))); // Last 5 seconds of data
```
Scala版本:
```scala
dataStream
  .keyBy(0)
  .window(TumblingEventTimeWindows.of(Time.seconds(5))) // Last 5 seconds of data
```

#### 1.8 WindowAll

```
DataStream → AllWindowedStream
```

可以在常规的 DataStream 上定义窗口。窗口根据某些特征（例如，在最近5秒内到达的数据）对所有流数据进行分组。请参阅[Flink中的窗口是什么](http://smartsi.club/flink-stream-windows-overall.html)以获取窗口的详细说明。

> 在很多情况下，这是不是一个并发转换操作。所有记录都在 windowAll 算子的一个任务上处理。

Java版本:
```java
dataStream
  .windowAll(TumblingEventTimeWindows.of(Time.seconds(5))); // Last 5 seconds of data
```

Scala版本:
```scala
dataStream
  .windowAll(TumblingEventTimeWindows.of(Time.seconds(5))) // Last 5 seconds of data
```

#### 1.9 Window Apply

```
WindowedStream → DataStream
AllWindowedStream → DataStream
```

将普通函数应用于整个窗口。如下是手动对窗口元素求和的函数。

> 注意：如果你使用的是 windowAll 算子，则需要使用 AllWindowFunction 方法。

Java版本：
```java
windowedStream.apply (new WindowFunction<Tuple2<String,Integer>, Integer, Tuple, Window>() {
    public void apply (Tuple tuple,
            Window window,
            Iterable<Tuple2<String, Integer>> values,
            Collector<Integer> out) throws Exception {
        int sum = 0;
        for (value t: values) {
            sum += t.f1;
        }
        out.collect (new Integer(sum));
    }
});

// applying an AllWindowFunction on non-keyed window stream
allWindowedStream.apply (new AllWindowFunction<Tuple2<String,Integer>, Integer, Window>() {
    public void apply (Window window,
            Iterable<Tuple2<String, Integer>> values,
            Collector<Integer> out) throws Exception {
        int sum = 0;
        for (value t: values) {
            sum += t.f1;
        }
        out.collect (new Integer(sum));
    }
});
```

Scala版本:
```scala
windowedStream.apply { WindowFunction }

// applying an AllWindowFunction on non-keyed window stream
allWindowedStream.apply { AllWindowFunction }
```

#### 1.10 Window Reduce

```
WindowedStream → DataStream
```
将 Reduce 函数应用于窗口中并返回 Reduce 后的值。

Java版本:
```java
windowedStream.reduce (new ReduceFunction<Tuple2<String,Integer>>() {
    public Tuple2<String, Integer> reduce(Tuple2<String, Integer> value1, Tuple2<String, Integer> value2) throws Exception {
        return new Tuple2<String,Integer>(value1.f0, value1.f1 + value2.f1);
    }
});
```

Scala版本:
```scala
windowedStream.reduce { _ + _ }
```

#### 1.11 Aggregations on windows

```
WindowedStream → DataStream
```
在窗口上进行聚合。min 和 minBy 的区别是 min 返回最小值，而 minBy 返回该字段中具有最小值的元素（max 和 maxBy 同理）。

Java版本:
```java
windowedStream.sum(0);
windowedStream.sum("key");
windowedStream.min(0);
windowedStream.min("key");
windowedStream.max(0);
windowedStream.max("key");
windowedStream.minBy(0);
windowedStream.minBy("key");
windowedStream.maxBy(0);
windowedStream.maxBy("key");
```

Scala版本:
```scala
windowedStream.sum(0)
windowedStream.sum("key")
windowedStream.min(0)
windowedStream.min("key")
windowedStream.max(0)
windowedStream.max("key")
windowedStream.minBy(0)
windowedStream.minBy("key")
windowedStream.maxBy(0)
windowedStream.maxBy("key")
```

#### 1.12 Union
```
DataStream* → DataStream
```

合并两个或多个数据流，并创建一个包含所有流元素的新流。

> 注意：如果你与自己进行合并，每个元素将在结果流中出现两次。

Java版本:
```java
dataStream.union(otherStream1, otherStream2, ...);
```
Scala版本:
```scala
dataStream.union(otherStream1, otherStream2, ...)
```

#### 1.13 Window Join

```
DataStream,DataStream → DataStream
```

在给定的键和窗口上对两个数据流进行 join。

Java版本:
```java
dataStream.join(otherStream)
    .where(<key selector>).equalTo(<key selector>)
    .window(TumblingEventTimeWindows.of(Time.seconds(3)))
    .apply (new JoinFunction () {...});
```

Scala版本:
```scala
dataStream.join(otherStream)
    .where(<key selector>).equalTo(<key selector>)
    .window(TumblingEventTimeWindows.of(Time.seconds(3)))
    .apply { ... }
```

#### 1.14 Window CoGroup

```
DataStream,DataStream → DataStream
```

在给定键和窗口上对两个数据流进行组合。

Java版本:
```java
dataStream.coGroup(otherStream)
    .where(0).equalTo(1)
    .window(TumblingEventTimeWindows.of(Time.seconds(3)))
    .apply (new CoGroupFunction () {...});
```

Scala版本:
```scala
dataStream.coGroup(otherStream)
    .where(0).equalTo(1)
    .window(TumblingEventTimeWindows.of(Time.seconds(3)))
    .apply {}
```

### 2. 物理分区

物理分区操作的作用是根据指定的分区策略将数据重新分配到不同节点的 Task 实例上执行。当使用 DataStream 提供的 API 对数据处理过程中，依赖算子本身对数据的分区控制，如果用户希望自己控制数据分区，例如当数据发生数据倾斜的时候，就需要通过定义物理分区策略对数据进行重新分布处理。Flink 中已经提供了常见的分区策略，例如，随机分区(Random Partitioning)、平衡分区(Rebalancing Partitioning)、按比例分区(Rescaling Partitioning)等。

#### 2.1 Custom partitioning

```
DataStream → DataStream
```

使用用户自定义的分区器为每个元素选择指定的任务。

```java
dataStream.partitionCustom(partitioner, "someKey");
dataStream.partitionCustom(partitioner, 0);
```

#### 2.2 Random partitioning

```
DataStream → DataStream
```
通过随机的方式将数据分配在下游算子的每个分区中，分区相对均衡，但是比较容易失去原有数据的分区结构。

```java
dataStream.shuffle();
```

#### 2.3 Rebalancing (Round-robin partitioning)

```
DataStream → DataStream
```
通过循环的方式对数据进行重分区，尽可能保证每个分区的数据平衡。存在数据倾斜时使用这种策略就是比较有效的优化方法。

```java
dataStream.rebalance();
```

#### 2.4 Rescaling

```
DataStream → DataStream
```

和 Rebalancing Partitioning ⼀样，Rescaling Partitioning 也是⼀种通过循环的⽅式进⾏数据重平衡的分区策略。但不同的是，当使⽤ Rebalancing Partitioning 时，数据会全局性地通过⽹络介质传输到其他所有节点完成数据的重新平衡，⽽ Rescaling Partitioning 仅仅会对上下游继承的算⼦数据进⾏重平衡，具体的分区主要根据上下游算⼦的并⾏度决定。例如，上游算⼦的并发度为2，下游算⼦的并发度为6，其中一个上游算子将元素分配给其中三个下游算子，另一个上游算子分配给其他三个下游算子。另一方面，如果下游算子的并发度为2，而上游算子的并发度为6，那么其中三个上游算子将分配元素到其中一个下游算子，而其他三个上游算子将分配给另一个下游算子。

这个图显示了在上面的例子中的连接模式：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink-stream-operators-overall.png?raw=true)

```java
dataStream.rescale();
```

#### 2.5 Broadcasting

```
DataStream → DataStream
```

广播元素到每个分区。

```Java
dataStream.broadcast()
```

### 3. 任务链和资源组

Flink 可以将多个任务链接成一个任务在一个线程中执行，在降低线程上下文切换的开销，减少缓存容量，提高系统的吞吐量的同时降低延迟。

API 可以对任务链进行更细粒度的控制。如果要禁用整个作业中的链接，请使用 `StreamExecutionEnvironment.disableOperatorChaining()`。对于更细粒度的控制，可用使用以下函数。请注意，这些函数只能在 DataStream 转换操作之后使用，因为它们需要引用上一个转换操作。例如，你可以使用 `someStream.map（...）.startNewChain()`，但不能使用 `someStream.startNewChain()`。

> 资源组是 Flink 中的插槽，请参阅[插槽](https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/config.html#configuring-taskmanager-processing-slots)。如果需要，你可以在不同的插槽中手动隔离算子。

#### 3.1 创建新链

从这个算子开始，创建一个新的链。如下所示将两个 mapper 链接，但是 filter 不会与第一个 mapper 链接：
```java
someStream.filter(...).map(...).startNewChain().map(...);
```

#### 3.2 关闭链优化

不会将 map 算子链接到链上：
```java
someStream.map(...).disableChaining();
```

#### 3.3 设置 Slot 共享组

设置算子的 Slot 共享组。Flink 会将使用相同 Slot 共享组的算子放入同一 Slot，同时将不在同一个 Slot 共享组的算子放在其他 Slot 中。这可以用来隔离 Slot。默认 Slot 共享组的名称为 `default`，可通过调用 `slotSharingGroup("default")` 将算子显式加入共享组：
```java
someStream.filter(...).slotSharingGroup("name");
```

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文：[Operators](https://ci.apache.org/projects/flink/flink-docs-release-1.12/dev/stream/operators/)
