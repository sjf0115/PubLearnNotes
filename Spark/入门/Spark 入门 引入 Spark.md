---
layout: post
author: sjf0115
title: Spark 入门 引入 Spark
date: 2018-03-12 15:03:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-linking-with-spark
---

> Spark版本: 3.1.3

### 1. Java版

Spark 3.1.3 支持用于简洁编写函数的 [Lambda](https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html) 表达式，也可以使用 [org.apache.spark.api.java.function](https://spark.apache.org/docs/3.1.3/api/java/index.html?org/apache/spark/api/java/function/package-summary.html) 包中的类。

> 需要注意的是在 Spark 2.2.0 中删除了对 Java 7 的支持。

要在 Java 中编写 Spark 应用程序，需要在 Spark 上添加如下依赖项：
```xml
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-core_2.12</artifactId>
    <version>3.1.3</version>
    <scope>provided</scope>
</dependency>
```

另外，如果希望访问 HDFS 集群，需要根据你的 HDFS 版本添加 hadoop-client 的依赖：
```xml
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-client</artifactId>
    <version>${hadoop.version}</version>
</dependency>
```
最后，你需要将一些 Spark 类导入到程序中。 添加以下行：
```java
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.SparkConf;
```

### 2. Scala版

默认情况下，Spark 3.1.3 在 Scala 2.12 上构建并分布式运行。（Spark 可以与其他版本的 Scala 一起构建。）要在 Scala 中编写应用程序，需要使用兼容的 Scala 版本（例如2.12.X）。

要编写 Spark 应用程序，需要在 Spark 上添加如下依赖项：
```xml
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-core_2.12</artifactId>
    <version>3.1.3</version>
    <scope>provided</scope>
</dependency>
```

另外，如果希望访问 HDFS 集群，则需要根据你的 HDFS 版本添加 hadoop-client 的依赖：
```xml
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-client</artifactId>
    <version>${hadoop.version}</version>
</dependency>
```
最后，需要将一些 Spark 类导入到程序中。 添加以下行：
```scala
import org.apache.spark.SparkContext
import org.apache.spark.SparkConf
```

> 在 Spark 1.3.0 之前，需要明确导入 org.apache.spark.SparkContext._ 以启用基本的隐式转换。

原文：[Linking with Spark](https://spark.apache.org/docs/3.1.3/rdd-programming-guide.html#linking-with-spark)
