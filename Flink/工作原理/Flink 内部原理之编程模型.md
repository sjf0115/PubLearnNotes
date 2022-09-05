---
layout: post
author: sjf0115
title: Flink 内部原理之编程模型
date: 2017-12-29 12:54:01
tags:
  - Flink

categories: Flink
permalink: flink-programming-model
---

> Flink 1.8.0

### 1. 抽象层次

Flink 提供了不同级别的抽象层次来开发流处理和批处理应用程序：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-programming-model-1.png?raw=true)

最低级别的抽象只是提供有状态的数据流。通过 Process Function 集成到 DataStream API 中。它允许用户不受限制的处理来自一个或多个数据流的事件，并可以使用一致的容错状态。另外，用户可以注册事件时间和处理时间的回调函数，允许程序实现复杂的计算。

在实际中，大多数应用程序不需要上述描述的低级抽象，而是使用像 DataStream API (有界/无界流)和 DataSet API (有界数据集)核心 API 进行编程。这些核心 API 提供了用于数据处理的通用构建模块，如用户指定的各种转换，连接，聚合，窗口，状态等。在这些 API 中处理的数据类型被表示为对应编程语言中的类。

低级别的 Process Function 与 DataStream API 集成在一起，使得可以对特定操作使用较低级别的抽象接口。DataSet API 为有限数据集提供了额外的原语(primitives)，如循环/迭代。

Table API 是以表为核心的声明式 DSL，可以动态地改变表(当表表示流数据时)。Table API 遵循(扩展的)关系模型：每个表都有一个schema(类似于关系数据库中的表)，对应的 API 提供了类似的操作，如 select，project，join，group-by，aggregate 等。Table API 程序声明性地定义了如何在逻辑上实现操作，而不是明确指定操作实现的具体代码。尽管 Table API 可以通过各种类型的用户自定义函数进行扩展，它比核心 API 表达性要差一些，但使用上更简洁(编写代码更少)。另外，Table API 程序也会通过一个优化器，在执行之前应用优化规则。可以在表和 DataStream / DataSet 之间进行无缝转换，允许程序混合使用 Table API 和 DataStream 和 DataSet API 。

Flink 提供的最高级抽象是 SQL。这种抽象在语法和表现力方面与 Table API 类似，但是是通过 SQL 查询表达式实现程序。SQL 抽象与 Table API 紧密交互，可以在 Table API 中定义的表上执行。

> 注意：在 Flink 1.9.0 版本，Flink 实现了新的[技术架构](https://smartsi.blog.csdn.net/article/details/124159459)

### 2. 程序与数据流

Flink 程序的基本构建块是流和转换操作。从概念上讲，流是数据记录(可能是永无止境的)流，而转换是将一个或多个流作为输入产生一个或多个输出流。执行时，Flink 程序被映射到由流和转换算子组成的流式数据流。每个数据流从一个或多个 Source 开始，并在一个或多个 Sink 中结束。数据流类似于有向无环图(DAG)。尽管通过迭代构造允许特殊形式的环，但是为了简单起见，大部分都会如下描述：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-programming-model-2.png?raw=true)

程序中的转换与数据流中的算子通常是一一对应的。然而，有时候，一个转换可能由多个转换算子组成。

### 3. 并行数据流图

Flink 中的程序本质上是分布式并发执行的。在执行过程中，一个流可能会有一个或多个分区，相应的每个算子也会有一个或多个子任务。算子子任务之间相互独立，并且在不同的线程中执行，甚至有可能在不同的机器或容器上执行。算子子任务的数量等于算子的并发数。流的并发数总是等于产生算子的并发数。同一程序的不同算子可能具有不同的并发级别。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-programming-model-3.png?raw=true)

