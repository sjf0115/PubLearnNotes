在流处理中，窗口是处理无界流的核心抽象，而触发器（Trigger）则是决定"何时触发窗口计算"的指挥官。Flink 提供了丰富的内置触发器，其中 ContinuousEventTimeTrigger 是一个极具实用价值的触发器，它允许我们在窗口结束之前，以固定的时间间隔持续地输出窗口的中间结果。这对于需要低延迟感知、近乎实时监控业务指标的场景至关重要。

## 1. 介绍

在 ContinuousEventTimeTrigger 出现之前只有 EventTimeTrigger。EventTimeTrigger 当 Watermark 超过窗口结束时间时才触发计算窗口计算。对于短窗口(秒级窗口或者分钟窗口)，由于其窗口期较短，不用等待太久就很快能获取到结果。但是对于长窗口(如小时窗口或天窗口)，这意味着用户需要等待很长时间才能看到结果。

这种设计的初衷是保证结果的准确性和最终一致性。窗口会持续收集数据，直到 Watermark 表明该窗口的所有（或绝大多数）数据都已到达，这时才会触发计算并输出一个最终的、准确的结果。

然而，在许多实际的业务场景中，这种只输出一次最终结果的模式并不理想：
- 用户体验差：一个运营仪表盘如果每天只在午夜过后才更新一次日活数据，那么其价值将大打折扣。业务方希望看到的是随时间推移、逐步逼近最终结果的趋势。
- 故障排查与实时监控：如果处理逻辑有 Bug，或者数据流出现异常（如某个数据源停止发送数据），使用 EventTimeTrigger 你需要等到窗口结束才能发现问题，为时已晚。你需要更早地看到中间状态以便及时干预。

ContinuousEventTimeTrigger 通过定期触发窗口计算来解决这个问题。在窗口结束之前，以可配置的固定时间间隔提前触发窗口计算，输出当前的中间结果，同时在窗口结束时依然输出一个最终结果。

## 2. 与 EventTimeTrigger 的异同点

| 特性     | EventTimeTrigger | ContinuousEventTimeTrigger |
| :------------- | :------------- | :------------- |
| 设计目标 | 保证最终输出的准确性 | 在准确性和低延迟之间取得平衡 |
| 触发时机 | 仅一次：当 Watermark 超过窗口结束时间时触发 | 多次：当 Watermark 超过窗口结束时间时触发；以固定间隔（如每10秒钟）触发 |
| 输出性质 | 仅输出一个最终的、完整的结果 | 输出一系列中间的、近似的结果，最后输出一个最终的、完整的结果 |
| 延迟 | 高。必须等待窗口结束和水位线推进 | 低。可以很快地看到初步结果，延迟取决于配置的间隔 |
| 适用场景 | 对延迟不敏感但对准确性要求极高的场景，如离线报表、日终结算。| 对延迟敏感，需要早期预览或增量更新的场景，如实时监控仪表盘、实时推荐系统。|

最核心的区别就是触发机制与输出结果：
- EventTimeTrigger 的行为像一个“期末考试”：学生整个学期都在学习（窗口收集数据），但只在期末进行一次考试并给出最终成绩（触发计算输出结果）。
- ContinuousEventTimeTrigger 的行为像“随堂小测 + 期末考试”：学生不仅期末要考试，平时还会进行多次随堂小测。每次小测都反映了学生当前的学习水平（中间近似结果），而期末考试则是最终的综合评定（最终准确结果）。

## 3. 实践

下面我们以一个具体的示例来演示 ContinuousEventTimeTrigger 如何使用，如下所示计算每一分钟内每个单词的出现次数，并且要求每10秒输出一次结果：
```java
DataStream<WordCountTimestamp> result = words.keyBy(new KeySelector<WordCountTimestamp, String>() {
         @Override
         public String getKey(WordCountTimestamp wc) throws Exception {
             return wc.getWord();
         }
     })
     // 事件时间滚动窗口 滚动大小1分钟
     .window(TumblingEventTimeWindows.of(Time.minutes(1)))
     // 周期性事件时间触发器 每10秒触发一次计算
     .trigger(ContinuousEventTimeTrigger.of(Time.seconds(10)))
     // 求和
     .reduce(new ReduceFunction<WordCountTimestamp>() {
         @Override
         public WordCountTimestamp reduce(WordCountTimestamp v1, WordCountTimestamp v2) throws Exception {
             int count = v1.getFrequency() + v2.getFrequency();
             String ids = v1.getId() + "," + v2.getId();
             Long timestamp = Math.max(v1.getTimestamp(), v2.getTimestamp());
             LOG.info("id: {}, count: {}, timestamp: {}", ids, count, timestamp);
             return new WordCountTimestamp(ids, v1.getWord(), count, timestamp);
         }
     });
```
> [ContinuousEventTriggerExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/trigger/ContinuousEventTriggerExample.java)

