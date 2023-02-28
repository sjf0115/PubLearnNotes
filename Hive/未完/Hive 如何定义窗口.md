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

```sql
(ROWS | RANGE) BETWEEN (UNBOUNDED | [num]) PRECEDING AND ([num] PRECEDING | CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN CURRENT ROW AND (CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN [num] FOLLOWING AND (UNBOUNDED | [num]) FOLLOWING
```


## 1. 概述



## 2. 语法

```sql
Function (arg1,..., argn) OVER ([PARTITION BY <...>] [ORDER BY <....>] [<window_expression>])
```

窗口计算过程：
- 按窗口定义，将所有输入数据分区、再排序（如果需要的话）
- 对每一行数据，计算它的窗口范围
- 将窗口内的行集合输入窗口函数，计算结果填入当前行

### 2.1 窗口函数

绝大多数的聚合函数都可以配合窗口使用，例如 MAX()、MIN()、SUM()、COUNT()、AVG() 等。

### 2.2 窗口大小

窗口大小定义语法格式如下：
```sql
(ROWS | RANGE) BETWEEN <start> AND <end>
```

定义的窗口是一个闭区间，用于确定数据边界，注意包含 start 和 end 位置的数据行。从上面可以看出窗口大小定义分为两种，一种是基于行的(ROWS)，一种是基于值的(RANGE)：
- 基于行 ROWS 类型
  - 通过数据行数确定数据边界。
- 基于值 RANGE 类型
  - 通过比较 ORDER BY 指定的列值大小关系来确定数据边界。

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


不是所有的函数在运行都是可以通过改变窗口的大小，来控制计算的数据集的范围！所有的排名函数和LAG,LEAD，支持使用over()，但是在over()中不能定义 window_clause


#### 2.2.1 ROWS

ROWS 类型是基于行类型，需要通过数据行数来确定窗口边界，是物理意义上的行。比如 ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING 代表从当前行往前一行以及往后一行。


```sql
ROWS BETWEEN (UNBOUNDED | [num]) PRECEDING AND ([num] PRECEDING | CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
ROWS BETWEEN CURRENT ROW AND (CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
ROWS BETWEEN [num] FOLLOWING AND (UNBOUNDED | [num]) FOLLOWING
```

> 假设 idx 表示当前行的下标

| 起始 |  终止 | 窗口范围 | 说明 |
| -------- | -------- | -------- | -------- |
| UNBOUNDED PRECEDING  | [N] PRECEDING       | [0, idx - N]               |
| UNBOUNDED PRECEDING  | CURRENT ROW         | [0, idx]                   |
| UNBOUNDED PRECEDING  | [N] FOLLOWING       | [0, idx + N]               |
| UNBOUNDED PRECEDING  | UNBOUNDED FOLLOWING | [0, size - 1]              |
| [N] PRECEDING        | [M] PRECEDING       | [idx - N, idx - M], N >= M |
| [N] PRECEDING        | CURRENT ROW         | [idx - N, idx]             |
| [N] PRECEDING        | [M] FOLLOWING       | [idx - N, idx + M]         |
| [N] PRECEDING        | UNBOUNDED FOLLOWING | [idx - N, size - 1]        |
| CURRENT ROW          | CURRENT ROW         | [idx, idx]                 |
| CURRENT ROW          | [M] FOLLOWING       | [idx, idx + M]             |
| CURRENT ROW          | UNBOUNDED FOLLOWING | [idx, size - 1]            |
| [N] FOLLOWING        | [M] FOLLOWING       | [idx + N, idx + M], N <= M |
| [N] FOLLOWING        | UNBOUNDED FOLLOWING | [idx + N, size - 1]        |

> 需要注意的是在 ROWS 类型下 `[N] PRECEDING` 表示当前行往后倒退 N 行，同样的 `[M] FOLLOWING` 表示当前行往前前进 M 行

