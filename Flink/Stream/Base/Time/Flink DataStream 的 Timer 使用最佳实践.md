
## 1. Timer 介绍

Timer 是 Flink 提供的定时器机制。通常，Flink 作业是事件驱动计算的，但在一些场景下，Flink 作业需要基于处理时间（ProcessingTime）或者事件时间（EventTime）驱动计算和发送数据，这时便需要使用 Timer。算子可以注册一个 Timer，当时间达到指定的处理时间，或事件时间水印（Watermark）达到指定的事件时间时，便会触发指定的计算逻辑。Flink 中的窗口便是基于 Timer 实现的。

多数情况下，这类需求可以使用 SQL 中的窗口满足。但有时，Flink 作业存在更加复杂且定制化的需求，这时可以考虑使用 DataStream API，利用其中的 Timer 机制实现。

## 2. Timer 使用方法

Flink 作业开发者可以在 KeyedStream 上使用 KeyedProcessFunction，或者在 ConnectedStream 上使用 KeyedCoProcessFunction，又或在 BroadcastConnectedStream 上使用 KeyedBroadcastProcessFunction。通过这些 Function 中提供的 TimerService 来使用 Timer。其中使用最多的是 KeyedProcessFunction。我们以此为例来介绍下如何使用 Timer。

KeyedProcessFunction 与 RichFlatMapFunction 非常相近，同样可以处理单条数据，输出0到任意多条数据，但 KeyedProcessFunction 只能在 KeyedStream 上使用，并提供了额外的 Timer 支持。

**重要**

由于 Timer 会使用 KeyedState 进行保存和恢复，因此只能在 KeyedProcessFunction 中使用 Timer，无法在 ProcessFunction 中使用。

```java
public abstract class KeyedProcessFunction<K, I, O> extends AbstractRichFunction {

    // 处理输入数据。
	public abstract void processElement(I value, Context ctx, Collector<O> out) throws Exception;

    // 当达到Timer指定时间时的回调。
	public void onTimer(long timestamp, OnTimerContext ctx, Collector<O> out) throws Exception {}

    // 处理数据中使用的Context，也是Timer回调中使用的Context的基类。
    public abstract class Context {

        // 当前处理的数据或Timer的时间戳。
        public abstract Long timestamp();

        // 获取TimerService以进行Timer注册或删除操作。
        public abstract TimerService timerService();

        // 将数据作为Side Output输出。
        public abstract <X> void output(OutputTag<X> outputTag, X value);

        // 获取当前处理的数据的Key。
        public abstract K getCurrentKey();
    }

    // Timer回调中使用的Context。
    public abstract class OnTimerContext extends Context {
        // 获取当前Timer的TimeDomain，即使用处理时间还是事件时间。
        public abstract TimeDomain timeDomain();

        // 获取当前Timer的Key。
        public abstract K getCurrentKey();
    }
}
```

KeyedProcessFunction.Context 提供了访问 TimerService 的途径，可以在处理数据或 Timer 时使用 TimerService 注册新的 Timer 或删除已有的 Timer。注册所使用的时间单位均为毫秒。

```java
public interface TimerService {

    // 获取当前的处理时间。
    long currentProcessingTime();

    // 获取当前的事件时间水印。
    long currentWatermark();

    // 注册指定处理时间的Timer。
    void registerProcessingTimeTimer(long time);

    // 注册指定事件时间的Timer。
    void registerEventTimeTimer(long time);

    // 删除指定处理时间的Timer。
    void deleteProcessingTimeTimer(long time);

    // 删除指定事件时间的Timer。
    void deleteEventTimeTimer(long time);
}
```

在 processElement 中注册 Timer 时，会使用当前处理的数据的Key，而在 onTimer 中注册 Timer 时会继承当前处理的 Timer 的 Key。同一个 Key 在同一个时间点只会有一个 Timer，因此也只会触发一次计算。不同的 Key 则会分别触发计算。注册的单个 Timer 均为一次性触发，如果需要实现周期性触发的逻辑，则需要在 onTimer 中注册下一个触发时间点的 Timer。

## 3. Timer 使用示例

