---
layout: post
author: sjf0115
title: Flink Table API & SQL 自定义 TableAggregate 表聚合函数
date: 2022-05-21 10:02:21
tags:
  - Flink

categories: Flink
permalink: flink-table-sql-custom-table-aggregate-function
---

> Flink 版本：1.13.5

## 1. 什么是表聚合函数

Table Aggregate function 也被称为表聚合函数，主要功能是将一行或多行数据进行聚合然后输出一行或者多行数据。我们可以理解为是表函数和聚合函数的一个结合，是一个'多对多'的转换。

## 2. 如何自定义表聚合函数

自定义表聚合函数 Table Aggregate Function 需要继承 org.apache.flink.table.functions.TableAggregateFunction 抽象类。TableAggregateFunction 的结构和原理与 AggregateFunction 非常类似，同样有两个泛型参数 `<T, ACC>`，T 表示聚合输出的结果类型，ACC 则表示聚合的中间状态类型：
```java
public class Top2TableAggregateFunction extends TableAggregateFunction<Tuple2<Long, Integer>, Top2TableAggregateFunction.Top2Accumulator> {
  ...
}
```
表聚合函数的核心同样也是累加器 Accumulator，我们需要自定义一个累加器。累加器是一种中间数据结构，用于存储聚合值，直到计算出最终聚合结果。如下所示的累加器用来存储输入元素的总和以及元素个数：
```java
// Top2 聚合中间结果数据结构
public static class Top2Accumulator {
    public long first = 0;
    public long second = 0;
}
```
在 TableAggregateFunction 抽象类中同样也包含了必须实现的方法 createAccumulator、emitValue（或者 emitUpdateWithRetract）、accumulate。在方法实现中，与聚合函数最大的不同就是在输出方法上使用了 emitValue（或者 emitUpdateWithRetract）：
```java
public void emitValue(Top2Accumulator acc, Collector<Tuple2<Long, Integer>> out) {
    if (acc.first != Integer.MIN_VALUE) {
        out.collect(Tuple2.of(acc.first, 1));
    }
    if (acc.second != Integer.MIN_VALUE) {
        out.collect(Tuple2.of(acc.second, 2));
    }
}
```
区别在于 emitValue 没有输出类型，而输入参数有两个：第一个是 ACC 类型的累加器，第二个则是用于输出数据的 `Collector<T>` 类型的 out。表聚合函数输出数据不再像聚合函数一样直接 return，而是调用 out.collect 方法。聚合函数的 getValue 方法一次只能输出一个标量值，而 emitValue（或者 emitUpdateWithRetract）调用多次就可以输出多行数据，在这一点上与表函数非常相似。需要注意的是，emitValue 在抽象类中没有定义，所以不能直接在代码中重写该方法，只能手动实现。

回过头来，我们看一下必须实现的其他方法。其中，createAccumulator 方法主要用于创建一个空的 Accumulator，用来存储计算过程中读取的中间数据：
```java
@Override
public Top2Accumulator createAccumulator() {
    Top2Accumulator acc = new Top2Accumulator();
    acc.first = Integer.MIN_VALUE;
    acc.second = Integer.MIN_VALUE;
    return acc;
}
```
> 在这我们还对变量做了初始化

accumulate 方法将每次传入的数据元素累加到自定义的累加器中(在这是 Top2Accumulator)，另外 accumulate 方法也可以通过方法复载的方式处理不同类型的数据：
```java
public void accumulate(Top2Accumulator acc, Long value) {
    if (value > acc.first) {
        acc.second = acc.first;
        acc.first = value;
    } else if (value > acc.second) {
        acc.second = value;
    }
}
```
这是进行聚合计算的核心方法，每来一行数据都会调用。它的第一个参数是确定的，就是当前的累加器，后面的参数则是聚合函数调用时传入的参数，可以有多个，类型也可以不同。这个方法主要是更新聚合状态，所以没有返回类型。需要注意的是，accumulate 方法在抽象类中也没有定义，所以不能直接在代码中重写该方法，只能手动实现。

