---
layout: post
author: wy
title: BookKeeper 简介
date: 2022-02-01 08:40:21
tags:
  - BookKeeper

categories: BookKeeper
permalink: introduction-to-apache-bookkeeper
---

Apache BookKeeper 是企业级存储系统，旨在提供强大的持久性保证、一致性和低延迟。最初是由雅虎研究院（Yahoo! Research）开发，作为 Hadoop 分布式文件系统（HDFS）NameNode 的高可用（HA）解决方案，以解决严重的单点故障问题。

BookKeeper 在 2011 年作为 Apache ZooKeeper 下的子项目孵化，并在 2015 年 1 月毕业成为顶级项目。这 4 年多来，BookKeeper 已被 Twitter、Yahoo 和 Salesforce 等企业广泛使用，用于存储和服务关键任务数据，并支撑了不同的场景。在这篇博文中，我们将简要介绍 BookKeeper 的概念以及相关术语。

## 1. 背景介绍

BookKeeper 的作者 Benjamin Reed、Flavio Junqueira 和 Ivan Kelly 利用他们构建 ZooKeeper 的经验设计了一个灵活的系统来支持各种工作负载。除了主要用作分布式系统的预写日志 (WAL) 机制外。BookKeeper 目前发展超出了最初的规划，并已成为多个企业级系统的基本组件，这包括 Twitter 的 EventBus 和雅虎的 Apache Pulsar（孵化中）。

## 2. BookKeeper 是什么？

BookKeeper 是一种可扩展的、具有容错能力和低延迟的存储服务，主要用来优化实时工作负载。根据我们多年的经验，一个企业级的实时存储平台应该具备如下几项要求：
- 以非常低的延迟（< 5 ms）写读流数据
- 能够持久的、一致的和容错的存储数据
- 在写数据时能够进行流式传输或追尾传输
- 有效地存储并提供对历史和实时数据的访问