如前面所说，Flink 的窗口就是使用 Timer 实现的。首先我们看一下基于事件时间窗口，每分钟对输入数值求和并输出的例子。在 DataStream API 中使用窗口的代码示例如下。
```java
DataStream<Tuple2<String, Long>> sum = inputs
        .keyBy(input->input.f0)
        .window(TumblingEventTimeWindows.of(Time.minutes(1)))
        .reduce(new SumReduceFunction());
```

我们可以尝试直接使用 KeyedProcessFunction 和 Timer 来实现类似的逻辑：
```java
DataStream<Tuple2<String, Long>> sum = inputs
    .keyBy(input -> input.f0)
    .process(new KeyedProcessFunction<String, Tuple2<String, Long>, Tuple2<String, Long>>() {
        // 记录窗口内总和的State。
        private ValueState<Long> sumState;

        @Override
        public void open(Configuration parameters) throws Exception {
            super.open(parameters);
            sumState = getRuntimeContext().getState(new ValueStateDescriptor<>("sum", Long.class));
        }

        @Override
        public void processElement(Tuple2<String, Long> value, Context ctx, Collector<Tuple2<String, Long>> out) throws Exception {
            if (sumState.value() == null) {
                // 当某个Key的数据第一次处理，或在Timer触发后第一次处理时，根据当前数据的事件时间，计算所属的时间窗口，注册窗口结束时刻的Timer。
                ctx.timerService().registerEventTimeTimer(getWindowStartWithOffset(ctx.timestamp(), 0, 60 * 1000) + 60 * 1000);
                sumState.update(value.f1);
            } else {
                // 否则进行累加。
                sumState.update(sumState.value() + value.f1);
            }
        }

        @Override
        public void onTimer(long timestamp, OnTimerContext ctx, Collector<Tuple2<String, Long>> out) throws Exception {
            // 输出此期间的总和，并清除累积值。
            out.collect(new Tuple2<>(ctx.getCurrentKey(), sumState.value()));
            sumState.clear();
        }

        // 该方法自TimeWindow.java中复制而来，用于计算给定时间戳所从属的窗口的起点。
        private long getWindowStartWithOffset(long timestamp, long offset, long windowSize) {
            final long remainder = (timestamp - offset) % windowSize;
            // handle both positive and negative cases
            if (remainder < 0) {
                return timestamp - (remainder + windowSize);
            } else {
                return timestamp - remainder;
            }
        }
    });
```

当一个Key首次有数据输入时，Function会计算当前数据的事件时间属于哪一个时间窗口，注册这个时间窗口结束时刻触发的Timer，并开始累加数据。事件时间水印达到指定时刻之后，Flink会调用onTimer，将累加值输出出去，并清除累加状态。此后这个Key再有新的数据输入时，会重复这个过程。

以上这两个实现的逻辑基本是相同的。可以发现如果Timer处理后，这个Key不再有数据输入，后续也不会再输出这个Key的数据。有时作业的逻辑已知输入Key是有限个，希望有一个Key输入一次后，无论后续是否还有数据，都以相同的事件时间周期输出周期内的累加值，可以将OnTimer的实现修改为：

```java
@Override
public void onTimer(long timestamp, OnTimerContext ctx, Collector<Tuple2<String, Long>> out) throws Exception {
    // 输出此期间的总和。
    out.collect(new Tuple2<>(ctx.getCurrentKey(), sumState.value()));
    // 重置但不清除累积值。
    sumState.update(0L);
    // 注册下一次输出累积值的Timer。该timestamp就是窗口结束时刻，下一个窗口可以直接加60s。
    ctx.timerService().registerEventTimeTimer(timestamp + 60 * 1000);
}
```

如此便可以使得`sumState.value()`在赋值一次后永远不为null，从而实现无论是否有数据，都会继续定期输出这个Key的累加值，无数据时会输出0。

**说明**

这里的输出周期是基于事件时间水印的事件时间周期。

如果想要基于处理时间而非事件时间进行聚合，则可以替换processElement中注册Timer和获取时间的逻辑，改为：

```
@Override
public void processElement(Tuple2<String, Long> value, Context ctx, Collector<Tuple2<String, Long>> out) throws Exception {
    if (sumState.value() == null) {
        // 根据当前的处理时间，计算所属的时间窗口，注册窗口结束时间的Timer。
        ctx.timerService().registerProcessingTimeTimer(getWindowStartWithOffset(ctx.timerService().currentProcessingTime(), 0, 60 * 1000) + 60 * 1000);
        sumState.update(value.f1);
    } else {
        sumState.update(sumState.value() + value.f1);
    }
}
```

