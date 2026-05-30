---
layout: post
author: sjf0115
title: Flink 元素如何分配到窗口：开始时间与结束时间是如何计算的
date: 2022-09-20 09:30:00
tags:
  - Flink

categories: Flink
permalink: flink-stream-windows-assign-and-time
---

> 基于 Flink 1.13.6 版本源码

很多刚接触 Flink 窗口的同学，常常会有这样的疑问：
- 一条事件到来时，它到底会被分到哪个窗口？
- 窗口的开始时间是从「第一条数据进入的时刻」开始算的吗？
- `getStart()` 和 `getEnd()` 返回的时间戳，到底是包含还是不包含？
- 滑动窗口下，一条数据为什么会被分配到多个窗口？

这些问题的答案，都藏在 `WindowAssigner.assignWindows()` 这个核心方法里。本文将基于 Flink 1.13.6 源码，把窗口分配的全过程讲清楚。

## 1. 窗口分配的入口：WindowAssigner

### 1.1 抽象设计

Flink 的所有窗口分配逻辑都由 `WindowAssigner` 统一抽象：

```java
// org.apache.flink.streaming.api.windowing.assigners.WindowAssigner
@PublicEvolving
public abstract class WindowAssigner<T, W extends Window> implements Serializable {

    /**
     * 返回应该将该元素分配到的窗口集合
     *
     * @param element   待分配的元素
     * @param timestamp 元素的时间戳（事件时间或处理时间）
     * @param context   上下文（可获取当前处理时间等）
     */
    public abstract Collection<W> assignWindows(
            T element, long timestamp, WindowAssignerContext context);

    public abstract Trigger<T, W> getDefaultTrigger(StreamExecutionEnvironment env);

    public abstract TypeSerializer<W> getWindowSerializer(ExecutionConfig executionConfig);

    public abstract boolean isEventTime();
}
```

关键点：
- **返回值是 `Collection<W>`** 而非单个窗口——因为同一条数据在滑动窗口、会话窗口下可能属于**多个**窗口
- **入参 `timestamp`** 是元素的时间戳：事件时间窗口下是 EventTime，处理时间窗口下是 ProcessingTime
- **`isEventTime()`** 标识窗口语义，决定下游 Trigger 如何选择计时器类型

### 1.2 内置窗口分配器

Flink 1.13 内置的窗口分配器主要有 7 种：

| 分配器 | 时间语义 | 一个元素分配到的窗口数 |
|--------|----------|---------------------|
| `TumblingEventTimeWindows` | 事件时间 | 1 |
| `TumblingProcessingTimeWindows` | 处理时间 | 1 |
| `SlidingEventTimeWindows` | 事件时间 | size / slide |
| `SlidingProcessingTimeWindows` | 处理时间 | size / slide |
| `EventTimeSessionWindows` | 事件时间 | 1（后续可合并） |
| `ProcessingTimeSessionWindows` | 处理时间 | 1（后续可合并） |
| `GlobalWindows` | 无 | 1（一个全局窗口） |

下面我们重点剖析 `TumblingEventTimeWindows`、`SlidingEventTimeWindows` 和 `EventTimeSessionWindows` 的分配逻辑。

---

## 2. 时间窗口的数据结构 TimeWindow

在剖析分配逻辑之前，先看时间窗口本身是怎么表示的：

```java
// org.apache.flink.streaming.api.windowing.windows.TimeWindow
@PublicEvolving
public class TimeWindow extends Window {

    private final long start;  // 起始时间戳（包含）
    private final long end;    // 结束时间戳（不包含）

    public TimeWindow(long start, long end) {
        this.start = start;
        this.end = end;
    }

    /** 窗口起始时间戳——属于该窗口的第一个时间戳 */
    public long getStart() {
        return start;
    }

    /** 窗口结束时间戳——不属于该窗口的第一个时间戳（开区间） */
    public long getEnd() {
        return end;
    }

    /** 仍然属于该窗口的最大时间戳 = end - 1 */
    @Override
    public long maxTimestamp() {
        return end - 1;
    }
}
```

