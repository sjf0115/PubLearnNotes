
本文主要介绍了以下内容：

什么是确定性？
批处理都是确定性的吗？
两个非确定性结果的批查询示例
批处理中的不确定性因素
流上的确定性
流上的不确定性
流上的不确定更新
如何消除流查询的不确定性影响

## 1. 什么是确定性？

引用 SQL 标准中对`确定性`的描述：如果一个操作在重复相同输入值时能保证计算输出相同的结果，那么该操作就是`确定性`的。

## 2. 批处理都是确定性的吗？

在经典的批处理场景中，对于给定的有界数据集，重复执行同一查询会得到一致的结果，这就是对确定性最直观的理解。

### 2.1 两个非确定性结果的批查询示例

但实际上，同一个查询在批处理上也并不总是能得到一致的结果，来看如下两个查询示例。比如有一张新建的网站点击日志表：
```sql
CREATE TABLE clicks (
    uid VARCHAR(128),
    cTime TIMESTAMP(3),
    url VARCHAR(256)
)
```
写入一些新数据：
```sql
+------+---------------------+------------+
|  uid |               cTime |        url |
+------+---------------------+------------+
| Mary | 2022-08-22 12:00:01 |      /home |
|  Bob | 2022-08-22 12:00:01 |      /home |
| Mary | 2022-08-22 12:00:05 | /prod?id=1 |
|  Liz | 2022-08-22 12:01:00 |      /home |
| Mary | 2022-08-22 12:01:30 |      /cart |
|  Bob | 2022-08-22 12:01:35 | /prod?id=3 |
+------+---------------------+------------+
```
#### 2.1.1 查询1示例

对点击日志表进行时间过滤，筛选出最近 2 分钟的点击日志：
```sql
SELECT * FROM clicks
WHERE cTime BETWEEN TIMESTAMPADD(MINUTE, -2, CURRENT_TIMESTAMP) AND CURRENT_TIMESTAMP;
```
当在 '2022-08-22 12:02:00' 时刻提交该查询时，查询返回了表中全部的 6 条数据。一分钟后，也就是在 '2022-08-22 12:03:00' 时刻再次执行该查询时, 只返回了 3 条数据：
```sql
+------+---------------------+------------+
|  uid |               cTime |        url |
+------+---------------------+------------+
|  Liz | 2022-08-22 12:01:00 |      /home |
| Mary | 2022-08-22 12:01:30 |      /cart |
|  Bob | 2022-08-22 12:01:35 | /prod?id=3 |
+------+---------------------+------------+
```

#### 2.1.2 查询2示例

希望对每条返回的记录添加一个唯一标识（因为 clicks 表没有定义主键）：
```sql
SELECT UUID() AS uuid, * FROM clicks LIMIT 3;
```
连续执行两次该查询，同一条记录两次查询生成了不同的 uuid 标识：
```sql
-- 第 1 次执行
+--------------------------------+------+---------------------+------------+
|                           uuid |  uid |               cTime |        url |
+--------------------------------+------+---------------------+------------+
| aaaa4894-16d4-44d0-a763-03f... | Mary | 2022-08-22 12:00:01 |      /home |
| ed26fd46-960e-4228-aaf2-0aa... |  Bob | 2022-08-22 12:00:01 |      /home |
| 1886afc7-dfc6-4b20-a881-b0e... | Mary | 2022-08-22 12:00:05 | /prod?id=1 |
+--------------------------------+------+---------------------+------------+

-- 第 2 次执行
+--------------------------------+------+---------------------+------------+
|                           uuid |  uid |               cTime |        url |
+--------------------------------+------+---------------------+------------+
| 95f7301f-bcf2-4b6f-9cf3-1ea... | Mary | 2022-08-22 12:00:01 |      /home |
| 63301e2d-d180-4089-876f-683... |  Bob | 2022-08-22 12:00:01 |      /home |
| f24456d3-e942-43d1-a00f-fdb... | Mary | 2022-08-22 12:00:05 | /prod?id=1 |
+--------------------------------+------+---------------------+------------+
```

### 2.2 批处理中的不确定性

