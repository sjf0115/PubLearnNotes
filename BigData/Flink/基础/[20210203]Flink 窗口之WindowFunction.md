---
layout: post
author: smartsi
title: Flink 窗口之WindowFunction
date: 2021-02-06 22:38:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-windows-function
---

在之前的文章中我们已经了解 Flink 可以不同类型的窗口的 Assigner，在指定 [Windows Assigner](http://smartsi.club/flink-stream-windows-overall.html) 之后，我们需要在每个窗口上指定我们要执行的计算逻辑。这是窗口函数（Windows Function）的责任，一旦系统确定窗口准备好处理数据，窗口函数就会被调用来处理窗口中的每个元素。

窗口函数可以是 ReduceFunction，AggregateFunction, FoldFunction 或者 ProcessWindowFunction。前两个函数执行效率更高，因为 Flink 可以在每个元素到达窗口时增量地进行聚合。ProcessWindowFunction 可以获取一个窗口内所有元素的迭代器以及元素所在窗口的其他元信息。使用 ProcessWindowFunction 进行窗口操作不能像其他那样有效率，是因为 Flink 在调用该函数之前必须在内部缓存窗口中的所有元素。所以按照计算原理可以分为两大类：一类是增量聚合函数，对应有 ReduceFunction，AggregateFunction, FoldFunction；另一类是全量窗口函数，对应有 ProcessWindowFunction。增量聚合函数计算性能高，占有存储空间少，主要是因为基于中间状态的计算结果，窗口中只维护中间结果的状态值，不需要缓存原始数据。而全量窗口函数使用的代价相对较高，性能比较弱，主要因为算子需要对属于该窗口的元素进行缓存，只有等到床就触发的时候，才对所有的原始元素进行汇总计算。如果接入的数据量比较大或者窗口时间比较长，就可能会导致计算性能的下降。

下面将会介绍每种 Windows Function 在 Flink 中如何使用。

### 1. ReduceFunction

ReduceFunction 定义了对输入的两个相同类型的元素按照指定的计算逻辑进行集合，然后输出相同类型的一个结果元素。Flink 使用 ReduceFunction 增量聚合窗口的元素。如下代码所示，创建好 Window Assigner 之后通过在 reduce() 函数汇总指定 ReduceFunction 逻辑：
```java
DataStream<Tuple2<String, Integer>> wordsCount = ...;
DataStream<Tuple2<String, Integer>> result = wordsCount
        // 根据输入单词分组
        .keyBy(0)
        // 窗口大小为1秒的滚动窗口
        .timeWindow(Time.seconds(1))
        // ReduceFunction
        .reduce(new ReduceFunction<Tuple2<String, Integer>> (){
            @Override
            public Tuple2<String, Integer> reduce(Tuple2<String, Integer> value1, Tuple2<String, Integer> value2) throws Exception {
                return new Tuple2(value1.f0, value1.f1 + value2.f1);
            }
        });
```
上述示例获得窗口中的所有元素元组的第二个字段之和。

> 完成代码请查阅:[ReduceFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/ReduceFunctionExample.java)

### 2. AggregateFunction

AggregateFunction 是 ReduceFunction 的一个通用版本，相对于 ReduceFunction 更加灵活，实现复杂度也相对更高。AggregateFunction 接口中有三个参数：输入元素类型（IN）、累加器类型（ACC）以及输出元素类型（OUT），此外还定义了四个需要重写的方法，其中 createAccumulator() 方法创建 accumulator，add() 方法定义数据的添加逻辑，getResult 定义了根据 accumulator 计算结果的逻辑，merge() 方法定义了合并 accumulator 的逻辑：
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
如下代码所示，实现 AggregateFunction 求取最近一分钟平均值的聚合运算：
```java
DataStream<Tuple2<String, Double>> result = stream
        // 提取时间戳与设置Watermark
        .assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor<Tuple3<String, Long, Integer>>(Time.minutes(10)) {
            @Override
            public long extractTimestamp(Tuple3<String, Long, Integer> element) {
                return element.f1;
            }
        })
        // 格式转换
        .map(new MapFunction<Tuple3<String,Long,Integer>, Tuple2<String, Integer>>() {
            @Override
            public Tuple2<String, Integer> map(Tuple3<String, Long, Integer> value) throws Exception {
                return new Tuple2<String, Integer>(value.f0, value.f2);
            }
        })
        // 分组
        .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
            @Override
            public String getKey(Tuple2<String, Integer> value) throws Exception {
                return value.f0;
            }
        })
        // 窗口大小为10分钟、滑动步长为5分钟的滑动窗口
        .timeWindow(Time.minutes(10), Time.minutes(5))
        .aggregate(new AverageAggregateFunction());

/**
 * 自定义AggregateFunction
 */
private static class AverageAggregateFunction implements AggregateFunction<Tuple2<String, Integer>, Tuple3<String, Long, Long>, Tuple2<String, Double>> {

    // IN：Tuple2<String, Long>
    // ACC：Tuple3<String, Long, Long> -> <Key, Sum, Count>
    // OUT：Tuple2<String, Double>

    @Override
    public Tuple3<String, Long, Long> createAccumulator() {
        return new Tuple3<String, Long, Long>("", 0L, 0L);
    }

    @Override
    public Tuple3<String, Long, Long> add(Tuple2<String, Integer> value, Tuple3<String, Long, Long> accumulator) {
        return new Tuple3<String, Long, Long>(value.f0, accumulator.f1 + value.f1, accumulator.f2 + 1L);
    }

    @Override
    public Tuple2<String, Double> getResult(Tuple3<String, Long, Long> accumulator) {
        return new Tuple2<String, Double>(accumulator.f0, ((double) accumulator.f1) / accumulator.f2);
    }

    @Override
    public Tuple3<String, Long, Long> merge(Tuple3<String, Long, Long> a, Tuple3<String, Long, Long> b) {
        return new Tuple3<String, Long, Long>(a.f0, a.f1 + b.f1, a.f2 + b.f2);
    }
}
```

> 完成代码请查阅:[AggregateFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/AggregateFunctionExample.java)

通过如下输入数据，我们可以观察输出的具体窗口信息以及Watermark：
```
A,2021-02-14 12:07:01,9
B,2021-02-14 12:08:01,5
A,2021-02-14 12:14:01,3
C,2021-02-14 12:09:01,2
C,2021-02-14 12:15:01,5
A,2021-02-14 12:08:01,4
B,2021-02-14 12:13:01,6
B,2021-02-14 12:21:01,1
D,2021-02-14 12:04:01,3
B,2021-02-14 12:26:01,2
B,2021-02-14 12:17:01,7
D,2021-02-14 12:09:01,8
C,2021-02-14 12:30:01,1
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-function-1.jpg?raw=true)

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-function-2.jpg?raw=true)

### 4. ProcessWindowFunction

前面提到的 ReduceFunction 和 AggregateFunction 都是基于中间状态实现增量计算的窗口函数，虽然已经满足绝大数的场景，但是在某些情况下，统计更复杂的指标可能还是需要依赖于窗口中的所有的数据元素，或者需要操作窗口中的状态和窗口元数据，这时就需要使用到 ProcessWindowFunction。ProcessWindowFunction 会获得窗口内所有元素的 Iterable 以及一个可以访问时间和状态信息的 Context 对象，这使得它可以比其他窗口函数提供更大的灵活性。这是以牺牲性能和资源消耗为代价的，因为不能增量进行聚合，而是需要在内部进行缓冲，直到窗口被认为准备好进行处理为止。

ProcessWindowFunction 的结构如下所示，在类中 Context 抽象类中完整的定义了 Window 的元数据以及可以操作的 Window 状态数据，包括 GlobalState 和 WindowState：
```java
public abstract class ProcessWindowFunction<IN, OUT, KEY, W extends Window> extends AbstractRichFunction {
  private static final long serialVersionUID = 1L;
  // 评估窗口并定义窗口的输出元素
  public abstract void process(KEY key, Context context, Iterable<IN> elements, Collector<OUT> out) throws Exception;
  // 当窗口生命周期结束时清除中间状态
  public void clear(Context context) throws Exception {}
  // 包含窗口元数据的Content
  public abstract class Context implements java.io.Serializable {
    // 返回评估所属窗口
  	public abstract W window();
    // 返回窗口当前处理时间
  	public abstract long currentProcessingTime();
    // 返回窗口当前基于事件时间的Watermark
  	public abstract long currentWatermark();
    // 返回窗口的中间状态
  	public abstract KeyedStateStore windowState();
    // 返回每个Key对应的中间状态
  	public abstract KeyedStateStore globalState();
    // 根据OutputTag输出数据
  	public abstract <X> void output(OutputTag<X> outputTag, X value);
  }
}
```
在实现 ProcessWindowFunction 接口中，如果不操作状态数据，那么只需要实现 process() 方法即可，该方法中定义了评估窗口和具体数据输出的逻辑。如下代码所示，通过自定义实现 ProcessWindowFunction 完成基于窗口上的 Key 统计，并输出窗口结束时间等元数据信息：
```java
DataStream result = stream
      // 提取时间戳与设置Watermark
      .assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor<Tuple3<String, Long, Integer>>(Time.minutes(10)) {
          @Override
          public long extractTimestamp(Tuple3<String, Long, Integer> element) {
              return element.f1;
          }
      })
      // 分组
      .keyBy(new KeySelector<Tuple3<String, Long, Integer>, String>() {

          @Override
          public String getKey(Tuple3<String, Long, Integer> value) throws Exception {
              return value.f0;
          }
      })
      // 窗口大小为10分钟、滑动步长为5分钟的滑动窗口
      .timeWindow(Time.minutes(10), Time.minutes(5))
      // 窗口函数
      .process(new MyProcessWindowFunction());

