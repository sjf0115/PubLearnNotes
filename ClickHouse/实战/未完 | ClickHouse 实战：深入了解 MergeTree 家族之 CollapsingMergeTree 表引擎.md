假设现在需要设计一款数据库，该数据库支持对已经存在的数据实现行级粒度的修改或删除，你会怎么设计？一种最符合常理的思维可能是：首先找到保存数据的文件，接着修改这个文件，删除或者修改那些需要变化的数据行。然而在大数据领域，对于ClickHouse这类高性能分析型数据库而言，对数据源文件修改是一件非常奢侈且代价高昂的操作。相较于直接修改源文件，它们会将修改和删除操作转换成新增操作，即以增代删。CollapsingMergeTree就是一种通过以增代删的思路，支持行级数据修改和删除的表引擎。它通过定义一个sign标记位字段，记录数据行的状态。如果sign标记为1，则表示这是一行有效的数据；如果sign标记为-1，则表示这行数据需要被删除。当CollapsingMergeTree分区合并时，同一数据分区内，sign标记为1和-1的一组数据会被抵消删除。这种1和-1相互抵消的操作，犹如将一张瓦楞纸折叠了一般。这种直观的比喻，想必也正是折叠合并树 (CollapsingMergeTree) 名称的由来。

CollapsingMergeTree 引擎继承自 MergeTree， 并在合并过程中增加了对行进行折叠的逻辑。 CollapsingMergeTree 表引擎会异步删除（折叠） 成对的行，如果排序键（ORDER BY）中的所有字段都相同，且仅特殊字段 Sign 不同， 并且 Sign 字段只能取值 1 或 -1。 没有与之构成 Sign 取值相反配对的行会被保留。

> 此引擎可以显著减少存储空间占用， 从而提高 SELECT 查询的效率。

## 2. 语法

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster] (
    name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1],
    name2 [type2] [DEFAULT|MATERIALIZED|ALIAS expr2],
    ...
)
ENGINE = CollapsingMergeTree(Sign)
[PARTITION BY expr]
[ORDER BY expr]
[SAMPLE BY expr]
[SETTINGS name=value, ...]
```
从上面可以看到创建一张 `CollapsingMergeTree` 表的方法与创建普通 `MergeTree` 表无异，只需要替换 Engine：
```sql
ENGINE = CollapsingMergeTree (Sign)
```

## 3. 折叠

考虑这样一种情况：你需要为某个给定对象保存持续变化的数据。看起来为每个对象只保留一行并在有变化时更新它似乎是合乎逻辑的， 然而，更新操作对数据库管理系统（DBMS）来说代价高且缓慢，因为它们需要在存储中重写数据。 如果我们需要快速写入数据，执行大量更新操作并不是可接受的方法， 但我们始终可以按顺序写入某个对象的变更。 为此，我们使用特殊列 Sign。
- 如果 Sign = 1，表示该行是一个'状态（state）'行：一行包含表示当前有效状态的字段。
- 如果 Sign = -1，表示该行是一个'撤销（cancel）'行：一行用于撤销具有相同属性的对象状态。

例如，我们希望统计用户在某个网站上查看了多少页面以及访问这些页面的时长。 在某个给定时间点，我们写入如下记录用户活动状态的一行数据：
```
┌──────────────UserID─┬─PageViews─┬─Duration─┬─Sign─┐
│ 4324182021466249494 │         5 │      146 │    1 │
└─────────────────────┴───────────┴──────────┴──────┘
```
随后，当我们检测到用户活动发生变化时，会使用以下两行将其写入表中：
```
┌──────────────UserID─┬─PageViews─┬─Duration─┬─Sign─┐
│ 4324182021466249494 │         5 │      146 │   -1 │
│ 4324182021466249494 │         6 │      185 │    1 │
└─────────────────────┴───────────┴──────────┴──────┘
```
第一行会取消该对象之前的状态（在本例中表示一个用户）。 对于该“已取消”行，应复制所有排序键字段，Sign 字段除外。 上面的第二行表示当前状态。

由于我们只需要用户活动的最终状态，原始的 “state” 行和我们插入的 “cancel” 行可以像下方所示那样删除，从而折叠对象的无效（旧）状态：
```
┌──────────────UserID─┬─PageViews─┬─Duration─┬─Sign─┐
│ 4324182021466249494 │         5 │      146 │    1 │ -- old "state" row can be deleted
│ 4324182021466249494 │         5 │      146 │   -1 │ -- "cancel" row can be deleted
│ 4324182021466249494 │         6 │      185 │    1 │ -- new "state" row remains
└─────────────────────┴───────────┴──────────┴──────┘
```
CollapsingMergeTree 在合并数据分片时，会执行这种折叠行为。

这种方法的特点
- 写入数据的程序必须记住对象的状态，才能在需要时将其取消。“cancel” 行应包含与 “state” 行相同的排序键字段，以及相反的 Sign。这会增加初始存储占用，但 **可以让我们快速写入数据**。
- 列中不断增长的长数组会因为写入负载增加而降低引擎效率。数据越简单，效率越高。
- SELECT 的结果高度依赖于对象变更历史的一致性。在准备要插入的数据时要谨慎。对于不一致的数据，可能会得到不可预测的结果。例如，本应非负的指标（如会话深度）出现负值。





https://mp.weixin.qq.com/s/so5lpHGCbi3GB8qfNSUPrQ


https://clickhouse.com/docs/zh/engines/table-engines/mergetree-family/collapsingmergetree
