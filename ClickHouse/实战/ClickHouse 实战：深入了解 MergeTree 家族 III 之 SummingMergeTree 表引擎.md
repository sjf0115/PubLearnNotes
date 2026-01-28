## 1. 概述

假设我们只需要查询数据的汇总结果，不关心明细数据，并且数据的汇总条件是预先明确的，即 GROUP BY 条件明确，且不会随意改变。对于这样的查询场景，在 ClickHouse 中如何解决呢？我们首先想到的便是使用 [MergeTree](https://smartsi.blog.csdn.net/article/details/157103654) 表存储数据，然后通过 GROUP BY 聚合查询，并利用 SUM 等聚合函数汇总结果。但是这种方案存在如下两个问题：
- 存在额外的存储开销：我们不需要查询明细数据，只关心汇总结果，所以不需要一直保存所有的明细数据。
- 存在额外的查询开销：我们只关心汇总结果，虽然 MergeTree 性能强大，但是每次查询都进行实时聚合计算也是一种性能消耗。

为了应对这类查询场景，ClickHouse 引入了 `SummingMergeTree` 表引擎。该引擎继承自 [MergeTree 基础表引擎](https://smartsi.blog.csdn.net/article/details/157103654)，不同之处在于，当对 `SummingMergeTree` 表的数据分片 Part 进行合并时，ClickHouse 会将所有具有相同排序键的多行汇总合并为一行(按照预先定义的条件聚合汇总数据)，其中数值数据类型列的值为这些行的求和结果。这样既减少了数据行，又降低了后续汇总查询的开销。

> 特点：在合并分时候按照预先定义的条件聚合汇总数据，将多行数据汇总合并成一行

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

`columns` 是一个可选参数，可以指定多个被 SUM 汇总的列字段。需要注意的是这些列必须是数值类型，且不能出现在分区键或排序键中。如果未指定 `columns`，ClickHouse 会对所有数值类型且不在排序键中的列进行求和。

## 3. 特性

### 3.1 聚合粒度与汇总列

聚合粒度由 ORDER BY 决定。汇总聚合列可以通过 `columns` 可选参数来指定需要被 SUM 汇总的列字段。如果未指定 `columns`，那么 ClickHouse 会对所有不在排序键中的数值列进行求和。

#### 3.1.1 指定列

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
`summing_merge_tree_v1` 基于 k 字段(排序键)进行聚合，并明确指定 v1 列需要进行汇总求和。现在向表中插入如下数据：
```sql
INSERT INTO summing_merge_tree_v1 VALUES ('a', 1, 1, 1);
INSERT INTO summing_merge_tree_v1 VALUES ('b', 2, 2, 2);
INSERT INTO summing_merge_tree_v1 VALUES ('a', 1, 3, 3);
INSERT INTO summing_merge_tree_v1 VALUES ('b', 2, 4, 4);
INSERT INTO summing_merge_tree_v1 VALUES ('c', 3, 0, 5);
```
那么在查询返回结果时，在 k 相同时对求和列进行 SUM 汇总：
```sql
SELECT k1, k2, v1, v2 FROM summing_merge_tree_v1 FINAL;

┌─k1─┬─k2─┬─v1─┬─v2─┐
│ a  │  1 │  4 │  1 │
└────┴────┴────┴────┘
┌─k1─┬─k2─┬─v1─┬─v2─┐
│ b  │  2 │  6 │  2 │
└────┴────┴────┴────┘
```

从上面可以看到通过 `columns` 可选参数指定的数值数据类型列(例如，v1)会被 SUM 汇总，如果某列(例如, v2)不在排序键中且没被 `columns` 参数指定，则会从已有值中任意选取一个值(不会求和)。此外如果用于求和的所有列的值都为 0，则该行(例如，k1='c'的行)会被删除。还有就是排序键列(例如, k2)中的值不会被求和。

### 3.1.2 不指定列

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
`summing_merge_tree_v2` 还是基于 k 字段(排序键)进行聚合，只是没有明确需要进行汇总求和的列。现在向表中插入如下数据：
```sql
INSERT INTO summing_merge_tree_v2 VALUES ('a', 1, 1, 1);
INSERT INTO summing_merge_tree_v2 VALUES ('b', 2, 2, 2);
INSERT INTO summing_merge_tree_v2 VALUES ('a', 1, 3, 3);
INSERT INTO summing_merge_tree_v2 VALUES ('b', 2, 4, 4);
INSERT INTO summing_merge_tree_v2 VALUES ('c', 3, 0, 5);
```
那么在查询返回结果时，在 k 相同时对求和列进行 SUM 汇总：
```sql
SELECT k1, k2, v1, v2 FROM summing_merge_tree_v2 FINAL;

┌─k1─┬─k2─┬─v1─┬─v2─┐
│ a  │  1 │  4 │  4 │
│ b  │  2 │  6 │  6 │
│ c  │  3 │  0 │  5 │
└────┴────┴────┴────┘
```
从上面可以看到如果未指定 `columns`，ClickHouse 会对所有不在排序键中数值类型的列(例如，v1和v2)进行求和 SUM。


### 3.2 ORDER BY 与 PRIMARY KEY 不同

如果需要同时定义 ORDER BY 与 PRIMARY KEY，通常只有一种可能，那便是明确希望 ORDER BY 与 PRIMARY KEY 不同。这种情况通常只会在使用 SummingMergeTree 或 AggregatingMergeTree 时才会出现。这是为何呢？这是因为 SummingMergeTree 与 AggregatingMergeTree 的聚合都是根据 ORDER BY 进行的。由此可以引出两点原因：主键与聚合的条件定义分离，为修改聚合条件留下空间。现在用一个示例说明。假设一张 SummingMergeTree 数据表有 A、B、C、D、E、F 六个字段，如果需要按照 A、B、C、D 汇总，则有：
```sql
ORDER BY (A，B，C，D)
```
但是如此一来，此表的主键也被定义成了A、B、C、D。而在业务层面，其实只需要对字段A进行查询过滤，应该只使用A字段创建主键。所以，一种更加优雅的定义形式应该是：
```sql
ORDER BY (A、B、C、D)
PRIMARY KEY A
```
> 需要注意的是如果同时声明了ORDER BY与PRIMARY KEY，MergeTree会强制要求PRIMARYKEY列字段必须是ORDER BY的前缀。这种强制约束保障了即便在两者定义不同的情况下，主键仍然是排序键的前缀，不会出现索引与数据顺序混乱的问题。

### 3.3 最终一致性

当数据被插入到表中时，会按原样保存。ClickHouse 会定期合并已插入的数据分片 Part，在此过程中，具有相同排序键的行会被求和，并在每个合并结果的数据分片 Part 中替换为一行。

ClickHouse 合并数据分片 Part 的方式可能导致：不同的合并结果数据分片 Part 中仍然可能包含具有相同排序键的行，即求和可能是不完整的。即 ClickHouse 可能不会对所有行进行完整的求和处理，因此我们在查询中使用聚合函数 sum 和 GROUP BY 子句：
```sql
SELECT key, sum(value) FROM summtt GROUP BY key
```


- 对于 AggregateFunction 类型 的列，ClickHouse 的行为类似于 AggregatingMergeTree 引擎，会根据该函数对数据进行聚合。


在知道了SummingMergeTree的使用方法后，现在简单梳理一下它的处理逻辑。(1) 用ORBER BY排序键作为聚合数据的条件Key。(2) 只有在合并分区的时候才会触发汇总的逻辑。(3) 以数据分区为单位来聚合数据。当分区合并时，同一数据分区内聚合Key相同的数据会被合并汇总，而不同分区之间的数据则不会被汇总。(4) 如果在定义引擎时指定了columns汇总列 （非主键的数值类型字段） ，则SUM汇总这些列字段；如果未指定，则聚合所有非主键的数值类型字段。(5) 在进行数据汇总时，因为分区内的数据已经基于ORBER BY排序，所以能够找到相邻且拥有相同聚合Key的数据。
(6) 在汇总数据时，同一分区内，相同聚合Key的多行数据会合并成一行。其中，汇总字段会进行SUM计算；对于那些非汇总字段，则会使用第一行数据的取值。(7) 支持嵌套结构，但列字段名称必须以Map后缀结尾。嵌套类型中，默认以第一个字段作为聚合Key。除第一个字段以外，任何名称以Key、Id或Type为后缀结尾的字段，都将和第一个字段一起组成复合Key。


在使用嵌套数据类型的时候，默认情况下，会以嵌套类型中第一个字段作为聚合条件Key。假设表内的数据如下所示：


我们建议将此引擎与 MergeTree 结合使用。在 MergeTree 表中存储完整数据，并使用 SummingMergeTree 存储聚合后的数据，例如在生成报表时使用。这样的做法可以避免由于主键设计不当而导致有价值数据的丢失。

> 参考：[SummingMergeTree 表引擎](https://clickhouse.com/docs/zh/engines/table-engines/mergetree-family/summingmergetree)
