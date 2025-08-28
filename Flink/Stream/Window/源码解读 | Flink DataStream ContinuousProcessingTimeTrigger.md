
onElement 方法：
```java
public TriggerResult onElement(Object element, long timestamp, W window, TriggerContext ctx) throws Exception {
    ReducingState<Long> fireTimestamp = ctx.getPartitionedState(stateDesc);
    timestamp = ctx.getCurrentProcessingTime();
    // 如果为 null 表示之前未注册处理时间定时器
    if (fireTimestamp.get() == null) {
       // 计算下一次触发的时间点
       long start = timestamp - (timestamp % interval);
       long nextFireTimestamp = start + interval;
       // 注册处理时间定时器
       ctx.registerProcessingTimeTimer(nextFireTimestamp);
       // 更新到状态中
       fireTimestamp.add(nextFireTimestamp);
       return TriggerResult.CONTINUE;
    }
    return TriggerResult.CONTINUE;
}
```
在这个方法中核心是为周期间隔内首次到达的数据记录注册处理时间定时器。

onProcessingTime 方法：
```java
public TriggerResult onProcessingTime(long time, W window, TriggerContext ctx) throws Exception {
    ReducingState<Long> fireTimestamp = ctx.getPartitionedState(stateDesc);

    if (fireTimestamp.get().equals(time)) {
        fireTimestamp.clear();
        // 注册下一个触发的定时器
        fireTimestamp.add(time + interval);
        ctx.registerProcessingTimeTimer(time + interval);
        return TriggerResult.FIRE;
    }
    return TriggerResult.CONTINUE;
}
```
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