除了以上三个必须要实现的方法之外，在 Table Aggregation Function 中还有根据具体使用场景选择性实现的方法，如 retract、merge 等方法。其中，merge 方法是在多批聚合和 Session Window 场景中使用，它会定义累加器的合并操作，而且这个方法对一些场景的优化也很有用。retract 方法是在聚合函数用在 OVER 窗口聚合中使用，保证数据可以进行撤回操作。

## 3. 示例

表聚合函数的一个典型应用场景就是 Top N。在示例中，假设我们有一个每位同学成绩单的表。该表由三列（name、course 和 score）、8 行数据组成。我们希望找到表中每门课程成绩最高的两位同学，即每门课程的 Top2。我们需要检查每一行数据并输出一个包含成绩最高的两位同学的表。具体代码如下：
```java
public class Top2TableAggregateFunction extends TableAggregateFunction<Tuple2<Long, Integer>, Top2TableAggregateFunction.Top2Accumulator> {
    // Top2 聚合中间结果数据结构
    public static class Top2Accumulator {
        public long first = 0;
        public long second = 0;
    }

    // 创建 Top2Accumulator 累加器并做初始化
    @Override
    public Top2Accumulator createAccumulator() {
        Top2Accumulator acc = new Top2Accumulator();
        acc.first = Integer.MIN_VALUE;
        acc.second = Integer.MIN_VALUE;
        return acc;
    }

    // 接收输入元素并累加到 Accumulator 数据结构
    public void accumulate(Top2Accumulator acc, Long value) {
        if (value > acc.first) {
            acc.second = acc.first;
            acc.first = value;
        } else if (value > acc.second) {
            acc.second = value;
        }
    }

    // 输出元素
    public void emitValue(Top2Accumulator acc, Collector<Tuple2<Long, Integer>> out) {
        if (acc.first != Integer.MIN_VALUE) {
            out.collect(Tuple2.of(acc.first, 1));
        }
        if (acc.second != Integer.MIN_VALUE) {
            out.collect(Tuple2.of(acc.second, 2));
        }
    }

    // 合并
    public void merge(Top2Accumulator acc, Iterable<Top2Accumulator> iterable) {
        for (Top2Accumulator otherAcc : iterable) {
            // 复用 accumulate 方法
            accumulate(acc, otherAcc.first);
            accumulate(acc, otherAcc.second);
        }
    }
}
```
emitValue 方法总是输出累加器的全部的数据。在无界场景下，这可能会带来性能问题。以 Top N 为例。emitValue 每次都会输出所有 N 个值。可以使用 emitUpdateWithRetract 来改善 emitValue 的性能问题，以撤回模式增量输出数据。换句话说，一旦有更新，该方法可以在发送新的更新记录之前撤回旧记录。为此，累加器需要保留旧的和新的前两个值：
```java
public class Top2RetractTableAggregateFunction extends TableAggregateFunction<Tuple2<Long, Integer>, Top2RetractTableAggregateFunction.Top2Accumulator> {
    // Top2 聚合中间结果数据结构
    public static class Top2Accumulator {
        public long beforeFirst = 0;
        public long beforeSecond = 0;
        public long afterFirst = 0;
        public long afterSecond = 0;
    }

    // 创建 Top2Accumulator 累加器并做初始化
    @Override
    public Top2Accumulator createAccumulator() {
        Top2Accumulator acc = new Top2Accumulator();
        acc.beforeFirst = Integer.MIN_VALUE;
        acc.beforeSecond = Integer.MIN_VALUE;
        acc.afterFirst = Integer.MIN_VALUE;
        acc.afterSecond = Integer.MIN_VALUE;
        return acc;
    }

    // 接收输入元素并累加到 Accumulator 数据结构
    public void accumulate(Top2Accumulator acc, Long value) {
        if (value > acc.afterFirst) {
            acc.afterSecond = acc.afterFirst;
            acc.afterFirst = value;
        } else if (value > acc.afterSecond) {
            acc.afterSecond = value;
        }
    }

    // 带撤回的输出
    public void emitUpdateWithRetract(Top2Accumulator acc, RetractableCollector<Tuple2<Long, Integer>> out) {
        if (!Objects.equals(acc.afterFirst, acc.beforeFirst)) {
            // 撤回旧记录
            if (acc.beforeFirst != Integer.MIN_VALUE) {
                out.retract(Tuple2.of(acc.beforeFirst, 1));
            }
            // 输出新记录
            out.collect(Tuple2.of(acc.afterFirst, 1));
            acc.beforeFirst = acc.afterFirst;
        }
        if (!Objects.equals(acc.afterSecond, acc.beforeSecond)) {
            // 撤回旧记录
            if (acc.beforeSecond != Integer.MIN_VALUE) {
                out.retract(Tuple2.of(acc.beforeSecond, 2));
            }
            // 输出新记录
            out.collect(Tuple2.of(acc.afterSecond, 2));
            acc.beforeSecond = acc.afterSecond;
        }
    }
}
```