实际效果如下所示：
```java
10:27:48,113 INFO  WordCountOutOfOrderSource [] - id: 1, word: a, frequency: 2, eventTime: 1662303772840|2022-09-04 23:02:52
10:27:49,120 INFO  WordCountOutOfOrderSource [] - id: 2, word: a, frequency: 1, eventTime: 1662303770844|2022-09-04 23:02:50
10:27:49,198 INFO  ContinuousEventTriggerExample [] - id: 1,2, count: 3, timestamp: 1662303772840
10:27:50,127 INFO  WordCountOutOfOrderSource [] - id: 3, word: a, frequency: 3, eventTime: 1662303773848|2022-09-04 23:02:53
10:27:50,142 INFO  ContinuousEventTriggerExample [] - id: 1,2,3, count: 6, timestamp: 1662303773848
10:27:51,133 INFO  WordCountOutOfOrderSource [] - id: 4, word: a, frequency: 2, eventTime: 1662303774866|2022-09-04 23:02:54
10:27:51,174 INFO  ContinuousEventTriggerExample [] - id: 1,2,3,4, count: 8, timestamp: 1662303774866
10:27:52,139 INFO  WordCountOutOfOrderSource [] - id: 5, word: a, frequency: 1, eventTime: 1662303777839|2022-09-04 23:02:57
10:27:52,211 INFO  ContinuousEventTriggerExample [] - id: 1,2,3,4,5, count: 9, timestamp: 1662303777839
10:27:53,145 INFO  WordCountOutOfOrderSource [] - id: 6, word: a, frequency: 2, eventTime: 1662303784887|2022-09-04 23:03:04
10:27:54,151 INFO  WordCountOutOfOrderSource [] - id: 7, word: a, frequency: 3, eventTime: 1662303776894|2022-09-04 23:02:56
10:27:54,176 INFO  ContinuousEventTriggerExample [] - id: 1,2,3,4,5,7, count: 12, timestamp: 1662303777839
10:27:55,155 INFO  WordCountOutOfOrderSource [] - id: 8, word: a, frequency: 1, eventTime: 1662303786891|2022-09-04 23:03:06
10:27:55,222 INFO  ContinuousEventTriggerExample [] - id: 6,8, count: 3, timestamp: 1662303786891
// 窗口[2,3)第1次结果输出
WordCountTimestamp{id='1,2,3,4,5,7', word='a', frequency=12, timestamp=1662303777839}
10:27:56,162 INFO  WordCountOutOfOrderSource [] - id: 9, word: a, frequency: 5, eventTime: 1662303778877|2022-09-04 23:02:58
10:27:57,168 INFO  WordCountOutOfOrderSource [] - id: 10, word: a, frequency: 4, eventTime: 1662303791904|2022-09-04 23:03:11
10:27:57,194 INFO  ContinuousEventTriggerExample [] - id: 6,8,10, count: 7, timestamp: 1662303791904
10:27:58,174 INFO  WordCountOutOfOrderSource [] - id: 11, word: a, frequency: 1, eventTime: 1662303795918|2022-09-04 23:03:15
10:27:58,233 INFO  ContinuousEventTriggerExample [] - id: 6,8,10,11, count: 8, timestamp: 1662303795918
// 窗口[3,4)第1次结果输出
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
10:27:59,179 INFO  WordCountOutOfOrderSource [] - id: 12, word: a, frequency: 6, eventTime: 1662303779883|2022-09-04 23:02:59
10:28:00,181 INFO  WordCountOutOfOrderSource [] - id: 13, word: a, frequency: 2, eventTime: 1662303846254|2022-09-04 23:04:06
// 窗口[3,4)第2次结果输出
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
// 窗口[3,4)第3次结果输出
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
// 窗口[3,4)第4次结果输出
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
// 窗口[3,4)第5次结果输出
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
// 窗口[3,4)第6次结果输出
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
// 窗口[4,5)第1次结果输出
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
// 窗口[4,5)第2次结果输出
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
// 窗口[4,5)第3次结果输出
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
// 窗口[4,5)第4次结果输出
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
// 窗口[4,5)第5次结果输出
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
// 窗口[4,5)第6次结果输出
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
```
从上面可以看到窗口 [2,3) 只输出可一次，是在窗口结束时触发计算输出。窗口 [3, 4) 第1次结果输出是在窗口生效后超过10秒事件时间触发的，也可以理解。但是为什么窗口 [3, 4) 和窗口[4,5)后续连续输出多次呢？为了好的阐释为什么有这么的输出，我们需要详细研究一下 ContinuousEventTimeTrigger 的实现逻辑。

