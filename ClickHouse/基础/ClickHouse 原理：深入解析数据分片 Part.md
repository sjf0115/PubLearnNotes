在 ClickHouse 的世界里，Part（数据分片） 是一个核心概念，它直接影响到系统的存储效率、查询性能和数据管理方式。理解 Part 的工作原理，对于优化 ClickHouse 集群的性能至关重要。本文将从基础概念出发，逐步深入探讨 Part 的各个方面。

## 1. 什么是数据分片 Part

在 ClickHouse 中，每个使用 MergeTree 表引擎家族的表时，其数据在磁盘上都被组织成一组不可变的数据分片 Part。

为说明这一点，我们使用这张表（改编自 UK property prices dataset），用于追踪英国已售房产的成交日期、城镇、街道和价格：
```sql
CREATE TABLE uk.uk_price_paid_simple (
    date Date,
    town LowCardinality(String),
    street LowCardinality(String),
    price UInt32
)
ENGINE = MergeTree
ORDER BY (town, street);
```
每当有一组行被插入到表中时，就会创建一个数据分片 Part。
```

```



如下图所示：

![](https://clickhouse.com/docs/zh/assets/images/part-aae66074e0cc955e3293358543ffcd59.png)

当 ClickHouse 服务器处理示意图中包含 4 行的示例插入操作（例如通过 INSERT INTO 语句）时，将执行以下几个步骤：
- ① 排序：根据表的 **排序键(town, street)** 对行进行排序，并为排序后的行生成稀疏主索引。
- ② 拆分：将排序后的数据按列拆分。
- ③ 压缩：对每一列进行压缩。
- ④ 写入磁盘：将压缩后的列作为二进制列文件保存在一个新目录中，该目录代表此次插入产生的数据分片 Part。同时，稀疏主索引也会被压缩并存储在同一目录中。

> 根据表所使用的具体引擎，在排序的同时可能还会进行其他处理。

## 2. Part 内部结构

**数据分片 Part** 是自包含的，包含了解释其内容所需的全部元数据，而不需要一个集中式 Catalog。除了稀疏主索引之外，**数据分片 Part** 还包含其他元数据，例如二级数据跳过索引、列统计信息、校验和、最小-最大索引（如果使用了分区），以及更多信息。

如前所述，`Part` 是磁盘上的物理文件。默认情况下，所有与数据相关的文件都位于 `/var/lib/clickhouse` 目录下。ClickHouse 中的每个 MergeTree 表都有一个唯一目录路径来存储 `Part`。你可以通过 `system.parts` 系统表查询到 `Parts` 的实际存储位置、片段名称、分区信息（如果有的话）以及其他一些有用的信息。



## 2. Part 合并

为了管理每个表中的 **数据分片 Part** 数量，后台合并任务会定期将较小的 **数据分片 Part** 合并成更大的 **数据分片 Part**，直到它们达到一个可配置的压缩大小（通常约为 150 GB）。经过合并的 **数据分片 Part** 会被标记为非活跃，并在可配置的时间间隔后删除。随着时间推移，这一过程会形成一个由合并 **数据分片 Part** 组成的分层结构，这也是该表引擎被称为 MergeTree 表的原因：

![](https://clickhouse.com/docs/zh/assets/images/merges-a40d36416ac789a0984eb295718aa109.png)

为尽量减少初始 **数据分片 Part** 的数量以及合并带来的开销，数据库客户端建议要么批量插入，例如一次插入 20,000 行，要么使用异步插入模式。在异步模式下，ClickHouse 会将来自多个针对同一张表的 INSERT 语句的行缓存在一起，仅当缓冲区大小超过可配置阈值或超时时，才创建一个新的 **数据分片 Part**。

## 3. 监控表的分片

你可以使用虚拟列` _part`，查询示例表当前所有处于活动状态的 **数据分片 Part** 列表：
```sql
SELECT _part
FROM uk.uk_price_paid_simple
GROUP BY _part
ORDER BY _part ASC;

   ┌─_part───────┐
1. │ all_0_5_1   │
2. │ all_12_17_1 │
3. │ all_18_23_1 │
4. │ all_6_11_1  │
   └─────────────┘
```
上面的查询会检索磁盘上的目录名称，每个目录都代表该表的一个活动 **数据分片 Part**。另外，ClickHouse 会在 `system.parts` 系统表中跟踪所有表的全部 **数据分片 Part** 信息，下面这个查询会针对上面的示例表返回当前所有活动 **数据分片 Part** 的列表，包括它们的合并层级以及这些 **数据分片 Part** 中存储的行数：
```sql
SELECT
    name,
    level,
    rows
FROM system.parts
WHERE (database = 'uk') AND (`table` = 'uk_price_paid_simple') AND active
ORDER BY name ASC;

   ┌─name────────┬─level─┬────rows─┐
1. │ all_0_5_1   │     1 │ 6368414 │
2. │ all_12_17_1 │     1 │ 6442494 │
3. │ all_18_23_1 │     1 │ 5977762 │
4. │ all_6_11_1  │     1 │ 6459763 │
   └─────────────┴───────┴─────────┘
```
每在该数据块上执行一次合并操作，其合并级别就会增加 1。级别为 0 表示这是一个尚未被合并过的新数据块。
