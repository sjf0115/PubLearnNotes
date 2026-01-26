使用 MergeTree 引擎表时会将数据以不可变的数据分片 Part 的形式存储在磁盘上。每次插入数据时都会创建新的数据分片 Part，其中包含已排序、已压缩的列文件，以及索引和校验和等元数据。随着时间推移，后台进程会将较小的数据分片 Part 合并为更大的数据分片 Part，以减少碎片并提高查询性能。

![](https://clickhouse.com/docs/zh/assets/images/simple_merges-e524ee5a768a2150c350988073817dfe.png)

> 关于数据分片 Part 的结构以及它们是如何形成的详细说明，建议参考本[ClickHouse 原理：深入解析数据分片 Part](https://smartsi.blog.csdn.net/article/details/157332454)。

第一反应你可能会想通过以下方式手动触发这种合并操作：
```sql
OPTIMIZE TABLE <table> FINAL;
```
虽然这个命令看起来像是"万能解决方案"，但在生产环境中不加选择地使用它可能导致严重问题，因为它会触发资源密集型操作，从而可能对集群性能产生影响。本文将深入探讨为什么应该避免使用 `OPTIMIZE FINAL`，以及什么情况下才是它的正确使用场景。

## 1. OPTIMIZE FINAL 的本质是什么？

在深入讨论之前，让我们先了解 `OPTIMIZE FINAL` 的实际作用：
```sql
OPTIMIZE TABLE <table> [PARTITION partition_expr] FINAL;
```
这个命令的主要功能是：
- **强制合并表的所有数据分片 Part**，无论后台合并策略如何
- **触发最终合并**，即使单个数据分片 Part 已经达到最大大小限制
- **重建数据**，以完全优化的形式存储

## 2. 为什么应该避免使用 OPTIMIZE FINAL？

### 2.1 **严重的性能影响**

`OPTIMIZE FINAL` 是一个 **阻塞操作**，它会锁定表并阻止并发读写：
```sql
-- 这个操作会阻塞表的读写，直到完成
OPTIMIZE TABLE events FINAL;
```

对于大型表，这个过程可能需要数小时甚至数天。在此期间：
- 表不可写（INSERT 操作会阻塞或失败）
- 查询性能可能严重下降
- 系统资源被大量占用

### 2.2 **成本高昂**

运行 OPTIMIZE FINAL 会强制 ClickHouse 将所有活跃的数据分片 Part 合并成单个数据分片 Part，即使之前已经执行过大型合并：
- 解压缩所有数据分片 Part
- 合并数据
- 再次对其进行压缩
- 将最终的数据分片 Part 写入磁盘或对象存储

这些步骤非常耗费 CPU 和 I/O，在涉及大规模数据集时，可能会给系统带来显著压力。

### 2.3 忽略安全限制

通常，ClickHouse 会避免合并大于约 150 GB 的数据分片 Part（可通过 `max_bytes_to_merge_at_max_space_in_pool` 进行配置）。但 `OPTIMIZE FINAL` 会忽略这一安全机制，这意味着：
- 它可能会尝试将多个 150 GB 的数据分片 Part 合并成一个巨大的数据分片 Part
- 这可能导致合并时间很长、内存压力增大，甚至内存耗尽
- 这些超大数据分片 Part 后续可能难以再合并，即进一步尝试合并它们会因为上述原因而失败。在某些需要通过合并来保证查询行为正确的场景中，这可能会带来不良后果，例如 ReplacingMergeTree 中重复数据不断累积，从而降低查询时的性能。

## 3. 什么时候可以考虑使用 OPTIMIZE FINAL？

尽管有上述缺点，但在某些特定场景下，`OPTIMIZE FINAL` 还是有用的：

### 3.1 **表结构变更后**

当修改表结构（如添加/删除列）后，可能需要强制合并：
```sql
-- 修改表结构后
ALTER TABLE events ADD COLUMN new_column String;

-- 然后可以考虑合并，但更好的做法是等待自动合并
OPTIMIZE TABLE events FINAL;
```

### 3.2 **数据修复场景**

当怀疑数据损坏或需要强制清理已删除的行时：
```sql
-- 在删除大量行后，清理存储空间
ALTER TABLE events DELETE WHERE date < '2023-01-01';

-- 等待一段时间后，如果需要立即回收空间
OPTIMIZE TABLE events FINAL;
```

### 3.3 **准备只读副本或归档**

在创建表的静态副本或准备归档时：
```sql
-- 创建完全优化的表副本
CREATE TABLE events_archive AS events ENGINE = MergeTree()
ORDER BY (date, user_id);

INSERT INTO events_archive SELECT * FROM events;

-- 确保归档表完全优化
OPTIMIZE TABLE events_archive FINAL;
```

## 4. 总结

**黄金法则：除非绝对必要，否则不要使用 `OPTIMIZE FINAL`。** ClickHouse 已经会在后台执行智能合并，以优化存储和查询效率。这些合并是增量的、感知资源使用情况的，并且会遵循已配置的阈值。除非存在非常特定的需求（例如在冻结表或导出之前对数据进行最终定版），否则通常应当让 ClickHouse 自行管理合并过程。

> 参考：[避免使用 OPTIMIZE FINAL](https://clickhouse.com/docs/zh/optimize/avoidoptimizefinal)
