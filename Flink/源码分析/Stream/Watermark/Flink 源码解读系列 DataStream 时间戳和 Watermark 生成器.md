
TimestampAssigner 目的只有一个就是从记录元素中提取元素的时间戳：
```java
public interface TimestampAssigner<T> extends Function {
  // 分配时间时间戳
	long extractTimestamp(T element, long previousElementTimestamp);
}
```
接口中只有一个方法 extractTimestamp，最终会交由用户来实现提取时间戳的逻辑。


Flink 根据 Watermark 的生成形式分为两种类型，分别是 Periodic Watermark 和 Punctuated Watermark。Periodic Watermark 根据设定的时间间隔周期性生成 Watermark，Punctuated Watermark 则根据某些特殊条件生成 Watermark，例如数据流中特定数据量满足条件后触发生成 Watermark。

## 1. AssignerWithPeriodicWatermarks

AssignerWithPeriodicWatermarks 在 TimestampAssigner 为元素提取时间戳的基础之上增加了生成 Watermark 的逻辑，可以理解为 AssignerWithPeriodicWatermarks 是一个时间戳和 Watermark 生成器：
```java
public interface AssignerWithPeriodicWatermarks<T> extends TimestampAssigner<T> {
	@Nullable
	Watermark getCurrentWatermark();
}
```

Periodic Watermark 根据 ExecutionConfig.setAutoWatermarkInterval() 设定的时间间隔周期性的生成 Watermark，时间间隔默认为 200 毫秒。每次都会调用 getCurrentWatermark() 方法，如果返回的 Watermark 非空且大于前一个 Watermark，则将输出新的 Watermark。

> 如何被周期性调用的？

在 Flink 中已经内置实现了两种 Periodic Watermark Assigner，分别是 AscendingTimestampExtractor 和 BoundedOutOfOrdernessTimestampExtractor。

### 1.1 AscendingTimestampExtractor

AscendingTimestampExtractor 将数据中的 Timestamp 根据指定字段提取，并用当前的 Timestamp 作为最新的 Watermark，比较适合于事件按顺序生成，没有乱序的情况：
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
核心方法有两个，一个是用于提取事件时间戳的 extractTimestamp()，另一个是用于生成 Watermark 的 getCurrentWatermark()。

#### 1.1.1 时间戳提取

我们首先看一下元素事件时间戳如何提取：
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
AscendingTimestampExtractor 生成了一个 extractAscendingTimestamp 抽象方法，需要用户自己实现元素时间戳的提取逻辑，毕竟 Flink 没办法知道我们的业务逻辑。有了用户实现的时间戳提取逻辑之后，Flink 需要做的就是判断提取的时间戳是否大于当前时间戳，需要确保时间是一个递增的时间序列。如果出现异常数据(小于当前时间戳，可能延迟到达了。需要用户判断一下当前场景使用 AscendingTimestampExtractor 是否合适)，Flink 也给我们提供了解决方案，使用名为 MonotonyViolationHandler 的组件进行处理，并提供了三种策略：
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

#### 1.1.2 Watermark 生成

AscendingTimestampExtractor 的 Watermark 生成逻辑比较简单，根据当前提取的元素时间戳来设置 Watermark：
```java
public final Watermark getCurrentWatermark() {
	return new Watermark(currentTimestamp == Long.MIN_VALUE ? Long.MIN_VALUE : currentTimestamp - 1);
}
```

### 1.2 BoundedOutOfOrdernessTimestampExtractor

第二种 Assigner 是通过设定固定的时间间隔来指定 Watermark 落后于 Timestamp 的区间长度，也就是最大可容忍延迟时间。创建 BoundedOutOfOrdernessTimestampExtractor 需要指定最大可容忍延迟时间 maxOutOfOrderness：
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
Periodic Watermark 核心方法都一样，一个是用于提取事件时间戳的 extractTimestamp()，另一个是用于生成 Watermark 的 getCurrentWatermark()。

#### 1.2.1 时间戳提取

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
跟 AscendingTimestampExtractor 一样，用户都需要自己实现元素时间戳的提取逻辑，在这需要实现 extractTimestamp 抽象方法。BoundedOutOfOrdernessTimestampExtractor 不需要保证元素时间戳是单调递增的，提取的时间戳直接返回即可。由于可以接受元素是乱序的，所以在这还需要保存元素的最大时间戳 currentMaxTimestamp 来判断元素到达情况。

#### 1.2.2 Watermark 生成

```java
public final Watermark getCurrentWatermark() {
  	// this guarantees that the watermark never goes backwards.
  	long potentialWM = currentMaxTimestamp - maxOutOfOrderness;
  	if (potentialWM >= lastEmittedWatermark) {
  		lastEmittedWatermark = potentialWM;
  	}
  	return new Watermark(lastEmittedWatermark);
}
```

## 2. AssignerWithPunctuatedWatermarks

AssignerWithPunctuatedWatermarks 跟 AssignerWithPeriodicWatermarks 一样，也是增加了生成 Watermark 的逻辑：
```java
public interface AssignerWithPunctuatedWatermarks<T> extends TimestampAssigner<T> {
	@Nullable
	Watermark checkAndGetNextWatermark(T lastElement, long extractedTimestamp);
}
```
