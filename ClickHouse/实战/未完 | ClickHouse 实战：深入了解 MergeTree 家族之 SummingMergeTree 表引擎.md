假设有这样一种查询需求：终端用户只需要查询数据的汇总结果，不关心明细数据，并且数据的汇总条件是预先明确的 （GROUP BY条件明确，且不会随意改变） 。对于这样的查询场景，在 ClickHouse 中如何解决呢？最直接的方案就是使用 MergeTree 存储数据，然后通过 GROUP BY 聚合查询，并利用 SUM 聚合函数汇总结果。这种方案存在两个问题：
- 存在额外的存储开销：终端用户不会查询任何明细数据，只关心汇总结果，所以不应该一直保存所有的明细数据。
- 存在额外的查询开销：终端用户只关心汇总结果，虽然 MergeTree 性能强大，但是每次查询都进行实时聚合计算也是一种性能消耗。

`SummingMergeTree` 就是为了应对这类查询场景而生的。该引擎继承自 MergeTree，它能够在合并分区的时候按照预先定义的条件聚合汇总数据，将同一分组下的多行数据汇总合并成一行，这样既减少了数据行，又降低了后续汇总查询的开销。当对 `SummingMergeTree` 表的数据分区片段进行合并时，ClickHouse 会将所有具有相同排序键的多行，合并为一行，其中数值数据类型列的值为这些行的求和结果。

> 特点：在合并分区的时候按照预先定义的条件聚合汇总数据，将同一分组下的多行数据汇总合并成一行

## 2. 语法

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster]
(
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

### 2.1 columns

columns 是一个可选参数，可以指定多个被 SUM 汇总的列字段。需要注意的是这些列必须是数值类型，且不能出现在分区键或排序键中。如果未指定 columns，ClickHouse 会对所有数值类型且不在排序键中的列进行求和。

### 2.2 ORDER BY与PRIMARY KEY不同

如果需要同时定义ORDER BY与PRIMARY KEY，通常只有一种可能，那便是明确希望ORDER BY与PRIMARY KEY不同。这种情况通常只会在使用SummingMergeTree或AggregatingMergeTree时才会出现。这是为何呢？这是因为SummingMergeTree与AggregatingMergeTree的聚合都是根据ORDER BY进行的。由此可以引出两点原因：主键与聚合的条件定义分离，为修改聚合条件留下空间。现在用一个示例说明。假设一张SummingMergeTree数据表有A、B、C、D、E、F六个字段，如果需要按照A、B、C、D汇总，则有：
```sql
ORDER BY (A，B，C，D)
```
但是如此一来，此表的主键也被定义成了A、B、C、D。而在业务层面，其实只需要对字段A进行查询过滤，应该只使用A字段创建主键。所以，一种更加优雅的定义形式应该是：
```sql
ORDER BY (A、B、C、D)
PRIMARY KEY A
```
> 需要注意的是如果同时声明了ORDER BY与PRIMARY KEY，MergeTree会强制要求PRIMARYKEY列字段必须是ORDER BY的前缀。这种强制约束保障了即便在两者定义不同的情况下，主键仍然是排序键的前缀，不会出现索引与数据顺序混乱的问题。

## 3. 注意

当数据被插入到表中时，会按原样保存。ClickHouse 会定期合并已插入的数据部分，在此过程中，具有相同排序键的行会被求和，并在每个合并结果的数据部分中替换为一行。

ClickHouse 合并数据部分的方式可能导致：不同的合并结果数据部分中仍然可能包含具有相同排序键的行，即求和可能是不完整的。因此，在执行查询时（SELECT），应按照上面的示例使用聚合函数 sum() 和 GROUP BY 子句。

求和的通用规则
- 数值数据类型列中的值会被求和。参与求和的列集合由参数 columns 定义。
- 如果用于求和的所有列的值都为 0，则该行会被删除。
- 如果某列不在排序键中且不参与求和，则会从已有值中任意选取一个值。
- 排序键列中的值不会被求和。
- 对于 AggregateFunction 类型 的列，ClickHouse 的行为类似于 AggregatingMergeTree 引擎，会根据该函数对数据进行聚合。


在知道了SummingMergeTree的使用方法后，现在简单梳理一下它的处理逻辑。(1) 用ORBER BY排序键作为聚合数据的条件Key。(2) 只有在合并分区的时候才会触发汇总的逻辑。(3) 以数据分区为单位来聚合数据。当分区合并时，同一数据分区内聚合Key相同的数据会被合并汇总，而不同分区之间的数据则不会被汇总。(4) 如果在定义引擎时指定了columns汇总列 （非主键的数值类型字段） ，则SUM汇总这些列字段；如果未指定，则聚合所有非主键的数值类型字段。(5) 在进行数据汇总时，因为分区内的数据已经基于ORBER BY排序，所以能够找到相邻且拥有相同聚合Key的数据。
(6) 在汇总数据时，同一分区内，相同聚合Key的多行数据会合并成一行。其中，汇总字段会进行SUM计算；对于那些非汇总字段，则会使用第一行数据的取值。(7) 支持嵌套结构，但列字段名称必须以Map后缀结尾。嵌套类型中，默认以第一个字段作为聚合Key。除第一个字段以外，任何名称以Key、Id或Type为后缀结尾的字段，都将和第一个字段一起组成复合Key。

## 4. 示例

```sql
CREATE TABLE summtt
(
    key UInt32,
    value UInt32
)
ENGINE = SummingMergeTree()
ORDER BY key
```
向其中写入数据：
```sql
INSERT INTO summtt VALUES(1,1),(1,2),(2,1)
```
ClickHouse 可能不会对所有行进行完整的求和处理，因此我们在查询中使用聚合函数 sum 和 GROUP BY 子句：
```sql
SELECT key, sum(value) FROM summtt GROUP BY key
```

`SummingMergeTree` 也支持嵌套类型的字段，在使用嵌套类型字段时，需要被 SUM 汇总的字段名称必须以 Map 后缀结尾，例如：
```sql
CREATE TABLE summing_table_nested (
    id String,
    nestMap Nested (
        id UInt32,
        key UInt32,
        val UInt64
    ),
    create_time DateTime
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM (create_time)
ORDER BY id;
```
在使用嵌套数据类型的时候，默认情况下，会以嵌套类型中第一个字段作为聚合条件Key。假设表内的数据如下所示：




> 参考：[SummingMergeTree 表引擎](https://clickhouse.com/docs/zh/engines/table-engines/mergetree-family/summingmergetree)