/**
 * 自定义实现 ProcessWindowFunction
 */
private static class MyProcessWindowFunction extends ProcessWindowFunction<Tuple3<String, Long, Integer>, String, String, TimeWindow> {
    @Override
    public void process(String key, Context context, Iterable<Tuple3<String, Long, Integer>> elements, Collector<String> out) throws Exception {
        long count = 0;
        List<String> list = Lists.newArrayList();
        for (Tuple3<String, Long, Integer> element : elements) {
            list.add(element.f0 + "|" + element.f1 + "|" + DateUtil.timeStamp2Date(element.f1, "yyyy-MM-dd HH:mm:ss"));
            Integer value = element.f2;
            count += value;
        }
        TimeWindow window = context.window();
        long start = window.getStart();
        long end = window.getEnd();
        String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
        String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
        long currentWatermark = context.currentWatermark();
        String currentWatermarkTime = DateUtil.timeStamp2Date(currentWatermark, "yyyy-MM-dd HH:mm:ss");
        long currentProcessingTimeStamp = context.currentProcessingTime();
        String currentProcessingTime = DateUtil.timeStamp2Date(currentProcessingTimeStamp, "yyyy-MM-dd HH:mm:ss");

        StringBuilder sb = new StringBuilder();
        sb.append("Key: " + list.toString());
        sb.append(", Window[" + startTime + ", " + endTime + "]");
        sb.append(", Count: " + count);
        sb.append(", CurrentWatermarkTime: " + currentWatermarkTime);
        sb.append(", CurrentProcessingTime: " + currentProcessingTime);
        LOG.info(sb.toString());
        out.collect(sb.toString());
    }
}
```
> 完成代码请查阅:[ProcessWindowFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/ProcessWindowFunctionExample.java)

通过如下输入数据，我们可以观察输出的具体窗口信息以及Watermark：
```
A,2021-02-14 12:07:01
B,2021-02-14 12:08:01
A,2021-02-14 12:14:01
C,2021-02-14 12:09:01
C,2021-02-14 12:15:01
A,2021-02-14 12:08:01
B,2021-02-14 12:13:01
B,2021-02-14 12:21:01
D,2021-02-14 12:04:01
B,2021-02-14 12:26:01
B,2021-02-14 12:17:01
D,2021-02-14 12:09:01
C,2021-02-14 12:30:01
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-function-3.jpg?raw=true)