## 4. 深度解析

> org.apache.flink.streaming.api.windowing.triggers.ContinuousEventTimeTrigger

### 4.1 类结构与成员变量

ContinuousEventTimeTrigger
```java
public class ContinuousEventTimeTrigger<W extends Window> extends Trigger<Object, W> {
    @Override
    public TriggerResult onElement(Object o, long l, W w, TriggerContext triggerContext) throws Exception {
        return null;
    }

    @Override
    public TriggerResult onProcessingTime(long l, W w, TriggerContext triggerContext) throws Exception {
        return null;
    }

    @Override
    public TriggerResult onEventTime(long l, W w, TriggerContext triggerContext) throws Exception {
        return null;
    }

    @Override
    public void clear(W w, TriggerContext triggerContext) throws Exception {

    }
}
```

### 4.2 onElement

每个元素到达时都会进行一些判断与处理：
- 如果 Watermark 超过了窗口结束时间则会立即触发窗口的计算
- 如果 Watermark 没有超过窗口结束时间，不触发窗口计算，只注册定时器
  - 每个到达的元素都会注册窗口结束时间事件时间定时器
    - 定时器的时间戳是窗口的结束时间 `window.maxTimestamp()`
  - 第一个元素进入窗口时(周期性定时器状态 ReducingState 为空)，则为窗口首次注册周期性事件时间定时器
    - 定时器的时间戳是窗口的结束时间 `window.maxTimestamp()` 与 `窗口开始时间 + 窗口周期触发间隔` 的最小值

```java
public TriggerResult onElement(Object element, long timestamp, W window, TriggerContext ctx) throws Exception {
    if (window.maxTimestamp() <= ctx.getCurrentWatermark()) {
        LOG.info("watermark already past the window, window fire immediately, watermark: {}({}), maxTimestamp: {}({})",
                ctx.getCurrentWatermark(), DateUtil.timeStamp2Date(ctx.getCurrentWatermark()),
                window.maxTimestamp(), DateUtil.timeStamp2Date(window.maxTimestamp())
        );
        return TriggerResult.FIRE;
    } else {
        // 1. 注册窗口结束时间事件时间定时器
        LOG.info("register window end eventTime timer, maxTimestamp: {}({})", window.maxTimestamp(), DateUtil.timeStamp2Date(window.maxTimestamp()));
        ctx.registerEventTimeTimer(window.maxTimestamp());
        // 2. 首次注册周期性事件时间定时器
        ReducingState<Long> fireTimestampState = (ReducingState)ctx.getPartitionedState(this.stateDesc);
        if (fireTimestampState.get() == null) {
            long windowStart = timestamp - timestamp % this.interval;
            this.registerNextFireTimestamp(windowStart, window, ctx, fireTimestampState);
        }
        return TriggerResult.CONTINUE;
    }
}

// 注册事件时间定时器
private void registerNextFireTimestamp(long time, W window, Trigger.TriggerContext ctx, ReducingState<Long> fireTimestampState) throws Exception {
    // windowStart + interval 与 窗口结束时间 window.maxTimestamp 最小值
    long nextFireTimestamp = Math.min(time + this.interval, window.maxTimestamp());
    fireTimestampState.add(nextFireTimestamp);
    LOG.info("register continuous eventTime timer, nextFireTimestamp: {}({})", nextFireTimestamp, DateUtil.timeStamp2Date(nextFireTimestamp));
    ctx.registerEventTimeTimer(nextFireTimestamp);
}
```

### 4.3 onEventTime

