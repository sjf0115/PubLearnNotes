在无界流中，数据是持续不断产生的。当我们要计算“过去一小时的销售额”或“每分钟的异常用户数”时，必须明确一个问题："过去一小时"和"每分钟"是基于哪个时钟定义的？是数据产生时的世界时间（事件时间），还是数据到达Flink系统时的机器时间（处理时间）？

Flink提供了三种时间语义来回答这个问题：
- Event Time（事件时间）：使用数据元素自身携带的时间戳。这是最符合真实世界逻辑的时间语义，能处理乱序事件，但会带来一定的延迟。
- Ingestion Time（摄入时间）：数据进入Flink Source算子时的时间戳。是事件时间和处理时间的一个折中，开销比事件时间小，但不如事件时间准确。
- Processing Time（处理时间）：数据执行计算操作时，算子所在机器的系统时间。延时最低，但结果不确定性最大。

而时间特性（Time Characteristic），就是告诉 Flink 运行时，你应该使用哪种时间语义来驱动窗口计算、定时器等与时间相关的操作。

## 第一阶段：Flink 1.12 之前 - 显式设置时代

在 Flink 1.12 版本之前，我们需要在运行环境中显式地设置全局的时间特性。核心 API 是 `StreamExecutionEnvironment.setStreamTimeCharacteristic()`。目前可以接收如下三种值，分别对应上述三种类型的时间类型：
```java
public enum TimeCharacteristic {
    // 处理时间
    ProcessingTime,
    // 摄入时间
    IngestionTime,
    // 事件时间
    EventTime
}
```
> 在 1.12 之前，默认的时间特性是 TimeCharacteristic.ProcessingTime。

通过 `setStreamTimeCharacteristic()` 方法设置是当时最经典、最常用的方式：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

// 显式设置为事件时间
env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime);

// 或者设置为处理时间（默认）
// env.setStreamTimeCharacteristic(TimeCharacteristic.ProcessingTime);

// 或者设置为摄入时间（较少使用）
// env.setStreamTimeCharacteristic(TimeCharacteristic.IngestionTime);
```

通过 `setStreamTimeCharacteristic` 方法可以看出其本质是修改 Watermark 的发送时间间隔来设置时间特性：
```java
public void setStreamTimeCharacteristic(TimeCharacteristic characteristic) {
    this.timeCharacteristic = Preconditions.checkNotNull(characteristic);
    if (characteristic == TimeCharacteristic.ProcessingTime) {
        getConfig().setAutoWatermarkInterval(0);
    } else {
        getConfig().setAutoWatermarkInterval(200);
    }
}
```
如果设置的是 ProcessingTime 则 Watermark 的发送时间间隔为 0，即禁用 Watermark；如果设置的是 EventTime 或者 IngestionTime，则设置为 200 毫秒。当然这是一个默认值，如果默认值不适用于您的应用程序，可以通过 ExecutionConfig 的 `setAutoWatermarkInterval(long)` 方法重新修改。

如下展示了一个使用处理时间计算每分钟单词个数的示例，注意的是窗口的行为会与时间特性相匹配：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 设置Checkpoint
env.enableCheckpointing(1000L);
// 设置事件时间特性 处理时间
env.setStreamTimeCharacteristic(TimeCharacteristic.ProcessingTime);
DataStream<String> source = env.socketTextStream("localhost", 9100, "\n");
// Stream of (word, count)
DataStream<Tuple2<String, Long>> words = source
        .flatMap(new FlatMapFunction<String, Tuple2<String, Long>>() {
            @Override
            public void flatMap(String str, Collector<Tuple2<String, Long>> collector) throws Exception {
                String[] words = str.split("\\s+");
                for (String word : words) {
                    collector.collect(Tuple2.of(word, 1L));
                }
            }
        });

// 滚动窗口
DataStream<Tuple2<String, Long>> tumblingTimeWindowStream = words
        // 根据单词分组
        .keyBy(new KeySelector<Tuple2<String,Long>, String>() {
            @Override
            public String getKey(Tuple2<String, Long> tuple2) throws Exception {
                return tuple2.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .timeWindow(Time.minutes(1))
        // 求和
        .sum(1);
```

## 2. 第二阶段：Flink 1.12 及之后 - 隐式与默认时代

社区为了简化 API 并推动用户使用更准确的事件时间，做出了两项重大改变：
- 弃用显式设置方法：`setStreamTimeCharacteristic()` 被标记为` @Deprecated`。
- 改变默认行为：默认的时间语义不再是处理时间，而是自动切换为事件时间，但仅在必要时。

> [FLINK-19319](https://issues.apache.org/jira/browse/FLINK-19319)

在新的版本中，你不需要（也不应该）再调用 `env.setStreamTimeCharacteristic()` 了。取而代之是：只要你使用了事件时间相关的操作（如分配了 Watermark），Flink 就认为你在使用事件时间；否则，就默认使用处理时间。

如何选择时间特性？
- 如果你想使用处理时间（Processing Time）
  - 做法：什么都不用做。不要分配 Watermark，也不要使用事件时间定时器。
  - 原理：Flink 检测到你没有定义任何事件时间的要素，就会自动回退到处理时间。
- 如果你想使用事件时间（Event Time）
  - 做法：只需为你的 DataStream 分配 WatermarkStrategy。这是唯一且必须的步骤。
  - 原理：一旦你调用了`.assignTimestampsAndWatermarks()`，Flink 就会自动将后续所有基于时间的操作（如窗口、间隔连接）切换为事件时间模式。
- 如果你想使用摄入时间（Ingestion Time）
  - 做法：使用 `WatermarkStrategy.forIngestion()`。
  - 原理：摄入时间在内部被实现为一种特殊的事件时间，其时间戳是在 Source 任务中自动生成的，Watermark 也是自动生成的。