需要注意的是使用 ProcessWindowFunction 进行简单聚合（如count）的效率非常低。下一节将展示如何使用 ReduceFunction 或 AggregateFunction 与 ProcessWindowFunction 组合一起使用实现增量聚合以及获取 ProcessWindowFunction 的额外元数据信息。

### 5. 使用增量聚合的ProcessWindowFunction

ReduceFunction，AggregateFunction等这些增量函数虽然在一定程度上能够提升窗口的计算性能，但是这些函数的灵活性却不及 ProcessWindowFunction，例如，对窗口状态的操作以及对窗口中元数据获取等。但是如果使用 ProcessWindowFunction 来完成一些基础的增量计算却比较浪费资源。这时可以使用 ProcessWindowFunction 与 ReduceFunction 或者 AggregateFunction 等增量函数组合使用，以充分利用两种函数各自的优势。元素到达窗口时对其使用 ReduceFunction 或者 AggregateFunction 增量函数进行增量聚合，当关闭窗口时向 ProcessWindowFunction 提供聚合结果。这样我们可以增量的计算窗口，同时还可以访问窗口的元数据信息。

> 我们也可以使用旧版的 WindowFunction 代替 ProcessWindowFunction 进行增量窗口聚合。

#### 5.1 使用ReduceFunction进行增量聚合

