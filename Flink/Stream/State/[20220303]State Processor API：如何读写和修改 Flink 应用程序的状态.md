---
layout: post
author: smartsi
title: State Processor API：如何读写和修改 Flink 应用程序的状态
date: 2022-03-03 14:56:01
tags:
  - Flink

categories: Flink
permalink: how-to-read-write-and-modify-the-state-of-flink
---

无论是在生产环境中运行 Apache Flink 还是在调研 Apache Flink，总会遇到一个问题：如何读写以及更新 Flink Savepoint 中的状态？为了解决这个问题，在 Apache Flink 1.9.0 版本引入了 State Processor API，扩展 DataSet API 实现读写以及修改 Flink Savepoint 和 Checkpoint 中状态。

在这篇文章中，我们解释了为什么说这个特性是 Flink 前进的一大步，以及该特性的用途和用法。最后，我们会讨论 State Processor API 的未来规划，以及如何与 Flink 流批统一的未来整体规划保持一致。

## 1. Flink 1.9 之前的状态流处理

几乎所有重要的流处理应用程序都是有状态的，其中大多数都需要运行数月或者数年。随着时间的推移，这些作业累积了很多有价值的状态，如果由于失败而丢失，重建这些状态代价非常大，甚至可能都无法重建。为了保证应用程序状态的一致性和持久性，Flink 从一开始就设计了完善的 Checkpoint 和恢复机制。随着每个版本的发布，Flink 社区都会添加与状态相关的功能，来提高 Checkpoint 和故障恢复的速度、改善应用程序维护和管理。

然而，Flink 用户经常提起的一个需求就是能够'从外部'访问应用程序的状态。这个需求的动机是验证或者调试应用程序的状态、将应用程序的状态迁移到另一个应用程序、将应用程序从 Heap State Backend 改为 RocksDB State Backend，或者导入来自外部系统（如关系数据库）中应用程序的初始状态。

尽管这些需求的出发点都是合理的，但到目前为止从外部访问应用程序状态这一功能仍然相当有限。Flink 的 Queryable State 特性只支持基于键的查找（点查询），并且不能保证返回值的一致性（应用从故障中恢复前后，key 的值可能不同）。可查询状态不能添加或者修改应用程序的状态。此外，作为应用程序状态的一致快照的 Savepoint 也无法访问，因为应用程序状态是使用自定义二进制格式编码的。

## 2. 使用 State Processor API 读写应用程序状态

Flink 1.9 引入的 State Processor API 真正改变了我们处理应用程序状态的现状！简而言之，基于 DataSet API 扩展实现 Input 和 OutputFormats 来读写 Savepoint 或者 Checkpoint 的数据。由于 DataSet API 和 Table API 可以相互转换，你可以使用关系 Table API 或者 SQL 查询来分析和处理状态数据。

例如，你可以获取正在运行的流处理应用程序的 Savepoint，使用 DataSet 批处理程序对其进行分析，来验证应用程序是否正确。或者，你可以从任何存储中读取一批数据，对其进行处理，然后将结果写入到 Savepoint 中，用来初始化应用程序的状态。现在也可以修复 Savepoint 中不一致的状态条目。以前应用程序被参数和设计选择(无法在启动后不丢失应用程序所有状态的情况下进行更改)所限制，现在 State Processor API 开辟了许多方法来开发有状态的应用程序，。例如，现在你可以任意修改状态的数据类型、调整算子的最大并行度、拆分或合并算子状态、重新分配算子 UID 等等。

## 3. 应用程序状态与数据集映射

State Processor API 可以将流应用程序状态与一个或多个可以单独处理的数据集进行映射。为了能够更好的使用 API，你需要了解这个映射的工作原理。

首先让我们先来看看有状态的 Flink 作业是什么样的。Flink 作业由算子组成，通常有一个或多个 Source 算子，几个实际处理数据的算子，以及一个或多个 Sink 算子。每个算子在一个或多个任务中并行运行，并可以处理不同类型的状态。算子可以有零个、一个或者多个列表形式的 Operator State，作用域仅限于算子的任务。如果将算子应用在 Keyed Stream 上，那么还可以有零个、一个或者多个 Keyed State，作用域仅限定在从每个已处理记录中提取的 Key 上。你可以将 Keyed State 视为分布式键值映射。

下图展示了应用程序 MyApp，由三个算子 Src、Proc 和 Snk 组成。Src 有一个 Operator State（os1），Proc 有一个 Operator State（os2）以及两个 Keyed State（ks1，ks2），Snk 是无状态的。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/how-to-read-write-and-modify-the-state-of-flink-1.png?raw=true)

MyApp 的 Savepoint 和 Checkpoint 由所有状态数据组成，并以可以恢复每个任务状态的方式进行组织。当使用批处理作业处理 Savepoint（或 Checkpoint）数据时，我们需要一个模型，将每个任务的状态数据映射到数据集或表中。实际上，我们可以把 Savepoint 视为一个数据库。每个算子（由 UID 标识）代表一个命名空间。算子的每个 Operator State 可以映射为命名空间下的一个专用表，只有一列来保存所有任务的状态数据。算子的 Keyed State 可以映射为一个表，一列存储 Key，一列存储 Keyed State。下图展示了 MyApp Savepoint 如何与数据库映射。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/how-to-read-write-and-modify-the-state-of-flink-2.png?raw=true)

该图展示了 Src 的 Operator State 的值如何映射到一个具有一列五行的表上，每一行代表 Src 所有并行任务中的一个并行实例。算子 Proc 的 Operator State os2 类似地也会映射到一个表上。Keyed State ks1 和 ks2 组合成一个包含三列的表，一列存储 Key，一列用于 ks1，一列用于 ks2，每一行代表同一 Key 的两个 Keyed State。由于算子 Snk 没有任何状态，它的命名空间是空的。

State Processor API 现在提供了创建、加载和写入 Savepoint 的方法。你可以从加载的 Savepoint 上读取数据集或者将数据集转换为状态并将其添加到 Savepoint 中。可以使用 DataSet API 的完整功能来处理数据集。使用这些方法，可以解决所有前面提到的用例（以及更多用例）。如果您想详细了解如何使用 State Processor API，请查看文档：https://ci.apache.org/projects/flink/flink-docs-release-1.9/dev/libs/state_processor_api.html

## 4. 为什么使用 DataSet API？

如果你对 Flink 的[路线图](https://flink.apache.org/roadmap.html) 比较熟悉，你可能会惊讶 State Processor API 为什么要基于 DataSet API 构建。因为 Flink 社区正计划使用 BoundedStreams 的概念扩展 DataStream API，并弃用 DataSet API。在设计此功能时，我们还评估了 DataStream API 以及 Table API，但都无法提供相应的功能支持。我们不想因为 Flink API 的进展而阻塞这个特性的开发，因此我们决定先在 DataSet API 上构建这个功能，但将其对 DataSet API 的依赖降到最低。因此，将其迁移到另一个 API 也相当容易。

## 5. 总结

一直以来 Flink 用户一直需要这一项功能，可以从外部访问和修改流应用程序的状态。在 Flink 1.9.0 版本，借助 State Processor API 将应用程序状态公开为一种可操作的数据格式。该功能为用户维护和管理 Flink 流应用程序开辟了许多新的可能性，包括流应用程序的任意演变以及应用程序状态的导出和引导。 简而言之，状态处理器 API 解锁了保存点曾经的黑匣子。


原文:[](https://flink.apache.org/feature/2019/09/13/state-processor-api.html)
