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

除了以上三个必须要实现的方法之外，在 Table Aggregation Function 中还有根据具体使用场景选择性实现的方法，如 retract、merge、emitUpdateWithRetract 等方法。其中 emitUpdateWithRetract 主要用来改善性能问题。emitValue 方法总是输出累加器的全部的数据。在无界场景下，这可能会带来性能问题。以 Top N 为例。emitValue 每次都会输出所有 N 个值。为了提高性能，可以实现 emitUpdateWithRetract，以撤回模式增量输出数据。换句话说，一旦有更新，该方法可以在发送新的更新记录之前撤回旧记录。该方法将优先于 emitValue 方法使用：
```java

```
其中，merge 方法是在多批聚合和 Session Window 场景中使用，它会定义累加器的合并操作，而且这个方法对一些场景的优化也很有用：
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

表聚合函数相对比较复杂，它的一个典型应用场景就是 Top N 查询。比如我们希望选出 一组数据排序后的前两名，这就是最简单的 TOP-2 查询。没有线程的系统函数，那么我们就 可以自定义一个表聚合函数来实现这个功能。在累加器中应该能够保存当前最大的两个值，每 当来一条新数据就在 accumulate()方法中进行比较更新，最终在 emitValue()中调用两次 out.collect()将前两名数据输出。
