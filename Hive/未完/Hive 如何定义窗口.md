SQL 结构化查询语言是数据分析领域的重要工具之一。它提供了数据筛选、转换、聚合等操作，并能借助 Hive 和 Hadoop 进行大数据量的处理。但是，传统的 SQL 语句并不能支持诸如分组排名、滑动平均值等计算，原因是 GROUP BY 语句只能为每个分组的数据返回一行结果，而非每条数据一行。幸运的是，新版的 SQL 标准引入了窗口查询功能，使用 WINDOW 语句我们可以基于分区和窗口为每条数据都生成一行结果记录，这一标准也已得到了 Hive 的支持。

![](https://shzhangji.com/cnblogs/images/hive-window/window-stock.png)

## 1. 认识




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

## 2. 窗口定义

SQL 窗口查询引入了三个新的概念：窗口分区、窗口帧以及窗口函数。

PARTITION 语句会按照一个或多个指定字段，将查询结果集拆分到不同的 窗口分区 中，并可按照一定规则排序。如果没有 PARTITION BY，则整个结果集将作为单个窗口分区；如果没有 ORDER BY，我们则无法定义窗口帧，进而整个分区将作为单个窗口帧进行处理。

窗口帧 用于从分区中选择指定的多条记录，供窗口函数处理。Hive 提供了两种定义窗口帧的形式：ROWS 和 RANGE。两种类型都需要配置上界和下界。例如，ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW 表示选择分区起始记录到当前记录的所有行；SUM(close) RANGE BETWEEN 100 PRECEDING AND 200 FOLLOWING 则通过 字段差值 来进行选择。如当前行的 close 字段值是 200，那么这个窗口帧的定义就会选择分区中 close 字段值落在 100 至 400 区间的记录。以下是所有可能的窗口帧定义组合。如果没有定义窗口帧，则默认为 RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW。

```
(ROWS | RANGE) BETWEEN (UNBOUNDED | [num]) PRECEDING AND ([num] PRECEDING | CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN CURRENT ROW AND (CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN [num] FOLLOWING AND (UNBOUNDED | [num]) FOLLOWING
```


## 1. 概述



## 2. 语法

```sql
Function (arg1,..., argn) OVER ([PARTITION BY <...>] [ORDER BY <....>] [<window_expression>])
```

## 窗口函数

绝大多数的聚合函数都可以配合窗口使用，例如 MAX()、MIN()、SUM()、COUNT()、AVG() 等。

## 3. 窗口大小

窗口大致的定义分为两种，一种是基于行的，一种是基于值的。


在 SELECT 语句中加入窗口函数，计算窗口函数的结果时，数据会按照窗口定义中的 PARTITION BY 和 ORDER BY 语句进行分区和排序：
- 如果没有 PARTITION BY 语句，那么只有一个分区，即一个包含全部数据的分区。
- 如果没有 ORDER BY 语句，则分区内的数据会按照任意顺序排布，最终生成一个数据流

之后对于每一行数据（当前行），会按照窗口定义中的 frame_clause 从数据流中截取一段数据，构成当前行的窗口。窗口函数会根据窗口中包含的数据，计算得到窗口函数针对当前行对应的输出结果。


| 名词 | 含义 |
| -------- | -------- |
| preceding     | 往前     |
| following     | 往后     |
| unbounded     | 无限     |
| current row     | 当前行     |
| unbounded preceding     | 无限往前，即起点     |
| unbounded following     | 无限往后，即终点     |
| N preceding     | 往前 N 行     |
| N following     | 往后 N 行     |


如果不指定 PARTITION BY，则不对数据进行分区，换句话说，所有数据看作同一个分区；
如果不指定 ORDER BY，则不对各分区做排序，通常用于那些顺序无关的窗口函数，例如 SUM()
如果不指定窗口子句，则默认采用以下的窗口定义：
- 若不指定 ORDER BY，默认使用分区内所有行 `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`
- 若指定了 ORDER BY，默认使用分区内第一行到当前值 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`

窗口计算过程：
- 按窗口定义，将所有输入数据分区、再排序（如果需要的话）
- 对每一行数据，计算它的窗口范围
- 将窗口内的行集合输入窗口函数，计算结果填入当前行


### 3.2 窗口帧 Frame

frame_clause 语法格式如下：
```sql
--格式一。
{ROWS|RANGE} <frame_start> [<frame_exclusion>]
--格式二。
{ROWS|RANGE} between <frame_start> and <frame_end> [<frame_exclusion>]
```

frame_clause 是一个闭区间，用于确定数据边界，包含 frame_start 和 frame_end 位置的数据行。

```sql
(ROWS | RANGE) BETWEEN (UNBOUNDED | [num]) PRECEDING AND ([num] PRECEDING | CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN CURRENT ROW AND (CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN [num] FOLLOWING AND (UNBOUNDED | [num]) FOLLOWING
```

- ROWS 类型：通过数据行数确定数据边界。
RANGE类型：通过比较order by列值的大小关系来确定数据边界。一般在窗口定义中会指定order by，未指定order by时，一个分区中的所有数据行具有相同的order by列值。NULL与NULL被认为是相等的。


开启 ROWS BETWEEN 是不是必须使用 ORDER BY ？


#### ROWS vs RANGE

ROWS BETWEEN AND 通过数据行数来确定窗口的边界，是物理意义上的行。比如 ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING 代表从当前行往前一行以及往后一行。

RANGE BETWEEN AND 通过比较 ORDER BY 列值的大小关系来确定窗口的边界。一般在窗口定义中会指定 ORDER BY，如果 未指定 ORDER BY 时，一个分区中的所有数据行具有相同的 ORDER BY 列值。NULL 与 NULL 被认为是相等的。


不是所有的函数在运行都是可以通过改变窗口的大小，来控制计算的数据集的范围！所有的排名函数和LAG,LEAD，支持使用over()，但是在over()中不能定义 window_clause


当为排序函数，如row_number(),rank()等时，over中的order by只起到窗口内排序作用。

当为聚合函数，如max，min，count等时，over中的order by不仅起到窗口内排序，还起到窗口内从当前行到之前所有行的聚合（多了一个范围）。

### 3.3 区间范围

#### Row

(1) 起始范围：

| Boundary1.type |  Boundary1.amt | Behavior |
| -------- | -------- | -------- |
| PRECEDING     | UNBOUNDED     | start = 0     |
| PRECEDING     | unsigned int  | start = R.idx - Boundary1.amt |
| CURRENT ROW   |               | start = R.idx |
| FOLLOWING     | UNBOUNDED     | Error |
| FOLLOWING     | unsigned int  | start = R.idx + b1.amt |

(2) 终止范围：

| Boundary2.type | Boundary2.amt | Behavior |
| -------- | -------- | -------- |
| PRECEDING | UNBOUNDED | Error |
| PRECEDING | unsigned int | end = R.idx - Boundary2.amt b2.amt == 0 => end = R.idx + 1 |
| CURRENT ROW | | end = R.idx + 1 |
| FOLLOWING | UNBOUNDED | end = Part Spec.size |
| FOLLOWING | unsigned int | end = R.idx + b2.amt + 1 |




资料：
- https://help.aliyun.com/document_detail/34994.html#section-w1o-ihh-omn
- https://www.studytime.xin/article/hive-knowledge-window-function.html
- https://mp.weixin.qq.com/s/mPpj_RYBztfKHZwZQCTCGQ

## 4. 聚合函数


参考：
- https://shzhangji.com/cnblogs/2017/09/05/hive-window-and-analytical-functions/
