
在事件时间语义下，窗口中可能会出现数据迟到的情况。这是因为在乱序流中，Watermark 并不一定能保证时间戳更早的所有数据不会再来。当 Watermark 已经到达窗口结束时间时，窗口会触发计算并输出结果，这时一般也就要销毁窗口了;如果窗口关闭之后，又有本属于窗口内的数据姗姗来迟，默认情况下就会被丢弃。这也很好理解:窗口触发计算就像发车，如果要赶的车已经开走了，又不能坐其他的车(保证分配窗口的正确性)，那就只好放弃坐班车了。

不过在多数情况下，直接丢弃数据也会导致统计结果不准确，我们还是希望该上车的人都能上来。为了解决迟到数据的问题，Flink 提供了一个特殊的接口，可以为窗口算子设置一个 “允许的最大延迟”(Allowed Lateness)。也就是说，我们可以设定允许延迟一段时间，在这段时间内，窗口不会销毁，继续到来的数据依然可以进入窗口中并触发计算。直到 Watermark 推进到了窗口结束时间 + 延迟时间，才真正将窗口的内容清空，正式关闭窗口。

基于 WindowedStream 调用 allowedLateness() 方法，传入一个 Time 类型的延迟时间，就可以表示允许这段时间内的延迟数据：
```java
stream.keyBy(...)
      .window(TumblingEventTimeWindows.of(Time.hours(1)))
      .allowedLateness(Time.minutes(1))
```
比如上面的代码中，我们定义了 1 小时的滚动窗口，并设置了允许 1 分钟的延迟数据。也就是说，在不考虑 Watermakr 延迟的情况下，对于8点到9点的窗口，本来应该是 Watermark 到达 9 点整就触发计算并关闭窗口。但是现在可以允许延迟 1 分钟，那么 9 点整就只是触发一次计算并输出结果，并不会销毁窗口。后续到达的数据，只要属于 8 点到 9 点窗口，依然可以在之前统计的基础上继续叠加，并且再次输出一个更新后的结果。直到 Watermark 到达了 9 点零 1 分，这时就真正清空状态、关闭窗口，之后再来的迟到数据就会被丢弃了。

从这里我们就可以看到，窗口的触发计算(Fire)和清除(Purge)操作确实可以分开。不过在默认情况下，允许的延迟是 0，这样一旦 Watermark 到达了窗口结束时间就会触发计算并清除窗口，两个操作看起来就是同时发生了。当窗口被清除(关闭)之后，再来的数据就会被丢弃。

## 2. 将迟到的数据放入侧输出流

我们自然会想到，即使可以设置窗口的延迟时间，终归还是有限的，后续的数据还是会被丢弃。如果不想丢弃任何一个数据，又该怎么做呢? Flink 还提供了另外一种方式处理迟到数据。我们可以将未收入窗口的迟到数据，放入侧输出流(side output)进行另外的处理。所谓的侧输出流，相当于是数据流的一个“分支”， 这个流中单独放置那些错过了该上的车、本该被丢弃的数据。

基于 WindowedStream 调用.sideOutputLateData() 方法，就可以实现这个功能。方法需要 传入一个“输出标签”(OutputTag)，用来标记分支的迟到数据流。因为保存的就是流中的原 始数据，所以 OutputTag 的类型与流中数据类型相同。