定时器触发时会调用 onEventTime 方法，只有当事件时间到达周期触发时间或者到达窗口结束时间时才会触发：
- 窗口结束触发：当事件时间到达窗口结束时间时，只触发窗口计算
  - 如果定时器触发的时间等于窗口的结束时间
- 周期性触发：当事件时间到达周期触发时间时，触发窗口计算，并注册下一个周期性时间定时器
  - 如果定时器触发的时间等于状态中保存的定时器时间

```java
@Override
public TriggerResult onEventTime(long time, W window, TriggerContext ctx) throws Exception {
    LOG.info("onEventTime time: {}", time);
    if (time == window.maxTimestamp()) {
        // 1. 窗口结束触发
        // 如果定时器触发的时间等于窗口的结束时间，窗口结束需要立即触发 不注册定时器
        LOG.info("onEventTime window end fire, time: {}({}), maxTimestamp: {}({})",
                time, DateUtil.timeStamp2Date(time),
                window.maxTimestamp(), DateUtil.timeStamp2Date(window.maxTimestamp())
        );
        return TriggerResult.FIRE;
    } else {
        // 2. 周期性触发
        ReducingState<Long> fireTimestampState = (ReducingState)ctx.getPartitionedState(this.stateDesc);
        Long fireTimestamp = (Long)fireTimestampState.get();
        LOG.info("onEventTime fireTimestamp: {}", fireTimestamp);
        if (fireTimestamp != null && fireTimestamp == time) {
            fireTimestampState.clear();
            LOG.info("onEventTime window continuous fire, time: {}({}), fireTimestamp: {}({})",
                    time, DateUtil.timeStamp2Date(time),
                    fireTimestamp, DateUtil.timeStamp2Date(fireTimestamp)
            );
            this.registerNextFireTimestamp(time, window, ctx, fireTimestampState);
            return TriggerResult.FIRE;
        } else {
            return TriggerResult.CONTINUE;
        }
    }
}
```

### 4.4 onProcessingTime

事件时间触发器不关心处理时间：
```java
@Override
public TriggerResult onProcessingTime(long time, W window, TriggerContext ctx) throws Exception {
    return TriggerResult.CONTINUE;
}
```

### 4.5 触发器合并

在窗口合并时，不仅仅需要合并窗口中的状态，可能还需要合并窗口依赖的触发器。因此提供了如下两个方法来支持触发器的合并：
```java
@Override
public boolean canMerge() {
    return true;
}

@Override
public void onMerge(W window, OnMergeContext ctx) throws Exception {
    ctx.mergePartitionedState(stateDesc);
    Long nextFireTimestamp = ctx.getPartitionedState(stateDesc).get();
    if (nextFireTimestamp != null) {
        ctx.registerEventTimeTimer(nextFireTimestamp);
    }
}
```
如果触发器支持合并触发器状态，并可以与 MergingWindowAssigner 一起使用，那么 canMerge 返回 true，否则返回 false。如果触发器不支持合并，则无法与 MergingWindowAssigner 组合使用。当多个窗口需要合并为一个窗口，并且还需要合并触发器状态时会调用 onMerge 进行触发器状态的合并。需要注意的是，如果 canMerge 返回 true，那么必须实现 onMerge 方法。

### 4.6 状态管理

ContinuousEventTimeTrigger 使用 ReducingState 来存储下一次应该触发的时间戳。这种设计具有以下优点：
- 容错性: 状态由 Flink 状态后端管理，支持精确一次语义
- 高效性: 只需要存储一个长整型数值，开销很小
- 一致性: 即使发生故障恢复，触发时间也能保持正确


```java
private final ReducingStateDescriptor<Long> stateDesc;

private ContinuousEventTimeTrigger(long interval) {
    this.stateDesc = new ReducingStateDescriptor("fire-time", new Min(), LongSerializer.INSTANCE);
    this.interval = interval;
}

private static class Min implements ReduceFunction<Long> {
    private static final long serialVersionUID = 1L;

    @Override
    public Long reduce(Long value1, Long value2) throws Exception {
        return Math.min(value1, value2);
    }
}
```