## 4. 调用

### 4.1 非撤回输出模式

非撤回输出模式即使用 emitValue 方法输出数据。对于 Table API，可以直接通过内联方式使用：
```java
DataStream<Row> sourceStream = env.fromElements(
        Row.of("李雷", "语文", 78),
        Row.of("韩梅梅", "语文", 50),
        Row.of("李雷", "语文", 99),
        Row.of("韩梅梅", "语文", 80),
        Row.of("李雷", "英语", 90),
        Row.of("韩梅梅", "英语", 40),
        Row.of("李雷", "英语", 98),
        Row.of("韩梅梅", "英语", 88)
);

// 注册虚拟表
tEnv.createTemporaryView("stu_score", sourceStream, $("name"), $("course"), $("score"));

tEnv.from("stu_score")
    .groupBy($("course"))
    .flatAggregate(call(Top2TableAggregateFunction.class, $("score")))
    .select($("course"), $("f0"), $("f1"))
    .execute()
    .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+----------------------+-------------+
| op |                         course |                   f0 |          f1 |
+----+--------------------------------+----------------------+-------------+
| +I |                           语文 |                   78 |           1 |
| -D |                           语文 |                   78 |           1 |
| +I |                           语文 |                   78 |           1 |
| +I |                           语文 |                   50 |           2 |
| -D |                           语文 |                   78 |           1 |
| -D |                           语文 |                   50 |           2 |
| +I |                           语文 |                   99 |           1 |
| +I |                           语文 |                   78 |           2 |
| -D |                           语文 |                   99 |           1 |
| -D |                           语文 |                   78 |           2 |
| +I |                           语文 |                   99 |           1 |
| +I |                           语文 |                   80 |           2 |
| +I |                           英语 |                   90 |           1 |
| -D |                           英语 |                   90 |           1 |
| +I |                           英语 |                   90 |           1 |
| +I |                           英语 |                   40 |           2 |
| -D |                           英语 |                   90 |           1 |
| -D |                           英语 |                   40 |           2 |
| +I |                           英语 |                   98 |           1 |
| +I |                           英语 |                   90 |           2 |
| -D |                           英语 |                   98 |           1 |
| -D |                           英语 |                   90 |           2 |
| +I |                           英语 |                   98 |           1 |
| +I |                           英语 |                   90 |           2 |
+----+--------------------------------+----------------------+-------------+
```
除了通过内联方式直接调用之外，也可以先通过 createTemporarySystemFunction 函数注册为临时系统函数，然后再调用。在这我们同时对输出字段做了重命名：
```java
tEnv.createTemporarySystemFunction("Top2", new Top2TableAggregateFunction());
tEnv.from("stu_score")
        .groupBy($("course"))
        .flatAggregate(call("Top2", $("score")).as("score", "rank"))
        .select($("course"), $("score"), $("rank"))
        .execute()
        .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+----------------------+-------------+
| op |                         course |                score |        rank |
+----+--------------------------------+----------------------+-------------+
| +I |                           语文 |                   78 |           1 |
| -D |                           语文 |                   78 |           1 |
| +I |                           语文 |                   78 |           1 |
| +I |                           语文 |                   50 |           2 |
| -D |                           语文 |                   78 |           1 |
| -D |                           语文 |                   50 |           2 |
| +I |                           语文 |                   99 |           1 |
| +I |                           语文 |                   78 |           2 |
| -D |                           语文 |                   99 |           1 |
| -D |                           语文 |                   78 |           2 |
| +I |                           语文 |                   99 |           1 |
| +I |                           语文 |                   80 |           2 |
| +I |                           英语 |                   90 |           1 |
| -D |                           英语 |                   90 |           1 |
| +I |                           英语 |                   90 |           1 |
| +I |                           英语 |                   40 |           2 |
| -D |                           英语 |                   90 |           1 |
| -D |                           英语 |                   40 |           2 |
| +I |                           英语 |                   98 |           1 |
| +I |                           英语 |                   90 |           2 |
| -D |                           英语 |                   98 |           1 |
| -D |                           英语 |                   90 |           2 |
| +I |                           英语 |                   98 |           1 |
| +I |                           英语 |                   90 |           2 |
+----+--------------------------------+----------------------+-------------+
```

