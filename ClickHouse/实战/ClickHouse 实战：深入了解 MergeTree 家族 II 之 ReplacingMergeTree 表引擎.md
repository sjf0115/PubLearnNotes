## 1. 核心原理

> 特点：一定程度上解决了重复数据的问题，适用于在后台清理重复数据以节省存储空间

虽然 MergeTree 拥有主键，但是它的 **主键却没有唯一键的约束**。这意味着即便多行数据的主键相同，它们还是能够被正常写入。在某些使用场合，用户并不希望数据表中含有重复的数据。`ReplacingMergeTree` 就是在这种背景下为了数据去重而设计的，它能够在 **合并数据分片 Part 时删除重复的数据**，在保证查询性能的同时，实现了"最终一致性"的数据更新模型。它的出现，确实也在一定程度上解决了重复数据的问题。

> 为什么说是“一定程度”​？下面会详细介绍

`ReplacingMergeTree` 表引擎继承自 `MergeTree` 基础表引擎，并对数据分片 Part 的合并逻辑进行了调整。`ReplacingMergeTree` 会将所有具有相同 **排序键** 的行在数据分片 Part 合并时合并为一行，只保留指定版本的最新行。`ReplacingMergeTree` 通过表的 `ORDER BY` 子句，而非 `PRIMARY KEY` 来删除重复记录。即行的唯一性是由表的 `ORDER BY` 子句决定的，而不是由 `PRIMARY KEY` 决定。与常规数据库的 UPDATE 操作不同，`ReplacingMergeTree` 的更新是"异步"和"延迟"的，只在数据合并时发生。合并发生在后台未知时间，因此无法提前规划，且部分数据可能长时间保持未处理状态(重复数据没有被删除)。

> 尽管可以通过 OPTIMIZE 查询触发一次临时合并，但不要依赖这种方式，因为 OPTIMIZE 查询会读写大量数据。

因此，`ReplacingMergeTree` 适用于在后台清理重复数据以节省存储空间，但并不能保证数据中完全不存在重复项。

