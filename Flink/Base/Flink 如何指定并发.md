---
layout: post
author: sjf0115
title: Flink 如何指定并发
date: 2018-01-04 14:07:01
tags:
  - Flink

categories: Flink
permalink: flink-parallel-execute
---

> Flink 1.11

本节介绍如何在 Flink 中配置程序并发执行。一个 Flink 程序由多个 Task (transformations/operators，data sources 以及 sinks)组成。一个 Task 可以分成多个并发实例来执行，每个并发实例只处理输入数据的一个子集。一个 Task 的并发实例的个数称为并发度(parallelism)。

如果你想使用[保存点](http://smartsi.club/flink-stream-deployment-savepoints.html)，也应该考虑设置最大并发度。从保存点恢复时，可以更改指定算子或整个程序的并发度，并且此配置指定了并发的上限。

### 1. 设置并发度

在 Flink 中一个 Task 的并发度可以指定不同级别。

#### 1.1 算子级别

单个算子，数据源，Sink 都可以通过调用 `setParallelism()` 方法来指定并发度。如下代码所示指定算子级别的并发度：

Java版本:
```java
DataStream<String> text = [...]
DataStream<Tuple2<String, Integer>> wordCounts = text
    .flatMap(new LineSplitter())
    .keyBy(0)
    .timeWindow(Time.seconds(5))
    .sum(1).setParallelism(5);

wordCounts.print();

env.execute("Word Count Example");
```
Scala版本:
```
val env = StreamExecutionEnvironment.getExecutionEnvironment

val text = [...]
val wordCounts = text
    .flatMap{ _.split(" ") map { (_, 1) } }
    .keyBy(0)
    .timeWindow(Time.seconds(5))
    .sum(1).setParallelism(5)
wordCounts.print()

env.execute("Word Count Example")
```

#### 1.2 执行环境级别

如[Flink 程序剖析](https://smartsi.blog.csdn.net/article/details/126088002) 博文所述，Flink 程序是在执行环境的上下文中执行的。执行环境为它执行的所有算子，数据源和 Sink 提供了默认的并发度。执行环境的并发度可以通过显式配置一个算子的并发度来覆盖。

执行环境的默认并发度可以通过调用 `setParallelism()` 方法来指定。要为执行的所有算子，数据源和 Sink 设置并发度为3，可以按如下代码所示设置执行环境的默认并发度：

Java版本:
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setParallelism(3);

DataStream<String> text = [...]
DataStream<Tuple2<String, Integer>> wordCounts = [...]
wordCounts.print();

env.execute("Word Count Example");
```
Scala版本:
```
val env = StreamExecutionEnvironment.getExecutionEnvironment
env.setParallelism(3)

val text = [...]
val wordCounts = text
    .flatMap{ _.split(" ") map { (_, 1) } }
    .keyBy(0)
    .timeWindow(Time.seconds(5))
    .sum(1)
wordCounts.print()

env.execute("Word Count Example")
```

#### 1.3 客户端级别

在向 Flink 提交作业时，可以在客户端设置并发度。客户端可以是 Java 或者 Scala 程序。Flink 的命令行接口(`CLI`)就是其中一种客户端。对于 CLI 客户端，可以使用 `-p` 参数指定并发度。如下代码所示指定10个并发：
```
./bin/flink run -p 10 ../examples/*WordCount-java*.jar
```
在 Java/Scala 程序中，并发度设置如下：

Java版本:
```java
try {
    PackagedProgram program = new PackagedProgram(file, args);
    InetSocketAddress jobManagerAddress = RemoteExecutor.getInetFromHostport("localhost:6123");
    Configuration config = new Configuration();

    Client client = new Client(jobManagerAddress, config, program.getUserCodeClassLoader());

    // set the parallelism to 10 here
    client.run(program, 10, true);

} catch (ProgramInvocationException e) {
    e.printStackTrace();
}
```

Scala版本:
```
try {
    PackagedProgram program = new PackagedProgram(file, args)
    InetSocketAddress jobManagerAddress = RemoteExecutor.getInetFromHostport("localhost:6123")
    Configuration config = new Configuration()

    Client client = new Client(jobManagerAddress, new Configuration(), program.getUserCodeClassLoader())

    // set the parallelism to 10 here
    client.run(program, 10, true)

} catch {
    case e: Exception => e.printStackTrace
}
```

#### 1.4 系统级别

可以通过在 `./conf/flink-conf.yaml` 中设置 `parallelism.default` 属性来为所有执行环境定义全系统默认并发度。详细信息请参阅[配置文档](https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/config.html)。

### 2. 设置最大并发度

最大并发度可以在可以设置并发度的地方设置(客户端级别和系统级别除外)。你可以调用 `setMaxParallelism()` 方法来设置最大并发度。最大并发度的默认设置大致为：算子并发度 +（算子并发度 / 2），下限为 127，上限为 32768。

将最大并发度设置为一个非常大的数可能会对性能造成不利影响，这是因为某些状态后端必须保持内部数据结构与 KeyGroup 的数量成比例（这也是可伸缩状态的内部实现机制）。

推荐订阅：
![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-jk.jpeg?raw=true)

原文:[Parallel Execution](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/parallel.html)
