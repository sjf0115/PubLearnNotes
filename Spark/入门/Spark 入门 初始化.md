---
layout: post
author: sjf0115
title: Spark 入门 初始化
date: 2018-03-12 16:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-initializing-spark
---

> Spark 版本: 3.1.3

### 1. 初始化

Spark 程序必须做的第一件事是创建一个 `JavaSparkContext` 对象(Scala和Python中是`SparkContext`对象)，这告诉了 Spark 如何访问集群。要创建 `SparkContext`，你首先需要构建一个包含有关应用程序信息的 `SparkConf` 对象。

Java版本：
```java
private static String appName = "JavaWordCountDemo";
private static String master = "local";

// 初始化Spark
private static SparkConf conf = new SparkConf().setAppName(appName).setMaster(master);
private static JavaSparkContext sc = new JavaSparkContext(conf);
```

Scala版本：
```scala
val conf = new SparkConf().setAppName(appName).setMaster(master)
new SparkContext(conf)
```
> 每个 JVM 只能有一个 SparkContext 处于活跃状态。在创建新的 SparkContext 之前，必须先调用 `stop()` 方法停止之前活跃的 SparkContext。

Python版本：
```python
conf = SparkConf().setAppName(appName).setMaster(master)
sc = SparkContext(conf=conf)
```

appName 参数是应用程序在集群UI上显示的名称。master 是 Spark，Mesos 或 YARN 集群的 URL，或以本地模式运行的特殊字符串 `local`。实际上，当在集群上运行时，你不需要在程序中写死 `master`，而是使用 `spark-submit` 启动应用程序并以参数传递进行接收。但是，对于本地测试和单元测试，你可以通过 `local` 来运行 Spark 进程。


### 2. 使用Shell

在 Spark shell 中，已经为你创建了一个专有的 `SparkContext`，可以通过变量 `sc` 访问。你自己创建的 `SparkContext` 将无法工作。可以用 `--master` 参数来设置 `SparkContext` 要连接的集群，用 `--jars` 来设置需要添加到 classpath 中的 JAR 包，如果有多个 JAR 包使用逗号分割符连接它们。你还可以通过 `--packages` 参数提供逗号分隔的 maven 坐标列表，将依赖关系（例如Spark Packages）添加到 shell 会话中。依赖项存在的任何可选存储库（例如Sonatype）可以传递给 `--repositories` 参数。例如：在一个拥有 4 核的环境上运行 bin/spark-shell，使用：

```
./bin/spark-shell --master local[4]
```
或者，还可以将 code.jar 添加到其 classpath 中，请使用：
```
 ./bin/spark-shell --master local[4] --jars code.jar
```
使用maven坐标来包含依赖项：
```
 ./bin/spark-shell --master local[4] --packages "org.example:example:0.1"
```
可以执行 `spark-shell --help` 获取完整的选项列表。`spark-shell` 调用的是更常用的[`spark-submit`脚本](http://blog.csdn.net/sunnyyoona/article/details/55271395)。


原文：http://spark.apache.org/docs/2.3.0/rdd-programming-guide.html#initializing-spark
