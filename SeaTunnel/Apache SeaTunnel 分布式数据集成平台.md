---
layout: post
author: sjf0115
title: Apache SeaTunnel 分布式数据集成平台
date: 2022-03-25 11:33:01
tags:
  - SeaTunnel

categories: SeaTunnel
permalink: apache-seatunnel-introduction
---

> 当前版本：2.1.0

## 1. 简介

随着互联网流量爆发式增长，越来越多的公司业务需要支撑海量数据存储，对高并发、高可用、高可扩展性等特性提出了更高的要求，这促使各种类型的数据库快速发展，至今常见数据库已经达到 200 多个。与之相伴的便是，各种数据库之间的同步与转换需求激增，数据集成便成了大数据领域的一个亟需优秀解决方案的方向。当前市面上没有一个简单易用且支持每天数百亿条海量数据同步的开源软件，于是 SeaTunnel 应运而生。

SeaTunnel 是一个非常好用的、超高性能的、分布式数据集成平台，架构于 Apache Spark 和 Apache Flink 之上，实现海量数据的实时同步与转换。每天可以稳定高效的同步数百亿数据，目前已接近百家公司在生产上使用。

SeaTunnel 原名 Waterdrop，于 2017 年由乐视创建，并于同年在 GitHub 上开源，2021 年 10 月改名为 SeaTunnel。2021 年 12 月，SeaTunnel 正式通过世界顶级开源组织 Apache 软件基金会的投票决议，以全票通过的优秀表现正式成为 Apache 孵化器项目，成为 Apache 基金会中第一个诞生自中国的数据集成平台项目。

## 2. 目标

SeaTunnel 尽所能为您解决海量数据同步中可能遇到的问题：
- 使用 Spark、Flink 作为底层数据同步引擎使其具备分布式执行能力，提高数据同步的吞吐性能;
- 集成多种能力缩减 Spark、Flink 应用到生产环境的周期与复杂度;
- 利用可插拔的插件体系支持超过 100 种数据源;
- 引入管理与调度能力做到自动化的数据同步任务管理;
- 特定场景做端到端的优化提升数据同步的数据一致性;
- 开放插件化与 API 集成能力帮助企业实现快速定制与集成;

## 3. 使用场景

SeaTunnel 的使用场景广阔，包括如下场景：
- 海量数据同步
- 海量数据集成
- 海量数据 ETL
- 海量数据聚合
- 多源数据处理

## 4. 特性

数据集成平台要围绕解决海量数据同步这一目标进行，核心理念是保持海量数据能快速同步的同时还能保持数据的一致性，具体到 Apache SeaTunnel 来说，Apache SeaTunnel 具有以下核心特性:
- 高扩展性：模块化和插件化，支持热插拔, 带来更好的扩展性;
- 插件丰富：内置丰富插件，支持各种数据产品的传输和集成;
- 成熟稳定：经历大规模生产环境使用和海量数据的检验，具有高性能、海量数据的处理能力;
- 简单易用：特有的架构设计，简单易用，灵活配置，无需开发;
- SQL支持：支持通过 SQL 进行数据处理和聚合;
- 流式支持：支持实时流式处理;

## 5. 架构与工作流程

Apache SeaTunnel 发展上有 2 个大版本，1.x 版本基于 Spark 构建，现在在打造的 2.x 既支持 Spark 又支持 Flink。在架构设计上，Apache SeaTunnel 参考了 Presto 的 SPI 化思想，有很好的插件化体系设计。

在技术选型时，Apache SeaTunnel 主要考虑技术成熟度和社区活跃性。Spark、Flink 都是非常优秀并且流行的大数据计算框架，所以 1.x 版本选了 Spark，2.x 版本将架构设计的更具扩展性，用户可以选择 Spark 或 Flink 集群来做 Apache SeaTunnel 的计算层，当然架构扩展性的考虑也是为以后支持更多引擎准备，说不定已经有某个更先进的计算引擎在路上，也说不定 Apache SeaTunnel 社区自己会实现一个为数据同步量身打造的引擎。

如下图是 Apache SeaTunnel 的整个工作流程，数据处理流水线由 Source、Sink 以及多个 Transform 构成，以满足多种数据处理需求:
```
Source[Data Source Input] -> Transform[Data Processing] -> Sink[Result Output]
```

![](https://github.com/sjf0115/ImageBucket/blob/main/SeaTunnel/apache-seatunnel-introduction-1.png?raw=true)

如果用户习惯了 SQL，也可以直接使用 SQL 构建数据处理管道，更加简单高效。目前，SeaTunnel 支持的 Transform 列表也在扩展中。你也可以开发自己的数据处理插件。

## 6. SeaTunnel 支持的插件

Source 插件：
- File
- Hdfs
- Kafka
- Druid
- InfluxDB
- S3
- Socket
- 自研输入插件

Transform 插件：
- Add
- Checksum
- Convert
- Date
- Drop
- Grok
- Json
- Kv
- Lowercase
- Remove
- Rename
- Repartition
- Replace
- Sample
- Split
- Sql
- Table
- Truncate
- Uppercase
- Uuid
- 自研过滤器插件

Sink 插件:
- Elasticsearch
- File
- Hdfs
- Jdbc
- Kafka
- Druid
- InfluxDB
- Mysql
- S3
- Stdout
- 自研输出插件

## 7. 生产应用案例

- [唯品会](https://mp.weixin.qq.com/s/LVC0UZau24IwOuWN2wLt3w)：唯品会早在 1.0 版本时就引用了 SeaTunnel，使用 SeaTunnel 进行一些 Hive 到 ClickHouse 之间数据交互的工作。
- [Oppo](https://mp.weixin.qq.com/s/2m2fu0lO8BH74UiBHePVbg)：基于 SeaTunnel 进行的二次开发搭建 ETL 特征生产处理平台。
- [Bilibili](https://mp.weixin.qq.com/s/Jexke3ZZAVRiMebwDsRiQg)：基于 SeaTunnel 二次开发实现 AlterEgo 项目。SeaTunnel 在 B 站每天完成千亿级记录、百T级数据的出入仓，解决了电商、直播、创作中心等场景核心任务出入仓难题。
- 微博：微博某业务有数百个实时流式计算任务使用内部定制版 SeaTunnel，以及其子项目 Guardian 做 Seatunnel On Yarn 的任务监控。
- 新浪大数据运维分析平台：新浪运维数据分析平台使用 SeaTunnel 为新浪新闻，CDN 等服务做运维大数据的实时和离线分析，并写入 Clickhouse。
- 搜狗奇点系统：搜狗奇点系统使用 SeaTunnel 作为 ETL 工具, 帮助建立实时数仓体系。
- 趣头条数据中心：使用 SeaTunnel 支撑 MySQL To Hive 的离线 ETL 任务、实时 Hive To Clickhouse 的 backfill 技术支撑，很好的 cover 离线、实时大部分任务场景。
- 永辉超市子公司-永辉云创会员电商数据分析平台：SeaTunnel 为永辉云创旗下新零售品牌永辉生活提供电商用户行为数据实时流式与离线 SQL 计算。
- 水滴筹：水滴筹在 Yarn 上使用 SeaTunnel 做实时流式以及定时的离线批处理，每天处理 3～4T 的数据量，最终将数据写入 Clickhouse。
- 腾讯云：将业务服务的各种日志收集到 Apache Kafka 中，通过 Seatunnel 消费和提取 Apache Kafka 中的部分数据，然后存储到 Clickhouse 中。

参考：
- [Introduction](https://seatunnel.apache.org/zh-CN/docs/2.1.0/introduction)