**核心要点（务必记住）**：

| 方法 | 含义 | 区间 |
|------|------|------|
| `getStart()` | 窗口起始时间戳 | **包含** |
| `getEnd()` | 窗口结束时间戳 | **不包含**（开区间） |
| `maxTimestamp()` | 窗口内最大有效时间戳 | `getEnd() - 1` |

也就是说，TimeWindow 表示的是**左闭右开**的时间区间 `[start, end)`。

> 这是初学者最常踩的坑：如果你需要"窗口内最后一条事件的发生时间上限"，应该用 `maxTimestamp()` 或 `getEnd() - 1`，而不是 `getEnd()`。

---

## 3. 滚动窗口：一个元素一个窗口

### 3.1 核心源码

`TumblingEventTimeWindows` 的 `assignWindows` 实现非常简洁：

```java
// org.apache.flink.streaming.api.windowing.assigners.TumblingEventTimeWindows
@Override
public Collection<TimeWindow> assignWindows(
        Object element, long timestamp, WindowAssignerContext context) {
    if (timestamp > Long.MIN_VALUE) {
        if (staggerOffset == null) {
            staggerOffset = windowStagger.getStaggerOffset(
                    context.getCurrentProcessingTime(), size);
        }
        // 计算窗口起始时间
        long start = TimeWindow.getWindowStartWithOffset(
                timestamp,
                (globalOffset + staggerOffset) % size,
                size);
        // 返回单个窗口 [start, start + size)
        return Collections.singletonList(new TimeWindow(start, start + size));
    } else {
        throw new RuntimeException(
                "Record has Long.MIN_VALUE timestamp (= no timestamp marker). "
                + "Is the time characteristic set to 'ProcessingTime', or did you forget to call "
                + "'DataStream.assignTimestampsAndWatermarks(...)'?");
    }
}
```

逻辑非常清晰：
1. 校验时间戳合法性（`Long.MIN_VALUE` 表示无时间戳）
2. 计算窗口起始时间 `start`
3. 构造 `TimeWindow(start, start + size)` 返回

### 3.2 窗口起始时间公式

整个分配的核心是 `TimeWindow.getWindowStartWithOffset` 这个静态方法：

```java
// org.apache.flink.streaming.api.windowing.windows.TimeWindow
public static long getWindowStartWithOffset(long timestamp, long offset, long windowSize) {
    return timestamp - (timestamp - offset + windowSize) % windowSize;
}
```

**重要结论**：窗口的开始时间**不是**根据"第一条进入窗口的元素"决定的，而是由这个**纯函数**计算出来的——任何相同时间戳的数据，得到的窗口起点都完全一致。

### 3.3 公式推导

不带偏移量（offset=0）时，公式简化为：
```
start = timestamp - (timestamp + windowSize) % windowSize
```

从数学上看，这是把 `timestamp` 向下对齐到 `windowSize` 的整数倍。例如 `windowSize = 5000ms`：

| timestamp | timestamp % 5000 | start | window |
|-----------|------------------|-------|--------|
| 0     | 0    | 0     | [0, 5000)     |
| 3000  | 3000 | 0     | [0, 5000)     |
| 4999  | 4999 | 0     | [0, 5000)     |
| 5000  | 0    | 5000  | [5000, 10000) |
| 7500  | 2500 | 5000  | [5000, 10000) |

> 加上 `+ windowSize` 是为了**处理 `timestamp - offset` 为负数的情况**，因为 Java 的 `%` 运算对负数会返回负数（如 `-3 % 5 = -3`），加上 `windowSize` 后再取模可以保证结果非负。

### 3.4 偏移量 offset 的作用

offset 的作用是**让窗口边界整体平移**。这在跨时区场景下至关重要：

```java
// 默认情况下，1 天的窗口边界是 UTC 0 点（在中国是早上 8 点）
.window(TumblingEventTimeWindows.of(Time.days(1)))

// 通过 offset = -8h，让窗口边界对齐到 UTC+8 的 0 点（中国本地 0 点）
.window(TumblingEventTimeWindows.of(Time.days(1), Time.hours(-8)))
```

