## 1. 时间特性 TimeCharacteristic

当你指定一个窗口来收集每分钟的记录时，如何判定每个窗口中需要包含哪些事件呢？在 Flink DataStream API 中，你可以使用时间特性来告知 Flink 在创建窗口时如何定义时间。时间特性是 StreamExecutionEnvironment 的一个属性，目前可以接收如下三种值，分别对应上述三种类型的时间类型：
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
可以通过 StreamExecutionEnvironment 的 setStreamTimeCharacteristic 方法来设置时间特性：
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
通过上述代码可以看到设置时间特性其本质是设置 Watermark 的时间间隔。如果设置的是 ProcessingTime 则 Watermark 的时间间隔为 0，禁用 WWatermark；如果设置的是 EventTime 或者 IngestionTime，则设置为 200 毫秒。当然这是一个默认值，如果默认值不适用于您的应用程序，可以通过 ExecutionConfig 的 setAutoWatermarkInterval(long) 方法重新修改。

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

## 2. 弃用时间特性

在 Flink 1.12 中，默认的时间特性已更改为事件时间 EventTime，因此不再需要调用 setStreamTimeCharacteristic 来启用事件时间的支持。如果你想显示使用处理时间 ProcessingTime，只需要通过 `ExecutionConfig.setAutoWatermarkInterval(long)` 方法将 Watermark 时间间隔设置为 0 禁用 Watermark 即可。如果你想使用摄入时间 IngestionTime，还需要手动设置适当的 WatermarkStrategy 策略。

> [FLINK-19319](https://issues.apache.org/jira/browse/FLINK-19319)
