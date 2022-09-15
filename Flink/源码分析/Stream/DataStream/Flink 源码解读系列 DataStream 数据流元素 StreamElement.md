---
layout: post
author: sjf0115
title: Flink 源码解读系列 DataStream 数据流元素 StreamElement
date: 2022-09-14 14:47:01
tags:
  - Flink

categories: Flink
permalink: flink-stream-code-stream-element
---

Flink 中使用 StreamElement 来表示数据流元素：
```java
public abstract class StreamElement {
    // 是否是 Watermark
    public final boolean isWatermark() {
        return getClass() == Watermark.class;
    }
    // 是否是数据流状态 StreamStatus
    public final boolean isStreamStatus() {
        return getClass() == StreamStatus.class;
    }
    // 是否是数据记录 StreamRecord
    public final boolean isRecord() {
        return getClass() == StreamRecord.class;
    }
    // 是否是延迟标记 LatencyMarker
    public final boolean isLatencyMarker() {
        return getClass() == LatencyMarker.class;
    }
    // 转换为数据记录 StreamRecord
    public final <E> StreamRecord<E> asRecord() {
        return (StreamRecord<E>) this;
    }
    // 转换为 Watermark
    public final Watermark asWatermark() {
        return (Watermark) this;
    }
    // 转换为数据流状态 StreamStatus
    public final StreamStatus asStreamStatus() {
        return (StreamStatus) this;
    }
    // 转换为延迟标记 LatencyMarker
    public final LatencyMarker asLatencyMarker() {
        return (LatencyMarker) this;
    }
}
```
StreamElement 是一个抽象类，其下有数据记录 StreamRecord、延迟标记 Latency Marker、Watermark、数据流状态 StreamStatus 4 种类型，如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-code-stream-element-1.png?raw=true)

在执行层面上，4 种数据流元素都被序列化成二进制数据，形成混合的数据流，在算子中将混合数据流中的数据流元素反序列化出来，根据其类型分别进行处理。

下面我们详细看一下每种数据流元素。

## 1. 数据记录 StreamRecord

StreamRecord 表示数据流中的一条记录（或者叫作一个事件）。数据记录 StreamRecord 中包含一个数据值以及一个可选的事件戳：
```java
public final class StreamRecord<T> extends StreamElement {
    // 数据记录值
    private T value;
    // 时间戳
    private long timestamp;
    private boolean hasTimestamp;

    public StreamRecord(T value) {
        this.value = value;
    }
    public StreamRecord(T value, long timestamp) {
        this.value = value;
        this.timestamp = timestamp;
        this.hasTimestamp = true;
    }
}
```
> org.apache.flink.streaming.runtime.streamrecord

从上面可以看出 StreamRecord 本质上是一个数据值和可选事件戳的封装。此外，还提供了一些工具方法：
```java
// 替换数据记录的值 可以改变数据类型
public <X> StreamRecord<X> replace(X element) {
    this.value = (T) element;
    return (StreamRecord<X>) this;
}
// 替换数据记录的值和时间戳
public <X> StreamRecord<X> replace(X value, long timestamp) {
    this.timestamp = timestamp;
    this.value = (T) value;
    this.hasTimestamp = true;
    return (StreamRecord<X>) this;
}
// 创建数据记录的一个副本 仅复制时间戳字段 记录值用新传递的值覆盖
public StreamRecord<T> copy(T valueCopy) {
    StreamRecord<T> copy = new StreamRecord<>(valueCopy);
    copy.timestamp = this.timestamp;
    copy.hasTimestamp = this.hasTimestamp;
    return copy;
}
// 将此数据记录复制到新的数据记录中 仅复制时间戳字段 记录值用新传递的值覆盖
public void copyTo(T valueCopy, StreamRecord<T> target) {
    target.value = valueCopy;
    target.timestamp = this.timestamp;
    target.hasTimestamp = this.hasTimestamp;
}
// 为数据记录设置时间戳
public void setTimestamp(long timestamp) {
    this.timestamp = timestamp;
    this.hasTimestamp = true;
}
// 擦除数据记录中的时间戳
public void eraseTimestamp() {
    this.hasTimestamp = false;
}
```

## 2. 延迟标记 LatencyMarker

延迟标记 LatencyMarker 是一种特殊的记录类型，用来近似评估延迟。在 Source 中创建，并向下游发送，在 Sink 节点中使用 LatencyMarker 估计数据在整个 DAG 图中流转花费的时间，用来近似地评估总体上的处理延迟。延迟标记 LatencyMarker 中包含一个在 Source 算子中周期性地生产的时间戳、算子 Id 以及 Source 算子所在的 Task 下标：
```java
public final class LatencyMarker extends StreamElement {
    // 时间戳
    private final long markedTime;
    // 算子Id
    private final OperatorID operatorId;
    // Task 下标
    private final int subtaskIndex;
    // 构造器
    public LatencyMarker(long markedTime, OperatorID operatorId, int subtaskIndex) {
        this.markedTime = markedTime;
        this.operatorId = operatorId;
        this.subtaskIndex = subtaskIndex;
    }
    ...
}
```
> org.apache.flink.streaming.runtime.streamrecord

## 3. Watermark

Watermark 也是一种特殊的记录类型，表示一个时间戳，用来告诉算子所有时间早于等于 Watermark 的数据记录都已经到达，不会再有比 Watermark 更早的数据记录了。算子可以根据 Watermark 触发窗口的计算、清理资源等。具体可以详细阅读[Flink Watermark 机制](https://smartsi.blog.csdn.net/article/details/126689246)。Watermark 内部只包含一个时间戳：
```java
public final class Watermark extends StreamElement {
    // 时间戳
    private final long timestamp;
    // 根据时间戳创建 Watermark
    public Watermark(long timestamp) {
        this.timestamp = timestamp;
    }
    ...
}
```
> org.apache.flink.streaming.api.watermark

## 4. 数据流状态 StreamStatus

数据流状态 StreamStatus 也是一种特殊的记录类型，用来通知 Task 是否会继续接收到上游的记录或者 Watermark。StreamStatus 在 Source 算子中生成，并向下游传递。StreamStatus 内部只包含一个状态值 status：
```java
public final class StreamStatus extends StreamElement {
    public static final int IDLE_STATUS = -1;
    public static final int ACTIVE_STATUS = 0;
    public static final StreamStatus IDLE = new StreamStatus(IDLE_STATUS);
    public static final StreamStatus ACTIVE = new StreamStatus(ACTIVE_STATUS);
    // 状态值
    public final int status;
    // 根据状态值创建数据流状态
    public StreamStatus(int status) {
        if (status != IDLE_STATUS && status != ACTIVE_STATUS) {
            // 状态值只能是 0 和 -1
            throw new IllegalArgumentException(xxx);
        }
        this.status = status;
    }
    ...
}
```
> org.apache.flink.streaming.runtime.streamstatus

状态值 status 只能是 0 和 -1，分别对应 StreamStatus 的两种状态：空闲状态（IDLE）和活动状态（ACTIVE）。
