---
layout: post
author: sjf0115
title: 影响 Flink 有状态函数和算子性能的 3 个重要因素
date: 2019-04-22 12:32:01
tags:
  - Flink

categories: Flink
permalink: performance-factors-stateful-functions-operators-flink
---

本文重点介绍开发人员在有状态流处理应用中使用 Flink 的 Keyed State 的函数或算子评估性能时应牢记的3个重要因素。

Keyed State 是 Flink 中两种状态中的其中一种，另一种是 Operator State。顾名思义，Keyed State 与 Key 进行绑定，只适合处理来自 KeyedStream 数据的函数和算子。Operator State 和 Keyed State 之间的区别在于 Operator State 是作用于算子的每个并发实例上（子任务），而 Keyed State 是基于每个 Key 的一个状态分区进行分区或分片。

下面我们讨论 3 个会影响 Flink Keyed State 性能的因素，在开发有状态流应用程序时应该记住这些因素。

### 1. 选择合适的状态后端

对 Flink 应用程序有状态函数或算子性能影响最大的是我们所选择的状态后端。最明显的因素是每个状态后端以不同的方式处理状态序列化以持久化保存。

例如，在使用 FsStateBackend 或 MemoryStateBackend 时，本地状态在运行时期间作为堆上对象进行维护，因此在访问和更新时开销比较低。仅在创建状态快照以创建 Flink 检查点或保存点时才会发生序列化开销。使用这些状态后端的缺点是状态大小受 JVM 堆大小的限制，并且可能会遇到 OutOfMemory 错误或垃圾回收的长暂停。相反，诸如 RocksDBStateBackend 之类的核外（out-of-core）状态后端可以通过在磁盘上维护本地状态来允许更大的状态大小。需要权衡的是每个状态的读写都需要序列化/反序列化。

为了解决这个问题，如果你的状态大小很小并且预计不会超过堆大小，那么使用堆上后端将是明智的选择，因为它避免了序列化开销。否则，RocksDBStateBackend 将成为大型状态应用程序的首选。

### 2. 选择适合的状态原语

> ValueState / ListState / MapState

另一个重要因素是选择正确的状态原语。Flink 目前支持 3 个用于 Keyed State 的状态原语：ValueState，ListState 和 MapState。

Flink 新手可能犯的一个常见错误就是选择状态原语，例如，`ValueState<Map<String，Integer >>`，map 条目希望能随机访问。在这种情况下，使用 `MapState<String，Integer>` 肯定会更好，尤其是考虑到核外状态后端（例如 RocksDBStateBackend），在访问时需要序列化/反序列化整个 ValueState 状态，而对于 MapState，只会序列化每个条目。

### 3. 访问模式

继上一节关于状态原语之后，我们已经知道访问状态的应用程序逻辑有助于我们确定使用哪种状态结构。正如开发人员在设计任何类型的应用程序时期望的那样，为应用程序的特定数据访问模式使用不合适的数据结构会对整体性能产生严重影响。

### 4. 结论

开发人员应该考虑上述所有三个因素，因为它们可以在很大程度上影响 Flink 中有状态函数和算子的性能。

英译对照
- 算子: operator
- 状态后端: state backend
- 检查点: checkpoints
- 保存点: savepoints
- 状态原语: state primitives

原文:[
3 important performance factors for stateful functions and operators in Flink](https://www.ververica.com/blog/performance-factors-stateful-functions-operators-flink)
