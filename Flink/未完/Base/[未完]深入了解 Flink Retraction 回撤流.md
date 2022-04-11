
### 1. 简介

Retraction 是流式数据处理中撤回过早下发（Early Firing）数据的一种机制，类似于传统数据库的 Update 操作。级联的聚合等复杂 SQL 中如果没有 Retraction 机制，就会导致最终的计算结果与批处理不同，这也是目前业界很多流计算引擎的缺陷。

'撤回'是数据流的重要组成部分，用于修正流中提前触发的结果。提前触发在流式处理场景中被广泛使用，例如，'无窗口'或无限流聚合和流内连接、窗口（提前触发）聚合和流-流内部连接。如 Streaming 102 [1] 中所述，主要在如下两种情况下需要撤回：
- 更新 Keyed Table：Key 是 Source Table 上的主键（PK）或者是聚合中的 groupKey/partitionKey
- 动态窗口（例如，会话窗口）合并：窗口合并时新值可能会在多个先前的窗口中进行替换。

据我们所知，流中提前触发结果的撤回在以前从未得到实际解决。在这个提案中，我们开发了一个撤回解决方案，并解释了如何使用这种方案解决'更新 Keyed Table'的问题。这个解决方案也可以很容易地扩展到动态窗口合并上，因为撤回的关键部分：如何修正提前触发的结果，这在不同场景下中是相同的。

为简单起见，在这篇文章中我们使用'聚合'和'JOIN'来表示无限流的聚合和无限流与流的 JOIN。如果撤回发生在窗口物化输出之前，那么这个解决方案也可以适用于窗口（提前触发）聚合和窗口流 JOIN。如果撤回发生在窗口物化输出之后，那么实现撤回的解决方案代价会非常大。在这种情况下，需要将窗口状态保留到永久存储中。在实践中，我们通常会尝试通过调整窗口状态生命周期（保留窗口状态多长时间）和延迟到达/更新 QoS（易出错的用户能容忍）来尽量减轻在窗口物化后撤回的影响。还需要注意的是，窗口聚合和窗口流 JOIN 如果没有在提前触发模式下执行并且窗口的结果还没有输出，那么不需要撤回。

### 2. 101 - 了解问题

考虑如下统计词频分布的 SQL：
```sql

SELECT
  cnt, COUNT(cnt) AS freq
FROM (
  SELECT word, COUNT(*) AS cnt
  FROM words_table
  GROUP BY word
)
GROUP BY cnt
```
假设输入数据是：

| word  |
| :---- |
| Hello |
| World |
| Hello |

则经过上面的计算后，预期的输出结果应该是：

| cnt   | freq  |
| :---- | :---- |
| 1     | 1     |
| 2     | 1     |

但与批处理不同，流处理的数据是一条条到达的，理论上每一条数据都会触发一次计算，所以在处理了第一个 Hello 和第一个 World 之后，词频为 1 的单词数已经变成了 2：

![](1)

此时再处理第二个 Hello 时，如果不能修正之前的结果，Hello 就会在词频等于 1 和词频等于 2 这两个窗口下被同时统计，显然这个结果是错误的，这就是没有 Retraction 机制带来的问题。




我们以更新 Keyd Table 为例来说明为什么需要对之前输出的结果进行撤回。在这个例子中，我们首先计算每个单词的出现次数，然后再计算次数对应的单词个数。如表 1 所示，假设初始阶段 count:1 的频率为 2，count:2 的频率为 1。

![](1)

### 3. 解决方案

从上面的例子中，我们知道一些算子需要额外的消息来修正上游的提前触发结果。为了帮助这些算子，我们添加了额外的信号来指示来自上游表的数据是对新 Key 的'添加'还是对现有 Key '替换'新值。对于添加新 Key，我们只需要发送一个数据并将其标记为 Accumulate 消息（数据的附加属性）。对于替换新值，我们需要发送两个数据，一个是带有旧值的 Retract 消息，另一个是带有新值的 Accumulate 消息。

为了抽象模型，对导致撤回场景的表进行分类，主要涉及源表，聚合后的表，JOIN 后的表，分类如下所示：

| Table | Table 类型 | 触发条件 |
| :------------- | :------------- | :------------- |
| Source Table | Replace Table | 带有主键的 Source Table |
| Source Table | Append Table | 其他条件 |
| 聚合后的 Table | Replace Table | 无限流 Keyed 聚合(无限流 Group 聚合) |
| 聚合后的 Table | Replace Table | 提前触发的窗口聚合 |
| 聚合后的 Table | Replace Table | 没有 Key 的无限流聚合 |
| 聚合后的 Table | Append Table | 没有提前触发的窗口聚合(推断：在窗口完成之前没有输出或者在窗口结果输出后没有延迟到达) |
| JOIN 后的 Table | Replace Table | JOIN Key 是左表或者右表的主键 |
| JOIN 后的 Table | Append Table | 其他条件 |

