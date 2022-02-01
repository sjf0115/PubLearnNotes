---
layout: post
author: wy
title: Debezium 1.9.0.Alpha1 正式发布
date: 2022-02-01 14:33:21
tags:
  - Debezium

categories: Debezium
permalink: debezium-1-9-alpha1-released
---

我很高兴宣布 Debezium 1.9 系列的第一个版本 1.9.0.Alpha1 正式发布。这是新的一年来的第一个新版本！Debezium 1.9.0.Alpha1 版本包含大量修复和改进，最显着的是改进了指标以及提供对 Oracle ROWID 数据类型的支持。

## 1. 改进的指标

Debezium 的 Connector 提供了大量的监控指标。我们在 TotalNumberOfEventsSeen 指标基础之上进行了扩展，提供这些事件的细分类型。为了支持这一努力，添加了如下新指标：
- TotalNumberOfCreateEventsSeen
- TotalNumberOfUpdateEventsSeen
- TotalNumberOfDeleteEventsSeen

这些指标分别表示自 Connector 流式处理阶段开始以来发生的插入、更新和删除事件的数量。因此，你不仅可以继续获取事件总数，现在还可以按不同事件类型进行获取。

## 2. Oracle ROWID 数据类型支持

Oracle 用户可以使用 ROWID 数据类型的列来优化表示当前行与由 ROWID 列值标识的行之间的关系。从这个版本开始，使用 ROWID 数据类型的列可以被 Debezium 捕获并在变更事件中输出。

Oracle 有两种风格的行标识符列数据类型，ROWID 和 UROWID。虽然这些在某些情况下可以互换使用，但在变更数据捕获事件下它们是不同的。尽管我们添加了对 ROWID 的支持，但目前仍不支持对 UROWID 的支持。

## 3. 其他修复

此版本中有很多 Bug 修复和稳定性改进，如下可以值得关注：
- JSON 有效负载在启用时未扩展 ([DBZ-4457](https://issues.redhat.com/browse/DBZ-4457))
- R/O 增量快照可以在重启时阻塞 binlog 流 ([DBZ-4502](https://issues.redhat.com/browse/DBZ-4502))
- Infinispan 不适用于缓存名称中的下划线 ([DBZ-4526](https://issues.redhat.com/browse/DBZ-4526))
- 无法处理长度超过 Integer.MAX_VALUE 的列定义([DBZ-4583](https://issues.redhat.com/browse/DBZ-4583))
- Oracle Connector 找不到 SCN ([DBZ-4597](https://issues.redhat.com/browse/DBZ-4597))
- 将 Postgres JDBC 驱动程序升级到 42.3.1 版本 ([DBZ-4374](https://issues.redhat.com/browse/DBZ-4374))
- 将 SQL Server 驱动程序升级到 9.4 版本([DBZ-4463](https://issues.redhat.com/browse/DBZ-4463))

此版本总共修复了100 个问题。

## 4. 下一步

我们已经在邮件列表中开始了关于 Debezium 2.0 的公开讨论。您的反馈非常宝贵，请告诉我们您希望添加、修改或者改进的内容！与此同时，我们才刚刚开始！在接下来的几周内还会有另一个 1.9 预发布版本，我们保持每 3 周一版的节奏。随着我们继续获得社区反馈，您还可以期待在本季度发布 1.8 的 Bug 修复。

原文:[Debezium 1.9.0.Alpha1 Released](https://debezium.io/blog/2022/01/26/debezium-1-9-alpha1-released/)
