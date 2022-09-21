## 1. 什么是迟到数据

之前介绍过，Watermark 可以用来平衡结果的完整性和延迟。除非你选择一种非常保守的 Watermark 生成策略，等待足够长的时间确保应该到的数据已经全部到达（以高延迟为代价确保了数据的完整性），否则你的应用程序很有可能有迟到的数据。

所谓迟到数据是指数据记录元素到达算子后，本应该参与的计算已经执行完毕。在事件时间窗口算子中，如果数据记录元素到达算子时窗口分配器为其分配的窗口因为算子 Watermark 超过了窗口的结束时间而销毁，那么可以认为这条数据记录元素就是迟到数据（迟到数据在窗口计算时就不会被纳入窗口的统计范围内）。可以看出迟到数据本质是指某个 Watermark 之后到来的数据记录元素，并且其时间戳小于 Watermark。所以只有在事件时间语义下，讨论迟到数据的处理才是有意义的。

一般情况 Watermark 不应该把延迟设置得太大，否则流处理的实时性就会大大降低。因为 Watermark 的延迟主要是用来处理分布式网络传输导致的数据乱序，而网络传输的乱序程度一般并不会很大，大多集中在几毫秒至几百毫秒。所以实际应用中，我们往往会给 Watermark 设置一个'能够处理大多数乱序数据的最小延迟'，视需求一般设在毫秒到秒级。保证了低延迟，但是就有可能数据记录在 Watermark 之后到达，必须额外添加一些代码来处理延迟事件。DataStream API 提供了不同的选项来应对迟到的数据记录：
- 丢弃迟到数据记录
- 基于迟到数据更新计算结果
- 将迟到的数据记录输出到单独的数据流中

## 2. 迟到数据处理

### 2.1 丢弃迟到数据记录

处理迟到数据元素的最简单方式就是直接将其丢弃，这也是事件时间窗口的默认行为。在这种情况下，不需要我们做任何额外的处理。如下代码所示，计算事件时间一分钟窗口内每个单词的出现次数，并设置了 5s 的最大乱序时间：
```java
SingleOutputStreamOperator<Tuple2<String, Integer>> stream = source
      .assignTimestampsAndWatermarks(
              // 5s的最大乱序
              WatermarkStrategy.<Tuple4<Integer, String, Integer, Long>>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                      .withTimestampAssigner(new SerializableTimestampAssigner<Tuple4<Integer, String, Integer, Long>>() {
                          @Override
                          public long extractTimestamp(Tuple4<Integer, String, Integer, Long> element, long recordTimestamp) {
                              return element.f3;
                          }
                      })
      )
      // 分组
      .keyBy(new KeySelector<Tuple4<Integer, String, Integer, Long>, String>() {
          @Override
          public String getKey(Tuple4<Integer, String, Integer, Long> tuple) throws Exception {
              return tuple.f1;
          }
      })
      // 1分钟的滚动窗口
      .window(TumblingEventTimeWindows.of(Time.minutes(1)))
      // 窗口计算
      .process(new ProcessWindowFunction<Tuple4<Integer, String, Integer, Long>, Tuple2<String, Integer>, String, TimeWindow>() {
          @Override
          public void process(String key, Context context, Iterable<Tuple4<Integer, String, Integer, Long>> elements, Collector<Tuple2<String, Integer>> out) throws Exception {
              // 单词个数
              int count = 0;
              List<Integer> ids = Lists.newArrayList();
              for (Tuple4<Integer, String, Integer, Long> element : elements) {
                  ids.add(element.f0);
                  count++;
              }
              // 时间窗口元数据
              TimeWindow window = context.window();
              long start = window.getStart();
              long end = window.getEnd();
              String startTime = DateUtil.timeStamp2Date(start);
              String endTime = DateUtil.timeStamp2Date(end);
              // Watermark
              long watermark = context.currentWatermark();
              String watermarkTime = DateUtil.timeStamp2Date(watermark);
              //  输出日志
              LOG.info("word: {}, count: {}, ids: {}, window: {}, watermark: {}",
                      key, count, ids,
                      "[" + startTime + ", " + endTime + "]",
                      watermark + "|" + watermarkTime
              );
              out.collect(Tuple2.of(key, count));
          }
      });
```
> 完整代码请查阅[LatenessDiscordExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/late/LatenessDiscordExample.java)

