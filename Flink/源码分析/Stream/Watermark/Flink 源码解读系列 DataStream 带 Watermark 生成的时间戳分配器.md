---
layout: post
author: smartsi
title: Flink 源码解读系列 DataStream 带 Watermark 生成的时间戳分配器
date: 2022-09-10 12:06:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-code-time-assigner-with-watermark
---

> Flink 1.10

这篇文章主要从源码角度讲一下 Flink DataStream 是如何生成 Watermark 的。

我们通常通过 DataStream 的 assignTimestampsAndWatermarks 方法分配时间戳并生成 Watermark。assignTimestampsAndWatermarks 方法可以传入两种时间戳分配器：
- 周期性生成 Watermark 的时间戳分配器：AssignerWithPeriodicWatermarks
- 断点式生成 Watermark 的时间戳分配器：AssignerWithPunctuatedWatermarks

这两种时间戳分配器均是 TimestampAssigner 的子类，具体继承关系如下图所示。在为元素分配时间戳的基础之上增加了生成 Watermark 的逻辑，可以理解是一个实现 Watermark 生成逻辑的时间戳分配器。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-code-time-assigner-with-watermark-1.png?raw=true)

## 1. TimestampAssigner

时间戳分配器 TimestampAssigner 主要用来从元素中提取时间戳并为元素分配事件时间时间戳。TimestampAssigner 接口比较简单，只有一个 extractTimestamp 方法，最终会交由用户来实现提取时间戳的逻辑：
```java
public interface TimestampAssigner<T> extends Function {
  // 提取时间戳
	long extractTimestamp(T element, long previousElementTimestamp);
}
```
用户可能会比较疑惑数据里不是已经有时间戳了吗，为什么还要创建时间戳分配器来分配时间戳呢？这是因为原始的时间戳只是写入日志数据的一个字段，如果不提取出来并明确告诉 Flink，Flink 是无法知道数据真正产生的时间。当然，有些时候数据源本身就提供了时间戳信息，比如读取 Kafka 时，我们就可以从 Kafka 数据中直接获取时间戳，而不需要单独提取字段分配了。

## 2. AssignerWithXXXWatermarks

根据 Watermark 生成形式不同，分为周期性生成 Watermark 和断点式生成 Watermark 两种形式。周期性生成 Watermark 需要实现 AssignerWithPeriodicWatermarks 接口，而断点式生成 Watermark 则需要实现 AssignerWithPunctuatedWatermarks 接口。

### 2.1 AssignerWithPeriodicWatermarks

AssignerWithPeriodicWatermarks 接口是周期性生成 Watermark 的时间戳分配器通用实现接口。实现该接口的时间分配器会根据设定的时间间隔周期性生成 Watermark。可以通过如下方式设置生成 Watermark 的时间间隔周期，默认 200 毫秒：
```java
// 设置每 100ms 生成 Watermark
env.getConfig().setAutoWatermarkInterval(100);
```
AssignerWithPeriodicWatermarks 接口在 TimestampAssigner 基础之上增加了生成 Watermark 的方法 getCurrentWatermark：
```java
public interface AssignerWithPeriodicWatermarks<T> extends TimestampAssigner<T> {
	@Nullable
	Watermark getCurrentWatermark();
}
```
根据设定的时间间隔系统会周期性的调用 getCurrentWatermark 方法，如果返回的 Watermark 非空并且大于前一个 Watermark 的时间戳，才会输出一个新的 Watermark。如果当前 Waternark 与前一个 Watermark 相同，那表示自上一次调用此方法以来，在事件时间上没有任何进展。如果返回一个空值，或者返回的 Watermark 的时间戳小于上次发出的时间戳，就不会生成新的 Watermark。

在 Flink 中已经内置实现了两种周期性生成 Watermark 的时间戳分配器，分别是 AscendingTimestampExtractor 和 BoundedOutOfOrdernessTimestampExtractor。

#### 2.1.1 AscendingTimestampExtractor

AscendingTimestampExtractor 是一个实现 AssignerWithPeriodicWatermarks 接口的抽象类，周期性生成 Watermark。这种时间分配器比较适合于事件按顺序生成，没有乱序的情况。

AscendingTimestampExtractor 时间分配器不仅需要实现 AssignerWithPeriodicWatermarks 接口中的 getCurrentWatermark 方法来生成 Watermark，还需实现 TimestampAssigner 中的 extractTimestamp 方法来实现为元素分配时间戳：
```java
public abstract class AscendingTimestampExtractor<T> implements AssignerWithPeriodicWatermarks<T> {
	@Override
	public final long extractTimestamp(T element, long elementPrevTimestamp) {
      // 提取事件时间戳
	}
	@Override
	public final Watermark getCurrentWatermark() {
		  // 生成 Watermark
	}
}
```

