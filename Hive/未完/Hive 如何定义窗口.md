SQL 结构化查询语言是数据分析领域的重要工具之一。它提供了数据筛选、转换、聚合等操作，并能借助 Hive 和 Hadoop 进行大数据量的处理。但是，传统的 SQL 语句并不能支持诸如分组排名、滑动平均值等计算，原因是 GROUP BY 语句只能为每个分组的数据返回一行结果，而非每条数据一行。幸运的是，新版的 SQL 标准引入了窗口查询功能，使用 WINDOW 语句我们可以基于分区和窗口为每条数据都生成一行结果记录，这一标准也已得到了 Hive 的支持。

![](https://shzhangji.com/cnblogs/images/hive-window/window-stock.png)

```sql
SELECT
  uid, dt, score,
  AVG(score) OVER w AS avg_score
FROM (
   SELECT 'a' AS uid, '20220811' AS dt, 10 AS score
   UNION ALL
   SELECT 'a' AS uid, '20220812' AS dt, 18 AS score
   UNION ALL
   SELECT 'a' AS uid, '20220813' AS dt, 15 AS score
   UNION ALL
   SELECT 'b' AS uid, '20220813' AS dt, 10 AS score
   UNION ALL
   SELECT 'b' AS uid, '20220812' AS dt, 6 AS score
   UNION ALL
   SELECT 'b' AS uid, '20220811' AS dt, 1 AS score
) AS a
WINDOW w AS (PARTITION BY uid ORDER BY dt ROWS BETWEEN 1 PRECEDING AND CURRENT ROW);
```
OVER、WINDOW、以及 ROWS BETWEEN AND 都是新增的窗口查询关键字。在这个查询中，PARTITION BY 和 ORDER BY 的工作方式与 GROUP BY、ORDER BY 相似，区别在于它们不会将多行记录聚合成一条结果，而是将它们拆分到互不重叠的分区中进行后续处理。其后的 ROWS BETWEEN AND 语句用于构建一个窗口帧。此例中，每一个窗口帧都包含了当前记录和上一条记录。下文会对窗口帧做进一步描述。最后，AVG 是一个窗口函数，用于计算每个窗口帧的结果。窗口帧的定义（WINDOW 语句）还可以直接附加到窗口函数之后：
```sql
SELECT
  uid, dt, score,
  AVG(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) AS avg_score
FROM ...
```

## 2. 窗口的基本概念

SQL 窗口查询引入了三个新的概念：窗口分区、窗口帧以及窗口函数。

PARTITION 语句会按照一个或多个指定字段，将查询结果集拆分到不同的 窗口分区 中，并可按照一定规则排序。如果没有 PARTITION BY，则整个结果集将作为单个窗口分区；如果没有 ORDER BY，我们则无法定义窗口帧，进而整个分区将作为单个窗口帧进行处理。

窗口帧 用于从分区中选择指定的多条记录，供窗口函数处理。Hive 提供了两种定义窗口帧的形式：ROWS 和 RANGE。两种类型都需要配置上界和下界。例如，ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW 表示选择分区起始记录到当前记录的所有行；SUM(close) RANGE BETWEEN 100 PRECEDING AND 200 FOLLOWING 则通过 字段差值 来进行选择。如当前行的 close 字段值是 200，那么这个窗口帧的定义就会选择分区中 close 字段值落在 100 至 400 区间的记录。以下是所有可能的窗口帧定义组合。如果没有定义窗口帧，则默认为 RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW。

```
(ROWS | RANGE) BETWEEN (UNBOUNDED | [num]) PRECEDING AND ([num] PRECEDING | CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN CURRENT ROW AND (CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN [num] FOLLOWING AND (UNBOUNDED | [num]) FOLLOWING
```

参考：
- https://shzhangji.com/cnblogs/2017/09/05/hive-window-and-analytical-functions/
