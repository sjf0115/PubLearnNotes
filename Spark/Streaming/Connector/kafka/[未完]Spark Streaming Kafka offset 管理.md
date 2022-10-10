---
layout: post
author: sjf0115
title: Spark Streaming Kafka offset 管理
date: 2018-08-14 21:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-offset-management-for-apache-kafka
---

我们在使用 Spark Streaming 读取 Kafka 中持续不断的流时，我们不得不考虑 Kafka Offset 的管理，以便在出现故障时可以恢复流应用程序。在这篇文章中，我们将介绍几种管理 Offset 的方法。

### 1. Offset 管理简介

Spark Streaming 与 Kafka 的集成允许用户从单个Kafka Topic 或多个 Kafka Topic 中读取消息。Kafka Topic 从分布式分区集合中接收消息。每个分区按顺序维护已接收的消息，由 offset 进行标识，也称为位置。开发人员可以利用 Offsets 来控制他们的 Spark Streaming 作业读取的位置，但它确实需要偏移管理。

Offsets 管理对于保证流式应用在整个生命周期中数据的连贯性是非常有益的。例如，如果在应用停止或者报错退出之前没有将 offset 保存在持久化数据库中，那么 offset rangges 就会丢失。更进一步说，如果不读取分区的 Offsets，Spark Streaming 作业将无法继续处理上次停止时的数据。

![]()

上图描述了管理 Spark Streaming 应用程序中的 Offsets 的一般流程。Offsets 可以通过多种方式进行管理，但通常都遵循以下几个步骤：
- 在初始化 Direct DStream 时，需要指定每个 Topic 分区与 Offsets 的映射，这样 Direct DStream 就知道从每个分区的什么位置读取数据。指定的 Offsets 与下面的第四步写入的位置相同。
- 然后读取并处理该批消息。
- 处理完后，存储结果以及 Offsets。存储结果和提交 Offsets 操作周围的虚线只是强调如果需要更严格的语义，用户可以进一步进行一些操作确保更严格的语义。这包括幂等操作或将结果与 Offsets 原子性存储。
- 最后，外部持久数据存储（如HBase，Kafka，HDFS和ZooKeeper）来跟踪已处理的消息。

根据业务需求，可以将不同的场景合并到上述步骤中。Spark 程序的灵活性允许用户通过细粒度控制在周期性处理阶段之前还是之后存储 Offsets。考虑以下情况：Spark Streaming 应用程序正在读取来自 Kafka 的消息，对 HBase 数据执行查找以丰富或转换消息，然后将丰富的消息发布到另一个 Topic 或单独的系统（例如其他消息传递系统，返回到 HBase，Solr，DBMS等）。在这个例子中，我们只考虑消息处理之后发送到其他系统中。

### 2. 存储 Offset 到外部系统

在本节中，我们将来探讨一下不同的外部持久化 Offsets 存储选项。

对于本节中提到的方法，如果使用 `spark-streaming-kafka-0-10` 库，我们建议用户将 `enable.auto.commit` 设置为 `false`。这个配置仅适用于这个版本，如果将 `enable.auto.commit` 设置为 `true` 表示使用由 `auto.commit.interval.ms` 配置的时间间隔周期性的自动提交 Offsets。在 Spark Streaming 中，将此配置设置为 `true` 时会在 Kafka 读取消息后自动将 Offsets 提交给 Kafka，而这时 Spark 不一定已处理完这些消息（数据有可能还没有处理完，就提交 Offsets）。如果精确控制 Offsets 的提交，需要将 Kafka 参数 `enable.auto.commit` 设置为 `false`，然后按照以下选项之一进行操作。

#### 2.1 Spark Streaming checkpoints

#### 2.2 Storing Offsets in HBase

#### 2.3 Storing Offsets in ZooKeeper








用户可以在 ZooKeeper 中存储 Offsets 范围，这可以为在 Kafka 流上次停止的地方启动流处理提供了一种可靠的方法。

在这种场景下，在启动时，Spark Streaming 作业将从 ZooKeeper 上查询每个 Topic 分区的最新处理的 Offsets。如果在 ZooKeeper 上找到一个之前从未管理的新分区（新分区出现），最新处理的 Offsets 默认为从头开始。处理完每个批次数据后，用户可以选择存储处理的第一个 Offsets 还是最后一个 Offsets。此外，在 ZooKeeper 中存储 Offsets 的 znode 位置使用与旧的 Kafka 消费者API相同的格式。因此，跟踪或监视存储在 ZooKeeper 中的Kafka Offsets 的工具仍然有效。

初始化 ZooKeeper 连接以查询和存储 ZooKeeper 的 Offsets：
```

```


























### 3. 不管理 Offset











https://juejin.cn/post/6844903589748408333















原文：http://blog.cloudera.com/blog/2017/06/offset-management-for-apache-kafka-with-apache-spark-streaming/
