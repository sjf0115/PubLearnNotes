---
layout: post
author: smartsi
title: Flink DataStream Java Lambda 表达式的限制
date: 2021-10-07 16:35:01
tags:
  - Flink

categories: Flink
permalink: java-lambda-expressions-in-flink
---

Java 8 引入了一些新的语言特性，旨在实现更快、更清晰的编码。凭借最重要的特性 'Lambda 表达式'，打开了函数式编程的大门。Lambda 表达式允许以直接的方式实现和传递函数，而无需声明额外的（匿名）类。Flink 支持对 Java API 的所有算子使用 Lambda 表达式，但是当 Lambda 表达式使用 Java 泛型时，我们都必须显式声明类型信息。

下面通过两个例子来展示如何使用 Lambda 表达式并描述使用上的限制。

### 1. MapFunction与泛型

以下示例说明了如何实现一个简单的 map() 函数，该函数使用 Lambda 表达式对其输入进行平方，输出值为本身和平方的元组：
```java
env.fromElements(1, 2, 3)
  .map(i -> Tuple2.of(i, i*i))
  .print();
```
由于在 map 函数中使用了 Lambda 表达式，结果抛出如下异常信息：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/java-lambda-expressions-in-flink-1.png?raw=true)

从上面报错信息可以知道 Lambda 中由于使用了泛型导致类型擦除而抛异常。map() 函数返回值 Tuple2<Integer, Integer> 被擦除为 Tuple2 map(Integer value)。在许多情况下，当涉及 Java 泛型时，Lambda 方法无法为自动类型提取提供足够的信息。报错信息中也给出了解决方案：
- 使用一个(匿名)类来代替实现 'org.apache.flink.api.common.functions.MapFunction' 接口。
- 必须使用类型信息显式指定类型。

下面我们详细看一下具体的对应方案。

#### 1.1 匿名内部类方式

使用匿名内部类来代替实现 'org.apache.flink.api.common.functions.MapFunction' 接口：
```java
env.fromElements(1, 2, 3)
    .map(new MapFunction<Integer, Tuple2<Integer, Integer>>() {
        @Override
        public Tuple2<Integer, Integer> map(Integer i) throws Exception {
            return new Tuple2<Integer, Integer>(i, i * i);
        }
    })
    .print();
```
为什么采用匿名内部类就没有问题？因为匿名内部类会编译成相关的类字节码存储在 class 文件中，而 Lambda 表达式只是 Java 的语法糖并不会存在相关的类字节码，Lambda 表达式是在运行时调用 invokedynamic 指令，亦即在第一次执行其逻辑时才会确定。因此 Lambda 表达式比起匿名内部类，会丢失更多的类型信息。

#### 1.2 自定义类方式

使用自定义类来代替实现 'org.apache.flink.api.common.functions.MapFunction' 接口：
```java
public static class MyMapFunction implements MapFunction<Integer, Tuple2<Integer, Integer>> {
    @Override
    public Tuple2<Integer, Integer> map(Integer i) {
        return Tuple2.of(i, i*i);
    }
}

env.fromElements(1, 2, 3)
  .map(new MyMapFunction())
  .print();
```
#### 1.3 returns方式

使用 returns 语句显示的指明类型信息：
```java
env.fromElements(1, 2, 3)
    .map(i -> Tuple2.of(i, i*i))
    .returns(Types.TUPLE(Types.INT, Types.INT))
    .print();
```

### 2. FlatMap与泛型

在下面示例中我们在 flatMap() 函数中使用 Lambda 表达式将字符串拆成多行：
```java
env.fromElements("1,2,3", "4,5")
    .flatMap((String input, Collector<String> out) -> {
        String[] params = input.split(",");
        for(String value : params) {
            out.collect(value);
        }
    })
    .print();
```
由于 flatMap() 函数签名 void flatMap(IN value, Collector<OUT> out) 中有泛型 Collector<OUT>，所以在编译是进行泛型类型擦除，最终编译为 flatMap(IN value, Collector out)。这使得 Flink 无法自动推断输出类型的类型信息。所以在 flatMap() 函数中使用 Lambda 表达式会抛出类似如下的异常:

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/java-lambda-expressions-in-flink-2.png?raw=true)

跟 MapFunction 的报错信息基本一致，都是由于 Lambda 中使用泛型导致类型擦除。解决方案也类似：
- 使用一个(匿名)类来代替实现 'org.apache.flink.api.common.functions.FlatMapFunction' 接口。
- 必须使用类型信息显式指定类型。

下面我们详细看一下具体的对应方案。

#### 2.1 匿名内部类方式

使用匿名内部类来代替实现 'org.apache.flink.api.common.functions.FlatMapFunction' 接口：
```java
env.fromElements("1,2,3", "4,5")
    .flatMap(new FlatMapFunction<String, String>() {
        @Override
        public void flatMap(String input, Collector<String> out) throws Exception {
            String[] params = input.split(",");
            for(String value : params) {
                out.collect(value);
            }
        }
    })
    .print();
```

#### 2.2 自定义类方式

使用自定义类来代替实现 'org.apache.flink.api.common.functions.FlatMapFunction' 接口：
```java
public static class MyFlatMapFunction implements FlatMapFunction<String, String> {
    @Override
    public void flatMap(String input, Collector<String> out) throws Exception {
        String[] params = input.split(",");
        for(String value : params) {
            out.collect(value);
        }
    }
}

env.fromElements("1,2,3", "4,5")
  .flatMap(new MyFlatMapFunction())
  .print();
```

#### 2.3 returns方式

使用 returns 语句显示的指明类型信息：
```java
env.fromElements("1,2,3", "4,5")
  .flatMap((String input, Collector<String> out) -> {
      String[] params = input.split(",");
      for(String value : params) {
          out.collect(value);
      }
  })
  .returns(String.class)
  .print();
```

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- [Java Lambda Expressions ](https://ci.apache.org/projects/flink/flink-docs-release-1.14/docs/dev/datastream/java_lambdas/)
