ClickHouse 可能有一个独特的功能——聚合状态（除了聚合函数外）。你可以参考 AggregatingMergeTree 引擎和 State 组合的文档。

## 1. 前言

简而言之，许多数据库使用概率数据结构，例如 HyperLogLog（简称 HLL）来实现唯一/去重计算，你可以在 Spark、ElasticSearch、Flink、Postgres、BigQuery 和 Redis 等服务中看到它的效果。但通常你只能在聚合函数中使用它一次，例如查询每月去重用户数——得到一个数字，这样就满足了。由于无法直接访问 HLL 结构的内部表示形式(HLL 是概率性数据结构)，因此无法复用预聚合或部分聚合的数据。而在 ClickHouse 中，你可以做到这一点，因为 HLL 结构具有一致性。

ClickHouse 的速度非常快，其设计理念是处理原始数据而不是预聚合数据。但是让我们做个实验：假设我们需要计算上月去重用户相关指标。

## 2. 核心思路

思路是：按日预聚合数据，然后汇总所有结果。这就是所谓的分桶法——之后你就可以只汇总最近 30 天的测量值来计算上个月的统计数据，或者只汇总最近 7 天测量值来计算上周的统计数据。

创建预聚合表：
```sql
create table events_unique (
  date Date,
  group_id String,
  client_id String,
  event_type String,
  product_id String,
  value AggregateFunction(uniq, String)
) ENGINE = MergeTree(date, (group_id, client_id, event_type, product_id, date), 8192);
```
这里我将聚合列声明为 `AggregateFunction(uniq, String)`。我们关注的是基于 String 列计算的去重指标（为了进一步优化，后续可考虑使用 FixedString 或二进制数据）。

向预聚合表插入数据：
```sql
INSERT INTO events_unique
SELECT date, group_id, client_id, event_type, product_id, uniqState(visitor_id) AS value
FROM events
GROUP BY date, group_id, client_id, event_type, product_id;
```
进行冒烟测试，确认其可以正常运行：
```sql
SELECT uniqMerge(value)
FROM events_unique
GROUP BY product_id;
```
现在比较原始表与预聚合表的查询性能。基于原始表查询如下所示：
```sql
SELECT uniq(visitor_id) AS c
FROM events
WHERE client_id = 'aaaaaaaa'
   AND event_type = 'click'
   AND product_id = 'product1'
   AND date >= '2017–01–20'
   AND date < '2017–02–20';

┌──────c─┐
│ 457954 │
└────────┘
1 rows in set. Elapsed: 0.948 sec. Processed 13.22 million rows, 1.61 GB (13.93 million rows/s., 1.70 GB/s.)
```
基于预聚合表查询如下所示：
```sql
SELECT uniqMerge(value) AS c
FROM events_unique
WHERE client_id = 'aaaaaaaa'
   AND event_type = 'click'
   AND product_id = 'product1'
   AND date >= '2017–01–20'
   AND date < '2017–02–20';

┌──────c─┐
│ 457954 │
└────────┘
1 rows in set. Elapsed: 0.050 sec. Processed 39.39 thousand rows, 8.55 MB (781.22 thousand rows/s., 169.65 MB/s.)
```
结果表明，我们的处理时间缩短到 1/20。

在实践中，将物化视图与 AggregatingMergeTree 引擎结合使用，会比使用单独的表更方便。

## 3. 总结

ClickHouse 允许您在数据库内部存储聚合状态，而不仅限于应用程序层面，这为性能优化和新用例带来了更多可能性。更多细节请参阅 AggregatingMergeTree 引擎的详细文档（包含更多 uniqMerge 与 uniqState 示例）。

> []原文](https://altinity.com/blog/2017/7/10/clickhouse-aggregatefunctions-and-aggregatestate)
