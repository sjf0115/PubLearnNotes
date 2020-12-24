---
layout: post
author: sjf0115
title: Flink 四种优化Flink应用程序的方法
date: 2018-02-11 10:39:01
tags:
  - Flink
  - Flink 优化

categories: Flink
permalink: four-ways-to-optimize-your-flink-applications
---

`Flink` 是一个复杂的框架，并提供了许多方法来调整其执行。在本文中，我将展示四种不同的方法来提高 `Flink` 应用程序的性能。如果你不熟悉 `Flink`，你可以阅读其他介绍性的文章，比如[这个](https://brewing.codes/2017/09/25/flink-vs-spark/)，[这个](https://brewing.codes/2017/10/01/start-flink-batch/)和[这个](https://brewing.codes/2017/10/09/start-flink-streaming/)。如果你已经熟悉 `Apache Flink`，本文将帮助你更快地创建应用程序。

### 1. 使用 Flink tuples

当你使用像 `groupBy`，`join` 或 `keyBy` 这样的操作时， `Flink` 提供了多种方式在数据集中选择`key`。你可以使用 `key` 选择器函数：
```java
// Join movies and ratings datasets
movies.join(ratings)
      // Use movie id as a key in both cases
      .where(new KeySelector<Movie, String>() {
            @Override
            public String getKey(Movie m) throws Exception {
                return m.getId();
            }
      })
      .equalTo(new KeySelector<Rating, String>() {
            @Override
            public String getKey(Rating r) throws Exception {
                return r.getMovieId();
            }
      })
```
或者你可以在 `POJO` 类型中指定一个字段名称：
```java
movies.join(ratings)
    // Use same fields as in the previous example
    .where("id")
    .equalTo("movieId")
```
但是，如果你正在使用 `Flink` `tuple` 类型，你可以简单地指定将要作为 `key` 的字段在元组中的位置：
```java
DataSet<Tuple2<String, String>> movies ...
DataSet<Tuple3<String, String, Double>> ratings ...

movies.join(ratings)
    // Specify fields positions in tuples
    .where(0)
    .equalTo(1)
```

最后一种方式会给你最好的性能，但可读性呢？ 这是否意味着你的代码现在看起来像这样：
```java
DataSet<Tuple3<Integer, String, Double>> result = movies.join(ratings)
    .where(0)
    .equalTo(0)
    .with(new JoinFunction<Tuple2<Integer,String>, Tuple2<Integer,Double>, Tuple3<Integer, String, Double>>() {
        // What is happening here?
        @Override
        public Tuple3<Integer, String, Double> join(Tuple2<Integer, String> first, Tuple2<Integer, Double> second) throws Exception {
            // Some tuples are joined with some other tuples and some fields are returned???
            return new Tuple3<>(first.f0, first.f1, second.f1);
        }
    });
```
在这种情况下，提高可读性的常见方法是创建一个继承自 `TupleX` 类的类，并为这些字段实现 `getter` 和 `setter` 方法。在这里，下面是 `Flink` `Gelly` 库的 `Edge` 类的大体实现，具有三个字段并继承了 `Tuple3` 类：
```java
public class Edge<K, V> extends Tuple3<K, K, V> {

    public Edge(K source, K target, V value) {
        this.f0 = source;
        this.f1 = target;
        this.f2 = value;
    }

    // Getters and setters for readability
    public void setSource(K source) {
        this.f0 = source;
    }

    public K getSource() {
        return this.f0;
    }

    // Also has getters and setters for other fields
    ...
}
```

### 2. 重用 Flink对象

另一个可以用来提高 `Flink` 应用程序性能的方法是当你从自定义函数中返回数据时使用可变对象。看看这个例子：
```
stream
    .apply(new WindowFunction<WikipediaEditEvent, Tuple2<String, Long>, String, TimeWindow>() {
        @Override
        public void apply(String userName, TimeWindow timeWindow, Iterable<WikipediaEditEvent> iterable, Collector<Tuple2<String, Long>> collector) throws Exception {
            long changesCount
            // A new Tuple instance is created on every execution
            collector.collect(new Tuple2<>(userName, changesCount));
        }
    }
```

正如你所看到的，在 `apply` 函数的每次执行中，我们都创建一个 `Tuple2` 类型的实例，这会给垃圾收集器造成很大压力。解决这个问题的一种方法是重复使用同一个实例：
```
stream
    .apply(new WindowFunction<WikipediaEditEvent, Tuple2<String, Long>, String, TimeWindow>() {
        // Create an instance that we will reuse on every call
        private Tuple2<String, Long> result = new Tuple<>();

        @Override
        public void apply(String userName, TimeWindow timeWindow, Iterable<WikipediaEditEvent> iterable, Collector<Tuple2<String, Long>> collector) throws Exception {
            long changesCount = ...

            // Set fields on an existing object instead of creating a new one
            result.f0 = userName;
            // Auto-boxing!! A new Long value may be created
            result.f1 = changesCount;

            // Reuse the same Tuple2 object
            collector.collect(result);
        }
    }
```
上述代码会更好些。虽然我们在每次调用的时候只创建了一个 `Tuple2` 实例，但是我们还是间接地创建了 `Long` 类型的实例。为了解决这个问题， `Flink` 提供了很多的值类（value classes），`IntValue`, `LongValue`, `StringValue`, `FloatValue` 等。这些类的目的是为内置类型提供可变版本，所以我们可以在用户自定义函数中重用这些类型，下面就是如何使用的例子：
```
stream
    .apply(new WindowFunction<WikipediaEditEvent, Tuple2<String, Long>, String, TimeWindow>() {
        // Create a mutable count instance
        private LongValue count = new IntValue();
        // Assign mutable count to the tuple
        private Tuple2<String, LongValue> result = new Tuple<>("", count);

        @Override
        // Notice that now we have a different return type
        public void apply(String userName, TimeWindow timeWindow, Iterable<WikipediaEditEvent> iterable, Collector<Tuple2<String, LongValue>> collector) throws Exception {
            long changesCount = ...

            // Set fields on an existing object instead of creating a new one
            result.f0 = userName;
            // Update mutable count value
            count.setValue(changesCount);

            // Reuse the same tuple and the same LongValue instance
            collector.collect(result);
        }
    }
```
上面这些使用习惯在 `Flink` 类库中被普遍使用，比如 `Flink` `Gelly`。

### 3. 使用函数注解

优化 `Flink` 应用程序的另一种方法是提供关于用户自定义函数对输入数据做什么的一些信息。由于 `Flink` 无法解析和理解代码，因此你可以提供关键信息，这将有助于构建更高效的执行计划。有三个注解我们可以使用：
- `@ForwardedFields` - 指定输入值中的哪些字段保持不变并在输出值中使用。
- `@NotForwardedFields` - 指定在输出中同一位置不保留的字段。
- `@ReadFields` - 指定用于计算结果值的字段。你只能指定那些在计算中使用的字段，而不是仅仅将数据拷贝到输出中的字段。

我们来看看如何使用 `ForwardedFields` 注解：
```java
// Specify that the first element is copied without any changes
@ForwardedFields("0")
class MyFunction implements MapFunction<Tuple2<Long, Double>, Tuple2<Long, Double>> {
    @Override
    public Tuple2<Long, Double> map(Tuple2<Long, Double> value) {
       // Copy first field without change
        return new Tuple2<>(value.f0, value.f1 + 123);
    }
}
```
上述代码意味着输入元组的第一个元素将不会改变，并且在返回时也处于同一个位置（译者注：第一个位置）。

如果你不改变字段，只是简单地将它移到不同的位置上，你同样可以使用 `ForwardedFields` 注解来实现。下面例子中，我们简单地将输入元组的字段进行交换（译者注：第一个字段移到第二个位置，第二个字段移到第一个位置）：
```java
// 1st element goes into the 2nd position, and 2nd element goes into the 1st position
@ForwardedFields("0->1; 1->0")
class SwapArguments implements MapFunction<Tuple2<Long, Double>, Tuple2<Double, Long>> {
    @Override
    public Tuple2<Double, Long> map(Tuple2<Long, Double> value) {
       // Swap elements in a tuple
        return new Tuple2<>(value.f1, value.f0);
    }
}
```
上面例子中提到的注解只能应用到只有一个输入参数的函数中，比如 `map` 或者 `flatMap`。如果你有两个输入参数的函数，你可以使用 `ForwardedFieldsFirst` 和 `ForwardedFieldsSecond` 注解分别为第一和第二个参数提供信息。

下面我们看一下如何在 `JoinFunction` 接口的实现中使用这些注解（译者注：第一个输入元组的两个字段拷贝到输出元组的第一个和第二个位置，第二个输入元组的第二个字段拷贝到输出元组的第三个位置）：
```java
// Two fields from the input tuple are copied to the first and second positions of the output tuple
@ForwardedFieldsFirst("0; 1")
// The third field from the input tuple is copied to the third position of the output tuple
@ForwardedFieldsSecond("2")
class MyJoin implements JoinFunction<Tuple2<Integer,String>, Tuple2<Integer,Double>, Tuple3<Integer, String, Double>>() {
    @Override
    public Tuple3<Integer, String, Double> join(Tuple2<Integer, String> first, Tuple2<Integer, Double> second) throws Exception {
        return new Tuple3<>(first.f0, first.f1, second.f1);
    }
})
```

`Flink` 同样提供了 `NotForwardedFieldsFirst`, `NotForwardedFieldsSecond`, `ReadFieldsFirst`, 和 `ReadFirldsSecond` 注解来实现同样的功能。

### 4. 选择 join 类型

如果你告诉 `Flink` 一些信息，可以加快 `join` 的速度，但在讨论它为什么会起作用之前，让我们先来谈谈 `Flink` 是如何执行 `join`的。

当 `Flink` 处理批量数据时，集群中的每台机器都存储了部分数据。要执行 `join` 操作，`Flink` 需要找到两个两个数据集中满足 `join` 条件的所有记录对（译者注：`key` 相同的数据）。 要做到这一点，`Flink` 首先必须将两个数据集中具有相同 `key` 的数据放在集群中的同一台机器上。有两种策略：
- `Repartition-Repartition` 策略：在这种场景下，根据它们的 `key` 对两个数据集进行重新分区，通过网络发送数据。这就意味着如果数据集非常大，这将花费大量的时间将数据在网络之间进行复制。
- `Broadcast-Forward` 策略：在这种场景下，一个数据集保持不变，将第二个数据集拷贝到集群上第二个数据集拥有第一个数据集部分数据的所有机器上（译者注：将达尔戈数据集进行分发到对应机器上）。

如果用一个较大的数据集与一个小数据集进行 `join`，你可以使用 `Broadcast-Forward` 策略并避免对第一个数据集进行重分区的昂贵代价。这很容易做到：
```
ds1.join(ds2, JoinHint.BROADCAST_HASH_FIRST)
```
这表示第一个数据集比第二个数据集小得多。

`Flink` 支持的其他 `join` 提示有以下几种：
- `BROADCAST_HASH_SECOND` – 表示第二个数据集比较小
- `REPARTITION_HASH_FIRST` – 表示第一个数据集比较小
- `REPARTITION_HASH_SECOND` – 表示第二个数据集有点小
- `REPARTITION_SORT_MERGE` – 表示对两个数据集重新分区并使用排序和合并策略
- `OPTIMIZER_CHOOSES` – `Flink` 优化器将决定如何连接数据集


原文： https://brewing.codes/2017/10/17/flink-optimize/
