---
layout: post
author: smartsi
title: Flink 1.10 版本之前如何生成 Watermark
date: 2021-01-30 12:06:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-event-timestamp-and-extractors
---

> Flink 1.10

我们说使用 Watermark，那我们是在基于事件时间处理数据，首先第一步就是设置时间特性：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime);
```
除了在 StreamExecutionEnvironment 中指定 TimeCharacteristic 外，Flink 还需要知道事件的时间戳，这意味着需要为流中的每个元素分配事件时间戳。通常，这可以通过元素的某个字段来提取时间戳来完成。通过指定字段提取事件时间的过程，我们一般叫做 Timestamp Assigning。简单来讲，就是告诉系统需要通过哪个字段作为事件时间的数据来源。Timestamp 指定完毕之后，下面就需要创建相应的 Watermark。需要用户根据 Timestamp 计算出 Watermark 的生成策略。

目前 Flink 支持两种方式生成 Watermark（以及指定 Timestamp）：
- 直接在 DataStream Source 算子接口的 SourceFunction 中定义。
- 通过定义 Timestamp Assigner 与 Watermark Generator 来生成。

## 1. Source Functions 中定义 Watermark

在 Source Functions 中定义 Timestamp 和 Watermark，也就是说数据源可以将时间戳直接分配给它们产生的元素，并且还可以直接输出 Watermark。这就意味着不再需要指定 Timestamp Assigner。如果在后续流程中使用了 Timestamp Assigner，那么数据源提供的 Timestamp 和 Watermark 将会被覆盖。

用户需要重写 SourceFunction 接口中的 run() 方法实现数据生成逻辑，同时需要调用 SourceContext 上的 collectWithTimestamp() 方法生成事件时间戳以及要调用 emitWatermark() 方法来生成 Watermark。

如下代码是一个简单的示例数据源，在该数据源中分配时间戳并生成 Watermark：
```java
public class WatermarkSimpleSource extends RichParallelSourceFunction<WBehavior> {

    private Random random = new Random();
    private volatile boolean cancel;

    @Override
    public void run(SourceContext<WBehavior> ctx) throws Exception {
        while (!cancel) {
          WBehavior next = getNext();
          ctx.collectWithTimestamp(next, next.getEventTimestamp());
          if (next.hasWatermarkTime()) {
              ctx.emitWatermark(new Watermark(next.getWatermarkTime()));
          }
        }
    }

    @Override
    public void cancel() {
        cancel = true;
    }
}
```
> []()


## 2. 指定 Timestamp Assigner 与 Watermark Generator

如果用户使用了 Flink 已经定义好的外部数据源连接器，就不能再实现 SourceFunction 接口来生成流式数据以及相应的 Timestamp 和 Watermark，这种情况下就需要借助 Timestamp Assigner 来管理数据流中的 Timestamp 和 Watermark。Timestamp Assigner 一般是跟在 Source 算子后面，也可以在后续的算子中指定，只要保证 Timestamp Assigner 在第一个时间相关的算子之前即可。例如，一种常见的模式就是在解析（MapFunction）和过滤（FilterFunction）之后使用 Timestamp Assigner。

如果用户已经在 SourceFunction 中定义 Timestamp 和 Watermark 的生成逻辑，同时又使用了 Timestamp Assigner，此时 Assigner 会覆盖 SourceFunction 中定义的逻辑。

Flink 根据 Watermark 的生成形式分为两种类型，分别是 Periodic Watermark 和 Punctuated Watermark。Periodic Watermark 根据设定的时间间隔周期性的生成 Watermark，Punctuated Watermark 则根据某些特殊条件生成 Watermark，例如，数据流中特定数据量满足条件后触发生成 Watermark。在 Flink 中生成 Watermark 的逻辑需要分别借助如下接口实现：
```java
public SingleOutputStreamOperator<T> assignTimestampsAndWatermarks(AssignerWithPeriodicWatermarks<T> timestampAndWatermarkAssigner)
public SingleOutputStreamOperator<T> assignTimestampsAndWatermarks(AssignerWithPunctuatedWatermarks<T> timestampAndWatermarkAssigner)
```
> 1.10 版本之后使用 assignTimestampsAndWatermarks(WatermarkStrategy<T> watermarkStrategy) 接口。

### 2.1 Periodic Watermark

Periodic Watermark 根据设定的时间间隔周期性的生成 Watermark。使用 AssignerWithPeriodicWatermarks 接口分配时间戳并定期生成 Watermark。通过 ExecutionConfig.setAutoWatermarkInterval() 配置生成 Watermark 的周期性时间间隔，默认为 200 毫秒。每次都会调用 getCurrentWatermark() 方法，如果返回的 Watermark 非空且大于前一个 Watermark，则将输出新的 Watermark。

在 Flink 中已经内置实现了两种 Periodic Watermark Assigner，除此之外我们还可以自定义实现 Watermark。

#### 2.1.1 Ascending Timestamp Assigner

第一种 Assigner 是升序模式，将数据中的 Timestamp 根据指定字段提取，并用当前的 Timestamp 作为最新的 Watermark，这种 Assigner 比较适合于事件按顺序生成，没有乱序的情况。具体看一下源代码：
```java
public abstract class AscendingTimestampExtractor<T> implements AssignerWithPeriodicWatermarks<T> {

