---
layout: post
author: smartsi
title: Flink SQL 自定义 Connector
date: 2021-08-18 08:30:21
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-custom-connector
---

> Flink 版本：1.13

动态表（Dynamic tables）是 Flink Table & SQL API 的核心概念，以统一的方式处理有界和无界数据。因为动态表只是一个逻辑概念，Flink 并不会拥有数据。相反，动态表的内容存储在外部系统（例如数据库、KV存储、消息队列）或文件中。动态 Source 和动态 Sink 分别用来从外部系统读取数据和向外部系统写入数据。在本文中 Source 和 Sink 以 Connector 术语表示。Flink 已经为 Kafka、Hive 以及不同的文件系统提供了内置的 Connector。有关内置 Connector 更多信息，请参阅官方文档 [Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/overview/) 部分。

本文的重点是介绍如何开发自定义的的 Connector。

> 动态表的详细介绍可以参阅博文 [Flink SQL 动态表的持续查询](https://mp.weixin.qq.com/s/CaNPCtEjxRRhm1T1lZJj1w)。

### 1. Connector 架构

在许多情况下，开发者不想从头开始创建一个新的 Connector，而是希望稍微修改现有的 Connector。有时候开发者还希望能创建专门的 Connector。本文对这两种用例都会有所帮助。下面会介绍表 Connector 的一般架构：

![](1)

> 实心箭头表示在转换过程中从一个阶段到另一个阶段，对象是如何转换为另一个对象的。

#### 1.1 Metadata

Table API 和 SQL 都是声明式 API。这包括表的声明。因此，执行 CREATE TABLE 语句会在目标 catalog 中更新元数据。对于大多数 catalog 的实现，对于此操作不会修改外部系统中的物理数据。指定 Connector 的依赖项不必出现在类路径中。WITH 子句中声明的选项既不会验证也不以其他方式解释。动态表的元数据（通过 DDL 创建或由 catalog 提供）由 CatalogTable 实例表示。必要时，表名将在内部解析为 CatalogTable。

#### 1.2 Planning

表程序在生成查询计划和优化时，需要将 CatalogTable 解析为 DynamicTableSource（用于在 SELECT 查询中读取）和 DynamicTableSink（用于在 INSERT INTO 语句中写入）。

DynamicTableSourceFactory 和 DynamicTableSinkFactory 提供指定 Connector 的逻辑，来将 CatalogTable 元数据转换为 DynamicTableSource 和 DynamicTableSink 实例。在大多数情况下，factory 的目的是验证选项（例如示例中的 'port' = '5022'）、配置编码/解码格式（如果需要）以及创建表 Connector 的参数化实例。

默认情况下，使用 Java 的服务提供者接口 (SPI) 来自动发现 DynamicTableSourceFactory 以及 DynamicTableSinkFactory 的实例。`connector` 选项（例如示例中的 'connector' = 'custom'）必须与 factory 的有效标识符相对应。

尽管在类命名中可能不明显，但 DynamicTableSource 和 DynamicTableSink 也可以被视为有状态的工厂，它们最终为读取/写入实际数据生成具体的运行时实现。

规划器使用源和接收器实例来执行特定于连接器的双向通信，直到找到最佳逻辑计划。根据可选声明的能力接口（例如 SupportsProjectionPushDown 或 SupportsOverwrite），规划器可能会对实例应用更改，从而改变生成的运行时实现。

#### 1.3 Runtime

一旦逻辑规划完成，planner 将从表 Connector 获取运行时实现。运行时逻辑在 Flink 的核心 Connector 接口中实现，例如 InputFormat 或 SourceFunction。这些接口按另一个抽象级别分组为 ScanRuntimeProvider、LookupRuntimeProvider 以及 SinkRuntimeProvider 的子类。例如，OutputFormatProvider（提供 org.apache.flink.api.common.io.OutputFormat）和 SinkFunctionProvider（提供 org.apache.flink.streaming.api.functions.sink.SinkFunction）都是 SinkRuntimeProvider 的具体实例。



mvn dependency:resolve -Dincludes=org.apache.flink:flink-table-api-java-bridge_2.12 -Dclassifier=sources


















参考：
- [User-defined Sources & Sinks](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/dev/table/sourcessinks/)
- [FLIP-95: New TableSource and TableSink interfaces](https://cwiki.apache.org/confluence/display/FLINK/FLIP-95%3A+New+TableSource+and+TableSink+interfaces)
