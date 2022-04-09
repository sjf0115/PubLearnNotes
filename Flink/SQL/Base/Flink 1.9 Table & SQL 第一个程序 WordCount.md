---
layout: post
author: sjf0115
title: Flink 1.9 Table & SQL 第一个程序 WordCount
date: 2021-08-16 22:34:01
tags:
  - Flink

categories: Flink
permalink: flink-1.9-table-sql-word-count
---

> Flink 版本：1.9.3

> 在 Flink 1.9 版本，Table API 和 SQL 功能尚不完整，正在积极开发中。

## 1. 依赖

### 1.1 Planner

从 Flink 1.9 开始，Flink 提供了两种不同的 Planner 实现来执行 Table & SQL API 程序：
- Blink Planner：Flink 1.9+
- Old Planner：Flink 1.9 之前

Planner 负责将关系运算符转换为可执行的、优化的 Flink 作业。两个 Planner 都带有不同的优化规则和运行时类。它们在支持的功能集上会有所不同。在生产中，我们还是推荐使用在 Flink 1.9 版本之前就存在的 Old Planner。

### 1.2 依赖项

根据你使用的编程语言，需要将 Java 或者 Scala API 添加到项目中，以便能使用 Table API 和 SQL 来定义作业流：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-api-java-bridge_2.11</artifactId>
  <version>1.9.3</version>
  <scope>provided</scope>
</dependency>
```
> 在这我们使用 Java 语言。

此外，如果你想在 IDE 中本地运行 Table API 或者 SQL 程序，那么必须添加如下依赖：
```xml
<!-- 推荐使用老的 Planner -->
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner_2.11</artifactId>
  <version>1.9.3</version>
  <scope>provided</scope>
</dependency>
<!-- 不建议使用新的 Blink Planner -->
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner-blink_2.11</artifactId>
  <version>1.9.3</version>
  <scope>provided</scope>
</dependency>
```
在内部实现上，Table 生态系统的一部分是基于 Scala 实现的。因此，需要确保为批处理和流式应用程序添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-streaming-scala_2.11</artifactId>
  <version>1.9.3</version>
  <scope>provided</scope>
</dependency>
```
如果要实现与 Kafka 交互的自定义格式或者实现自定义函数，则需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-common</artifactId>
  <version>1.9.3</version>
  <scope>provided</scope>
</dependency>
```

## 2. WordCount 示例

下面通过几个简单的 WordCount 的例子来体验一下 Flink Table & SQL 的代码是如何编写的。我们会分别从批处理和流处理两个场景下介绍如何开发一个简单的 WordCount 例子，在每种场景下我们又可以分别使用 Table API 和 SQL 的方式实现。

### 2.1 Batch

#### 2.1.1 Table 版 WordCount

第一步创建执行环境：
```java
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
BatchTableEnvironment tEnv = BatchTableEnvironment.create(env);
```
第二步读取数据创建 DataSet：
```java
DataSet<WordCount> input = env.fromElements(
    new WordCount("Hello", 1L),
    new WordCount("Ciao", 1L),
    new WordCount("Hello", 1L)
);
```
第三步将输入数据 DataSet 转换为 Table：
```java
Table table = tEnv.fromDataSet(input);
```
第四步执行查询：
```java
Table resultTable = table
    .groupBy("word")
    .select("word, frequency.sum as frequency");
```
第五步查询结果 Table 转换为 DataSet：
```java
DataSet<WordCount> result = tEnv.toDataSet(resultTable, WordCount.class);
```
最后一步输出：
```java
result.print();
```

完整代码如下：
```java
// 创建执行环境
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
BatchTableEnvironment tEnv = BatchTableEnvironment.create(env);

// 读取数据作为输入
DataSet<WordCount> input = env.fromElements(
        new WordCount("Hello", 1L),
        new WordCount("Ciao", 1L),
        new WordCount("Hello", 1L));

// DataSet 转换为 Table
Table table = tEnv.fromDataSet(input);

// 执行查询
Table resultTable = table
        .groupBy("word")
        .select("word, frequency.sum as frequency");

// Table 转换为 DataSet
DataSet<WordCount> result = tEnv.toDataSet(resultTable, WordCount.class);