### 4.2 撤回输出模式

撤回输出模式即使用 emitUpdateWithRetract 方法输出数据。对于 Table API，可以直接通过内联方式使用：
```java
DataStream<Row> sourceStream = env.fromElements(
        Row.of("李雷", "语文", 78),
        Row.of("韩梅梅", "语文", 50),
        Row.of("李雷", "语文", 99),
        Row.of("韩梅梅", "语文", 80),
        Row.of("李雷", "英语", 90),
        Row.of("韩梅梅", "英语", 40),
        Row.of("李雷", "英语", 98),
        Row.of("韩梅梅", "英语", 88)
);

// 注册虚拟表
tEnv.createTemporaryView("stu_score", sourceStream, $("name"), $("course"), $("score"));

tEnv.from("stu_score")
  .groupBy($("course"))
  .flatAggregate(call(Top2RetractTableAggregateFunction.class, $("score")))
  .select($("course"), $("f0"), $("f1"))
  .execute()
  .print();
```
如上代码输出如下结果：
```

```
除了通过内联方式直接调用之外，也可以先通过 createTemporarySystemFunction 函数注册为临时系统函数，然后再调用。在这我们同时对输出字段做了重命名：
```java
tEnv.createTemporarySystemFunction("Top2", new Top2TableAggregateFunction());
tEnv.from("stu_score")
        .groupBy($("course"))
        .flatAggregate(call("Top2", $("score")).as("score", "rank"))
        .select($("course"), $("score"), $("rank"))
        .execute()
        .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+----------------------+-------------+
| op |                         course |                score |        rank |
+----+--------------------------------+----------------------+-------------+
| +I |                           语文 |                   78 |           1 |
| -D |                           语文 |                   78 |           1 |
| +I |                           语文 |                   78 |           1 |
| +I |                           语文 |                   50 |           2 |
| -D |                           语文 |                   78 |           1 |
| -D |                           语文 |                   50 |           2 |
| +I |                           语文 |                   99 |           1 |
| +I |                           语文 |                   78 |           2 |
| -D |                           语文 |                   99 |           1 |
| -D |                           语文 |                   78 |           2 |
| +I |                           语文 |                   99 |           1 |
| +I |                           语文 |                   80 |           2 |
| +I |                           英语 |                   90 |           1 |
| -D |                           英语 |                   90 |           1 |
| +I |                           英语 |                   90 |           1 |
| +I |                           英语 |                   40 |           2 |
| -D |                           英语 |                   90 |           1 |
| -D |                           英语 |                   40 |           2 |
| +I |                           英语 |                   98 |           1 |
| +I |                           英语 |                   90 |           2 |
| -D |                           英语 |                   98 |           1 |
| -D |                           英语 |                   90 |           2 |
| +I |                           英语 |                   98 |           1 |
| +I |                           英语 |                   90 |           2 |
+----+--------------------------------+----------------------+-------------+
```