##### 2.1.1.1 分配事件时间戳

我们首先看一下如何为元素分配事件时间戳：
```java
// 抽象方法让用户实现
public abstract long extractAscendingTimestamp(T element);
// 通用时间戳提取逻辑
public final long extractTimestamp(T element, long elementPrevTimestamp) {
  	final long newTimestamp = extractAscendingTimestamp(element);
  	if (newTimestamp >= this.currentTimestamp) {
  		this.currentTimestamp = newTimestamp;
  		return newTimestamp;
  	} else {
      // 异常 非递增
  		violationHandler.handleViolation(newTimestamp, this.currentTimestamp);
  		return newTimestamp;
  	}
}
```
AscendingTimestampExtractor 生成了一个 extractAscendingTimestamp 抽象方法，需要用户自己实现元素时间戳的提取逻辑，毕竟 Flink 没办法知道我们的业务逻辑。有了用户实现的时间戳提取逻辑之后，Flink 需要做的就是判断提取的时间戳是否大于当前时间戳，需要确保时间戳是一个递增的时间序列。如果出现异常数据(小于当前时间戳，可能延迟到达了。需要用户判断一下当前场景使用 AscendingTimestampExtractor 是否合适)，Flink 也给我们提供了解决方案，使用名为 MonotonyViolationHandler 的组件进行处理，并提供了三种策略：
- IgnoringHandler
- FailingHandler
- LoggingHandler

第一种是 IgnoringHandler，违反时间戳单调递增时，不执行任何操作：
```java
public static final class IgnoringHandler implements MonotonyViolationHandler {
  @Override
  public void handleViolation(long elementTimestamp, long lastTimestamp) {}
}
```

第二种是 FailingHandler，违反时间戳单调递增时，程序抛出异常：
```java
public static final class FailingHandler implements MonotonyViolationHandler {
		@Override
		public void handleViolation(long elementTimestamp, long lastTimestamp) {
			throw new RuntimeException("Ascending timestamps condition violated. Element timestamp "
					+ elementTimestamp + " is smaller than last timestamp " + lastTimestamp);
		}
	}
```

第三种是 LoggingHandler，违反时间戳单调递增时仅打印 WARN 日志，这也是默认采取的策略：
```java
public static final class LoggingHandler implements MonotonyViolationHandler {
  private static final Logger LOG = LoggerFactory.getLogger(AscendingTimestampExtractor.class);
  @Override
  public void handleViolation(long elementTimestamp, long lastTimestamp) {
    LOG.warn("Timestamp monotony violated: {} < {}", elementTimestamp, lastTimestamp);
  }
}
```

##### 2.1.1.2 生成 Watermark

AscendingTimestampExtractor 的 Watermark 生成逻辑比较简单，用当前提取的元素时间戳作为最新的 Watermark：
```java
public final Watermark getCurrentWatermark() {
	return new Watermark(currentTimestamp == Long.MIN_VALUE ? Long.MIN_VALUE : currentTimestamp - 1);
}
```
这个方法定义了当前 Watermark 的获取逻辑，即判断当前时间戳师傅是最小值 Long.MIN_VALUE，如果是，代表了当初始化后还没有数据到来时，当前的 Watermark就为 Long.MIN_VALUE，以保证程序的正常运行。如果有数据到来时，Watermark 就是 currentTimestamp - 1。

> Watermark 为什么要减 1 毫秒呢？时间戳为 t 的水位线，表示时间戳 ≤t 的数据全部到齐，不会再来了。如果考虑有序流，也就是延迟时间为 0 的情况，那么时间戳为 7 秒的数据到来时，之后其实是还有可能继续来 7 秒的数据的；所以生成的 Watermark 不是 7 秒，而是 6 秒 999 毫秒，7 秒的数据还可以继续来。

#### 2.1.2 BoundedOutOfOrdernessTimestampExtractor

