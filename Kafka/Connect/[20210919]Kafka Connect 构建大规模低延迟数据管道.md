---
layout: post
author: smartsi
title: Kafka Connect 构建大规模低延迟的数据管道
date: 2021-09-19 13:55:00
tags:
  - Kafka

categories: Kafka
permalink: announcing-kafka-connect-building-large-scale-low-latency-data-pipelines
---

很长一段时间以来，公司所做的大部分数据处理都是作为批作业运行，例如，从数据库中转储的 CSV 文件、在一天结束时收集的日志文件等。但企业是实时一直运营的，与其只在一天结束时处理数据，还不如在数据到达时就对其做出反应？这是流处理的新兴世界。但是只有当数据捕获以流的方式完成时，流处理才成为可能；毕竟，我们无法将每天批量处理的 CSV 转储作为流处理。这种向流处理的转变推动了 Apache Kafka 的流行。但是，即使使用 Kafka，构建这种类型的实时数据管道也需要付出一些努力。

Apache Kafka 0.9+ 中的一项新功能 Kafka Connect 使构建和管理流数据管道变得更加容易。

### 1. 流数据平台：所有数据的中心枢纽

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines-1.png?raw=true)

我们有机会在 LinkedIn 构建了一个基于 Kafka 的流数据平台。我们认为流数据的未来就是流数据平台，可以作为所有数据的中心枢纽，在公司范围内广泛运行并支持各种分布式应用程序和系统以流的方式实时消费和处理数据。

流数据平台可以完成两件事：
- 数据集成：流数据平台捕获事件流或者数据变改，并将它们提供给其他数据系统，例如，关系数据库、KV存储、Hadoop 或者数据仓库。
- 流式处理：支持对流进行连续、实时的处理与转换，并使结果在系统范围内可用。

在这里，我们只关注数据集成，并探讨 Kafka Connect 如何通过提供一个通用框架来实现数据集成（在不同系统之间进行流数据传输）。

### 2. Kafka：流数据平台的基础

Apache Kafka 已成为以低延迟向各种应用程序存储和传输大规模流数据的标准。Kafka 为现代流数据集成提供了基础，但是作为中心流数据平台，我们是如何真正将来自其他系统的数据以流的方式导入 Kafka？

当今，采用 Kafka 的公司都会编写一堆代码来发布他们的数据流。我们可以看到，正确地做这件事要比看起来更复杂。如果我们自己实现，那么每个 Connector 都必须解决如下的一系列问题：
- Schema 管理：数据管道需要有携带 Schema 信息的能力。如果没有此功能，我们不得不在下游重新创建。此外，如果同一数据有多个消费者，那么每个消费者都必须重新创建。我们将在以后的博文中介绍数据管道 Schema 管理的各种细微差别。
- 容错：一个流程运行多个实例，并对失败有弹性恢复的能力。
- 并行性：水平扩容以处理大规模数据集。
- 延迟：实时采集、传输和处理数据，从而摆脱每天一次的数据存储。
- 投递语义：在机器故障或者进程崩溃时提供强有力的语义保证。
- 运维和监控：以一致的方式监控每个数据集成进程的健康状况以及进度。

这些问题本身就非常困难，如果每个 Connector 单独解决是不可行的。相反，我们可以构建一个基础设施平台来运行各种 Connector，以一致的方式解决这些问题。到目前，采用 Kafka 进行数据集成还需要大量的专业知识，开发 Kafka Connector 还需要基于客户端 API 构建。

### 3. Kafka Connect 介绍

在 Apache Kafka 的 0.9 版本中，我们添加了一个名为 Kafka Connect 的框架，将构建可扩展流数据管道付诸实践。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines-2.png?raw=true)

Kafka Connect 是一个使用 Kafka 进行大规模实时流数据集成的框架。抽象了 Kafka 每个 Connector 需要解决的常见问题：Schema 管理、容错、分区、Offset 管理、投递语义以及运维和监控。Kafka Connect 有两个目标：
- 鼓励在 Kafka 之上开发丰富的开源 Connector 生态系统。我们设想很快就会有一个大型 Connector 存储库，用于实现不同系统间的流数据传输。
- 简化用于流数据集成的 Connector 应用。用户可以部署协作良好的 Kafka Connector，并且以一致的方式进行监控、部署和管理。

