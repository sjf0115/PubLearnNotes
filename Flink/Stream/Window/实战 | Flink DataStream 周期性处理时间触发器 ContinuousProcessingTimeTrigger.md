在流处理中，窗口是处理无界流的核心抽象，而触发器（Trigger）则是决定"何时触发窗口计算"的指挥官。Flink 提供了丰富的内置触发器，其中 ContinuousProcessingTimeTrigger 是一个极具实用价值的触发器，它允许我们在窗口结束之前，以固定的时间间隔持续地输出窗口的中间结果。这对于需要低延迟感知、近乎实时监控业务指标的场景至关重要。

## 1. 介绍

在 ContinuousProcessingTimeTrigger 之前的 ProcessingTimeTrigger，只有当系统时间超过窗口结束时间时才会触发窗口计算。对于短窗口(秒级窗口或者分钟窗口)，由于其窗口期较短，不用等待太久很快就能获取到结果。但是对于长窗口(如小时窗口或天窗口)，这意味着用户需要等待很长时间才能看到结果。

这种设计的初衷是保证结果的准确性和最终一致性。窗口会持续收集数据，直到系统时间到达表明该窗口的所有数据都已到达，这时才会触发计算并输出一个最终的、准确的结果。然而，在许多实际的业务场景中，这种只输出一次最终结果的模式并不理想：
- 用户体验差：一个运营仪表盘如果每天只在午夜过后才更新一次日活数据，那么其价值将大打折扣。业务方希望看到的是随时间推移、逐步逼近最终结果的趋势。
- 故障排查与实时监控：如果处理逻辑有 Bug，或者数据流出现异常（如某个数据源停止发送数据），使用 ProcessingTimeTrigger 你需要等到窗口结束才能发现问题，为时已晚。你需要更早地看到中间状态以便及时干预。

ContinuousProcessingTimeTrigger 通过定期触发窗口计算来解决这个问题。在窗口结束之前，以可配置的固定时间间隔提前触发窗口计算，输出当前的中间结果，同时在窗口结束时依然输出一个最终结果。

## 2. 与 ProcessingTimeTrigger 的异同点

| 特性     | ProcessingTimeTrigger | ContinuousProcessingTimeTrigger |
| :------------- | :------------- | :------------- |
| 设计目标 | 保证最终输出的准确性 | 在准确性和低延迟之间取得平衡 |
| 触发时机 | 仅一次：当 Watermark 超过窗口结束时间时触发 | 多次：当 Watermark 超过窗口结束时间时触发；以固定间隔（如每10秒钟）触发 |
| 输出性质 | 仅输出一个最终的、完整的结果 | 输出一系列中间的、近似的结果；最后输出一个最终的、完整的结果 |
| 延迟 | 高，必须等待窗口结束和 Watermark 推进 | 低，可以很快地看到初步结果，延迟取决于配置的间隔 |
| 适用场景 | 对延迟不敏感但对准确性要求极高的场景，如离线报表、日终结算。| 对延迟敏感，需要早期预览或增量更新的场景，如实时监控仪表盘、实时推荐系统。|

最核心的区别就是触发机制与输出性质：
- EventTimeTrigger 的行为像一个"期末考试"：学生整个学期都在学习（窗口收集数据），但只在期末进行一次考试并给出最终成绩（触发计算输出结果）。
- ContinuousEventTimeTrigger 的行为像"随堂小测 + 期末考试"：学生不仅期末要考试，平时还会进行多次随堂小测。每次小测都反映了学生当前的学习水平（中间近似结果），而期末考试则是最终的综合评定（最终准确结果）。

## 3. 实践

