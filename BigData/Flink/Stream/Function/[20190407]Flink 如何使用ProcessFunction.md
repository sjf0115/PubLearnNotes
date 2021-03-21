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

### 1. 抽象级别

在学习 ProcessFunction 之前，我们先来回顾一下 Flink 的[抽象级别](http://smartsi.club/flink-programming-model.html)。Flink 为我们提供了不同级别的抽象层次来开发流处理和批处理应用程序：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-programming-model-1.png?raw=true)

最低级别的抽象只是提供有状态的数据流，通过 ProcessFunction 集成到 DataStream API 中。这里的 ProcessFunction 就是我们本章将要重点介绍的内容。ProcessFunction 可以让用户轻松的处理来自一个或多个数据流的事件，并可以使用一致性容错状态。另外，用户可以注册事件时间或者处理时间的回调函数以实现复杂的计算。

在实际中，大多数应用程序都不需要上面的低级抽象，而是使用 DataStream API 或者 DataSet API 进行编程。这些核心 API 提供了用于数据处理的通用构建模块，例如，Join，聚合，窗口，状态等。低级别的 ProcessFunction 与 DataStream API 集成在一起，使得可以对特定操作使用低级别的抽象接口。

再上一抽象层次是 Table API，是以表为核心的声明式DSL，可以动态地改变表(当表表示流数据时)。Table API 遵循(扩展的)关系性模型：每个表都有一个 Schema (类似于关系性数据库中的表)，对应的 API 也提供了关系性数据库类似的操作，例如，select，project，join，group-by，aggregate等。Table API 声明性地定义了如何在逻辑上实现操作，而不是明确指定操作实现的具体代码。尽管 Table API 可以通过各种类型的用户自定义函数进行扩展，但它比核心API表达性要差一些，使用上要更简洁一些(编写代码更少)。另外，Table API 程序也会通过优化器在执行之前进行优化。表和 DataStream、DataSet 可以进行无缝转换，也可以允许程序混合使用 Table API 和 DataStream/DataSet API。

Flink 提供的最高级抽象是 SQL。这种抽象在语法和表现力方面与 Table API 类似，但是是通过 SQL 查询表达式实现程序。SQL抽象与 Table API 紧密交互，SQL查询可以在 Table API 定义的表上执行。

### 2. ProcessFunction

从上面抽象层次来看，从上往下在使用上有更高的灵活性，相应的易用性也会越来越低。ProcessFunction 相比其他函数给我们提供了最大的灵活性，可以允许我们访问流应用程序所有的基本构件：
- 事件(数据流元素)
- 状态(容错和一致性，只适用于 KeyedStream)
- Timer(定时器：事件时间和处理时间)

ProcessFunction 可以被认为是一种提供了对 State 和 Timer 访问的 FlatMapFunction。每在输入流中接收到一个事件，就会调用此函数来处理。如下代码所示是 ProcessFunction 接口：
```java
public abstract class ProcessFunction<I, O> extends AbstractRichFunction {
	public abstract void processElement(I value, Context ctx, Collector<O> out) throws Exception;
	public void onTimer(long timestamp, OnTimerContext ctx, Collector<O> out) throws Exception {}

	public abstract class Context {
		public abstract Long timestamp();
		public abstract TimerService timerService();
		public abstract <X> void output(OutputTag<X> outputTag, X value);
	}

	public abstract class OnTimerContext extends Context {
		public abstract TimeDomain timeDomain();
	}
}
```
ProcessFunction 接口比较简单，主要提供了两个方法：
- processElement：对于每一个接入的数据元素通过该方法可以实现状态的更新，也可以注册基于事件时间或者处理时间的定时器（未来某一时间需要调用的 callback 回调函数）。
- onTimer：通过该方法可以在当某一时间到来后检查条件是否满足，并执行对应的操作，例如输出数据元素等。

对于容错的状态，ProcessFunction 可以通过 RuntimeContext 访问 KeyedState，类似于其他有状态函数访问 KeyedState。Timer 可以根据处理时间或者事件时间的变化做一些对应的处理。每次调用 processElement() 都可以获得一个 Context 对象，通过该对象可以访问元素的事件时间戳以及 TimerService。TimerService 可以为尚未发生的事件时间或者处理时间实例注册回调。当 Timer 到达某个时刻时，会调用 onTimer() 方法。在调用期间，所有状态再次限定为 Timer 创建的键，允许定时器操作 KeyedState。

> 如果要访问 KeyedState 和定时器，那必须在 KeyedStream 上使用 ProcessFunction。

```java
stream.keyBy(...).process(new MyProcessFunction())
```

### 3. 如何使用ProcessFunction

在以下示例中，KeyedProcessFunction 为每个 Key 维护一个计数器，并且会把最近一分钟(事件时间)内没有更新的键/值对输出：
- 计数，键以及最后更新的时间戳会存储在 ValueState 中，ValueState 由 key 隐含定义。
- 对于每条记录，KeyedProcessFunction 增加计数器并修改最后的时间戳。
- 该函数还会在一分钟后调用回调（事件时间）。
- 每次调用回调时，都会检查存储计数的最后修改时间与回调的事件时间时间戳，如果匹配则发送`键/计数`键值对（即在一分钟内没有更新）

> 这个简单的例子可以用会话窗口实现。在这里使用 KeyedProcessFunction 只是用来说明它的基本模式。

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

```
A,2021-03-02 08:48:01
B,2021-03-02 08:48:05
A,2021-03-02 08:48:11

A,2021-03-02 08:58:21
```


> 在 Flink 1.4.0 版本之前，当调用处理时间定时器时，`ProcessFunction.onTimer()` 方法会将当前处理时间设置为事件时间时间戳。用户可能会注意不到，但是这是有问题的，因为处理时间时间戳是不确定的，不与 Watermark 对齐。此外，如果用户实现的逻辑依赖于这个错误的时间戳，很可能会出现出乎意料的错误。升级到 1.4.0 版本后，使用不正确的事件时间戳的作业会失败，用户必须将作业调整为正确的逻辑。

### 4. KeyedProcessFunction

KeyedProcessFunction 作为 ProcessFunction 的扩展，可以在 onTimer() 方法中访问 Timer 的 Key：
```java
@Override
public void onTimer(long timestamp, OnTimerContext ctx, Collector<OUT> out) throws Exception {
    K key = ctx.getCurrentKey();
    // ...
}
```

### 5. Timer

基于事件时间或者处理时间的 Timer 在内部由 TimerService 维护并排队执行。TimerService 只为同一个 Key 和时间戳保存一个 Timer，即每个 Key 在每个时间戳上最多有一个 Timer。如果为同一时间戳注册了多个 Timer，那么也只会调用一次 onTimer() 方法。

> Flink同步调用 onTimer() 和 processElement() 方法。因此，用户不必担心状态的并发修改。

#### 5.1 容错能力

Timer 具有容错能力，并且与应用程序的状态一起进行快照。如果故障恢复或从保存点启动应用程序，就会恢复 Timer。

#### 5.2 Timer合并

由于 Flink 仅为同一个 Key 和时间戳维护一个 Timer，因此可以通过降低 Timer 的频率来进行合并以减少 Timer 的数量。对于频率为1秒的定时器（事件时间或处理时间），我们可以将目标时间向下舍入为整秒数。Timer 最多提前1秒触发。因此，每个 Key 在每秒最多有一个定时器：
```java
long coalescedTime = ((ctx.timestamp() + timeout) / 1000) * 1000;
ctx.timerService().registerProcessingTimeTimer(coalescedTime);
```

由于事件时间 Timer 仅当 Watermark 到达时才会触发，因此我们可以将当前 Watermark 与下一个 Watermark 的 Timer 一起调度和合并：
```java
long coalescedTime = ctx.timerService().currentWatermark() + 1;
ctx.timerService().registerEventTimeTimer(coalescedTime);
```

可以使用如下方式停止一个处理时间的 Timer：
```java
long timestampOfTimerToStop = ...
ctx.timerService().deleteProcessingTimeTimer(timestampOfTimerToStop);
```

可以使用如下方式停止一个事件时间的 Timer：
             Java版本：
```java
long timestampOfTimerToStop = ...
ctx.timerService().deleteEventTimeTimer(timestampOfTimerToStop);
```

> 如果没有给指定时间戳注册定时器，那么停止定时器没有任何效果。                               


欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[Process Function (Low-level Operations)](https://ci.apache.org/projects/flink/flink-docs-stable/dev/stream/operators/process_function.html)
