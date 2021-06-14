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

从上面抽象层次来看，从上往下在使用上有更高的灵活性，相应的易用性也会越来越低。Process Function 是一个低级流处理操作，相比其他函数可以给我们提供最大的灵活性，允许我们访问流应用程序所有的基本构建块：
- Event(事件：数据流元素)
- State(状态：用于容错和一致性，只适用于 KeyedStream)
- Timer(定时器：事件时间和处理时间，只适用于 KeyedStream)

在这我们只介绍低级流处理算子中的典型算子：ProcessFunction 和 KeyedProcessFunction。例如，CoProcessFunction、 KeyedCoProcessFunction 等其他低阶流处理算子暂时先不做介绍。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/how-to-user-process-function-of-flink-1.png?raw=true)

DataStream 与 KeyedStreamd 都有 process 方法，DataStream 接收的是 ProcessFunction，而 KeyedStream 接收的是 KeyedProcessFunction(原本也支持 ProcessFunction，现在已被废弃)：
```java
// DataStream
@PublicEvolving
public <R> SingleOutputStreamOperator<R> process(ProcessFunction<T, R> processFunction) {
}

// KeyedStream
@Deprecated
@Override
@PublicEvolving
public <R> SingleOutputStreamOperator<R> process(ProcessFunction<T, R> processFunction) {
}

@PublicEvolving
public <R> SingleOutputStreamOperator<R> process(KeyedProcessFunction<KEY, T, R> keyedProcessFunction) {
}
```

从上图中可以看出 ProcessFunction 既可以作用于 DataStream 上，也可以作用于 KeyedStream 上。如果作用于 DataStream 上，只能访问数据流元素(事件)，不能访问状态，也不支持注册定时器。ProcessFunction 也可以作用于 KeyedStream 上，只不过已经被标记 @Deprecated，建议在 KeyedStream 上使用 KeyedProcessFunction。

#### 2.1 ProcessFunction

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
- processElement：对于输入数据流中的每一个元素都会调用该方法，可以产生零个或多个元素作为输出。通过该方法可以实现状态的更新，也可以通过 Context 对象注册基于事件时间或者处理时间的定时器，并在未来某一时间调用下面的 onTimer 回调函数。
- onTimer：如果注册了定时器，通过该方法可以在当某一时间到来后检查条件是否满足，并执行对应的操作，例如输出数据元素等。

> 需要注意的是仅当 ProcessFunction 作用于 KeyedStream 上时，才可以访问 KeyedState 和 定时器（也仅限定对应键的 Timer）。

每次调用 processElement() 都可以获得一个 Context 对象，通过该对象可以访问元素的事件时间戳，也可以获取 TimeService 来查询当前时间或者注册定时器。TimerService 可以为尚未发生的事件时间或者处理时间实例注册一个定时器。当定时器触发时，就会调用 onTimer() 回调函数。可以通过 onTimer 方法中的 OnTimerContext 对象访问定时器触发时间戳以及获取 TimeService 来查询当前处理时间或者 Watermark，也可以注册定时器。onTimer() 回调函数可能会在不同时间点内被调用，什么时候时间点会被触发呢？这取决于使用处理时间还是事件时间来注册定时器：
- 使用处理时间注册定时器时，当服务器的系统时间到达定时器的时间戳时，就会调用 onTimer() 方法。
- 使用事件时间注册定时器时，当算子的 Watermark 到达或超过定时器的时间戳时，就会调用 onTimer() 方法。

