---
layout: post
author: sjf0115
title: Flink 如何使用ProcessFunction
date: 2019-04-07 20:17:21
tags:
  - Flink

categories: Flink
permalink: how-to-user-process-function-of-flink
---

### 1. ProcessFunction

ProcessFunction 函数是低阶流处理算子，可以访问流应用程序所有（非循环）基本构建块：
- 事件 (数据流元素)
- 状态 (容错和一致性)
- 定时器 (事件时间和处理时间)

ProcessFunction 可以被认为是一种提供了对 KeyedState 和定时器访问的 FlatMapFunction。每在输入流中接收到一个事件，就会调用来此函数来处理。

对于容错的状态，ProcessFunction 可以通过 RuntimeContext 访问 KeyedState，类似于其他有状态函数访问 KeyedState。

定时器可以对处理时间和事件时间的变化做一些处理。每次调用 `processElement()` 都可以获得一个 Context 对象，通过该对象可以访问元素的事件时间戳以及 TimerService。TimerService 可以为尚未发生的事件时间/处理时间实例注册回调。当定时器到达某个时刻时，会调用 `onTimer()` 方法。在调用期间，所有状态再次限定为定时器创建的键，允许定时器操作 KeyedState。

> 如果要访问 KeyedState 和定时器，那必须在 KeyedStream 上使用 ProcessFunction。

```java
stream.keyBy(...).process(new MyProcessFunction())
```

### 2. 低阶Join

要在两个输入上实现低阶操作，应用程序可以使用 CoProcessFunction。这个函数绑定了两个不同的输入，并为来自两个不同输入的记录分别调用 `processElement1()` 和 `processElement2()`。

实现低阶 Join 通常遵循以下模式：
- 为一个输入（或两个）创建状态对象。
- 在从输入中收到元素时更新状态。
- 在从其他输入收到元素时扫描状态对象并生成 Join 结果。

例如，你可能会将客户数据与金融交易数据进行 Join，并将客户数据存储在状态中。如果你比较关心无序事件 Join 的完整性和确定性，那么当客户数据流的 Watermark 已经超过交易时间时，你可以使用定时器来计算和发出交易的 Join。

### 3. Example

在以下示例中，KeyedProcessFunction 为每个键维护一个计数，并且会把一分钟(事件时间)内没有更新的键/值对输出：
- 计数，键以及最后更新的时间戳会存储在 ValueState 中，ValueState 由 key 隐含定义。
- 对于每条记录，KeyedProcessFunction 增加计数器并修改最后的时间戳。
- 该函数还会在一分钟后调用回调（事件时间）。
- 每次调用回调时，都会检查存储计数的最后修改时间与回调的事件时间时间戳，如果匹配则发送`键/计数`键值对（即在一分钟内没有更新）

> 这个简单的例子可以用会话窗口实现。在这里使用 KeyedProcessFunction 只是用来说明它的基本模式。