下面我们以一个具体的示例来演示 ContinuousProcessingTimeTrigger 如何使用，如下所示计算每一分钟内每个单词的出现次数，并且要求每10秒输出一次结果：
```java
// 随机生成单词
DataStream<WordCount> words = env.addSource(new WordCountMockSource(1, 35),"words");

// 滚动窗口 统计每分钟每个单词的个数，每10秒输出一次结果
DataStream<WordCount> result = words
        // 根据单词分组
        .keyBy(new KeySelector<WordCount, String>() {
            @Override
            public String getKey(WordCount wc) throws Exception {
                return wc.getWord();
            }
        })
        // 处理时间滚动窗口 窗口大小1分钟
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
        // 周期性处理时间触发器 每10秒触发一次计算
        .trigger(ContinuousProcessingTimeTrigger.of(Time.seconds(10)))
        // 求和
        .reduce(new ReduceFunction<WordCount>() {
            @Override
            public WordCount reduce(WordCount wc1, WordCount wc2) throws Exception {
                long count = wc1.getFrequency() + wc2.getFrequency();
                LOG.info("word: {}, count: {}", wc1.getWord(), count);
                return new WordCount(wc1.getWord(), count);
            }
        });
```
> 完整底代码请查阅：[]()

## 4. 深度解析

ContinuousProcessingTimeTrigger 框架如下所示：
```java
public class ContinuousProcessingTimeTrigger<W extends Window> extends Trigger<Object, W> {
    private static final long serialVersionUID = 1L;
    private final long interval;
    private final ReducingStateDescriptor<Long> stateDesc;

    private ContinuousProcessingTimeTrigger(long interval) {

    }

    public TriggerResult onElement(Object element, long timestamp, W window, Trigger.TriggerContext ctx) throws Exception {

    }

    public TriggerResult onEventTime(long time, W window, Trigger.TriggerContext ctx) throws Exception {

    }

    public TriggerResult onProcessingTime(long time, W window, Trigger.TriggerContext ctx) throws Exception {

    }

    public void clear(W window, Trigger.TriggerContext ctx) throws Exception {

    }

    public boolean canMerge() {

    }

    public void onMerge(W window, Trigger.OnMergeContext ctx) throws Exception {

    }

    private void registerNextFireTimestamp(long time, W window, Trigger.TriggerContext ctx, ReducingState<Long> fireTimestampState) throws Exception {

    }

    private static class Min implements ReduceFunction<Long> {

    }
}
```
核心是 onElement 和 onProcessingTime 方法。下面详细介绍 ContinuousProcessingTimeTrigger 的每一部分构成。

### 4.1 状态管理

ContinuousProcessingTimeTrigger 使用 ReducingState 来存储下一次应该触发的时间戳(通过 ReduceFunction 保存最小的时间戳)。这种设计具有以下优点：
- 容错性: 状态由 Flink 状态后端管理，支持精确一次语义
- 高效性: 只需要存储一个长整型数值，开销很小
- 一致性: 即使发生故障恢复，触发时间也能保持正确

```java
private final ReducingStateDescriptor<Long> stateDesc;

private ContinuousProcessingTimeTrigger(long interval) {
    this.stateDesc = new ReducingStateDescriptor("fire-time", new Min(), LongSerializer.INSTANCE);
    this.interval = interval;
}

private static class Min implements ReduceFunction<Long> {
    private static final long serialVersionUID = 1L;

    private Min() {
    }

    public Long reduce(Long value1, Long value2) throws Exception {
        return Math.min(value1, value2);
    }
}
```

### 4.2 元素到达处理 onElement

每个元素到达时都会进行一些判断与处理：
- 第一个元素进入窗口时(周期性定时器状态 ReducingState 为空)，则为窗口注册起始周期性处理时间定时器
  - 定时器的时间戳是窗口的结束时间 `window.maxTimestamp()` 与 `窗口开始时间 + 窗口周期触发间隔` 的最小值

```java
public TriggerResult onElement(Object element, long timestamp, W window, Trigger.TriggerContext ctx) throws Exception {
    ReducingState<Long> fireTimestampState = (ReducingState)ctx.getPartitionedState(this.stateDesc);
    timestamp = ctx.getCurrentProcessingTime();
    // 为窗口注册起始周期性事件时间定时器
    if (fireTimestampState.get() == null) {
        this.registerNextFireTimestamp(timestamp - timestamp % this.interval, window, ctx, fireTimestampState);
    }
    return TriggerResult.CONTINUE;
}

// 注册处理时间定时器
private void registerNextFireTimestamp(long time, W window, Trigger.TriggerContext ctx, ReducingState<Long> fireTimestampState) throws Exception {
    long nextFireTimestamp = Math.min(time + this.interval, window.maxTimestamp());
    fireTimestampState.add(nextFireTimestamp);
    ctx.registerProcessingTimeTimer(nextFireTimestamp);
}
```

