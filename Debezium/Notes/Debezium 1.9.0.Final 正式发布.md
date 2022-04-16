---
layout: post
author: wy
title: Debezium 1.9.0.Final 正式发布
date: 2022-04-07 12:33:21
tags:
  - Debezium

categories: Debezium
permalink: debezium-1-9-final-released
---

我很高兴宣布 Debezium 1.9.0.Final 正式发布！除了修复一系列 Bug 以及优化之外，此版本的主要功能还包括：
- 提供对 Apache Cassandra 4 的支持
- 提供对 SQL Server 的 Debezium Connector 的多数据库支持
- 提供将 Debezium Server 作为 Knative 事件源的能力
- 对 Debezium Server 与 Redis Streams 集成的诸多优化

此外，社区已经为 1.9 版本修复了 [276](https://issues.redhat.com/issues/?jql=project%20%3D%20DBZ%20AND%20fixVersion%20in%20(1.9.0.Alpha1%2C%201.9.0.Alpha2%2C%201.9.0.Beta1%2C%201.9.0.CR1%2C%201.9.0.Final)%20ORDER%20BY%20key%20ASC%2C%20status%20DESC) 个 issue；

## 1. 对 Apache Cassandra 4 的支持

及时赶上 Debezium 1.9 版本，在 Debezium Cassandra Connector 中实现了对 Cassandra 4 的支持。更具体地说，是添加了一个新的 Connector，即你现在可以下载 debezium-connector-cassandra-3 或者 debezium-connector-cassandra-4 Connector，具体取决于你的数据库版本。一般我们通常在一个 Connector 中争取实现对多版本的支持，但这次支持新版本所需的代码变更非常大，所以我们决定为两个 Connector 版本单独提供代码库（将共性提取到共享模块中）。

Cassandra 3 和 4 的两个 Connector 暂时仍处于孵化状态，你可以期待在新版本中更多功能的优化。

## 2. 对 SQL Server 的 Debezium Connector 的多数据库支持

SQL Server 允许在一台物理机上配置多个逻辑数据库，这可以非常方便地分离多租户应用程序的不同租户的数据。之前需要为 SQL Server 的每个逻辑数据库设置一个 Debezium Connector 实例，这在处理几十个甚至几百个数据库时变的比较麻烦。在过去的一年里，Sergei Morozov 和他所在的 SugarCRM 团队重新设计了 Debezium SQL Server Connector 以及 Debezium Connector 框架，使其能够识别多分区以解决下面的问题：框架现在能够处理多个源分区的流式变更，这些分区是拆分到不同的 Connector 任务上（在 Kafka Connect 术语中），而这些任务又可以分布在 Kafka Connect 集群的不同 Worker 节点上。

对于 SQL Server Connector，一个逻辑数据库相当于一个这样的源分区，因此你现在可以从一台 SQL Server 物理机流式传输 20 个数据库实例，拆分成四个源任务，分布在五个 Kafka Connect Worker 节点上运行。要使用新的多分区模式，需要通过新的 database.names Connector 配置属性（而不是使用先前的 database.dbname）配置要捕获的数据库的名称，并可以将 tasks.max 的值设置为一个大于 1 的值（可选）。需要注意的是，Schema、主题名称以及 Connector 指标的结构在单分区和多分区模式下是不同的，以便分别说明逻辑数据库的名称和源任务的 id。

多分区模式在 1.9 版本中是实验性的，并计划在未来版本中完全替换 SQL Server Connector 旧的单分区模式，当然你也可以使用多分区模式从一个逻辑数据库中捕获变更。如果可能的话，后续还将为其他 Connector 推出多分区模式，例如用于 Oracle 和 IBM Db2 的 Connector。

## 3. 其他变化

让我们看一下 Debezium 1.9 中的其他的新功能。

首先，Debezium Server 包含了一个用于 HTTP Sink 的适配器，这意味着可以用作 Knative Serving 的 'native' 事件源，不用先通过 Apache Kafka 等消息代理发送消息。

然后，Redis 的友好人员加紧为 Debezium Server 与 Redis Streams 集成做出了一些优化：除了一些性能优化之外，现在还可以将 MySQL 等 Connector 的数据库历史存储在 Redis 中，偏移量也可以存储在 Redis 中。远不止这些：Debezium Server 现在支持自定义配置 providers，正如 Kafka Connect 中已经提供的那样。

要了解有关 Debezium 1.9 中的所有功能、优化和 Bug 修复的更多信息，请查看原始发布公告（[Alpha1](https://mp.weixin.qq.com/s/PWj49UTzytW77mpC9zAJrA)、[Alpha2](https://mp.weixin.qq.com/s/gbmiTSuR3ruLwgC1Y-G-4A)、[Beta1](https://debezium.io/blog/2022/03/03/debezium-1-9-beta1-released/) 和 [CR1](https://mp.weixin.qq.com/s/bFIkJm4iXrG8bX9etvGH4A)）以及 [1.9 发布说明](https://debezium.io/releases/1.9/release-notes)！

## 4. 未来

那么 1.9 之后的下一版本是什么？你可能会认为是 1.10，但这不是我们要做的；相反，我们计划在今年晚些时候发布 Debezium 2.0 作为新的主要版本！Debezium 2.0 将是我们摆脱遗留问题的一个版本。例如，我们计划：
- 删除 MySQL 和 MongoDB Connector 的遗留实现（使用更强大和成熟的实现的 Debezium 标准 Connector 框架）
- 放弃对 Postgres 的 wal2json 支持（被 pgoutput 取代）
- 使用 Java 11 作为基线（例如，允许发出 JDK Flight Recorder 事件以获得更好的诊断）
- 默认使用多分区模式指标（提高一致性）
- 使默认主题名称更加一致，例如心跳主题
- 更改少数列类型的默认类型映射

此计划正在如火如荼地进行，我们非常邀请您加入邮件列表或 Jira 中的 DBZ-3899 issue 上讨论。需要注意的是，虽然我们希望借此机会清理随着时间的推移积累的一些奇怪问题，但向后兼容性也一如既往地重要，我们将尽量减少对现有用户的影响。但正如你对新的主要版本期望的那样，与通常的次要版本相比，升级可能需要花更多的时间。

就时间表而言，由于计划变更的规模和数量，我们将偏离通常的季度发布节奏，而是保留两个季度用于开发 Debezium 2.0，即你可以期待九月底的发布。同时，根据收到的 bug 报告的需要，来发布 1.9 版本的 bug 修复版本。

原文:[Debezium 1.9.0.Final Released](https://debezium.io/blog/2022/04/06/debezium-1.9-final-released/)