假设输入数据如下所示：
```
// 格式：行为唯一标识Id, 单词, 出现次数, 事件时间戳
1, a, 2, 1662303772840 // 23:02:52
2, a, 1, 1662303770844 // 23:02:50
3, a, 3, 1662303773848 // 23:02:53
4, a, 2, 1662303774866 // 23:02:54
5, a, 1, 1662303777839 // 23:02:57
6, a, 2, 1662303784887 // 23:03:04
7, a, 3, 1662303776894 // 23:02:56
8, a, 1, 1662303786891 // 23:03:06
9, a, 5, 1662303778877 // 23:02:58
10, a, 4, 1662303791904 // 23:03:11
11, a, 1, 1662303795918 // 23:03:15
12, a, 6, 1662303779883 // 23:02:59
13, a, 2, 1662303846254 // 23:04:06
```
实际效果如下所示：
```
22:23:44,553 Source      [] - id: 1, word: a, count: 2, eventTime: 1662303772840|2022-09-04 23:02:52
22:23:45,563 Source      [] - id: 2, word: a, count: 1, eventTime: 1662303770844|2022-09-04 23:02:50
22:23:46,567 Source      [] - id: 3, word: a, count: 3, eventTime: 1662303773848|2022-09-04 23:02:53
22:23:47,572 Source      [] - id: 4, word: a, count: 2, eventTime: 1662303774866|2022-09-04 23:02:54
22:23:48,574 Source      [] - id: 5, word: a, count: 1, eventTime: 1662303777839|2022-09-04 23:02:57
22:23:49,579 Source      [] - id: 6, word: a, count: 2, eventTime: 1662303784887|2022-09-04 23:03:04
22:23:50,585 Source      [] - id: 7, word: a, count: 3, eventTime: 1662303776894|2022-09-04 23:02:56
22:23:51,588 Source      [] - id: 8, word: a, count: 1, eventTime: 1662303786891|2022-09-04 23:03:06
22:23:51,784 Sum         [] - word: a, count: 12, ids: [1, 2, 3, 4, 5, 7], window: [2022-09-04 23:02:00, 2022-09-04 23:03:00], watermark: 1662303781890|2022-09-04 23:03:01
(a,12)
22:23:52,589 Source      [] - id: 9, word: a, count: 5, eventTime: 1662303778877|2022-09-04 23:02:58
22:23:53,594 Source      [] - id: 10, word: a, count: 4, eventTime: 1662303791904|2022-09-04 23:03:11
22:23:54,598 Source      [] - id: 11, word: a, count: 1, eventTime: 1662303795918|2022-09-04 23:03:15
22:23:55,600 Source      [] - id: 12, word: a, count: 6, eventTime: 1662303779883|2022-09-04 23:02:59
22:23:56,605 Source      [] - id: 13, word: a, count: 2, eventTime: 1662303846254|2022-09-04 23:04:06
22:23:56,649 Sum         [] - word: a, count: 8, ids: [6, 8, 10, 11], window: [2022-09-04 23:03:00, 2022-09-04 23:04:00], watermark: 1662303841253|2022-09-04 23:04:01
(a,8)
22:23:57,619 Sum         [] - word: a, count: 2, ids: [13], window: [2022-09-04 23:04:00, 2022-09-04 23:05:00], watermark: 9223372036854775807|292278994-08-17 15:12:55
(a,2)
```
id 为 1 到 7 的数据记录持续输入，直到 id = 8 的数据记录到达后，Watermark（1662303781890=1662303786891-5000-1）超过了窗口 `[2022-09-04 23:02:00, 2022-09-04 23:03:00]` 的结束时间，触发该窗口计算。`1, 2, 3, 4, 5, 7` 数据记录分配到该窗口参与计算，尽管 id = 7 的数据记录延迟到达，但依然不妨碍它参与计算，因为 id = 7 数据记录到达时分配的窗口还没触发计算。同理，`6, 8, 10, 11, 13` 数据记录也分配到窗口参与计算，但是发现 id = 9 的数据记录并没有输出。这是因为 id = 9 和 12 的数据记录延迟太长时间，当它到达时它本应该属于的窗口 `[2022-09-04 23:02:00, 2022-09-04 23:03:00]` 早已触发计算后并销毁，导致该数据记录被丢弃。

### 2.2 基于迟到数据更新计算结果

