---
layout: post
author: smartsi
title: FLIP-145:Flink SQL 支持窗口 TVF
date: 2022-01-28 21:59:21
tags:
  - Flink SQL

categories: Flink
permalink: flink-sql-support-sql-windowing-table-valued-function
---

## 1. 动机

本次 FLIP 的主要目的是提升 Flink 的近实时（NRT）体验。我们建议支持开窗表值函数 (TVF) 语法作为 NRT 用例的入口点。下面会解释为什么做出这个决定以及引入窗口 TVF 的好处。

通常，我们将数据处理分为实时（以秒为单位）、近实时（以分钟为单位）和批处理（> 小时）处理。Flink 是著名的流处理系统，广泛应用在实时场景。同时，社区在加强其批处理能力也付出了很多努力。有一些用户抱怨 Flink 在 NRT 场景下成本很高。我们都知道，NRT 是一个非常常见的场景。我们之前可能忽略了这个场景，所以我们要进行改进，使 Flink 成为 NRT 场景的出色引擎。

## 2. 目标

为此我们需要做什么？我们调查了许多 Flink 的流式作业，我们发现了有如下痛点：
- 学习成本：通常，用户使用窗口来进行分钟/秒粒度的统计。但是，目前 Flink SQL 中窗口并不好用，只支持窗口聚合，不支持窗口 JOIN、窗口 TopN、窗口去重。很难级联不同的算子（例如 JOIN，AGG），用户不得不学习时间属性和一些流特有的功能，例如，TUMBLE_ROWTIME。
- 性能：Flink 是一个原生的流引擎，可以提供出色的低延迟。但在某些情况下，用户不需要如此低的延迟，可以将延迟转换为吞吐量的提升。

在行业中，用户通常使用批处理引擎和调度程序来构建 NRT Pipeline。我们也调研了很多这样的使用场景，发现大多数作业都是每 15 分钟调度的累积聚合（从 0 点到当前分钟的聚合）。例如，10:00 的累积 UV 数表示从 00:00 到 10:00 的 UV 总数。因此，每日报告是一条单调递增的曲线，如下图所示：

![](1)

根据我们的研究，大多数此类场景都是由批处理作业支持，并且每 15 分钟调度一次。上游是一个 15 分钟的分区表，每个分区内包含 15 分钟内的数据。批处理作业会加载今天到目前为止的所有分区：
```sql
where ds = '${current_date}' and (hh <'${hour}' or (hh ='${hour}' and mm <= ' ${分钟}'))
```
但是这样计算会有如下问题：
- 重复计算：越早的分区会被越多的读取和计算。
- 延迟：调度器的开销增加了延迟。集群忙时资源不能保证。通常，15 分钟作业的延迟超过 30 分钟。
- 数据输出不稳定：集群资源使用高峰时，会丢失部分分区调度任务。
- 数据漂移：事件时间 14:59 的部分数据可能会写入 [15:00, 30:00) 分区。那么 [00:00, 15:00) 分区的聚合结果可能会不准确。用户可以再多读取一个分区，但这又会增加延迟。

基于上述调研，改进 NRT 的目标就是要提供一个易于使用且性能良好的 API，同时要解决用户在批处理作业和调度程序解决方案中遇到的问题。这样就可以扩展 Flink SQL 的边界，从传统的批处理中吸引用户。窗口 TVF 是我们为此目标提出的一个解决方案。我们认为通过新的 API 和改进的性能，我们具有有如下优势并能解决上述痛点：
- 减少延迟：流处理和摆脱调度程序可以节省调度时间。流处理系统可以连续处理，更及时的产生输出。
- 数据稳定输出：流式作业是一个长期运行的任务，窗口的输出永远不会丢失。
- 使用 Watermark 机制解决数据漂移和乱序问题。
- 降低学习成本并支持更丰富的开窗操作。传播常规的 window_start 和 window_end 列比传播特殊的时间属性列更容易。

## 3. 公共接口