> Timer 的具体使用细节可以参阅 [Flink 定时器的4个特性](http://smartsi.club/4-characteristics-of-timers-in-apache-flink.html)

由于 ProcessFunction 继承了 AbstractRichFunction 抽象类，因此可以通过 RuntimeContext 访问 KeyedState。

> 在 Flink 1.4.0 版本之前，当调用处理时间定时器时，ProcessFunction.onTimer() 方法会将当前处理时间设置为事件时间时间戳。用户可能会注意不到，但是这是有问题的，因为处理时间时间戳是不确定的，不与 Watermark 对齐。此外，如果用户实现的逻辑依赖于这个错误的时间戳，很可能会出现出乎意料的错误。升级到 1.4.0 版本后，使用不正确的事件时间戳的作业会失败，用户必须将作业调整为正确的逻辑。

下面我们看一下如何在 KeyedStream 上应用 ProcessFunction（建议生产环境中使用 KeyedProcessFunction 代替）。在以下示例中，ProcessFunction 为每个 Key 维护一个计数器，并会把最近 10s (事件时间)内没有更新的键/值对输出：
- 计数，键以及最后更新的时间戳会存储在 ValueState 中。
- 对于每条记录，ProcessFunction 会增加计数器并修改最后的时间戳。
- 该函数还会在 10s 后调用 onTimer 回调函数（基于事件时间）。
- 每次调用回调时，都会检查存储计数的最后修改时间与回调的事件时间时间戳，如果匹配则会输出 `键/计数` 键值对（即在 10s 内没有更新）

> 这个简单的例子可以用会话窗口实现。在这里使用 ProcessFunction 只是用来说明它的基本模式。

```java
private static class MyProcessFunction extends ProcessFunction<Tuple2<String, String>, Tuple2<String, Long>> {
    // 状态
    private ValueState<MyEvent> state;
    @Override
    public void open(Configuration parameters) throws Exception {
        // 状态描述符
        ValueStateDescriptor<MyEvent> stateDescriptor = new ValueStateDescriptor<>("ProcessFunctionState", MyEvent.class);
        // 状态
        state = getRuntimeContext().getState(stateDescriptor);
    }

    @Override
    public void processElement(Tuple2<String, String> value, Context ctx, Collector<Tuple2<String, Long>> out) throws Exception {
        // 获取Watermark时间戳
        long watermark = ctx.timerService().currentWatermark();
        LOG.info("[Watermark] watermark: [{}|{}]", watermark, DateUtil.timeStamp2Date(watermark));

        String key = value.f0;
        // 当前状态值
        MyEvent stateValue = state.value();
        if (stateValue == null) {
            stateValue = new MyEvent();
            stateValue.count = 0L;
        }
        // 更新值
        stateValue.key = key;
        stateValue.count++;
        stateValue.lastModified = ctx.timestamp();
        // 更新状态
        state.update(stateValue);

        // 注册事件时间定时器 10s后调用onTimer方法
        ctx.timerService().registerEventTimeTimer(stateValue.lastModified + delayTime);
        LOG.info("[Element] Key: {}, Count: {}, LastModified: [{}|{}]",
                stateValue.key, stateValue.count, stateValue.lastModified,
                DateUtil.timeStamp2Date(stateValue.lastModified)
        );
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Tuple2<String, Long>> out) throws Exception {
        // 当前状态值
        MyEvent stateValue = state.value();
        // 检查这是一个过时的定时器还是最新的定时器
        boolean isLatestTimer = false;
        if (timestamp == stateValue.lastModified + delayTime) {
            out.collect(new Tuple2<>(stateValue.key, stateValue.count));
            isLatestTimer = true;
        }

        Long timerTimestamp = ctx.timestamp();
        Long watermark = ctx.timerService().currentWatermark();
        LOG.info("[Timer] Key: {}, Count: {}, LastModified: [{}|{}], TimerTimestamp: [{}|{}], Watermark: [{}|{}], IsLatestTimer: {}",
                stateValue.key, stateValue.count,
                stateValue.lastModified, DateUtil.timeStamp2Date(stateValue.lastModified),
                timerTimestamp, DateUtil.timeStamp2Date(timerTimestamp),
                watermark, DateUtil.timeStamp2Date(watermark),
                isLatestTimer
        );
    }
}

/**
 * 存储在状态中的数据结构
 */
public static class MyEvent {
    public String key;
    public Long count;
    public Long lastModified;
}
```
> 完整代码请查阅:[ProcessFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/function/ProcessFunctionExample.java)

```
a,2021-06-13 20:23:08
a,2021-06-13 20:23:11
b,2021-06-13 20:23:23
c,2021-06-13 20:23:34
a,2021-06-13 20:23:45
b,2021-06-13 20:23:59
b,2021-06-13 20:25:01
```
我们以上面的输入元素为例，来看一下 ProcessFunction 具体执行情况：

| ID | key | 事件时间戳 | 定时器触发时间 | Watermark | 触发定时器 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | a | 20:23:08 | 20:23:18 | 20:22:57 |  无 | |
| 02 | a | 20:23:11 | 20:23:21 | 20:23:00 |  无 | |
| 03 | b | 20:23:23 | 20:23:33 | 20:23:12 |  无 | |
| 04 | c | 20:23:34 | 20:23:44 | 20:23:23 | 01、02 |
| 05 | a | 20:23:45 | 20:23:55 | 20:23:34 | 03 |
| 06 | b | 20:23:59 | 20:24:09 | 20:23:48 | 04 |
| 07 | b | 20:25:01 | 20:25:11 | 20:24:50 | 05、06 |

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/how-to-user-process-function-of-flink-2.png?raw=true)

#### 2.2 KeyedProcessFunction

