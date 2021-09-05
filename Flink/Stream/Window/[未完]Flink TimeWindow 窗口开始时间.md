

Flink 中窗口的时间不是根据进入窗口的第一个元素计为窗口的开始时间和加Size计窗口结束时间，而是根据Flink内置计算公式timestamp - (timestamp - offset + windowSize) % windowSize计算：
```java
/**
 * 根据时间戳计算窗口开始时间
 *
 * @param timestamp epoch millisecond to get the window start.
 * @param offset The offset which window start would be shifted by.
 * @param windowSize The size of the generated windows.
 * @return window start
 */
public static long getWindowStartWithOffset(long timestamp, long offset, long windowSize) {
    return timestamp - (timestamp - offset + windowSize) % windowSize;
}
```


使用TimeWindow时，窗口算子（如aggregate, reduce等）允许传入一个ProcessWindowFunction参数。通过重写ProcessWindowFunction的process(KEY key, Context context, Iterable<IN> elements, Collector<OUT> out)方法，可以对窗口计算结果进行再加工，其中context提供了对当前window的访问。使用context.window().getStart()和context.window().getEnd()可以分别得到窗口打开时间和关口关闭时间。
- context.window().getStart()得到的是属于窗口的第一条数据的时间。
- context.window().getEnd()得到的是不属于窗口的第一条数据的时间。

这里需要注意的是，getEnd()得到的时间不输入窗口，当使用事件时间时需要尤为注意，如果你需要的是这个窗口里面最后一个事件的发生时间，不能用getEnd()的结果。

https://juejin.cn/post/6844904110244773895