Java版本：
```java
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.java.tuple.Tuple;
import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.ProcessFunction;
import org.apache.flink.streaming.api.functions.ProcessFunction.Context;
import org.apache.flink.streaming.api.functions.ProcessFunction.OnTimerContext;
import org.apache.flink.util.Collector;

// 数据源
DataStream<Tuple2<String, String>> stream = ...;

// 对KeyedStream应用ProcessFunction
DataStream<Tuple2<String, Long>> result = stream
    .keyBy(0)
    .process(new CountWithTimeoutFunction());

/**
 * 存储在state中的数据类型
 */
public class CountWithTimestamp {
    public String key;
    public long count;
    public long lastModified;
}

/**
 * 维护了计数和超时间隔的ProcessFunction实现
 */
public class CountWithTimeoutFunction extends KeyedProcessFunction<Tuple, Tuple2<String, String>, Tuple2<String, Long>> {
    /** 这个状态是通过 ProcessFunction 维护*/
    private ValueState<CountWithTimestamp> state;

    @Override
    public void open(Configuration parameters) throws Exception {
        state = getRuntimeContext().getState(new ValueStateDescriptor<>("myState", CountWithTimestamp.class));
    }

    @Override
    public void processElement(
            Tuple2<String, String> value,
            Context ctx,
            Collector<Tuple2<String, Long>> out) throws Exception {

        // 查看当前计数
        CountWithTimestamp current = state.value();
        if (current == null) {
            current = new CountWithTimestamp();
            current.key = value.f0;
        }

        // 更新状态中的计数
        current.count++;

        // 设置状态的时间戳为记录的事件时间时间戳
        current.lastModified = ctx.timestamp();

        // 状态回写
        state.update(current);

        // 从当前事件时间开始注册一个60s的定时器
        ctx.timerService().registerEventTimeTimer(current.lastModified + 60000);
    }

    @Override
    public void onTimer(
            long timestamp,
            OnTimerContext ctx,
            Collector<Tuple2<String, Long>> out) throws Exception {

        // 得到设置这个定时器的键对应的状态
        CountWithTimestamp result = state.value();

        // 检查定时器是过时定时器还是最新定时器
        if (timestamp == result.lastModified + 60000) {
            // emit the state on timeout
            out.collect(new Tuple2<String, Long>(result.key, result.count));
        }
    }
}
```
Scala版本:
```Scala
import org.apache.flink.api.common.state.ValueState
import org.apache.flink.api.common.state.ValueStateDescriptor
import org.apache.flink.api.java.tuple.Tuple;
import org.apache.flink.streaming.api.functions.ProcessFunction
import org.apache.flink.streaming.api.functions.ProcessFunction.Context
import org.apache.flink.streaming.api.functions.ProcessFunction.OnTimerContext
import org.apache.flink.util.Collector

// the source data stream
val stream: DataStream[Tuple2[String, String]] = ...

// apply the process function onto a keyed stream
val result: DataStream[Tuple2[String, Long]] = stream
  .keyBy(0)
  .process(new CountWithTimeoutFunction())

/**
  * The data type stored in the state
  */
case class CountWithTimestamp(key: String, count: Long, lastModified: Long)

/**
  * The implementation of the ProcessFunction that maintains the count and timeouts
  */
class CountWithTimeoutFunction extends KeyedProcessFunction[Tuple, (String, String), (String, Long)] {

  /** The state that is maintained by this process function */
  lazy val state: ValueState[CountWithTimestamp] = getRuntimeContext
    .getState(new ValueStateDescriptor[CountWithTimestamp]("myState", classOf[CountWithTimestamp]))

  override def processElement(
      value: (String, String),
      ctx: KeyedProcessFunction[Tuple, (String, String), (String, Long)]#Context,
      out: Collector[(String, Long)]): Unit = {

    // initialize or retrieve/update the state
    val current: CountWithTimestamp = state.value match {
      case null =>
        CountWithTimestamp(value._1, 1, ctx.timestamp)
      case CountWithTimestamp(key, count, lastModified) =>
        CountWithTimestamp(key, count + 1, ctx.timestamp)
    }

    // write the state back
    state.update(current)

    // schedule the next timer 60 seconds from the current event time
    ctx.timerService.registerEventTimeTimer(current.lastModified + 60000)
  }

  override def onTimer(
      timestamp: Long,
      ctx: KeyedProcessFunction[Tuple, (String, String), (String, Long)]#OnTimerContext,
      out: Collector[(String, Long)]): Unit = {

    state.value match {
      case CountWithTimestamp(key, count, lastModified) if (timestamp == lastModified + 60000) =>
        out.collect((key, count))
      case _ =>
    }
  }
}
```

> 在 Flink 1.4.0 版本之前，当调用处理时间定时器时，`ProcessFunction.onTimer()` 方法会将当前处理时间设置为事件时间时间戳。用户可能会注意不到，但是这是有问题的，因为处理时间时间戳是不确定的，不与 Watermark 对齐。此外，如果用户实现的逻辑依赖于这个错误的时间戳，很可能会出现出乎意料的错误。升级到 1.4.0 版本后，使用不正确的事件时间戳的作业会失败，用户必须将作业调整为正确的逻辑。

