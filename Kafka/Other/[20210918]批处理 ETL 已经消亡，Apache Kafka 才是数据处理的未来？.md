---
layout: post
author: smartsi
title: 批处理 ETL 已经消亡，Apache Kafka 才是数据处理的未来？
date: 2021-09-18 22:44:01
tags:
  - Kafka

categories: Kafka
permalink: batch-etl-streams-kafka
---

> 无意之间看到了一篇老文章，一起回顾一下。

在 2016 年 旧金山 [QCon](https://qconsf.com/) 会议上，Neha Narkhede 做了 'ETL 已死，而实时流长存' 的演讲，并讨论了企业数据处理所要面对的不断变化的格局。该演讲的一个核心前提是开源的 Apache Kafka 流处理平台能够提供一个灵活且统一的框架，以支持现代需求的数据转换和处理。

Confluent 的联合创始人兼 CTO Narkhede 在演讲开始时指出，数据以及数据处理系统在过去十年中发生了重大变化。过去传统通常由提供联机事务处理 (OLTP) 的操作数据库以及提供在线分析处理 (OLAP) 的关系数据仓库组成。来自各种操作数据库的数据通常每天一次或两次批量加载到数据仓库中。这种数据集成过程通常称为提取-转换-加载，即我们所说的 ETL。

最近几个数据趋势正在推动传统 ETL 架构发生巨大变化：
- 单服务器数据库正在被各种各样的分布式数据平台所取代，它们在在公司范围内广泛运行。
- 除了事务性数据之外，现在有了更多类型的数据源：例如日志、传感器、指标数据等。
- 流数据越来越普遍，同时在业务上每日批处理的速度已经不能满足要求，需要有更快的处理速度。

这些趋势所造成的后果是传统的数据集成方法最终看起来一团糟：既有自定义处理脚本、企业中间件（消息队列 MQ 技术）还有批处理技术（例如，Hadoop）。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/batch-etl-streams-kafka-1.png?raw=true)

在探讨现代流处理技术如何缓解这些问题之前，Narkhede 简要回顾了一下数据集成的简短历史。从 1990 年代开始，零售业中的企业越来越热衷于使用新的数据形式来分析买家趋势。存储在 OLTP 数据库中的操作数据，必须要提取、转换为目标数据仓库模式，然后加载到数据仓库中。虽然这项技术在过去二十年中的逐渐成熟，但数据仓库内的数据覆盖率仍然相对较低，主要是由于 ETL 的如下缺点：
- 需要一个全局模式。
- 数据清理和管理都是手动的，从根本上来说很容易出错。
- ETL 的成本很高：通常很慢并且需要大量时间以及资源。
- ETL 工具的构建仅局限在以批处理方式连接数据库和数据仓库。

在实时 ETL 方面，早期尝试的方案是企业应用集成（Enterprise application integration，EAI），并使用 ESB 和 MQ 实现数据集成。尽管对实时处理很有效，但这些技术通常无法扩展到所需的规模。这给传统的数据集成带来了两难的选择：实时但不可扩展，或者可扩展但只能采用批处理方案。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/batch-etl-streams-kafka-2.png?raw=true)

Narkhede 指出现代流处理对数据集成提出了新的要求：
- 能够处理大量且多样性的数据。
- 平台必须要从底层就支持实时处理，这会促进向以事件为中心的根本转变。
- 必须使用向前兼容的数据架构，同时能够支持添加更多需要以不同方式处理相同数据的应用程序的能力。

这些要求推动了统一数据集成平台的创建，而不是一系列专门定制的工具。这个平台必须拥抱现代架构和基础设施的基本理念、能够容错、能够并行、支持多种投递语义、提供有效的运维和监控，并且允许进行模式管理。Apache Kafka 是七年前由 LinkedIn 开发的，它就是这样的一个开源流平台，可以通过如下方式作为组织数据的中枢神经系统运行：
- 用作应用程序的实时、可扩展消息总线，不需要 EAI。
- 充当提供所有数据处理目的地的真实来源管道。
- 充当有状态流处理微服务的构建块。

Apache Kafka 在 LinkedIn 目前每天处理 14 万亿条的消息，并且已经部署到了世界范围内成千上万的公司中，包括财富 500 强的公司，如 Cisco、Netflix、PayPal 和 Verizon。Kafka 已经快速成为流数据的首选存储方案，并且为连接多个数据中心的应用程序集成提供了可扩展的消息传递支持。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/batch-etl-streams-kafka-3.png?raw=true)

Kafka 的基础理念是 log，一个只能往上追加、完全有序的数据结构。log 本身采用了发布-订阅的语义，发布者能够非常容易地以不可变和单调的方式往 log 上追加数据，订阅者可以维护自己的指针，以便指示当前正在处理的消息。

Kafka 通过 Kafka Connect API 来构建流数据管道，也就是 ETL 中的 E 和 L。Connect API 利用了 Kafka 的可扩展性，基于 Kafka 的容错模型进行构建并且提供了一种统一的方式监控所有的 Connector。流处理和转换可以通过 Kafka Streams API 来实现，这提供了 ETL 中的 T。使用 Kafka 作为流处理平台能够无需为每个目标 sink、数据存储或系统创建定制化（很可能是重复的）抽取、转换和加载组件。来自 source 的数据经过抽取后可以作为结构化的事件放到平台中，然后可以通过流处理进行任意的转换。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/batch-etl-streams-kafka-4.png?raw=true)

在演讲的最后一部分，Narkhede 更详细地讨论了流处理的概念，即流数据的转换，并提出了两个相互对立的愿景：实时 MapReduce 与事件驱动的微服务。实时 MapReduce 适用于用例分析，需要中央集群以及自定义打包、部署和监控。Apache Storm、Spark Streaming 和 Apache Flink 实现了这一点。 Narkhede 认为，事件驱动的微服务愿景，可以通过 Kafka Streams API 实现，让任何用例都能访问流处理，这只需要向 Java 应用程序添加一个嵌入式库以及搭建一个 Kafka 集群。

Kafka Streams API 提供了一个便利的 fluent DSL，具有像 join、map、filter 和 window 这样的算子。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/batch-etl-streams-kafka-5.png?raw=true)

这是真正的每次一个事件（event-at-a-time）的流处理，不是微批处理，基于事件的时间并且使用数据流风格的窗口来处理延迟到达的数据。Kafka Streams 提供了开箱即用的本地状态支持，并且支持快速的状态化和容错处理。它还支持流的重放，在更新应用、迁移数据或执行A/B 测试的时候，这是非常有用的。

Narkhede 总结说，log 统一了批处理和流处理，log 可以通过批处理的窗口方式进行消费，也能在每个元素抵达的时候进行检查以实现实时处理，Apache Kafka 能够提供 'ETL 的崭新未来'。

> Narkhede 在旧金山 QCon 的完整视频可以在 InfoQ 上通过 [ETL Is Dead; Long Live Streams](https://www.infoq.com/presentations/etl-streams) 查看。


欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文: [Is Batch ETL Dead, and is Apache Kafka the Future of Data Processing?](https://www.infoq.com/articles/batch-etl-streams-kafka/)
