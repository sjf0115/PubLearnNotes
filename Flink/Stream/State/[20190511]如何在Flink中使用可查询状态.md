---
layout: post
author: sjf0115
title: 如何在Flink中使用可查询状态
date: 2019-05-11 14:56:17
updated: 2019-05-11 14:56:17
tags:
  - Flink

categories: Flink
  permalink: how-to-use-queryable-state-of-flink
---

流应用程序状态是处理事件时更新的所有变量的集合。在各个事件的处理过程中可靠且一致地保持状态是使流式传输框架真正有用的原因：它是所有有趣操作所必需的，例如窗口，连接，统计，状态机等。 Apache Flink对流应用程序状态的支持已经很先进：它的基于检查点的容错机制是轻量级的，并且在发生故障时保证了一次性语义，其保存点功能使得部署代码更新成为可能，而不会丢失应用程序的当前进度。

### 2. 有状态的流处理架构

首先，我们会看到一个没有可查询状态的 Flink 用例：
![]()

上图展示了一个 Flink 程序，该程序消费来自 Kafka 的用户行为事件（例如展示次数，点击次数等），根据键计数（例如内容ID），在某个时间间隔进行窗口计数，然后将完成的窗口发送到 Key-Value 存储中，以便用户可以访问最终计数。状态存储在应用程序的本地。有状态的流处理架构为我们提供：
- 低延迟：Flink 的性能可以确保我们快速进行计算，并且可以快速访问已完成的窗口。
- 容错：Flink 的检查点管理应用程序内本地状态，并确保发生故障时 Exactly-Once 语义。这意味着即使出现故障，我们也可以确信我们的结果是准确的（没有重复计算，也没有丢失事件）。
- 准确性：Flink 的事件时间处理意味着无序数据可以根据事件实际发生的时间而不是当它到达我们的处理系统时的时间进行窗口划分。在处理由上游系统造成的延迟时，这一点尤为重要。

但是在窗口完成之前我们无法获得计数，我们仍然需要等窗口完成后发送到外部存储。从理论上讲，这两点应该是可以解决的。毕竟，我们知道我们的计数以应用程序状态的形式存在于 Flink 应用程序中。我们需要一种方法来获取它们。

### 3. 可查询状态作为实时访问层

Flink 的可查询状态提供了对 Flink 内部应用程序状态的访问权限，在此用例中，它提供了一种对运行数据聚合的方法，以便我们可以在窗口完成之前更新计数。下面是我们添加可查询状态后的流处理架构：
![]()

上图与我们第一个图几乎相同，只有一个补充：我们现在可以使用 Flink 的可查询状态 API 访问正在进行计算的窗口的结果。换句话说，负责向用户提供结果的外部应用程序直接与我们的 Flink 应用程序交互以提供对聚合的访问权限，而已经完成的窗口仍然会被发送到 Key-Value 存储中。在这种方法中，我们已经解决了有状态流处理架构中一个明显的缺点 - 不能实时访问正在运行中的聚合的结果。但是我们仍然需要依赖于外部存储，发送已完成计数。

### 4. 逻辑结论：没有Key-Value存储

让我们更进一步：
![]()

上图展现了一种方法，其中可查询状态允许我们可以不使用外部存储，之前我们需要发送已完成窗口数据。应用程序的所有结果都存储在 Flink 状态中，并且仅存储在 Flink 状态中。通过充分利用 Flink 的应用程序状态，通过移除对额外存储的依赖简化了端到端系统。Flink 可查询状态背后的愿景是：提供从状态中访问实时结果的应用程序以及简化架构。

### 5. Example

我们来看一个 Flink 应用程序，该应用程序为外部查询提供计数。我们可以访问[这](https://github.com/dataartisans/flink-queryable_state_demo)并亲自体验一下。

![]()

在这个例子中，我们有一个 BumpEvent 实例流，每个事件由用户与商品交互时触发。出于演示的目的，源自己生成事件。
```java
public class BumpEvent {
    private final int userId;
    private final String itemId;
}
```
我们示例中的 itemId 是由数字字母组成的三个字符，如ABC或1A3。我们想要计算每个项目收到多少个碰撞，因此通过itemId键入流。 在创建了键控流之后，我们使用Flink的状态抽象将其公开为可查询状态流。
```java
// Increment the count for each event (keyed on itemId)
FoldingStateDescriptor<BumpEvent, Long> countingState = new FoldingStateDescriptor<>(
     "itemCounts",
      0L, // 初始化为0
      (acc, event) -> acc + 1L, // 为每个事件加一
      Long.class
);

bumps.keyBy(BumpEvent::getItemId).asQueryableState("itemCounts", countingState);
```
可查询状态流接收每个事件并更新创建的状态实例。在这个例子中，我们使用 FoldingState 来为每个接收到的事件更新累加器。在我们的例子中，我们增加一个计数(acc + 1L)。请注意，你不受变种 FoldingState 的约束，也可以完全灵活地使用其他 Flink 支持的状态。现在，我们的应用程序已准备好返回外部查询的结果。查询由完全异步的 QueryableStateClient 处理，并在必要时处理状态位置的查找以及实际查询状态实例的网络通信。作为用户，你只需提供以下信息即可设置客户端：
- 要查询的作业的ID
- 要查询的状态实例名称
- 键和值的类型

在我们的示例中，状态实例的名称是 itemCounts，键类型是 String，值是 Long。其余由客户端处理，你可以直接开始查询你的数据流。我们的演示代码包含一个简单的REPL，允许你针对正在运行的作业重复提交查询：
```
./run-query-repl.sh 2488a115d832013edbbd5a6599e49e45
[info] Querying job with ID '2488a115d832013edbbd5a6599e49e45'
[info] Executing EventCountClient from queryablestatedemo-1.0-SNAPSHOT.jar (exit via Control+C)
$ ABC
[info] Querying key 'abc'
446 (query took 99 ms)
$ ABC
[info] Querying key 'abc'
631 (query took 1 ms)
```
我们使用键 ABC 查询作业物品的计数，每次返回的计数都是在增加的，首先是446，然后是631。初始查询需要比较长的时间，因为客户端进行位置定位以找出哪个 TaskManager 实际上维护键 ABC 的状态。在查找到位置信息之后，客户端将其缓存以用于以后的请求。然后由保存指定键的状态的 TaskManager 直接返回实际请求。



英译对照:
- 可查询状态: Queryable State
- 状态: State

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[Queryable State in Apache Flink® 1.2.0: An Overview & Demo](https://www.ververica.com/blog/queryable-state-use-case-demo)
