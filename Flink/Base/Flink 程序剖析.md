---
layout: post
author: sjf0115
title: Flink 程序剖析
date: 2018-01-04 09:54:01
tags:
  - Flink
  - Flink 基础

categories: Flink
permalink: flink-anatomy-of-a-flink-program
---

Flink 程序程序看起来像转换数据集合的普通程序。每个程序都由相同的基本部分组成：
- 获得一个执行环境
- 加载/创建初始数据
- 指定在这些数据上的转换操作
- 指定计算结果存放位置
- 触发程序执行

现在我们将对每一步进行一个简要的概述。请注意，`Java DataSet API` 的所有核心类都可以在 `org.apache.flink.api.java` 包中找到，而 `Java DataStream API` 的类可以在 `org.apache.flink.streaming.api` 中找到。`Scala DataSet API` 的所有核心类都可以在 `org.apache.flink.api.scala` 包中找到，而 `Scala DataStream API` 的类可以在 `org.apache.flink.streaming.api.scala` 中找到。

`StreamExecutionEnvironment` 是所有 `Flink` 程序的基础。你可以使用 `StreamExecutionEnvironment` 上的如下静态方法获取：
Java版本:
```java
getExecutionEnvironment()
createLocalEnvironment()
createRemoteEnvironment(String host, int port, String... jarFiles)
```

Scala版本:
```
getExecutionEnvironment()
createLocalEnvironment()
createRemoteEnvironment(host: String, port: Int, jarFiles: String*)
```

通常情况下，我们只需要使用 `getExecutionEnvironment()` 即可，因为这会根据上下文做正确的选择：如果你在 `IDE` 内执行程序或作为常规的 `Java` 程序，将创建一个本地环境，在你的本地机器上执行你的程序。如果使用程序创建 `JAR` 文件并通过命令行调用它，那么 `Flink` 集群管理器将执行你的 `main` 方法，并且 `getExecutionEnvironment()` 返回一个用于在集群上执行你程序的执行环境。

对于指定数据源，执行环境有多种方法可以从文件中读取数据：可以逐行读取，以 CSV 格式文件读取或使用完全自定义的数据输入格式。只要将文本文件作为一系列行读取，就可以使用：

Java版本:
```Java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
DataStream<String> text = env.readTextFile("file:///path/to/file");
```

Scala版本:
```
val env = StreamExecutionEnvironment.getExecutionEnvironment()
val text: DataStream[String] = env.readTextFile("file:///path/to/file")
```

这将为你提供一个 `DataStream`，然后就可以应用转换函数来创建新的派生 `DataStream`。通过调用 `DataStream` 上的转换函数来应用转换操作。例如，一个 `map` 转换函数看起来像这样：

Java版本:
```java
DataStream<String> input = ...;
DataStream<Integer> parsed = input.map(new MapFunction<String, Integer>() {
    @Override
    public Integer map(String value) {
        return Integer.parseInt(value);
    }
});
```

Scala版本:
```
val input: DataSet[String] = ...
val mapped = input.map { x => x.toInt }
```
这将通过将原始集合中的每个 `String` 转换为 `Integer` 来创建一个新的 `DataStream`。一旦获得了包含最终结果的 `DataStream`，就可以通过创建接收器(`sink`)将其写入外部系统中。下面是创建接收器的一些示例方法：

Java版本:
```java
writeAsText(String path)
print()
```

Scala版本:
```
writeAsText(path: String)
print()
```

一旦你指定的完整程序需要触发程序执行，可以通过调用 `StreamExecutionEnvironment` 的 `execute()` 方法来触发程序的执行。根据执行环境的类型，执行将在你的本地机器上触发，或提交程序在集群上执行。`execute()` 方法返回一个 `JobExecutionResult`，它包含执行时间和累加器结果。
