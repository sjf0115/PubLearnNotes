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

在之前的文章中我们已经了解了 Flink 的[窗口机制](https://smartsi.blog.csdn.net/article/details/126554021)，并介绍了其中涉及的组件：WindowAssigner、WindowFunction、Trigger、Evictor。在 [Flink 窗口分配器 WindowAssigner](https://smartsi.blog.csdn.net/article/details/126652876) 中我们知道可以通过不同类型的窗口分配器 WindowAssigner 将元素分配到窗口中。在指定 WindowAssigner 后，需要在每个窗口上指定我们要执行的计算逻辑，这就是窗口函数（WindowFunction）的责任。一旦系统确定窗口准备好处理数据，窗口函数就会被调用来处理窗口中的每个元素。

按照窗口计算原理划分，可用于处理窗口数据的函数有两种：
- 增量聚合函数：增量聚合函数在窗口内以状态形式存储某个值，每个新加入的窗口的元素对该值进行更新，即窗口中只维护中间结果的状态值，不需要缓存原始数据。这种函数计算性能高，占有存储空间少，因为 Flink 可以在每个元素到达窗口时增量地进行聚合。代表函数有 ReduceFunction，AggregateFunction。
- 全量窗口函数：全量窗口函数对属于该窗口的元素全部进行缓存，只有等到窗口触发的时候，才对所有的原始元素进行汇总计算。这种函数不会像增量聚合函数那样有效率，使用的代价相对较高，性能相对差一些，如果接入的数据量比较大或者窗口时间比较长，就可能会导致计算性能的下降。此外也通常需要占用更多的空间。不过可以获取一个窗口内所有元素的迭代器以及元素所在窗口的其他元信息，可以支持更复杂的操作。代表函数有 ProcessWindowFunction。

下面将会介绍每种 Windows Function 在 Flink 中如何使用。

### 1. ReduceFunction

ReduceFunction 定义了对输入的两个相同类型的元素按照指定的计算逻辑进行聚合，然后输出相同类型的一个结果元素。窗口只需要一个在状态中存储的当前聚合结果，以及一个和 ReduceFunction 的输入输出类型相同的值。每当收到一个新元素时，算子都会以该元素和从窗口状态取出的当前聚合值为参数调用 ReduceFunction，随后会用 ReduceFunction 的结果更新窗口状态中的值。

在窗口上使用 ReduceFunction 的优点是只需为每个窗口维护一个常数级别的小状态，此外函数的接口也很简单。然而， ReduceFunction 的应用场景也有一定的局限，由于输入和输出类型必须一致，所以通常仅限于一些简单的聚合。

如下代码所示，使用 ReduceFunction 计算每个单词出现的次数，只需要在 `reduce()` 函数中指定 ReduceFunction 即可：
```java
DataStream<Tuple2<String, Integer>> wordsCount = ...;
DataStream<Tuple2<String, Integer>> stream = wordsCount
                // 根据单词分组
                .keyBy(new KeySelector<Tuple2<String,Integer>, String>() {
                    @Override
                    public String getKey(Tuple2<String, Integer> value) throws Exception {
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
                        LOG.info("word: {}, count: {}", value1.f0, count);
                        return Tuple2.of(value1.f0, count);
                    }
                });
```

> 完整代码请查阅:[WindowReduceFunctionExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/function/WindowReduceFunctionExample.java)

实际效果如下：
```java
22:13:35,478 INFO  SimpleWordSource      [] - word: a
22:13:45,484 INFO  SimpleWordSource      [] - word: a
22:13:45,584 INFO  WindowReduceFunctionExample [] - word: a, count: 2
22:13:55,486 INFO  SimpleWordSource      [] - word: a
22:13:55,517 INFO  WindowReduceFunctionExample [] - word: a, count: 3
(a,3)
22:14:05,488 INFO  SimpleWordSource      [] - word: a
22:14:15,491 INFO  SimpleWordSource      [] - word: b
22:14:25,496 INFO  SimpleWordSource      [] - word: a
22:14:25,548 INFO  WindowReduceFunctionExample [] - word: a, count: 2
22:14:35,497 INFO  SimpleWordSource      [] - word: b
22:14:35,571 INFO  WindowReduceFunctionExample [] - word: b, count: 2
22:14:45,502 INFO  SimpleWordSource      [] - word: a
22:14:45,594 INFO  WindowReduceFunctionExample [] - word: a, count: 3
22:14:55,508 INFO  SimpleWordSource      [] - word: b
22:14:55,515 INFO  WindowReduceFunctionExample [] - word: b, count: 3
(a,3)
(b,3)
22:15:05,509 INFO  SimpleWordSource      [] - word: a
22:15:15,514 INFO  SimpleWordSource      [] - word: a
22:15:15,597 INFO  WindowReduceFunctionExample [] - word: a, count: 2
22:15:25,515 INFO  SimpleWordSource      [] - word: a
22:15:25,538 INFO  WindowReduceFunctionExample [] - word: a, count: 3
22:15:35,520 INFO  SimpleWordSource      [] - word: b
22:15:45,523 INFO  SimpleWordSource      [] - word: a
22:15:45,606 INFO  WindowReduceFunctionExample [] - word: a, count: 4
22:15:55,528 INFO  SimpleWordSource      [] - word: b
22:15:55,565 INFO  WindowReduceFunctionExample [] - word: b, count: 2
(a,4)
(b,2)
...
```

### 2. AggregateFunction

和 ReduceFunction 类似，AggregateFunction 也是以增量方式处理窗口内的元素，也需要在状态中存储当前的聚合结果。不同的是，AggregateFunction 是 ReduceFunction 的一个通用版本，相对于 ReduceFunction 更加灵活，但实现复杂度也相对更高。AggregateFunction 的中间数据和输出数据类型不再依赖输入类型。

AggregateFunction 接口中有三个参数：输入元素类型（IN）、累加器类型（ACC）以及输出元素类型（OUT），此外还定义了四个需要重写的方法，其中 `createAccumulator()` 方法创建 accumulator，`add()` 方法定义数据的添加逻辑，`getResult()` 定义了根据 accumulator 计算结果的逻辑，`merge()` 方法定义了合并 accumulator 的逻辑：
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
// 计算分钟内的平均温度
DataStream<Tuple2<String, Double>> stream = source
        // 分组
        .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
            @Override
            public String getKey(Tuple2<String, Integer> value) throws Exception {
                return value.f0;
            }
        })
        // 窗口大小为1分钟的滚动窗口
        .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
        // 窗口增量聚合函数 AggregateFunction
        .aggregate(new AggregateFunction<Tuple2<String, Integer>, Tuple3<String, Integer, Integer>, Tuple2<String, Double>>() {
            @Override
            public Tuple3<String, Integer, Integer> createAccumulator() {
                // 累加器 Key, Sum, Count  中间状态
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
        });
```

> 完整代码请查阅:[AggregateFunctionExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/function/WindowAggregateFunctionExample.java)

实际效果如下：
```java
22:31:39,539 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 22
22:31:49,544 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 26
22:31:59,548 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 26
22:32:00,007 INFO  WindowAggregateFunctionExample [] - id: b, sum: 22℃, count: 1, avg: 22.0℃
(b,22.0)
22:32:00,008 INFO  WindowAggregateFunctionExample [] - id: c, sum: 26℃, count: 1, avg: 26.0℃
(c,26.0)
22:32:00,009 INFO  WindowAggregateFunctionExample [] - id: a, sum: 26℃, count: 1, avg: 26.0℃
(a,26.0)
22:32:09,550 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 23
22:32:19,555 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 22
22:32:29,561 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 27
22:32:39,563 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 27
22:32:49,564 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 22
22:32:59,566 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 22
22:33:00,000 INFO  WindowAggregateFunctionExample [] - id: c, sum: 94℃, count: 4, avg: 23.5℃
(c,23.5)
22:33:00,001 INFO  WindowAggregateFunctionExample [] - id: a, sum: 27℃, count: 1, avg: 27.0℃
(a,27.0)
22:33:00,001 INFO  WindowAggregateFunctionExample [] - id: b, sum: 22℃, count: 1, avg: 22.0℃
(b,22.0)
22:33:09,570 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 24
22:33:19,575 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 20
22:33:29,578 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 29
22:33:39,579 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 24
22:33:49,582 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 26
22:33:59,587 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 24
22:34:00,003 INFO  WindowAggregateFunctionExample [] - id: b, sum: 68℃, count: 3, avg: 22.666666666666668℃
(b,22.666666666666668)
22:34:00,004 INFO  WindowAggregateFunctionExample [] - id: c, sum: 24℃, count: 1, avg: 24.0℃
(c,24.0)
22:34:00,004 INFO  WindowAggregateFunctionExample [] - id: a, sum: 55℃, count: 2, avg: 27.5℃
(a,27.5)
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

如下代码所示，使用 ProcessWindowFunction 完成计算最近一分钟每个传感器的最低和最高温度功能，并输出窗口结束时间等元数据信息：
```java
// 最低温度和最高温度
DataStream<Tuple3<String, Integer, Integer>> stream = source
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
        .process(new ProcessWindowFunction<Tuple2<String, Integer>, Tuple3<String, Integer, Integer>, String, TimeWindow>() {
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
        });
```
> 完整代码请查阅:[ProcessWindowFunctionExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/function/ProcessWindowFunctionExample.java)

实际效果如下所示：
```java
22:48:40,714 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 24
22:48:50,717 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 28
22:49:00,007 INFO  ProcessWindowFunctionExample [] - sensorId: c, List: [24], Low: 24, High: 24, Window: [2025-08-26 22:48:00, 2025-08-26 22:49:00], ProcessingTime: 2025-08-26 22:49:00
([24],24,24)
22:49:00,008 INFO  ProcessWindowFunctionExample [] - sensorId: b, List: [28], Low: 28, High: 28, Window: [2025-08-26 22:48:00, 2025-08-26 22:49:00], ProcessingTime: 2025-08-26 22:49:00
([28],28,28)
22:49:00,722 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 23
22:49:10,728 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 26
22:49:20,729 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 26
22:49:30,734 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 29
22:49:40,738 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 23
22:49:50,743 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 27
22:50:00,005 INFO  ProcessWindowFunctionExample [] - sensorId: a, List: [23, 26, 29, 23], Low: 23, High: 29, Window: [2025-08-26 22:49:00, 2025-08-26 22:50:00], ProcessingTime: 2025-08-26 22:50:00
([23, 26, 29, 23],23,29)
22:50:00,006 INFO  ProcessWindowFunctionExample [] - sensorId: c, List: [26, 27], Low: 26, High: 27, Window: [2025-08-26 22:49:00, 2025-08-26 22:50:00], ProcessingTime: 2025-08-26 22:50:00
([26, 27],26,27)
22:50:00,744 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 23
22:50:10,748 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 27
22:50:20,754 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 24
22:50:30,754 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 27
22:50:40,759 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 30
22:50:50,764 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 26
22:51:00,004 INFO  ProcessWindowFunctionExample [] - sensorId: c, List: [23, 27, 27], Low: 23, High: 27, Window: [2025-08-26 22:50:00, 2025-08-26 22:51:00], ProcessingTime: 2025-08-26 22:51:00
([23, 27, 27],23,27)
22:51:00,005 INFO  ProcessWindowFunctionExample [] - sensorId: a, List: [30], Low: 30, High: 30, Window: [2025-08-26 22:50:00, 2025-08-26 22:51:00], ProcessingTime: 2025-08-26 22:51:00
([30],30,30)
22:51:00,005 INFO  ProcessWindowFunctionExample [] - sensorId: b, List: [24, 26], Low: 24, High: 26, Window: [2025-08-26 22:50:00, 2025-08-26 22:51:00], ProcessingTime: 2025-08-26 22:51:00
([24, 26],24,26)
...
```

### 4. 使用增量聚合的 ProcessWindowFunction

ReduceFunction，AggregateFunction 等这些增量函数虽然在一定程度上能够提升窗口的计算性能，但是这些函数的灵活性却不及 ProcessWindowFunction，例如对窗口状态的操作以及对窗口中元数据获取等。但是如果使用 ProcessWindowFunction 来完成一些基础的增量计算却比较浪费资源。这时可以使用 ProcessWindowFunction 与 ReduceFunction 或者 AggregateFunction 等增量函数组合使用，以充分利用两种函数各自的优势。元素到达窗口时对其使用 ReduceFunction 或者 AggregateFunction 增量函数进行增量聚合；当窗口触发器触发时再向 ProcessWindowFunction 提供聚合结果，这样传递给 `ProcessWindowFunction.process()` 方法的 Iterable 参数内将只有一个增量聚合值。这样我们就可以实现增量计算窗口，同时还可以访问窗口的元数据信息。

> 我们也可以使用旧版的 WindowFunction 代替 ProcessWindowFunction 进行增量窗口聚合。

在 DataStream API 中实现 ProcessWindowFunction 与 ReduceFunction 或者 AggregateFunction 等增量函数组合使用，需要将 ProcessWindowFunction 分别作为 `Reduce()` 和 `aggregate()` 函数的第二个参数即可。

#### 4.1 ReduceFunction 与 ProcessWindowFunction 组合使用

如下代码示例展示了如何将 ReduceFunction 增量函数与 ProcessWindowFunction 函数组合使用来实现 ReduceFunction 示例中功能(计算每个单词出现的次数)：
```java
// 滚动窗口
DataStream<Tuple4<String, Integer, String, String>> stream = wordsCount
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
        return Tuple2.of(wordCount1.f0, count);
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
> 完整代码请查阅:[ReduceProcessWindowFunctionExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/function/ReduceProcessWindowFunctionExample.java)

实际效果如下：
```java
23:03:45,728 INFO  SimpleWordSource      [] - word: b
23:03:55,733 INFO  SimpleWordSource      [] - word: b
23:03:55,834 INFO  ReduceProcessWindowFunctionExample [] - word: b, count: 2
23:04:00,009 INFO  ReduceProcessWindowFunctionExample [] - word: b, count: 2, window: [2025-08-26 23:03:00, 2025-08-26 23:04:00], processingTime: 2025-08-26 23:04:00
(b,2,2025-08-26 23:03:00,2025-08-26 23:04:00)
23:04:05,738 INFO  SimpleWordSource      [] - word: a
23:04:15,742 INFO  SimpleWordSource      [] - word: a
23:04:15,756 INFO  ReduceProcessWindowFunctionExample [] - word: a, count: 2
23:04:25,743 INFO  SimpleWordSource      [] - word: a
23:04:25,762 INFO  ReduceProcessWindowFunctionExample [] - word: a, count: 3
23:04:35,745 INFO  SimpleWordSource      [] - word: a
23:04:35,795 INFO  ReduceProcessWindowFunctionExample [] - word: a, count: 4
23:04:45,749 INFO  SimpleWordSource      [] - word: b
23:04:55,755 INFO  SimpleWordSource      [] - word: b
23:04:55,781 INFO  ReduceProcessWindowFunctionExample [] - word: b, count: 2
23:05:00,005 INFO  ReduceProcessWindowFunctionExample [] - word: a, count: 4, window: [2025-08-26 23:04:00, 2025-08-26 23:05:00], processingTime: 2025-08-26 23:05:00
(a,4,2025-08-26 23:04:00,2025-08-26 23:05:00)
23:05:00,006 INFO  ReduceProcessWindowFunctionExample [] - word: b, count: 2, window: [2025-08-26 23:04:00, 2025-08-26 23:05:00], processingTime: 2025-08-26 23:05:00
(b,2,2025-08-26 23:04:00,2025-08-26 23:05:00)
23:05:05,757 INFO  SimpleWordSource      [] - word: b
23:05:15,761 INFO  SimpleWordSource      [] - word: a
23:05:25,767 INFO  SimpleWordSource      [] - word: b
23:05:25,841 INFO  ReduceProcessWindowFunctionExample [] - word: b, count: 2
23:05:35,772 INFO  SimpleWordSource      [] - word: b
23:05:35,870 INFO  ReduceProcessWindowFunctionExample [] - word: b, count: 3
23:05:45,777 INFO  SimpleWordSource      [] - word: a
23:05:45,878 INFO  ReduceProcessWindowFunctionExample [] - word: a, count: 2
23:05:55,781 INFO  SimpleWordSource      [] - word: b
23:05:55,819 INFO  ReduceProcessWindowFunctionExample [] - word: b, count: 4
23:06:00,005 INFO  ReduceProcessWindowFunctionExample [] - word: b, count: 4, window: [2025-08-26 23:05:00, 2025-08-26 23:06:00], processingTime: 2025-08-26 23:06:00
(b,4,2025-08-26 23:05:00,2025-08-26 23:06:00)
23:06:00,006 INFO  ReduceProcessWindowFunctionExample [] - word: a, count: 2, window: [2025-08-26 23:05:00, 2025-08-26 23:06:00], processingTime: 2025-08-26 23:06:00
(a,2,2025-08-26 23:05:00,2025-08-26 23:06:00)
...
```

#### 4.2 AggregateFunction 与 ProcessWindowFunction 组合使用

如下代码示例展示了如何将 AggregateFunction 增量函数与 ProcessWindowFunction 函数组合使用来实现 AggregateFunction 示例中功能(计算每个传感器的平均温度)：
```java
// 计算分钟内的平均温度
DataStream<Tuple4<String, Double, String, String>> stream = source
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
> 完整代码请查阅:[AggregateProcessWindowFunctionExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/function/AggregateProcessWindowFunctionExample.java)

实际效果如下：
```java
23:11:11,465 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 22
23:11:21,470 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 24
23:11:31,475 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 27
23:11:41,479 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 23
23:11:51,484 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 26
23:12:00,006 INFO  AggregateProcessWindowFunctionExample [] - id: a, sum: 49, count: 2, avg: 24.5
23:12:00,009 INFO  AggregateProcessWindowFunctionExample [] - id: a, avgTemperature: 24.5, window: [2025-08-26 23:11:00, 2025-08-26 23:12:00], processingTime: 2025-08-26 23:12:00
(a,24.5,2025-08-26 23:11:00,2025-08-26 23:12:00)
23:12:00,009 INFO  AggregateProcessWindowFunctionExample [] - id: c, sum: 26, count: 1, avg: 26.0
23:12:00,010 INFO  AggregateProcessWindowFunctionExample [] - id: c, avgTemperature: 26.0, window: [2025-08-26 23:11:00, 2025-08-26 23:12:00], processingTime: 2025-08-26 23:12:00
(c,26.0,2025-08-26 23:11:00,2025-08-26 23:12:00)
23:12:00,010 INFO  AggregateProcessWindowFunctionExample [] - id: b, sum: 47, count: 2, avg: 23.5
23:12:00,011 INFO  AggregateProcessWindowFunctionExample [] - id: b, avgTemperature: 23.5, window: [2025-08-26 23:11:00, 2025-08-26 23:12:00], processingTime: 2025-08-26 23:12:00
(b,23.5,2025-08-26 23:11:00,2025-08-26 23:12:00)
23:12:01,489 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 26
23:12:11,494 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 30
23:12:21,499 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 30
23:12:31,504 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 22
23:12:41,509 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 24
23:12:51,514 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 29
23:13:00,002 INFO  AggregateProcessWindowFunctionExample [] - id: b, sum: 80, count: 3, avg: 26.666666666666668
23:13:00,003 INFO  AggregateProcessWindowFunctionExample [] - id: b, avgTemperature: 26.666666666666668, window: [2025-08-26 23:12:00, 2025-08-26 23:13:00], processingTime: 2025-08-26 23:13:00
(b,26.666666666666668,2025-08-26 23:12:00,2025-08-26 23:13:00)
23:13:00,004 INFO  AggregateProcessWindowFunctionExample [] - id: a, sum: 81, count: 3, avg: 27.0
23:13:00,004 INFO  AggregateProcessWindowFunctionExample [] - id: a, avgTemperature: 27.0, window: [2025-08-26 23:12:00, 2025-08-26 23:13:00], processingTime: 2025-08-26 23:13:00
(a,27.0,2025-08-26 23:12:00,2025-08-26 23:13:00)
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
// 最低温度和最高温度
DataStream<Tuple3<String, Integer, Integer>> stream = source
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
        .apply(new WindowFunction<Tuple2<String, Integer>, Tuple3<String, Integer, Integer>, String, TimeWindow>() {
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
        });
```
> 完整代码请查阅:[WindowFunctionExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/stream/window/function/WindowFunctionExample.java)

效果如下：
```java
23:21:03,685 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 27
23:21:13,691 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 25
23:21:23,695 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 27
23:21:33,701 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 30
23:21:43,704 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 26
23:21:53,707 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 22
23:22:00,007 INFO  WindowFunctionExample [] - sensorId: b, temperatures: [27, 30], low: 27, high: 30, window: [2025-08-26 23:21:00, 2025-08-26 23:22:00]
([27, 30],27,30)
23:22:00,008 INFO  WindowFunctionExample [] - sensorId: a, temperatures: [27, 26], low: 26, high: 27, window: [2025-08-26 23:21:00, 2025-08-26 23:22:00]
([27, 26],26,27)
23:22:00,009 INFO  WindowFunctionExample [] - sensorId: c, temperatures: [25, 22], low: 22, high: 25, window: [2025-08-26 23:21:00, 2025-08-26 23:22:00]
([25, 22],22,25)
23:22:03,708 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 27
23:22:13,708 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 25
23:22:23,714 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 21
23:22:33,718 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 28
23:22:43,721 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 29
23:22:53,726 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 23
23:23:00,000 INFO  WindowFunctionExample [] - sensorId: c, temperatures: [27], low: 27, high: 27, window: [2025-08-26 23:22:00, 2025-08-26 23:23:00]
([27],27,27)
23:23:00,001 INFO  WindowFunctionExample [] - sensorId: b, temperatures: [28, 23], low: 23, high: 28, window: [2025-08-26 23:22:00, 2025-08-26 23:23:00]
([28, 23],23,28)
23:23:00,002 INFO  WindowFunctionExample [] - sensorId: a, temperatures: [25, 21, 29], low: 21, high: 29, window: [2025-08-26 23:22:00, 2025-08-26 23:23:00]
([25, 21, 29],21,29)
23:23:03,727 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 30
23:23:13,731 INFO  SimpleTemperatureSource [] - sensorId: a, temperature: 21
23:23:23,736 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 27
23:23:33,738 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 26
23:23:43,742 INFO  SimpleTemperatureSource [] - sensorId: c, temperature: 30
23:23:53,747 INFO  SimpleTemperatureSource [] - sensorId: b, temperature: 23
23:24:00,004 INFO  WindowFunctionExample [] - sensorId: a, temperatures: [30, 21], low: 21, high: 30, window: [2025-08-26 23:23:00, 2025-08-26 23:24:00]
([30, 21],21,30)
23:24:00,005 INFO  WindowFunctionExample [] - sensorId: c, temperatures: [30], low: 30, high: 30, window: [2025-08-26 23:23:00, 2025-08-26 23:24:00]
([30],30,30)
23:24:00,005 INFO  WindowFunctionExample [] - sensorId: b, temperatures: [27, 26, 23], low: 23, high: 27, window: [2025-08-26 23:23:00, 2025-08-26 23:24:00]
([27, 26, 23],23,27)
...
```

参考:
- [Window Functions](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/stream/operators/windows.html#window-functions)
- Flink核心技术与实战