如下代码示例展示了如何将 ReduceFunction 增量函数与 ProcessWindowFunction 组合使用以返回窗口中的不同Key的求和以及该窗口的开始时间等窗口元信息：
```java
DataStream<Tuple2<ContextInfo, Tuple2<String, Integer>>> result = stream
      // 提取时间戳与设置Watermark
      .assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor<Tuple3<String, Long, Integer>>(Time.minutes(10)) {
          @Override
          public long extractTimestamp(Tuple3<String, Long, Integer> element) {
              return element.f1;
          }
      })
      // 格式转换
      .map(new MapFunction<Tuple3<String,Long,Integer>, Tuple2<String, Integer>>() {
          @Override
          public Tuple2<String, Integer> map(Tuple3<String, Long, Integer> value) throws Exception {
              return new Tuple2<String, Integer>(value.f0, value.f2);
          }
      })
      // 分组
      .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
          @Override
          public String getKey(Tuple2<String, Integer> value) throws Exception {
              return value.f0;
          }
      })
      // 窗口大小为10分钟、滑动步长为5分钟的滑动窗口
      .timeWindow(Time.minutes(10), Time.minutes(5))
      // ReduceFunction 相同单词将第二个字段求和
      .reduce(new MyReduceFunction(), new MyProcessWindowFunction());

/**
 * 自定义ReduceFunction：根据Key实现SUM
 */
private static class MyReduceFunction implements ReduceFunction<Tuple2<String, Integer>> {
    public Tuple2<String, Integer> reduce(Tuple2<String, Integer> value1, Tuple2<String, Integer> value2) {
        return new Tuple2(value1.f0, value1.f1 + value2.f1);
    }
}

/**
 * 自定义ProcessWindowFunction：获取窗口元信息
 */
private static class MyProcessWindowFunction extends ProcessWindowFunction<Tuple2<String, Integer>, Tuple2<ContextInfo, Tuple2<String, Integer>>, String, TimeWindow> {
    @Override
    public void process(String key, Context context, Iterable<Tuple2<String, Integer>> elements, Collector<Tuple2<ContextInfo, Tuple2<String, Integer>>> out) throws Exception {
        Tuple2<String, Integer> tuple = elements.iterator().next();
        // 窗口元信息
        TimeWindow window = context.window();
        long start = window.getStart();
        long end = window.getEnd();
        String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
        String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
        long currentWatermark = context.currentWatermark();
        String currentWatermarkTime = DateUtil.timeStamp2Date(currentWatermark, "yyyy-MM-dd HH:mm:ss");
        long currentProcessingTimeStamp = context.currentProcessingTime();
        String currentProcessingTime = DateUtil.timeStamp2Date(currentProcessingTimeStamp, "yyyy-MM-dd HH:mm:ss");

        ContextInfo contextInfo = new ContextInfo();
        contextInfo.setKey(tuple.f0);
        contextInfo.setSum(tuple.f1);
        contextInfo.setWindowStartTime(startTime);
        contextInfo.setWindowEndTime(endTime);
        contextInfo.setCurrentWatermark(currentWatermarkTime);
        contextInfo.setCurrentProcessingTime(currentProcessingTime);
        LOG.info("[WINDOW] " + contextInfo.toString());
        // 输出
        out.collect(new Tuple2<ContextInfo, Tuple2<String, Integer>>(contextInfo, tuple));
    }
}
```
> 完成代码请查阅:[ReduceProcessWindowFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/ReduceProcessWindowFunctionExample.java)