只有 Replace Table 才可以生成 Retract 消息，上表展示了 Replace Table 的一些示例。keyed 聚合的结果表以及对具有 PK 的表的表扫描通常都是 Replace Table。如果 JOIN Key 是左表或右表的键，那么 JOIN 的结果表也是 Replace Table。通常，如果表 Schema 中包含 PrimaryKey(PK) 定义（在创建表时给出的分组/分区键或者是传统主键），则表被视为 Replace Table。但是也有两个例外：
- 对于带有 PK 的表，当用户声明输入数据始终具有唯一的主键时（因此永远不会发生更新）。在这种情况下，这些表不是 Replace Table 而是 Append Table，尽管它们都有 PK 定义
- 没有 PK 的表本身就存在删除消息，那么它也可以生成 Retract 消息。

不能独立完成结果细化的算子需要 Retract 消息。这通常是因为旧记录和新记录具有不同的 Key，算子无法在没有 Retract 消息的情况下撤回旧记录。接下来，我们为算子的每个输入引入一个重要的属性，NeedRetract。这个属性表示算子输入是否需要来自上游的撤回消息。需要注意的是，这个属性是针对每个输入的，而不是针对每个算子的。虽然大多数算子只有一个输入，但有些算子可能有多个输入（例如，join、union），并且 NeedRetract 的属性可能因同一算子的不同输入而异。

算子输入的 NeedRetraction 属性

| 算子 | 是否需要回撤 | 条件 |
| :------------- | :------------- | :------------- |
| Aggregate 输入 | Y | 任意 |
| 流 JOIN 输入 | N | JOIN Key 与上游的主键一样 |
| 流 JOIN 输入 | Y | 其他 |
| TableInsert Sink 输入 | Y | 该 Table 的消费者需要撤回 |
| TableInsert Sink 输入 | N | 其他 |


需要撤回的算子比较少。如上表所示，到目前为止，我们看到的只有 JOIN、Aggregate 和 SinkTable 算子需要撤回。在不同的 Key 上对数据进行重新分组/重新分区时，旧数据和新数据的结果总是有不同的 Key。在分布式系统中，数据在不同的节点上进行存储和计算。因此，仅通过一条消息是不可能完成细化的。因此，我们必须需要一条 Accumulate 消息来添加带新 Key 的新数据，并需要一条 Retract 消息来删除另一个不同的 Key 的旧数据。因此，对于 Keyed 聚合，它只有一个输入，并且这个输入总是需要撤回的。在大多数情况下，内连接的输入需要撤回。只有当 JOIN Key 与上游 Replace Table 的 PK 完全相同时，内连接输入不需要撤回。这是因为来自上游的新旧数据始终具有相同的 Key，并将存储在相同的内存/状态地址下。用给定 Key 的新数据替换旧数据将完成整个结果细化。如果 Sink Table 明确声明需要撤回，例如它的下游有聚合或 JOIN 操作，那么 Sink TableInsert 的输入需要撤回。

解决撤回问题的一种简单方法是让所有 Replace Table 生成 Retract 消息，并且所有具有 NeedRetract 输入的算子都需要处理 Retract 消息。但是，生成和处理 Retract 消息是有代价的：
- 如果 Replace Table 总是生成 Retract 消息，会导致网络流量翻倍；
- 对于大多数聚合，通常处理撤回的执行计划要比不处理撤回的执行计划代价更大。例如，在一个 MAX 聚合中，如果需要处理撤回，则聚合函数必须记住所有记录，否则当 Retract 消息要求撤回当前 MAX 值时，系统将无法选出新的 MAX 值（如果此 MAX 多次出现，则为相同的 MAX 值，或者整个过去记录中的第二个 MAX 值）。 因此，选择新 MAX 值的存储和计算成本代价比较大。

为了实现最小的存储/计算/网络成本，我们必须让优化器检查整个查询计划并回答如下问题：
- Q1：算子是否需要处理来自输入的 Retract 消息。
- Q2：算子是否会发送（生成或转发）Retract 消息。

我们接下来定义一个算子属性，即累加模式，表示累加是如何工作的。目前有两种累加模式：累加模式（AccMode）和累加和撤回模式（AccRetractMode）。在 AccMode 模式下，算子的所有输入只是简单地累加到现有状态并生成一个累加消息给下游，而在 AccRetractMode 模式下，除了发送累加消息之外，算子还可以生成或转发额外的撤回消息。需要注意的是，只有 Replace Table 才能在 AccRetractMode 模式下工作。累积模式回答了上面第二个问题 Q2。第一个问题 Q1 的答案实际上很简单，如果上游的输入在 AccRetractMode 下工作，则期望算子处理 Retract 消息。

