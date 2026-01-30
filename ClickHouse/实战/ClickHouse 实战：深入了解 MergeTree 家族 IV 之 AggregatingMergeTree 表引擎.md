## 1. 概述

有过数据仓库建设经验的读者一定知道“数据立方体”的概念，这是一个在数据仓库领域十分常见的模型。它通过以空间换时间的方法提升查询性能，将需要聚合的数据预先计算出来，并将结果保存起来。在后续进行聚合查询的时候，直接使用结果数据。AggregatingMergeTree 就有些许数据立方体的意思，它能够在合并分区的时候，按照预先定义的条件聚合数据。同时，根据预先定义的聚合函数计算数据并通过二进制的格式存入表内。将同一分组下的多行数据聚合成一行，既减少了数据行，又降低了后续聚合查询的开销。可以说，AggregatingMergeTree是SummingMergeTree的升级版，它们的许多设计思路是一致的，例如同时定义ORDER BY与PRIMARY KEY的原因和目的。但是在使用方法上，两者存在明显差异，应该说AggregatingMergeTree的定义方式是MergeTree家族中最为特殊的一个。

该引擎继承自 MergeTree，并对数据部分的合并逻辑进行了调整。ClickHouse 会将所有具有相同排序键的行在单个数据部分内合并为一行，该行存储了聚合函数状态的组合。

该引擎会处理所有具有以下类型的列：
- AggregateFunction
- SimpleAggregateFunction


在实时数据分析领域，ClickHouse以其卓越的查询性能著称，而AggregatingMergeTree表引擎正是实现这一性能的关键武器之一。作为MergeTree家族的一员，AggregatingMergeTree专为预聚合数据场景设计，通过在数据写入时进行聚合计算，将海量明细数据压缩为高度聚合的中间状态，从而在查询时获得数量级的性能提升。

与传统的事后聚合不同，AggregatingMergeTree采用了"空间换时间"的策略，将聚合计算提前到数据入库阶段。这种设计理念特别适合监控指标分析、用户行为分析、物联网传感器数据等需要频繁进行聚合查询的场景。