	private static final long serialVersionUID = 1L;

	/** The current timestamp. */
	private long currentTimestamp = Long.MIN_VALUE;

	private MonotonyViolationHandler violationHandler = new LoggingHandler();

	public abstract long extractAscendingTimestamp(T element);

  // 提取事件时间戳
	@Override
	public final long extractTimestamp(T element, long elementPrevTimestamp) {
		final long newTimestamp = extractAscendingTimestamp(element);
		if (newTimestamp >= this.currentTimestamp) {
			this.currentTimestamp = newTimestamp;
			return newTimestamp;
		} else {
			violationHandler.handleViolation(newTimestamp, this.currentTimestamp);
			return newTimestamp;
		}
	}
  // 生成 Watermark
	@Override
	public final Watermark getCurrentWatermark() {
		return new Watermark(currentTimestamp == Long.MIN_VALUE ? Long.MIN_VALUE : currentTimestamp - 1);
	}
}
```

具体如和使用呢？如下代码所示，通过 AscendingTimestampExtractor 来指定 Timestamp 字段，不需要显示的指定 Watermark，因为已经在系统中默认使用 Timestamp 创建 Watermark：
```java
// <key, timestamp, value>
DataStream<Tuple3<String, Long, Integer>> input ...

DataStream<Tuple3<String, Long, Integer>> result =
  input.assignTimestampsAndWatermarks(new AscendingTimestampExtractor<Tuple3<String, Long, Integer>>() {
    @Override
    public long extractAscendingTimestamp(Tuple3<String, Long, Integer> tuple) {
        return tuple.f1;
    }
});
```
假如出现了延迟数据（递减的时间戳），系统是如何处理的呢？如果产生了递减的时间戳，就要使用名为 MonotonyViolationHandler 的组件进行处理，并提供了三种策略：
- IgnoringHandler
- FailingHandler
- LoggingHandler

(1) IgnoringHandler

违反时间戳单调递增时，不执行任何操作：
```java
public static final class IgnoringHandler implements MonotonyViolationHandler {
  private static final long serialVersionUID = 1L;

  @Override
  public void handleViolation(long elementTimestamp, long lastTimestamp) {}
}
```

(2) FailingHandler

违反时间戳单调递增时，程序抛出异常：
```java
public static final class FailingHandler implements MonotonyViolationHandler {
		private static final long serialVersionUID = 1L;

		@Override
		public void handleViolation(long elementTimestamp, long lastTimestamp) {
			throw new RuntimeException("Ascending timestamps condition violated. Element timestamp "
					+ elementTimestamp + " is smaller than last timestamp " + lastTimestamp);
		}
	}
