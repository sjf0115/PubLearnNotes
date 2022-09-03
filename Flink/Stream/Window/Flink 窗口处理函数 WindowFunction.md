---
layout: post
author: smartsi
title: Flink 窗口处理函数 WindowFunction
date: 2021-02-06 22:38:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-windows-function
---

在之前的文章中我们已经了解了 Flink 的[窗口机制](https://smartsi.blog.csdn.net/article/details/126554021?spm=1001.2014.3001.5502)，并介绍了其中涉及的组件：WindowAssigner、WindowFunction、Trigger、Evictor。在 [Flink 窗口分配器 WindowAssigner](https://smartsi.blog.csdn.net/article/details/126652876) 中我们知道可以通过不同类型的窗口分配器 WindowAssigner 将元素分配到窗口中。在指定 WindowAssigner 后，需要在每个窗口上指定我们要执行的计算逻辑，这就是窗口函数（WindowFunction）的责任。一旦系统确定窗口准备好处理数据，窗口函数就会被调用来处理窗口中的每个元素。

按照窗口计算原理划分，可用于处理窗口数据的函数有两种：
- 增量聚合函数：增量聚合函数在窗口内以状态形式存储某个值，每个新加入的窗口的元素对该值进行更新，即窗口中只维护中间结果的状态值，不需要缓存原始数据。这种函数计算性能高，占有存储空间少，因为 Flink 可以在每个元素到达窗口时增量地进行聚合。代表函数有 ReduceFunction，AggregateFunction。
- 全量窗口函数：全量窗口函数对属于该窗口的元素全部进行缓存，只有等到窗口触发的时候，才对所有的原始元素进行汇总计算。这种函数不会像增量聚合函数那样有效率，使用的代价相对较高，性能相对差一些，如果接入的数据量比较大或者窗口时间比较长，就可能会导致计算性能的下降。此外也通常需要占用更多的空间。不过可以获取一个窗口内所有元素的迭代器以及元素所在窗口的其他元信息，可以支持更复杂的操作。代表函数有 ProcessWindowFunction。

下面将会介绍每种 Windows Function 在 Flink 中如何使用。

### 1. ReduceFunction

ReduceFunction 定义了对输入的两个相同类型的元素按照指定的计算逻辑进行集合，然后输出相同类型的一个结果元素。窗口只需要一个在状态中存储的当前聚合结果，以及一个和 ReduceFunction 的输入输出类型相同的值。每当收到一个新元素时，算子都会以该元素和从窗口状态取出的当前聚合值为参数调用 ReduceFunction，随后会用 ReduceFunction 的结果更新窗口状态中的值。

在窗口上使用 ReduceFunction 的优点是只需为每个窗口维护一个常数级别的小状态，此外函数的接口也很简单。然而， ReduceFunction 的应用场景也有一定的局限，由于输入和输出类型必须一致，所以通常仅限于一些简单的聚合。

如下代码所示，使用 ReduceFunction 计算每个单词出现的次数，只需要在 reduce() 函数中指定 ReduceFunction 即可：
```java
DataStream<Tuple2<String, Integer>> wordsCount = ...;
DataStream<Tuple2<String, Integer>> result = wordsCount
        // 根据单词分组
        .keyBy(new KeySelector<Tuple2<String,Integer>, String>() {
            @Override
            public String getKey(Tuple2<String, Integer> value) throws Exception {
                LOG.info("[Source] word: {}", value.f0);
                return value.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
        // ReduceFunction 相同单词求和
        .reduce(new ReduceFunction<Tuple2<String, Integer>>() {
            @Override
            public Tuple2<String, Integer> reduce(Tuple2<String, Integer> value1, Tuple2<String, Integer> value2) throws Exception {
                int count = value1.f1 + value2.f1;
                LOG.info("[ReduceFunction] word: {}, count: {}", value1.f0, count);
                return new Tuple2(value1.f0, count);
            }
        });
```

> 完整代码请查阅:[ReduceFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/function/ReduceFunctionExample.java)

实际效果如下：
```
2022-09-03 15:52:07,129 INFO  xxx.SimpleWordSource      [] - word: b
2022-09-03 15:52:17,135 INFO  xxx.SimpleWordSource      [] - word: b
2022-09-03 15:52:17,189 INFO  xxx.ReduceFunctionExample [] - word: b, count: 2
2022-09-03 15:52:27,136 INFO  xxx.SimpleWordSource      [] - word: a
2022-09-03 15:52:37,140 INFO  xxx.SimpleWordSource      [] - word: a
2022-09-03 15:52:37,221 INFO  xxx.ReduceFunctionExample [] - word: a, count: 2
2022-09-03 15:52:47,141 INFO  xxx.SimpleWordSource      [] - word: b
2022-09-03 15:52:47,235 INFO  xxx.ReduceFunctionExample [] - word: b, count: 3
2022-09-03 15:52:57,142 INFO  xxx.SimpleWordSource      [] - word: a
2022-09-03 15:52:57,177 INFO  xxx.ReduceFunctionExample [] - word: a, count: 3
2022-09-03 15:53:00,002 INFO  xxx.PrintLogSinkFunction  [] - (b,3)
2022-09-03 15:53:00,003 INFO  xxx.PrintLogSinkFunction  [] - (a,3)
2022-09-03 15:53:07,147 INFO  xxx.SimpleWordSource      [] - word: a
2022-09-03 15:53:17,152 INFO  xxx.SimpleWordSource      [] - word: b
2022-09-03 15:53:27,154 INFO  xxx.SimpleWordSource      [] - word: b
2022-09-03 15:53:27,224 INFO  xxx.ReduceFunctionExample [] - word: b, count: 2
2022-09-03 15:53:37,159 INFO  xxx.SimpleWordSource      [] - word: b
2022-09-03 15:53:37,255 INFO  xxx.ReduceFunctionExample [] - word: b, count: 3
2022-09-03 15:53:47,164 INFO  xxx.SimpleWordSource      [] - word: a
2022-09-03 15:53:47,194 INFO  xxx.ReduceFunctionExample [] - word: a, count: 2
2022-09-03 15:53:57,167 INFO  xxx.SimpleWordSource      [] - word: b
2022-09-03 15:53:57,223 INFO  xxx.ReduceFunctionExample [] - word: b, count: 4
2022-09-03 15:54:00,002 INFO  xxx.PrintLogSinkFunction  [] - (a,2)
2022-09-03 15:54:00,002 INFO  xxx.PrintLogSinkFunction  [] - (b,4)
...
```

### 2. AggregateFunction

和 ReduceFunction 类似，AggregateFunction 也是以增量方式处理窗口内的元素，也需要在状态中存储当前的聚合结果。不同的是，AggregateFunction 是 ReduceFunction 的一个通用版本，相对于 ReduceFunction 更加灵活，但实现复杂度也相对更高。AggregateFunction 的中间数据和输出数据类型不再依赖输入类型。

AggregateFunction 接口中有三个参数：输入元素类型（IN）、累加器类型（ACC）以及输出元素类型（OUT），此外还定义了四个需要重写的方法，其中 createAccumulator() 方法创建 accumulator，add() 方法定义数据的添加逻辑，getResult() 定义了根据 accumulator 计算结果的逻辑，merge() 方法定义了合并 accumulator 的逻辑：
```java
public interface AggregateFunction<IN, ACC, OUT> extends Function, Serializable {
  // 创建 accumulator
  ACC createAccumulator();
  // 定义数据的添加逻辑
	ACC add(IN value, ACC accumulator);
  // 定义了根据 accumulator 计算结果的逻辑
	OUT getResult(ACC accumulator);
  // 定义了合并 accumulator 的逻辑
	ACC merge(ACC a, ACC b);
}
```

如下代码所示，使用 AggregateFunction 函数计算每个传感器的平均温度，其中累加器负责维护不断变化的温度总和和数量，通过 getResult 计算最终的温度平均值：
```java
DataStreamSource<Tuple2<String, Integer>> source;
// 计算1分钟内的平均温度
SingleOutputStreamOperator<Tuple2<String, Double>> stream = source
        // 分组
        .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
            @Override
            public String getKey(Tuple2<String, Integer> value) throws Exception {
                return value.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
        .aggregate(new AvgTemperatureAggregateFunction());

/**
 * 自定义AggregateFunction
 *      IN：Tuple2<String, Integer> 输入类型
 *      ACC：Tuple3<String, Integer, Integer> -> <Key, Sum, Count> 中间结果类型
 *      OUT：Tuple2<String, Double> 输出类型
 */
 private static class AvgTemperatureAggregateFunction implements AggregateFunction<
       Tuple2<String, Integer>,
       Tuple3<String, Integer, Integer>,
       Tuple2<String, Double>> {
   @Override
   public Tuple3<String, Integer, Integer> createAccumulator() {
       // 累加器 Key, Sum, Count
       return Tuple3.of("", 0, 0);
   }

   @Override
   public Tuple3<String, Integer, Integer> add(Tuple2<String, Integer> value, Tuple3<String, Integer, Integer> accumulator) {
       // 输入一个元素 更新累加器
       return Tuple3.of(value.f0, accumulator.f1 + value.f1, accumulator.f2 + 1);
   }

   @Override
   public Tuple2<String, Double> getResult(Tuple3<String, Integer, Integer> accumulator) {
       // 从累加器中获取总和和个数计算平均值
       double avgTemperature = ((double) accumulator.f1) / accumulator.f2;
       LOG.info("id: {}, sum: {}℃, count: {}, avg: {}℃", accumulator.f0, accumulator.f1, accumulator.f2, avgTemperature);
       return Tuple2.of(accumulator.f0, avgTemperature);
   }

   @Override
   public Tuple3<String, Integer, Integer> merge(Tuple3<String, Integer, Integer> a, Tuple3<String, Integer, Integer> b) {
       // 累加器合并
       return Tuple3.of(a.f0, a.f1 + b.f1, a.f2 + b.f2);
   }
}
```

> 完整代码请查阅:[AggregateFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/function/AggregateFunctionExample.java)

实际效果如下：
```
2022-09-03 17:24:36,466 INFO  xxx.SimpleTemperatureSource  [] - sensorId: a, temperature: 27
2022-09-03 17:24:46,469 INFO  xxx.SimpleTemperatureSource  [] - sensorId: b, temperature: 21
2022-09-03 17:24:56,473 INFO  xxx.SimpleTemperatureSource  [] - sensorId: c, temperature: 30
2022-09-03 17:25:00,008 INFO  xxx.AggregateFunctionExample [] - id: a, sum: 27℃, count: 1, avg: 27.0℃
2022-09-03 17:25:00,008 INFO  xxx.PrintLogSinkFunction     [] - (a,27.0)
2022-09-03 17:25:00,009 INFO  xxx.AggregateFunctionExample [] - id: c, sum: 30℃, count: 1, avg: 30.0℃
2022-09-03 17:25:00,009 INFO  xxx.PrintLogSinkFunction     [] - (c,30.0)
2022-09-03 17:25:00,010 INFO  xxx.AggregateFunctionExample [] - id: b, sum: 21℃, count: 1, avg: 21.0℃
2022-09-03 17:25:00,010 INFO  xxx.PrintLogSinkFunction     [] - (b,21.0)
2022-09-03 17:25:06,473 INFO  xxx.SimpleTemperatureSource  [] - sensorId: a, temperature: 25
2022-09-03 17:25:16,474 INFO  xxx.SimpleTemperatureSource  [] - sensorId: b, temperature: 25
2022-09-03 17:25:26,478 INFO  xxx.SimpleTemperatureSource  [] - sensorId: b, temperature: 30
2022-09-03 17:25:36,482 INFO  xxx.SimpleTemperatureSource  [] - sensorId: a, temperature: 26
2022-09-03 17:25:46,484 INFO  xxx.SimpleTemperatureSource  [] - sensorId: a, temperature: 30
2022-09-03 17:25:56,485 INFO  xxx.SimpleTemperatureSource  [] - sensorId: b, temperature: 30
2022-09-03 17:26:00,005 INFO  xxx.AggregateFunctionExample [] - id: a, sum: 81℃, count: 3, avg: 27.0℃
2022-09-03 17:26:00,005 INFO  xxx.PrintLogSinkFunction     [] - (a,27.0)
2022-09-03 17:26:00,006 INFO  xxx.AggregateFunctionExample [] - id: b, sum: 85℃, count: 3, avg: 28.3333℃
2022-09-03 17:26:00,006 INFO  xxx.PrintLogSinkFunction     [] - (b,28.3333)
2022-09-03 17:26:06,486 INFO  xxx.SimpleTemperatureSource  [] - sensorId: b, temperature: 27
2022-09-03 17:26:16,487 INFO  xxx.SimpleTemperatureSource  [] - sensorId: c, temperature: 29
2022-09-03 17:26:26,493 INFO  xxx.SimpleTemperatureSource  [] - sensorId: a, temperature: 29
2022-09-03 17:26:36,494 INFO  xxx.SimpleTemperatureSource  [] - sensorId: c, temperature: 22
2022-09-03 17:26:46,499 INFO  xxx.SimpleTemperatureSource  [] - sensorId: c, temperature: 23
2022-09-03 17:26:56,502 INFO  xxx.SimpleTemperatureSource  [] - sensorId: c, temperature: 29
2022-09-03 17:27:00,003 INFO  xxx.AggregateFunctionExample [] - id: b, sum: 27℃, count: 1, avg: 27.0℃
2022-09-03 17:27:00,004 INFO  xxx.PrintLogSinkFunction     [] - (b,27.0)
2022-09-03 17:27:00,004 INFO  xxx.AggregateFunctionExample [] - id: a, sum: 29℃, count: 1, avg: 29.0℃
2022-09-03 17:27:00,004 INFO  xxx.PrintLogSinkFunction     [] - (a,29.0)
2022-09-03 17:27:00,005 INFO  xxx.AggregateFunctionExample [] - id: c, sum: 103℃, count: 4, avg: 25.75℃
2022-09-03 17:27:00,005 INFO  xxx.PrintLogSinkFunction     [] - (c,25.75)
...
```

### 3. ProcessWindowFunction

前面提到的 ReduceFunction 和 AggregateFunction 都是基于中间状态实现增量计算的窗口函数。虽然已经满足绝大数的场景，然而有些时候我们可能还是需要窗口中的所有的数据元素（或者需要操作窗口中的状态和窗口元数据）来执行一些更加复杂的计算，例如计算窗口内数据的中值或者出现频率最高的值。这时就需要使用到 ProcessWindowFunction，可以实现对窗口内容执行任意计算。

ProcessWindowFunction 会获得窗口内所有元素的 Iterable 以及一个可以访问时间和状态信息的 Context 对象，这使得它可以比其他窗口函数提供更大的灵活性。这是以牺牲性能和资源消耗为代价的，因为不能增量进行聚合，而是需要在内部进行缓冲直到窗口被认为准备好进行处理为止。

ProcessWindowFunction 的结构如下所示，process() 方法在被调用时会传入窗口元素的 Key，一个用于访问窗口内所有元素的 Iterable 以及一个用于输出结果的 Collector。此外，该方法和其他处理方法一样都有一个 Context 参数。在 Context 对象中可以访问窗口的元数据（例如当前处理时间和 Watermark），用于管理单个窗口和每个 Key 的状态存储，以及用于发送数据的旁路输出：
```java
public abstract class ProcessWindowFunction<IN, OUT, KEY, W extends Window> extends AbstractRichFunction {
  private static final long serialVersionUID = 1L;
  // 执行窗口计算并输出
  public abstract void process(KEY key, Context context, Iterable<IN> elements, Collector<OUT> out) throws Exception;
  // 当窗口生命周期结束时清除中间状态
  public void clear(Context context) throws Exception {}
  // 包含窗口元数据的Context
  public abstract class Context implements java.io.Serializable {
    // 所属窗口
  	public abstract W window();
    // 当前处理时间
  	public abstract long currentProcessingTime();
    // 当前基于事件时间的Watermark
  	public abstract long currentWatermark();
    // 窗口的中间状态
  	public abstract KeyedStateStore windowState();
    // 每个Key对应的中间状态
  	public abstract KeyedStateStore globalState();
    // OutputTag输出数据
  	public abstract <X> void output(OutputTag<X> outputTag, X value);
  }
}
```
上面我们提过 Context 对象的一些功能，例如访问当前处理时间和事件时间等，此外 ProcessWindowFunction 的 Context 对象还提供了一些特有的功能。窗口的元数据通常会包含用于标识窗口的信息，例如时间窗口中的开始和结束时间。另一项功能是访问单个窗口的状态 WindowState 以及每个 Key 的全局状态 GlobalState。其中单个窗口的状态是指当前正在计算的窗口实例的状态，而全局状态指得是不属于任何一个窗口的 KeyedState。单个窗口状态用于维护同一个窗口内多次调用 process() 方法所需要的共享信息，这种多次调用可能是由于配置了允许数据迟到或者使用了自定义触发器。使用了单个窗口状态的 ProcessWindowFunction 需要实现 clear() 方法，在窗口清除前清理仅供当前窗口使用的状态。全局状态可用于在 Key 相同的多个窗口之间共享信息。

如下代码所示，使用 ProcessWindowFunction 完成基于窗口上的分组统计的功能，并输出窗口结束时间等元数据信息：
```java
// 最低温度和最高温度
SingleOutputStreamOperator<Tuple3<String, Integer, Integer>> stream = source
        // 分组
        .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {

            @Override
            public String getKey(Tuple2<String, Integer> value) throws Exception {
                return value.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
        // 窗口函数
        .process(new HighLowTemperatureProcessWindowFunction());

/**
 * 自定义实现 ProcessWindowFunction
 *      计算最高温度和最低温度
 */
private static class HighLowTemperatureProcessWindowFunction extends ProcessWindowFunction<
        Tuple2<String, Integer>, // 输入类型
        Tuple3<String, Integer, Integer>, // 输出类型
        String, // key 类型
        TimeWindow> {
    @Override
    public void process(String key, Context context, Iterable<Tuple2<String, Integer>> elements, Collector<Tuple3<String, Integer, Integer>> out) throws Exception {
        int lowTemperature = Integer.MAX_VALUE;
        int highTemperature = Integer.MIN_VALUE;
        List<Integer> temperatures = Lists.newArrayList();
        for (Tuple2<String, Integer> element : elements) {
            // 温度列表
            temperatures.add(element.f1);
            Integer temperature = element.f1;
            // 计算最低温度
            if (temperature < lowTemperature) {
                lowTemperature = temperature;
            }
            // 计算最高温度
            if (temperature > highTemperature) {
                highTemperature = temperature;
            }
        }
        // 时间窗口元数据
        TimeWindow window = context.window();
        long start = window.getStart();
        long end = window.getEnd();
        String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
        String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
        // 当前处理时间
        long currentProcessingTimeStamp = context.currentProcessingTime();
        String currentProcessingTime = DateUtil.timeStamp2Date(currentProcessingTimeStamp, "yyyy-MM-dd HH:mm:ss");
        LOG.info("sensorId: {}, List: {}, Low: {}, High: {}, Window: {}, ProcessingTime: {}",
                key, temperatures, lowTemperature, highTemperature,
                "[" + startTime + ", " + endTime + "]", currentProcessingTime
        );
        out.collect(Tuple3.of(temperatures.toString(), lowTemperature, highTemperature));
    }
}
```
> 完整代码请查阅:[ProcessWindowFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/function/ProcessWindowFunctionExample.java)

实际效果如下所示：
```
2022-09-03 17:40:10,108 INFO  xxx.SimpleTemperatureSource       [] - sensorId: c, temperature: 25
2022-09-03 17:40:20,109 INFO  xxx.SimpleTemperatureSource       [] - sensorId: c, temperature: 21
2022-09-03 17:40:30,110 INFO  xxx.SimpleTemperatureSource       [] - sensorId: c, temperature: 21
2022-09-03 17:40:40,111 INFO  xxx.SimpleTemperatureSource       [] - sensorId: c, temperature: 26
2022-09-03 17:40:50,112 INFO  xxx.SimpleTemperatureSource       [] - sensorId: a, temperature: 29
2022-09-03 17:41:00,023 INFO  xxx.ProcessWindowFunctionExample  [] - sensorId: c, List: [25, 21, 21, 26], Low: 21, High: 26, Window: [2022-09-03 17:40:00, 2022-09-03 17:41:00], ProcessingTime: 2022-09-03 17:41:00
2022-09-03 17:41:00,024 INFO  xxx.PrintLogSinkFunction          [] - ([25, 21, 21, 26],21,26)
2022-09-03 17:41:00,024 INFO  xxx.ProcessWindowFunctionExample  [] - sensorId: a, List: [29], Low: 29, High: 29, Window: [2022-09-03 17:40:00, 2022-09-03 17:41:00], ProcessingTime: 2022-09-03 17:41:00
2022-09-03 17:41:00,024 INFO  xxx.PrintLogSinkFunction          [] - ([29],29,29)
2022-09-03 17:41:00,117 INFO  xxx.SimpleTemperatureSource       [] - sensorId: b, temperature: 23
2022-09-03 17:41:10,121 INFO  xxx.SimpleTemperatureSource       [] - sensorId: b, temperature: 23
2022-09-03 17:41:20,126 INFO  xxx.SimpleTemperatureSource       [] - sensorId: b, temperature: 20
2022-09-03 17:41:30,129 INFO  xxx.SimpleTemperatureSource       [] - sensorId: b, temperature: 20
2022-09-03 17:41:40,135 INFO  xxx.SimpleTemperatureSource       [] - sensorId: b, temperature: 22
2022-09-03 17:41:50,139 INFO  xxx.SimpleTemperatureSource       [] - sensorId: b, temperature: 25
2022-09-03 17:42:00,001 INFO  xxx.ProcessWindowFunctionExample  [] - sensorId: b, List: [23, 23, 20, 20, 22, 25], Low: 20, High: 25, Window: [2022-09-03 17:41:00, 2022-09-03 17:42:00], ProcessingTime: 2022-09-03 17:42:00
2022-09-03 17:42:00,002 INFO  xxx.PrintLogSinkFunction          [] - ([23, 23, 20, 20, 22, 25],20,25)
2022-09-03 17:42:00,143 INFO  xxx.SimpleTemperatureSource       [] - sensorId: a, temperature: 20
2022-09-03 17:42:10,148 INFO  xxx.SimpleTemperatureSource       [] - sensorId: c, temperature: 26
2022-09-03 17:42:20,150 INFO  xxx.SimpleTemperatureSource       [] - sensorId: a, temperature: 24
2022-09-03 17:42:30,154 INFO  xxx.SimpleTemperatureSource       [] - sensorId: b, temperature: 28
2022-09-03 17:42:40,159 INFO  xxx.SimpleTemperatureSource       [] - sensorId: a, temperature: 25
2022-09-03 17:42:50,159 INFO  xxx.SimpleTemperatureSource       [] - sensorId: b, temperature: 21
2022-09-03 17:43:00,006 INFO  xxx.ProcessWindowFunctionExample  [] - sensorId: a, List: [20, 24, 25], Low: 20, High: 25, Window: [2022-09-03 17:42:00, 2022-09-03 17:43:00], ProcessingTime: 2022-09-03 17:43:00
2022-09-03 17:43:00,006 INFO  xxx.PrintLogSinkFunction          [] - ([20, 24, 25],20,25)
2022-09-03 17:43:00,007 INFO  xxx.ProcessWindowFunctionExample  [] - sensorId: b, List: [28, 21], Low: 21, High: 28, Window: [2022-09-03 17:42:00, 2022-09-03 17:43:00], ProcessingTime: 2022-09-03 17:43:00
2022-09-03 17:43:00,007 INFO  xxx.PrintLogSinkFunction          [] - ([28, 21],21,28)
2022-09-03 17:43:00,008 INFO  xxx.ProcessWindowFunctionExample  [] - sensorId: c, List: [26], Low: 26, High: 26, Window: [2022-09-03 17:42:00, 2022-09-03 17:43:00], ProcessingTime: 2022-09-03 17:43:00
2022-09-03 17:43:00,008 INFO  xxx.PrintLogSinkFunction          [] - ([26],26,26)
...
```

### 4. 使用增量聚合的 ProcessWindowFunction

ReduceFunction，AggregateFunction 等这些增量函数虽然在一定程度上能够提升窗口的计算性能，但是这些函数的灵活性却不及 ProcessWindowFunction，例如对窗口状态的操作以及对窗口中元数据获取等。但是如果使用 ProcessWindowFunction 来完成一些基础的增量计算却比较浪费资源。这时可以使用 ProcessWindowFunction 与 ReduceFunction 或者 AggregateFunction 等增量函数组合使用，以充分利用两种函数各自的优势。元素到达窗口时对其使用 ReduceFunction 或者 AggregateFunction 增量函数进行增量聚合；当窗口触发器触发时再向 ProcessWindowFunction 提供聚合结果，这样传递给 ProcessWindowFunction.process() 方法的 Iterable 参数内将只有一个增量聚合值。这样我们就可以实现增量计算窗口，同时还可以访问窗口的元数据信息。

> 我们也可以使用旧版的 WindowFunction 代替 ProcessWindowFunction 进行增量窗口聚合。

在 DataStream API 中实现 ProcessWindowFunction 与 ReduceFunction 或者 AggregateFunction 等增量函数组合使用，需要将 ProcessWindowFunction 分别作为 Reduce() 和 aggregate() 函数的第二个参数即可。

#### 4.1 ReduceFunction 与 ProcessWindowFunction 组合使用

如下代码示例展示了如何将 ReduceFunction 增量函数与 ProcessWindowFunction 函数组合使用来实现 ReduceFunction 示例中功能(计算每个单词出现的次数)：
```java
// Stream of (word, 1)
DataStream<Tuple2<String, Integer>> wordsCount = source.flatMap(new FlatMapFunction<String, Tuple2<String, Integer>>() {
    @Override
    public void flatMap(String value, Collector out) {
        for (String word : value.split("\\s")) {
            out.collect(Tuple2.of(word, 1));
        }
    }
});

// 滚动窗口
SingleOutputStreamOperator<Tuple4<String, Integer, String, String>> stream = wordsCount
        // 根据单词分组
        .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
            @Override
            public String getKey(Tuple2<String, Integer> value) throws Exception {
                return value.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
        // ReduceFunction 和 ProcessWindowFunction 组合使用
        .reduce(new CountReduceFunction(), new WordsCountProcessWindowFunction());

/**
 * 自定义ReduceFunction：
 *      计算每个单词出现的个数
 */
private static class CountReduceFunction implements ReduceFunction<Tuple2<String, Integer>> {
    public Tuple2<String, Integer> reduce(Tuple2<String, Integer> wordCount1, Tuple2<String, Integer> wordCount2) {
        int count = wordCount1.f1 + wordCount2.f1;
        LOG.info("word: {}, count: {}", wordCount1.f0, count);
        return new Tuple2(wordCount1.f0, count);
    }
}

/**
 * 自定义ProcessWindowFunction：
 *      获取窗口元信息
 */
private static class WordsCountProcessWindowFunction extends ProcessWindowFunction<
        Tuple2<String, Integer>,
        Tuple4<String, Integer, String, String>,
        String,
        TimeWindow> {
    @Override
    public void process(String s, Context context, Iterable<Tuple2<String, Integer>> elements, Collector<Tuple4<String, Integer, String, String>> out) throws Exception {
        // 窗口聚合结果值
        Tuple2<String, Integer> wordCount = elements.iterator().next();
        String word = wordCount.f0;
        Integer count = wordCount.f1;
        // 窗口元信息
        TimeWindow window = context.window();
        long start = window.getStart();
        long end = window.getEnd();
        String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
        String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
        // 当前处理时间
        long currentProcessingTimeStamp = context.currentProcessingTime();
        String currentProcessingTime = DateUtil.timeStamp2Date(currentProcessingTimeStamp, "yyyy-MM-dd HH:mm:ss");
        LOG.info("word: {}, count: {}, window: {}, processingTime: {}",
                word, count,
                "[" + startTime + ", " + endTime + "]", currentProcessingTime
        );
        // 输出
        out.collect(Tuple4.of(word, count, startTime, endTime));
    }
}
```
> 完整代码请查阅:[ReduceProcessWindowFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/function/ReduceProcessWindowFunctionExample.java)

实际效果如下：
```
2022-09-03 17:55:39,217 INFO  xxx.SimpleWordSource                    [] - word: b
2022-09-03 17:55:49,223 INFO  xxx.SimpleWordSource                    [] - word: b
2022-09-03 17:55:49,274 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: b, count: 2
2022-09-03 17:55:59,227 INFO  xxx.SimpleWordSource                    [] - word: a
2022-09-03 17:56:00,005 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: b, count: 2, window: [2022-09-03 17:55:00, 2022-09-03 17:56:00], processingTime: 2022-09-03 17:56:00
2022-09-03 17:56:00,005 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: a, count: 1, window: [2022-09-03 17:55:00, 2022-09-03 17:56:00], processingTime: 2022-09-03 17:56:00
2022-09-03 17:56:00,005 INFO  xxx.PrintLogSinkFunction                [] - (b,2,2022-09-03 17:55:00,2022-09-03 17:56:00)
2022-09-03 17:56:00,006 INFO  xxx.PrintLogSinkFunction                [] - (a,1,2022-09-03 17:55:00,2022-09-03 17:56:00)
2022-09-03 17:56:09,229 INFO  xxx.SimpleWordSource                    [] - word: a
2022-09-03 17:56:19,233 INFO  xxx.SimpleWordSource                    [] - word: b
2022-09-03 17:56:29,237 INFO  xxx.SimpleWordSource                    [] - word: b
2022-09-03 17:56:29,311 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: b, count: 2
2022-09-03 17:56:39,238 INFO  xxx.SimpleWordSource                    [] - word: a
2022-09-03 17:56:39,247 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: a, count: 2
2022-09-03 17:56:49,239 INFO  xxx.SimpleWordSource                    [] - word: b
2022-09-03 17:56:49,284 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: b, count: 3
2022-09-03 17:56:59,240 INFO  xxx.SimpleWordSource                    [] - word: b
2022-09-03 17:56:59,328 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: b, count: 4
2022-09-03 17:57:00,003 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: a, count: 2, window: [2022-09-03 17:56:00, 2022-09-03 17:57:00], processingTime: 2022-09-03 17:57:00
2022-09-03 17:57:00,003 INFO  xxx.PrintLogSinkFunction                [] - (a,2,2022-09-03 17:56:00,2022-09-03 17:57:00)
2022-09-03 17:57:00,004 INFO  xxx.ReduceProcessWindowFunctionExample  [] - word: b, count: 4, window: [2022-09-03 17:56:00, 2022-09-03 17:57:00], processingTime: 2022-09-03 17:57:00
2022-09-03 17:57:00,004 INFO  xxx.PrintLogSinkFunction                [] - (b,4,2022-09-03 17:56:00,2022-09-03 17:57:00)
...
```

#### 4.2 AggregateFunction 与 ProcessWindowFunction 组合使用

如下代码示例展示了如何将 AggregateFunction 增量函数与 ProcessWindowFunction 函数组合使用来实现 AggregateFunction 示例中功能(计算每个传感器的平均温度)：
```java
// 计算分钟内的平均温度
SingleOutputStreamOperator<Tuple4<String, Double, String, String>> stream = source
        // 分组
        .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
            @Override
            public String getKey(Tuple2<String, Integer> value) throws Exception {
                return value.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
        // 窗口计算 AggregateFunction 和 ProcessWindowFunction 配合使用
        .aggregate(new AvgTemperatureAggregateFunction(), new AvgTemperatureProcessWindowFunction());

/**
 * 自定义AggregateFunction
 *      计算平均温度
 */
private static class AvgTemperatureAggregateFunction implements AggregateFunction<
       Tuple2<String, Integer>, // 输入类型
       Tuple3<String, Integer, Integer>, // <Key, Sum, Count> 中间结果类型
       Tuple2<String, Double>> { // 输出类型
   @Override
   public Tuple3<String, Integer, Integer> createAccumulator() {
       // 累加器 Key, Sum, Count
       return Tuple3.of("", 0, 0);
   }

   @Override
   public Tuple3<String, Integer, Integer> add(Tuple2<String, Integer> value, Tuple3<String, Integer, Integer> accumulator) {
       // 输入一个元素 更新累加器
       return Tuple3.of(value.f0, accumulator.f1 + value.f1, accumulator.f2 + 1);
   }

   @Override
   public Tuple2<String, Double> getResult(Tuple3<String, Integer, Integer> accumulator) {
       // 从累加器中获取总和和个数计算平均值
       double avgTemperature = ((double) accumulator.f1) / accumulator.f2;
       LOG.info("id: {}, sum: {}, count: {}, avg: {}", accumulator.f0, accumulator.f1, accumulator.f2, avgTemperature);
       return Tuple2.of(accumulator.f0, avgTemperature);
   }

   @Override
   public Tuple3<String, Integer, Integer> merge(Tuple3<String, Integer, Integer> a, Tuple3<String, Integer, Integer> b) {
       // 累加器合并
       return Tuple3.of(a.f0, a.f1 + b.f1, a.f2 + b.f2);
   }
}

/**
 * 自定义ProcessWindowFunction：
 *      获取窗口元信息
 */
private static class AvgTemperatureProcessWindowFunction extends ProcessWindowFunction<
        Tuple2<String, Double>, // 输入类型
        Tuple4<String, Double, String, String>, // 输出类型
        String, // Key 类型
        TimeWindow> {
    @Override
    public void process(String s, Context context, Iterable<Tuple2<String, Double>> elements, Collector<Tuple4<String, Double, String, String>> out) throws Exception {
        // 窗口聚合结果值
        Tuple2<String, Double> avgTemperatureTuple = elements.iterator().next();
        String id = avgTemperatureTuple.f0;
        Double avgTemperature = avgTemperatureTuple.f1;
        // 窗口元信息
        TimeWindow window = context.window();
        long start = window.getStart();
        long end = window.getEnd();
        String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
        String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
        // 当前处理时间
        long currentProcessingTimeStamp = context.currentProcessingTime();
        String currentProcessingTime = DateUtil.timeStamp2Date(currentProcessingTimeStamp, "yyyy-MM-dd HH:mm:ss");
        LOG.info("id: {}, avgTemperature: {}, window: {}, processingTime: {}",
                id, avgTemperature,
                "[" + startTime + ", " + endTime + "]", currentProcessingTime
        );
        // 输出
        out.collect(Tuple4.of(id, avgTemperature, startTime, endTime));
    }
}
```
> 完整代码请查阅:[AggregateProcessWindowFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/function/AggregateProcessWindowFunctionExample.java)

实际效果如下：
```
2022-09-03 18:17:30,570 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 20
2022-09-03 18:17:40,574 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 27
2022-09-03 18:17:50,576 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 22
2022-09-03 18:18:00,006 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: c, sum: 47, count: 2, avg: 23.5
2022-09-03 18:18:00,013 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: c, avgTemperature: 23.5, window: [2022-09-03 18:17:00, 2022-09-03 18:18:00], processingTime: 2022-09-03 18:18:00
2022-09-03 18:18:00,013 INFO  xxx.PrintLogSinkFunction      [] - (c,23.5,2022-09-03 18:17:00,2022-09-03 18:18:00)
2022-09-03 18:18:00,014 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: a, sum: 22, count: 1, avg: 22.0
2022-09-03 18:18:00,014 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: a, avgTemperature: 22.0, window: [2022-09-03 18:17:00, 2022-09-03 18:18:00], processingTime: 2022-09-03 18:18:00
2022-09-03 18:18:00,014 INFO  xxx.PrintLogSinkFunction      [] - (a,22.0,2022-09-03 18:17:00,2022-09-03 18:18:00)
2022-09-03 18:18:00,580 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 30
2022-09-03 18:18:10,585 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 22
2022-09-03 18:18:20,588 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 24
2022-09-03 18:18:30,590 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 26
2022-09-03 18:18:40,594 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 30
2022-09-03 18:18:50,596 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 26
2022-09-03 18:19:00,004 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: c, sum: 52, count: 2, avg: 26.0
2022-09-03 18:19:00,005 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: c, avgTemperature: 26.0, window: [2022-09-03 18:18:00, 2022-09-03 18:19:00], processingTime: 2022-09-03 18:19:00
2022-09-03 18:19:00,005 INFO  xxx.PrintLogSinkFunction      [] - (c,26.0,2022-09-03 18:18:00,2022-09-03 18:19:00)
2022-09-03 18:19:00,005 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: a, sum: 106, count: 4, avg: 26.5
2022-09-03 18:19:00,006 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: a, avgTemperature: 26.5, window: [2022-09-03 18:18:00, 2022-09-03 18:19:00], processingTime: 2022-09-03 18:19:00
2022-09-03 18:19:00,006 INFO  xxx.PrintLogSinkFunction      [] - (a,26.5,2022-09-03 18:18:00,2022-09-03 18:19:00)
2022-09-03 18:19:00,602 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 29
2022-09-03 18:19:10,604 INFO  xxx.SimpleTemperatureSource   [] - sensorId: b, temperature: 25
2022-09-03 18:19:20,605 INFO  xxx.SimpleTemperatureSource   [] - sensorId: b, temperature: 28
2022-09-03 18:19:30,610 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 22
2022-09-03 18:19:40,614 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 25
2022-09-03 18:19:50,618 INFO  xxx.SimpleTemperatureSource   [] - sensorId: b, temperature: 27
2022-09-03 18:20:00,003 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: c, sum: 54, count: 2, avg: 27.0
2022-09-03 18:20:00,004 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: c, avgTemperature: 27.0, window: [2022-09-03 18:19:00, 2022-09-03 18:20:00], processingTime: 2022-09-03 18:20:00
2022-09-03 18:20:00,005 INFO  xxx.PrintLogSinkFunction      [] - (c,27.0,2022-09-03 18:19:00,2022-09-03 18:20:00)
2022-09-03 18:20:00,005 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: a, sum: 22, count: 1, avg: 22.0
2022-09-03 18:20:00,005 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: a, avgTemperature: 22.0, window: [2022-09-03 18:19:00, 2022-09-03 18:20:00], processingTime: 2022-09-03 18:20:00
2022-09-03 18:20:00,005 INFO  xxx.PrintLogSinkFunction      [] - (a,22.0,2022-09-03 18:19:00,2022-09-03 18:20:00)
2022-09-03 18:20:00,006 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: b, sum: 80, count: 3, avg: 26.666666666666668
2022-09-03 18:20:00,006 INFO  xxx.AggregateProcessWindowFunctionExample [] - id: b, avgTemperature: 26.666666666666668, window: [2022-09-03 18:19:00, 2022-09-03 18:20:00], processingTime: 2022-09-03 18:20:00
2022-09-03 18:20:00,006 INFO  xxx.PrintLogSinkFunction      [] - (b,26.666666666666668,2022-09-03 18:19:00,2022-09-03 18:20:00)
...
```

### 5. WindowFunction

在某些可以使用 ProcessWindowFunction 的地方，我们也可以使用 WindowFunction。这是 ProcessWindowFunction 的旧版本，提供的上下文信息比较少，并且缺乏某些高级功能，例如，每个窗口的 Keyed 状态。WindowFunction 的结构如下所示：
```java
public interface WindowFunction<IN, OUT, KEY, W extends Window> extends Function, Serializable {
  void apply(KEY key, W window, Iterable<IN> input, Collector<OUT> out) throws Exception;
}
```
如下代码展示了使用 WindowFunction 计算每个传感器最低温度和最高温度的功能：
```java
SingleOutputStreamOperator<Tuple3<String, Integer, Integer>> stream = source
        // 分组
        .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {

            @Override
            public String getKey(Tuple2<String, Integer> value) throws Exception {
                return value.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
        // 使用 WindowFunction
        .apply(new HighLowTemperatureWindowFunction());

/**
 * 自定义实现WindowFunction
 *      计算最低温度和最高问温度
 */
private static class HighLowTemperatureWindowFunction implements WindowFunction<
        Tuple2<String, Integer>, // 输入类型
        Tuple3<String, Integer, Integer>, // 输出类型
        String, // key 类型
        TimeWindow> {
    @Override
    public void apply(String key, TimeWindow window, Iterable<Tuple2<String, Integer>> elements, Collector<Tuple3<String, Integer, Integer>> out) throws Exception {
        int lowTemperature = Integer.MAX_VALUE;
        int highTemperature = Integer.MIN_VALUE;
        List<Integer> temperatures = Lists.newArrayList();
        for (Tuple2<String, Integer> element : elements) {
            // 温度列表
            temperatures.add(element.f1);
            Integer temperature = element.f1;
            // 计算最低温度
            if (temperature < lowTemperature) {
                lowTemperature = temperature;
            }
            // 计算最高温度
            if (temperature > highTemperature) {
                highTemperature = temperature;
            }
        }
        // 时间窗口元数据
        long start = window.getStart();
        long end = window.getEnd();
        String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
        String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
        LOG.info("sensorId: {}, temperatures: {}, low: {}, high: {}, window: {}",
                key, temperatures, lowTemperature, highTemperature,
                "[" + startTime + ", " + endTime + "]"
        );
        out.collect(Tuple3.of(temperatures.toString(), lowTemperature, highTemperature));
    }
}
```
> 完整代码请查阅:[WindowFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/function/WindowFunctionExample.java)

效果如下：
```
2022-09-03 18:21:56,775 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 25
2022-09-03 18:22:00,015 INFO  xxx.WindowFunctionExample     [] - sensorId: c, temperatures: [25], low: 25, high: 25, window: [2022-09-03 18:21:00, 2022-09-03 18:22:00]
2022-09-03 18:22:00,015 INFO  xxx.PrintLogSinkFunction      [] - ([25],25,25)
2022-09-03 18:22:06,779 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 20
2022-09-03 18:22:16,780 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 30
2022-09-03 18:22:26,782 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 23
2022-09-03 18:22:36,786 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 20
2022-09-03 18:22:46,789 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 23
2022-09-03 18:22:56,790 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 24
2022-09-03 18:23:00,004 INFO  xxx.WindowFunctionExample     [] - sensorId: c, temperatures: [20, 20, 23, 24], low: 20, high: 24, window: [2022-09-03 18:22:00, 2022-09-03 18:23:00]
2022-09-03 18:23:00,004 INFO  xxx.PrintLogSinkFunction      [] - ([20, 20, 23, 24],20,24)
2022-09-03 18:23:00,005 INFO  xxx.WindowFunctionExample     [] - sensorId: a, temperatures: [30, 23], low: 23, high: 30, window: [2022-09-03 18:22:00, 2022-09-03 18:23:00]
2022-09-03 18:23:00,005 INFO  xxx.PrintLogSinkFunction      [] - ([30, 23],23,30)
2022-09-03 18:23:06,795 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 27
2022-09-03 18:23:16,796 INFO  xxx.SimpleTemperatureSource   [] - sensorId: b, temperature: 22
2022-09-03 18:23:26,799 INFO  xxx.SimpleTemperatureSource   [] - sensorId: a, temperature: 20
2022-09-03 18:23:36,803 INFO  xxx.SimpleTemperatureSource   [] - sensorId: c, temperature: 27
2022-09-03 18:23:46,806 INFO  xxx.SimpleTemperatureSource   [] - sensorId: b, temperature: 25
2022-09-03 18:23:56,808 INFO  xxx.SimpleTemperatureSource   [] - sensorId: b, temperature: 28
2022-09-03 18:24:00,004 INFO  xxx.WindowFunctionExample     [] - sensorId: a, temperatures: [27, 20], low: 20, high: 27, window: [2022-09-03 18:23:00, 2022-09-03 18:24:00]
2022-09-03 18:24:00,005 INFO  xxx.PrintLogSinkFunction      [] - ([27, 20],20,27)
2022-09-03 18:24:00,005 INFO  xxx.WindowFunctionExample     [] - sensorId: c, temperatures: [27], low: 27, high: 27, window: [2022-09-03 18:23:00, 2022-09-03 18:24:00]
2022-09-03 18:24:00,005 INFO  xxx.PrintLogSinkFunction      [] - ([27],27,27)
2022-09-03 18:24:00,006 INFO  xxx.WindowFunctionExample     [] - sensorId: b, temperatures: [22, 25, 28], low: 22, high: 28, window: [2022-09-03 18:23:00, 2022-09-03 18:24:00]
2022-09-03 18:24:00,006 INFO  xxx.PrintLogSinkFunction      [] - ([22, 25, 28],22,28)
...
```

参考:
- [Window Functions](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/stream/operators/windows.html#window-functions)
- Flink核心技术与实战