在两个算子之间的流可以以一对一模式或重新分发模式传输数据:
- 一对一流(例如上图中的 Source 和 map 算子之间的流)保留了元素的分区和排序。这意味着将会在 map 算子的子任务[1]中看到在 Source 算子的子任务[1]中产生的相同元素，并且具有相同的顺序。
- 重分发流(例如上图的的 map() 和 keyBy()/window()/apply() 之间，以及在 keyBy()/window()/apply() 和 Sink 之间的数据流)改变了流的分区。每个算子子任务根据所选的转换操作将数据发送到不同的目标子任务。比如 keyBy() (根据key的哈希值重新分区)，broadcast()，或者 rebalance() (随机重新分区)。在重新分配交换中，只会在每对发送与接受子任务(比如，map() 的子任务[1]与 keyBy()/window()/apply() 的子任务[2])中保留元素间的顺序。在上图的例子中，尽管在子任务之间每个 key 的顺序都是确定的，但是由于程序的并发引入了不确定性，最终到达 Sink 的元素顺序就不能保证与一开始的元素顺序完全一致。

### 4. 窗口

聚合事件(比如计数、求和)在流上的工作方式与批处理不同。比如，不可能对流中的所有元素进行计数，因为通常流是无限的(无界的)。相反，流上的聚合(计数，求和等)需要由 窗口来划定范围，比如在最近5分钟内计算，或者对最近100个元素求和。窗口可以是时间驱动的 (比如：每30秒）或者数据驱动的(比如：每100个元素)。窗口有不同的类型，比如滚动窗口(没有重叠)，滑动窗口(有重叠)，以及会话窗口(由不活动的间隙所打断)：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-programming-model-4.png?raw=true)

更多的窗口示例可以在这篇[博客](https://smartsi.blog.csdn.net/article/details/126554021)中找到。

### 5. 时间

当提到流程序(例如定义窗口)中的时间时，你可以参考不同的时间概念：
- 事件时间是事件创建的时间。通常由事件中的时间戳描述。Flink 通过时间戳分配器访问事件时间戳。
- 摄入时间是事件进入 Flink 数据流源(source)算子的时间。
- 处理事件是每一个执行基于时间操作算子的本地时间。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-programming-model-5.png?raw=true)

更多关于如何处理时间的详细信息可以查看[事件时间](https://smartsi.blog.csdn.net/article/details/126554454)文档.

### 6. 有状态操作

尽管数据流中的很多操作一次只查看一个独立的事件(比如事件解析器)，但是有些操作会记录多个事件间的信息(比如窗口算子)。这些操作被称为有状态的。

有状态操作的状态保存在一个可被视为嵌入式键值对存储中。状态与由有状态算子读取的流一起被严格地分区与分布(distributed)。因此，只有在应用 keyBy() 函数之后，才能访问 KeyedStreams 上的键/值对状态，并且仅限于与当前事件 key 相关联的值。对齐流和状态的 key确保了所有状态更新都是本地操作，保证一致性，而没有事务开销。这种对齐还使得 Flink 可以透明地重新分配状态与调整流的分区。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-programming-model-6.png?raw=true)

### 7. 容错性检查点

Flink 组合使用流重放与检查点实现了容错。检查点与每一个输入流以及每一个算子对应的状态所在的特定点相关联。一个流数据流可以可以从一个检查点恢复出来，其中通过恢复算子状态并从检查点重放事件以保持一致性(一次处理语义)。检查点时间间隔是在恢复时间(需要重放的事件数量)内消除执行过程中容错开销的一种手段。

### 8. 批处理操作

Flink 将批处理程序作为流处理程序的一种特殊情况来执行，只是流是有界的(有限个元素)。在内部 DataSet 被视为数据流。因此上述适用于流处理程序的概念同样适用于批处理程序，除了一些例外：
- 批处理程序的容错不使用检查点。通过重放全部流来恢复。这是可能的，因为输入是有限的。这使恢复的成本更高，但是使常规处理更便宜，因为它避免了检查点。
- DataSet API 中的有状态操作使用简化的 in-memory / out-of-core 数据结构，而不是键/值索引。
- DataSet API 引入了特殊的同步(基于 superstep 的)迭代，而这种迭代仅仅能在有界流上执行。
