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

MergeTree 家族表引擎专为高数据摄取速率和海量数据规模而设计。插入操作会创建表部件（part），这些部件会由后台进程与其他表部件进行合并。

MergeTree 家族表引擎的主要特性：

表的主键决定了每个表部件内部的排序顺序（聚簇索引）。主键并不引用单独的行，而是引用称为粒度（granule）的 8192 行数据块。这样可以使超大数据集的主键足够小，从而始终保留在主内存中，同时仍然能够快速访问磁盘上的数据。

表可以使用任意分区表达式进行分区。分区裁剪可以在查询条件允许的情况下跳过读取某些分区。

数据可以在多个集群节点之间进行复制，以实现高可用、故障切换以及零停机升级。参见 Data replication。

MergeTree 表引擎支持多种统计信息种类和采样方法，以帮助进行查询优化。

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