这篇博文的其余部分是对 Kafka Connect 的简要概述，并没有深入探讨架构的细节。从本质上讲，Kafka Connect 很简单。所谓的 Sources 用来将数据导入 Kafka，Sinks 用来从 Kafka 导出数据。Source 或 Sink 的实现称之为 Connector。用户部署 Connector 以在 Kafka 上启用数据流。

Kafka Connect 专为大规模数据集成而设计，并内置并行模型；Kafka Connect 的 Source 和 Sink 都可以映射到经过分区的记录流。这是 Kafka Topic 分区概念的概括：流可以认为是被分割成独立的无限记录序列的完整记录集。让我举几个例子：如果一个流代表一个数据库，那么一个流分区将代表数据库中的一个表；同样，如果一个流代表一个 HBase 集群，那么一个流分区将代表一个特定的 HBase Region。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines-3.png?raw=true)

流分区是最小的并行单元，允许 Connector 并行处理数据。在上面的例子中，Kafka Connect 可以独立地、在不同的主机上、并行地为每个表或每个 HBase Region 复制数据。Kafka Connect 支持动态数量的分区；随着时间的推移，流可能会增长需要添加更多分区或者流变小需要删除分区。例如，允许数据库 Connector 发现新创建的表，而无需重新启动 Connector。

Kafka Connect 与 Kafka 紧密集成，因此可以充分利用 Kafka 的重要功能，这有如下好处：首先，Kafka 有一个并行模型，可以水平扩展，同时保证每个分区的有序性。这样 Kafka Connector 就可以利用 Kafka 的并行模型来水平扩展以应对大量流数据集成的工作负载。其次，Kafka 支持定义记录在分区中的位置的 Offset，并且还提供对 Offset 的管理。这样构建在 Kafka 之上的每个 Connector，无论是 Source 还是 Sink，都可以通过共享一个通用机制来跟踪 Connector 在流中的位置，以及在故障恢复后重新启动消费。在 Kafka 0.9 版本中加入了第三个同样重要的功能：组管理。组管理机制允许一组进程不仅就组成员身份达成一致，而且还可以协调成员身份更改的操作。类似于 Kafka 消费者组如何使用它来判断哪些消费者属于同一组并协调谁使用哪些分区，Kafka Connect 利用它在形成 Kafka Connect 集群的一组进程上对 Connector 分区进行负载平衡。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines-4.png?raw=true)

Offset 管理是流数据集成的关键，由于数据流没有预期的结束，因此 Connector 必须以连续的方式记住它们在流中的位置。这样 Connector 在出现故障时也可以保证投递语义；从他们中断的地方恢复数据复制，而不是丢失数据或重新复制太多数据。Kafka Connect 中的每条记录都包含一个键、一个值以及一个 Offset，用于标记流分区中每条记录的位置。Offset 因 Source 而不同：对于通用数据库 Source，Offset 可能指时间戳列值，而对于 MySQL Source，Offset 指行在事务日志中的位置。对于 Sink Connector 而言，是 Kafka Offset。Kafka Connect 提供了 Offset 存储机制；Connector 可以根据需要或者按配置的固定间隔刷新 Offset。框架透明地处理 Offset 恢复，以便 Connector 可以从流中的最后一个检查点位置重新开始消费数据。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines-5.png?raw=true)

Kafka Connect 在 Source 和 Sink 系统之间支持两种不同级别的投递语义保证：At-Least-Once(至少一次), At-Most-Once(至多一次)，并在将来的版本中支持 Exactly-Once。由 Connector 的实现来提供投递语义保证。例如，任何允许幂等写入以及提供存储 Offset 和数据能力的 Sink 都可以提供 Exactly-Once 语义。另一方面，还不支持 Exactly-Once 语义写入 Kafka，因此，写入 Kafka 的 Source Connect 仅支持 At-Least-Once(至少一次), At-Most-Once(至多一次) 语义保证。

Kafka Connect 与流程部署和资源管理无关，它不负责启动、停止或重新启动进程。换句话说，Kafka Connect 会自动检测故障并重新平衡剩余进程的工作。Kafka Connect 并没有强加特定的资源管理框架或一组操作工具；它可以和 Pupper、Chef、Mesos、Kubernetes 或者 YARN 搭配使用。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines-6.png?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文：[Announcing Kafka Connect: Building large-scale low-latency data pipelines](https://www.confluent.io/blog/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines/)