```

(3) LoggingHandler

违反时间戳单调递增时，仅打印 WARN 日志级别日志，这也是默认采取的策略：
```java
public static final class LoggingHandler implements MonotonyViolationHandler {
  private static final long serialVersionUID = 1L;

  private static final Logger LOG = LoggerFactory.getLogger(AscendingTimestampExtractor.class);

  @Override
  public void handleViolation(long elementTimestamp, long lastTimestamp) {
    LOG.warn("Timestamp monotony violated: {} < {}", elementTimestamp, lastTimestamp);
  }
}
```
单调递增的事件时间并不太符合实际情况，所以AscendingTimestampExtractor用得不多。

#### 2.1.2 固定时延间隔的Assigner

第二种 Assigner 是通过设定固定的时间间隔来指定 Watermark 落后于 Timestamp 的区间长度，也就是最大可容忍迟到的时间长度。我们先看一下源代码：
```java
public abstract class BoundedOutOfOrdernessTimestampExtractor<T> implements AssignerWithPeriodicWatermarks<T> {
	private long currentMaxTimestamp;
	private long lastEmittedWatermark = Long.MIN_VALUE;
	private final long maxOutOfOrderness;

	public BoundedOutOfOrdernessTimestampExtractor(Time maxOutOfOrderness) {
		if (maxOutOfOrderness.toMilliseconds() < 0) {
			throw new RuntimeException("Tried to set the maximum allowed " +
				"lateness to " + maxOutOfOrderness + ". This parameter cannot be negative.");
		}
		this.maxOutOfOrderness = maxOutOfOrderness.toMilliseconds();
		this.currentMaxTimestamp = Long.MIN_VALUE + this.maxOutOfOrderness;
	}

	public abstract long extractTimestamp(T element);

  // 生成 Watermark
	@Override
	public final Watermark getCurrentWatermark() {
		// this guarantees that the watermark never goes backwards.
		long potentialWM = currentMaxTimestamp - maxOutOfOrderness;
		if (potentialWM >= lastEmittedWatermark) {
			lastEmittedWatermark = potentialWM;
		}
		return new Watermark(lastEmittedWatermark);
	}

  // 提取事件时间戳
	@Override
	public final long extractTimestamp(T element, long previousElementTimestamp) {
		long timestamp = extractTimestamp(element);
		if (timestamp > currentMaxTimestamp) {
			currentMaxTimestamp = timestamp;
		}
		return timestamp;
	}
}
```
通过上面我们可以看到 Flink 已经帮我们实现了 Timestamp 提取的部分逻辑以及 Watermark 生成逻辑。那具体如何使用呢？如下代码所示，通过创建 BoundedOutOfOrdernessTimestampExtractor 实现类来定义 Timestamp Assigner，其中第一个参数 Time.minutes(10) 表示最大可容忍的时延为 10 分钟，并在 extractTimestamp 中实现时间戳抽取逻辑。在代码中我们选择第2个元素作为事件时间戳，其中 Watermark 是根据事件时间戳减去固定的时间延迟而生成的，如果当前数据中的时间大于 Watermark 的时间，则会被认为是迟到事件，并且在计算其相应窗口结果时默认忽略该元素：
```java
// <key, timestamp, value>
DataStream<Tuple3<String, Long, Integer>> input ...

DataStream<Tuple3<String, Long, Integer>> withTimestampsAndWatermarks =
    input.assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor<Tuple3<String, Long, Integer>>(Time.minutes(10)) {
    @Override
    public long extractTimestamp(Tuple3<String, Long, Integer> element) {
        return element.f1;
    }
});
```
#### 2.1.3 自定义 Periodic Watermark

除了上述两种内置的 Periodic Watermark Assigner，我们还可以自定义实现 AssignerWithPeriodicWatermarks 接口来实现 Periodic Watermark。如下代码所示，通过重写 getCurrentWatermark 和 extractTimestamp 方法来分别定义生成 Watermark 逻辑和时间戳抽取逻辑。其中 getCurrentWatermark 生成 Watermark 逻辑需要依赖于 currentMaxTimeStamp，该方法每次被调用时，如果产生的 Watermark 比现在的大，就会覆盖现在的 Watermark，从而实现 Watermark 的更新，即每当有新的最大时间戳出现时，可能就会产生新的 Watermark：
```java
public static class CustomPeriodicWatermarkAssigner implements AssignerWithPeriodicWatermarks<Tuple2<String, Long>> {