### 4. KeyedProcessFunction

KeyedProcessFunction 作为 ProcessFunction 的扩展，可以在 `onTimer()` 方法中访问定时器的键：

Java版本:
```java
@Override
public void onTimer(long timestamp, OnTimerContext ctx, Collector<OUT> out) throws Exception {
    K key = ctx.getCurrentKey();
    // ...
}
```
Scala版本:
```Scala
override def onTimer(timestamp: Long, ctx: OnTimerContext, out: Collector[OUT]): Unit = {
  var key = ctx.getCurrentKey
  // ...
}
```
### 5. 定时器

TimerService 在内部维护两种类型的定时器（处理时间和事件时间定时器）并排队执行。

TimerService 会删除每个键和时间戳重复的定时器，即每个键在每个时间戳上最多有一个定时器。如果为同一时间戳注册了多个定时器，则只会调用一次 `onTimer（）` 方法。

> Flink同步调用 `onTimer()` 和 `processElement()` 方法。因此，用户不必担心状态的并发修改。

#### 5.1 容错

定时器具有容错能力，并且与应用程序的状态一起进行快照。如果故障恢复或从保存点启动应用程序，就会恢复定时器。

> 在故障恢复之前应该触发的处理时间定时器会被立即触发。当应用程序从故障中恢复或从保存点启动时，可能会发生这种情况。

#### 5.2 定时器合并

由于 Flink 仅为每个键和时间戳维护一个定时器，因此可以通过降低定时器的频率来进行合并以减少定时器的数量。

对于频率为1秒的定时器（事件时间或处理时间），我们可以将目标时间向下舍入为整秒数。定时器最多提前1秒触发，但不会迟于我们的要求，精确到毫秒。因此，每个键每秒最多有一个定时器。

Java版本:
```java
long coalescedTime = ((ctx.timestamp() + timeout) / 1000) * 1000;
ctx.timerService().registerProcessingTimeTimer(coalescedTime);
```
Scala版本:
```Scala
val coalescedTime = ((ctx.timestamp + timeout) / 1000) * 1000
ctx.timerService.registerProcessingTimeTimer(coalescedTime)
```
由于事件时间定时器仅当 Watermark 到达时才会触发，因此我们可以将当前 Watermark 与下一个 Watermark 的定时器一起调度和合并：

Java版本:
```java
long coalescedTime = ctx.timerService().currentWatermark() + 1;
ctx.timerService().registerEventTimeTimer(coalescedTime);
```
Scala版本:
```Scala
val coalescedTime = ctx.timerService.currentWatermark + 1
ctx.timerService.registerEventTimeTimer(coalescedTime)
```
可以使用一下方式停止一个处理时间定时器：
Java版本:
```java
long timestampOfTimerToStop = ...
ctx.timerService().deleteProcessingTimeTimer(timestampOfTimerToStop);
```
Scala版本:
```Scala
val timestampOfTimerToStop = ...
ctx.timerService.deleteProcessingTimeTimer(timestampOfTimerToStop)
```
可以使用一下方式停止一个事件时间定时器：
             Java版本：
```java
long timestampOfTimerToStop = ...
ctx.timerService().deleteEventTimeTimer(timestampOfTimerToStop);
```
Scala版本：
```scala
val timestampOfTimerToStop = ...
ctx.timerService.deleteEventTimeTimer(timestampOfTimerToStop)
```
> 如果没有给指定时间戳注册定时器，那么停止定时器没有任何效果。                               

> Flink版本:1.8

英译对照:
- 事件: Events
- 状态: State
- 定时器: Timers

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[Process Function (Low-level Operations)](https://ci.apache.org/projects/flink/flink-docs-stable/dev/stream/operators/process_function.html)
