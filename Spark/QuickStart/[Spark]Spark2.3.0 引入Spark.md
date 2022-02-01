---
layout: post
author: sjf0115
title: Spark2.3.0 引入Spark
date: 2018-03-12 15:03:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-linking-with-spark
---

### 1. Java版

Spark 2.3.0 支持用于简洁编写函数的 lambda 表达式，你也可以使用 org.apache.spark.api.java.function 包中的类。

请注意，在 Spark 2.2.0 中删除了对 Java 7 的支持。

要在 Java 中编写 Spark 应用程序，需要在 Spark 上添加依赖项。Spark可通过 Maven 仓库获得：
```
groupId = org.apache.spark
artifactId = spark-core_2.11
version = 2.3.0
```

另外，如果希望访问 HDFS 集群，需要根据你的 HDFS 版本添加 hadoop-client 的依赖：
```
groupId = org.apache.hadoop
artifactId = hadoop-client
version = <your-hdfs-version>
```
最后，你需要将一些 Spark 类导入到程序中。 添加以下行：
```
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.SparkConf;
```

### 2. Scala版

默认情况下，Spark 2.3.0 在 Scala 2.11 上构建并分布式运行。（Spark 可以与其他版本的 Scala 一起构建。）要在 Scala 中编写应用程序，需要使用兼容的 Scala 版本（例如2.11.X）。

要编写 Spark 应用程序，需要在 Spark 上添加依赖项。Spark 可通过 Maven 仓库获得：
```
groupId = org.apache.spark
artifactId = spark-core_2.11
version = 2.3.0
```

另外，如果希望访问 HDFS 集群，则需要根据你的 HDFS 版本添加 hadoop-client 的依赖：
```
groupId = org.apache.hadoop
artifactId = hadoop-client
version = <your-hdfs-version>
```
最后，需要将一些 Spark 类导入到程序中。 添加以下行：
```
import org.apache.spark.SparkContext
import org.apache.spark.SparkConf
```

> 备注

> 在 Spark 1.3.0 之前，需要明确导入 org.apache.spark.SparkContext._ 以启用基本的隐式转换。

> Spark版本: 2.3.0

原文：http://spark.apache.org/docs/2.3.0/rdd-programming-guide.html#linking-with-spark