带 offset 的对齐示例（windowSize=1h, offset=15min）：

| timestamp | window |
|-----------|--------|
| 00:14:59 | [-00:45, 00:15) |
| 00:15:00 | [00:15, 01:15) |
| 01:14:59 | [00:15, 01:15) |
| 01:15:00 | [01:15, 02:15) |

所有窗口都从「每小时第 15 分钟」对齐。

### 3.5 一个完整示例

假设事件时间 `timestamp = 1700000123456`，窗口大小 `size = 60000ms`（1 分钟），offset = 0：
```
start = 1700000123456 - (1700000123456 + 60000) % 60000
      = 1700000123456 - 1700000183456 % 60000
      = 1700000123456 - 23456
      = 1700000100000

end   = start + size = 1700000160000

window = TimeWindow(1700000100000, 1700000160000)
       = [2023-11-14 22:15:00, 2023-11-14 22:16:00)
```

数据被分到对齐到分钟边界的窗口中，与"第一条数据是什么时候到的"完全无关。

---

## 4. 滑动窗口：一个元素多个窗口

### 4.1 核心源码

`SlidingEventTimeWindows` 的 `assignWindows` 与滚动窗口最大的不同，是它返回的是**一个窗口列表**：

```java
// org.apache.flink.streaming.api.windowing.assigners.SlidingEventTimeWindows
@Override
public Collection<TimeWindow> assignWindows(
        Object element, long timestamp, WindowAssignerContext context) {
    if (timestamp > Long.MIN_VALUE) {
        // 预估窗口数 = size / slide
        List<TimeWindow> windows = new ArrayList<>((int) (size / slide));
        // 1. 找到"最近一个开始时间"——按 slide 对齐
        long lastStart = TimeWindow.getWindowStartWithOffset(timestamp, offset, slide);
        // 2. 从 lastStart 往前推，每次减一个 slide，直到 start <= timestamp - size
        for (long start = lastStart; start > timestamp - size; start -= slide) {
            windows.add(new TimeWindow(start, start + size));
        }
        return windows;
    } else {
        throw new RuntimeException(...);
    }
}
```

### 4.2 三个关键点

**第一点**：`getWindowStartWithOffset` 的 windowSize 参数传的是 **`slide`** 而非 `size`。这是因为滑动窗口的边界由 slide 决定（每 slide 启动一个新窗口）。

**第二点**：循环条件 `start > timestamp - size` 决定了向前回溯多少个窗口——只要窗口起点还能"覆盖"到当前时间戳，就把它加入列表。

**第三点**：一个元素被分配到的窗口数量 = `size / slide`（向上取整）。

### 4.3 滑动窗口分配示例

假设 `size = 10s`，`slide = 5s`，`offset = 0`，事件时间戳 `timestamp = 12s`：

```
1. lastStart = 12 - (12 + 5) % 5 = 12 - 2 = 10
2. 循环展开：
   start = 10 → window [10, 20)，start - slide = 5 > 12 - 10 = 2 ✓ 继续
   start = 5  → window [5, 15)， start - slide = 0 > 2 ✗ 停止
```

最终该元素被分配到 **2 个窗口**：`[10, 20)` 和 `[5, 15)`。

可视化：

```
时间轴: 0────5────10────15────20────25
窗口1:        [────────────) [5, 15)
窗口2:             [────────────) [10, 20)
                ▲
                timestamp=12 同时落在两个窗口里
```

### 4.4 边界情况验证

让我们验证一个边界点 `timestamp = 15`（精确落在窗口边界）：
```
lastStart = 15 - (15 + 5) % 5 = 15 - 0 = 15
循环：
  start = 15 → window [15, 25)，start - slide = 10 > 15 - 10 = 5 ✓
  start = 10 → window [10, 20)，start - slide = 5  > 5      ✗ 停止
```

