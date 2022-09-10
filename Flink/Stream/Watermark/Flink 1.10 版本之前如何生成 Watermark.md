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

> Flink 1.9

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


## 2. 在用户自定义函数指定

如果用户使用了 Flink 已经定义好的外部数据源连接器，就不能再实现 SourceFunction 接口来生成流式数据以及相应的 Timestamp 和 Watermark，这种情况下就需要借助时间戳分配器 TimestampAssigner 为元素分配时间戳以及生成 Watermark。TimestampAssigner 一般是跟在 Source 算子后面，也可以在后续的算子中指定，只要保证 TimestampAssigner 在第一个时间相关的算子之前即可。例如一种常见的模式就是在解析（MapFunction）和过滤（FilterFunction）之后使用 Timestamp Assigner。

如果用户已经在 SourceFunction 中定义 Timestamp 和 Watermark 的生成逻辑，同时又使用了 TimestampAssigner，此时分配器会覆盖 SourceFunction 中定义的逻辑。

Flink 根据 Watermark 的生成形式分时间戳分配器为两种类型，一种是周期性生成 Watermark 时间戳分配器，一种是断点式生成 Watermark 时间戳分配器。周期性生成 Watermark 时间戳分配器根据设定的时间间隔周期性的生成 Watermark，而断点式生成 Watermark 时间戳分配器则根据某些特殊条件生成 Watermark，例如数据流中特定数据量满足条件后触发生成 Watermark。在 Flink 中需要通过 assignTimestampsAndWatermarks 方法来指定不同形式的时间戳分配器：
```java
public SingleOutputStreamOperator<T> assignTimestampsAndWatermarks(AssignerWithPeriodicWatermarks<T> timestampAndWatermarkAssigner)
public SingleOutputStreamOperator<T> assignTimestampsAndWatermarks(AssignerWithPunctuatedWatermarks<T> timestampAndWatermarkAssigner)
```
> 1.10 版本之后使用 assignTimestampsAndWatermarks(WatermarkStrategy<T> watermarkStrategy) 接口。

### 2.1 周期性生成 Watermark 时间戳分配器

断点式生成 Watermark 时间戳分配器根据设定的时间间隔周期性的生成 Watermark。使用 AssignerWithPeriodicWatermarks 接口分配时间戳并定期生成 Watermark。可以通过如下方式设置生成 Watermark 的时间间隔周期，默认 200 毫秒：
```java
// 设置每 100ms 生成 Watermark
env.getConfig().setAutoWatermarkInterval(100);
```
每次都会调用 getCurrentWatermark() 方法，如果返回的 Watermark 非空且大于前一个 Watermark，则将输出新的 Watermark。

在 Flink 中已经内置实现了两种周期性生成 Watermark 的时间戳分配器：
- AscendingTimestampExtractor
- BoundedOutOfOrdernessTimestampExtractor

除此之外我们还可以自定义实现 Watermark。

#### 2.1.1 AscendingTimestampExtractor

