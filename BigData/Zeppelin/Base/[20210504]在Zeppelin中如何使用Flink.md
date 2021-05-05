---
layout: post
author: smartsi
title: 在Zeppelin中如何使用Flink
date: 2020-10-18 16:43:01
tags:
  - Zeppelin
  - Flink

categories: Zeppelin
permalink: how-to-use-flink-in-zeppelin
---

在 Zeppelin 0.9 中，我们在 Zeppelin 中重构 Flink 解释器以支持最新版本的 Flink。目前仅支持 Flink 1.10+ 版本，不支持旧版本的 Flink。Zeppelin 中的 Flink 解释器组支持 Apache Flink，该解释器组由以下五个解释器组成。

| 名称 | Class | 描述 |
| :------------- | :------------- | :------------- |
| %flink | FlinkInterpreter	| 创建 ExecutionEnvironment / StreamExecutionEnvironment / BatchTableEnvironment / StreamTableEnvironment并提供Scala环境 |
| %flink.pyflink | PyFlinkInterpreter	| 提供 Python 环境 |
| %flink.ipyflink	| IPyFlinkInterpreter	| 提供 ipython 环境 |
| %flink.ssql	| FlinkStreamSqlInterpreter	| 提供 Stream SQL 环境 |
| %flink.bsql	| FlinkBatchSqlInterpreter | 提供 Batch SQL 环境 |

> 目前 Zeppelin 最新版本为 0.9

下载适用于 scala 2.11 的Flink 1.10（Zeppelin 仅支持 scala-2.11，尚不支持scala-2.12）






















...
