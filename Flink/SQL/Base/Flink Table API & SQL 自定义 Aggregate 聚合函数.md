---
layout: post
author: sjf0115
title: Flink Table API & SQL 自定义 Aggregate 聚合函数
date: 2022-05-20 10:02:21
tags:
  - Flink

categories: Flink
permalink: flink-table-sql-custom-aggregate-function
---

> Flink 版本：1.13.5

## 1. 什么是聚合函数

Aggregate function 也被称为聚合函数，主要功能是将一行或多行数据进行聚合然后输出一个标量值，例如在数据集中根据 Key 求取指定 Value 的最大值或最小值。这是一个'多对一'的转换。Flink 常见的内置聚合函数函数有 SUM()、MAX()、MIN()、AVG()、COUNT() 等。

## 2. 如何自定义聚合函数

自定义聚合函数 Aggregate Function 需要继承 org.apache.flink.table.functions.AggregateFunction 抽象类。AggregateFunction 有两个泛型参数 `<T, ACC>`，T 表示聚合输出的结果类型，ACC 则表示聚合的中间状态类型：
```java
public class AvgAggregateFunction extends AggregateFunction<Double, AvgAggregateFunction2.AvgAccumulator> {
    // 聚合中间结果数据结构
    public static class AvgAccumulator {
        public long sum = 0;
        public int count = 0;
    }

    //---------------------------------------------------
    // 1. 必须实现的方法

    // 创建 Accumulator 数据结构
    @Override
    public AvgAccumulator createAccumulator() {
        return null;
    }
    // 返回最终结果
    @Override
    public Double getValue(AvgAccumulator accumulator) {
        return null;
    }
    // 接收输入元素并累加到 Accumulator 数据结构
    public void accumulate(AvgAccumulator acc, Long value) {
    }

    //------------------------------------------------------
    // 2. 非必须实现的方法
    // 回撤
    public void retract(AvgAccumulator acc, Long value) {
    }
    // 合并 Accumulator 数据结构
    public void merge(AvgAccumulator acc, Iterable<AvgAccumulator> iterable) {
    }
    // 重置 Accumulator 数据结构
    public void resetAccumulator(AvgAccumulator acc) {
    }
}
```
聚合函数的核心是累加器 Accumulator，我们需要自定义一个累加器。累加器是一种中间数据结构，用于存储聚合值，直到计算出最终聚合结果。如下所示的累加器用来存储输入元素的总和以及元素个数：
```java
// 聚合中间结果数据结构
public static class AvgAccumulator {
    public long sum = 0;
    public int count = 0;
}
```
在 AggregateFunction 抽象类中包含了必须实现的方法 createAccumulator、getValue、accumulate。其中，createAccumulator 方法主要用于创建一个空的 Accumulator，用来存储计算过程中读取的中间数据：
```java
@Override
public AvgAccumulator createAccumulator() {
    return new AvgAccumulator();
}
```
accumulate 方法将每次传入的数据元素累加到自定义的累加器中(在这是 AvgAccumulator)，另外 accumulate 方法也可以通过方法复载的方式处理不同类型的数据：
```java
public void accumulate(AvgAccumulator acc, Long value) {
    // 更新累加器
    acc.sum += value;
    acc.count ++;
}
```
这是进行聚合计算的核心方法，每来一行数据都会调用。它的第一个参数是确定的，就是当前的累加器，后面的参数则是聚合函数调用时传入的参数，可以有多个，类型也可以不同。这个方法主要是更新聚合状态，所以没有返回类型。需要注意的是，accumulate 方法与之前标量函数和表函数中的 eval 类似，抽象类中并没有定义 accumulate 方法，所以不能直接在代码中重写该方法，只能手动实现，但 Table API 的框架底层又要求了计算方法必须为 accumulate，同时必须为 public。

当完成所有的数据累加操作结束后，最后通过 getValue 方法返回函数的统计结果，最终完成整个 AggregateFunction 的计算流程。输入参数是 ACC 类型的累加器，输出类型为 T：
```java
@Override
public Double getValue(AvgAccumulator acc) {
    // 输出最终结果 平均值
    if (acc.count == 0) {
        return null;
    } else {
        return acc.sum * 1.0 / acc.count;
    }
}
```
在遇到复杂类型时，Flink 的类型推导可能会无法得到正确的结果。所以 AggregateFunction 也可以专门对累加器和返回结果的类型进行声明，可以通过 getTypeInference 方法来指定的。

除了以上三个必须要实现的方法之外，在 Aggregation Function 中还有根据具体使用场景选择性实现的方法，如 retract、merge、resetAccumulator 等方法。其中，merge 方法是在多批聚合和 Session Window 场景中使用，它会定义累加器的合并操作，而且这个方法对一些场景的优化也很有用：
```java
// 非必须:合并 Accumulator 数据结构
public void merge(AvgAccumulator acc, Iterable<AvgAccumulator> iterable) {
    for (AvgAccumulator a : iterable) {
        acc.count += a.count;
        acc.sum += a.sum;
    }
}
```
retract 方法是在聚合函数用在 OVER 窗口聚合中使用，保证数据可以进行撤回操作：
```java
// 非必须:回撤
public void retract(AvgAccumulator acc, Long value) {
    acc.sum -= value;
    acc.count --;
}
```
resetAccumulator 方法是在批量计算中多批聚合的场景中使用，主要对 accumulator 计数器进行重置操作：
```java
// 非必须:重置 Accumulator 数据结构
public void resetAccumulator(AvgAccumulator acc) {
    acc.count = 0;
    acc.sum = 0L;
}
```
AggregateFunction 的所有方法都必须是 public 的，并且不能是静态的。

