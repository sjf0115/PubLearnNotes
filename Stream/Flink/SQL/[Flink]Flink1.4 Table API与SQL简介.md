---
layout: post
author: sjf0115
title: Flink1.4 Table与SQL简介
date: 2018-03-12 11:29:01
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-table-and-sql
---

`Apache Flink` 具有两个相关联的API - `Table API` 和 `SQL` - 用于统一处理流和批处理。`Table API` 是一种集成 `Scala` 和 `Java` 语言的查询API，它允许以非常直观的方式组合来自相关算子的查询，例如 `selection`, `filter`, 以及 `join`。`Flink` 的 `SQL` 基于实现 `SQL` 标准的 `Apache Calcite` 实现的。无论输入是批量输入（`DataSet`）还是流输入（`DataStream`），在任一接口中指定的查询都具有相同的语义并指定相同的结果。

`Table API` 和 `SQL` 接口与 `Flink` 的 `DataStream` 和 `DataSet API` 紧密结合。You can easily switch between all APIs and libraries which build upon the APIs。例如，你可以使用CEP库从 `DataStream` 中提取模式，然后使用 `Table API` 分析模式，或者可以在处理数据上运行 `Gelly` 图算法之前使用 `SQL` 查询进行扫描，过滤和聚合批处理表。

请注意，Table API 和 SQL 尚未完成并且正在积极开发。并非所有操作都支持 `[Table API，SQL]` 和 `[stream, batch]` 输入的每种组合。

### 安装

Table API 和 SQL 捆绑在 `flink-table Maven` 构件中。必须将以下依赖项添加到你的项目才能使用 Table API 和 SQL：
```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table_2.11</artifactId>
  <version>1.4.1</version>
</dependency>
```

另外，你需要为 Flink 的 Scala 批处理或流式 API 添加依赖项。对于批量查询，需要添加：
```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-scala_2.11</artifactId>
  <version>1.4.1</version>
</dependency>
```
对于流式查询，需要添加：
```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-streaming-scala_2.11</artifactId>
  <version>1.4.1</version>
</dependency>
```
















































原文： https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/table/