我们通过给出 Flink 撤回解决方案的主要概念来完成本节。我们将在下一节中提供设计细节。给定一个查询计划，可以推导出一个算子的结果表的类型。除了表类型，我们还可以为所有算子的每个输入生成 NeedRetract 属性。我们将这些信息提供给查询计划优化器。优化器会检查整个查询计划来决定每个算子的累加方式（最终回答 Q1 和 Q2 问题），从而将算子转化为最优计划。

### 4. 设计细节

在本节中，我们将解释所提出的撤回解决方案的设计细节：

(1) 如何决定每个算子的累加模式：我们首先添加一个 RetractionRule。在优化阶段，RetractionRule 会遍历整个查询计划，以生成算子每个输入的结果表类型和 NeedRetract 属性。完成此步骤后，会从 Sink 到 Source 扫描查询计划树，当找到 NeedRetract 输入时，它会检查所有上游表，看是否有 Replace Table。如果找到任何匹配对，优化器会将 Replace Table 和 NeedRetract 输入之间的算子设置为 AccRetractMode 模式，并为每个算子选择适当的运行时执行计划（不同的算子以不同的方式生成、转发和处理撤回消息，如下面所描述的）。下图展示了三个不同的查询计划以及每个算子的累积模式。

![](2)

![](3)

(2) 生成 Retract 消息的算子（在 AccRetractMode 下）：不同的算子有不同的方式来生成或转发 Retract 消息
- 带有 PK 的 Source：如下图所示，当 Source 指定 PK 时，我们需要额外增加一个 keyBy 和一个生成 Retract 消息的 flatMap 函数。
- Keyed 聚合：当在 AccRetractMode 下聚合时，我们必须使用可以生成 Retract 消息的特定函数。当接收到来自上游的消息时，会首先从现有状态中获取旧值，然后将新值累加到状态中。如果新值与旧值不同，会生成一条 Accumulate 消息和 Retract 消息。

(3) 使用 Retract 消息的算子（当它的上游处于 AccRetractMode 时）：不同的算子有不同的方式来消费 Retract 消息
- Keyed 聚合：聚合将检查消息类型并执行 retract() 函数以细化结果。需要注意的是，这对于无限或'无窗口'聚合始终有效。窗口聚合（groupbyWindow 或 overWindow）仅在在提前触发模式下执行或窗口已经发出时才需要。如果在提前触发模式下没有执行累加并且没有发出窗口，则不需要撤回。
- Join：对于每个输入，JoinFunction 将历史 RecordMap 以 (Record->Counter) 的格式存储在 MapState 中。当接收到当前记录时，会根据消息属性更新 MapState。如果消息是 Retract 消息，Counter 将减一，如果消息是 Accumulate 消息，则加一。MapState 更新后，当前记录与另一个表中的记录进行 JOIN，并在发送到下游时保持 Retract 或 Accumulate 属性。
- sinkTable：我们会在 Sink Table 中保留消息的 Retract 或 Accumulate 属性（仅当该表的消费者需要 Retract 消息时）。

(4) 其他算子（AccMode 或 AccRetractMode）：除上述算子外，所有其他算子都会透明地处理消息并传递到下游，不改变它们的消息类型（Accumulate 或 Retract）。例如：
- Select：不区分 Retract 或 Accumulate 属性，将属性传递给下游
- Filter：不区分 Retract 或 Accumulate 属性，将属性传递给下游（如果记录能满足条件）

3.1 回撤流
在Flink中，Group by会产生回撤流。何谓回撤流？可以将回撤流理解为可以更新历史数据的流。

因为已经发往下游的数据是追不回来的，因此更新历史消息并不是将发完下游的历史数据进行更改。

当得知某个key对应的数据已经存在的情况下，如果该key对应的数据再次到来，会生成一条delete数据和一条新的insert消息发完下游。

3.2 写乱序
既然回撤流有两个操作：delete和insert。当单个Task写单个Shard的并发数比较大时，可能会出现写数据乱序。

即，应当是先delete再insert。发生乱序时可能先处理了insert，再处理了delete，也就丢失了数据。



https://ata.alibaba-inc.com/articles/97246?spm=ata.23639746.0.0.68e851a38KBd4E
https://ata.alibaba-inc.com/articles/94607
https://ata.alibaba-inc.com/articles/120955?spm=ata.23639746.0.0.68e851a38KBd4E











-
- https://blog.csdn.net/u013411339/article/details/119974387?spm=1001.2101.3001.6650.15&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7Edefault-15.highlightwordscore&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7Edefault-15.highlightwordscore