迟到数据到达算子后，它本应该参与的计算已经执行完毕，这表示算子之前输出的结果可能是不完整或者不正确的。例如上面的例子，如果正常没有延迟的情况下，id = 9 和 12 的数据记录会归属到 `[2022-09-04 23:02:00, 2022-09-04 23:03:00]` 窗口，现在却是该窗口丢失这两条数据记录。我们还是希望该来的数据记录尽量的都能参与计算。所以直接丢弃迟到数据不是我们的第一选择，还有一种策略就是容忍一定的延迟，在这段时间内迟到的数据对之前不完整的结果进行更新。如果对不完整的结果进行更新（重新计算并更新结果），就不得不考虑下面两个问题：
- 支持重新计算并对已输出结果进行更新的算子需要保留那些用于再次计算结果的状态。通常算子无法永久保留所有状态，最终还是在某个时间点将其清除，一旦清除了这些结果对应的状态，结果就无法再更新，只能将其丢弃。所以需要保留结果对应的状态直到不再需要。
- 除了在算子中保持状态，受结果更新影响的下游算子或者外部系统需要能够处理这些更新。例如，为了实现此目的，键值窗口算子的结果以及更新写入到一个 KV 存储数据库中，可以通过 Upsert 写入模式将之前的结果更新为最近一次的结果。

为了支持容忍一定的延迟，窗口算子 API 提供了一个方法，可以显示声明支持迟到的数据。在使用事件时间窗口时，你可以指定一个名为 AllowedLateness 的可允许最大延迟时间，即我们可以允许延迟一定时间。配置了该属性的窗口算子在 Watermark 超过窗口的结束时间之后不会立即销毁窗口（正常情况下会销毁），而是会继续保留窗口到 AllowedLateness 设定的可允许最大延迟时间。在这段额外时间内迟到的数据记录元素也会像按时到达的数据记录一样进入窗口中并触发计算。直到 Watermark 超过了窗口的结束时间加 AllowedLateness 设定的可允许最大延迟时间，窗口才会被最终销毁，此后的延迟数据记录都将直接丢弃。

基于 WindowedStream 调用 allowedLateness() 方法，传入一个 Time 类型的延迟时间，就可以表示允许这段时间内的延迟数据：
```java
stream.keyBy(...)
      .window(TumblingEventTimeWindows.of(Time.minutes(1)))
      .allowedLateness(Time.seconds(10))
```
比如上面的代码中，我们定义了 1 分钟的滚动窗口，并设置了允许 10 秒的最大延迟时间。也就是说，在不考虑 Watermark 延迟的情况下，对于 02 分到 03 分的窗口，本来应该是 Watermark 到达 03 分整就会触发窗口计算并销毁。但是现在可以允许延迟 10 秒钟，那么 03 分整就只是触发一次计算并输出结果，并不会销毁窗口。后续到达的数据，只要属于 02 分到 03 分窗口，依然可以在之前统计的基础上继续叠加，并且再次输出一个更新后的结果。直到 Watermark 到达了 03 分 10 秒钟，这时就真正清空状态、销毁窗口，之后再来的迟到数据就会被丢弃了。

如下代码所示，还是上面的例子计算事件时间一分钟窗口内每个单词的出现次数，唯一的变化是调用 allowedLateness() 方法设置最大延迟时间：
```java
SingleOutputStreamOperator<Tuple2<String, Integer>> stream = source
        .assignTimestampsAndWatermarks(
                // 5s的最大乱序
                WatermarkStrategy.<Tuple4<Integer, String, Integer, Long>>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                        .withTimestampAssigner(new SerializableTimestampAssigner<Tuple4<Integer, String, Integer, Long>>() {
                            @Override
                            public long extractTimestamp(Tuple4<Integer, String, Integer, Long> element, long recordTimestamp) {
                                return element.f3;
                            }
                        })
        )
        // 分组
        .keyBy(new KeySelector<Tuple4<Integer, String, Integer, Long>, String>() {
            @Override
            public String getKey(Tuple4<Integer, String, Integer, Long> tuple) throws Exception {
                return tuple.f1;
            }
        })
        // 1分钟的滚动窗口
        .window(TumblingEventTimeWindows.of(Time.minutes(1)))
        // 核心点：最大允许延迟10s
        .allowedLateness(Time.seconds(10))
        // 窗口计算
        .process(xxx);
```
> 完整代码请查阅[AllowedLatenessExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/late/AllowedLatenessExample.java)

