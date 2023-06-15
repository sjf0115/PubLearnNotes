---
layout: post
author: LittleMagic
title: 基于 Calcite 解析 Flink SQL 列级数据血缘
date: 2023-06-15 20:16:01
tags:
  - Flink

categories: Flink
permalink: calcite-flink-sql-column-lineage
---

## 1. 数据血缘

数据血缘（data lineage）是数据治理（data governance）的重要组成部分，也是元数据管理、数据质量管理的有力工具。通俗地讲，数据血缘就是数据在产生、加工、流转到最终消费过程中形成的有层次的、可溯源的联系。成熟的数据血缘系统可以帮助开发者快速定位问题，以及追踪数据的更改，确定上下游的影响等等。

在数据仓库的场景下，数据的载体是数据库中的表和列（字段），相应地，数据血缘根据粒度也可以分为较粗的表级血缘和较细的列（字段）级血缘。离线数仓的数据血缘提取已经有了成熟的方法，如利用 Hive 提供的 LineageLogger 与 Execution Hooks 机制。本文就来简要介绍一种在实时数仓中基于 Calcite 解析 Flink SQL 列级血缘的方法，在此之前，先用几句话聊聊 Calcite 的关系式元数据体系。

## 2. Calcite 关系式元数据

在 Calcite 内部，库表元数据由 Catalog 来处理，关系式元数据才会被冠以 `[Rel]Metadata` 的名称。关系式元数据与 RelNode 对应，以下是与其相关的 Calcite 组件：
- RelMetadataQuery：为关系式元数据提供统一的访问接口；
- RelMetadataProvider：为 RelMetadataQuery 各接口提供实现的中间层；
- MetadataFactory：生产并维护 RelMetadataProvider 的工厂；
- MetadataHandler：处理关系式元数据的具体实现逻辑，全部位于 `org.apache.calcite.rel.metadata` 包下，且类名均以 `RelMd` 作为前缀。

Calcite 内置了许多种默认的关系式元数据实现，并以接口的形式统一维护在 BuiltInMetadata 抽象类里，如下图所示，名称都比较直白（如RowCount就表示该RelNode查询结果的行数）。
