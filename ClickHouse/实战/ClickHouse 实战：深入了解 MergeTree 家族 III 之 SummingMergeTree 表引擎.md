## 1. 概述

> 特点：在合并分时候按照预先定义的条件聚合汇总数据，将多行数据汇总合并成一行

假设我们只需要查询数据的汇总结果，不关心明细数据，并且数据的汇总条件是预先定义的，即 GROUP BY 条件明确，且不会随意改变。对于这样的查询场景，在 ClickHouse 中如何解决呢？我们首先想到的便是使用 [MergeTree](https://smartsi.blog.csdn.net/article/details/157103654) 表存储数据，然后通过 GROUP BY 聚合查询，并利用 SUM 等聚合函数汇总结果。但是这种方案存在如下两个问题：
- 存在额外的存储开销：我们不需要查询明细数据，只关心汇总结果，所以不需要一直保存所有的明细数据。
- 存在额外的查询开销：我们只关心汇总结果，虽然 MergeTree 性能强大，但是每次查询都进行实时聚合计算也是一种性能消耗。

为了应对这类查询场景，ClickHouse 引入了 `SummingMergeTree` 表引擎。该引擎继承自 [MergeTree 基础表引擎](https://smartsi.blog.csdn.net/article/details/157103654)，不同之处在于，当对 `SummingMergeTree` 表的数据分片 Part 进行合并时，ClickHouse 会将所有具有相同排序键的多行汇总合并为一行(按照预先定义的条件聚合汇总数据)，汇总行的数值数据类型列值为这些行的求和结果。这样既减少了数据行，又降低了后续汇总查询的开销。

## 2. 语法

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster] (
    name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1],
    name2 [type2] [DEFAULT|MATERIALIZED|ALIAS expr2],
    ...
) ENGINE = SummingMergeTree([columns])
[PARTITION BY expr]
[ORDER BY expr]
[SAMPLE BY expr]
[SETTINGS name=value, ...]
```
从上面可以看到创建一张 `SummingMergeTree` 表的方法与创建普通 `MergeTree` 表无异，只需要替换 Engine：
```sql
ENGINE = SummingMergeTree ([columns])
```

其中 `columns` 是一个可选参数，可以指定多个被 SUM 汇总的列字段。需要注意的是这些列必须是数值类型，且不能出现在分区键或排序键中。如果未指定 `columns`，ClickHouse 会对所有数值类型且不在排序键中的列进行求和。

## 3. 特性

### 3.1 求和

求和的聚合粒度由 ORDER BY 决定，而 SUM 汇总聚合列可以通过 `columns` 可选参数来指定。如果未指定 `columns`，那么 ClickHouse 会对所有不在排序键中的数值列进行求和。

#### 3.1.1 指定列

假设有如下一张 `summing_merge_tree_v1` 表：
```sql
DROP TABLE summing_merge_tree_v1;
CREATE TABLE summing_merge_tree_v1 (
    k1 String,
    k2 UInt32,
    v1 UInt32,
    v2 UInt32
)
ENGINE = SummingMergeTree(v1)
ORDER BY (k1, k2);
```
`summing_merge_tree_v1` 表基于 k1 和 k2 字段(排序键)进行聚合，并明确指定 v1 列需要进行汇总求和。现在向表中插入如下数据：
```sql
INSERT INTO summing_merge_tree_v1 VALUES ('a', 1, 1, 1);
INSERT INTO summing_merge_tree_v1 VALUES ('b', 2, 2, 2);
INSERT INTO summing_merge_tree_v1 VALUES ('a', 1, 3, 3);
INSERT INTO summing_merge_tree_v1 VALUES ('b', 2, 4, 4);
INSERT INTO summing_merge_tree_v1 VALUES ('c', 3, 0, 5);
```
那么在查询返回结果时，在 k1 和 k2 排序键相同的行中对求和列进行 SUM 汇总：
```sql
SELECT k1, k2, v1, v2 FROM summing_merge_tree_v1 FINAL;