```sql
WITH behavior AS (
  SELECT 'a' AS uid, '20230211' AS dt, 1 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230213' AS dt, 3 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230214' AS dt, 4 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230212' AS dt, 2 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230215' AS dt, 5 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230216' AS dt, 6 AS score
)
SELECT
  uid, dt, score,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS s1,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS s2,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND 1 FOLLOWING) AS s3,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS s4,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN 2 PRECEDING AND 1 PRECEDING) AS s5,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS s6,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN 2 PRECEDING AND 1 FOLLOWING) AS s7,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN 2 PRECEDING AND UNBOUNDED FOLLOWING) AS s8,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN CURRENT ROW AND CURRENT ROW) AS s9,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN CURRENT ROW AND 1 FOLLOWING) AS s10,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) AS s11,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN 1 FOLLOWING AND 2 FOLLOWING) AS s12,
  COLLECT_SET(score) OVER (ORDER BY dt ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS s13
FROM behavior;
```

#### 2.2.2 RANGE

RANGE 类型，是基于值类型，需要通过比较 ORDER BY 指定的列值大小关系来确定数据边界。

```sql
RANGE BETWEEN (UNBOUNDED | [num]) PRECEDING AND ([num] PRECEDING | CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
RANGE BETWEEN CURRENT ROW AND (CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
RANGE BETWEEN [num] FOLLOWING AND (UNBOUNDED | [num]) FOLLOWING
```

| 起始 |  终止 | 窗口范围 |
| -------- | -------- | -------- |
| UNBOUNDED PRECEDING  | [N] PRECEDING       | [0, idx - N]   |
| UNBOUNDED PRECEDING  | CURRENT ROW         | [0, idx]     |
| UNBOUNDED PRECEDING  | [N] FOLLOWING       | [0, idx + N]   |
| UNBOUNDED PRECEDING  | UNBOUNDED FOLLOWING | [0, size - 1]  |
| [N] PRECEDING        | [M] PRECEDING       | [idx - N, idx - M], N >= M |
| [N] PRECEDING        | CURRENT ROW         | [idx - N, idx] |
| [N] PRECEDING        | [M] FOLLOWING       | [idx - N, idx + M] |
| [N] PRECEDING        | UNBOUNDED FOLLOWING | [idx - N, size - 1] |
| CURRENT ROW          | CURRENT ROW         | [idx, idx] |
| CURRENT ROW          | [M] FOLLOWING       | [idx, idx + M] |
| CURRENT ROW          | UNBOUNDED FOLLOWING | [idx, size - 1] |
| [N] FOLLOWING        | [M] FOLLOWING       | [idx + N, idx + M], N <= M |
| [N] FOLLOWING        | UNBOUNDED FOLLOWING | [idx + N, size - 1] |

> 需要注意的是在 RANGE 类型下 `[N] PRECEDING` 表示当前值减去 N，同样的 `[M] FOLLOWING` 表示当前值加上 M
> Window Frame Boundary Amount must be a positive integer

```sql
WITH behavior AS (
  SELECT 'a' AS uid, '20230211' AS dt, 1 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230213' AS dt, 3 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230214' AS dt, 4 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230212' AS dt, 2 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230215' AS dt, 5 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230216' AS dt, 6 AS score
)
SELECT
  uid, dt, score,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS s1,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS s2,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN UNBOUNDED PRECEDING AND 1 FOLLOWING) AS s3,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS s4,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 2 PRECEDING AND 1 PRECEDING) AS s5,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 2 PRECEDING AND CURRENT ROW) AS s6,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 2 PRECEDING AND 1 FOLLOWING) AS s7,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 2 PRECEDING AND UNBOUNDED FOLLOWING) AS s8,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN CURRENT ROW AND CURRENT ROW) AS s9,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN CURRENT ROW AND 1 FOLLOWING) AS s10,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) AS s11,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 1 FOLLOWING AND 2 FOLLOWING) AS s12,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS s13
FROM behavior;
```