周期性生成 Watermark 的时间戳分配器第一种内置实现是 AscendingTimestampExtractor。实现了 AssignerWithPeriodicWatermarks 接口，用当前提取的元素时间戳作为最新的 Watermark。这种时间分配器比较适合于事件按顺序生成，没有乱序的情况。具体源码解读可以查看 [AscendingTimestampExtractor](https://smartsi.blog.csdn.net/article/details/126797894?spm=1001.2014.3001.5502)。

AscendingTimestampExtractor 时间戳分配器使用比较简单，通过 assignTimestampsAndWatermarks 方法指定 AscendingTimestampExtractor 时间戳分配器的实现，并且只需要重写 extractAscendingTimestamp 方法来指定时间戳即可：
```java
// <key, timestamp, value>
DataStream<Tuple3<String, Long, Integer>> source ...

// 计算单词出现的次数
SingleOutputStreamOperator<Tuple4<String, Long, String, String>> stream = source
    .assignTimestampsAndWatermarks(new AscendingTimestampExtractor<Tuple2<String, Long>>() {
        @Override
        public long extractAscendingTimestamp(Tuple2<String, Long> tuple) {
            // 提取时间戳
            return tuple.f1;
        }
    })
    .map(new MapFunction<Tuple2<String, Long>, Tuple2<String, Long>>() {
        @Override
        public Tuple2<String, Long> map(Tuple2<String, Long> tuple2) throws Exception {
            return Tuple2.of(tuple2.f0, 1L);
        }
    })
    // 分组
    .keyBy(new KeySelector<Tuple2<String, Long>, String>() {
        @Override
        public String getKey(Tuple2<String, Long> element) throws Exception {
            return element.f0;
        }
    })
    // 每1分钟一个窗口
    .timeWindow(Time.minutes(1))
    // 求和
    .process(new ProcessWindowFunction<Tuple2<String, Long>, Tuple4<String, Long, String, String>, String, TimeWindow>() {
        @Override
        public void process(String word, Context context, Iterable<Tuple2<String, Long>> elements, Collector<Tuple4<String, Long, String, String>> out) throws Exception {
            // 计算出现次数
            long count = 0;
            for (Tuple2<String, Long> element : elements) {
                count ++;
            }
            // 当前 Watermark
            long currentWatermark = context.currentWatermark();
            // 时间窗口元数据
            TimeWindow window = context.window();
            long start = window.getStart();
            long end = window.getEnd();
            String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
            String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
            LOG.info("word: {}, count: {}, watermark: {}, windowStart: {}, windowEnd: {}",
                    word, count, currentWatermark,
                    start + "|" + startTime, end + "|" + endTime
            );
            // 输出
            out.collect(Tuple4.of(word, count, startTime, endTime));
        }
    });
```

> 完整代码请查阅[AscendingWatermarkExample](https://github.com/sjf0115/data-example/blob/master/flink-example-1.9/src/main/java/com/flink/example/stream/watermark/extractor/AscendingWatermarkExample.java)

实际效果如下
```
19:38:39,800 INFO  Source  [] - word: b, timestamp: 1662809919797, time: 2022-09-10 19:38:39
19:38:49,819 INFO  Source  [] - word: a, timestamp: 1662809929819, time: 2022-09-10 19:38:49
19:38:59,824 INFO  Source  [] - word: b, timestamp: 1662809939824, time: 2022-09-10 19:38:59
19:39:09,827 INFO  Source  [] - word: a, timestamp: 1662809949826, time: 2022-09-10 19:39:09
19:39:14,838 INFO  Process [] - word: b, count: 2, watermark: 1662809949825, windowStart: 1662809880000|2022-09-10 19:38:00, windowEnd: 1662809940000|2022-09-10 19:39:00
(b,2,2022-09-10 19:38:00,2022-09-10 19:39:00)
19:39:14,840 INFO  Process [] - word: a, count: 1, watermark: 1662809949825, windowStart: 1662809880000|2022-09-10 19:38:00, windowEnd: 1662809940000|2022-09-10 19:39:00
(a,1,2022-09-10 19:38:00,2022-09-10 19:39:00)
19:39:19,831 INFO  Source  [] - word: b, timestamp: 1662809959831, time: 2022-09-10 19:39:19
...
```

#### 2.1.2 BoundedOutOfOrdernessTimestampExtractor

周期性生成 Watermark 的时间戳分配器第二种内置实现是 BoundedOutOfOrdernessTimestampExtractor。实现了 AssignerWithPeriodicWatermarks 接口，用当前最大时间戳减去最大乱序时间作为最新的 Watermark。这种时间分配器比较适合于乱序场景。具体源码解读可以查看 [BoundedOutOfOrdernessTimestampExtractor](https://smartsi.blog.csdn.net/article/details/126797894?spm=1001.2014.3001.5502)。

BoundedOutOfOrdernessTimestampExtractor 的使用类似 AscendingTimestampExtractor，也需要通过 assignTimestampsAndWatermarks 方法指定 BoundedOutOfOrdernessTimestampExtractor 时间戳分配器的实现，并且需要重写 extractTimestamp 方法来指定时间戳。不一样的地方是，时间戳分配器的实现需要指定最大乱序时间 maxOutOfOrderness。如下代码所示，通过创建 BoundedOutOfOrdernessTimestampExtractor 实现类来实现时间戳分配器，并指定最大乱序时间为 5 秒：
```java
// 每1s输出一次单词
DataStreamSource<Tuple4<Integer, String, Integer, Long>> source = env.addSource(new OutOfOrderSource());
// 计算每1分钟内每个单词出现的次数
DataStream<Tuple3<String, Integer, String>> result = source
        .assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor<Tuple4<Integer, String, Integer, Long>>(Time.seconds(5)) {
            @Override
            public long extractTimestamp(Tuple4<Integer, String, Integer, Long> element) {
                return element.f3;
            }
        })
        // 分组
        .keyBy(new KeySelector<Tuple4<Integer, String, Integer, Long>, String>() {
            @Override
            public String getKey(Tuple4<Integer, String, Integer, Long> element) throws Exception {
                return element.f1;
            }
        })
        // 每1分钟的滚动窗口
        .timeWindow(Time.minutes(1))
        // 求和
        .process(new ProcessWindowFunction<Tuple4<Integer, String, Integer, Long>, Tuple3<String, Integer, String>, String, TimeWindow>() {
            @Override
            public void process(String key, Context context, Iterable<Tuple4<Integer, String, Integer, Long>> elements, Collector<Tuple3<String, Integer, String>> out) throws Exception {
                // 计算出现次数
                int count = 0;
                List<Integer> ids = Lists.newArrayList();
                for (Tuple4<Integer, String, Integer, Long> element : elements) {
                    count += element.f2;
                    ids.add(element.f0);
                }
                // 当前 Watermark
                long currentWatermark = context.currentWatermark();
                // 时间窗口元数据
                TimeWindow window = context.window();
                long start = window.getStart();
                long end = window.getEnd();
                String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
                String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
                LOG.info("word: {}, count: {}, ids: {}, watermark: {}, windowStart: {}, windowEnd: {}",
                        key, count, ids.toString(), currentWatermark,
                        start + "|" + startTime, end + "|" + endTime
                );
                out.collect(Tuple3.of(key, count, ids.toString()));
            }
        });

```
> 完整代码请查阅[BoundedOutOfOrderWatermarkExample](https://github.com/sjf0115/data-example/blob/master/flink-example-1.9/src/main/java/com/flink/example/stream/watermark/extractor/BoundedOutOfOrderWatermarkExample.java)

如上示例，设置 5 秒的最大乱序时间，计算1分钟窗口内每个单词的出现次数。实际效果如下：
```
2022-09-05 08:54:56,157 Source    [] - id: 1, word: a, count: 2, eventTime: 1662303772840|2022-09-04 23:02:52
2022-09-05 08:54:57,161 Source    [] - id: 2, word: a, count: 1, eventTime: 1662303770844|2022-09-04 23:02:50
2022-09-05 08:54:58,165 Source    [] - id: 3, word: a, count: 3, eventTime: 1662303773848|2022-09-04 23:02:53
2022-09-05 08:54:59,170 Source    [] - id: 4, word: a, count: 2, eventTime: 1662303774866|2022-09-04 23:02:54
2022-09-05 08:55:00,171 Source    [] - id: 5, word: a, count: 1, eventTime: 1662303777839|2022-09-04 23:02:57
2022-09-05 08:55:01,174 Source    [] - id: 6, word: a, count: 2, eventTime: 1662303784887|2022-09-04 23:03:04
2022-09-05 08:55:02,178 Source    [] - id: 7, word: a, count: 3, eventTime: 1662303776894|2022-09-04 23:02:56
2022-09-05 08:55:03,182 Source    [] - id: 8, word: a, count: 1, eventTime: 1662303786891|2022-09-04 23:03:06
2022-09-05 08:55:03,396 Sum       [] - word: a, count: 12, ids: [1, 2, 3, 4, 5, 7], watermark: 1662303781891,
                                       windowStart: 1662303720000|2022-09-04 23:02:00, windowEnd: 1662303780000|2022-09-04 23:03:00
2022-09-05 08:55:03,396 Print     [] - (a,12,[1, 2, 3, 4, 5, 7])
2022-09-05 08:55:04,187 Source    [] - id: 9, word: a, count: 5, eventTime: 1662303778877|2022-09-04 23:02:58
2022-09-05 08:55:05,191 Source    [] - id: 10, word: a, count: 4, eventTime: 1662303791904|2022-09-04 23:03:11
2022-09-05 08:55:06,192 Source    [] - id: 11, word: a, count: 1, eventTime: 1662303795918|2022-09-04 23:03:15
2022-09-05 08:55:07,196 Source    [] - id: 12, word: a, count: 6, eventTime: 1662303779883|2022-09-04 23:02:59
2022-09-05 08:55:08,203 Source    [] - id: 13, word: a, count: 2, eventTime: 1662303846254|2022-09-04 23:04:06
2022-09-05 08:55:08,242 Sum       [] - word: a, count: 8, ids: [6, 8, 10, 11], watermark: 1662303841254,
                                       windowStart: 1662303780000|2022-09-04 23:03:00, windowEnd: 1662303840000|2022-09-04 23:04:00
2022-09-05 08:55:08,243 Print     [] - (a,8,[6, 8, 10, 11])
2022-09-05 08:55:09,210 Sum       [] - word: a, count: 2, ids: [13], watermark: 9223372036854775807, windowStart: 1662303840000|2022-09-04 23:04:00, windowEnd: 1662303900000|2022-09-04 23:05:00
2022-09-05 08:55:09,211 Print     [] - (a,2,[13])
```

#### 2.1.3 自定义周期性生成 Watermark 的时间戳分配器

除了上述两种内置的周期性生成 Watermark 的时间戳分配器，我们还可以自定义实现 AssignerWithPeriodicWatermarks 接口来实现时间戳分配器。如下代码所示，通过重写 getCurrentWatermark 和 extractTimestamp 方法来分别定义生成 Watermark 逻辑和时间戳抽取逻辑。其中 getCurrentWatermark 生成 Watermark 逻辑需要依赖于 currentMaxTimeStamp。该方法每次被调用时，如果产生的 Watermark 比现在的大，就会覆盖现在的 Watermark，从而实现 Watermark 的更新。每当有新的最大时间戳出现时，可能就会产生新的 Watermark：
```java
public abstract class CustomBoundedOutOfOrderTimestampExtractor<T> implements AssignerWithPeriodicWatermarks<T> {
    private static final Logger LOG = LoggerFactory.getLogger(CustomBoundedOutOfOrderTimestampExtractor.class);
    private static final long serialVersionUID = 1L;
    // 当前最大时间戳
    private long currentMaxTimestamp;
    // 当前 Watermark
    private long lastEmittedWatermark = Long.MIN_VALUE;
    // 最大乱序时间
    private final long maxOutOfOrder;

    public CustomBoundedOutOfOrderTimestampExtractor(Time maxOutOfOrder) {
        if (maxOutOfOrder.toMilliseconds() < 0) {
            throw new RuntimeException("Tried to set the maximum allowed " + "lateness to " + maxOutOfOrder + ". This parameter cannot be negative.");
        }
        this.maxOutOfOrder = maxOutOfOrder.toMilliseconds();
        this.currentMaxTimestamp = Long.MIN_VALUE + this.maxOutOfOrder;
    }

    // 用户自定义实现时间戳提取逻辑
    public abstract long extractTimestamp(T element);

    @Override
    public final Watermark getCurrentWatermark() {
        // 保证 Watermark 递增的
        long potentialWM = currentMaxTimestamp - maxOutOfOrder;
        if (potentialWM >= lastEmittedWatermark) {
            lastEmittedWatermark = potentialWM;
        }
        LOG.info("currentMaxTimestamp: {}, currentWatermark: {}", currentMaxTimestamp, lastEmittedWatermark);
        return new Watermark(lastEmittedWatermark);
    }

    @Override
    public final long extractTimestamp(T element, long previousElementTimestamp) {
        long timestamp = extractTimestamp(element);
        // 当前最大时间戳计算 Watermark
        if (timestamp > currentMaxTimestamp) {
            currentMaxTimestamp = timestamp;
        }
        return timestamp;
    }
}
```
> 完整代码请查阅[CustomPeriodicWatermarkExample](https://github.com/sjf0115/data-example/blob/master/flink-example-1.9/src/main/java/com/flink/example/stream/watermark/custom/CustomPeriodicWatermarkExample.java)

### 2.2 断点式生成 Watermark 时间戳分配器

除了根据时间周期性生成 Watermark，用户也可以根据某些特殊条件生成 Watermark，例如判断某个数据元素为某个事件时，就会触发生成 Watermark。我们需要自定义实现 AssignerWithPunctuatedWatermarks 接口来实现断点式生成 Watermark 时间戳分配器。如下代码所示，通过重写 extractTimestamp 和 checkAndGetNextWatermark 方法来分别定义时间戳抽取逻辑和生成 Watermark 的逻辑：
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
> 完整代码请查阅[CustomPunctuatedWatermarkExample](https://github.com/sjf0115/data-example/blob/master/flink-example-1.9/src/main/java/com/flink/example/stream/watermark/custom/CustomPunctuatedWatermarkExample.java)
