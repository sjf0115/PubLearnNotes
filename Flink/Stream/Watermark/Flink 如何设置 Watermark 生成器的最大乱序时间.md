---
layout: post
author: sjf0115
title: Flink 如何设置 Watermark 生成器的最大乱序时间
date: 2026-05-18 18:30:01
tags:
  - Flink

categories: Flink
permalink: flink-stream-how-to-set-watermark-max-out-of-orderness
---

> Flink 版本：1.13

## 1. 引言

在使用 Flink 基于事件时间（EventTime）进行窗口计算时，Watermark 的最大乱序时间（MaxOutOfOrderness）是一个至关重要的参数。设置得太小，大量迟到数据会被丢弃，影响计算准确性；设置得太大，窗口触发延迟增加，实时性下降。

那么，**如何科学地确定最大乱序时间？** 本文介绍两种实用方法：经验主义法和精准分析法。

---

## 2. 背景知识

在深入探讨之前，先回顾几个关键概念：
- **Watermark**：用于衡量事件时间推进的标记，语义为"所有时间戳 ≤ Watermark 的事件都已到达"
- **MaxOutOfOrderness**：最大可容忍的乱序时间，Watermark = 当前最大事件时间 - MaxOutOfOrderness - 1
- **迟到数据**：事件到达时，其所属窗口已经被 Watermark 触发计算，该数据即为迟到数据

设置 MaxOutOfOrderness 本质上是在 **数据准确性** 和 **处理延迟** 之间做权衡：

| MaxOutOfOrderness | 准确性 | 延迟 | 状态开销 |
|---|---|---|---|
| 过小 | 低（丢弃多） | 低 | 小 |
| 过大 | 高（丢弃少） | 高 | 大 |
| 合适 | 可接受 | 可接受 | 可控 |

---

## 3. 方法一：经验主义法

### 3.1 思路

根据历史经验直接设定一个最大乱序时间，然后通过监控指标观察效果，不断迭代调整。

### 3.2 操作步骤

**第一步：根据经验设置初始值**

例如，根据历史经验，大部分数据源的最大乱序时间不会超过 1min，我们就可以直接将最大乱序时间设置为 1min：
```java
DataStream<Event> stream = source
    .assignTimestampsAndWatermarks(
        WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofMinutes(1))
            .withTimestampAssigner((event, timestamp) -> event.getEventTime())
    );
```

**第二步：通过 Metrics 监控迟到数据量**

在作业运行过程中，通过 Flink Web UI 中算子的 Metrics 模块查看 `numLateRecordsDropped` 指标，该指标表示当前 SubTask 丢弃了多少条迟到的数据。

> **注意**：如果使用旁路输出（SideOutput）的方式将迟到数据输出，Flink 的 SubTask 将不会统计 `numLateRecordsDropped` 指标。

**第三步：不断迭代调整**

通过观察丢弃比例，不断调整最大乱序时间，将数据乱序的影响降低到可接受的误差范围内。例如：

| 最大乱序时间 | 正常计算数据占比 | 是否可接受 |
|---|---|---|
| 1min | 98.5% | 不可接受 |
| 2min | 98.8% | 不可接受 |
| 3min | 99.0% | 可接受 ✓ |

### 3.3 优缺点

| 优点 | 缺点 |
|---|---|
| 简单直观，操作门槛低 | 无法精准分析乱序分布 |
| 快速上手，适合大多数场景 | 需要多次迭代调整 |
| 不需要额外开发 | 依赖人工经验判断 |

---

## 4. 方法二：精准分析法

### 4.1 思路

通过编写专门的 Flink 作业来精准探查数据的乱序分布情况，从而科学地确定最大乱序时间。

### 4.2 核心原理

要精准探查数据乱序，首先需要理解 **Flink 时间窗口算子如何判断数据迟到**：
- 时间窗口算子通过 Watermark 维护事件时间时钟
- 当事件时间时钟推进超过窗口的最大时间戳时，触发窗口计算
- 如果一条数据所属窗口的最大时间戳 **小于** 当前事件时间时钟，说明该窗口已被触发，这条数据就是迟到数据

判断条件可以总结为：
```
如果 watermark >= windowMaxTimestamp → 数据迟到（窗口已触发）
如果 watermark <  windowMaxTimestamp → 数据正常（窗口未触发）
```

### 4.3 实现方案

