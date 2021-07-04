---
layout: post
author: sjf0115
title: Flink 使用 Broadcast State 的4个注意事项
date: 2021-07-04 19:45:21
tags:
  - Flink

categories: Flink
permalink: broadcast-state-pattern-flink-considerations
---

在 Apache Flink 1.5.0 中引入了广播状态（Broadcast State）。本文将描述什么是广播状态模式，广播状态与其他的 Operator State 有什么区别，最后说明一下在 Flink 中使用该功能时需要考虑的一些重要注意事项。

### 1. 什么是广播状态模式

广播状态模式指的是将低吞吐量的事件流（例如，包含一组规则）广播到某个算子所有并发实例上的一种流应用程序，然后与来自另一条事件流的原始数据进行计算。广播状态模式的一些典型应用案例如下：
- 动态规则：假如我们有这样一条规则，当交易值超过100万美元时需要发警报，并将这一规则广播到算子所有并发实例上。
- 数据丰富：对只包含用户ID的交易数据流进行数据丰富，可以将广播数据与用户ID进行关联。

为了实现这样的应用，广播状态是关键组件，我们将在下文详细描述。

### 2. 什么是广播状态？

广播状态是 Flink 中支持的第三种类型的 Operator State。广播状态使得 Flink 用户能够以容错、可扩展地将来自广播的低吞吐的事件流数据存储下来。来自另一条数据流的事件可以流经同一算子的各个并发实例，并与广播状态中的数据一起处理。有关其他类型的状态以及如何使用它们的更多信息，可以查阅 Flink 文档。

广播状态与其他 Operator State 之间有三个主要区别。不同于其余类型的 Operator State，广播状态：
- Map 的格式
- 有一条广播的输入流
- 算子可以有多个不同名字的广播状态

广播状态怎么使用可以查看博文[Flink 广播状态实战指南](http://smartsi.club/a-practical-guide-to-broadcast-state-in-apache-flink.html)。

### 3. 重要注意事项

对于急切想要使用广播状态的 Flink 用户，Flink 官方文档提供了有关 API 的详细指南，以及在应用程序中如何使用该功能。在使用广播状态时要记住以下4个重要事项：

#### 3.1 使用广播状态算子任务间不会相互通信

这也是为什么 (Keyed)-BroadcastProcessFunction 只有广播端可以修改广播状态内容的原因。用户必须保证对于到达的每个元素，算子所有并发任务必须以相同的方式修改广播状态内容（保证一致性）。或者说，如果不同的并发任务拥有不同的广播状态内容，将导致不一致结果。

#### 3.2 广播状态中事件顺序在不同任务上不尽相同

尽管广播流元素保证所有元素（最终）可以到达下游所有任务，但是元素到达每个任务的顺序可能会不同。因此，对广播状态的修改不能依赖于输入数据的顺序。

#### 3.3 所有算子任务都会快照下广播状态

在 checkpoint 时，所有任务都会快照他们的广播状态，并不仅仅是其中的一个，即使所有任务在广播状态中存储的元素是一样的。这样做的目的是为了避免在恢复期间从单个文件读取而造成热点。但是，我们还会通过权衡因子 p (=并发度)对增加的快照状态大小进行权衡（随着并发度的增加，快照的大小也会随之增加）。Flink 保证了在恢复/扩展时不会出现重复数据和丢失数据。在以相同或更小并行度恢复时，每个任务会读取其对应的检查点状态。在扩大并发度恢复时，每个任务优先读取自己的状态，剩下的任务（p_new-p_old）以循环方式读取先前任务检查点的状态。

#### 3.4 RocksDB状态后端目前还不支持广播状态

广播状态在运行时保存在内存中。因为当前(博文发表事件为2018.9)，RocksDB 状态后端还不适用于 Operator State。Flink 用户应该相应地为其应用程序配置足够的内存。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文:[Broadcast State Pattern in Apache Flink: 4 important considerations](https://www.ververica.com/blog/broadcast-state-pattern-flink-considerations)