`timestamp = 15` 被分配到 `[15, 25)` 和 `[10, 20)`——它属于 `[10, 20)` 窗口的最后一个时间戳，同时是 `[15, 25)` 窗口的第一个时间戳。这与 `[start, end)` 左闭右开的语义完全一致。

---

## 5. 会话窗口：基于元素动态生成

### 5.1 核心源码

会话窗口的分配逻辑与时间窗口完全不同——它**不预先对齐网格**，而是为每个元素**单独**生成一个临时窗口，长度为 `sessionGap`：

```java
// org.apache.flink.streaming.api.windowing.assigners.EventTimeSessionWindows
@Override
public Collection<TimeWindow> assignWindows(
        Object element, long timestamp, WindowAssignerContext context) {
    return Collections.singletonList(new TimeWindow(timestamp, timestamp + sessionTimeout));
}
```

### 5.2 合并机制

每个元素生成 `[timestamp, timestamp + gap)` 的临时窗口，由 `MergingWindowAssigner` 在后续阶段进行**合并**：

```java
// 调用 TimeWindow.mergeWindows 进行合并
public static void mergeWindows(
        Collection<TimeWindow> windows,
        MergingWindowAssigner.MergeCallback<TimeWindow> c) {
    // 按 start 排序
    // 遍历窗口，相邻窗口若 intersects 则 cover 为更大的窗口
    // 最终把多个小窗口合并为一个大会话窗口
}
```

合并示意：

```
原始（每元素一个临时窗口，gap=5）：
  evt@10 → [10, 15)
  evt@13 → [13, 18)   ← 与 [10, 15) 相交，合并为 [10, 18)
  evt@16 → [16, 21)   ← 与 [10, 18) 相交，合并为 [10, 21)
  evt@30 → [30, 35)   ← 与前面不相交，新会话窗口
```

