---
layout: post
author: sjf0115
title: Storm Core 中的窗口机制
date: 2018-12-14 21:33:01
tags:
  - Storm

categories: Storm
permalink: understanding-the-windows-of-storm-core
---

Storm Core 支持处理窗口内的元组。窗口需要指定如下两个参数：
- 窗口长度: 窗口的长度或持续时间。
- 滑动间隔: 窗口滑动的间隔。

### 1. 滑动窗口

元组分组在不同窗口中，并根据滑动间隔进行滑动。一个元组可以属于多个窗口。例如，一个窗口长度为 10 秒，滑动间隔为 5 秒的滑动窗口如下：
![]()

窗口每 5 秒进行一次评估，第一个窗口会与第二个窗口重叠一些元组。

### 2. 滚动窗口

元组基于时间或计数分组在不同的窗口中。任何一个元组只属于其中一个窗口。例如，一个基于时间窗口长度为 5 秒的滚动窗口如下：
![]()

窗口每 5 秒进行一次评估，没有窗口重叠。Storm 支持将元组个数或持续时间作为窗口长度和滑动间隔。

### 3. 窗口配置

需要窗口支持的可以实现 `IWindowedBolt` 接口:
```java
public interface IWindowedBolt extends IComponent {
    void prepare(Map stormConf, TopologyContext context, OutputCollector collector);
    void execute(TupleWindow inputWindow);
    void cleanup();
}
```
每次激活窗口时，都会调用 `execute` 方法。`TupleWindow` 参数提供了对窗口中当前元组，过期元组以及自上一个窗口以来添加的新元组的访问，这对于高效的窗口计算非常有用。

需要窗口支持的 Bolt 通常会继承 `BaseWindowedBolt`，它具有指定窗口长度和滑动间隔的api:
```java
public class SlidingWindowBolt extends BaseWindowedBolt {
    private OutputCollector collector;

    @Override
    public void prepare(Map stormConf, TopologyContext context, OutputCollector collector) {
        this.collector = collector;
    }

    @Override
    public void execute(TupleWindow inputWindow) {
      for(Tuple tuple: inputWindow.get()) {
        // do the windowing computation
        ...
      }
      // emit the results
      collector.emit(new Values(computedValue));
    }
}

public static void main(String[] args) {
    TopologyBuilder builder = new TopologyBuilder();
    builder.setSpout("spout", new RandomSentenceSpout(), 1);
    builder.setBolt("slidingwindowbolt", new SlidingWindowBolt().withWindow(new Count(30), new Count(10)), 1).shuffleGrouping("spout");

    Config conf = new Config();
    conf.setDebug(true);
    conf.setNumWorkers(1);

    StormSubmitter.submitTopologyWithProgressBar(args[0], conf, builder.createTopology());
}
```
支持以下窗口配置:
```java
withWindow(Count windowLength, Count slidingInterval)
基于元组个数的滑动窗口，在 `slidingInterval` 个元组到来之后进行滑动。

withWindow(Count windowLength)
基于元组个数的滑动窗口，每当一个元组到来都会进行滑动。

withWindow(Count windowLength, Duration slidingInterval)
基于元组个数的滑动窗口，在 `slidingInterval` 时间之后进行滑动。

withWindow(Duration windowLength, Duration slidingInterval)
基于持续时间的滑动窗口，在 `slidingInterval` 时间之后进行滑动。

withWindow(Duration windowLength)
基于持续时间的滑动窗口，每当一个元组到来都会进行滑动。

withWindow(Duration windowLength, Count slidingInterval)
基于持续时间的滑动窗口，在 `slidingInterval` 个元组到来之后进行滑动。

withTumblingWindow(BaseWindowedBolt.Count count)
基于元组个数的滚动窗口，在指定个元组之后进行滚动。

withTumblingWindow(BaseWindowedBolt.Duration duration)
基于持续时间的滚动窗口，在指定持续时间之后进行滚动。
```

### 4. 元组时间戳与无序元组

默认情况下，在窗口中进行追踪的时间戳是 bolt 处理元组的时间。窗口计算是基于正在处理的时间戳进行的。Storm 支持基于源生成的时间戳进行追踪窗口。
> 可以参考[Flink1.4 事件时间与处理时间](http://smartsi.club/flink-stream-event-time-and-processing-time.html)

```java
/**
* Specify a field in the tuple that represents the timestamp as a long value. If this
* field is not present in the incoming tuple, an {@link IllegalArgumentException} will be thrown.
*
* @param fieldName the name of the field that contains the timestamp
*/
public BaseWindowedBolt withTimestampField(String fieldName)
```

将从传入的元组中查找上述 fieldName 的值，并考虑进行窗口计算。如果元组中不存在该字段，将会抛出异常。或者可以使用 `TimestampExtractor` 从元组中提取出时间戳值（例如，从元组内的嵌套字段中提取时间戳）:
```java
/**
* Specify the timestamp extractor implementation.
*
* @param timestampExtractor the {@link TimestampExtractor} implementation
*/
public BaseWindowedBolt withTimestampExtractor(TimestampExtractor timestampExtractor)
```
除了指定时间戳字段和提取器之外，你还可以指定时间延迟参数，该参数表示具有乱序时间戳的元组的最大时间限制(译者译：可能延迟的最大时间)：
```java
/**
* Specify the maximum time lag of the tuple timestamp in milliseconds. It means that the tuple timestamps
* cannot be out of order by more than this amount.
*
* @param duration the max lag duration
*/
public BaseWindowedBolt withLag(Duration duration)
```
### 5. 保证

目前 Storm Core 中的窗口函数提供至少一次保证。从 Bolt `execute(TupleWindow inputWindow)` 方法发出的值会自动锚定到 inputWindow 中的所有元组。下游 Bolt 可以对所接收的元组(即从窗口 Bolt 发出的元组)进行 ack 以完成元组树。如果不是，将重放元组并重新评估窗口计算。

窗口中的元组在到期后会自动被 ack，即当它们在 `windowLength + slidingInterval` 之后掉出窗口时。请注意，对于基于时间的窗口，配置 `topology.message.timeout.secs` 应该远远超过 `windowLength + slidingInterval`，否则元组将超时并重播，并可能导致重复的窗口计算。对于基于计数的窗口，应调整配置，以便可以在超时期限内接收 `windowLength + slidingInterval` 个元组。

> Storm 版本：1.2.2

原文：[Windowing Support in Core Storm](http://storm.apache.org/releases/1.2.2/Windowing.html)
