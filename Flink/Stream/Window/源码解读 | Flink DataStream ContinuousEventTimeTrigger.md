

```java
public class CustomContinuousEventTimeTrigger<W extends Window> extends Trigger<Object, W> {
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

## 1. onElement

```java
public TriggerResult onElement(Object element, long timestamp, W window, Trigger.TriggerContext ctx) throws Exception {
    if (window.maxTimestamp() <= ctx.getCurrentWatermark()) {
        // 如果 Watermark 已经超过了窗口结束时间 立即触发
        return TriggerResult.FIRE;
    } else {
        // 每个正常到达的元素都要注册事件时间定时器
        ctx.registerEventTimeTimer(window.maxTimestamp());
        ReducingState<Long> fireTimestampState = (ReducingState)ctx.getPartitionedState(this.stateDesc);
        if (fireTimestampState.get() == null) {
            this.registerNextFireTimestamp(timestamp - timestamp % this.interval, window, ctx, fireTimestampState);
        }
        return TriggerResult.CONTINUE;
    }
}
```

## 2. onEventTime

```java
public TriggerResult onEventTime(long time, W window, Trigger.TriggerContext ctx) throws Exception {
    if (time == window.maxTimestamp()) {
        return TriggerResult.FIRE;
    } else {
        ReducingState<Long> fireTimestampState = (ReducingState)ctx.getPartitionedState(this.stateDesc);
        Long fireTimestamp = (Long)fireTimestampState.get();
        if (fireTimestamp != null && fireTimestamp == time) {
            fireTimestampState.clear();
            this.registerNextFireTimestamp(time, window, ctx, fireTimestampState);
            return TriggerResult.FIRE;
        } else {
            return TriggerResult.CONTINUE;
        }
    }
}
```

## 3. onProcessingTime

```java
public TriggerResult onProcessingTime(long time, W window, Trigger.TriggerContext ctx) throws Exception {
    return TriggerResult.CONTINUE;
}
```

## 4. clear

```java
public void clear(W window, Trigger.TriggerContext ctx) throws Exception {
    ReducingState<Long> fireTimestamp = (ReducingState)ctx.getPartitionedState(this.stateDesc);
    Long timestamp = (Long)fireTimestamp.get();
    if (timestamp != null) {
        ctx.deleteEventTimeTimer(timestamp);
        fireTimestamp.clear();
    }

}
```

## 5. canMerge&onMerge

```java
public boolean canMerge() {
    return true;
}

public void onMerge(W window, Trigger.OnMergeContext ctx) throws Exception {
    ctx.mergePartitionedState(this.stateDesc);
    Long nextFireTimestamp = (Long)((ReducingState)ctx.getPartitionedState(this.stateDesc)).get();
    if (nextFireTimestamp != null) {
        ctx.registerEventTimeTimer(nextFireTimestamp);
    }

}
```

## 6. 状态

```java
private final ReducingStateDescriptor<Long> stateDesc;

private ContinuousEventTimeTrigger(long interval) {
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

## 7.

```java
private void registerNextFireTimestamp(long time, W window, Trigger.TriggerContext ctx, ReducingState<Long> fireTimestampState) throws Exception {
    long nextFireTimestamp = Math.min(time + this.interval, window.maxTimestamp());
    fireTimestampState.add(nextFireTimestamp);
    ctx.registerEventTimeTimer(nextFireTimestamp);
}
```


## 2. 实践

```java
22:22:42,042 INFO  WordCountOutOfOrderSource [] - id: 1, word: a, frequency: 2, eventTime: 1662303772840|2022-09-04 23:02:52
22:22:43,048 INFO  WordCountOutOfOrderSource [] - id: 2, word: a, frequency: 1, eventTime: 1662303770844|2022-09-04 23:02:50
22:22:43,143 INFO  ContinuousEventTriggerExample [] - id: 1,2, count: 3, timestamp: 1662303772840
22:22:44,052 INFO  WordCountOutOfOrderSource [] - id: 3, word: a, frequency: 3, eventTime: 1662303773848|2022-09-04 23:02:53
22:22:44,076 INFO  ContinuousEventTriggerExample [] - id: 1,2,3, count: 6, timestamp: 1662303773848
22:22:45,055 INFO  WordCountOutOfOrderSource [] - id: 4, word: a, frequency: 2, eventTime: 1662303774866|2022-09-04 23:02:54
22:22:45,114 INFO  ContinuousEventTriggerExample [] - id: 1,2,3,4, count: 8, timestamp: 1662303774866
22:22:46,058 INFO  WordCountOutOfOrderSource [] - id: 5, word: a, frequency: 1, eventTime: 1662303777839|2022-09-04 23:02:57
22:22:46,159 INFO  ContinuousEventTriggerExample [] - id: 1,2,3,4,5, count: 9, timestamp: 1662303777839
22:22:47,059 INFO  WordCountOutOfOrderSource [] - id: 6, word: a, frequency: 2, eventTime: 1662303784887|2022-09-04 23:03:04
22:22:48,065 INFO  WordCountOutOfOrderSource [] - id: 7, word: a, frequency: 3, eventTime: 1662303776894|2022-09-04 23:02:56
22:22:48,138 INFO  ContinuousEventTriggerExample [] - id: 1,2,3,4,5,7, count: 12, timestamp: 1662303777839
22:22:49,069 INFO  WordCountOutOfOrderSource [] - id: 8, word: a, frequency: 1, eventTime: 1662303786891|2022-09-04 23:03:06
22:22:49,175 INFO  ContinuousEventTriggerExample [] - id: 6,8, count: 3, timestamp: 1662303786891
WordCountTimestamp{id='1,2,3,4,5,7', word='a', frequency=12, timestamp=1662303777839}
22:22:50,076 INFO  WordCountOutOfOrderSource [] - id: 9, word: a, frequency: 5, eventTime: 1662303778877|2022-09-04 23:02:58
22:22:51,082 INFO  WordCountOutOfOrderSource [] - id: 10, word: a, frequency: 4, eventTime: 1662303791904|2022-09-04 23:03:11
22:22:51,153 INFO  ContinuousEventTriggerExample [] - id: 6,8,10, count: 7, timestamp: 1662303791904
22:22:52,086 INFO  WordCountOutOfOrderSource [] - id: 11, word: a, frequency: 1, eventTime: 1662303795918|2022-09-04 23:03:15
22:22:52,188 INFO  ContinuousEventTriggerExample [] - id: 6,8,10,11, count: 8, timestamp: 1662303795918
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
22:22:53,092 INFO  WordCountOutOfOrderSource [] - id: 12, word: a, frequency: 6, eventTime: 1662303779883|2022-09-04 23:02:59
22:22:54,096 INFO  WordCountOutOfOrderSource [] - id: 13, word: a, frequency: 2, eventTime: 1662303846254|2022-09-04 23:04:06
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
WordCountTimestamp{id='6,8,10,11', word='a', frequency=8, timestamp=1662303795918}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
```
