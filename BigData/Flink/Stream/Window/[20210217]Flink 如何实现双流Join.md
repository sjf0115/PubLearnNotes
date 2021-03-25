
### 1. Window Join

### 2. Window CoGroup

### 3. Interval Join

Flink 中基于 DataStream 的 Join，只能实现在同一个窗口的两个数据流进行 Join，但是在实际中常常会存在数据乱序或者延时的情况，导致两个流的数据进度不一致，就会出现数据跨窗口的情况，那么数据就无法在同一个窗口内 Join。Flink 基于 KeyedStream 提供的 Interval Join 机制可以对两个 keyedStream 进行 Join, 按照相同的 key 在一个相对数据时间的时间段内进行 Join。按照指定字段以及右流相对左流偏移的时间区间进行关联，即：
```
b.timestamp ∈ [a.timestamp + lowerBound, a.timestamp + upperBound]
```
或者
```
a.timestamp + lowerBound <= b.timestamp <= a.timestamp + upperBound
```
![]()

> 其中a和b分别是上图中绿色流和橘色流中的元素，并且有相同的 key。只需要保证 lowerBound 永远小于等于 upperBound 即可，均可以为正数或者负数。

从上面可以看出绿色流可以晚到 lowerBound（lowerBound为负的话）时间，也可以早到 upperBound（upperBound为正的话）时间。也可以理解为橘色流中的每个元素可以和绿色流指中定区间的元素进行 Join。需要注意的是 Interval Join 当前仅支持事件时间：
```java
public IntervalJoined<T1, T2, KEY> between(Time lowerBound, Time upperBound) {
			if (timeBehaviour != TimeBehaviour.EventTime) {
				throw new UnsupportedTimeCharacteristicException("Time-bounded stream joins are only supported in event time");
			}
}
```

下面我们具体看看如何实现一个 Interval Join：
```java
// 绿色流
DataStream<Tuple3<String, String, String>> greenStream = greenSource.map(new MapFunction<String, Tuple3<String, String, String>>() {
    @Override
    public Tuple3<String, String, String> map(String str) throws Exception {
        String[] params = str.split(",");
        String key = params[0];
        String eventTime = params[2];
        String value = params[1];
        LOG.info("[绿色流] Key: {}, Value: {}, EventTime: {}", key, value, eventTime);
        return new Tuple3<>(key, value, eventTime);
    }
}).assignTimestampsAndWatermarks(
        // 需要指定Watermark
        WatermarkStrategy.<Tuple3<String, String, String>>forBoundedOutOfOrderness(Duration.ofMillis(100))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, String, String>>() {
                    @Override
                    public long extractTimestamp(Tuple3<String, String, String> element, long recordTimestamp) {
                        Long timeStamp = null;
                        try {
                            timeStamp = DateUtil.date2TimeStamp(element.f2, "yyyy-MM-dd HH:mm:ss");
                        } catch (ParseException e) {
                            e.printStackTrace();
                        }
                        return timeStamp;
                    }
                })
);

// 橘色流
DataStream<Tuple3<String, String, String>> orangeStream = orangeSource.map(new MapFunction<String, Tuple3<String, String, String>>() {
    @Override
    public Tuple3<String, String, String> map(String str) throws Exception {
        String[] params = str.split(",");
        String key = params[0];
        String value = params[1];
        String eventTime = params[2];
        LOG.info("[橘色流] Key: {}, Value: {}, EventTime: {}", key, value, eventTime);
        return new Tuple3<>(key, value, eventTime);
    }
}).assignTimestampsAndWatermarks(
        // 需要指定Watermark
        WatermarkStrategy.<Tuple3<String, String, String>>forBoundedOutOfOrderness(Duration.ofMillis(100))
                .withTimestampAssigner(new SerializableTimestampAssigner<Tuple3<String, String, String>>() {
                    @Override
                    public long extractTimestamp(Tuple3<String, String, String> element, long recordTimestamp) {
                        Long timeStamp = null;
                        try {
                            timeStamp = DateUtil.date2TimeStamp(element.f2, "yyyy-MM-dd HH:mm:ss");
                        } catch (ParseException e) {
                            e.printStackTrace();
                        }
                        return timeStamp;
                    }
                })
);

KeySelector<Tuple3<String, String, String>, String> keySelector = new KeySelector<Tuple3<String, String, String>, String>() {
    @Override
    public String getKey(Tuple3<String, String, String> value) throws Exception {
        return value.f0;
    }
};

// 双流合并
DataStream result = orangeStream
    .keyBy(keySelector)
    .intervalJoin(greenStream.keyBy(keySelector))
    .between(Time.seconds(-2), Time.seconds(1))
    .process(new ProcessJoinFunction<Tuple3<String, String, String>, Tuple3<String, String, String>, String>() {
        @Override
        public void processElement(Tuple3<String, String, String> left,
                                   Tuple3<String, String, String> right,
                                   Context ctx, Collector<String> out) throws Exception {
            LOG.info("[合并流] Key: {}, Value: {}, EventTime: {}",
                    left.f0, "[" + left.f1 + ", " + right.f1 + "]",
                    "[" + right.f2 + "|" + ctx.getRightTimestamp() + ", " + right.f2 + "|" + ctx.getLeftTimestamp() + "]"
            );
            out.collect(left.f1 + ", " + right.f1);
        }
    });
```
需要注意的是 Interval Join 当前仅支持事件时间，所以需要为流指定事件时间戳。

```
绿色流：
c,0,2021-03-22 12:09:01
c,1,2021-03-22 12:09:01
c,3,2021-03-22 12:21:02
c,4,2021-03-22 12:45:03
c,4,2021-03-22 13:39:03

橘色流：
c,0,2021-03-22 12:09:01
c,1,2021-03-22 12:09:01
c,2,2021-03-22 12:21:02
c,3,2021-03-22 12:21:02
c,4,2021-03-22 12:45:03
c,5,2021-03-22 12:45:03
c,6,2021-03-22 13:14:04
c,7,2021-03-22 13:14:04
c,4,2021-03-22 13:39:03
```