批处理中的不确定性, 主要是由`不确定函数`造成的，如上述两个查询示例中，内置函数 `CURRENT_TIMESTAMP` 和 `UUID()` 在批处理中的行为是有差异的。继续看一个查询示例：
```sql
SELECT CURRENT_TIMESTAMP, * FROM clicks;
```
`CURRENT_TIMESTAMP` 在返回的记录上都是同一个值：
```sql
+-------------------------+------+---------------------+------------+
|       CURRENT_TIMESTAMP |  uid |               cTime |        url |
+-------------------------+------+---------------------+------------+
| 2022-08-23 17:25:46.831 | Mary | 2022-08-22 12:00:01 |      /home |
| 2022-08-23 17:25:46.831 |  Bob | 2022-08-22 12:00:01 |      /home |
| 2022-08-23 17:25:46.831 | Mary | 2022-08-22 12:00:05 | /prod?id=1 |
| 2022-08-23 17:25:46.831 |  Liz | 2022-08-22 12:01:00 |      /home |
| 2022-08-23 17:25:46.831 | Mary | 2022-08-22 12:01:30 |      /cart |
| 2022-08-23 17:25:46.831 |  Bob | 2022-08-22 12:01:35 | /prod?id=3 |
+-------------------------+------+---------------------+------------+
```
这个差异是因为 Flink 继承了 Apache Calcite 对函数的定义，在确定性函数之外存在`不确定函数`和`动态函数`(内置的动态函数以时间函数为主)两类：不确定函数会在运行时执行（即在集群执行，每条记录单独计算）；而动态函数只有当生成查询计划时确定对应的值，运行时不再执行（不同时间执行得到不同的值，但同一次执行得到的值一致）。更多信息及完整的参见[内置函数的确定性](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/functions/udfs/#system-built-in-function-determinism)。

## 3. 流上的确定性

流和批处理的一个核心区别是数据的无界性，Flink SQL 对流计算抽象为[动态表上的连续查询](https://smartsi.blog.csdn.net/article/details/149184089)。 因此批查询示例中的动态函数在流场景中也成为了不确定性函数（逻辑上每条基表记录的变更都会触发查询被执行）。如下示例中如果 `clicks` 点击日志表来源于持续写入的 Kafka topic，同样的查询在流模式下返回的 `CURRENT_TIMESTAMP` 也就会随着时间推移而变化:
```sql
SELECT CURRENT_TIMESTAMP, * FROM clicks;
```
例如：
```sql
+-------------------------+------+---------------------+------------+
|       CURRENT_TIMESTAMP |  uid |               cTime |        url |
+-------------------------+------+---------------------+------------+
| 2022-08-23 17:25:46.831 | Mary | 2022-08-22 12:00:01 |      /home |
| 2022-08-23 17:25:47.001 |  Bob | 2022-08-22 12:00:01 |      /home |
| 2022-08-23 17:25:47.310 | Mary | 2022-08-22 12:00:05 | /prod?id=1 |
+-------------------------+------+---------------------+------------+
```

### 3.1 流上的不确定性

流上除了`不确定函数`，可能产生不确定性的主要有：
- Source Connector 回溯读取的不确定性
- 基于处理时间计算的不确定性
- 基于 TTL 淘汰内部状态数据的不确定性

#### 3.1.1 Source Connector 回溯读取的不确定性

对于 Flink SQL 来说，所能提供的确定性只局限于计算部分，因为它本身并不存储用户数据（这里有必要区分流下的托管内部状态和用户本身数据），所以对于无法提供确定性回溯读取数据的 Source Connector 实现会带来输入数据的不确定性，从而可能产生不确定的计算结果。常见的比如从指定相同时间点位 Offset 多次请求读取的数据不一致、或请求的数据因为保存时限已经不存在等（如请求的 Kafka topic 数据已经超出了保存时限）。

#### 3.1.2 基于处理时间计算的不确定性

区别于事件时间，处理时间是基于机器的本地时间，这种处理不能提供确定性。依赖时间属性的相关操作包括窗口聚合、Interval Join、Temporal Join 等。

另一个典型的操作是 Lookup Join，语义上是类似基于处理时间的 Temporal Join，访问的外部表如存在更新，就会产生不确定性。

#### 3.1.3 基于 TTL 淘汰内部状态数据的不确定性

因为流处理数据无界性的特点，长时间运行的流查询操作(例如常规 Join、分组聚合)维护的内部状态数据可能持续膨胀。开启状态 TTL 来淘汰内部状态数据很多时候是必要的妥协，但这种淘汰数据的方式可能让计算结果变得不确定。

这些不确定性对不同查询的影响是不同的，某些查询仅仅是产生不确定的结果（查询可以正常运行，只是多次运行无法得到确定一致的结果），而某些查询的不确定性会造成更严重的影响，比如结果错误甚至查询无法正常运行。后者的主要原因在于`不确定性更新`。

### 3.2 流上的不确定性更新

Flink SQL 基于[动态表上的连续查询](https://smartsi.blog.csdn.net/article/details/149184089)抽象实现了一套完整的增量更新机制，所有需要产生增量消息的操作都维护了完整的内部状态数据，整个查询管道（包含了从 Source、Sink 的完整执行图）的顺利运行依赖算子之间对更新消息的正确性传递保证，这种保证可能会被不确定性破坏从而导致错误。

什么是`不确定性更新`（Non-deterministic Update, 简称 `NDU`）？ 更新消息可能包含几种不同的类型：插入（`Insert`，简称 `I`）、删除（`Delete`，简称 `D`）、更新前（`Update_Before`，简称 `UB`），更新后（`Update_After`，简称 `UA`），在仅有插入类型的变更日志查询管道中不存在 `NDU` 问题。在有更新消息（除 `I` 外至少包含 `D`、`UB`、`UA` 的中一种）时，会根据查询推导消息的更新键（可视为变更日志的主键）：
- 能推导出更新键时，管道中的算子通过更新键来维护内部状态
- 不能推导出更新键时（有可能 CDC 源表或 Sink 表就没定义主键，也可能从查询的语义上某些操作就推导不出来），所有算子维护的内部状态只能通过完整的行来处理更新（D/UB/UA）消息, Sink 节点在没有定义主键时以 Retract 模式工作，按整行进行删除操作。 因此，在按行删除时，所有需要维护状态的算子收到的更新消息不能被不确定的列值干扰, 否则就会导致 NDU 问题造成计算错误。

在有更新消息传递并且无法推导出更新键的链路上，以下三点是最主要的 NDU 问题来源：

不确定函数（包括标量、表值、聚合类型的内置或自定义函数）
在一个变化的源表上 Lookup Join
CDC 源表携带了元数据字段（系统列，不属于实体行本身）
注意：基于 TTL 淘汰内部状态数据产生的不确定性造成的异常将作为一个运行时容错处理策略单独讨论(FLINK-24666)。

### 3.3 如何消除流查询的不确定性影响 #
流查询中的不确定更新(NDU)问题通常不是直观的，可能较复杂的查询中一个微小条件的改动就可能产生 NDU 问题风险，从 1.16 版本开始，Flink SQL (FLINK-27849)引入了实验性的 NDU 问题处理机制 ’table.optimizer.non-deterministic-update.strategy’， 当开启 TRY_RESOLVE 模式时，会检查流查询中是否存在 NDU 问题，并尝试消除由 Lookup Join 产生的不确定更新问题（内部会增加物化处理），如果还存在上述第 1 或 第 3 点因素无法自动消除，Flink SQL 会给出尽量详细的错误信息提示用户调整 SQL 来避免引入不确定性（考虑到物化带来的高成本和算子复杂性，目前还没有支持对应的自动解决机制）。

最佳实践 #
1. #
运行流查询前主动开启 TRY_RESOLVE 模式，在检查到流查询中存在无法解决的 NDU 问题时，尽量按照错误提示修改 SQL 主动避免问题

一个来源于 FLINK-27639 的真实案例：

INSERT INTO t_join_sink
SELECT o.order_id, o.order_name, l.logistics_id, l.logistics_target, l.logistics_source, now()
FROM t_order AS o
LEFT JOIN t_logistics AS l ON ord.order_id=logistics.order_id
在默认情况下生成的执行计划在运行时会发生撤回错误，当启用 TRY_RESOLVE 模式时, 会给出如下错误提示：

org.apache.flink.table.api.TableException: The column(s): logistics_time(generated by non-deterministic function: NOW ) can not satisfy the determinism requirement for correctly processing update message(changelogMode contains not only insert ‘I’).... Please consider removing these non-deterministic columns or making them deterministic.

related rel plan:
Calc(select=[CAST(order_id AS INTEGER) AS order_id, order_name, logistics_id, logistics_target, logistics_source, CAST(NOW() AS TIMESTAMP(6)) AS logistics_time], changelogMode=[I,UB,UA,D], upsertKeys=[])
+- Join(joinType=[LeftOuterJoin], where=[=(order_id, order_id0)], select=[order_id, order_name, logistics_id, logistics_target, logistics_source, order_id0], leftInputSpec=[JoinKeyContainsUniqueKey], rightInputSpec=[HasUniqueKey], changelogMode=[I,UB,UA,D], upsertKeys=[])
   :- Exchange(distribution=[hash[order_id]], changelogMode=[I,UB,UA,D], upsertKeys=[{0}])
   :  +- TableSourceScan(table=[[default_catalog, default_database, t_order, project=[order_id, order_name], metadata=[]]], fields=[order_id, order_name], changelogMode=[I,UB,UA,D], upsertKeys=[{0}])
   +- Exchange(distribution=[hash[order_id]], changelogMode=[I,UB,UA,D], upsertKeys=[])
      +- TableSourceScan(table=[[default_catalog, default_database, t_logistics, project=[logistics_id, logistics_target, logistics_source, order_id], metadata=[]]], fields=[logistics_id, logistics_target, logistics_source, order_id], changelogMode=[I,UB,UA,D], upsertKeys=[{0}])
按照错误提示，移除 now() 函数或使用其他确定性函数替代（或使用订单表中原始的时间字段），就可以消除上述 NDU 问题，避免运行时错误。

2. #
使用 Lookup Join 时，尽量带上主键定义（如果有的话）

带有主键定义的维表在很多情况下可以避免 Flink SQL 推导不出更新键，从而省去高昂的物化代价

以下两个案例描述了为什么鼓励用户为查询表声明主键：

insert into sink_with_pk
select t1.a, t1.b, t2.c
from (
  select *, proctime() proctime from cdc
) t1
join dim_with_pk for system_time as of t1.proctime as t2
   on t1.a = t2.a

-- 执行计划：声明了 pk 后的维表，通过 pk 连接时左流的 upsertKey 属性得以保留，从而节省了高开销的物化节点
Sink(table=[default_catalog.default_database.sink_with_pk], fields=[a, b, c])
+- Calc(select=[a, b, c])
   +- LookupJoin(table=[default_catalog.default_database.dim_with_pk], joinType=[InnerJoin], lookup=[a=a], select=[a, b, a, c])
      +- DropUpdateBefore
         +- TableSourceScan(table=[[default_catalog, default_database, cdc, project=[a, b], metadata=[]]], fields=[a, b])   
insert into sink_with_pk
select t1.a, t1.b, t2.c
from (
  select *, proctime() proctime from cdc
) t1
join dim_without_pk for system_time as of t1.proctime as t2
   on t1.a = t2.a

-- 不启用 `TRY_RESOLVE` 模式时在运行时可能产生错误，当启用 `TRY_RESOLVE` 时的执行计划
Sink(table=[default_catalog.default_database.sink_with_pk], fields=[a, b, c], upsertMaterialize=[true])
+- Calc(select=[a, b, c])
   +- LookupJoin(table=[default_catalog.default_database.dim_without_pk], joinType=[InnerJoin], lookup=[a=a], select=[a, b, a, c], upsertMaterialize=[true])
      +- TableSourceScan(table=[[default_catalog, default_database, cdc, project=[a, b], metadata=[]]], fields=[a, b])
尽管第二个查询可以通过启用 TRY_RESOLVE 选项（增加物化）来解决正确性问题，但成本高昂，与声明了主键的第一个查询相比，会多出两个更昂贵的物化操作。

3. #
当 Lookup Join 访问的查找表是静态的，可以不启用 TRY_RESOLVE 模式

当 Lookup Join 访问的是静态数据，可以先开启 TRY_RESOLVE 模式检查没有其他 NDU 问题后，再恢复 IGNORE 模式，避免不必要的物化开销。

注意：这里需要确保查找表是纯静态不更新的，否则 IGNORE 模式是不安全的。