通过如下输入数据，我们可以观察输出的具体窗口信息以及Watermark：
```
A,2021-02-14 12:07:01
B,2021-02-14 12:08:01
A,2021-02-14 12:14:01
C,2021-02-14 12:09:01
C,2021-02-14 12:15:01
A,2021-02-14 12:08:01
B,2021-02-14 12:13:01
B,2021-02-14 12:21:01
D,2021-02-14 12:04:01
B,2021-02-14 12:26:01
B,2021-02-14 12:17:01
D,2021-02-14 12:09:01
C,2021-02-14 12:30:01
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-function-4.jpg?raw=true)

#### 5.2 使用AggregateFunction进行增量聚合

如下代码示例展示了如何将 AggregateFunction 增量函数与 ProcessWindowFunction 组合使用以返回窗口中的不同Key的平均值以及该窗口的开始时间等窗口元信息：
```java
DataStream<Tuple2<ContextInfo, Tuple3<Long, Long, Double>>> result = stream
          // 提取时间戳与设置Watermark
          .assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor<Tuple3<String, Long, Integer>>(Time.minutes(10)) {
              @Override
              public long extractTimestamp(Tuple3<String, Long, Integer> element) {
                  return element.f1;
              }
          })
          // 格式转换
          .map(new MapFunction<Tuple3<String,Long,Integer>, Tuple2<String, Integer>>() {
              @Override
              public Tuple2<String, Integer> map(Tuple3<String, Long, Integer> value) throws Exception {
                  return new Tuple2<String, Integer>(value.f0, value.f2);
              }
          })
          // 分组
          .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
              @Override
              public String getKey(Tuple2<String, Integer> value) throws Exception {
                  return value.f0;
              }
          })
          // 窗口大小为10分钟、滑动步长为5分钟的滑动窗口
          .timeWindow(Time.minutes(10), Time.minutes(5))
          // 分组求平均值
          .aggregate(new MyAggregateFunction(), new MyProcessWindowFunction());

/**
 * 自定义ReduceFunction：根据Key实现求平均数
 */
private static class MyAggregateFunction implements AggregateFunction<Tuple2<String, Integer>, Tuple2<Long, Long>, Tuple3<Long, Long, Double>> {

    // IN：Tuple2<String, Integer>
    // ACC：Tuple2<Long, Long> -> <Sum, Count>
    // OUT：Tuple3<Long, Long, Double>

    @Override
    public Tuple2<Long, Long> createAccumulator() {
        return new Tuple2<Long, Long>(0L, 0L);
    }

    @Override
    public Tuple2<Long, Long> add(Tuple2<String, Integer> value, Tuple2<Long, Long> accumulator) {
        return new Tuple2<Long, Long>(accumulator.f0 + value.f1, accumulator.f1 + 1L);
    }

    @Override
    public Tuple3<Long, Long, Double> getResult(Tuple2<Long, Long> accumulator) {
        return new Tuple3<>(accumulator.f0, accumulator.f1, ((double) accumulator.f0) / accumulator.f1);
    }

    @Override
    public Tuple2<Long, Long> merge(Tuple2<Long, Long> a, Tuple2<Long, Long> b) {
        return new Tuple2<Long, Long>(a.f0 + b.f0, a.f1 + b.f1);
    }
}

/**
 * 自定义ProcessWindowFunction：获取窗口元信息
 */
private static class MyProcessWindowFunction extends ProcessWindowFunction<Tuple3<Long, Long, Double>, Tuple2<ContextInfo, Tuple3<Long, Long, Double>>, String, TimeWindow> {
    @Override
    public void process(String key, Context context, Iterable<Tuple3<Long, Long, Double>> elements, Collector<Tuple2<ContextInfo, Tuple3<Long, Long, Double>>> out) throws Exception {
        Tuple3<Long, Long, Double> tuple = elements.iterator().next();
        // 窗口元信息
        TimeWindow window = context.window();
        long start = window.getStart();
        long end = window.getEnd();
        String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
        String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");
        long currentWatermark = context.currentWatermark();
        String currentWatermarkTime = DateUtil.timeStamp2Date(currentWatermark, "yyyy-MM-dd HH:mm:ss");
        long currentProcessingTimeStamp = context.currentProcessingTime();
        String currentProcessingTime = DateUtil.timeStamp2Date(currentProcessingTimeStamp, "yyyy-MM-dd HH:mm:ss");

        ContextInfo contextInfo = new ContextInfo();
        contextInfo.setKey(key);
        contextInfo.setResult("SUM: " + tuple.f0 + ", Count: " + tuple.f1 + ", Average: " + tuple.f2);
        contextInfo.setWindowStartTime(startTime);
        contextInfo.setWindowEndTime(endTime);
        contextInfo.setCurrentWatermark(currentWatermarkTime);
        contextInfo.setCurrentProcessingTime(currentProcessingTime);
        LOG.info("[WINDOW] " + contextInfo.toString());
        // 输出
        out.collect(new Tuple2<ContextInfo, Tuple3<Long, Long, Double>>(contextInfo, tuple));
    }
}
```
> 完成代码请查阅:[AggregateProcessWindowFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/AggregateProcessWindowFunctionExample.java)

通过如下输入数据，我们可以观察输出的具体窗口信息以及Watermark：
```
A,2021-02-14 12:07:01,9
B,2021-02-14 12:08:01,5
A,2021-02-14 12:14:01,3
C,2021-02-14 12:09:01,2
C,2021-02-14 12:15:01,5
A,2021-02-14 12:08:01,4
B,2021-02-14 12:13:01,6
B,2021-02-14 12:21:01,1
D,2021-02-14 12:04:01,3
B,2021-02-14 12:26:01,2
B,2021-02-14 12:17:01,7
D,2021-02-14 12:09:01,8
C,2021-02-14 12:30:01,1
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-function-5.jpg?raw=true)

