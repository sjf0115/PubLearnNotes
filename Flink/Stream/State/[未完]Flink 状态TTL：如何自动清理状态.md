---
layout: post
author: wy
title: Flink 状态TTL：如何自动清理状态
date: 2021-07-25 20:37:01
tags:
  - Flink

categories: Flink
permalink: how-to-automatically-cleanup-state-with-state-ttL
---

> Flink 版本 1.8.0

许多有状态流应用程序的一个共同需求是自动清理应用程序状态，以便有效控制状态大小，以及控制应用程序状态的有效时间。Apache Flink 从 1.6.0 版本开始引入状态的生存时间（time-to-live，TTL）功能，使得应用程序的状态清理以及有效的控制状态大小成为可能。

在本文中，我们会讨论 State TTL 的功能以及用例。此外，我们还展示如何使用和配置 State TTL。同时，我们将会解释 Flink 如何借助 State TTL 功能来管理状态，并对 Flink 1.8.0 中该功能引入的相关新特性进行一些展示。本文章最后对未来的改进和扩展作了展望。

### 1. 状态的暂时性

从两个主要方面来解释为什么状态只应该维持有限的时间。让我们设想一个 Flink 应用程序，它接收用户登录事件流，并为每个用户存储上一次登录时的相关事件信息和时间戳，以改善高频访问用户的体验。

控制状态的大小。State TTL 的主要使用场景就是能够有效地管理不断增长的状态大小。通常情况下，数据只需要暂时保存，例如，户处在一次网络连接会话中。当用户访问事件结束时，这些数据对我们已经没有用处，但实际上还占用状态存储空间。Flink 1.8.0 引入的基于 TTL 的后台状态清理机制，使得我们能够自动地对无用数据进行清理。此前，应用程序开发人员必须采取额外的操作并显式地删除无用状态以释放存储空间。这种手动清理过程不仅容易出错，而且效率也低于新的惰性删除状态方法。以上述存储上一次登录时间的示例，一段时间后可能不再需要上一次的登录信息，因为用户可能变为非高频用户。

遵守数据保护和敏感数据要求。随着数据隐私法规的发展，例如，欧盟颁布的通用数据保护法规 GDPR），使得遵守此类数据要求或处理敏感数据成为许多用例和应用程序的首要任务。此类使用场景的典型案例包括需要仅在特定时间段内保存数据并防止其后可以再次访问该数据。这对于为客户提供短期服务的公司来说是一个挑战。State TTL 这一特性，可以保证应用程序仅在有限时间内可以进行访问，有助于遵守数据保护法规。

这两个需求都可以通过 State TTL 功能来解决，这个功能在键值变得不重要并且不再需要保存在存储中时，就可以不断地、持续地删除键值对应的状态。

### 2. 对应用状态的持续清理

Apache Flink 1.6.0 版本引入了 State TTL 功能。流处理应用的开发者可以配置算子状态在超时后过期以及清除。在 Flink 1.8.0 中，该功能得到了进一步的扩展，对 RocksDB 和堆状态后端（FSStateBackend 和 MemoryStateBackend）的旧数据进行持续性的清理。

在 Flink 的 DataStream API 中，应用状态由状态描述符定义。State TTL 是通过将 StateTtlConfiguration 对象传递给状态描述符来配置的。以下 Java 示例展示了如何创建 State TTL 的配置，并将其提供给状态描述符，该描述符将用户的上次登录时间作为 Long 值保存：
```java
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.time.Time;
import org.apache.flink.api.common.state.ValueStateDescriptor;

StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.days(7))
    .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
    .setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
    .build();

ValueStateDescriptor<Long> lastUserLogin =
    new ValueStateDescriptor<>("lastUserLogin", Long.class);

lastUserLogin.enableTimeToLive(ttlConfig);
```
Flink 提供了多个选项来配置状态 TTL 功能：
- 什么时候重置 TTL？默认情况下，当状态修改时会更新状态的到期时间。或者也可以在读取时更新，但需要额外的写操作来更新时间戳。
- 过期的数据是否还可以访问？State TTL 采用惰性策略来清理过期状态。这可能导致应用程序尝试读取已过期但尚未删除的状态。我们可以配置此类读取请求是否可以返回过期状态。在任何一种情况下，过期状态都会在之后立即删除。虽然返回过期状态有利于数据的可用性，但数据保护法规要求不能返回过期状态。
- 哪些时间语义用于 TTL 计时器？在 Flink 1.8.0 中，用户只能使用处理时间来定义 TTL。计划在未来支持事件时间。

内部实现上，State TTL 功能通过存储上次修改的时间戳以及实际状态值来实现。虽然这种方法增加了一些存储开销，但它可以允许 Flink 在状态访问、Checkpoint、恢复以及存储清理过程中检查过期状态。

### 3. 垃圾回收

当在读操作中访问状态时，Flink 会检查它的时间戳，如果过期则清除状态（是否返回过期状态，取决于你配置的状态可见性）。由于这种惰性删除策略，那些永远都不会再访问的过期状态将永远占用存储空间，除非它被垃圾回收。那么，在没有显示处理过期状态的情况下，如何删除这些数据呢？一般来说，我们可以配置不同的策略在后台进行删除。

#### 3.1 保持完整状态快照干净

Flink 1.6.0 已经支持在生成检查点或保存点的完整快照时自动驱逐过期状态。请注意，状态驱逐并不适用于增量检查点。必须明确启用完整快照上的状态驱逐，如以下示例所示：
```java
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.days(7))
    .cleanupFullSnapshot()
    .build();
```

本地存储大小保持不变，但存储的快照会减少。只有当算子从快照重新加载其状态时，即在恢复或从保存点启动时，算子的本地状态才会被清除。由于这些限制，应用程序在 Flink 1.6.0 过期后仍然需要主动删除状态。为了改善用户体验，Flink 1.8.0 引入了另外两种自主清理策略，其中一种用于 Flink 的两种状态后端。我们在下面描述它们。

### 3.2 堆状态后端中的增量清理

此方法特定于堆状态后端（FSStateBackend 和 MemoryStateBackend）。这个想法是状态后端为所有状态条目维护一个惰性全局迭代器。某些事件，例如状态访问，会触发增量清理。每次触发增量清理时，迭代器都会前进。检查遍历的状态条目并删除过期的。以下代码示例显示了如何启用增量清理：
```java
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.days(7))
    // check 10 keys for every state access
    .cleanupIncrementally(10, false)
    .build();
```
如果启用，每个状态访问都会触发清理步骤。 对于每个清理步骤，都会检查一定数量的状态条目是否过期。 有两个调整参数。 第一个定义了每个清理步骤要检查的状态条目数。 第二个参数是在每个处理过的记录之后触发清理步骤的标志，除了每个状态访问。

这种方法有两个重要的警告： * 第一个是增量清理所花费的时间增加了记录处理延迟。 * 第二个实际上应该可以忽略不计，但仍然值得一提：如果没有访问状态或没有处理记录，则不会删除过期状态。

一种常见的方法是基于计时器在一定时间后手动清理状态。想法是为每个状态值和访问的 TTL 注册一个计时器。当定时器结束时，如果自定时器注册以来没有发生状态访问，则可以清除状态。这种方法引入了额外的成本，因为计时器会随着原始状态一起消耗存储空间。然而，Flink 1.6 对定时器处理进行了重大改进，例如高效的定时器删除（FLINK-9423）和 RocksDB 支持的定时器服务。







原文:[State TTL in Flink 1.8.0: How to Automatically Cleanup Application State in Apache Flink](https://flink.apache.org/2019/05/19/state-ttl.html)
