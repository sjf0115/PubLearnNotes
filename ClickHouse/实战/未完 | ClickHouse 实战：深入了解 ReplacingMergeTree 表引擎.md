> 特点：一定程度上解决了重复数据的问题

虽然 MergeTree 拥有主键，但是它的 **主键却没有唯一键的约束**。这意味着即便多行数据的主键相同，它们还是能够被正常写入。在某些使用场合，用户并不希望数据表中含有重复的数据。`ReplacingMergeTree` 就是在这种背景下为了数据去重而设计的，它能够在 **合并分区时删除重复的数据**。它的出现，确实也在一定程度上解决了重复数据的问题。

`ReplacingMergeTree` 会删除具有相同排序键值的重复记录（指表的 `ORDER BY` 子句，而非 `PRIMARY KEY`）。数据去重仅在合并期间发生。合并在后台于未知时间执行，因此无法提前规划，且部分数据可能长时间保持未处理状态。尽管可以通过 OPTIMIZE 查询触发一次临时合并，但不要依赖这种方式，因为 OPTIMIZE 查询会读写大量数据。因此，`ReplacingMergeTree` 适用于在后台清理重复数据以节省存储空间，但并不能保证数据中完全不存在重复项。

> 行的唯一性是由表的 ORDER BY 子句决定的，而不是由 PRIMARY KEY 决定。


> 为什么说是“一定程度”​？此处先按下不表。

## 2. 语法

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster]
(
    name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1],
    name2 [type2] [DEFAULT|MATERIALIZED|ALIAS expr2],
    ...
) ENGINE = ReplacingMergeTree([ver [, is_deleted]])
[PARTITION BY expr]
[ORDER BY expr]
[PRIMARY KEY expr]
[SAMPLE BY expr]
[SETTINGS name=value, ...]
```

### 2.1 ver

创建一张 `ReplacingMergeTree` 表的方法与创建普通 `MergeTree` 表无异，只需要替换 Engine：
```sql
ENGINE = ReplacingMergeTree (ver)
```
其中，`ver` 是选填参数，表示版本号的列。可以指定一个 `UInt*`、`Date` 或者 `DateTime` 类型的字段作为版本号。这个参数决定了数据去重时所使用的算法。

在合并时，`ReplacingMergeTree` 会在所有具有相同排序键的行中只保留一行：
- 如果未设置 `ver`，则保留选集中最后一行。一次选集是指参与该次合并的多个数据 part 中的一组行。最新创建的 part（最后一次插入）会排在选集的最后。因此，去重后，对于每个唯一排序键，将保留最近一次插入中的最后一行。
- 如果指定了 `ver`，则保留具有最大版本号的行。如果多行的 `ver` 相同，保留最新插入的那一行。

### 2.2 is_deleted

is_deleted 为 `UInt8` 类型。在合并过程中用于确定该行数据表示的是当前状态还是应被删除的列名；1 表示“删除”行，0 表示“状态”行。

只有在使用 ver 时才可以启用 is_deleted。


## 3. 示例


接下来，用一个具体的示例说明它的用法。首先执行下面的语句创建数据表：
```sql
CREATE TABLE user_profile (
    user_id UInt64,
    username String,
    email String,
    updated_at DateTime,
    version UInt32
)
ENGINE = ReplacingMergeTree(version)
PARTITION BY bitShiftRight(user_id, 20)
ORDER BY (user_id, username);


CREATE TABLE replace_table (
    id String,
    code String,
    create_time DateTime
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(create_time)
ORDER BY(id, code)
PRIMARY KEY id
```

```sql
-- without ver - the last inserted 'wins'
CREATE TABLE myFirstReplacingMT
(
    `key` Int64,
    `someCol` String,
    `eventTime` DateTime
)
ENGINE = ReplacingMergeTree
ORDER BY key;

INSERT INTO myFirstReplacingMT Values (1, 'first', '2020-01-01 01:01:01');
INSERT INTO myFirstReplacingMT Values (1, 'second', '2020-01-01 00:00:00');

SELECT * FROM myFirstReplacingMT FINAL;

┌─key─┬─someCol─┬───────────eventTime─┐
│   1 │ second  │ 2020-01-01 00:00:00 │
└─────┴─────────┴─────────────────────┘


-- with ver - the row with the biggest ver 'wins'
CREATE TABLE mySecondReplacingMT
(
    `key` Int64,
    `someCol` String,
    `eventTime` DateTime
)
ENGINE = ReplacingMergeTree(eventTime)
ORDER BY key;

INSERT INTO mySecondReplacingMT Values (1, 'first', '2020-01-01 01:01:01');
INSERT INTO mySecondReplacingMT Values (1, 'second', '2020-01-01 00:00:00');

SELECT * FROM mySecondReplacingMT FINAL;

┌─key─┬─someCol─┬───────────eventTime─┐
│   1 │ first   │ 2020-01-01 01:01:01 │
└─────┴─────────┴─────────────────────┘
```

## 4. 查询时去重 & FINAL

在合并阶段，ReplacingMergeTree 使用 ORDER BY 列（用于创建表）中的值作为唯一标识来识别重复行，并仅保留版本最高的那一行。不过，这种方式只能在最终状态上接近正确——它并不保证所有重复行都会被去重，因此不应将其作为严格依赖。由于更新和删除记录在查询时仍可能被计算在内，查询结果因此可能不正确。

为了获得准确的结果，用户需要在后台合并的基础上，再配合查询时去重以及删除记录的剔除。这可以通过使用 FINAL 运算符来实现。例如，考虑以下示例：
```sql
SELECT count()
FROM rmt_example

┌─count()─┐
│     200 │
└─────────┘

1 row in set. Elapsed: 0.002 sec.
```
在不使用 FINAL 的情况下进行查询会返回不正确的计数结果（具体数值会因合并情况而异）。
```sql
SELECT count()
FROM rmt_example
FINAL

┌─count()─┐
│     100 │
└─────────┘

1 row in set. Elapsed: 0.002 sec.
```
添加 FINAL 后即可得到正确的结果。







https://clickhouse.com/docs/zh/engines/table-engines/mergetree-family/replacingmergetree

https://clickhouse.com/docs/zh/guides/replacing-merge-tree