WITH behavior AS (
  SELECT 'a' AS uid, '20230211' AS dt, 1 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230212' AS dt, 2 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230213' AS dt, 3 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230214' AS dt, 4 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230215' AS dt, 5 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230216' AS dt, 6 AS score
)
SELECT
  uid, dt, score,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS s1,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 3 PRECEDING AND 1 PRECEDING) AS s2,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 1 FOLLOWING AND 2 FOLLOWING) AS s3,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS s4
FROM behavior;




我们以 dt = '20230214' 这一行数据为例，ORDER BY 指定值比较字段为 score，即当前值为 4：
- `UNBOUNDED PRECEDING AND 1 PRECEDING` 表示的范围为 `(-∞, 3]` s1 结果应该为 `[1, 2, 3]`，但结果为 `[1,2]` 不符合预期
- `3 PRECEDING AND 1 PRECEDING` 表示的范围为 `[1, 3]`，s2 结果应该为 `[1, 2, 3]`，但结果为 `[1,2]` 不符合预期
- `1 FOLLOWING AND 2 FOLLOWING` 表示的范围为 `[5, 6]`，s3 结果应该为 `[5 ,6]`，但结果为 `[6]` 不符合预期
- `1 FOLLOWING AND UNBOUNDED FOLLOWING` 表示的范围为 `[5, +∞)`，s4 结果应该为 `[5 ,6]`，但结果为 `[6]` 不符合预期





输出结果如下所示：

![](2)

我们以 dt = '20230214' 这一行数据为例，ORDER BY 指定值比较字段为 score，即当前值为 4：
- `UNBOUNDED PRECEDING AND 1 PRECEDING` 表示的范围为 `(-∞, 3]` s1 结果为 `[1, 2, 3]` 结果不符合预期
- `UNBOUNDED PRECEDING AND CURRENT ROW` 表示的范围为 `(-∞, 4]`，s2 结果为 `[1, 2, 3, 4]`
- `UNBOUNDED PRECEDING AND 1 FOLLOWING` 表示的范围为 `(-∞, 5]`，s3 结果为 `[1, 2, 3, 4, 5]`
- `UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` 表示的范围为 `(-∞, +∞)`，s4 结果为 `[1, 2, 3, 4, 5, 6]`
- `2 PRECEDING AND 1 PRECEDING` 表示的范围为 `[2, 3]`，s5 结果为 `[2, 3]` 结果不符合预期
- `2 PRECEDING AND CURRENT ROW` 表示的范围为 `[2, 4]`，s6 结果为 `[2, 3, 4]`      
- `2 PRECEDING AND 1 FOLLOWING` 表示的范围为 `[2, 5]`，s7 结果为 `[2, 3, 4, 5]`   
- `2 PRECEDING AND UNBOUNDED FOLLOWING` 表示的范围为 `[2, +∞)`，s8 结果为 `[2, 3, 4, 5, 6]`   
- `CURRENT ROW AND CURRENT ROW` 表示的范围为 `[4, 4]`，s9 结果为 `[4]`   
- `CURRENT ROW AND 1 FOLLOWING` 表示的范围为 `[4, 5]`，s10 结果为 `[4, 5]`   
- `CURRENT ROW AND UNBOUNDED FOLLOWING` 表示的范围为 `[4, +∞)`，s11 结果为 `[4, 5 ,6]`
- `1 FOLLOWING AND 2 FOLLOWING` 表示的范围为 `[5, 6]`，s12 结果为 `[5 ,6]` 结果不符合预期
- `1 FOLLOWING AND UNBOUNDED FOLLOWING` 表示的范围为 `[5, +∞)`，s13 结果为 `[5 ,6]` 结果不符合预期


