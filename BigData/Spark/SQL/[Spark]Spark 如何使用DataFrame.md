---
layout: post
author: sjf0115
title: Spark 如何使用DataFrame
date: 2018-06-03 15:31:01
tags:
  - Spark
  - Spark SQL

categories: Spark
permalink: spark-sql-how-to-use-dataframe-in-spark
---


当我们首次开源 Apache Spark 时，我们的目标是为通用编程语言（Java，Python，Scala）中的分布式数据处理提供一个简单的API。 Spark 通过在分布式数据集合（RDD）上进行函数转换(functional transformations)实现分布式数据处理。这是一个令人难以置信的强大的API：过去需要数千行代码才能表达的任务现在减少到几十个。

随着 Spark 不断的发展壮大，我们希望除大数据工程师之外的更多用户能够利用分布式处理的能力。新的 DataFrames API 就是为了这个目标而创建的。这个API受 R 和 Python（Pandas） 中的数据框架(data frames)的启发，但是从头开始设计以支持现代大数据和数据科学应用程序的需求。作为现有 RDD API 的扩展，DataFrame 具有以下特性：
- 能够从单台笔记本电脑上的千字节数据扩展到大型群集上的数PB数据
- 支持各种数据格式和存储系统
- 通过 Spark SQL Catalyst 优化器实现代码优化
- 通过 Spark 无缝集成所有大数据工具和基础架构
- 为 Python，Java，Scala 和 R 提供API

对于熟悉其他编程语言数据框架的新用户，此API应该让他们感到很熟悉。对于现有的 Spark 用户，此扩展 API 将使 Spark 更易于编程，同时通过智能优化和代码生成来提高性能。

### 1. 什么是DataFrames

在 Spark中，DataFrame 是分布式数据集合，具有命名列。在概念上等同于关系数据库中的表或 R/Python 中的 data frame，但经过了优化器的优化。DataFrame 可以从各种来源构建，例如：结构化数据文件，Hive 表，外部数据库或现有的 RDD。

以下示例显示如何在 Java 中构建 DataFrame。Scala 和 Python 中提供了类似的API。
```java
// 创建DataFrame
Dataset<Row> dataFrame = sparkSession.read().json("src/main/resources/person.json");
```

### 2. 如何使用DataFrames

DataFrames 构建完成后，将为分布式数据操作提供特定于域的语言。以下是使用 DataFrame 处理大量用户的人口统计数据的示例：
```java

```























原文：https://databricks.com/blog/2015/02/17/introducing-dataframes-in-spark-for-large-scale-data-science.html
