---
layout: post
author: wy
title: Debezium 1.9.0.Alpha2 正式发布
date: 2022-02-16 21:33:21
tags:
  - Debezium

categories: Debezium
permalink: debezium-1-9-alpha2-released
---

我很高兴宣布 Debezium 1.9 系列的第二个版本，1.9.0.Alpha2 正式发布。此版本包含了对 Oracle 21c 的支持、围绕 Redis for Debezium Server 的改进、配置 kafka.query.timeout.ms 参数以及围绕 DDL 解析器、构建基础架构等的许多 Bug 修复。整体来说，在此版本修复了 [51](https://issues.redhat.com/issues/?jql=project%20%3D%20DBZ%20AND%20fixVersion%20%3D%201.9.0.Alpha2%20ORDER%20BY%20issuetype%20DESC) 个问题。让我们一起看看其中的一些亮点。

## 1. 支持 Oracle 21c

Debezium Oracle Connector 在 Oracle 21c 最新版本 21.3.0.0 上完成测试，并且实现兼容。如果你使用 LogMiner 或 Xstreams 适配器，现在无需任何更改就可以使用 Oracle 的最新旗舰版本和流变更事件。如果你在 Oracle 12 或 Oracle 19 上执行数据库升级，你不需要修改 Connector 配置（已经兼容）。

## 2. 配置 kafka.query.timeout.ms 参数

当使用 Kafka Admin Client 并调用 API 时，默认超时时间为 3 秒。新的 kafka.query.timeout.ms 参数可以为 Kafka Admin Client 提供自定义超时时间，以避免在使用 TLS 和 SSL 加密以及网络延迟引起的非预期超时环境中可能出现超时问题。

感谢社区成员 Snigdhajyoti Ghosh 所做的出色工作。

## 3. Redis for Debezium Servers 的改进

我们在支持 Redis 的 Debezium Servers 中新增了三个参数：
- redis.retry.initial.delay.ms
- redis.retry.max.delay.ms
- batch.size

Redis 允许使用 maxmemory 配置参数指定最大内存上限；但是，如果未配置此参数，那么 Redis 会继续分配内存。如果所有内存都用完了，就会发生 OutOfMemory 异常。现在 Redis Sink 使用 redis.retry.initial.delay.ms 和 redis.retry.max.delay.ms 来配置初始和最大重试延迟时间，以更好地应对这个问题以及与连接相关的问题。如果你曾经或者现在正遇到此类异常，我们强烈建议你尝试这些新配置参数，以提高 Sink 的弹性和体验。

基于管道的事务可以大大增加 Redis 查询。为了利用基于管道的事务，可以指定 batch.size 配置参数，这可以允许 Redis 批量写入变更记录，而不是一个一个地写入。

## 4. 其他修复

如下是一些值得注意的 Bug 修复和升级：
- Oracle Logminer：在进行中事务切换'快照→流'会丢失数据库变更 [DBZ-4367](https://issues.redhat.com/browse/DBZ-4367)
- DDL 解析问题：ALTER TABLE … MODIFY PARTITION … [DBZ-4649](https://issues.redhat.com/browse/DBZ-4649)
- OracleSchemaMigrationIT 使用 Xstream 适配器出现失败 [DBZ-4703](https://issues.redhat.com/browse/DBZ-4703)
- 将 UI 从 webpack-dev-server v3 版本迁移到 v4 [DBZ-4642](https://issues.redhat.com/browse/DBZ-4642)
- 将 postgres 驱动程序升级到 42.3.2 版本 [DBZ-4658](https://issues.redhat.com/browse/DBZ-4658)
- Quarkus 升级到 2.7.0.Final [DBZ-4677](https://issues.redhat.com/browse/DBZ-4677)
- 指示 XStream 不支持 ROWID [DBZ-4702](https://issues.redhat.com/browse/DBZ-4702)
- 增量快照不支持列区分大小写 [DBZ-4584](https://issues.redhat.com/browse/DBZ-4584)
- 构建触发器问题 [DBZ-4672](https://issues.redhat.com/browse/DBZ-4672)
- 无法使用嵌套的对象数组扩展 JSON payload [DBZ-4704](https://issues.redhat.com/browse/DBZ-4704)

原文:[Debezium 1.9.0.Alpha2 Released](https://debezium.io/blog/2022/02/09/debezium-1-9-alpha2-released/)