> 因为目前在 Flink 中对 Scala 的类型参数提取效率相对较低，因此 Flink 建议用户尽可能实现 Java 语言的 Aggregation Function，同时应尽可能使用原始数据类型，例如 Int、Long 等，避免使用复合数据类型，如自定义 POJOs 等，这样做的主要原因是在 Aggregation Function 计算过程中，期间会有大量对象被创建和销毁，将对整个系统的性能造成一定的影响。

下面举一个具体的示例，来实现系统内置聚合函数里的 AVG() 来计算平均值：
```java
public class AvgAggregateFunction extends AggregateFunction<Double, AvgAggregateFunction.AvgAccumulator>{

    // 聚合中间结果数据结构
    public static class AvgAccumulator {
        public long sum = 0;
        public int count = 0;
    }

    // 创建 Accumulator 数据结构
    @Override
    public AvgAccumulator createAccumulator() {
        return new AvgAccumulator();
    }

    // 返回最终结果 平均值
    @Override
    public Double getValue(AvgAccumulator acc) {
        if (acc.count == 0) {
            return null;
        } else {
            return acc.sum * 1.0 / acc.count;
        }
    }

    // 接收输入元素并累加到 Accumulator 数据结构
    public void accumulate(AvgAccumulator acc, Long value) {
        acc.sum += value;
        acc.count ++;
    }

    // 非必须:回撤
    public void retract(AvgAccumulator acc, Long value) {
        acc.sum -= value;
        acc.count --;
    }

    // 非必须:合并 Accumulator 数据结构
    public void merge(AvgAccumulator acc, Iterable<AvgAccumulator> iterable) {
        for (AvgAccumulator a : iterable) {
            acc.count += a.count;
            acc.sum += a.sum;
        }
    }

    // 非必须:重置 Accumulator 数据结构
    public void resetAccumulator(AvgAccumulator acc) {
        acc.count = 0;
        acc.sum = 0L;
    }
}
```
## 3. 调用函数

### 3.1 Table API

对于 Table API，可以直接通过内联方式使用：
```java
DataStream<Row> sourceStream = env.fromElements(
        Row.of("李雷", "语文", 58),
        Row.of("韩梅梅", "英语", 90),
        Row.of("李雷", "英语", 95),
        Row.of("韩梅梅", "语文", 85)
);

// 注册虚拟表
tEnv.createTemporaryView("stu_score", sourceStream, $("name"), $("course"), $("score"));
tEnv.from("stu_score")
  .groupBy($("course"))
  .select($("course"), call(AvgAggregateFunction.class, $("score")).as("avg_score"))
  .execute()
  .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                         course |                      avg_score |
+----+--------------------------------+--------------------------------+
| +I |                           英语 |                           90.0 |
| -U |                           英语 |                           90.0 |
| +U |                           英语 |                           92.5 |
| +I |                           语文 |                           58.0 |
| -U |                           语文 |                           58.0 |
| +U |                           语文 |                           71.5 |
+----+--------------------------------+--------------------------------+
```
除了通过内联方式直接调用之外，也可以先通过 createTemporarySystemFunction 函数注册为临时系统函数，然后再调用：
```java
tEnv.createTemporarySystemFunction("custom_avg", AvgAggregateFunction.class);
tEnv.from("stu_score")
        .groupBy($("course"))
        .select($("course"), call("custom_avg", $("score")).as("avg_score"))
        .execute()
        .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                         course |                      avg_score |
+----+--------------------------------+--------------------------------+
| +I |                           语文 |                           58.0 |
| -U |                           语文 |                           58.0 |
| +U |                           语文 |                           71.5 |
| +I |                           英语 |                           90.0 |
| -U |                           英语 |                           90.0 |
| +U |                           英语 |                           92.5 |
+----+--------------------------------+--------------------------------+
```

### 3.2 SQL

对于 SQL 查询，函数必须通过名称注册，然后被调用：
```java
tEnv.createTemporarySystemFunction("custom_avg", new AvgAggregateFunction());
tEnv.sqlQuery("SELECT course, custom_avg(score) AS avg_score FROM stu_score GROUP BY course")
        .execute()
        .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                         course |                      avg_score |
+----+--------------------------------+--------------------------------+
| +I |                           语文 |                           58.0 |
| -U |                           语文 |                           58.0 |
| +U |                           语文 |                           71.5 |
| +I |                           英语 |                           90.0 |
| -U |                           英语 |                           90.0 |
| +U |                           英语 |                           92.5 |
+----+--------------------------------+--------------------------------+
```

> [完整代码](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/custom/AvgAggregateFunctionExample.java)