### 4.3 定时器触发 onProcessingTime

定时器触发时会调用 onProcessingTime 方法，只有当系统时间到达周期触发时间或者到达窗口结束时间时才会触发：
- 窗口结束触发：当系统时间到达窗口结束时间时，只触发窗口计算
  - 如果定时器触发的时间等于窗口的结束时间
- 周期性触发：当事件时间到达周期触发时间时，触发窗口计算，并注册下一个周期的事件时间定时器
  - 如果定时器触发的时间等于状态中保存的定时器时间
```java
public TriggerResult onProcessingTime(long time, W window, Trigger.TriggerContext ctx) throws Exception {
    ReducingState<Long> fireTimestampState = (ReducingState)ctx.getPartitionedState(this.stateDesc);
    if (((Long)fireTimestampState.get()).equals(time)) {
        fireTimestampState.clear();
        this.registerNextFireTimestamp(time, window, ctx, fireTimestampState);
        return TriggerResult.FIRE;
    } else {
        return TriggerResult.CONTINUE;
    }
}
```

处理时间触发器只关心处理时间，不关心事件时间：
```java
public TriggerResult onEventTime(long time, W window, Trigger.TriggerContext ctx) throws Exception {
    return TriggerResult.CONTINUE;
}
```

### 问题

在这个方法中核心是判断要不要触发窗口计算以及注册下一个时间点的处理时间定时器。在这里计算下一次定时器触发时间只是简单的的使用当前处理时间加上周期间隔。前几个触发周期都可以正常输出数据，但问题是原本在处理时间到达窗口结束时间触发的窗口计算没有触发。例如，如下滚动窗口大小为1分钟，使用周期性处理时间触发器，每 10s 触发一次计算：
```java
// 处理时间滚动窗口 滚动大小60s
.window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
// 周期性处理时间触发器 每10s触发一次计算
.trigger(CustomContinuousProcessingTimeTrigger.of(Time.seconds(10)))
```

上述代码可以正确计算 `0-10s`、`10-20s`、`20-30s`、`30-40s`、`40-50s` 的触发周期，但是丢失了 `50-60s` 区间到达的数据。

这一问题在 Flink 1.13.6 版本已经得到修复，具体可以查阅[FLINK-20443](https://issues.apache.org/jira/browse/FLINK-20443)。下面具体看一下是如何修复的：
```java
public TriggerResult onProcessingTime(long time, W window, TriggerContext ctx) throws Exception {
    ReducingState<Long> fireTimestampState = ctx.getPartitionedState(stateDesc);
    if (fireTimestampState.get().equals(time)) {
        fireTimestampState.clear();
        registerNextFireTimestamp(time, window, ctx, fireTimestampState);
        return TriggerResult.FIRE;
    }
    return TriggerResult.CONTINUE;
}

private void registerNextFireTimestamp(long time, W window, TriggerContext ctx, ReducingState<Long> fireTimestampState) throws Exception {
    // 在这个地方做了优化
    long nextFireTimestamp = Math.min(time + interval, window.maxTimestamp());
    fireTimestampState.add(nextFireTimestamp);
    ctx.registerProcessingTimeTimer(nextFireTimestamp);
}
```
在新版本中注册定时器抽象出 registerNextFireTimestamp 方法，核心点是修改了下一次定时器触发时间的判断逻辑。旧版本只是简单的使用当前处理时间加上周期间隔，现在优化为取当前处理时间加上周期间隔和窗口结束的最大时间戳的最小值，保证到达窗口结束时间时一定会触发计算。



...