相比之前只是增加了一些日志输出。输出效果如下所示：
```java
// 1. 每个元素到达需要注册窗口结束时间事件时间定时器 23:02:59
// [2, 3) 窗口首次注册周期性事件时间定时器 23:02:59 Min(23:02:60, 23:02:59) -> 23:02:59
10:27:48,113 INFO  WordCountOutOfOrderSource [] - id: 1, word: a, frequency: 2, eventTime: 1662303772840|2022-09-04 23:02:52
10:27:48,158 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303779999(2022-09-04 23:02:59)
10:27:48,158 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303779999(2022-09-04 23:02:59)

// 2. 每个元素到达需要注册窗口结束时间事件时间定时器 23:02:59
10:27:49,120 INFO  WordCountOutOfOrderSource [] - id: 2, word: a, frequency: 1, eventTime: 1662303770844|2022-09-04 23:02:50
10:27:49,198 INFO  CustomContinuousEventTriggerExample [] - id: 1,2, count: 3, timestamp: 1662303772840
10:27:49,199 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303779999(2022-09-04 23:02:59)

// 3. 每个元素到达需要注册窗口结束时间事件时间定时器 23:02:59
10:27:50,127 INFO  WordCountOutOfOrderSource [] - id: 3, word: a, frequency: 3, eventTime: 1662303773848|2022-09-04 23:02:53
10:27:50,142 INFO  CustomContinuousEventTriggerExample [] - id: 1,2,3, count: 6, timestamp: 1662303773848
10:27:50,143 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303779999(2022-09-04 23:02:59)

// 4. 每个元素到达需要注册窗口结束时间事件时间定时器 23:02:59
10:27:51,133 INFO  WordCountOutOfOrderSource [] - id: 4, word: a, frequency: 2, eventTime: 1662303774866|2022-09-04 23:02:54
10:27:51,174 INFO  CustomContinuousEventTriggerExample [] - id: 1,2,3,4, count: 8, timestamp: 1662303774866
10:27:51,175 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303779999(2022-09-04 23:02:59)

// 5. 每个元素到达需要注册窗口结束时间事件时间定时器 23:02:59
10:27:52,139 INFO  WordCountOutOfOrderSource [] - id: 5, word: a, frequency: 1, eventTime: 1662303777839|2022-09-04 23:02:57
10:27:52,211 INFO  CustomContinuousEventTriggerExample [] - id: 1,2,3,4,5, count: 9, timestamp: 1662303777839
10:27:52,211 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303779999(2022-09-04 23:02:59)

// 6. 每个元素到达需要注册窗口结束时间事件时间定时器 23:03:59
// [3, 4) 窗口首次注册周期性事件时间定时器 23:03:10
10:27:53,145 INFO  WordCountOutOfOrderSource [] - id: 6, word: a, frequency: 2, eventTime: 1662303784887|2022-09-04 23:03:04
10:27:53,240 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303839999(2022-09-04 23:03:59)
10:27:53,241 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303790000(2022-09-04 23:03:10)

// 7. 每个元素到达需要注册窗口结束时间事件时间定时器 23:02:59
10:27:54,151 INFO  WordCountOutOfOrderSource [] - id: 7, word: a, frequency: 3, eventTime: 1662303776894|2022-09-04 23:02:56
10:27:54,176 INFO  CustomContinuousEventTriggerExample [] - id: 1,2,3,4,5,7, count: 12, timestamp: 1662303777839
10:27:54,177 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303779999(2022-09-04 23:02:59)

// 8. 每个元素到达需要注册窗口结束时间事件时间定时器 23:03:59
10:27:55,155 INFO  WordCountOutOfOrderSource [] - id: 8, word: a, frequency: 1, eventTime: 1662303786891|2022-09-04 23:03:06
10:27:55,222 INFO  CustomContinuousEventTriggerExample [] - id: 6,8, count: 3, timestamp: 1662303786891
10:27:55,223 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303839999(2022-09-04 23:03:59)

// 9. 事件时间定时器 23:02:59 触发 等于窗口结束时间触发 [2, 3) 窗口计算输出结果
10:27:55,327 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303779999
10:27:55,328 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window end fire, time: 1662303779999(2022-09-04 23:02:59), maxTimestamp: 1662303779999(2022-09-04 23:02:59)
WordCountTimestamp{id='1,2,3,4,5,7', word='a', frequency=12, timestamp=1662303777839}
10:27:55,329 INFO  CustomContinuousEventTimeTrigger [] - delete eventTime timer and clear fireTimestamp

// 10. [2, 3) 窗口已经触发计算并销毁 不需要调用Trigger？
10:27:56,162 INFO  WordCountOutOfOrderSource [] - id: 9, word: a, frequency: 5, eventTime: 1662303778877|2022-09-04 23:02:58

// 11. 每个元素到达需要注册窗口结束时间事件时间定时器 23:03:59
10:27:57,168 INFO  WordCountOutOfOrderSource [] - id: 10, word: a, frequency: 4, eventTime: 1662303791904|2022-09-04 23:03:11
10:27:57,194 INFO  CustomContinuousEventTriggerExample [] - id: 6,8,10, count: 7, timestamp: 1662303791904
10:27:57,194 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303839999(2022-09-04 23:03:59)

// 12. 每个元素到达需要注册窗口结束时间事件时间定时器 23:03:59
10:27:58,174 INFO  WordCountOutOfOrderSource [] - id: 11, word: a, frequency: 1, eventTime: 1662303795918|2022-09-04 23:03:15
10:27:58,233 INFO  CustomContinuousEventTriggerExample [] - id: 6,8,10,11, count: 8, timestamp: 1662303795918
10:27:58,233 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303839999(2022-09-04 23:03:59)

// 13. 周期性触发器 23:03:10 触发 [3, 4) 窗口计算输出结果，注册下一个周期性触发器 23:03:20
10:27:58,440 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303790000
10:27:58,440 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303790000
10:27:58,441 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303790000(2022-09-04 23:03:10), fireTimestamp: 1662303790000(2022-09-04 23:03:10)
10:27:58,441 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303800000(2022-09-04 23:03:20)
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}

// 14. [2, 3) 窗口已经触发计算并销毁 不需要调用Trigger？
10:27:59,179 INFO  WordCountOutOfOrderSource [] - id: 12, word: a, frequency: 6, eventTime: 1662303779883|2022-09-04 23:02:59

// 15. 每个元素到达需要注册窗口结束时间事件时间定时器 23:04:59，[4, 5) 窗口首次注册周期性事件时间定时器 23:04:10
10:28:00,181 INFO  WordCountOutOfOrderSource [] - id: 13, word: a, frequency: 2, eventTime: 1662303846254|2022-09-04 23:04:06
10:28:00,206 INFO  CustomContinuousEventTimeTrigger [] - register window end eventTime timer, maxTimestamp: 1662303899999(2022-09-04 23:04:59)
10:28:00,207 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303850000(2022-09-04 23:04:10)

// 16. 周期性触发器 23:03:20 触发 [3, 4) 窗口计算输出结果，注册下一个周期性触发器 23:03:30
10:28:00,207 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303800000
10:28:00,207 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303800000
10:28:00,208 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303800000(2022-09-04 23:03:20), fireTimestamp: 1662303800000(2022-09-04 23:03:20)
10:28:00,208 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303810000(2022-09-04 23:03:30)
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}

// 17. 周期性触发器 23:03:30 触发 [3, 4) 窗口计算输出结果，注册下一个周期性触发器 23:03:40
10:28:00,208 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303810000
10:28:00,208 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303810000
10:28:00,209 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303810000(2022-09-04 23:03:30), fireTimestamp: 1662303810000(2022-09-04 23:03:30)
10:28:00,209 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303820000(2022-09-04 23:03:40)
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}

// 18. 周期性触发器 23:03:40 触发 [3, 4) 窗口计算输出结果，注册下一个周期性触发器 23:03:50
10:28:00,209 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303820000
10:28:00,209 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303820000
10:28:00,209 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303820000(2022-09-04 23:03:40), fireTimestamp: 1662303820000(2022-09-04 23:03:40)
10:28:00,210 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303830000(2022-09-04 23:03:50)
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}

// 19. 周期性触发器 23:03:50 触发 [3, 4) 窗口计算输出结果，注册下一个周期性触发器 23:03:59
// Min(23:03:60, 23:03:59) -> 23:03:59
10:28:00,210 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303830000
10:28:00,210 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303830000
10:28:00,210 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303830000(2022-09-04 23:03:50), fireTimestamp: 1662303830000(2022-09-04 23:03:50)
10:28:00,210 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303839999(2022-09-04 23:03:59)
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}

// 20. 事件时间定时器 23:03:59 触发 等于窗口结束时间触发 [3, 4) 窗口计算输出结果
10:28:00,211 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303839999
10:28:00,211 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window end fire, time: 1662303839999(2022-09-04 23:03:59), maxTimestamp: 1662303839999(2022-09-04 23:03:59)
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
10:28:00,211 INFO  CustomContinuousEventTimeTrigger [] - delete eventTime timer and clear fireTimestamp

// 21. 周期性触发器 23:04:10 触发 [4, 5) 窗口计算输出结果，注册下一个周期性触发器 23:04:20
10:28:01,189 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303850000
10:28:01,189 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303850000
10:28:01,189 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303850000(2022-09-04 23:04:10), fireTimestamp: 1662303850000(2022-09-04 23:04:10)
10:28:01,190 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303860000(2022-09-04 23:04:20)
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}

// 22. 周期性触发器 23:04:20 触发 [4, 5) 窗口计算输出结果，注册下一个周期性触发器 23:04:30
10:28:01,190 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303860000
10:28:01,190 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303860000
10:28:01,190 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303860000(2022-09-04 23:04:20), fireTimestamp: 1662303860000(2022-09-04 23:04:20)
10:28:01,190 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303870000(2022-09-04 23:04:30)
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}

// 23. 周期性触发器 23:04:30 触发 [4, 5) 窗口计算输出结果，注册下一个周期性触发器 23:04:40
10:28:01,190 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303870000
10:28:01,190 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303870000
10:28:01,191 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303870000(2022-09-04 23:04:30), fireTimestamp: 1662303870000(2022-09-04 23:04:30)
10:28:01,191 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303880000(2022-09-04 23:04:40)
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}

// 23. 周期性触发器 23:04:40 触发 [4, 5) 窗口计算输出结果，注册下一个周期性触发器 23:04:50
10:28:01,191 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303880000
10:28:01,191 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303880000
10:28:01,191 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303880000(2022-09-04 23:04:40), fireTimestamp: 1662303880000(2022-09-04 23:04:40)
10:28:01,191 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303890000(2022-09-04 23:04:50)
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}

// 23. 周期性触发器 23:04:50 触发 [4, 5) 窗口计算输出结果，注册下一个周期性触发器 23:04:59
// Min(23:04:60, 23:04:59) -> 23:04:59
10:28:01,191 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303890000
10:28:01,191 INFO  CustomContinuousEventTimeTrigger [] - onEventTime fireTimestamp: 1662303890000
10:28:01,192 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window continuous fire, time: 1662303890000(2022-09-04 23:04:50), fireTimestamp: 1662303890000(2022-09-04 23:04:50)
10:28:01,192 INFO  CustomContinuousEventTimeTrigger [] - register continuous eventTime timer, nextFireTimestamp: 1662303899999(2022-09-04 23:04:59)
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}

// 24. 事件时间定时器 23:04:59 触发 等于窗口结束时间触发 [4, 5) 窗口计算输出结果
10:28:01,192 INFO  CustomContinuousEventTimeTrigger [] - onEventTime time: 1662303899999
10:28:01,192 INFO  CustomContinuousEventTimeTrigger [] - onEventTime window end fire, time: 1662303899999(2022-09-04 23:04:59), maxTimestamp: 1662303899999(2022-09-04 23:04:59)
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
```
> [CustomContinuousEventTriggerExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/trigger/CustomContinuousEventTriggerExample.java)


在使用 ContinuousEventTimeTrigger 有以下点需要注意

连续定时触发与第一条数据有关，例如第一条数据是2019-11-16 11:22:01， 10s触发一次，那么后续触发时间就分别是2019-11-16 11:22:10、2019-11-16 11:22:20、2019-11-16 11:22:30

如果数据时间间隔相对于定期触发的interval比较大，那么有可能会存在多次输出相同结果的场景，比喻说触发的interval是10s, 第一条数据时间是2019-11-16 11:22:00, 那么下一次的触发时间是2019-11-16 11:22:10， 如果此时来了一条2019-11-16 11:23:00 的数据，会导致其watermark直接提升了1min, 会直接触发5次连续输出，对于下游处理来说可能会需要做额外的操作。

窗口的每一个key的触发时间可能会不一致，是因为窗口的每一个key对应的第一条数据时间不一样，正如上述所描述定时规则。由于会注册一个窗口endTime的触发器，会触发窗口所有key的窗口函数，保证最终结果的正确性。


https://www.jianshu.com/p/e16b94284d9f
