---
layout: post
author: sjf0115
title: Flink 处理函数 ProcessFunction 和 KeyedProcessFunction
date: 2021-06-14 20:17:21
tags:
  - Flink

categories: Flink
permalink: how-to-user-process-function-of-flink
---

## 1. 处理函数

在学习 ProcessFunction 之前，我们先来回顾一下 Flink 的[抽象级别](http://smartsi.club/flink-programming-model.html)。Flink 为我们提供了不同级别的抽象层次来开发流处理和批处理应用程序：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-programming-model-1.png?raw=true)

在最底层有状态流处理中没有定义任何具体的算子（比如 map，filter，或者 window），而是提供一个统一的处理操作。它是所有转换算子的一个概括性的表达，可以自定义处理逻辑，所以这一层接口就被叫作处理函数。

我们之前学习的转换算子，一般只是针对某种具体操作来定义的，能够拿到的信息比较有限。比如 map 算子，我们实现的 MapFunction 中，只能获取到当前的数据，定义它转换之后的形式；而像窗口聚合这样的复杂操作，AggregateFunction 中除数据外，还可以获取到当前的状态（以累加器 Accumulator 形式出现）。但是无论哪种算子，如果我们想要访问事件的时间戳，或者当前的 Watermark 信息，一般很难做到。跟时间相关的操作，目前我们一般会用窗口来处理。而在很多应用需求中，要求我们对时间有更精细的控制，需要能够获取 Watermark，甚至要把控时间、定义什么时候做什么事，这就不是基本的时间窗口能够实现的了。这时候就需要使用处理函数了。处理函数提供了一个定时服务 TimerService，可以通过它访问数据流中的事件、时间戳、Watermark，甚至可以注册定时器。而且处理函数继承了 AbstractRichFunction 抽象类，所以拥有富函数类的所有特性，即可以访问状态以及其他运行时信息。此外，处理函数还可以直接将数据输出到侧输出流（side output）中。

在处理函数中，我们直面的就是数据流中最基本的元素：数据事件、状态以及时间(定时器)。这就相当于对流有了完全的控制权。处理函数可以让用户轻松的处理来自一个或多个数据流的事件，并可以使用一致性容错状态。另外，用户可以注册事件时间或者处理时间的回调函数以实现复杂的计算。所以，处理函数是最为灵活的处理方法，可以实现各种自定义的业务逻辑；处理函数比较抽象，没有具体的操作，所以对于一些常见的简单应用（比如求和、开窗口）会显得有些麻烦；不过正是因为它不限定具体做什么，所以理论上我们可以做任何事情，实现所有需求。

## 2. 处理函数分类

Flink 中的处理函数其实是一个大家族，我们平时常见的 ProcessFunction 只是其中一员。DataStream 在调用一些转换方法之后，有可能生成新的流类型；例如调用 keyBy() 之后得到 KeyedStream，进而再调用 window() 之后得到 WindowedStream。对于不同类型的流，其实都可以直接调用 process() 方法进行自定义处理，这时传入的参数就都叫作处理函数。尽管本质相同，都可以访问状态和时间信息，但彼此之间还是会有一些差异。Flink 为我们提供了如下几个不同的处理函数：
- ProcessFunction：最基本的处理函数，基于 DataStream 直接调用 process() 时作为参数传入。
- KeyedProcessFunction：对流按键分区后的处理函数，基于 KeyedStream 调用 process() 时作为参数传入。
- ProcessWindowFunction：开窗之后的处理函数，也是全窗口函数的代表。基于 WindowedStream 调用 process() 时作为参数传入。
- ProcessAllWindowFunction：同样是开窗之后的处理函数，基于 AllWindowedStream 调用 process() 时作为参数传入。
- CoProcessFunction：合并两条流之后的处理函数，基于 ConnectedStreams 调用 process() 时作为参数传入。
- KeyedCoProcessFunction：合并两条流之后的处理函数，同样是基于 ConnectedStreams 调用 process() 时作为参数传入。不同的是合并的两条 KeyedStream 流。
- ProcessJoinFunction：间隔连接（interval join）两条流之后的处理函数，基于 IntervalJoined 调用 process() 时作为参数传入。
- BroadcastProcessFunction：广播连接流处理函数，基于 BroadcastConnectedStream 调用 process() 时作为参数传入。
- KeyedBroadcastProcessFunction：按键分区的广播连接流处理函数，同样是基于 BroadcastConnectedStream 调用 process() 时作为参数传入。与 BroadcastProcessFunction 不同的是，这时的广播连接流，是一个 KeyedStream与广播流（BroadcastStream）做连接之后的产物。

## 3. ProcessFunction 和 KeyedProcessFunction

接下来，我们就对 ProcessFunction 和 KeyedProcessFunction 展开详细说明，两者具体关系图如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/how-to-user-process-function-of-flink-1.png?raw=true)