// 输出
result.print();
```

#### 2.1.2 SQL 版 WordCount

前两步跟 Table 版一样，第三步是将 DataSet 注册为一个 Table 以便在 SQL 中直接引用，如下所示我们将 DataSet 注册为名为 WordCount 的 Table，同时声明了两个字段 word 和 frequency：
```java
tEnv.registerDataSet("WordCount", input, "word, frequency");
```
第四步执行 SQL 查询，查询结果作为一个 Table 返回：
```java
Table table = tEnv.sqlQuery(
    "SELECT word, SUM(frequency) as frequency FROM WordCount GROUP BY word");
```
最后两步跟 Table 版一样不在赘述。

完整代码如下：
```java
// 执行环境
ExecutionEnvironment env = ExecutionEnvironment.getExecutionEnvironment();
BatchTableEnvironment tEnv = BatchTableEnvironment.create(env);

// 读取数据作为输入
DataSet<WordCount> input = env.fromElements(
        new WordCount("Hello", 1),
        new WordCount("Ciao", 1),
        new WordCount("Hello", 1));

// 注册 Table
tEnv.registerDataSet("WordCount", input, "word, frequency");

// 执行 SQL 查询
Table table = tEnv.sqlQuery(
        "SELECT word, SUM(frequency) as frequency FROM WordCount GROUP BY word");

// Table 转换为 DataSet
DataSet<WordCount> result = tEnv.toDataSet(table, WordCount.class);

// 输出
result.print();
```

### 2.2 Streaming

#### 2.2.1 Table 版 WordCount

第一步创建流处理的执行环境，流处理模式与批处理模型的执行环境不同：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 默认使用 OldPlanner
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);
```
第二步读取数据创建 DataStream：
```java
DataStream<WordCount> input = env.fromElements(
        new WordCount("Hello", 1L),
        new WordCount("Ciao", 1L),
        new WordCount("Hello", 1L));
```
第三步将输入数据 DataStream 转换为 Table：
```java
Table table = tEnv.fromDataStream(input);
```
第四步执行查询：
```java
Table resultTable = table
      .groupBy("word")
      .select("word, frequency.sum as frequency");
```
第五步查询结果 Table 转换为 DataStream 并输出：
```java
DataStream<Tuple2<Boolean, WordCount>> result = tEnv.toRetractStream(resultTable, WordCount.class);
result.print();
```
最后一步执行：
```java
env.execute();
```

完整代码如下：
```java
// 执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 默认使用 OldPlanner
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);

// 读取数据创建 DataStream
DataStream<WordCount> input = env.fromElements(
       new WordCount("Hello", 1L),
       new WordCount("Ciao", 1L),
       new WordCount("Hello", 1L));

// DataStream 转 Table
Table table = tEnv.fromDataStream(input);

// 执行查询
Table resultTable = table
       .groupBy("word")
       .select("word, frequency.sum as frequency");

// Table 转 DataStream
DataStream<Tuple2<Boolean, WordCount>> result = tEnv.toRetractStream(resultTable, WordCount.class);
result.print();

// 执行
env.execute();
```

#### 2.2.2 SQL 版 WordCount

前两步跟 Table 版一样，第三步是将 DataStream 注册为一个 Table 以便在 SQL 中直接引用，如下所示我们将 DataSet 注册为名为 WordCount 的 Table，同时声明了两个字段 word 和 frequency：
```java
tEnv.registerDataStream("WordCount", input, "word, frequency");
```
第四步执行 SQL 查询，查询结果作为一个 Table 返回：
```java
Table table = tEnv.sqlQuery(
    "SELECT word, SUM(frequency) as frequency FROM WordCount GROUP BY word");
```
最后两步跟 Table 版一样不在赘述。

完整代码如下：
```java
// 执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 默认 OldPlanner
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);

// 读取数据创建 DataStream
DataStream<WordCount> input = env.fromElements(
        new WordCount("Hello", 1L),
        new WordCount("Ciao", 1L),
        new WordCount("Hello", 1L));

// 注册 Table
tEnv.registerDataStream("WordCount", input, "word, frequency");

// 执行 SQL 查询
Table table = tEnv.sqlQuery(
        "SELECT word, SUM(frequency) as frequency FROM WordCount GROUP BY word");

// Table 转换为 DataSet
DataStream<Tuple2<Boolean, WordCount>> result = tEnv.toRetractStream(table, WordCount.class);
result.print();

// 执行
env.execute();
```

> 本文对应的 wordCount 案例在 [github](https://github.com/sjf0115/data-example/tree/master/flink-example-1.9/src/main/java/com/flink/example/table/base) 中
