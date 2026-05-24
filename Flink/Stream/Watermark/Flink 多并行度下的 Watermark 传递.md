---
layout: post
author: sjf0115
title: Flink 多并行度下的 Watermark 传递
date: 2026-05-18 14:30:01
tags:
  - Flink

categories: Flink
permalink: flink-stream-watermark-propagation-in-parallel
---

> Flink 版本：1.13

## 1. 引言

在 [Flink Watermark 机制](https://smartsi.blog.csdn.net/article/details/112553662) 中我们已经了解了 Watermark 的基本概念——它用于衡量事件时间的推进、解决乱序问题。在单并行度场景下，Watermark 的传递比较直观：Source 生成 Watermark，逐步往下游传递即可。

但在生产环境中，我们通常会设置多并行度。此时一个下游算子的子任务可能同时接收来自多个上游子任务的数据和 Watermark。**当不同输入通道的 Watermark 不一致时，下游算子该以哪个 Watermark 为准？** 这就是本文要深入探讨的核心问题：**多并行度下的 Watermark 传递机制**。

---

## 2. 问题场景

假设有如下拓扑：Source（并行度 2）→ Map（并行度 2）→ Window（并行度 2）。

```
Source[0] ──┬──▶ Window[0]
            ├──▶ Window[1]
Source[1] ──┤
            ├──▶ Window[0]
            └──▶ Window[1]
```

Window[0] 同时接收来自 Source[0] 和 Source[1] 的数据。如果 Source[0] 的 Watermark 已经推进到 `W(10)`，而 Source[1] 的 Watermark 还停留在 `W(3)`，那么 Window[0] 当前的 Watermark 应该是多少？

**答案：取所有输入通道 Watermark 的最小值，即 `W(3)`。**

这是因为 Watermark 的语义是"所有时间戳小于等于 Watermark 的事件都已到达"。如果某个通道的 Watermark 仍为 `W(3)`，就意味着时间戳在 3 到 10 之间的事件仍可能从该通道到达，不能贸然推进整体 Watermark。

---

## 3. 整体传递流程

Flink 1.13 中 Watermark 在多并行度下的传递遵循如下流程：

```
                    ┌────────────────────────────────────────┐
                    │         下游算子 子任务(SubTask)          │
                    │                                        │
  上游 SubTask 0 ──▶│  InputChannel 0 ─┐                     │
                    │                  │  StatusWatermarkValve│
  上游 SubTask 1 ──▶│  InputChannel 1 ─┤  (取 aligned 通道    │──▶ 输出 Watermark
                    │                  │   的最小值)           │    给下游
  上游 SubTask 2 ──▶│  InputChannel 2 ─┘                     │
                    │                                        │
                    └────────────────────────────────────────┘
```

**关键步骤**：

1. 每个输入通道（InputChannel）独立维护自己收到的最新 Watermark
2. 当某个通道收到新 Watermark 时，更新该通道的 Watermark 值
3. 从所有**已对齐（aligned）** 的通道中取 Watermark **最小值**
4. 如果这个最小值**大于**上一次输出的 Watermark，则向下游发送新的 Watermark
5. 处于 **IDLE（空闲）** 状态的通道不参与最小值计算

---

## 4. 核心源码解析

### 4.1 入口：AbstractStreamTaskNetworkInput

当数据从网络到达算子子任务时，由 `AbstractStreamTaskNetworkInput` 负责反序列化并分发。在 `processElement` 方法中，判断元素类型并路由：

```java
// AbstractStreamTaskNetworkInput.java（Flink 1.13）
private void processElement(StreamElement recordOrMark, DataOutput<T> output) throws Exception {
    if (recordOrMark.isRecord()) {
        output.emitRecord(recordOrMark.asRecord());
    } else if (recordOrMark.isWatermark()) {
        // Watermark 交给 StatusWatermarkValve 处理
        statusWatermarkValve.inputWatermark(
            recordOrMark.asWatermark(),
            flattenedChannelIndices.get(lastChannel),
            output);
    } else if (recordOrMark.isLatencyMarker()) {
        output.emitLatencyMarker(recordOrMark.asLatencyMarker());
    } else if (recordOrMark.isStreamStatus()) {
        // StreamStatus（IDLE/ACTIVE）也交给 Valve 处理
        statusWatermarkValve.inputStreamStatus(
            recordOrMark.asStreamStatus(),
            flattenedChannelIndices.get(lastChannel),
            output);
    }
}
```

**要点**：Watermark 不是直接转发给下游，而是交给 `StatusWatermarkValve`（水位线阀门）统一协调。

### 4.2 核心：StatusWatermarkValve

> org.apache.flink.streaming.runtime.streamstatus.StatusWatermarkValve

`StatusWatermarkValve` 是 Flink 1.13 中处理多输入通道 Watermark 传递的 **核心组件**。

#### 4.2.1 数据结构

```java
public class StatusWatermarkValve {
    // 每个输入通道的状态
    private final InputChannelStatus[] channelStatuses;
    // 上一次输出的 Watermark 值
    private long lastOutputWatermark;
    // 上一次输出的流状态
    private StreamStatus lastOutputStreamStatus;
}
```

每个 `InputChannelStatus` 维护了该通道的三个关键信息：
```java
private static class InputChannelStatus {
    // 该通道当前最新的 Watermark
    long watermark;
    // 该通道的状态：ACTIVE 或 IDLE
    StreamStatus streamStatus;
    // 该通道的 Watermark 是否已对齐
    boolean isWatermarkAligned;
}
```

#### 4.2.2 初始化

构造时，所有通道初始化为：Watermark = `Long.MIN_VALUE`，状态 = `ACTIVE`，对齐状态 = `true`。
```java
public StatusWatermarkValve(int numInputChannels) {
    checkArgument(numInputChannels > 0);
    this.channelStatuses = new InputChannelStatus[numInputChannels];
    for (int i = 0; i < numInputChannels; i++) {
        channelStatuses[i] = new InputChannelStatus();
        channelStatuses[i].watermark = Long.MIN_VALUE;
        channelStatuses[i].streamStatus = StreamStatus.ACTIVE;
        channelStatuses[i].isWatermarkAligned = true;
    }
    this.lastOutputWatermark = Long.MIN_VALUE;
    this.lastOutputStreamStatus = StreamStatus.ACTIVE;
}
```

#### 4.2.3 inputWatermark：接收 Watermark

当某个通道收到一个新的 Watermark 时：
```java
public void inputWatermark(Watermark watermark, int channelIndex, DataOutput<?> output) throws Exception {
    // 前置条件：上一次输出的流状态处于非空闲状态 且 该输入通道目前处于非空闲状态
    if (lastOutputStreamStatus.isActive() && channelStatuses[channelIndex].streamStatus.isActive()) {
        long watermarkMillis = watermark.getTimestamp();

        // 忽略比当前通道已有 Watermark 更小的值（Watermark 只能单调递增）
        if (watermarkMillis > channelStatuses[channelIndex].watermark) {
            // 更新该通道的 Watermark
            channelStatuses[channelIndex].watermark = watermarkMillis;

            // 如果该通道之前未对齐，检查现在是否已追上全局 Watermark
            if (!channelStatuses[channelIndex].isWatermarkAligned && watermarkMillis >= lastOutputWatermark) {
                channelStatuses[channelIndex].isWatermarkAligned = true;
            }

            // 尝试计算新的全局最小 Watermark 并输出
            findAndOutputNewMinWatermarkAcrossAlignedChannels(output);
        }
    }
}
```

**核心逻辑**：
1. **空闲状态通道的 Watermark 被忽略**：如果该通道或上一次输出的流状态处于空闲状态，直接跳过
2. **Watermark 只能单调递增**：如果新 Watermark ≤ 当前通道已有值，忽略
3. **对齐恢复**：之前因落后而标记为"未对齐"的通道，一旦追上 `lastOutputWatermark`，重新标记为对齐
4. **触发全局 Watermark 计算**

#### 4.2.4 findAndOutputNewMinWatermarkAcrossAlignedChannels：计算全局最小 Watermark

```java
private void findAndOutputNewMinWatermarkAcrossAlignedChannels(DataOutput<?> output) throws Exception {
    long newMinWatermark = Long.MAX_VALUE;
    boolean hasAlignedChannels = false;

    // 遍历所有通道，只考虑已对齐的通道
    for (InputChannelStatus channelStatus : channelStatuses) {
        if (channelStatus.isWatermarkAligned) {
            hasAlignedChannels = true;
            newMinWatermark = Math.min(channelStatus.watermark, newMinWatermark);
        }
    }

    // 只有在存在对齐通道 且 新最小值大于上次输出值时，才输出新 Watermark
    if (hasAlignedChannels && newMinWatermark > lastOutputWatermark) {
        lastOutputWatermark = newMinWatermark;
        output.emitWatermark(new Watermark(lastOutputWatermark));
    }
}
```

**关键要点**：

| 条件 | 说明 |
|------|------|
| 只考虑 `isWatermarkAligned = true` 的通道 | 空闲状态或严重落后的通道不参与 |
| `newMinWatermark > lastOutputWatermark` | 保证输出的 Watermark 严格单调递增 |
| 取所有对齐通道的 **最小值** | 确保不会跳过任何可能到达的事件 |

---

## 5. 空闲状态通道处理

### 5.1 问题：某个通道长期无数据

在实际场景中，某些 Source 子任务可能暂时没有数据（如 Kafka Partition 暂无消息）。如果严格取所有通道的最小 Watermark，那个"沉默"通道的 Watermark 将永远停留在 `Long.MIN_VALUE`，导致整体 Watermark **永远无法推进**。

### 5.2 解决方案：StreamStatus（IDLE / ACTIVE）

Flink 1.13 通过 `StreamStatus` 机制解决此问题。Source 可以将自己标记为 IDLE 空闲状态：
```java
// 当 Source 检测到暂时无数据时，发送 IDLE 状态
ctx.emitStreamStatus(StreamStatus.IDLE);

// 当 Source 重新有数据时，发送 ACTIVE 状态
ctx.emitStreamStatus(StreamStatus.ACTIVE);
```

### 5.3 inputStreamStatus 源码

```java
public void inputStreamStatus(StreamStatus streamStatus, int channelIndex, DataOutput<?> output)
        throws Exception {

    if (streamStatus.isIdle() && channelStatuses[channelIndex].streamStatus.isActive()) {
        // ACTIVE → IDLE：该通道标记为非对齐
        channelStatuses[channelIndex].streamStatus = StreamStatus.IDLE;
        channelStatuses[channelIndex].isWatermarkAligned = false;

        // 如果所有通道都变为 IDLE
        if (!InputChannelStatus.hasActiveChannels(channelStatuses)) {
            // 输出所有通道中的最大 Watermark（flush）
            if (channelStatuses[channelIndex].watermark == lastOutputWatermark) {
                findAndOutputMaxWatermarkAcrossAllChannels(output);
            }
            // 整体标记为 IDLE
            lastOutputStreamStatus = StreamStatus.IDLE;
            output.emitStreamStatus(lastOutputStreamStatus);
        } else if (channelStatuses[channelIndex].watermark == lastOutputWatermark) {
            // 如果变为 IDLE 的通道恰好是当前最小值的持有者
            // 重新计算剩余对齐通道的最小 Watermark（可能可以推进了）
            findAndOutputNewMinWatermarkAcrossAlignedChannels(output);
        }

    } else if (streamStatus.isActive() && channelStatuses[channelIndex].streamStatus.isIdle()) {
        // IDLE → ACTIVE：恢复活跃
        channelStatuses[channelIndex].streamStatus = StreamStatus.ACTIVE;

        // 如果该通道的 Watermark 已经 >= 全局输出值，直接标记为对齐
        if (channelStatuses[channelIndex].watermark >= lastOutputWatermark) {
            channelStatuses[channelIndex].isWatermarkAligned = true;
        }

        // 如果之前整体是 IDLE，现在有通道活跃了，恢复为 ACTIVE
        if (lastOutputStreamStatus.isIdle()) {
            lastOutputStreamStatus = StreamStatus.ACTIVE;
            output.emitStreamStatus(lastOutputStreamStatus);
        }
    }
}
```

**状态转换流程**：

```
通道 ACTIVE → IDLE:
  1. 标记通道为 IDLE + 非对齐
  2. 该通道不再参与最小 Watermark 计算
  3. 如果所有通道都 IDLE → 整体输出 IDLE
  4. 否则重新计算最小 Watermark（可能推进）

通道 IDLE → ACTIVE:
  1. 标记通道为 ACTIVE
  2. 如果其 Watermark >= lastOutputWatermark → 标记为对齐
  3. 如果整体之前是 IDLE → 恢复为 ACTIVE
```

### 5.4 对齐（Aligned）机制

`isWatermarkAligned` 的作用是**避免刚恢复的通道因旧 Watermark 把全局 Watermark 拉回去**：

- 当通道从 IDLE 恢复为 ACTIVE 时，如果其 Watermark 落后于 `lastOutputWatermark`，则标记为"未对齐"
- 未对齐的通道**不参与最小值计算**
- 一旦该通道的 Watermark 追上 `lastOutputWatermark`，重新标记为对齐

这样就避免了"全局 Watermark 倒退"的问题。

---

## 6. findAndOutputMaxWatermarkAcrossAllChannels

当所有通道都变为 IDLE 时，Flink 会将所有通道中的**最大 Watermark** flush 出去：

```java
private void findAndOutputMaxWatermarkAcrossAllChannels(DataOutput<?> output) throws Exception {
    long maxWatermark = Long.MIN_VALUE;
    for (InputChannelStatus channelStatus : channelStatuses) {
        maxWatermark = Math.max(channelStatus.watermark, maxWatermark);
    }
    if (maxWatermark > lastOutputWatermark) {
        lastOutputWatermark = maxWatermark;
        output.emitWatermark(new Watermark(lastOutputWatermark));
    }
}
```

**为什么此时取最大值？** 因为所有通道都 IDLE 意味着不再有新事件到达，此时可以安全地把 Watermark 推进到已知最大值，触发可能在等待的窗口计算。

---

## 7. 图解传递示例

假设 Window 算子有 2 个输入通道，初始状态：

```
┌──────────────────────────────────────────────────────────────────┐
│  Channel 0: watermark = Long.MIN_VALUE, aligned = true, ACTIVE  │
│  Channel 1: watermark = Long.MIN_VALUE, aligned = true, ACTIVE  │
│  lastOutputWatermark = Long.MIN_VALUE                            │
└──────────────────────────────────────────────────────────────────┘
```

**Step 1**：Channel 0 收到 `W(5)`

```
Channel 0: watermark = 5, aligned = true
Channel 1: watermark = Long.MIN_VALUE, aligned = true
最小值 = Long.MIN_VALUE → 不大于 lastOutputWatermark → 不输出
```

**Step 2**：Channel 1 收到 `W(3)`

```
Channel 0: watermark = 5, aligned = true
Channel 1: watermark = 3, aligned = true
最小值 = 3 → 大于 Long.MIN_VALUE → 输出 W(3)
lastOutputWatermark = 3
```

**Step 3**：Channel 0 收到 `W(8)`

```
Channel 0: watermark = 8, aligned = true
Channel 1: watermark = 3, aligned = true
最小值 = 3 → 等于 lastOutputWatermark → 不输出
```

**Step 4**：Channel 1 收到 `W(7)`

```
Channel 0: watermark = 8, aligned = true
Channel 1: watermark = 7, aligned = true
最小值 = 7 → 大于 lastOutputWatermark(3) → 输出 W(7)
lastOutputWatermark = 7
```

**Step 5**：Channel 1 变为 IDLE

```
Channel 0: watermark = 8, aligned = true, ACTIVE
Channel 1: watermark = 7, aligned = false, IDLE   ← 不参与计算
最小值 = 8（只看 Channel 0）→ 大于 7 → 输出 W(8)
lastOutputWatermark = 8
```

**Step 6**：Channel 1 恢复 ACTIVE，当前 watermark = 7

```
Channel 0: watermark = 8, aligned = true, ACTIVE
Channel 1: watermark = 7, aligned = false, ACTIVE  ← 7 < 8，未对齐
最小值 = 8（只看对齐的 Channel 0）→ 等于 lastOutputWatermark → 不输出
```

**Step 7**：Channel 1 收到 `W(10)`

```
Channel 1: watermark = 10 >= lastOutputWatermark(8) → 重新对齐
Channel 0: watermark = 8, aligned = true
Channel 1: watermark = 10, aligned = true
最小值 = 8 → 等于 lastOutputWatermark → 不输出
```

---

## 8. 关键设计总结

| 设计决策 | 原因 |
|---------|------|
| 取对齐通道的**最小值** | 保证 Watermark 语义正确——不会跳过任何可能到达的事件 |
| Watermark **单调递增** | 下游算子依赖 Watermark 单调递增来触发窗口，绝不能倒退 |
| IDLE 通道**不参与**最小值计算 | 避免无数据通道阻塞全局进度 |
| 恢复通道先标记**未对齐** | 防止旧 Watermark 把全局值拉回 |
| 全部 IDLE 时取**最大值** flush | 确保在所有输入结束时能触发待处理的窗口 |
| 每次收到新 Watermark 时**立即尝试推进** | 最小延迟地传递时间进度 |

---

## 9. 对窗口计算的影响

多并行度下的 Watermark 传递直接影响 **窗口触发时机**：

### 9.1 正常情况

如果所有上游子任务的事件时间推进速度一致，Watermark 将以**最慢通道**的速度推进。窗口会在所有通道的数据"对齐"后触发。

### 9.2 数据倾斜导致 Watermark 延迟

如果某个上游子任务处理速度慢或数据分布不均：

```
Source[0]: Watermark 快速推进到 W(100)
Source[1]: Watermark 停留在 W(10)

→ 下游窗口的 Watermark = min(100, 10) = W(10)
→ [0, 10] 的窗口可以触发，但 [10, 20]... [90, 100] 的窗口都在等待
```

**后果**：状态膨胀、窗口延迟触发、Checkpoint 变大。

### 9.3 解决方案

| 方案 | 说明 |
|------|------|
| Source IDLE 标记 | 无数据的 Source 及时发送 IDLE，让其不阻塞全局 |
| Watermark 对齐（Flink 1.15+） | 在 Source 层面协调 Watermark 对齐，限制快通道的推进速度 |
| 合理设置并行度 | 避免某些子任务分配不到数据 |
| 数据打散 | 避免热 Key 导致某个分区处理缓慢 |

---

## 10. 总结

本文基于 Flink 1.13 源码，详细剖析了多并行度下 Watermark 的传递机制：

1. **核心组件**：`StatusWatermarkValve` 负责协调多输入通道的 Watermark
2. **核心逻辑**：取所有已对齐通道的 Watermark 最小值，保证 Watermark 语义正确和单调递增
3. **IDLE 机制**：通过 `StreamStatus` 标记空闲通道，避免无数据通道阻塞全局 Watermark 推进
4. **对齐机制**：恢复活跃的通道需要 Watermark 追上全局值后才参与最小值计算，防止 Watermark 倒退
5. **全 IDLE flush**：所有通道都 IDLE 时取最大值输出，确保窗口能够触发

理解这个机制对于排查生产中的"窗口迟迟不触发"、"Watermark 不推进"等问题至关重要。

---

参考：
- [Flink 1.13 StatusWatermarkValve 源码](https://github.com/apache/flink/blob/release-1.13/flink-streaming-java/src/main/java/org/apache/flink/streaming/runtime/streamstatus/StatusWatermarkValve.java)
- [Flink 1.13 AbstractStreamTaskNetworkInput 源码](https://github.com/apache/flink/blob/release-1.13/flink-streaming-java/src/main/java/org/apache/flink/streaming/runtime/io/AbstractStreamTaskNetworkInput.java)
- [Timely Stream Processing - Apache Flink](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/concepts/time/)