实际效果如下所示：
```
23:05:42,889 Source      [] - id: 1, word: a, count: 2, eventTime: 1662303772840|2022-09-04 23:02:52
23:05:43,900 Source      [] - id: 2, word: a, count: 1, eventTime: 1662303770844|2022-09-04 23:02:50
23:05:44,902 Source      [] - id: 3, word: a, count: 3, eventTime: 1662303773848|2022-09-04 23:02:53
23:05:45,905 Source      [] - id: 4, word: a, count: 2, eventTime: 1662303774866|2022-09-04 23:02:54
23:05:46,910 Source      [] - id: 5, word: a, count: 1, eventTime: 1662303777839|2022-09-04 23:02:57
23:05:47,914 Source      [] - id: 6, word: a, count: 2, eventTime: 1662303784887|2022-09-04 23:03:04
23:05:48,917 Source      [] - id: 7, word: a, count: 3, eventTime: 1662303776894|2022-09-04 23:02:56
23:05:49,922 Source      [] - id: 8, word: a, count: 1, eventTime: 1662303786891|2022-09-04 23:03:06
23:05:50,054 Sum         [] - word: a, count: 12, ids: [1, 2, 3, 4, 5, 7], window: [2022-09-04 23:02:00, 2022-09-04 23:03:00], watermark: 1662303781890|2022-09-04 23:03:01
(a,12)
23:05:50,927 Source      [] - id: 9, word: a, count: 5, eventTime: 1662303778877|2022-09-04 23:02:58
23:05:50,984 Sum         [] - word: a, count: 17, ids: [1, 2, 3, 4, 5, 7, 9], window: [2022-09-04 23:02:00, 2022-09-04 23:03:00], watermark: 1662303781890|2022-09-04 23:03:01
(a,17)
23:05:51,931 Source      [] - id: 10, word: a, count: 4, eventTime: 1662303791904|2022-09-04 23:03:11
23:05:52,933 Source      [] - id: 11, word: a, count: 1, eventTime: 1662303795918|2022-09-04 23:03:15
23:05:53,935 Source      [] - id: 12, word: a, count: 6, eventTime: 1662303779883|2022-09-04 23:02:59
23:05:54,939 Source      [] - id: 13, word: a, count: 2, eventTime: 1662303846254|2022-09-04 23:04:06
23:05:55,231 Sum         [] - word: a, count: 8, ids: [6, 8, 10, 11], window: [2022-09-04 23:03:00, 2022-09-04 23:04:00], watermark: 1662303841253|2022-09-04 23:04:01
(a,8)
23:05:55,951 Sum         [] - word: a, count: 2, ids: [13], window: [2022-09-04 23:04:00, 2022-09-04 23:05:00], watermark: 9223372036854775807|292278994-08-17 15:12:55
(a,2)
```
相比第一次输出，在这当 id = 9 的数据记录到达时重新触发了窗口计算，依然可以在之前统计的基础上继续叠加，并且再次输出一个更新后的结果。id = 9 的数据记录依然可以参与窗口计算的原因是当前 Watermark(1662303781890)小于窗口结束时间戳(1662303780000)加 allowedLateness 可允许的最大延迟时间(10000)。而 id = 12 的数据记录到达时没有触发计算而是被丢弃，主要是延迟太久已经超出了可允许的最大延迟时间范围了。

### 2.3 将迟到的数据记录输出到单独的数据流中

即使可以设置窗口的延迟时间，终归还是有限的，后续的数据还是会被丢弃，例如上面例子中的 id = 12 的数据记录。如果不想丢弃任何一个数据，又该怎么做呢? Flink 还提供了另外一种方式处理迟到数据。我们可以将迟到没有被处理的数据记录输出到侧输出流(side output)中，后续就可以单独再进行处理。根据业务需求决定是否将迟到数据再回填集成到流式应用的结果中。

基于 WindowedStream 调用 sideOutputLateData() 方法，就可以实现这个功能。如下代码所示，还是基于上面的例子计算事件时间一分钟窗口内每个单词的出现次数，除了调用 allowedLateness() 方法设置最大延迟时间之外，还调用 sideOutputLateData() 将延迟没有被处理的数据输出到侧输出流中：
```java
// 窗口计算
SingleOutputStreamOperator<Tuple2<String, Integer>> stream = source
    .assignTimestampsAndWatermarks(
            // 5s的最大乱序
            WatermarkStrategy.<Tuple4<Integer, String, Integer, Long>>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                    .withTimestampAssigner(new SerializableTimestampAssigner<Tuple4<Integer, String, Integer, Long>>() {
                        @Override
                        public long extractTimestamp(Tuple4<Integer, String, Integer, Long> element, long recordTimestamp) {
                            return element.f3;
                        }
                    })
    )
    // 分组
    .keyBy(new KeySelector<Tuple4<Integer, String, Integer, Long>, String>() {
        @Override
        public String getKey(Tuple4<Integer, String, Integer, Long> tuple) throws Exception {
            return tuple.f1;
        }
    })
    // 1分钟的滚动窗口
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    // 最大允许延迟10s
    .allowedLateness(Time.seconds(10))
    // 迟到数据收集
    .sideOutputLateData(lateOutputTag)
    // 窗口计算
    .process(xxx);

// 输出并打印日志
stream.print();
// 侧输出
stream.getSideOutput(lateOutputTag).print("延迟链路");
```
> 完整代码请查阅[AllowedLatenessOutputExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/late/AllowedLatenessOutputExample.java)