    private final Long outOfOrdernessMillis = 600000L;
    private Long currentMaxTimeStamp = Long.MIN_VALUE + outOfOrdernessMillis + 1;

    // 默认200ms被调用一次
    @Nullable
    @Override
    public Watermark getCurrentWatermark() {
        return new Watermark(currentMaxTimeStamp - outOfOrdernessMillis - 1);
    }

    @Override
    public long extractTimestamp(Tuple2<String, Long> element, long recordTimestamp) {
        Watermark watermark = getCurrentWatermark();
        LOG.info("[INFO] watermark: {}", DateUtil.timeStamp2Date(watermark.getTimestamp(), "yyyy-MM-dd HH:mm:ss")+ " | " + watermark.getTimestamp() + "]");
        String key = element.f0;
        Long timestamp = element.f1;

        currentMaxTimeStamp = Math.max(timestamp, currentMaxTimeStamp);

        LOG.info("[INFO] timestamp, key: {}, eventTime: {}, currentMaxTimeStamp: {}, maxOutOfOrderness: {}",
                key,
                "[" + DateUtil.timeStamp2Date(timestamp, "yyyy-MM-dd HH:mm:ss") + " | " + timestamp + "]",
                "[" + DateUtil.timeStamp2Date(currentMaxTimeStamp, "yyyy-MM-dd HH:mm:ss")+" | "+currentMaxTimeStamp + "]",
                outOfOrdernessMillis
        );

        return timestamp;
    }
}
```
> 备注：Tuple2<String, Long> 中第二个元素为元素时间戳。

效果如下：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-event-timestamp-and-extractors-1.jpg?raw=true)

### 2.2 Punctuated Watermark

除了根据时间周期性生成 Periodic Watermark，用户也可以根据某些特殊条件生成 Punctuated Watermark，例如判断某个数据元素为某个事件时，就会触发生成 Watermark，如果不为某个事件，就不会触发生成 Watermark。我们需要自定义实现 AssignerWithPunctuatedWatermarks 接口来实现 Punctuated Watermark。如下代码所示，通过重写 extractTimestamp 和 checkAndGetNextWatermark 方法来分别定义时间戳抽取逻辑和生成 Watermark 的逻辑：
```java
public static class CustomPunctuatedWatermarkAssigner implements AssignerWithPunctuatedWatermarks<Tuple2<String, Long>> {
    @Nullable
    @Override
    public Watermark checkAndGetNextWatermark(Tuple2<String, Long> lastElement, long extractedTimestamp) {
        // 如果输入的元素为A时就会触发Watermark
        if (Objects.equals(lastElement.f0, "A")) {
            Watermark watermark = new Watermark(extractedTimestamp);
            LOG.info("[INFO] watermark: {}", DateUtil.timeStamp2Date(watermark.getTimestamp(), "yyyy-MM-dd HH:mm:ss") + " | " + watermark.getTimestamp() + "]");
            return watermark;
        }
        return null;
    }

    @Override
    public long extractTimestamp(Tuple2<String, Long> element, long recordTimestamp) {
        // 抽取时间戳
        return element.f1;
    }
}
```

效果如下：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-event-timestamp-and-extractors-2.jpg?raw=true)

示例数据：
```
A,2021-01-05 12:07:01
B,2021-01-05 12:08:01
A,2021-01-05 12:14:01
C,2021-01-05 12:09:01
C,2021-01-05 12:15:01
A,2021-01-05 12:08:01
```

参考:
- [Generating Timestamps / Watermarks](https://ci.apache.org/projects/flink/flink-docs-release-1.10/dev/event_timestamps_watermarks.html)
- Flink原理、实战与性能优化

推荐订阅：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-jk.jpeg?raw=true)