从上图中可以看出 ProcessFunction 既可以作用于 DataStream 上，也可以作用于 KeyedStream 上。如果作用于 DataStream 上，只能访问数据流元素(事件)，不能访问状态，也不支持注册定时器。ProcessFunction 也可以作用于 KeyedStream 上，只不过已经被标记 @Deprecated，建议在 KeyedStream 上使用 KeyedProcessFunction。

DataStream 与 KeyedStreamd 都有 process 方法，DataStream 接收的是 ProcessFunction，而 KeyedStream 接收的是 KeyedProcessFunction(较早版本也支持 ProcessFunction，现在已被废弃)：
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

### 3.1 ProcessFunction

ProcessFunction 抽象类继承了 AbstractRichFunction，有两个泛型类型参数：I 表示 Input，也就是输入的数据类型；O 表示 Output，也就是处理完成之后输出的数据类型。ProcessFunction 定义了两个方法：一个是必须要实现的抽象方法 processElement，另一个是非抽象方法 onTimer：
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

对于输入数据流中的每一个元素都会调用一次 processElement 方法，从而输出零个或多个元素。通过该方法可以实现状态的更新，也可以通过 Context 对象注册基于事件时间或者处理时间的定时器，并在未来某一时间调用 onTimer 回调函数。参数包括三个：输入数据值 value，上下文 ctx，以及 Collector 收集器 out。方法没有返回值，处理之后的数据通过收集器 out 来输出。这三个参数中最需要关注的是当前运行的上下文 ctx，是 ProcessFunction 中定义的内部抽象类 Context，可以获取到当前的时间戳，也可以获取 TimeService 来查询当前时间或者注册定时器，以及可以将数据发送到侧输出流（side output）的方法 output。

通过几个参数的分析不难发现，ProcessFunction 可以轻松实现 flatMap 这样的基本转换功能（当然 map、filter 更不在话下）；而通过富函数提供的获取上下文方法 getRuntimeContext() 也可以自定义状态进行处理，这也就能实现聚合操作的功能了。

另外一个方法 onTimer 用来定义定时器触发时的回调操作，这是一个非常强大、也非常有趣的功能。由于定时器只能在 KeyedStream 上使用，所以会到 KeyedProcessFunction 章节具体展示说明。如果在非 KeyedStream 上注册定时器，会抛出如下异常：
```java
Caused by: java.lang.UnsupportedOperationException: Setting timers is only supported on a keyed streams.
```

