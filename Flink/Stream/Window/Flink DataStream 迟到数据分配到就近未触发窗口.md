在 [Flink DataStream 窗口延迟数据处理 AllowedLateness](https://smartsi.blog.csdn.net/article/details/126964028) 中我们详细介绍了 Flink DataStream API 应对迟到数据的三种解决方案：
- **方案一**：直接丢弃迟到数据记录（事件时间窗口的默认行为）
- **方案二**：通过 `allowedLateness()` 容忍一定时间内的延迟，基于迟到数据更新计算结果
- **方案三**：通过 `sideOutputLateData()` 将迟到没有被处理的数据记录输出到侧输出流中，由下游单独处理

这三种方案各有适用场景，但是有一个共同的局限：**无法保证数据的准确性达到 100%**：
- 方案一直接丢弃，丢失即意味着数据不完整；
- 方案二的 AllowedLateness 终归是有限的，超过这个时间就会丢弃；
- 方案三虽然不丢数据，但侧输出流中的数据如何回填到主链路的结果中是个工程难题（往往需要外部存储和 Upsert 写入），增加了复杂度。

用户往往不希望乱序数据被直接丢弃，并且不想引入侧输出流回填这种复杂链路，而是希望乱序数据也能被时间窗口算子正常处理。能否有一种方案做到 **不丢任何一条数据，且全部参与窗口计算**？答案是肯定的——**将迟到数据分配到就近还没有触发的窗口中**。

本文基于 Flink 1.13.6 版本，详细介绍这种方案的实现思路、核心代码与运行效果。

## 2. 核心思路：迟到数据的窗口"修正"

### 2.1 思路图解

正常情况下，窗口分配器（WindowAssigner）根据数据元素的事件时间为其分配窗口。但当一条数据延迟到达时：

```
                           Watermark
                              ↓
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ [23:02-23:03]│    │ [23:03-23:04]│    │ [23:04-23:05]│
  │   已触发     │     │   未触发     │     │   未触发     │
  └─────────────┘     └─────────────┘     └─────────────┘
        ↑
        │ id=9 (23:02:58)
        │ id=12 (23:02:59)
        │ 本应归属，但窗口已经销毁/触发
```

如果按默认行为，这些迟到数据会被丢弃。**我们的做法是不丢，而是把它"挪"到当前 Watermark 所在的就近未触发窗口**：

```
                           Watermark
                              ↓
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ [23:02-23:03]│    │ [23:03-23:04]│    │ [23:04-23:05]│
  │   已触发     │  →  │ + id=9      │     │   未触发     │
  └─────────────┘     │ + id=12      │     └─────────────┘
                      └─────────────┘
```

以计算每种商品每1min的销售额（事件时间语义）为例，假设 AllowLateness 机制是关闭的，当前Flink作业中SubTask的Watermark是9:10:50，下一个将要被触发计算的时间窗口是[9:10:00, 9:11:00)，那么接下来如果有一个时间为9:01:01的数据输入到时间窗口算子中。正常情况下这条数据会被丢弃，而我们所期望的优化方案不是丢弃这条数据，而是把这条数据放入还没有被触发的最早的那个窗口里，也就是将这条数据放在窗口[9:10:00, 9:11:00)中，虽然数据所在的时间窗口有偏差，但这样至少可以保证数据不丢失。


如果遇到乱序数据，就把这条乱序数据放入最近的一个还没有被触发计算的时间窗口中，保证不会由于数据乱序而丢数。使用ProcessFunction的实现逻辑如下：通过ProcessFunction提供的定时器来实现时间窗口的计算逻辑并自定义乱序不丢数的逻辑，最终的实现如代码清单7-4所示。

### 2.2 这种"挪窗"的取舍

这种方案的核心权衡是：
- **优点**：所有数据都参与窗口计算，结果在统计口径上保证 100% 完整
- **代价**：迟到数据被划归到"它本不应该属于的窗口"，**窗口的语义被弱化**——`[23:03, 23:04)` 这个窗口的统计结果实际上既包含了原本属于它的数据，也包含了从 `[23:02, 23:03)` 迟到补录过来的数据

因此，这种方案适用于：
- 业务关注 **总量正确**，对窗口归属时间不敏感（如日累计、PV/UV 总和、对账总额）
- 不希望引入侧输出流回填的复杂链路
- 不希望长时间保留窗口状态（不依赖 AllowedLateness）

不适用于：
- 需要严格按照原始事件时间分窗输出（如分钟级业务指标趋势分析）

## 3. 实现方案：用 KeyedProcessFunction 自己接管窗口逻辑

由于 Flink 内置的 `WindowAssigner`（如 `TumblingEventTimeWindows`）一旦把数据分配到已触发的窗口就直接走丢弃逻辑，**没有钩子可以让我们改写归属窗口**。所以我们干脆抛开 `.window(...)`，使用 `KeyedProcessFunction` 自己实现一套"窗口分配 + 状态聚合 + 定时器触发"的逻辑。通过 ProcessFunction 提供的定时器来实现时间窗口的计算逻辑并自定义乱序不丢数的逻辑。整体执行流程如下：
```
   元素到达
       │
       ▼
processElement
  │
  ├── 1. 计算元素本应归属的窗口 [windowStart, windowEnd)
  │
  ├── 2. 判断是否迟到（windowEnd <= currentWatermark）
  │       └── 若迟到，把窗口修正为当前 Watermark 所在的窗口
  │
  ├── 3. 在窗口结束时间注册事件时间定时器
  │
  └── 4. 把元素聚合到 windowStart 对应的状态中

   Watermark 推进 → 触发 onTimer
       │
       ▼
onTimer
  │
  └── 遍历状态，输出所有 windowEnd ≤ timer 的窗口结果，并清除状态
```
### 3.1 当前元素实际归属的窗口

getWindowStartWithOffset：窗口对齐公式
```java
public static long getWindowStartWithOffset(long timestamp, long offset, long windowSize) {
    long remainder = (timestamp - offset) % windowSize;
    return remainder < 0L ? timestamp - (remainder + windowSize) : timestamp - remainder;
}
```

这个方法和 Flink 内置的 `TimeWindow.getWindowStartWithOffset` 等价，作用是把任意时间戳对齐到窗口起点。

举例（窗口大小 60s，offset = 0）：

| timestamp（毫秒） | timestamp（可读） | windowStart |
|---|---|---|
| 1662303772840 | 23:02:52 | 1662303720000（23:02:00） |
| 1662303778877 | 23:02:58 | 1662303720000（23:02:00） |
| 1662303781890 | 23:03:01 | 1662303780000（23:03:00） |

也就是说，**任何落在 `[23:02:00, 23:03:00)` 内的时间戳都会对齐到 `1662303720000` 这一个 windowStart**——这是我们用 `MapState` 把同一窗口的数据聚合在一起的基础。

### 3.2 迟到判定与窗口修正

```java
if (windowEnd <= currentWatermark) {
    windowStart = getWindowStartWithOffset(currentWatermark, 0L, windowSize);
    windowEnd = windowStart + windowSize;
}
```

这一步骤是整个方案的灵魂，它承担了两件事：判断一条数据是否迟到、以及把迟到数据修正到就近未触发的窗口。下面我们重点拆解为什么这样写就能判定迟到。

要理解这个判定，先回到 Flink 中 Watermark 的定义：Watermark = T 表示数据流向下游声明，**事件时间 ≤ T 的数据已经全部到达**，之后再出现事件时间 ≤ T 的数据都视为迟到数据。对一个事件时间滚动窗口 `[windowStart, windowEnd)`（左闭右开），Flink 内置 `EventTimeTrigger` 的触发条件是：当 Watermark ≥ windowEnd 时，触发该窗口的计算并清理状态。这是因为窗口区间右开——`windowEnd` 这一刻不再属于本窗口(下一窗口)，一旦 Watermark 推进到 `windowEnd`，就意味着「事件时间 ≤ windowEnd 的数据都到齐了」，本窗口内（即 `< windowEnd`）的数据自然也都到齐了，可以安全触发。

一条新到的数据，它本应归属的窗口是 `[windowStart, windowEnd)`。`currentWatermark ≥ windowEnd` 表明窗口 `[windowStart, windowEnd)` 已经触发过（或正要在本条 Watermark 推进时触发）。既然窗口已经触发并清理过状态，再补一条本应属于它的数据进来——就是 **迟到数据**。所以 `windowEnd <= currentWatermark` 等价于「这条数据所属的窗口已经/即将被 Watermark 关掉」，再写到这个窗口里没有意义，必须修正。

> 为什么是 `<=` 而不是 `<`
这一点容易被忽略，但很关键：**等号必须保留**。原因还是“区间右开”：
- 假设 `windowSize = 60s`，窗口 `[23:02:00, 23:03:00)`，则 `windowEnd = 23:03:00`
- 当 Watermark 第一次推进到 `23:03:00` 时，根据触发条件 `Watermark ≥ windowEnd`，窗口已被触发
- 此时若再来一条 `timestamp = 23:02:55` 的数据，计算得 `windowEnd = 23:03:00`，恰好等于 `currentWatermark`
- 如果写成 `<`，这条数据会被判为「未迟到」，仍然写入已被清理的 `[23:02:00, 23:03:00)`，但由于该窗口的定时器已经触发并不会再次触发，这条数据就 **永久滞留在状态里**——既不参与计算，也不会被释放，等同于丢失

> 所以等号一定要带上，确保「已经被 Watermark 关掉的窗口」全部走修正分支。

判定为迟到后，用 `currentWatermark` 替代元素自身的 `timestamp` 去对齐：
```java
windowStart = getWindowStartWithOffset(currentWatermark, 0L, windowSize);
windowEnd = windowStart + windowSize;
```

- Watermark 一定落在 **正在累积或刚刚开始累积** 的窗口里（该窗口 `[windowStart, windowEnd)` 满足 `windowStart ≤ Watermark < windowEnd`）
- 这个窗口的 `windowEnd > currentWatermark`，定时器还没有到期，状态还在
- 所以这个对齐结果就是“就近还没有触发的窗口”——迟到数据写进去后，会被这个窗口在未来的某次定时器触发时一起输出

### 3.3 状态聚合

```java
private transient MapState<Long, WordCountTimestamp> windowState;
```

为什么用 `MapState` 而不是 `ValueState`？
- **同一个 Key（如 word=a）下，一段时间内会有多个未触发窗口同时存在**：当前窗口、由迟到数据修正过来的窗口、再之后的窗口……
- `MapState<Long, T>` 用 windowStart 做 key，恰好对应到具体窗口，互不干扰
- `onTimer` 触发时只清理已到期的 entry，未到期的窗口状态继续保留

### 3.4 事件时间定时器

当每个元素到达时为每个窗口(结束时间)注册事件时间定时器：
```java
context.timerService().registerEventTimeTimer(windowEnd);
```

> 事件时间定时器在 Flink 内部是去重的：**对同一 Key 注册相同时间戳的定时器，只会触发一次**。所以即使一个窗口里来了 100 条数据、调用了 100 次 `registerEventTimeTimer(windowEnd)`，最终也只产生一个定时器。

当事件时间到达时会触发 `onTimer` 的处理，触发窗口结束时间小于等于定时器时间的所有窗口：
```java
public void onTimer(long timestamp, KeyedProcessFunction<String, WordCountTimestamp, WordCountTimestamp>.OnTimerContext ctx, Collector<WordCountTimestamp> out) throws Exception {
    Iterator<Map.Entry<Long, WordCountTimestamp>> iterator = this.windowState.entries().iterator();
    while (iterator.hasNext()) {
        Map.Entry<Long, WordCountTimestamp> entry = iterator.next();
        // 窗口结束时间小于等于当前触发的定时器时间 触发窗口
        if (entry.getKey() + windowTimeSize.toMilliseconds() <= timestamp) {
            out.collect(entry.getValue());
            iterator.remove();
        }
    }
}
```
> 这里没有限定"当前定时器时间戳必须等于 windowEnd"，而是用 `<=` 兜底——这样可以保证即使因为某些原因有窗口的定时器被错过（如数据全部迟到导致 windowEnd 早已被 Watermark 超过），也能在下一次定时器触发时一并输出，不会出现"状态留在 MapState 里永远不被释放"的内存泄漏。

## 4. 示例

下面是完整代码：
```java
public class LatenessRecentWindowExample {
    private static final Logger LOG = LoggerFactory.getLogger(LatenessRecentWindowExample.class);
    private static final Time windowTimeSize = Time.minutes(1);

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(1);

        // 单词流
        DataStreamSource<WordCountTimestamp> source = env.addSource(new WordCountOutOfOrderSource());
        // 定义 Watermark 策略
        DataStream<WordCountTimestamp> words = source
                .assignTimestampsAndWatermarks(
                        WatermarkStrategy.<WordCountTimestamp>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                                .withTimestampAssigner(new SerializableTimestampAssigner<WordCountTimestamp>() {
                                    @Override
                                    public long extractTimestamp(WordCountTimestamp wc, long recordTimestamp) {
                                        return wc.getTimestamp();
                                    }
                                })
                );

        // 窗口计算
        DataStream<WordCountTimestamp> stream = words
                .keyBy(new KeySelector<WordCountTimestamp, String>() {
                    @Override
                    public String getKey(WordCountTimestamp wc) throws Exception {
                        return wc.getWord();
                    }
                })
                .process(new KeyedProcessFunction<String, WordCountTimestamp, WordCountTimestamp>() {
                    private transient MapState<Long, WordCountTimestamp> windowState;

                    @Override
                    public void open(Configuration parameters) throws Exception {
                        // 保存窗口中的数据：windowStart -> 聚合结果
                        windowState = getRuntimeContext().getMapState(
                                new MapStateDescriptor<>("windowState", Long.class, WordCountTimestamp.class)
                        );
                    }

                    @Override
                    public void processElement(WordCountTimestamp wc,
                                               Context context,
                                               Collector<WordCountTimestamp> out) throws Exception {
                        Long timestamp = wc.getTimestamp();
                        long currentWatermark = context.timerService().currentWatermark();

                        // 1. 计算当前元素实际归属的窗口
                        long windowSize = windowTimeSize.toMilliseconds();
                        long windowStart = getWindowStartWithOffset(timestamp, 0L, windowSize);
                        long windowEnd = windowStart + windowSize;

                        // 2. 判断是否是迟到数据，如果是则修正窗口为就近未触发窗口
                        if (windowEnd <= currentWatermark) {
                            windowStart = getWindowStartWithOffset(currentWatermark, 0L, windowSize);
                            windowEnd = windowStart + windowSize;
                        }

                        // 3. 注册事件时间定时器（窗口结束时间触发）
                        context.timerService().registerEventTimeTimer(windowEnd);

                        // 4. 状态聚合
                        WordCountTimestamp wcState = windowState.get(windowStart);
                        if (Objects.equals(wcState, null)) {
                            wcState = new WordCountTimestamp();
                            wcState.setId(wc.getId());
                            wcState.setWord(wc.getWord());
                            wcState.setTimestamp(timestamp);
                            wcState.setFrequency(wc.getFrequency());
                            windowState.put(windowStart, wcState);
                        } else {
                            wcState.setId(wcState.getId() + "," + wc.getId());
                            wcState.setWord(wc.getWord());
                            wcState.setTimestamp(Math.max(wcState.getTimestamp(), wc.getTimestamp()));
                            wcState.setFrequency(wcState.getFrequency() + wc.getFrequency());
                            windowState.put(windowStart, wcState);
                        }
                    }

                    @Override
                    public void onTimer(long timestamp,
                                        OnTimerContext ctx,
                                        Collector<WordCountTimestamp> out) throws Exception {
                        Iterator<Map.Entry<Long, WordCountTimestamp>> iterator = windowState.entries().iterator();
                        while (iterator.hasNext()) {
                            Map.Entry<Long, WordCountTimestamp> entry = iterator.next();
                            // 窗口结束时间小于等于当前触发的定时器时间 → 触发窗口
                            if (entry.getKey() + windowTimeSize.toMilliseconds() <= timestamp) {
                                out.collect(entry.getValue());
                                iterator.remove();
                            }
                        }
                    }
                });

        stream.print();
        env.execute("LatenessRecentWindowExample");
    }

    public static long getWindowStartWithOffset(long timestamp, long offset, long windowSize) {
        long remainder = (timestamp - offset) % windowSize;
        return remainder < 0L ? timestamp - (remainder + windowSize) : timestamp - remainder;
    }
}
```

> 完整代码请查阅 [LatenessRecentWindowExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/late/LatenessRecentWindowExample.java)

假设输入数据如下所示：
```
// 格式：行为唯一标识Id, 单词, 出现次数, 事件时间戳
1,  a, 2, 1662303772840 // 23:02:52
2,  a, 1, 1662303770844 // 23:02:50
3,  a, 3, 1662303773848 // 23:02:53
4,  a, 2, 1662303774866 // 23:02:54
5,  a, 1, 1662303777839 // 23:02:57
6,  a, 2, 1662303784887 // 23:03:04
7,  a, 3, 1662303776894 // 23:02:56
8,  a, 1, 1662303786891 // 23:03:06
9,  a, 5, 1662303778877 // 23:02:58
10, a, 4, 1662303791904 // 23:03:11
11, a, 1, 1662303795918 // 23:03:15
12, a, 6, 1662303779883 // 23:02:59
13, a, 2, 1662303846254 // 23:04:06
```

实际运行效果如下所示：
```java
22:38:40,101 INFO  WordCountOutOfOrderSource [] - id: 1, word: a, frequency: 2, eventTime: 1662303772840|2022-09-04 23:02:52
22:38:41,109 INFO  WordCountOutOfOrderSource [] - id: 2, word: a, frequency: 1, eventTime: 1662303770844|2022-09-04 23:02:50
22:38:42,112 INFO  WordCountOutOfOrderSource [] - id: 3, word: a, frequency: 3, eventTime: 1662303773848|2022-09-04 23:02:53
22:38:43,117 INFO  WordCountOutOfOrderSource [] - id: 4, word: a, frequency: 2, eventTime: 1662303774866|2022-09-04 23:02:54
22:38:44,123 INFO  WordCountOutOfOrderSource [] - id: 5, word: a, frequency: 1, eventTime: 1662303777839|2022-09-04 23:02:57
22:38:45,128 INFO  WordCountOutOfOrderSource [] - id: 6, word: a, frequency: 2, eventTime: 1662303784887|2022-09-04 23:03:04
22:38:46,132 INFO  WordCountOutOfOrderSource [] - id: 7, word: a, frequency: 3, eventTime: 1662303776894|2022-09-04 23:02:56
22:38:47,138 INFO  WordCountOutOfOrderSource [] - id: 8, word: a, frequency: 1, eventTime: 1662303786891|2022-09-04 23:03:06
WordCountTimestamp{id='1,2,3,4,5,7', word='a', frequency=12, timestamp=1662303777839}
22:38:48,143 INFO  WordCountOutOfOrderSource [] - id: 9, word: a, frequency: 5, eventTime: 1662303778877|2022-09-04 23:02:58
22:38:49,146 INFO  WordCountOutOfOrderSource [] - id: 10, word: a, frequency: 4, eventTime: 1662303791904|2022-09-04 23:03:11
22:38:50,152 INFO  WordCountOutOfOrderSource [] - id: 11, word: a, frequency: 1, eventTime: 1662303795918|2022-09-04 23:03:15
22:38:51,157 INFO  WordCountOutOfOrderSource [] - id: 12, word: a, frequency: 6, eventTime: 1662303779883|2022-09-04 23:02:59
22:38:52,159 INFO  WordCountOutOfOrderSource [] - id: 13, word: a, frequency: 2, eventTime: 1662303846254|2022-09-04 23:04:06
WordCountTimestamp{id='6,8,9,10,11,12', word='a', frequency=19, timestamp=1662303795918}
WordCountTimestamp{id='13', word='a', frequency=2, timestamp=1662303846254}
```

按时间顺序拆解一下三次窗口触发：

**第一次触发**：id = 8 到达，Watermark 推进到 `1662303781890`（23:03:01），超过 `[23:02:00, 23:03:00)` 窗口结束时间，触发该窗口
- 累计 id：1, 2, 3, 4, 5, 7
- 累计 frequency：2 + 1 + 3 + 2 + 1 + 3 = **12**
- id = 6 不在该窗口内（事件时间 23:03:04，归属下一窗口）

**第二次触发**：id = 13 到达，Watermark 推进到 `1662303841253`（23:04:01），超过 `[23:03:00, 23:04:00)` 窗口结束时间，触发该窗口
- 累计 id：6, 8, 9, 10, 11, 12
- 累计 frequency：2 + 1 + 5 + 4 + 1 + 6 = **19**
- 注意：**id = 9 和 id = 12 原本属于 `[23:02:00, 23:03:00)` 窗口**，但因为到达时该窗口已经触发，根据修正逻辑被分配到了当前 Watermark 所在的 `[23:03:00, 23:04:00)` 窗口，从而和 id = 6, 8, 10, 11 一起参与了这次计算

**第三次触发**：作业结束 Watermark 推进到 `Long.MAX_VALUE`，触发 `[23:04:00, 23:05:00)` 窗口
- 累计 id：13
- 累计 frequency：**2**

从上面可以看懂 **没有任何一条数据被丢弃，全部参与了窗口计算** ——这正是该方案的核心优势。

## 6. 与之前三种方案的对比

把四种方案放在一起对比：

| 维度 | 丢弃迟到（默认） | AllowedLateness | sideOutputLateData | **就近未触发窗口（本文）** |
|---|---|---|---|---|
| 是否丢数据 | 丢 | 超过容忍时间会丢 | 不丢（侧流） | **不丢（全部进入主链路）** |
| 数据回填复杂度 | 不需要 | 不需要 | 需要外部存储 + Upsert | **不需要** |
| 窗口归属准确性 | 准确（丢弃迟到） | 准确（更新原窗口） | 准确（侧流原始时间） | **不准确（迟到数据被挪到就近窗口）** |
| 窗口状态保留时长 | 短 | 长（窗口结束 + AllowedLateness） | 短 | **短** |
| 窗口结果触发次数 | 1 次 | 多次（每个迟到数据触发一次更新） | 1 次 | **1 次** |
| 实现复杂度 | 极低 | 低 | 中 | **中（需要自己写 ProcessFunction）** |
| 适用场景 | 容忍少量丢失 | 业务能接受多次更新输出 | 需要保留迟到数据原始信息 | **关注总量、不希望多次更新输出** |

AllowedLateness 方案是 **把窗口保留更久，迟到数据回到自己原本的窗口**，那么一个窗口可能被触发多次，下游需要支持更新，本方案是 **窗口准时销毁，迟到数据补到就近未触发窗口**，每个窗口只触发一次。
侧输出流方案 **保留了迟到数据的原始事件时间**，但要求下游有外部存储能"找到原窗口结果并 Upsert"，本方案 **修改了迟到数据的归属**，但全部走主链路，下游无需任何回填逻辑


### 7. 注意

每个 Key 的 `MapState` 同时存活的 entry 数量约等于"当前活跃窗口数"。对于 1 分钟窗口，正常情况下只会有 1 ~ 2 个 entry。如果出现长时间数据稀疏断流（Watermark 不推进），entry 不会增长——因为新数据按事件时间继续往同一个 windowStart 聚合。但如果出现 **事件时间大跳跃**（如某个 Key 突然来了一条 24 小时之后的数据），会注册一个非常远的定时器，导致 `MapState` 中的旧窗口因为 Watermark 一直没追上而长期占内存。生产中建议加一个 **最大保留窗口数** 的兜底逻辑：
```java
if (windowState.entries().size() > MAX_PENDING_WINDOWS) {
    // 强制冲刷最早的窗口
    ...
}
```

此外不可避免的出现数据"穿越"现象：由于迟到数据被挪到了未触发窗口，一个 watermark=23:03:01 时刻触发的窗口结果，可能在 watermark=23:04:01 时才被加上迟到数据合并到下一个窗口里。**下游看到的窗口结果在时间维度上是单调的，但具体到分钟级业务指标上"前一分钟少、后一分钟多"是常态**。如果业务有趋势分析诉求，要提前与产品对齐。

## 8. 总结

回到本文开头的问题：**有没有一种方案能做到不丢任何一条迟到数据，且不引入侧输出流回填的复杂链路？** 答案就是本文介绍的 **将迟到数据分配到就近未触发的窗口**。它的核心代码不到 80 行，关键只有 4 步：
1. 用 `getWindowStartWithOffset` 把元素事件时间对齐到本应归属窗口
2. 用 `windowEnd <= currentWatermark` 判定迟到，并把窗口修正为当前 Watermark 所在窗口
3. 用 `MapState<windowStart, 聚合结果>` 维护多个并存的活跃窗口
4. 用事件时间定时器 + `<=` 比较触发并清理状态

它不是"银弹"——代价是窗口的语义被弱化，迟到数据被合并到了非自身归属的时间段。但当业务关注 **总量正确、链路简单、append-only 输出** 时，它比 AllowedLateness 和 sideOutputLateData 都更轻量。

至此，Flink DataStream 中处理迟到数据的四种方案就介绍完毕。在选型时，把 **业务对窗口归属时间的敏感度** 作为第一选择维度，再综合下游能力、状态成本、链路复杂度做最终决策。