当处理时间达到指定时间之后，便会调用对应的onTimer逻辑。基于以上类似的逻辑，修改State计算逻辑和输出数据的逻辑，可以实现其他类似的计算需求。

另一个单纯使用窗口不易实现而需要使用Timer实现的业务逻辑是心跳警告。当一个Key的输入一次后，如果一分钟内没有再输入新的数据，就发出一个告警消息。方便起见这里只使用Key作为输入，实现的代码如下。

```
DataStream<String> sum = inputs
    .keyBy(input->input)
    .process(new KeyedProcessFunction<String, String, String>() {
        // 记录此前的超时时间的State。
        private ValueState<Long> lastTimerState;

        @Override
        public void open(Configuration parameters) throws Exception {
            super.open(parameters);
            lastTimerState = getRuntimeContext().getState(new ValueStateDescriptor<>("timer", Long.class));
        }

        @Override
        public void processElement(String value, Context ctx, Collector<String> out) throws Exception {
            if (lastTimerState.value() != null) {
                // 清除此前注册的超时Timer。
                ctx.timerService().deleteProcessingTimeTimer(lastTimerState.value());
            }
            // 注册新的超时Timer，并记录在State中，用于后续清除。
            long timeout = ctx.timerService().currentProcessingTime() + 60 * 1000;
            ctx.timerService().registerProcessingTimeTimer(timeout);
            lastTimerState.update(timeout);
            // 输出正常数据。
            out.collect(value);
        }

        @Override
        public void onTimer(long timestamp, OnTimerContext ctx, Collector<String> out) throws Exception {
            // 进入此方法说明已超时，发送一个心跳超时警告的消息。也可以考虑使用SideOutput而非默认输出流进行输出。
            out.collect("Heartbeat timeout:" + ctx.getCurrentKey());
        });
```

## 4. Timer使用建议

-   大多数情况下窗口能够满足需求，建议优先使用窗口。

-   KeyedProcessFunction的processElement和onTimer方法不会被同时调用，因此不需要担心同步问题。但这也意味着处理onTimer逻辑是会阻塞处理数据的。

-   Flink没有提供查询Timer注册状态的API，因此如果预计需要进行Timer删除操作，Function需要自行记录已注册Timer的时间。

-   Timer会保存在Checkpoint中，当作业从Failover中恢复，或从Savepoint重新启动时，Timer也会被恢复。此时：

    -   已经到时间的处理时间Timer，会直接触发处理。因此作业启动后短时间内可能会触发大量的Timer进行数据处理和发送。

    -   事件时间Timer则会在收到对应时间的Watermark后触发处理。因此作业也有可能在启动后一段时间后，即事件时间水印更新后触发大量的Timer进行数据的处理和发送。

-   Timer与Key相关，在Checkpoint里会保存在KeyedState中，因此只能在KeyedStream，或者有Key的ConnectedStream或BroadcastConnectedStream上使用。无Key的流作业在需要使用Timer时，如果符合以下两种情况可以按相应的方法使用：

    -   如果Timer的逻辑与特定字段值无关，每条数据独立使用一个Timer，可以使用数据内的一个唯一ID（UUID）作为Key进行keyby。

        **重要**

        该字段需要存在于上游数据中，不可以是keyby方法中生成随机值。

    -   如果全局共享一个Timer，即全局进行聚合计算的情况，则可以使用一个常量作为Key进行keyby，并将并发设为1。


## 5. Timer使用注意事项

-   请尽量避免大量Timer同时触发的情况，例如数百万个Key的Timer都在整点触发。这种情况建议把触发时间打散到前后数分钟或更长的范围内。

-   请避免在processElement和onTimer中重复注册Timer，因为这会导致Timer数量急剧膨胀。

-   通常情况下Timer的开销是很小的，大量的Key注册Timer也没有问题。但仍然建议关注Checkpoint时间和内存状态。如果使用Timer后，Checkpoint时间或者内存使用量增加很多，超过可容忍范围，可能需要考虑优化逻辑，或使用其他方式实现。

-   如果在有限流上使用处理时间Timer需要注意，当数据处理结束时，未到时间的处理时间Timer将被忽略，这意味着数据可能会丢失。