下面是一个具体的应用示例：
```java
// 输入源 <message, timestamp>
DataStream<String> source = env.socketTextStream("localhost", 9100, "\n");
DataStream<Tuple2<String, Long>> stream = source.map(new MapFunction<String, Tuple2<String, Long>>() {
    @Override
    public Tuple2<String, Long> map(String str) throws Exception {
        String[] params = str.split(",");
        String message = params[0];
        Long timestamp = Long.parseLong(params[1]);
        LOG.info("输入元素 message: {}, timestamp: {}",  message, timestamp);
        return Tuple2.of(message, timestamp);
    }
});

// 逻辑处理
SingleOutputStreamOperator<Tuple2<String, Long>> processStream = stream
        // 如果使用事件时间必须设置Timestamp提取和Watermark生成 否则下游 ctx.timestamp() 为null
        .assignTimestampsAndWatermarks(
                WatermarkStrategy.<Tuple2<String, Long>>forBoundedOutOfOrderness(Duration.ofSeconds(10))
                        .withTimestampAssigner(new SerializableTimestampAssigner<Tuple2<String, Long>>() {
                            @Override
                            public long extractTimestamp(Tuple2<String, Long> element, long recordTimestamp) {
                                return element.f1;
                            }
                        })
        )
        // 数据处理 包含错误信息的元素输出到侧输出流中
        .process(new ProcessFunction<Tuple2<String, Long>, Tuple2<String, Long>>() {
            @Override
            public void processElement(Tuple2<String, Long> element, Context ctx, Collector<Tuple2<String, Long>> out) throws Exception {
                String message = element.f0;
                // Watermark
                Long watermark = ctx.timerService().currentWatermark();
                // 元素事件时间戳
                Long timestamp = ctx.timestamp();
                // 包含错误信息
                if (message.contains("error")) {
                    // 侧输出
                    ctx.output(errorOutputTag, element);
                } else {
                    // 主输出
                    out.collect(element);
                }
                LOG.info("元素处理 key: {}, timestamp: {}, watermark: {}", message, timestamp, watermark);
            }
        });

// 输出
processStream.print("MAIN");
processStream.getSideOutput(errorOutputTag).print("ERROR");
```

> 完整代码请查阅:[ProcessFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/function/process/ProcessFunctionExample.java)

这里我们在 ProcessFunction 中重写了 processElement 方法，自定义了一种处理逻辑：当数据元组的第一个字段包含 'error' 时，将其输出到侧输出流中，否则继续保留在主数据流中。主数据流中的输出是通过调用 out.collect 来实现的，侧输出流中的输出是通过调用 ctx.output 方法实现的。另外我们还通过调用
ctx.timerService().currentWatermark() 和 ctx.timestamp() 来获取当前的 Watermark 和元素的事件时间戳。

### 3.2 KeyedProcessFunction

在 Flink 程序中，为了实现数据的聚合统计，或者开窗计算之类的功能，我们一般都要先用 keyBy 算子对数据流进行按键分区，得到一个 KeyedStream。代码中更加常见的处理函数是 KeyedProcessFunction，最基本的 ProcessFunction 反而使用的没那么多。

KeyedProcessFunction 跟 ProcessFunction 抽象类一样，都是继承了 AbstractRichFunction。可以看到与 ProcessFunction 的定义几乎完全一样，区别只是在于类型参数多了一个 K，表示当前按键分区 key 的类型。同样地，我们必须实现一个 processElement 抽象方法，用
来处理流中的每一个数据；另外还有一个非抽象方法 onTimer 用来定义定时器触发时的回调操作：
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

在 ProcessFunction 章节中更多介绍的是 processElement，KeyedProcessFunction 的 processElement 并无差异，在这就不再赘述。KeyedProcessFunction 的一个特色，就是可以灵活地使用定时器。定时器是处理函数中进行时间相关操作的主要机制。onTimer 方法用于定义定时触发的操作，这个方法只有在注册的定时器触发的时候才会被调用。打个比方，注册定时器就是设定了一个闹钟，到了设定时间就会响；而 onTimer 中定义的就是闹钟响的时候要做的事。所以它本质上是一个基于时间的回调方法，通过时间的进展来触发，具体取决于使用处理时间还是事件时间来注册定时器：
- 使用处理时间注册定时器时，当服务器的系统时间到达定时器的时间戳时，就会调用 onTimer() 方法。
- 使用事件时间注册定时器时，当算子的 Watermark 到达或超过定时器的时间戳时，就会调用 onTimer() 方法。