- `UNBOUNDED PRECEDING AND 1 PRECEDING` 表示的范围为 `(-∞, 3]` s1 结果为 `[1, 2, 3]` 结果不符合预期
- `3 PRECEDING AND 1 PRECEDING` 表示的范围为 `[2, 3]`，s5 结果为 `[2, 3]` 结果不符合预期
- `1 FOLLOWING AND 2 FOLLOWING` 表示的范围为 `[5, 6]`，s12 结果为 `[5 ,6]` 结果不符合预期
- `1 FOLLOWING AND UNBOUNDED FOLLOWING` 表示的范围为 `[5, +∞)`，s13 结果为 `[5 ,6]` 结果不符合预期


开启 ROWS BETWEEN 是不是必须使用 ORDER BY ？


WITH behavior AS (
  SELECT 'a' AS uid, '20230211' AS dt, 1 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230213' AS dt, 3 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230214' AS dt, 4 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230212' AS dt, 2 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230215' AS dt, 5 AS score
  UNION ALL
  SELECT 'a' AS uid, '20230216' AS dt, 6 AS score
)
SELECT
  uid, dt, score,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS s2,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN UNBOUNDED PRECEDING AND 2 PRECEDING) AS s3,
  COLLECT_SET(score) OVER (ORDER BY score RANGE BETWEEN UNBOUNDED PRECEDING AND 3 PRECEDING) AS s4
FROM behavior;


#### 2.2.3 ROWS vs RANGE


RANGE BETWEEN AND 通过比较 ORDER BY 列值的大小关系来确定窗口的边界。一般在窗口定义中会指定 ORDER BY，如果 未指定 ORDER BY 时，一个分区中的所有数据行具有相同的 ORDER BY 列值。NULL 与 NULL 被认为是相等的。


当为排序函数，如row_number(),rank()等时，over中的order by只起到窗口内排序作用。

当为聚合函数，如max，min，count等时，over中的order by不仅起到窗口内排序，还起到窗口内从当前行到之前所有行的聚合（多了一个范围）。

如果不指定窗口子句，则默认采用以下的窗口定义：
- 若不指定 ORDER BY，默认使用分区内所有行 `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`
- 若指定了 ORDER BY，默认使用分区内第一行到当前值 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`

### 2.3 PARTITION BY


在 SELECT 语句中加入窗口函数，计算窗口函数的结果时，数据会按照窗口定义中的 PARTITION BY 和 ORDER BY 语句进行分区和排序。如果没有 PARTITION BY 语句，那么只有一个分区，即一个包含全部数据的分区。


之后对于每一行数据（当前行），会按照窗口定义中的 frame_clause 从数据流中截取一段数据，构成当前行的窗口。窗口函数会根据窗口中包含的数据，计算得到窗口函数针对当前行对应的输出结果。

### 2.4 ORDER BY

在 SELECT 语句中加入窗口函数，计算窗口函数的结果时，数据会按照窗口定义中的 PARTITION BY 和 ORDER BY 语句进行分区和排序。如果没有 ORDER BY 语句，则分区内的数据会按照任意顺序排布，最终生成一个数据流。


基于行 ROWS 类型中，ORDER BY 的作用是指定行的顺序。只有顺序是固定的，基于行的计算才是有意义的。
基于值 RANGE 类型中，ORDER BY 的作用是指定通过哪个字段值的大小关系来确定窗口的边界。在这种情况下不需要考虑上下行的顺序，而是通过字段值的范围来划分窗口。



如果不指定 ORDER BY，则不对各分区做排序，通常用于那些顺序无关的窗口函数，例如 SUM()


一般在窗口定义中会指定order by，未指定order by时，一个分区中的所有数据行具有相同的order by列值。NULL与NULL被认为是相等的。



资料：
- https://help.aliyun.com/document_detail/34994.html#section-w1o-ihh-omn
- https://www.studytime.xin/article/hive-knowledge-window-function.html
- https://mp.weixin.qq.com/s/mPpj_RYBztfKHZwZQCTCGQ
- https://shzhangji.com/cnblogs/2017/09/05/hive-window-and-analytical-functions/