实际效果如下所示：
```
23:33:12,848 Source      [] - id: 1, word: a, count: 2, eventTime: 1662303772840|2022-09-04 23:02:52
23:33:13,862 Source      [] - id: 2, word: a, count: 1, eventTime: 1662303770844|2022-09-04 23:02:50
23:33:14,868 Source      [] - id: 3, word: a, count: 3, eventTime: 1662303773848|2022-09-04 23:02:53
23:33:15,874 Source      [] - id: 4, word: a, count: 2, eventTime: 1662303774866|2022-09-04 23:02:54
23:33:16,878 Source      [] - id: 5, word: a, count: 1, eventTime: 1662303777839|2022-09-04 23:02:57
23:33:17,883 Source      [] - id: 6, word: a, count: 2, eventTime: 1662303784887|2022-09-04 23:03:04
23:33:18,886 Source      [] - id: 7, word: a, count: 3, eventTime: 1662303776894|2022-09-04 23:02:56
23:33:19,891 Source      [] - id: 8, word: a, count: 1, eventTime: 1662303786891|2022-09-04 23:03:06
23:33:19,987 Sum         [] - word: a, count: 12, ids: [1, 2, 3, 4, 5, 7], window: [2022-09-04 23:02:00, 2022-09-04 23:03:00], watermark: 1662303781890|2022-09-04 23:03:01
(a,12)
23:33:20,896 Source      [] - id: 9, word: a, count: 5, eventTime: 1662303778877|2022-09-04 23:02:58
23:33:20,925 Sum         [] - word: a, count: 17, ids: [1, 2, 3, 4, 5, 7, 9], window: [2022-09-04 23:02:00, 2022-09-04 23:03:00], watermark: 1662303781890|2022-09-04 23:03:01
(a,17)
23:33:21,899 Source      [] - id: 10, word: a, count: 4, eventTime: 1662303791904|2022-09-04 23:03:11
23:33:22,903 Source      [] - id: 11, word: a, count: 1, eventTime: 1662303795918|2022-09-04 23:03:15
23:33:23,908 Source      [] - id: 12, word: a, count: 6, eventTime: 1662303779883|2022-09-04 23:02:59
延迟链路> (12,a,6,1662303779883)
23:33:24,913 Source      [] - id: 13, word: a, count: 2, eventTime: 1662303846254|2022-09-04 23:04:06
23:33:25,198 Sum         [] - word: a, count: 8, ids: [6, 8, 10, 11], window: [2022-09-04 23:03:00, 2022-09-04 23:04:00], watermark: 1662303841253|2022-09-04 23:04:01
(a,8)
23:33:25,927 Sum         [] - word: a, count: 2, ids: [13], window: [2022-09-04 23:04:00, 2022-09-04 23:05:00], watermark: 9223372036854775807|292278994-08-17 15:12:55
(a,2)
```
从上面我们可以看到 id = 12 延迟到达而没有被处理的数据记录会输出到侧输出流中等待下一步的处理，这样我们就可以保证所有的数据不会丢失。

## 3. Watermark 和 AllowedLateness 区别

基于事件时间的流式处理，虽然提供了 Watermark 机制，却只能一定程度上解决数据的乱序问题，一般情况下 Watermark 也不会把延迟设置得太大。但是真实业务场景的数据延迟可能会非常严重，即使通过 Watermark 也无法等到所有的延迟数据进入窗口再进行处理，Flink 默认会将这种迟到的数据做丢弃处理，但是有些时候用户希望即使在数据延迟严重的情况下，仍然能得到正确的计算结果，此时就需要 AllowedLateness 机制来对迟到的数据进行特殊处理。

Watermark 和 AllowedLateness 到底有什么区别呢？
- Watermark 主要是为了解决数据乱序到达的问题；通过 Watermark 机制来处理 out-of-order 的问题，属于全局性的延迟处理，通常说的乱序问题的解决办法，就是指这类；
- AllowedLateness 只能应用在窗口算子上，用来解决窗口触发后数据迟到后的问题；Late Element 问题就是指这类。

当 Watermark 大于窗口结束时间（window.maxTimestamp()）加允许的最大延迟时间（allowedLateness），窗口就会被销毁。当 数据记录时间戳（element.getTimestamp()）加加允许的最大延迟时间（allowedLateness） > Watermark，元素就会落入窗口内。