使用一个 `Source → KeyBy/KeyedProcess → Sink` 的 Flink 作业来统计乱序数据的整体分布：
```java
private static final Logger LOG = LoggerFactory.getLogger(CalculateMaxOutOfOrderness.class);
private static final Gson gson = new GsonBuilder().create();
private static final Integer maxOutOfOrderness = 5;
private static final Long windowSize = 60000L;

public static void main(String[] args) throws Exception {
    final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
    env.setParallelism(1);

    // 单词流
    DataStreamSource<WordCountTimestamp> source = env.addSource(new WordCountOutOfOrderSource());
    // 定义 Watermark 策略 - 乱序流
    DataStream<WordCountTimestamp> words = source.assignTimestampsAndWatermarks(
            WatermarkStrategy
                    // 定义 Watermark 最大容忍5秒的延迟
                    .<WordCountTimestamp>forBoundedOutOfOrderness(Duration.ofSeconds(maxOutOfOrderness))
                    // 提取时间戳
                    .withTimestampAssigner(new SerializableTimestampAssigner<WordCountTimestamp>() {
                        @Override
                        public long extractTimestamp(WordCountTimestamp wc, long recordTimestamp) {
                            return wc.getTimestamp();
                        }
                    })
    );

    // 计算窗口延迟时间
    DataStream<LateTimeRecord> result = words
            // 分组
            .keyBy(new KeySelector<WordCountTimestamp, String>() {
                @Override
                public String getKey(WordCountTimestamp wc) throws Exception {
                    return wc.getWord();
                }
            })
            .process(new KeyedProcessFunction<String, WordCountTimestamp, LateTimeRecord>() {
                @Override
                public void processElement(WordCountTimestamp wc,
                                           KeyedProcessFunction<String, WordCountTimestamp, LateTimeRecord>.Context context,
                                           Collector<LateTimeRecord> collector) throws Exception {
                    // 元素时间戳
                    Long recordTimestamp = wc.getTimestamp();
                    // 当前事件时间时钟（即当前 Watermark）
                    long watermark = context.timerService().currentWatermark();
                    // 当前处理时间
                    long processingTime = context.timerService().currentProcessingTime();
                    // 计算该条数据所属 1分钟窗口的最大时间戳
                    long windowMaxTimestamp = getWindowMaxTimestamp(wc.getTimestamp(), windowSize);
                    // 计算延迟时间（乱序时长）
                    long lateTimestamp = watermark - windowMaxTimestamp;

                    LateTimeRecord record = new LateTimeRecord();
                    record.setRecordTimestamp(recordTimestamp);
                    record.setWatermark(watermark);
                    record.setProcessingTime(processingTime);
                    record.setWindowMaxTimestamp(windowMaxTimestamp);
                    record.setLateTimestamp(lateTimestamp);
                    LOG.info("数据延迟时间：{}", gson.toJson(record));
                    collector.collect(record);
                }
            });

    result.print();
    env.execute("BoundedWatermarkStrategyExample");
}

// 窗口最大时间戳
public static long getWindowMaxTimestamp(long timestamp, long windowSize) {
    return getWindowStartTimestamp(timestamp, windowSize) + windowSize - 1;
}

// 窗口开始时间戳
public static long getWindowStartTimestamp(long timestamp, long windowSize) {
    return timestamp - (timestamp + windowSize) % windowSize;
}

private static class LateTimeRecord {
    // 元素时间戳
    Long recordTimestamp;
    // 当前事件时间时间戳（即当前 Watermark）
    Long watermark;
    // 当前处理时间时间戳
    Long processingTime;
    // 该数据所属窗口最大时间戳
    Long windowMaxTimestamp;
    // 延迟时间（乱序时长）
    Long lateTimestamp ;

    public Long getRecordTimestamp() {
        return recordTimestamp;
    }

    public void setRecordTimestamp(Long recordTimestamp) {
        this.recordTimestamp = recordTimestamp;
    }

    public Long getWatermark() {
        return watermark;
    }

    public void setWatermark(Long watermark) {
        this.watermark = watermark;
    }

    public Long getProcessingTime() {
        return processingTime;
    }

    public void setProcessingTime(Long processingTime) {
        this.processingTime = processingTime;
    }

    public Long getWindowMaxTimestamp() {
        return windowMaxTimestamp;
    }

    public void setWindowMaxTimestamp(Long windowMaxTimestamp) {
        this.windowMaxTimestamp = windowMaxTimestamp;
    }

    public Long getLateTimestamp() {
        return lateTimestamp;
    }

    public void setLateTimestamp(Long lateTimestamp) {
        this.lateTimestamp = lateTimestamp;
    }
}
```

### 4.4 核心字段说明

| 字段 | 含义 | 计算方式 |
|---|---|---|
| `watermark` | 当前 SubTask 的事件时间时钟 | `context.timerService().currentWatermark()` |
| `windowMaxTimestamp` | 数据所属窗口的最大时间戳 | `eventTime - (eventTime % windowSize) + windowSize - 1` |
| `lateTimestamp` | 乱序时长 | `watermark - windowMaxTimestamp` |

### 4.5 测算步骤

**第一步**：KeyedProcess 算子的 SubTask 每读入一条数据，通过运行时上下文获取当前 SubTask 的事件时间时钟 `watermark`。

**第二步**：根据该条数据的事件时间戳计算其所属窗口的最大时间戳 `windowMaxTimestamp`。

**第三步**：计算 `watermark - windowMaxTimestamp` 的结果，即数据的乱序时长，保存到 `lateTimestamp` 字段并输出。

**第四步**：根据输出数据的 `lateTimestamp` 字段对乱序时长进行统计分析：