### 6. WindowFunction

在某些可以使用 ProcessWindowFunction 的地方，我们也可以使用 WindowFunction。这是 ProcessWindowFunction 的旧版本，提供的上下文信息比较少，并且缺乏某些高级功能，例如，每个窗口的 Keyed 状态。WindowFunction 的结构如下所示：
```java
public interface WindowFunction<IN, OUT, KEY, W extends Window> extends Function, Serializable {
  void apply(KEY key, W window, Iterable<IN> input, Collector<OUT> out) throws Exception;
}
```
如下代码展示了如何使用 WindowFunction 实现分组统计的功能：
```java
DataStream<Tuple2<String, Integer>> result = stream
        // 提取时间戳与设置Watermark
        .assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor<Tuple3<String, Long, Integer>>(Time.minutes(10)) {
            @Override
            public long extractTimestamp(Tuple3<String, Long, Integer> element) {
                return element.f1;
            }
        })
        // 分组
        .keyBy(new KeySelector<Tuple3<String, Long, Integer>, String>() {
            @Override
            public String getKey(Tuple3<String, Long, Integer> value) throws Exception {
                return value.f0;
            }
        })
        // 窗口大小为10分钟、滑动步长为5分钟的滑动窗口
        .timeWindow(Time.minutes(10), Time.minutes(5))
        .apply(new MyWindowFunction());

/**
 * 自定义实现WindowFunction
 */
private static class MyWindowFunction implements WindowFunction<Tuple3<String, Long, Integer>, Tuple2<String, Integer>, String, TimeWindow> {
    @Override
    public void apply(String key, TimeWindow window, Iterable<Tuple3<String, Long, Integer>> input, Collector<Tuple2<String, Integer>> out) throws Exception {
        int count = 0;
        List<String> list = Lists.newArrayList();
        for (Tuple3<String, Long, Integer> element : input) {
            list.add(element.f0 + "|" + element.f1 + "|" + DateUtil.timeStamp2Date(element.f1, "yyyy-MM-dd HH:mm:ss"));
            Integer value = element.f2;
            count += value;
        }

        // 窗口元信息相对ProcessWindowFunction较少
        long start = window.getStart();
        long end = window.getEnd();
        String startTime = DateUtil.timeStamp2Date(start, "yyyy-MM-dd HH:mm:ss");
        String endTime = DateUtil.timeStamp2Date(end, "yyyy-MM-dd HH:mm:ss");

        StringBuilder sb = new StringBuilder();
        sb.append("[Window] Key: " + list.toString());
        sb.append(", Window：[" + startTime + ", " + endTime + "]");
        sb.append(", Count: " + count);
        LOG.info(sb.toString());

        out.collect(new Tuple2<>(key, count));
    }
}
```
> 完成代码请查阅:[WindowFunctionExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/window/WindowFunctionExample.java)

通过如下输入数据，我们可以观察输出的具体窗口信息以及Watermark：
```
A,2021-02-14 12:07:01
B,2021-02-14 12:08:01
A,2021-02-14 12:14:01
C,2021-02-14 12:09:01
C,2021-02-14 12:15:01
A,2021-02-14 12:08:01
B,2021-02-14 12:13:01
B,2021-02-14 12:21:01
D,2021-02-14 12:04:01
B,2021-02-14 12:26:01
B,2021-02-14 12:17:01
D,2021-02-14 12:09:01
C,2021-02-14 12:30:01
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-stream-windows-function-6.jpg?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

推荐订阅：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-jk.jpeg?raw=true)

参考:
- [Window Functions](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/stream/operators/windows.html#window-functions)
- Flink核心技术与实战