> 会话窗口是 Flink 中唯一**实现了 `MergingWindowAssigner`** 的内置分配器。详见 [源码解读 \| Flink DataStream 窗口合并](https://smartsi.blog.csdn.net/article/details/...)。

---

## 6. 处理时间窗口

`TumblingProcessingTimeWindows` 的逻辑与 `TumblingEventTimeWindows` 几乎一致，唯一差别是使用**当前处理时间**作为时间戳：

```java
// TumblingProcessingTimeWindows.assignWindows
@Override
public Collection<TimeWindow> assignWindows(
        Object element, long timestamp, WindowAssignerContext context) {
    final long now = context.getCurrentProcessingTime();    // ← 关键差异
    if (staggerOffset == null) {
        staggerOffset = windowStagger.getStaggerOffset(now, size);
    }
    long start = TimeWindow.getWindowStartWithOffset(
            now, (globalOffset + staggerOffset) % size, size);
    return Collections.singletonList(new TimeWindow(start, start + size));
}
```

> 处理时间下，`assignWindows` 入参的 `timestamp` 被**忽略**——它直接调用 `context.getCurrentProcessingTime()`，因为处理时间窗口的归属由"当下系统时钟"决定，与数据自身携带的时间戳无关。

---

## 7. 窗口分配在算子中的位置

理解 `assignWindows` 之后，我们再看它在窗口算子 `WindowOperator` 中的调用时机：

```java
// org.apache.flink.streaming.runtime.operators.windowing.WindowOperator
@Override
public void processElement(StreamRecord<IN> element) throws Exception {
    final Collection<W> elementWindows = windowAssigner.assignWindows(
            element.getValue(),
            element.getTimestamp(),       // ← 元素时间戳
            windowAssignerContext);

    // 遍历每个分配到的窗口，更新状态、注册定时器
    for (W window : elementWindows) {
        // 1. 加入窗口状态
        windowState.add(element.getValue());
        // 2. 调用 Trigger.onElement 决定是否触发
        TriggerResult triggerResult = triggerContext.onElement(element);
        // 3. 注册窗口结束时的清理定时器
        registerCleanupTimer(window);
    }
}
```

调用链路：

```
StreamRecord 到达 WindowOperator
        │
        ▼
WindowOperator.processElement()
        │
        ▼
windowAssigner.assignWindows(value, timestamp, ctx)  ← 本文核心
        │
        ▼
返回 Collection<TimeWindow>
        │
        ▼
对每个窗口：状态更新 + Trigger 评估 + 定时器注册
```

---

## 8. 常见问题答疑

### 8.1 窗口的开始时间是从第一条数据决定的吗？

**不是**。窗口起点完全由 `getWindowStartWithOffset(timestamp, offset, size)` 计算，与"哪条数据先到"无关。这就保证了：
- **可重放性**：相同的数据流，多次执行会得到完全一致的窗口划分
- **跨实例一致性**：不同 Subtask 看到相同 key 的数据时，窗口边界完全相同
- **可并行**：每个分区独立计算窗口起点，无需协调

### 8.2 `getEnd()` 返回的时间戳到底属不属于窗口？

**不属于**。窗口是左闭右开 `[start, end)`，`getEnd()` 是"不属于该窗口的第一个时间戳"。例如 `[1000, 2000)`：
- 时间戳 1000 → 属于该窗口
- 时间戳 1999 → 属于该窗口
- 时间戳 2000 → **不属于**，属于下一个窗口

如果你要拿"窗口内最大有效时间戳"，应该用 `maxTimestamp() = end - 1`。

### 8.3 为什么用 `(timestamp - offset + windowSize) % windowSize` 而不是直接 `timestamp % windowSize`？

两个原因：
1. **支持 offset**：减去 `offset` 可以将窗口边界整体平移
2. **处理负数取模**：当 `timestamp - offset < 0` 时，Java 的 `%` 会返回负数，`+ windowSize` 后再取模可以保证结果非负

### 8.4 同一条数据会被分到多少个窗口？

| 窗口类型 | 数量 |
|----------|------|
| 滚动窗口 | 1 |
| 滑动窗口 | `size / slide`（向上取整） |
| 会话窗口 | 1（先生成单元素窗口，后续合并） |
| 全局窗口 | 1 |

### 8.5 ProcessingTime 窗口下传入的 timestamp 还有用吗？

**没用**。`TumblingProcessingTimeWindows.assignWindows` 内部直接调用 `context.getCurrentProcessingTime()`，完全不使用入参的 timestamp。这就是为什么处理时间窗口下不需要 `assignTimestampsAndWatermarks`。

---

## 9. 总结

Flink 窗口分配的核心逻辑：

1. **统一入口**：所有窗口的分配都通过 `WindowAssigner.assignWindows()` 完成
2. **时间窗口**：使用 `TimeWindow.getWindowStartWithOffset(timestamp, offset, size)` 静态计算窗口起点，与数据到达顺序无关
3. **左闭右开**：`TimeWindow [start, end)`，`getEnd()` 是开区间端点，`maxTimestamp() = end - 1`
4. **滚动窗口**：1 个元素 → 1 个窗口
5. **滑动窗口**：1 个元素 → `size / slide` 个窗口（从 lastStart 向前回溯）
6. **会话窗口**：先为每个元素生成临时窗口 `[ts, ts + gap)`，再通过 `mergeWindows` 合并相交窗口
7. **处理时间**：忽略数据时间戳，使用 `context.getCurrentProcessingTime()`

掌握了 `getWindowStartWithOffset` 这一行公式，几乎所有 Flink 时间窗口的"为什么这条数据落到了这个窗口"的疑问都能迎刃而解。

| 公式 | 用途 |
|------|------|
| `start = timestamp - (timestamp - offset + windowSize) % windowSize` | 计算窗口起点 |
| `end = start + size` | 滚动/滑动窗口结束时间 |
| `maxTimestamp = end - 1` | 仍属于该窗口的最大时间戳 |

> 进一步阅读：[Flink 窗口分配器 WindowAssigner](https://smartsi.blog.csdn.net/article/details/126613705)、[Flink Watermark 机制](https://smartsi.blog.csdn.net/article/details/126689246)。