Flink 中内置实现的第二种周期性生成 Watermark 的时间戳分配器是 BoundedOutOfOrdernessTimestampExtractor，是一个实现 AssignerWithPeriodicWatermarks 接口的抽象类，周期性生成 Watermark。这种时间分配器比较适合于乱序的情况。由于乱序流中需要等待迟到数据到齐，所以必须设置一个固定量的延迟时间，来指定 Watermark 滞后于数据流中最大时间戳一个固定的时间量（相当于把表调慢）。创建 BoundedOutOfOrdernessTimestampExtractor 需要指定最大乱序时间 maxOutOfOrderness：
```java
public abstract class BoundedOutOfOrdernessTimestampExtractor<T> implements AssignerWithPeriodicWatermarks<T> {
	public BoundedOutOfOrdernessTimestampExtractor(Time maxOutOfOrderness) {
  		if (maxOutOfOrderness.toMilliseconds() < 0) {
        // 必须大于0
  			throw new RuntimeException(xxx);
  		}
  		this.maxOutOfOrderness = maxOutOfOrderness.toMilliseconds();
  		this.currentMaxTimestamp = Long.MIN_VALUE + this.maxOutOfOrderness;
	}
	@Override
	public final Watermark getCurrentWatermark() {
      // 生成 Watermark
	}
	@Override
	public final long extractTimestamp(T element, long previousElementTimestamp) {
  		// 提取事件时间戳
	}
}
```
跟 AscendingTimestampExtractor 时间分配器一样，不仅需要实现 AssignerWithPeriodicWatermarks 接口中的 getCurrentWatermark 方法来生成 Watermark，还需实现 TimestampAssigner 中的 extractTimestamp 方法来实现为元素分配时间戳。

##### 2.1.2.1 分配事件时间戳

跟 AscendingTimestampExtractor 一样，用户需要自己实现元素时间戳提取逻辑 extractTimestamp：
```java
// 抽象方法让用户实现
public abstract long extractTimestamp(T element);
// 通用时间戳提取逻辑
public final long extractTimestamp(T element, long previousElementTimestamp) {
  	long timestamp = extractTimestamp(element);
  	if (timestamp > currentMaxTimestamp) {
  		currentMaxTimestamp = timestamp;
  	}
  	return timestamp;
}
```
BoundedOutOfOrdernessTimestampExtractor 不需要保证元素时间戳是单调递增的，提取的时间戳直接返回即可。但由于可以接受元素是乱序的，所以在这还需要保存元素的最大时间戳 currentMaxTimestamp 来计算 Watermark，保证  Watermark 不能出现后退的情况。

##### 2.1.2.2 Watermark 生成

BoundedOutOfOrdernessTimestampExtractor 的 Watermark 生成逻辑也比较简单，用当前最大时间戳减去最大乱序时间作为最新的 Watermark。只有当 Watermark 大于等于上一次发出的 Watermark 时，才会输出这次的 Watermark：
```java
// 上一次发出的 Watermark，初始为 Long.MIN_VALUE
private long lastEmittedWatermark = Long.MIN_VALUE;
public final Watermark getCurrentWatermark() {
    // 当前数据流中最大的时间戳减去最大乱序时间
  	long potentialWM = currentMaxTimestamp - maxOutOfOrderness;
    // 如果得到的 Watermark 大于等于上一次的 Watermark，则进行更新，从而保证 Watermark 是递增的。
  	if (potentialWM >= lastEmittedWatermark) {
  		lastEmittedWatermark = potentialWM;
  	}
  	return new Watermark(lastEmittedWatermark);
}
```
为什么不用当前的时间戳减去最大乱序时间作为最新的 Watermark 的呢？由于数据是乱序，所以有可能新的时间戳比之前的还小，如果直接将这个时间戳计算 Watermark，那么我们的'事件时钟'就回退了，Watermark 代表了时钟，时光不能倒流，所以 Watermark  的时间戳也不能减小。

### 2.2 AssignerWithPunctuatedWatermarks

周期性生成 Watermark 的时间戳分配器会根据设定的时间间隔周期性生成 Watermark，而断点式生成 Watermark 的时间戳分配器 AssignerWithPunctuatedWatermarks 则会根据某些特殊条件生成 Watermark，例如数据流中特定数据量满足条件后触发生成 Watermark。

Flink 没有为我们内置实现断点式生成 Watermark 的时间戳分配器。我们需要自定义实现 AssignerWithPunctuatedWatermarks 接口来创建时间戳分配器。用户需要通过重写 extractTimestamp 和 checkAndGetNextWatermark 方法来分别定义时间戳抽取逻辑和生成 Watermark 的逻辑：
```java
public interface AssignerWithPunctuatedWatermarks<T> extends TimestampAssigner<T> {
	@Nullable
	Watermark checkAndGetNextWatermark(T lastElement, long extractedTimestamp);
}
```
