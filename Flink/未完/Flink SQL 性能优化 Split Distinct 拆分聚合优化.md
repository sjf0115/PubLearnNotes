---
layout: post
author: sjf0115
title: Flink SQL 性能优化 Split Distinct 拆分聚合优化
date: 2022-10-16 10:02:21
tags:
  - Flink

categories: Flink
permalink: flink-sql-tuning-split-distinct-aggregate
---

> Flink 版本：1.13.5

## 1. 原理

Local-Global 优化对于一般的 SUM、COUNT、MAX、MIN、AVG 等普通聚合都能有效地消除数据倾斜，但是对于 DISTINCT 去重聚合收效不明显。例如，我们想要分析今天有多少用户登录，如下 SQL 语句：
```sql
SELECT day, COUNT(DISTINCT user_id)
FROM T
GROUP BY day
```
如果 DISTINCT Key，即 user_id 值分布比较稀疏，COUNT DISTINCT 并不会减少多少数据记录。即使启用了 Local-Global 两阶段聚合优化，也没有多大帮助。因为 DISTINCT KEY 的去重率不高，累加器中仍然包含了几乎所有的原始数据记录，即 Local 聚合之后并没有减少多少数据记录。Global 聚合依然会成为瓶颈（大部分数据记录还是由一个任务处理，即在同一天中）。

为了解决 COUNT DISTINCT 的热点问题，通常需要手动改写为两层聚合，即增加按 Distinct Key 取模的打散层：
- 第一层聚合按 Group Key 以及 Distinct Key 取模分桶进行打散。Distinct Key 使用 `HASH_CODE(DISTINCT_KEY) % BUCKET_NUM` 取模打散，分成 BUCKET_NUM 个桶。其中 BUCKET_NUM 默认为 1024，可以通过 `table.optimizer.distinct-agg.split.bucket-num option` 进行配置。
- 第二层聚合由原始 Group Key 分组，并使用 SUM 聚合来自不同桶的 COUNT DISTINCT 值。因为相同的 Distinct Key 只会在相同的桶中计算，所以转换是等价的。分桶充当附加 Group 的角色来分担 Group 中热点的负担。分桶使作业具有可伸缩性来解决不同聚合中的数据倾斜/热点。

拆分 DISTINCT 聚合后，上述查询改写为如下查询:
```sql
SELECT day, SUM(cnt)
FROM (
    SELECT day, COUNT(DISTINCT user_id) AS cnt
    FROM T
    GROUP BY day, MOD(HASH_CODE(user_id), 1024)
)
GROUP BY day
```
> day 为 Group Key，user_id 为 DISTINCT Key

下图展示了拆分 DISTINCT 聚合如何提高性能（假设颜色表示 days，字母表示 user_id）：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-tuning-split-distinct-aggregate-1.png?raw=true)

注意：上面是可以从这个优化中受益的最简单的示例。除此之外，Flink 还支持拆分更复杂的聚合查询，例如使用不同 DISTINCT Key 的多个 DISTINCT 聚合（例如 `COUNT(DISTINCT a), SUM(DISTINCT b)` ），可以与其他非 DISTINCT 聚合（例如 SUM、MAX、MIN、COUNT ）一起使用。

## 2. 适用场景

在使用 COUNT DISTINCT，但聚合节点性能无法满足要求时可以开启拆分 DISTINCT 优化。数据量不大的情况下，不建议使用拆分 DISTINCT 优化方法。拆分 DISTINCT 优化会自动打散成两层聚合，会引入额外的网络 Shuffle，在数据量不大的情况下，浪费资源。

> 需要注意的是，目前拆分 DISTINCT 优化不支持用户自定义的 AggregateFunction 的聚合。此外，该功能在 Flink 1.9.0 版本及以上版本才支持。

## 3. 启用

拆分 DISTINCT 优化默认是关闭的，您需要在作业中的配置如下参数：
```java
Configuration configuration = tEnv.getConfig().getConfiguration();
// 开启 MiniBatch
configuration.setString("table.exec.mini-batch.enabled", "true");
configuration.setString("table.exec.mini-batch.allow-latency", "1 s");
configuration.setString("table.exec.mini-batch.size", "5000");
// 开启拆分 Distinct 优化
configuration.setString("table.optimizer.distinct-agg.split.enabled", "true");
```
判断是否生效，可以通过 Web UI 中观察最终生成的拓扑图，是否由原来一层的聚合变成了两层的聚合，其中一个 partialFinalType 为 PARTITAL，另一个为 FINAL：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-sql-tuning-split-distinct-aggregate-2.png?raw=true)

## 4. 示例

![SplitDistinctAggExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/tuning/skew/SplitDistinctAggExample.java)
