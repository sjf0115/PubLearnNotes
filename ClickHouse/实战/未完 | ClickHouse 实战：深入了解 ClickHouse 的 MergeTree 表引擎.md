MergeTree 家族引擎是用于高负载任务的最通用和功能强大的表引擎。这些引擎的共同特性是快速的数据插入，并随后的后台数据处理。MergeTree 家族的引擎支持数据复制（与 Replicated* 版本的引擎）、分区、次级数据跳过索引以及其他在其他引擎中不支持的特性。

MergeTree 引擎目前有如下几种：
- MergeTree
- ReplacingMergeTree
- SummingMergeTree
- AggregatingMergeTree
- CollapsingMergeTree
- VersionedCollapsingMergeTree
- GraphiteMergeTree
- CoalescingMergeTree

#### 2.1.1 MergeTree

MergeTree 表引擎主要用于海量数据分析，支持数据分区、存储有序、主键索引、稀疏索引和数据TTL等。MergeTree 表引擎支持云数据库ClickHouse的所有SQL语法，但是部分功能与标准SQL存在差异。


> 尽管名字相似， Merge 引擎与 xxxMergeTree 引擎是不同的。

作为最核心的引擎，MergeTree 提供了强大的数据分区、索引和压缩功能。

```sql
CREATE TABLE visits (
    user_id UInt64,
    page_url String,
    visit_date Date,
    duration UInt32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(visit_date)
ORDER BY (user_id, visit_date)
SETTINGS index_granularity = 8192;
```

**核心特性：**
- 数据按主键排序存储
- 支持数据分区
- 使用稀疏索引加速查询
- 后台数据合并优化存储

#### 2.1.2 ReplacingMergeTree



#### 2.1.3 SummingMergeTree

预聚合数据，适合统计和分析场景。

```sql
CREATE TABLE sales_summary (
    product_id UInt32,
    date Date,
    quantity UInt64,
    revenue Decimal(10,2)
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (product_id, date);
```

#### 2.1.4 AggregatingMergeTree

存储预聚合的中间状态，支持复杂的聚合函数。

```sql
CREATE TABLE user_behavior_agg (
    user_id UInt64,
    date Date,
    page_views AggregateFunction(sum, UInt64),
    unique_visits AggregateFunction(uniq, UInt64)
) ENGINE = AggregatingMergeTree()
PARTITION BY date
ORDER BY (user_id, date);
```

#### 2.1.5 CollapsingMergeTree

#### 2.1.6 VersionedCollapsingMergeTree

#### 2.1.7 GraphiteMergeTree

#### 2.1.8 CoalescingMergeTree