| lateTimestamp 范围 | 含义 |
|---|---|
| `< 0` | 数据到达时窗口尚未触发，正常计算 |
| `≥ 0` | 数据到达时窗口已触发，属于迟到数据 |

### 4.6 统计示例

假设统计结果如下：

| 乱序时长分布 | 数据占比 |
|---|---|
| `lateTimestamp < 0`（无乱序） | 98% |
| `0 ≤ lateTimestamp < 1min` | 0.5% |
| `1min ≤ lateTimestamp < 3min` | 0.5% |
| `3min ≤ lateTimestamp < 10min` | 1% |

从上述分布可以看出：
- 98% 的数据没有发生乱序
- 剩余 2% 的数据发生了乱序，且乱序时长都在 10min 以内

基于此分析：
- 如果业务可接受 2% 的数据丢失，MaxOutOfOrderness 设为 **0**（即不等待）
- 如果要求 99% 以上准确率，MaxOutOfOrderness 设为 **3min**
- 如果要求 99.5% 以上准确率，MaxOutOfOrderness 设为 **10min**

### 4.7 注意事项

> **重要提示**：测算得到的结果只代表测算那一段时间内的数据乱序情况，不能代表这条数据流今后的乱序时长分布。

虽然可能出现乱序大于测算上限的情况，但这通常是小概率事件。大多数情况下，一条数据流的时延分布是比较稳定的，上述测算工作依然具有很高的参考价值。

**建议**：
- 选择业务高峰期进行测算，结果更具代表性
- 测算时间跨度建议覆盖至少一个完整业务周期（如一天或一周）
- 定期重新测算，发现数据乱序特征是否发生变化

### 4.8 优缺点

| 优点 | 缺点 |
|---|---|
| 精准量化乱序分布 | 需要额外开发测算作业 |
| 有数据支撑决策 | 需要运行一段时间才能得出结论 |
| 可做持续监控 | 测算结果有时效性 |

---

## 5. 最佳实践

### 5.1 选择建议

| 场景 | 推荐方法 |
|---|---|
| 快速上线，对乱序容忍度高 | 经验主义法 |
| 数据质量要求高，需要精准控制 | 精准分析法 |
| 初次接入新数据源 | 先用精准分析法探查，再确定参数 |
| 线上作业优化调参 | 经验主义法（观察 Metrics 迭代） |

### 5.2 综合策略

在生产实践中，推荐采用**两种方法结合**的策略：

1. **首次上线**：先用精准分析法运行探查作业 1~2 天，得到乱序分布
2. **确定参数**：根据分布结果和业务可接受的丢失率确定 MaxOutOfOrderness
3. **持续监控**：上线后通过 `numLateRecordsDropped` 指标持续监控
4. **定期校验**：每隔一段时间重新运行探查作业，确认分布是否变化

### 5.3 兜底方案：AllowedLateness + SideOutput

即使设置了合理的 MaxOutOfOrderness，仍可能有极少量数据超出预期延迟。此时可以配合使用 `allowedLateness` + 旁路输出作为兜底：

```java
DataStream<Event> result = stream
    .keyBy(Event::getKey)
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    .allowedLateness(Time.minutes(5))        // 允许额外 5min 的迟到
    .sideOutputLateData(lateOutputTag)       // 超过 allowedLateness 的数据旁路输出
    .aggregate(new MyAggregateFunction());

// 获取旁路输出的迟到数据，可写入日志或二次处理
DataStream<Event> lateStream = result.getSideOutput(lateOutputTag);
```

**三层防护体系**：

```
第一层：MaxOutOfOrderness（全局，容忍 x 时间的乱序）
         │
         ▼
第二层：AllowedLateness（窗口级，窗口触发后再等 y 时间）
         │
         ▼
第三层：SideOutput（兜底，超过所有容忍时间的数据旁路输出）
```

---

## 6. 总结

| 方法 | 适用场景 | 核心做法 |
|---|---|---|
| 经验主义法 | 快速上线、迭代调优 | 设置经验值 → 观察 `numLateRecordsDropped` → 迭代 |
| 精准分析法 | 新数据源、高精度场景 | 编写探查作业 → 统计 `lateTimestamp` 分布 → 科学决策 |

核心要点：
1. MaxOutOfOrderness 的本质是**准确性 vs 延迟**的权衡
2. 经验主义法简单直接，通过 `numLateRecordsDropped` 指标迭代调整
3. 精准分析法通过 `watermark - windowMaxTimestamp` 精确量化乱序分布
4. 生产环境建议两种方法结合使用，并配合 AllowedLateness + SideOutput 做兜底
5. 乱序分布可能随时间变化，需要定期重新评估

---

参考：
- [Generating Watermarks - Apache Flink](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/dev/datastream/event-time/generating_watermarks/)
- [Flink Watermark 机制](https://smartsi.blog.csdn.net/article/details/112553662)
- [Flink 轻松理解 Watermark](https://smartsi.blog.csdn.net/article/details/126551181)
