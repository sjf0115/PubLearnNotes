---
layout: post
author: sjf0115
title: Flink 内部原理之Operator Chain
date: 2018-03-07 11:40:01
tags:
  - Flink
  - Flink 内部原理

categories: Flink
permalink: flink-internals-operator-chain
---

### 1. 概述

在分布式运行中，Flink 将算子的 `SubTask` 连接成 `Task`。每个 `Task` 都只由一个线程执行。当一个算子链接到前一个算子时，这意味着它们运行在同一个线程中。他们变成一个由多个步骤组成的算子。这样可以获得更好的性能：它降低了线程间切换和缓冲的开销，并增加了整体吞吐量，同时降低了延迟。如果可能的话，Flink 默认链接算子（例如，两个连续的 `map` 转换）。API可以对链接进行更细粒度的控制。

下面这幅图，展示了 `Source`，`map`、`keyBy/window/apply` 并行度为2、`Sink` 并行度均为1，最终以5个并行的线程来执行的优化过程：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%88%86%E5%B8%83%E5%BC%8F%E8%BF%90%E8%A1%8C%E7%8E%AF%E5%A2%83-1.png?raw=true)

上图将 `Source` 和 `map` 两个紧密度高的算子优化后串成一个 `Operator Chain`，实际上一个 `Operator Chain` 就是一个大的 `Operator` 的概念。图中的 `Operator Chain` 表示一个 `Operator`，`keyBy` 表示一个 `Operator`， `Sink` 表示一个 `Operator`。图中的上半部分有3个 `Operator` 对应的是3个 `Task`。图中的下半部分是上半部分的一个并行化版本，对每一个 `Task` 都并行化为多个 `Subtask`，这里只是演示了2个并行度，`sink` 算子是1个并行度。

### 2. 限制条件

并不是任意两个算子就能链接在一起，有一些限制条件：
- 上下游的并行度一致
- 下游节点的入度为1 （也就是说下游节点没有来自其他节点的输入）
- 上下游节点都在同一个 slot group 中（下面会解释 slot group）
- 下游节点的 chain 策略为 ALWAYS（可以与上下游链接，map、flatmap、filter等默认是ALWAYS）
- 上游节点的 chain 策略为 ALWAYS 或 HEAD（只能与下游链接，不能与上游链接，Source默认是HEAD）
- 两个节点间数据分区方式是 forward（参考理解数据流的分区）
- 用户没有禁用 chain


### 3. 链接策略

为算子定义链接方案。当一个算子链接到前一个算子时，这意味着它们运行在同一个线程中。他们变成一个由多个步骤组成的算子。链接策略 `ChainingStrategy`有如下几种：
- `ALWAYS` 只要有可能，算子就会进行链接。为了性能优化，通常允许最大链接和增加算子并行度。
- `NEVER` 算子不会与前一个算子或后一个算子进行链接。
- `HEAD` 算子不会与前一个算子进行链接，但是有可能与后一个算子进行链接。

`StreamOperator` 使用的默认值是 `HEAD`，这意味着算子不会与前一个算子进行链接。但是大多数算子都会用 `ALWAYS` 来覆盖，这意味着只要有可能，他们就会被链接到前一个算子上。





Operator chain的行为可以通过编程API中进行指定。可以通过在DataStream的operator后面（如someStream.map(..))调用startNewChain()来指示从该operator开始一个新的chain（与前面截断，不会被chain到前面）。或者调用disableChaining()来指示该operator不参与chaining（不会与前后的operator chain一起）。在底层，这两个方法都是通过调整operator的 chain 策略（HEAD、NEVER）来实现的。另外，也可以通过调用StreamExecutionEnvironment.disableOperatorChaining()来全局禁用chaining。




如果要禁用整个作业中的链接，请使用 StreamExecutionEnvironment.disableOperatorChaining（）。对于更细粒度的控制，可用使用以下函数。请注意，这些函数只能在 DataStream 转换操作之后使用，因为它们引用上一个转换。例如，你可以使用 someStream.map（...）.startNewChain（），但不能使用 someStream.startNewChain（）。

资源组是 Flink 中的插槽，请参阅插槽。如果需要，你可以在不同的插槽中手动隔离算子。

3.1 开始一个新链

从这个算子开始，开始一个新的链。将这两个 mapper 链接，并且 filter 不会链接到第一个 mapper。
```
someStream.filter(...).map(...).startNewChain().map(...);
```
3.2 取消链

不会将map算子链接到链上：
```
someStream.map(...).disableChaining();
```







参考: http://smartsi.club/2018/01/03/flink-distributed-runtime/

https://yq.aliyun.com/articles/225621

https://yq.aliyun.com/articles/64819