```
22:00:55,757 Source      [] - id: 1, word: a, count: 2, eventTime: 1662303772840|2022-09-04 23:02:52
22:00:56,761 Source      [] - id: 2, word: a, count: 1, eventTime: 1662303770844|2022-09-04 23:02:50
22:00:57,764 Source      [] - id: 3, word: a, count: 3, eventTime: 1662303773848|2022-09-04 23:02:53
22:00:58,767 Source      [] - id: 4, word: a, count: 2, eventTime: 1662303774866|2022-09-04 23:02:54
22:00:59,772 Source      [] - id: 5, word: a, count: 1, eventTime: 1662303777839|2022-09-04 23:02:57
22:01:00,775 Source      [] - id: 6, word: a, count: 2, eventTime: 1662303784887|2022-09-04 23:03:04
22:01:01,777 Source      [] - id: 7, word: a, count: 3, eventTime: 1662303776894|2022-09-04 23:02:56
22:01:02,778 Source      [] - id: 8, word: a, count: 1, eventTime: 1662303786891|2022-09-04 23:03:06
22:01:02,937 Sum         [] - word: a, count: 6, ids: [1, 2, 3, 4, 5, 7], window: [2022-09-04 23:02:00, 2022-09-04 23:03:00], watermark: 1662303781890|2022-09-04 23:03:01
主链路> (a,6)
22:01:03,780 Source      [] - id: 9, word: a, count: 5, eventTime: 1662303778877|2022-09-04 23:02:58
22:01:03,860 Sum         [] - word: a, count: 7, ids: [1, 2, 3, 4, 5, 7, 9], window: [2022-09-04 23:02:00, 2022-09-04 23:03:00], watermark: 1662303781890|2022-09-04 23:03:01
主链路> (a,7)
22:01:04,783 Source      [] - id: 10, word: a, count: 4, eventTime: 1662303791904|2022-09-04 23:03:11
22:01:05,788 Source      [] - id: 11, word: a, count: 1, eventTime: 1662303795918|2022-09-04 23:03:15
22:01:06,793 Source      [] - id: 12, word: a, count: 6, eventTime: 1662303779883|2022-09-04 23:02:59
延迟链路> (12,a,6,1662303779883)
22:01:07,797 Source      [] - id: 13, word: a, count: 2, eventTime: 1662303846254|2022-09-04 23:04:06
22:01:07,868 Sum         [] - word: a, count: 4, ids: [6, 8, 10, 11], window: [2022-09-04 23:03:00, 2022-09-04 23:04:00], watermark: 1662303841253|2022-09-04 23:04:01
主链路> (a,4)
22:01:08,808 Sum         [] - word: a, count: 1, ids: [13], window: [2022-09-04 23:04:00, 2022-09-04 23:05:00], watermark: 9223372036854775807|292278994-08-17 15:12:55
主链路> (a,1)
```

## 3. 实现原理

```java
for (W window : elementWindows) {
    if (isWindowLate(window)) {
        continue;
    }
    isSkippedElement = false;

    windowState.setCurrentNamespace(window);
    windowState.add(element.getValue());

    triggerContext.key = key;
    triggerContext.window = window;

    TriggerResult triggerResult = triggerContext.onElement(element);
    if (triggerResult.isFire()) {
        ACC contents = windowState.get();
        if (contents == null) {
            continue;
        }
        emitWindowContents(window, contents);
    }
    if (triggerResult.isPurge()) {
        windowState.clear();
    }
    registerCleanupTimer(window);
}
```
对于可以合并的窗口，增加一个窗口后可能会导致窗口的合并，因此合并后的窗口才是实际要处理的窗口。除了窗口合并之外，其他处理逻辑基本一致，在这不再赘述：
```java
W actualWindow = mergingWindows.addWindow(
      window,
      new MergingWindowSet.MergeFunction<W>(){
          ...
      }
);
```

只有基于事件时间的窗口才有迟到窗口的概念，当窗口的清除时间小于等于当前 Watermark 即认为是迟到窗口：
```java
protected boolean isWindowLate(W window) {
    return (windowAssigner.isEventTime()
            && (cleanupTime(window) <= internalTimerService.currentWatermark()));
}
// 窗口的清除时间
private long cleanupTime(W window) {
    if (windowAssigner.isEventTime()) {
        long cleanupTime = window.maxTimestamp() + allowedLateness;
        return cleanupTime >= window.maxTimestamp() ? cleanupTime : Long.MAX_VALUE;
    } else {
        return window.maxTimestamp();
    }
}
```
> 需要注意的是，allowedLateness 是针对事件时间窗口分配器的

如果是基于事件时间的窗口，窗口的清除时间为窗口的最大时间戳加上最大可允许的时间 allowedLateness；如果是基于处理时间的窗口，窗口的清除时间为窗口为窗口的最大时间戳：


window.maxTimestamp() + allowedLateness <= watermark

```java
protected boolean isElementLate(StreamRecord<IN> element) {
    return (windowAssigner.isEventTime())
            && (element.getTimestamp() + allowedLateness
                    <= internalTimerService.currentWatermark());
}
```


窗口销毁时间: window.maxTimestamp + allowedLateness