窗口 TVF 的想法来自于 SIGMOD 2019 发布的 [One SQL To Rule Them All](https://github.com/sjf0115/PaperNotes/blob/main/One%20SQL%20to%20Rule%20Them%20All.pdf)。利用了新引入的 Polymorphic Table Functions（简称 PTF）(2016 标准 SQL 的一部分)。'One SQL' 论文中对两个窗口 TVF 进行了说明：滚动窗口和跳跃窗口。在 Flink SQL 中，我们还想为累积聚合添加一个新的类型窗口，这是 NRT 中很常见一个的场景。这需要 Calcite 的解析器支持。幸运的是，Calcite 1.25.0 版本已经支持滚动窗口和跳跃窗口 TVF。我们只需要基于它进行扩展以支持更多的窗口：累积窗口。

### 3.1 窗口 TVF

我们计划提出 4 种窗口 TVF：滚动窗口、跳跃窗口、累积窗口以及会话窗口。窗口 TVF 返回值是一个表，包含了所有数据列以及另外 window_start、window_end、window_time 3 列。window_time 用来以指示分配的窗口，是 window TVF 的一个时间属性，总是等于 'window_end - 1'。

#### 3.1.1 滚动窗口

表值函数 TUMBLE 基于时间属性列为表的每一行分配一个窗口。TUMBLE 的返回值是一个表，包含所有数据列以及另外 window_start、window_end、window_time 3 列。window_time 用来以指示分配的窗口。原始行时间属性 'timecol' 会作为窗口 TVF 中的一个常规时间戳列。所有分配的窗口都有相同的长度，这就是为什么滚动窗口有时被称为'固定窗口'的原因。TUMBLE 接收三个必需参数和一个可选参数：
```sql
TUMBLE(data, DESCRIPTOR(timecol), size [, offset ])
```
参数说明：
- data 是一个表参数，可以是有时间属性列的任何表。
- timecol 是一个列描述符，表示基于哪个时间属性列来分配滚动窗口。
- size 指定滚动窗口的长度（持续时间）。
- offset 是一个可选参数，指定从一个时刻开始滚动。

这是论文中对 Bid 表的使用示例：
```sql
> SELECT * FROM Bid;

--------------------------
| bidtime | price | item |
--------------------------
| 8:07    | $2    | A    |
| 8:11    | $3    | B    |
| 8:05    | $4    | C    |
| 8:09    | $5    | D    |
| 8:13    | $1    | E    |
| 8:17    | $6    | F    |
--------------------------

> SELECT * FROM TABLE(
   TUMBLE(TABLE Bid, DESCRIPTOR(bidtime), INTERVAL '10' MINUTES));
-- or with the named params
-- note: the DATA param must be the first

> SEL ECT * FROM TABLE(
   TUMBLE(
     DATA => TABLE Bid,
     TIMECOL => DESCRIPTOR(bidtime),
     SIZE => INTERVAL '10' MINUTES));

------------------------------------------------------
| bidtime | price | item | window_start | window_end |
------------------------------------------------------
| 8:07    | $2    | A    | 8:00         | 8:10       |
| 8:11    | $3    | B    | 8:10         | 8:20       |
| 8:05    | $4    | C    | 8:00         | 8:10       |
| 8:09    | $5    | D    | 8:00         | 8:10       |
| 8:13    | $1    | E    | 8:10         | 8:20       |
| 8:17    | $6    | F    | 8:10         | 8:20       |
------------------------------------------------------

> SELECT window_start, window_end, SUM(price)
  FROM TABLE(
    TUMBLE(TABLE Bid, DESCRIPTOR(bidtime), INTERVAL '10' MINUTES))
  GROUP BY window_start, window_end;

-------------------------------------
| window_start | window_end | price |
-------------------------------------
| 8:00         | 8:10       | $11   |
| 8:10         | 8:20       | $10   |
-------------------------------------
```

### 3.2 窗口操作

我们还希望支持基于窗口 TVF 的各种操作。这样可以使功能更加完善。

#### 3.2.1 窗口聚合

窗口聚合要求 GROUP BY 子句中包含窗口 TVF 的开始和结束列：
```sql
SELECT ...
FROM T -- 使用窗口 TVF 的表
GROUP BY window_start, window_end, ...
```
将来，如果窗口 TVF 是 TUMBLE 或 HOP，我们还可以简化 GROUP BY 子句，仅包含开始或结束列即可。

#### 3.2.2 窗口 JOIN

窗口 JOIN 要求 JOIN ON 条件中包含窗口开始时间和窗口结束时间与输入表的相等。窗口 JOIN 的语义与 DataStream 窗口 JOIN 的语义相同：
```sql
SELECT ...
FROM L [LEFT|RIGHT|FULL OUTER] JOIN R -- L 和 R 是使用窗口 TVF 的两个表
ON L.window_start = R.window_start AND L.window_end = R.window_end AND ...
```
将来，如果窗口 TVF 是 TUMBLE 或 HOP，我们还可以简化 JOIN ON 子句，仅包含窗口开始的相等即可。目前，窗口 TVF 左右输入表必须相同。这可以在将来扩展，例如，滚动窗口加入具有相同窗口大小的滑动窗口。

#### 3.2.3 窗口TopN

窗口 TopN 要求 PARTITION BY 子句包含窗口 TVF 的开始列和结束列：
```sql
SELECT ...
FROM (
   SELECT *,
     ROW_NUMBER() OVER (PARTITION BY window_start, window_end, ...
       ORDER BY col1 [asc|desc][, col2 [asc|desc]...]) AS rownum
   FROM T) -- 使用窗口 TVF 的表
WHERE rownum <= N [AND conditions]
```
将来，如果窗口 TVF 是 TUMBLE 或 HOP，我们还可以简化 PARTITION BY 子句，仅包含开始或结束列。

### 3.3 事件属性传递

正如我们上面提到的，4 种窗口 TVF 都会额外生成 3 列：window_start、window_end 以及指示分配的窗口 window_time。window_time 列是窗口 TVF 之后记录的时间属性，总是等于 'window_end - 1'。应用窗口 TVF 后，原始行时间属性 'timecol' 将成为常规时间戳列。为了通过基于窗口的操作传递时间属性，对于窗口聚合，用户只需在 GROUP BY 子句中添加 window_time 列并选择 out window_time 列即可。对于窗口 JOIN 和窗口 TopN，用户只需要选择 window_time 列，不需要添加到 JOIN ON 和 PARTITIONED BY 子句中。结果 window_time 列仍然是一个时间属性，可用于后续基于时间的操作，例如间隔 JOIN 和排序或窗口聚合。 例如：
```sql
-- window_time needs to be added to GROUP BY and the output window_time is still a time attribute after window aggregation
> SELECT window_start, window_end, window_time, SUM(price)
  FROM TABLE(
    TUMBLE(TABLE Bid, DESCRIPTOR(bidtime), INTERVAL '10' MINUTES))
  GROUP BY window_start, window_end, window_time;

-- L.window_time and R.window_time are still time attributes after window join
> SELECT L.window_time, R.window_time, ...
  FROM windowed_view1 AS L JOIN windowed_view2 AS R
  ON L.user_id = R.user_id AND L.window_start = R.window_start AND L.window_end = R.window_end;

-- window_time is still a time attribute after window TopN
> SELECT window_time, ...
  FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY window_start, window_end ORDER BY total_price DESC) as rank
    FROM trd_itm_ord_mm
  ) WHERE rank <= 100;
```

## 4. 示例

例如，如果我们有一个订单流，并且我们想要获取从 00:00 到当前 10 分钟的一些累积聚合，包括商品的销售、每件商品的不同买家、商品卖家的不同买家。 然后我们要获取从 00:00 到当前 10 分钟内销售额 Top100 的商品。可以用下面的复杂作业来说明，其中包含了累积窗口、窗口聚合、窗口 JOIN 和窗口 TopN 的使用：
```sql
CREATE TEMPORARY VIEW trd_itm_ord_mm
SELECT item_id, seller_id, window_start, window_end, sales, item_buyer_cnt, slr_buyer_cnt
FROM (
    SELECT item_id, seller_id, window_start, window_end, SUM(price) as sales, COUNT(DISTINCT user_id) as item_buyer_cnt
    FROM TABLE (
        CUMULATE(TABLE orders, DESCRIPTOR(pay_time), INTERVAL '10' MINUTES, INTERVAL '1' DAY)
    )
    GROUP BY item_id, seller_id, window_start, window_end;
) a
LEFT JOIN ( -- using window join to enrich the buyer count of the shop from 00:00 to current minute
    SELECT seller_id, window_start, window_end, COUNT(DISTINCT user_id) as slr_buyer_cnt
    FROM TABLE (
        CUMULATE(TABLE orders, DESCRIPTOR(pay_time), INTERVAL '10' MINUTES, INTERVAL '1' DAY)
    )
    GROUP BY seller_id, window_start, window_end;
) b
ON a.seller_id = b.seller_id AND a.window_start = b.window_start AND a.window_end = b.window_end;

INSERT INTO item_top100_cumulate_10min
SELECT *
FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY window_start, window_end ORDER BY total_price DESC) as rank
    FROM trd_itm_ord_mm
) WHERE rank <= 100;
```

## 5. 实现

在这不会深入探讨实现和优化的细节，但会说明基本的实现方法：
- 需要先将 Calcite 升级到 v1.25+。
- 不会引入任何新的逻辑节点，因为没有新的关系代数。
- 会引入新物理节点，用于支持在 window_start、window_end 列的窗口 JOIN、窗口聚合、窗口排名。
- 引入一个 MetadataHandler 来推断窗口开始和窗口结束列。此元数据用来从逻辑 JOIN/聚合/排序转换为物理窗口 JOIN/聚合/排序。如果窗口 JOIN/aggregate/rank 的输入节点是窗口 TVF，我们可以将 TVF 合并到窗口节点中。这样窗口分配就在同一个算子中，这可以帮助我们通过重用窗口状态来获得更好的性能，减少记录 Shuffle。例如，对于累积窗口，可以将窗口 [00:00, 01:00) 的状态用作窗口 [00:00, 02:00) 的基础状态。
- 复用 WindowOperator 的现有实现（即窗口聚合算子）。
- 支持窗口算子的小批量、局部全局、不同分割优化，以获得更好的性能。目前，它们仅在非窗口聚合中支持。

## 6. 性能优化

性能优化是一项长期计划。由于窗口操作是基于窗口数据，这是一个无限的有界数据序列。此类作业的 SLA 通常是窗口大小。所以我们可以利用窗口大小的持续时间来缓冲数据，预先聚合，减少对状态的操作，提高吞吐量。从长远来看，窗口操作可以在连续批处理模式下工作。数据源可以缓冲输入数据，直到特定窗口的所有数据都到达（通过 Watermark），然后数据源将窗口数据发送给下游算子。所有下游算子都是批处理算子，可以在每个窗口数据准备好时进行调度，不需要状态机制。下游算子处理有界窗口数据并以批处理方式输出窗口结果。这意味着我们可以利用现有的批处理算子实现和优化。这种方法对吞吐量非常有效，因为我们不需要访问状态。但是，这被几个运行时构建块所阻止，例如连续批处理模式、流和批处理算子的组合等......

因此，短期内，我们不得不使用流式算子并以流的模式工作。优化思路是尽可能多地缓冲批数据。与当前无界聚合的 mini-batch 机制类似，缓冲的批处理数据只有在 (1) 表示窗口结束的 Watermark 到达，或 (2) 用于缓冲的保留内存已满，或 (3) 检查点 barrier 到达时才能触发。我们保留一个预定义的内存空间（类似于批处理算子从 MemoryManager 分配内存）用于缓冲数据。缓冲的数据可以是记录或预先聚合的累加器，这具体取决于算子。用户可以调整保留内存大小的配置。通过这种方式，我们可以在访问状态之前聚合尽可能多的数据以提升吞吐量。这将比无界聚合上的 mini-batch 更有效，因为我们可以缓冲更多数据。另一方面，由于我们增量计算输入数据，而不是一次计算整个窗口数据，因此在关闭窗口时计算量会减少很多。因此，从窗口关闭到窗口结果发出的延迟会更短，集群 CPU 负载会更加平滑和稳定。

对于重叠的窗口，例如 HOP, CUMULATE，我们可以使用共享窗格状态来减少状态大小和操作。 例如，窗口大小为 1 小时，滑动步长为 10 分钟的跳跃窗口，我们可以每 10 分钟存储窗格大小的状态，这样可以减少存储大量重复记录以进行窗口连接。另一个例子，以 1 天最大窗口大小和 1 小时步长累积，窗口 [00:00, 01:00) 的状态可以用作窗口 [00:00, 02:00) 的基本状态，这可以 大大减少状态大小和操作。

## 7. 兼容性、弃用和迁移计划

## 8. 未来的工作

### 8.1 简化多态表函数语法

正如邮件列表中所讨论的，当前的 PTF 语法很冗长，如果我们可以删除 TABLE() 关键字，那就太好了，这将更容易被用户接受。Oracle 和 SQL Server 都不需要这样的关键字。一个简化的查询是这样的：
```sql
SELECT *
FROM TUMBLE(inputTable, DESCRIPTOR(timecol), INTERVAL '10' MINUTE);
```

### 8.2 支持带窗口 TVF 的计数窗口

Table API 支持计数窗口，但目前 SQL 还不支持。使用新的窗口 TVF 语法，我们将来还可以为计数窗口引入新的窗口函数。例如，以下 TUMBLE_ROW 以 10 行计数间隔分配窗口：
```sql
SELECT *
FROM TABLE(
   TUMBLE_ROW(
     data => TABLE inputTable,
     timecol => DESCRIPTOR(timecol),
     size => 10));
```

### 8.3 探索多态表函数的更多能力

正如我们所看到的，在未来，也许我们可以以标准的 PTF 方式支持 SQL 中的以下特性。
- Table API (FLIP-29) 中支持的高级操作，例如 drop_columns，用户定义的表聚合
- 用户自定义 JOIN 算子
- 一个快捷的 TopN 函数
- 重新分配 Watermark？
- 重新分区数据，类似于 Hive DISTRIBUTED BY 语法的功能。


[1] https://github.com/sjf0115/PaperNotes/blob/main/One%20SQL%20to%20Rule%20Them%20All.pdf

原文:[FLIP-145: Support SQL windowing table-valued function](https://cwiki.apache.org/confluence/display/FLINK/FLIP-145%3A+Support+SQL+windowing+table-valued+function#FLIP145:SupportSQLwindowingtablevaluedfunction-Motivation)