┌─k1─┬─k2─┬─v1─┬─v2─┐
│ a  │  1 │  4 │  1 │
└────┴────┴────┴────┘
┌─k1─┬─k2─┬─v1─┬─v2─┐
│ b  │  2 │  6 │  2 │
└────┴────┴────┴────┘
```

从上面可以看到通过 `columns` 可选参数指定的数值数据类型列 v1 会被 SUM 汇总；而 v2 数值类型列不在排序键中且没被 `columns` 参数指定，则会从已有值中任意选取一个值(不会求和)。此外如果用于求和的所有列的值都为 0，则该行(例如，k1='c'的行)会被删除。还有就是排序键列 k2 中的值不会被求和。

### 3.1.2 不指定列

假设有如下一张 `summing_merge_tree_v2` 表：
```sql
DROP TABLE summing_merge_tree_v2;
CREATE TABLE summing_merge_tree_v2 (
    k1 String,
    k2 UInt32,
    v1 UInt32,
    v2 UInt32
)
ENGINE = SummingMergeTree()
ORDER BY (k1, k2);
```
`summing_merge_tree_v2` 表还是基于 k1 和 k2 字段(排序键)进行聚合，只是没有明确指定需要进行汇总求和的列。现在向表中插入如下数据：
```sql
INSERT INTO summing_merge_tree_v2 VALUES ('a', 1, 1, 1);
INSERT INTO summing_merge_tree_v2 VALUES ('b', 2, 2, 2);
INSERT INTO summing_merge_tree_v2 VALUES ('a', 1, 3, 3);
INSERT INTO summing_merge_tree_v2 VALUES ('b', 2, 4, 4);
INSERT INTO summing_merge_tree_v2 VALUES ('c', 3, 0, 5);
```
那么在查询返回结果时，在 k1 和 k2 排序键相同的行中对所有数值类型列进行 SUM 汇总：
```sql
SELECT k1, k2, v1, v2 FROM summing_merge_tree_v2 FINAL;

┌─k1─┬─k2─┬─v1─┬─v2─┐
│ a  │  1 │  4 │  4 │
│ b  │  2 │  6 │  6 │
│ c  │  3 │  0 │  5 │
└────┴────┴────┴────┘
```
从上面可以看到如果未指定 `columns`，ClickHouse 会对所有不在排序键中数值类型的列 v1 和 v2 进行求和 SUM。

### 3.2 选择与排序键不同的主键

> 在使用 `SummingMergeTree` 和 `AggregatingMergeTree` 表引擎时，这一特性非常有用

上述示例中只指定了排序键，那么主键会被隐式定义为与排序键相同。当然也可以指定一个与排序键不同的主键。这在使用 `SummingMergeTree` 和 `AggregatingMergeTree` 表引擎时会非常有用。在这些引擎的常见使用场景中，表通常有两类列：维度（dimensions） 和 度量（measures）。典型查询会对度量列的值在任意 GROUP BY 条件下进行聚合，并按维度进行过滤。由于 `SummingMergeTree` 和 `AggregatingMergeTree` 会对具有相同排序键值的行进行聚合，因此将所有维度都加入排序键是很自然的做法。在这种情况下，更合理的做法是只在主键中保留少数几列，以保证高效的范围扫描，并将其余维度列加入排序键元组中。

现在用一个示例说明。假设一张 `SummingMergeTree` 表有 A、B、C、D、E、F 六列，如果需要按照 A、B、C、D 进行汇总，则有：
```sql
ORDER BY (A，B，C，D)
```
但是如此一来，此表的主键也被定义成了 A、B、C、D。而在业务层面，其实只需要对 A 列进行查询过滤，应该只使用 A 字段创建主键。所以，一种更加优雅的定义形式应该是：
```sql
ORDER BY (A、B、C、D)
PRIMARY KEY A
```

此外需要注意的是当选择与排序键不同的主键时，MergeTree 会强制要求主键列字段必须是排序键的前缀。例如下面的定义是错误的：
```sql
ORDER BY (B、C、D)
PRIMARY KEY A
```
> PRIMARY KEY 必须是 ORDER BY 的前缀。

这种强制约束保障了即便在两者定义不同的情况下，主键仍然是排序键的前缀，不会出现索引与数据顺序混乱的问题。

### 3.3 最终一致性

当数据被插入到表中时，会按原样保存。ClickHouse 会定期合并已插入的数据分片 Part，在此过程中，具有相同排序键的行会被求和，并在每个合并结果的数据分片 Part 中替换为一行。ClickHouse 合并数据分片 Part 的方式可能导致：不同的合并结果数据分片 Part 中仍然可能包含具有相同排序键的行，即求和可能是不完整的。即 ClickHouse 可能不会对所有行进行完整的求和处理，因此我们可以考虑在查询中使用聚合函数 SUM 和 GROUP BY 子句手动聚合：
```sql
SELECT k, SUM(v1)
FROM t
GROUP BY k
```

> 参考：[SummingMergeTree 表引擎](https://clickhouse.com/docs/zh/engines/table-engines/mergetree-family/summingmergetree)