BookKeeper 的设计完全符合上述要求，并被广泛部署来服务多个用例，例如为分布式系统提供高可用或多副本（例如 HDFS NameNode、Twitter 的 Manhattan KV 存储），在单个集群中或多个集群间（多个数据中心）提供跨机器复制，为发布/订阅消息系统(例如，Twitter 的 EventBus、Apache Pulsar）提供存储服务，还为流式作业存储不可变对象，例如检查点数据的快照。

## 3. BookKeeper 概念和术语

BookKeeper 提供复制的、持久的日志流存储，形成具有明确定义顺序序列的记录流。

### 3.1 记录(Records)

在 Apache BookKeeper 中，数据作为一系列不可分割的记录而不是单个字节写入日志。记录是 BookKeeper 中最小的 I/O 单元，也被称作地址单元。每条记录都包含与其相关或者分配给它的序列号（例如单调递增的长整数）。客户端总是从指定记录读取数据，或者追尾序列。这意味着客户端要监听要追加到日志的下一条记录的序列。客户端可以一次接收一条记录，也可以接收包含多条记录的数据块。序列号也可以用于随机检索记录。

### 3.2 日志(Log)

BookKeeper 提供了两种存储原语来表示日志：一个是 Ledger（又称日志段），另一个是 Stream（又称日志流）。

Ledger 是一系列数据记录，当客户端显式关闭它或者写入器（将记录写入其中的客户端）崩溃时，Ledger 就会关闭。一旦 Ledger 被关闭，就不能再写入任何记录了。Ledger 是 BookKeeper 中最低级别的存储原语。Ledger 可用于存储有限数据序列或者无限流。

![](https://github.com/sjf0115/ImageBucket/blob/main/BookKeeper/introduction-to-apache-bookkeeper-1.png?raw=true)

> BookKeeper Ledger：有限数据 entries 序列

Stream（又称日志流）是无限数据记录序列，默认情况下永远不会终止。与只能打开一次来追加记录的 Ledger 不同，Stream 可以多次打开来追加记录。Stream 在物理上由多个 Ledger 组成；Ledger 根据基于时间或空间滚动策略滚动生成。Stream 在被删除之前会存储相对较长的时间，几天、几个月甚至几年。Stream 的主要数据保留机制是截断，包括根据基于时间或空间的保留策略删除最早的 Ledger。

![](https://github.com/sjf0115/ImageBucket/blob/main/BookKeeper/introduction-to-apache-bookkeeper-2.png?raw=true)

> BookKeeper Stream：无限数据记录流

Ledger 和 Stream 为历史数据和实时数据提供统一的存储抽象。在写入数据时，日志流提供了流式传输或追尾传输实时数据记录的能力。存储为 Ledger 的实时数据会变为历史数据。流中积累的数据不受任何一台机器的容量限制。

### 3.3 命名空间

日志流通常在命名空间下进行分类和管理。命名空间是租户用来创建流的一种机制。命名空间也是一个部署或管理单元，可以让你配置命名空间级别的数据放置策略。同一命名空间的所有流都拥有相同的命名空间配置，并将记录存放在数据放置策略配置的存储节点中。这为同时管理多个流提供了强有力的支持。

### 3.4 Bookies

Bookies 即存储服务器。BookKeeper 跨多个 Bookies 复制和存储数据 Entries。一个 Bookie 就是一个单独的存储数据记录的 BookKeeper 存储服务器。出于性能考虑，单个 Bookie 上不是存储整个 Ledger，而是存储 Ledger 的片段。因此，Bookies 作为整体的一部分发挥作用。对于任意给定 Ledger L，集成指存储 Entries 到 L 上的一组 Bookies。写入 Ledger 时，Entries 就会跨集成分段（写入到一组 Bookies 中而不是所有的 Bookies）。

### 3.5 元数据

BookKeeper 需要元数据存储服务来存储与 Ledger 以及可用 Bookie 相关的信息。目前使用 ZooKeeper 来完成这项任务（还包括其他一些协调和配置管理任务）。

## 4. 与 BookKeeper 交互

在与 Bookie 交互时，BookKeeper 应用程序有两个主要角色。首先，他们创建 Ledger 或打开 Stream 来写入数据；其次，打开 Ledger 或 Stream 来读取数据。BookKeeper 提供了两个 API 来与 BookKeeper 中这两个不同的存储原语进行交互：

| API | 描述 |
| :------------- | :------------- |
| Ledger API | 一个低层次 API，可以让你能够直接与 Ledger 交互，根据需要灵活地与 Bookie 交互。 |
| Stream API | 通过 Apache DistributedLog 提供的更高层次、面向流的 API。可以让你与 Stream 交互，而无需管理与 Ledger 交互的复杂性。|

选择使用哪个 API 取决于用户对 Ledger 语义的控制精细程度。用户也可以在单个应用程序中同时使用这两个 API。

## 5. 放在一起看

下图展示了典型的 BookKeeper 安装示例。

![](https://github.com/sjf0115/ImageBucket/blob/main/BookKeeper/introduction-to-apache-bookkeeper-3.png?raw=true)

此图中需要注意的几点：
- 一个典型的 BookKeeper 安装包括一个元数据存储（例如 ZooKeeper）、一个 Bookie 集群以及使用提供的客户端库与 Bookies 交互的多个客户端
- Bookies 将自己发布到元数据存储中，以便客户端可以发现
- Bookies 与元数据存储交互以执行诸如垃圾回收删除数据之类的操作
- 应用程序使用提供的客户端库与 BookKeeper 交互（使用 Ledger API 或 DistributedLog Stream API）
- 应用程序 1 对 Ledger 精细控制，直接使用 Ledger API。
- 应用程序 2 不需要低层次 Ledger 控制，使用更加简化的日志流 API。

## 6. 结论

这篇文章提供了 BookKeeper 的高级概述，并介绍了 Entries, Ledgers, Streams, 命名空间以及 Bookies 概念。最后，我们看到了 BookKeeper 的经典部署，以及数据如何流转。

如果您对 BookKeeper 或 DistributedLog 感兴趣，你可能希望通过以下方式参与 BookKeeper 社区：
- BookKeeper Slack channel：http://apachebookkeeper.slack.com/
- BookKeeper 邮件列表：http://bookkeeper.apache.org/community/mailing-lists/

有关 Apache BookKeeper 项目的更多信息，请访问官方网站 https://bookkeeper.apache.org。

原文:[Introduction to Apache BookKeeper](https://www.splunk.com/en_us/blog/it/introduction-to-apache-bookkeeper.html)
