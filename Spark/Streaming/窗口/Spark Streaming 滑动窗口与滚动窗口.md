Spark Streaming 也支持窗口计算，它允许你在一个滑动窗口数据上应用transformation算子。下图阐明了这个滑动窗口。

![](1)

如上图显示，窗口在源 DStream 上滑动，可以对位于窗内的源 RDDs 进行聚合和转换，产生窗口化的 DStream 的 RDDs。在上图中，程序在三个时间单元的数据上进行窗口操作，并且每两个时间单元滑动一次。这说明，任何一个窗口操作都需要指定两个参数：
- 窗口长度：窗口的持续时间
- 滑动的时间间隔：窗口操作执行的时间间隔

> 这两个参数必须是源 DStream 的批时间间隔的倍数。

## 1. 滑动窗口

Spark Streaming 中最基本的窗口定义是 DStream 上的 window() 操作。该转换会创建一个带窗口的新 DStream，然后继续执行转换操作。

### 批次间隔

窗口流是通过将原始流中的多个 RDD 合并成一个 RDD 来创建的，因此滑动间隔一定是批次间隔的倍数，并且窗口的间隔也是滑动间隔的倍数。假设批次间隔为 5 秒，并且有一个 DStream 叫 `dStream`，那么 `dStream.window(30, 9)` 是不合法的，因为滑动间隔 9 不是批次间隔 5 的倍数，可以调整为 `dStream.window(30, 10)`；`dStream.window(40, 25)` 也是不合法的，尽管这里的窗口大小和滑动间隔都是批次间隔的倍数，但是窗口大小不是滑动间隔的倍数，可以调整为 `dStream.window(50, 25)`。

窗口大小是批次间隔的倍数，滑动间隔是批次间隔的倍数，窗口大小是滑动间隔的倍数。可以理解批次间隔是窗口流中时间间隔的不可分割的最小原子单位。此外需要注意的是滑动间隔要小于窗口大小，这样才能有效计算。

## 2. 滚动窗口

滚动窗口是一种特殊的滑动窗口，其滑动间隔等于窗口大小。通过 DStream 上的 window() 函数可以轻松实现一个滚动窗口：
```java
// 10s一个批次
JavaStreamingContext ssc = new JavaStreamingContext(sparkContext, Durations.seconds(10));

// 以端口 9100 作为输入源创建 DStream
JavaReceiverInputDStream<String> lines = ssc.socketTextStream(hostName, port);

// 将每行文本切分为单词
JavaPairDStream<String, Integer> wordCounts = lines.window(Durations.seconds(60), Durations.seconds(60)) // 1分钟的滚动窗口
        .flatMap(new FlatMapFunction<String, String>() {
            @Override
            public Iterator<String> call(String x) {
                return Arrays.asList(x.split("\\s+")).iterator();
            }
        })
        .mapToPair(new PairFunction<String, String, Integer>() {
            @Override
            public Tuple2<String, Integer> call(String word) {
                return new Tuple2<>(word, 1);
            }
        })
        .reduceByKey(new Function2<Integer, Integer, Integer>() {
            @Override
            public Integer call(Integer count1, Integer count2) {
                return count1 + count2;
            }
        });
// 输出
wordCounts.print();
```

```
-------------------------------------------
Time: 1735721630000 ms
-------------------------------------------
(d,65)
(b,65)
(a,65)
(c,65)
-------------------------------------------
Time: 1735721690000 ms
-------------------------------------------
(d,59)
(b,59)
(a,59)
(c,59)
-------------------------------------------
Time: 1735721750000 ms
-------------------------------------------
(d,60)
(b,60)
(a,60)
(c,60)
```

### 如何设置窗口大小

> 窗口大小与批次间隔的关系

窗口流是通过将原始流中的多个 RDD 合并成一个 RDD 来创建的，因此窗口大小一定是批次间隔的整数倍数。一般来说，只要是批次间隔的倍数，都可以作为窗口的长度。

此外需要注意的是窗口的间隔与流处理程序启动的开始时间是对齐的。假设批次间隔为 2 分钟、窗口长度为 30 分钟，如果应用程序的启动时间是10:01，那么窗口会在 10:31、11:01、11:31 等窗口间隔上触发计算。











。。。