## 2. 语法

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster] (
    name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1],
    name2 [type2] [DEFAULT|MATERIALIZED|ALIAS expr2],
    ...
)
ENGINE = ReplacingMergeTree([ver [, is_deleted]])
[PARTITION BY expr]
[ORDER BY expr]
[PRIMARY KEY expr]
[SAMPLE BY expr]
[SETTINGS name=value, ...]
```
从上面可以看到创建一张 `ReplacingMergeTree` 表的方法与创建普通 `MergeTree` 表无异，只需要替换 Engine：
```sql
ENGINE = ReplacingMergeTree([ver [, is_deleted]])
```
其中，`ver` 是一个表示版本号的可选参数。`is_deleted` 是一个表示当前行状态的可选参数，只有在使用 `ver` 时才可以启用 `is_deleted`。

## 3. 特性

### 3.1 版本控制策略

可以通过指定一个 `UInt*`、`Date` 或者 `DateTime` 类型的字段作为版本号 `ver` 来决定数据如何去重。在合并时，`ReplacingMergeTree` 会在所有具有相同排序键的行中只保留一行：
- 显式版本控制：如果指定了版本号 `ver`，则保留具有最大版本号的行。如果多行的 `ver` 相同，保留最新插入的那一行。
- 隐式版本控制：如果未设置版本号 `ver`，则保留最近一次插入中的最后一行。

#### 3.1.1 显式版本控制

显式版本控制是指指定版本号 `ver`，那么就会保留具有最大版本号的行。如果多行的版本号相同，保留最新插入的那一行。版本列最常用的方式是时间戳或递增ID：
```sql
CREATE TABLE replacing_merge_tree_v1 (
    id String,
    code String,
    create_time DateTime
)
ENGINE = ReplacingMergeTree(create_time)
PARTITION BY toYYYYMM(create_time)
ORDER BY id;
```
`replacing_merge_tree_v1` 基于 id 字段(排序键)去重，并且使用 create_time 字段作为版本号。现在向表中插入如下数据：
```sql
INSERT INTO replacing_merge_tree_v1 Values (1, 'A3', '2026-01-01 01:01:01');
INSERT INTO replacing_merge_tree_v1 Values (1, 'A2', '2026-01-01 01:01:01');
INSERT INTO replacing_merge_tree_v1 Values (1, 'A1', '2026-01-01 00:00:00');
```
那么在删除重复数据的时候，会保留同一组数据内 create_time 时间最长的那一行：
```sql
SELECT * FROM replacing_merge_tree_v1 FINAL;
┌─id─┬─code─┬─────────create_time─┐
│ 1  │ A2   │ 2026-01-01 01:01:01 │
└────┴──────┴─────────────────────┘
```
> FINAL 语法下面会详细介绍。

#### 3.1.2 隐式版本控制（无版本列）

隐式版本控制是指不指定版本列，ReplacingMergeTree 默认保留最后插入的行：
```sql
CREATE TABLE replacing_merge_tree_v2 (
    id String,
    code String,
    create_time DateTime
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(create_time)
ORDER BY id;
```
`replacing_merge_tree_v2` 相比于 `replacing_merge_tree_v1` 没有指定版本号 `ver`，还是基于 id 字段(排序键)去重。现在向表中插入如下数据：
```sql
INSERT INTO replacing_merge_tree_v2 Values (1, 'A3', '2026-01-01 01:01:01');
INSERT INTO replacing_merge_tree_v2 Values (1, 'A2', '2026-01-01 01:01:01');
INSERT INTO replacing_merge_tree_v2 Values (1, 'A1', '2026-01-01 00:00:00');
```
那么在删除重复数据的时候，会保留同一组数据内最近一次插入中的最后一行：
```sql
SELECT * FROM replacing_merge_tree_v2 FINAL;
┌─id─┬─code─┬─────────create_time─┐
│ 1  │ A1   │ 2026-01-01 00:00:00 │
└────┴──────┴─────────────────────┘
```

### 3.2 状态控住

版本号 `ver` 决定了相同排序键（ORDER BY）行的保留优先级，而 `is_deleted` 标记行的逻辑状态(`UInt8` 类型的可选参数)：1 表示行被删除，0 表示行未被删除(有效行)：
```sql
CREATE TABLE replacing_merge_tree_v3 (
    id String,
    code String,
    create_time DateTime,
    is_deleted UInt8
)
ENGINE = ReplacingMergeTree(create_time, is_deleted)
PARTITION BY toYYYYMM(create_time)
ORDER BY id;
```
> 需要注意的是只有在使用 `ver` 时才可以启用 `is_deleted`。

`replacing_merge_tree_v3` 指定版本号 `ver` 同时还设置行状态标记 `is_deleted`，此外还是基于 id 字段(排序键)去重。现在向表中插入如下数据：
```sql
INSERT INTO replacing_merge_tree_v3 Values (1, 'A1', '2026-01-01 01:01:01', 0);
INSERT INTO replacing_merge_tree_v3 Values (1, 'A1', '2026-01-01 01:01:01', 1);
```
那么在合并删除重复数据时，根据版本号会保留版本号最大的一行数据，如果插入的两行数据具有相同的版本号，则会保留最后插入的那一行，在这最后一行 `is_deleted` = 1 表示被删除(删除行)：
```sql
SELECT * FROM replacing_merge_tree_v3 FINAL;

0 rows in set. Elapsed: 0.003 sec.
```

## 3.3 查询模式 & FINAL

在合并阶段，`ReplacingMergeTree` 使用 ORDER BY 列中的值作为唯一标识来识别重复行，并仅保留版本最高的那一行。不过，这种方式只能在最终状态上接近正确——它并不保证所有重复行都会被去重，因此不应将其作为严格依赖。由于更新和删除记录在查询时仍可能被计算在内，查询结果因此可能不正确。为了获得准确的结果，用户需要在后台合并的基础上，再配合查询时去重以及删除记录的剔除，这可以通过使用 `FINAL` 运算符来实现。

假设我们有如下表：
```sql
CREATE TABLE replacing_merge_tree_v4 (
    id String,
    code String,
    create_time DateTime
)
ENGINE = ReplacingMergeTree(create_time)
PARTITION BY toYYYYMM(create_time)
ORDER BY id;
```
现在向表中插入如下数据：
```sql
INSERT INTO replacing_merge_tree_v4 Values (1, 'A3', '2026-01-01 01:01:01');
INSERT INTO replacing_merge_tree_v4 Values (1, 'A2', '2026-01-01 01:01:01');
INSERT INTO replacing_merge_tree_v4 Values (1, 'A1', '2026-01-01 00:00:00');
```
在不使用 FINAL 的情况下进行查询返回结果没有达到去重的效果（具体情况会因合并情况而异）：
```sql
SELECT * FROM replacing_merge_tree_v4;
┌─id─┬─code─┬─────────create_time─┐
│ 1  │ A2   │ 2026-01-01 01:01:01 │
└────┴──────┴─────────────────────┘
┌─id─┬─code─┬─────────create_time─┐
│ 1  │ A1   │ 2026-01-01 00:00:00 │
└────┴──────┴─────────────────────┘
┌─id─┬─code─┬─────────create_time─┐
│ 1  │ A3   │ 2026-01-01 01:01:01 │
└────┴──────┴─────────────────────┘
```
添加 FINAL 后确实得到了预期结果：
```sql
SELECT * FROM replacing_merge_tree_v4 FINAL;
┌─id─┬─code─┬─────────create_time─┐
│ 1  │ A2   │ 2026-01-01 01:01:01 │
└────┴──────┴─────────────────────┘
```

## 4. 总结

- 使用 ORDER BY 排序键作为判断重复数据的唯一键。
- 只有在合并分区的时候才会触发删除重复数据的逻辑。
- 在进行数据去重时，因为分区内的数据已经基于 ORBER BY 进行了排序，所以能够找到那些相邻的重复数据。
- 数据去重策略有两种：
  - 如果没有设置 ver 版本号，则保留同一组重复数据中的最后一行。
  - 如果设置了 ver 版本号，则保留同一组重复数据中 ver 字段取值最大的那一行。