与 processElement 类似，定时方法 onTimer 也有三个参数：时间戳 timestamp，上下文 ctx 以及收集器 out。这里的 timestamp 是指设定好的触发时间，事件时间语义下当然就是 Watermark 了。另外这里同样有上下文和收集器，所以也可以调用定时服务（TimerService），
以及任意输出处理之后的数据。

> Timer 的具体使用细节可以参阅 [Flink 定时器的 4 个特性](https://smartsi.blog.csdn.net/article/details/126714638)

KeyedProcessFunction 是处理函数中的使用最频繁的一个函数，可以认为是 ProcessFunction 的一个扩展。我们只要基于 keyBy 之后的 KeyedStream，直接调用 process 方法即可，这时需要传入的参数就是 KeyedProcessFunction 的实现类：
```java
stream.keyBy(xxx)
      .process(new CounterKeyedProcessFunction());
```

下面是一个使用事件时间定时器的具体示例。在以下示例中，KeyedProcessFunction 为每个 Key 维护一个计数器，并会把最近 10s (事件时间)内没有更新的结果输出：
```java
// 输入源
DataStream<String> source = env.socketTextStream("localhost", 9100, "\n");
DataStream<Tuple2<String, Long>> stream = source.map(new MapFunction<String, Tuple2<String, Long>>() {
    @Override
    public Tuple2<String, Long> map(String str) throws Exception {
        String[] params = str.split(",");
        String key = params[0];
        Long timestamp = Long.parseLong(params[1]);
        LOG.info("输入元素 key: {}, timestamp: {}",  key, timestamp);
        return Tuple2.of(key, timestamp);
    }
});

// 逻辑处理
DataStream<Tuple2<String, Long>> result = stream
        // 如果使用事件时间必须设置Timestamp提取和Watermark生成 否则下游 ctx.timestamp() 为null
        .assignTimestampsAndWatermarks(
                WatermarkStrategy.<Tuple2<String, Long>>forBoundedOutOfOrderness(Duration.ofSeconds(10))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple2<String, Long>>() {
                    @Override
                    public long extractTimestamp(Tuple2<String, Long> element, long recordTimestamp) {
                        return element.f1;
                    }
                })
        )
        .keyBy(new KeySelector<Tuple2<String,Long>, String>() {
            @Override
            public String getKey(Tuple2<String, Long> tuple) throws Exception {
                return tuple.f0;
            }
        })
        .process(new CounterKeyedProcessFunction());

// KeyedProcessFunction 具体实现
private static class CounterKeyedProcessFunction extends KeyedProcessFunction<String, Tuple2<String, Long>, Tuple2<String, Long>> {
        // 状态
        private ValueState<EventState> state;
        @Override
        public void open(Configuration parameters) throws Exception {
            // 状态描述符
            ValueStateDescriptor<EventState> stateDescriptor = new ValueStateDescriptor<>("KeyedProcessFunctionState", EventState.class);
            // 状态
            state = getRuntimeContext().getState(stateDescriptor);
        }

        @Override
        public void processElement(Tuple2<String, Long> value, Context ctx, Collector<Tuple2<String, Long>> out) throws Exception {
            // 当前状态值
            EventState eventState = state.value();
            if (eventState == null) {
                eventState = new EventState();
                eventState.count = 0L;
                eventState.lastModified = Long.MIN_VALUE;
            }
            // 更新值
            eventState.count++;
            if (eventState.lastModified < ctx.timestamp()) {
                eventState.lastModified = ctx.timestamp();
            }
            // 更新状态
            state.update(eventState);

            String key = ctx.getCurrentKey();
            // 获取Watermark时间戳
            long watermark = ctx.timerService().currentWatermark();
            LOG.info("状态更新 key: {}, count: {}, lastModified: {}, Watermark: {}",
                    key, eventState.count, eventState.lastModified, watermark
            );

            // 注册事件时间定时器 10s 后触发
            Long registerEventTime = eventState.lastModified + 10*1000;
            ctx.timerService().registerEventTimeTimer(registerEventTime);
            LOG.info("注册事件时间定时器 key: {}, timer: {}", key, registerEventTime);
        }

        @Override
        public void onTimer(long timestamp, OnTimerContext ctx, Collector<Tuple2<String, Long>> out) throws Exception {
            // timestamp 定时的事件时间
            // Key
            String key = ctx.getCurrentKey();
            // Watermark
            Long watermark = ctx.timerService().currentWatermark();
            // 检查这是一个过时的定时器还是最新的定时器
            EventState eventState = state.value();
            Long registerEventTime = eventState.lastModified + 10*1000; // 注册的事件时间定时器时间
            if (timestamp == registerEventTime) {
                // 最新注册的定时器 10s内没有更新输出当前值
                out.collect(Tuple2.of(key, eventState.count));
                LOG.info("最新定时器触发并输出 key: {}, count: {}, lastModified: {}, timer: {}, watermark: {}",
                        key, eventState.count, eventState.lastModified, timestamp, watermark
                );
            } else {
                // 过时的定时器
                LOG.info("过时定时器只触发不输出 key: {}, count: {}, lastModified: {}, timer: {}, watermark: {}",
                        key, eventState.count, eventState.lastModified, timestamp, watermark
                );
            }
        }
    }

    /**
     * 存储在状态中的数据结构
     */
    public static class EventState {
        public Long count;
        public Long lastModified;
    }
```
> 这个简单的例子可以用会话窗口实现。在这里使用 KeyedProcessFunction 只是用来说明它的基本模式。

> 完整代码请查阅:[KeyedProcessFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/function/process/KeyedProcessFunctionExample.java)

在上面代码中，由于定时器只能在 KeyedStream 上使用，所以先要进行 keyBy。之后我们自定义了一个 KeyedProcessFunction，其中 processElement 方法是每来一个数据都会调用一次，在这个方法主要完成计数器累加并定义一个 10 秒之后的定时器（基于事件时间）。而 onTimer 方法则会在定时器触发时调用，如果是最新的定时器，即 10s 内没有更新则输出当前值；如果是过时的定时器不做任何输出。

假设我们输入数据如下所示：
```
a,1663071788000  -- 2022-09-13 20:23:08
a,1663071792000  -- 2022-09-13 20:23:12
a,1663071790000  -- 2022-09-13 20:23:10
b,1663071803000  -- 2022-09-13 20:23:23
c,1663071814000  -- 2022-09-13 20:23:34
a,1663071825000  -- 2022-09-13 20:23:45
b,1663071839000  -- 2022-09-13 20:23:59
b,1663071901000  -- 2022-09-13 20:25:01
```
> -- 后面的为对应时间戳的时间，不作为输入

实际效果如下：
```
17:43:01,618 Stream [] - 输入元素 key: a, timestamp: 1663071788000
17:43:01,640 Stream [] - 状态更新 key: a, count: 1, lastModified: 1663071788000, Watermark: -9223372036854775808
17:43:01,641 Stream [] - 注册事件时间定时器 key: a, timer: 1663071798000
17:43:32,496 Stream [] - 输入元素 key: a, timestamp: 1663071792000
17:43:32,572 Stream [] - 状态更新 key: a, count: 2, lastModified: 1663071792000, Watermark: 1663071777999
17:43:32,573 Stream [] - 注册事件时间定时器 key: a, timer: 1663071802000
17:43:39,520 Stream [] - 输入元素 key: a, timestamp: 1663071790000
17:43:39,620 Stream [] - 状态更新 key: a, count: 3, lastModified: 1663071792000, Watermark: 1663071781999
17:43:39,620 Stream [] - 注册事件时间定时器 key: a, timer: 1663071802000
17:43:45,104 Stream [] - 输入元素 key: b, timestamp: 1663071803000
17:43:45,193 Stream [] - 状态更新 key: b, count: 1, lastModified: 1663071803000, Watermark: 1663071781999
17:43:45,193 Stream [] - 注册事件时间定时器 key: b, timer: 1663071813000
17:43:52,672 Stream [] - 输入元素 key: c, timestamp: 1663071814000
17:43:52,735 Stream [] - 状态更新 key: c, count: 1, lastModified: 1663071814000, Watermark: 1663071792999
17:43:52,735 Stream [] - 注册事件时间定时器 key: c, timer: 1663071824000
17:43:52,838 Stream [] - 过时定时器只触发不输出 key: a, count: 3, lastModified: 1663071792000, timer: 1663071798000, watermark: 1663071803999
(a,3)
17:43:52,839 Stream [] - 最新定时器触发并输出 key: a, count: 3, lastModified: 1663071792000, timer: 1663071802000, watermark: 1663071803999
17:43:59,888 Stream [] - 输入元素 key: a, timestamp: 1663071825000
17:43:59,983 Stream [] - 状态更新 key: a, count: 4, lastModified: 1663071825000, Watermark: 1663071803999
17:43:59,983 Stream [] - 注册事件时间定时器 key: a, timer: 1663071835000
(b,1)
17:43:59,983 Stream [] - 最新定时器触发并输出 key: b, count: 1, lastModified: 1663071803000, timer: 1663071813000, watermark: 1663071814999
17:44:05,553 Stream [] - 输入元素 key: b, timestamp: 1663071839000
17:44:05,567 Stream [] - 状态更新 key: b, count: 2, lastModified: 1663071839000, Watermark: 1663071814999
17:44:05,567 Stream [] - 注册事件时间定时器 key: b, timer: 1663071849000
(c,1)
17:44:05,671 Stream [] - 最新定时器触发并输出 key: c, count: 1, lastModified: 1663071814000, timer: 1663071824000, watermark: 1663071828999
17:44:13,073 Stream [] - 输入元素 key: b, timestamp: 1663071901000
17:44:13,126 Stream [] - 状态更新 key: b, count: 3, lastModified: 1663071901000, Watermark: 1663071828999
17:44:13,127 Stream [] - 注册事件时间定时器 key: b, timer: 1663071911000
(a,4)
17:44:13,231 Stream [] - 最新定时器触发并输出 key: a, count: 4, lastModified: 1663071825000, timer: 1663071835000, watermark: 1663071890999
17:44:13,231 Stream [] - 过时定时器只触发不输出 key: b, count: 3, lastModified: 1663071901000, timer: 1663071849000, watermark: 1663071890999
```
我们可以发现，数据到来之后，当前的 Watermark 与时间戳并不是一致的。当第一条数据到来，时间戳为 1663071788000，由于 Watermark 的生成是周期性的（默认 200ms 一次），不会立即发生改变，所以依然是最小值 Long.MIN_VALUE。随后只要到了 Watermark 生成的时间点（200ms 到了），就会依据当前的最大时间戳 1663071788000 来生成 Watermark 了。这里我们设置最大乱序时间为 10 秒，减去默认的 1 毫秒，所以 Watermark 推进到了 1663071777999 (1663071788000 - 10*1000 - 1)。而当时间戳为 1663071792000 的第二条数据到来之后，Watermark 同样没有立即改变，仍然是 1663071777999，就好像总是'滞后'数据一样。

这样程序的行为就可以得到合理解释了。事件时间语义下，定时器触发的条件就是 Watermark 推进到设定的时间。第一条数据到来后，设定的定时器时间为 1663071788000 + 10*1000 = 1663071798000；而当时间戳为 1663071792000 的第二条数据到来，Watermark 还处在 1663071777999 的位置，不会立即触发定时器；而之后 Watermark 会推进到 1663071781999，同样是无法触发定时器的。必须等到第五条数据到达后，将 Watermark 真正推进到 1663071803999，就可以触发定时器了。此时触发了两个定时器，一个是第一条数据设定的 1663071798000 定时器，一个是第二条和第三条重复设置的 1663071802000 定时器（重复只设置一个）。第二个触发的定时器表示元素在 10s 内没有更新需要输出。