为了应对这类查询场景，ClickHouse 引入了 `AggregatingMergeTree` 表引擎。该引擎继承自 [MergeTree 基础表引擎](https://smartsi.blog.csdn.net/article/details/157103654)，并对数据分片 Part 的合并逻辑进行了调整。不同之处在于，当对 `AggregatingMergeTree` 表的数据分片 Part 进行合并时，ClickHouse 会将所有具有相同排序键的多行汇总合并为一行(按照预先定义的条件聚合汇总数据)，汇总行的数值数据类型列值为这些行的求和结果。这样既减少了数据行，又降低了后续汇总查询的开销。


## 2. 语法

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster] (
    name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1],
    name2 [type2] [DEFAULT|MATERIALIZED|ALIAS expr2],
    ...
) ENGINE = AggregatingMergeTree()
[PARTITION BY expr]
[ORDER BY expr]
[SAMPLE BY expr]
[TTL expr]
[SETTINGS name=value, ...]
```
从上面可以看到创建一张 `AggregatingMergeTree` 表的方法与创建普通 `MergeTree` 表无异，只需要替换 Engine：
```sql
ENGINE = AggregatingMergeTree ()
```
`AggregatingMergeTree` 没有任何额外的设置参数，在分区合并时，在每个数据分区内，会按照 ORDER BY 聚合。

## 3. 注意

AggregatingMergeTree 在分区合并时，在每个数据分区内，会按照 ORDER BY 聚合。而使用何种聚合函数，以及针对哪些列字段计算，则是通过定义AggregateFunction数据类型实现的。以下面的语句为例：
```sql
CREATE TABLE agg_table (
    id String,
    city String,
    code AggregateFunction(uniq, String),
    value AggregateFunction(sum, UInt32),
    create_time DateTime
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM (create_time)
ORDER BY (id,city)
PRIMARY KEY id
```
上例中列字段 id 和 city 是聚合条件，而 code和 value 是聚合字段，等同于下面的语义：
```sql
SELECT
  id，city,
  UNIQ(code), SUM(value)
FROM agg_table
GROUP BY id，city
```

### 3.1 SELECT 和 INSERT

AggregateFunction 是 ClickHouse 提供的一种特殊的数据类型，它能够以二进制的形式存储中间状态结果。其使用方法也十分特殊，对于 AggregateFunction类型的列字段，数据的写入和查询都与寻常不同。在写入数据时，需要调用 `*State` 函数；而在查询数据时，则需要调用相应的 `*Merge` 函数。其中，`*` 表示定义时使用的聚合函数。例如示例中定义的 code 和 value，使用了 uniq 和 sum 函数。

那么，在写入数据时需要调用与 uniq、sum 对应的 uniqState 和 sumState 函数，并使用 INSERT SELECT 语法：
```sql
INSERT INTO TABLE agg_table
SELECT
  'A000','wuhan',
  uniqState('code1'),
  sumState(toUInt32(100)),
  '2019-08-10 17:00:00'
```
在查询数据时，如果直接使用列名访问code和value，将会是无法显示的二进制形式。此时，需要调用与uniq、sum对应的 uniqMerge、sumMerge 函数：
```sql
SELECT
  id,city,
  uniqMerge(code),
  sumMerge(value)
FROM agg_table
GROUP BY id, city
```
### 3.2 聚合物化视图

讲到这里，你是否会认为 AggregatingMergeTree 使用起来过于烦琐了？连正常进行数据写入都需要借助 INSERT…SELECT 的句式并调用特殊函数。如果直接像刚才示例中那样使用 AggregatingMergeTree，确实会非常麻烦。不过各位读者并不需要忧虑，因为目前介绍的这种使用方法，并不是它的主流用法。

AggregatingMergeTree 更为常见的应用方式是结合物化视图使用，将它作为物化视图的表引擎。而这里的物化视图是作为其他数据表上层的一种查询视图，如图7-1所示。首先，建立明细数据表，也就是俗称的底表：
```sql
CREATE TABLE agg_table_basic (
    id String,
    city String,
    code String,
    value UInt32
)
ENGINE = MergeTree()
PARTITION BY city
ORDER BY (id,city)
```
通常会使用MergeTree作为底表，用于存储全量的明细数据，并以此对外提供实时查询。接着，新建一张物化视图：
```sql
CREATE MATERIALIZED VIEW agg_view
ENGINE = AggregatingMergeTree ()
PARTITION BY city
ORDER BY (id,city)
AS SELECT
    id,
    city,
    uniqState(code)AS code,
    sumState(value)AS value
FROM agg_table_basic
GROUP BY id, city
```
物化视图使用AggregatingMergeTree表引擎，用于特定场景的数据查询，相比MergeTree，它拥有更高的性能。

在新增数据时，面向的对象是底表MergeTree：
```sql
INSERT INTO TABLE agg_table_basic
VALUES
('A000','wuhan','code1',100)
,
('A000','wuhan','code2',200)
,
('A000','zhuhai', 'code1',200)
```
数据会自动同步到物化视图，并按照AggregatingMergeTree引擎的规则处理。在查询数据时，面向的对象是物化视图AggregatingMergeTree：
```sql
SELECT id, sumMerge
(value)
, uniqMerge
(code)
 FROM agg_view GROUP BY id, city
```

## 4. 总结

(1) 用ORBER BY排序键作为聚合数据的条件Key。(2) 使用AggregateFunction字段类型定义聚合函数的类型以及聚合的字段。(3) 只有在合并分区的时候才会触发聚合计算的逻辑。(4) 以数据分区为单位来聚合数据。当分区合并时，同一数据分区内聚合Key相同的数据会被合并计算，而不同分区之间的数据则不会被计算。(5) 在进行数据计算时，因为分区内的数据已经基于ORBER BY排序，所以能够找到那些相邻且拥有相同聚合Key的数据。(6) 在聚合数据时，同一分区内，相同聚合Key的多行数据会合并成一行。对于那些非主键、非AggregateFunction类型字段，则会使用第一行数据的取值。(7) AggregateFunction类型的字段使用二进制存储，在写入数据时，需要调用*State函数；而在查询数据时，则需要调用相应的*Merge函数。其中，*表示定义时使用的聚合函数。(8) AggregatingMergeTree通常作为物化视图的表引擎，与普通MergeTree搭配使用。



> [AggregatingMergeTree 表引擎](https://clickhouse.com/docs/zh/engines/table-engines/mergetree-family/aggregatingmergetree)
