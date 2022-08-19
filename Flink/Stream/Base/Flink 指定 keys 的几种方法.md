---
layout: post
author: sjf0115
title: Flink 指定 keys 的几种方法
date: 2018-01-04 11:07:01
tags:
  - Flink

categories: Flink
permalink: flink-how-to-specifying-keys
---

一些转换(例如，`join`，`coGroup`，`keyBy`，`groupBy`)可以在一组元素上定义一个 key，其他转换(`Reduce`，`GroupReduce`，`Aggregate`，`Windows`)就可以在使用这些函数之前根据指定的 key 对数据进行分组。

一个 DataSet 进行如下分组:
```java
DataSet<...> input = // [...]
DataSet<...> reduced = input
.groupBy(/*define key here*/)
.reduceGroup(/*do something*/);
```
DataStream 也可以指定一个 key:
```java
DataStream<...> input = // [...]
DataStream<...> windowed = input
.keyBy(/*define key here*/)
.window(/*window specification*/);
```

> 备注: 在下面的讨论中，我们使用 DataStream API 和 keyBy 进行演示。如果想在 DataSet API 上使用，你只需要对应替换为 DataSet 和 groupBy 即可。

下面介绍几种 Flink 指定 Key 的几种方法。

### 1. 使用字段索引指定 Key

最简单的情况就是使用 Tuple 元组的一个或多个字段的索引位置进行 KeyBy。如下所示根据元组的第一个字段(整数类型)进行 KeyBy：
```java
DataStream<Tuple2<String, Integer>> wordsCount = stream.flatMap(new FlatMapFunction<String, Tuple2<String, Integer>>() {
    @Override
    public void flatMap(String value, Collector out) {
        for (String word : value.split("\\s")) {
            out.collect(Tuple2.of(word, 1));
        }
    }
});

KeyedStream<Tuple2<String, Integer>, Tuple> keyedStream1 = wordsCount.keyBy(0);
keyedStream1.sum(1).print("KeyedStream1");
```

上面只指定了一个索引位置，我们还可以指定多个索引位置实现在多个 Key 上进行 KeyBy，如下所示使用元组的第一个和第二个字段:
```java
KeyedStream<Tuple2<String, Integer>, Tuple> keyedStream2 = wordsCount.keyBy(0, 1);
keyedStream2.sum(1).print("KeyedStream2");
```

如果你有一个包含嵌套元组的 DataStream，例如：
```java
DataStream<Tuple3<Tuple2<Integer, Float>,String,Long>> ds;
KeyedStream<Tuple3<Tuple2<Integer, Float>, String, Long>, Tuple> keyedStream = ds.keyBy(0);
```
如果指定 keyBy(0)，则使用整个 Tuple2 作为分组 Key，即以 Integer 和 Float 的两个字段为 key。如果要使用嵌套中 Tuple2 的某个字段，则必须使用下面介绍的字段表达式指定 key。

> 目前 2.13.6 版本已经标注为 `@Deprecated`，推荐使用第三种方式 KeySelector

### 2. 使用字段表达式指定 Key

除了使用基于索引的方式，你还可以使用基于字符串字段表达式的方式来引用字段。字段表达式的方式可以非常容易地选择(嵌套)复合类型(如 Tuple 和 POJO 类型)中的字段。如下所示，通过元组第一个字段的名称 f0 来指定要分组的 Key：
```java
KeyedStream<Tuple2<String, Integer>, Tuple> keyedStream3 = wordsCount.keyBy("f0");
keyedStream3.sum(1).print("KeyedStream3");
```
除此之外，我们也可以通过的 POJO 的字段名称来指定 Key。如下所示我们有一个`WordCount` POJO 类，它有两个字段 `word` 和 `frequency`：
```Java
public class WordCount {
    // 单词
    private String word;
    // 频次
    private long frequency;
    ...
}
```
如果想通过 word 字段分组，我们只需将 word 传递给 keyBy() 函数即可，如下所示：
```java
DataStream<WordCount> wordsCount2 = stream.flatMap(new FlatMapFunction<String, WordCount>() {
    @Override
    public void flatMap(String value, Collector out) {
        for (String word : value.split("\\s")) {
            out.collect(new WordCount(word, 1L));
        }
    }
});
KeyedStream<WordCount, Tuple> keyedStream4 = wordsCount2.keyBy("word");
keyedStream4.sum("frequency").print("KeyedStream4");
```

字段表达式语法:
- 按其字段名称选择 POJO 字段。例如 word 是指向 POJO 类的 word 字段。
- 通过字段名称或 0 到 offset 的数值字段索引来选择元组字段。例如，f0 和 f5 分别指向元组类型的第 1 和第 6 个字段。
- 可以在 POJO 和元组中选择嵌套字段。例如，`user.zip` 是指 POJO 类 user 字段中的 zip 字段。支持 POJO 和 Tuples 的任意嵌套和组合，如 `f1.user.zip` 或 `user.f3.1.zip`。
- 你可以使用 `*` 通配符表达式选择所有类型。这也适用于不是元组或 POJO 类型的类型。

下面看一些嵌套的简单示例:
- count 名称对应 WordCount 类中的 count 字段。
- comple 名称递归地选择复合字段 POJO 类型 ComplexNestedClass 的所有字段。
- complex.word.f2 名称选择嵌套字段 Tuple3 的最后一个字段。
- complex.hadoopCitizen 名称选择 Hadoop IntWritable 类型。

```Java
public static class WordCount {
  public ComplexNestedClass complex; //nested POJO
  private int count;
  public int getCount() {
    return count;
  }
  public void setCount(int c) {
    this.count = c;
  }
}
public static class ComplexNestedClass {
  public Integer someNumber;
  public float someFloat;
  public Tuple3<Long, Long, String> word;
  public IntWritable hadoopCitizen;
}
```

> 目前 2.13.6 版本已经标注为 `@Deprecated`，推荐使用第三种方式 KeySelector

### 3. 使用 KeySelector 函数指定 Key

现在定义 Key 推荐使用的一种方法是使用 KeySelector 函数。KeySelector 函数将单个元素作为输入，并返回要指定的 Key。Key 可以是任何类型的。以下示例展示了如何使用 KeySelector：
```java
DataStream<Tuple2<String, Integer>> wordsCount = stream.flatMap(new FlatMapFunction<String, Tuple2<String, Integer>>() {
    @Override
    public void flatMap(String value, Collector out) {
        for (String word : value.split("\\s")) {
            out.collect(Tuple2.of(word, 1));
        }
    }
});

KeyedStream<Tuple2<String, Integer>, String> keyedStream5 = wordsCount.keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
    @Override
    public String getKey(Tuple2<String, Integer> tuple2) throws Exception {
        return tuple2.f0;
    }
});
keyedStream5.sum(1).print("KeyedStream5");
```
