在 ClickHouse 的 MergeTree 家族表引擎中，数据一致性处理一直是用户关注的焦点。特别是对于 `ReplacingMergeTree` 和 `CollapsingMergeTree` 这类需要数据去重和折叠的表引擎，ClickHouse 提供了 `SELECT FINAL` 和 `OPTIMIZE TABLE FINAL` 两种机制来确保查询时获得最终的一致状态。本文将深入探讨两者的工作原理、适用场景和性能影响。

## 1. 为什么需要 FINAL 机制？

### 1.1 MergeTree 家族的数据合并特性

ClickHouse 的 MergeTree 表引擎采用 LSM 树（Log-Structured Merge-Tree）结构，数据写入首先进入内存缓冲区，然后异步刷写到磁盘形成数据分片 Part。后台线程会定期合并这些数据分片 Part。

对于特殊表引擎：
- **ReplacingMergeTree**：根据排序键去重，保留最后插入或指定版本的数据
- **CollapsingMergeTree**：通过 sign 标志折叠行
- **VersionedCollapsingMergeTree**：带版本的折叠

**关键问题**：合并是异步的，在合并发生前，查询可能看到重复或未折叠的数据。

### 1.2 示例数据场景

```sql
-- 创建 ReplacingMergeTree 表
CREATE TABLE user_actions (
    user_id UInt64,
    action_time DateTime,
    action_type String,
    version UInt32
)
ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(action_time)
ORDER BY (user_id, action_time);

-- 插入重复数据
INSERT INTO user_actions VALUES (1, '2023-01-01 10:00:00', 'login', 1);
INSERT INTO user_actions VALUES (1, '2023-01-01 10:00:00', 'login', 2); -- 应替换前一条
```

在没有合并的情况下，普通查询会看到两条记录。

## 2. SELECT FINAL：查询时合并

### 2.1 工作原理

`SELECT FINAL` 在查询执行时，对涉及的数据分片 Part 进行实时合并，确保返回最终状态。

```sql
-- 普通查询：可能返回重复数据
SELECT * FROM user_actions WHERE user_id = 1;

-- 使用 FINAL：返回去重后的最终状态
SELECT * FROM user_actions FINAL WHERE user_id = 1;
```

### 2.2 执行流程分析

-  **数据读取阶段**：识别所有相关数据分片 Part
-  **内存中合并**：在内存中执行完整的合并逻辑
-  **结果返回**：输出合并后的最终数据

### 2.3 性能特征

**优点**：
- 实时性：总能获得最新一致视图
- 无副作用：不修改存储数据
- 灵活性：可按需使用

**缺点**：
- **查询性能影响**：合并操作增加 CPU 和内存开销
- **无法利用预聚合**：跳过 MergeTree 的预聚合优化
- **并发限制**：大量并发 FINAL 查询可能导致资源争用

### 2.4 使用示例与性能对比

```sql
-- 测试查询性能差异
EXPLAIN PIPELINE
SELECT count() FROM user_actions WHERE user_id = 1;
-- 简单扫描，利用索引

EXPLAIN PIPELINE  
SELECT count() FROM user_actions FINAL WHERE user_id = 1;
-- 包含额外的合并步骤
```

## 3. OPTIMIZE TABLE FINAL：存储层强制合并

### 3.1 工作原理

`OPTIMIZE TABLE FINAL` 触发数据分片的物理合并，生成新的、已优化的数据分片。

```sql
-- 触发强制合并
OPTIMIZE TABLE user_actions FINAL;

-- 后台合并的触发
OPTIMIZE TABLE user_actions FINAL DEDUPLICATE;
```

### 3.2 执行流程
1. **选择合并范围**：选择表或特定分区
2. **读取与合并**：读取相关数据片段，应用合并逻辑
3. **写入新片段**：生成合并后的新数据片段
4. **原子替换**：新片段准备就绪后替换旧片段

### 3.3 性能特征

**优点**：
- **一劳永逸**：合并后所有查询受益
- **查询性能提升**：后续查询无需额外合并开销
- **存储优化**：可能减少存储空间

**缺点**：
- **资源密集型**：合并过程消耗 I/O、CPU 和内存
- **阻塞风险**：大表合并可能影响并发写入
- **时机选择**：需要合理安排合并时间窗口

## 4. 核心区别对比

| 特性 | SELECT FINAL | OPTIMIZE TABLE FINAL |
|------|-------------|----------------------|
| **操作类型** | 查询时处理 | 存储层维护 |
| **数据影响** | 不修改存储数据 | 永久修改数据文件 |
| **性能影响** | 增加查询延迟 | 后台任务资源消耗 |
| **作用范围** | 单次查询有效 | 全表或分区有效 |
| **资源消耗** | 查询时 CPU/内存 | 合并时 I/O/CPU/内存 |
| **并发影响** | 可能争用资源 | 可能阻塞写入 |
| **使用场景** | 实时一致性查询 | 定期维护优化 |


接下来，用一个具体的示例说明使用它的一个注意事项。假设我们有如下表：
```sql
CREATE TABLE replacing_merge_tree_v5 (
    id String,
    code String,
    create_time DateTime
)
ENGINE = ReplacingMergeTree(create_time)
PARTITION BY toYYYYMM(create_time)
ORDER BY (id, code)
PRIMARY KEY id;
```
注意这里的 `ORDER BY` 是去除重复数据的关键，排序键 `ORDER BY` 所声明的表达式是后续作为判断数据是否重复的依据。

现在向表中插入如下数据：
```sql
INSERT INTO replacing_merge_tree_v5 Values (1, 'A1', '2026-02-01 01:01:01');
INSERT INTO replacing_merge_tree_v5 Values (1, 'A1', '2026-02-01 00:00:00');
INSERT INTO replacing_merge_tree_v5 Values (1, 'A2', '2026-02-01 00:00:00');
INSERT INTO replacing_merge_tree_v5 Values (1, 'A2', '2026-02-01 01:01:01');
```
写入之后，执行 optimize 强制分区合并或者使用 `FINAL`，并查询数据发现会按照 id 和 code 分组，保留分组内 create_time 最大的一条：
```sql
SELECT * FROM replacing_merge_tree_v5 FINAL;
┌─id─┬─code─┬─────────create_time─┐
│ 1  │ A1   │ 2026-02-01 01:01:01 │
│ 1  │ A2   │ 2026-02-01 01:01:01 │
└────┴──────┴─────────────────────┘
```
到目前为止，`ReplacingMergeTree` 看起来完美地解决了重复数据的问题。事实果真如此吗？ 现在尝试写入一条新数据：
```sql
INSERT INTO replacing_merge_tree_v5 Values (1, 'A2', '2026-08-01 01:01:01');
```



这是怎么回事呢？这是因为 ReplacingMergeTree 是以分区为单位删除重复数据的。只有在相同的数据分区内重复的数据才可以被删除，而不同数据分区之间的重复数据依然不能被剔除。这就是上面说 ReplacingMergeTree 只是在一定程度上解决了重复数据问题的原因。