```java
public abstract class KeyedProcessFunction<K, I, O> extends AbstractRichFunction {

	private static final long serialVersionUID = 1L;
	public abstract void processElement(I value, Context ctx, Collector<O> out) throws Exception;
	public void onTimer(long timestamp, OnTimerContext ctx, Collector<O> out) throws Exception {}
	public abstract class Context {
		public abstract Long timestamp();
		public abstract TimerService timerService();
		public abstract <X> void output(OutputTag<X> outputTag, X value);
		public abstract K getCurrentKey();
	}

	public abstract class OnTimerContext extends Context {
		public abstract TimeDomain timeDomain();
		@Override
		public abstract K getCurrentKey();
	}
}
```
KeyedProcessFunction 作为 ProcessFunction 的扩展，只能作用于 KeyedStream 上。与 ProcessFunction 感官上不同的地方在于 KeyedProcessFunction 可以在 processElement 和 onTimer() 方法中访问对应的 Key：
```java
public void processElement(IN value, Context ctx, Collector<OUT> out) throws Exception {
    String key = ctx.getCurrentKey();
    // ...
}

public void onTimer(long timestamp, OnTimerContext ctx, Collector<OUT> out) throws Exception {
    K key = ctx.getCurrentKey();
    // ...
}
```
> 建议生产环境中使用 KeyedProcessFunction 代替 ProcessFunction。

下面我们看一下如何在 KeyedStream 上应用 KeyedProcessFunction，需求场景跟 ProcessFunction 一样：
```java
private static class MyKeyedProcessFunction extends KeyedProcessFunction<String, Tuple2<String, String>, Tuple2<String, Long>> {
    // 状态
    private ValueState<MyEvent> state;
    @Override
    public void open(Configuration parameters) throws Exception {
        // 状态描述符
        ValueStateDescriptor<MyEvent> stateDescriptor = new ValueStateDescriptor<>("KeyedProcessFunctionState", MyEvent.class);
        // 状态
        state = getRuntimeContext().getState(stateDescriptor);
    }

    @Override
    public void processElement(Tuple2<String, String> value, Context ctx, Collector<Tuple2<String, Long>> out) throws Exception {
        // 获取Watermark时间戳
        long watermark = ctx.timerService().currentWatermark();
        LOG.info("[Watermark] watermark: [{}|{}]", watermark, DateUtil.timeStamp2Date(watermark));

        // 当前状态值
        MyEvent stateValue = state.value();
        if (stateValue == null) {
            stateValue = new MyEvent();
            stateValue.count = 0L;
        }
        // 更新值
        stateValue.count++;
        stateValue.lastModified = ctx.timestamp();
        // 更新状态
        state.update(stateValue);

        // 注册事件时间定时器 60s后调用onTimer方法
        ctx.timerService().registerEventTimeTimer(stateValue.lastModified + delayTime);

        String key = ctx.getCurrentKey();
        LOG.info("[Element] Key: {}, Count: {}, LastModified: [{}|{}]",
                key, stateValue.count, stateValue.lastModified,
                DateUtil.timeStamp2Date(stateValue.lastModified)
        );
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Tuple2<String, Long>> out) throws Exception {
        // Key
        String key = ctx.getCurrentKey();
        // 当前状态值
        MyEvent stateValue = state.value();
        // 检查这是一个过时的定时器还是最新的定时器
        boolean isLatestTimer = false;
        if (timestamp == stateValue.lastModified + delayTime) {
            out.collect(new Tuple2<>(key, stateValue.count));
            isLatestTimer = true;
        }
        Long timerTimestamp = ctx.timestamp();
        Long watermark = ctx.timerService().currentWatermark();
        LOG.info("[Timer] Key: {}, Count: {}, LastModified: [{}|{}], TimerTimestamp: [{}|{}], Watermark: [{}|{}], IsLatestTimer: {}",
                key, stateValue.count,
                stateValue.lastModified, DateUtil.timeStamp2Date(stateValue.lastModified),
                timerTimestamp, DateUtil.timeStamp2Date(timerTimestamp),
                watermark, DateUtil.timeStamp2Date(watermark),
                isLatestTimer
        );
    }
}

/**
 * 存储在状态中的数据结构
 */
public static class MyEvent {
    public Long count;
    public Long lastModified;
}
```
> 完整代码请查阅:[KeyedProcessFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/function/KeyedProcessFunctionExample.java)

### 3. 定时器

> 定时器使用细节可以参阅：[Flink 定时器的4个特性](http://smartsi.club/4-characteristics-of-timers-in-apache-flink.html)

基于事件时间或者处理时间的 Timer 在内部由 TimerService 维护并排队执行。TimerService 只为同一个 Key 和时间戳保存一个 Timer，即每个 Key 在每个时间戳上最多有一个 Timer。如果为同一时间戳注册了多个 Timer，那么也只会调用一次 onTimer() 方法。

Flink同步调用 onTimer() 和 processElement() 方法。因此，用户不必担心状态的并发修改。Timer 具有容错能力，并且与应用程序的状态一起进行快照。如果故障恢复或从保存点启动应用程序，就会恢复 Timer。

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

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文:[Process Function (Low-level Operations)](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/dev/datastream/operators/process_function/)
