
## 1. 窗口介绍

窗口函数支持在一个动态定义的数据子集上执行聚合操作或其他计算，常用于处理时间序列数据、排名、移动平均等问题，本文为您介绍窗口函数的命令格式、参数说明及示例。

## 2. 窗口核心三要素

窗口的语法声明如下:
```sql
-- partition_clause：
[partition by <expression> [, ...]]
-- orderby_clause：
[order by <expression> [asc|desc][nulls {first|last}] [, ...]]
-- frame_clause：
[<frame_clause>]
```

- 窗口分区子句 partition_clause：是一个可选子句。使用 PARTITION BY 关键词指定，类似 GROUP BY 的分组逻辑。分区列的值相同的行被视为在同一个窗口内。
- 窗口排序子句 orderby_clause：是一个可选子句。使用 ORDER BY 关键词指定，指定数据在一个窗口内如何排序
- 窗口框架子句 frame_clause：是一个可选子句。使用 ROWS/RANGE 关键词指定，确定计算范围的关键


在 SELECT 语句中加入窗口函数，计算窗口函数的结果时，数据会按照窗口定义中的 PARTITION BY 和 ORDER BY 语句进行分区和排序:
- 如果没有 PARTITION BY 语句，则仅有一个分区，包含全部数据。
- 如果没有 ORDER BY 语句，则分区内的数据会按照任意顺序排布，最终生成一个数据流。

对于每一行数据（当前行），会按照窗口定义中的 frame_clause 从数据流中截取一段数据，构成当前行的窗口。窗口函数会根据窗口中包含的数据，计算得到窗口函数针对当前行对应的输出结果。


### 2.1 Filter 子句

Hive 目前不支持标准 SQL 的 FILTER 语法。最常用的替代方法是使用 CASE WHEN 条件表达式
```sql
sql
SELECT
  dept,
  SUM(CASE WHEN region = 'North' THEN sales ELSE 0 END)
    OVER (PARTITION BY dept) AS north_sales,
  AVG(CASE WHEN quarter = 'Q4' THEN profit ELSE NULL END)
    OVER (ORDER BY date ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)
    AS q4_moving_avg
FROM sales_data;
```
> 对数值型字段使用 ELSE 0 保持数值计算逻辑；对平均计算使用 ELSE NULL 避免计入无效值


FILTER 子句的语法声明如下：
```sql
FILTER (WHERE filter_condition)
```
> 其中 `filter_condition` 为布尔表达式，和 `SELECT ... FROM ... WHERE` 语句中的 `WHERE` 用法完全相同。

如果提供了 FILTER 子句，则只有 `filter_condition` 值为 true 的行才会包含在窗口 frame 中。对于聚合窗口函数（包括：COUNT、SUM、AVG、MAX、MIN、WM_CONCAT等）仍为每行返回一个值，但 FILTER 表达式计算结果为 true 以外的值（NULL或FALSE）不会包含在任何行的窗口frame中。

需要注意的是 FILTER 子句并不会在查询结果中过滤掉不满足 `filter_condition` 的行，只是影响窗口函数计算的范围，认为这一行不存在。如果想要过滤掉相应的行，仍然需要在 `SELECT ... FROM ... WHERE` 语句中指定。此外这一行的窗口函数值并不是直接返回 0 或者 NULL，而是沿用前一行的窗口函数值(窗口函数计算时认为这一行不存在)。

只有当窗口函数为聚合类函数（包括：COUNT、SUM、AVG、MAX、MIN、WM_CONCAT等）时，才能使用 FILTER 子句，非聚合类函数（例如：RANK、ROW_NUMBER、NTILE）不能使用 FILTER 子句，否则会出现语法错误。

```sql
SET odps.sql.hive.compatible=TRUE;
WITH behavior AS (
    SELECT uid, dt, score
    FROM VALUES
        ('a', '20230211', 9),
        ('a', '20230213', 7),
        ('a', '20230214', 14),
        ('a', '20230212', 6),
        ('a', '20230215', 2),
        ('a', '20230216', 1),
        ('b', '20230216', 9),
        ('b', '20230211', 8),
        ('b', '20230213', 5),
        ('b', '20230214', 1)
        t (uid, dt, score)
)
SELECT
  uid, dt, score,
  MAX(score) FILTER(WHERE score > 5) OVER (PARTITION BY uid ORDER BY dt) AS max_score,
  MIN(score) FILTER(WHERE score > 5) OVER (PARTITION BY uid ORDER BY dt) AS min_score,
  SUM(score) FILTER(WHERE score > 5) OVER (PARTITION BY uid ORDER BY dt) AS sum_score,
  COUNT(*) FILTER(WHERE score > 5) OVER (PARTITION BY uid ORDER BY dt) AS count_score,
  COLLECT_LIST(score) FILTER(WHERE score > 5) OVER (PARTITION BY uid ORDER BY dt) AS collect_score
FROM behavior;
```

![undefined](https://intranetproxy.alipay.com/skylark/lark/0/2025/png/158678/1740015681080-26301475-9920-4de2-923f-71bd21d289c7.png)


## 3. 窗口分区子句

窗口分区子句 partition_clause 使用 PARTITION BY 关键词指定：
```sql
MAX(score) OVER (PARTITION BY uid ORDER BY dt)
```
类似 GROUP BY 的分组逻辑。分区列值相同的行被视为在同一个窗口内，上述语句中相同 uid 的归属到同一个窗口内。

窗口分区子句是一个可选子句，如果没有 PARTITION BY 语句，则仅有一个分区，包含全部数据。

## 4. 窗口排序子句

窗口排序子句 orderby_clause 使用 ORDER BY 关键词指定，指定数据在一个窗口内如何排序：
```sql
MAX(score) OVER (PARTITION BY uid ORDER BY dt)
```
窗口排序子句是一个可选子句。如果没有 ORDER BY 语句，则分区内的数据会按照任意顺序排列，最终生成一个数据流。

## 5. 窗口框架子句

窗口框架子句 frame_clause 支持三种类型语法：ROWS、RANGE、GROUPS。每种语法都支持同样的两种格式：
```sql
--格式一。
{ROWS|RANGE|GROUPS} <frame_start> [<frame_exclusion>]
--格式二。
{ROWS|RANGE|GROUPS} between <frame_start> and <frame_end> [<frame_exclusion>]
```

窗口框架子句 frame_clause 是一个闭区间，用于确定数据边界，包含 `frame_start` 和 `frame_end` 边界的数据行。

ROWS、RANGE、GROUPS 标识窗口框架子句 frame_clause 的类型，`frame_start`、`frame_end` 分别表示窗口的起始和终止边界。各类型的 `frame_start` 和 `frame_end` 实现规则不相同，下面会详细介绍。`frame_start` 必填，而 `frame_end` 是可选的，省略时默认为 `CURRENT ROW`。

`frame_start` 确定的位置必须在 `frame_end` 确定的位置的前面，或者等于 `frame_end` 的位置，即 `frame_start` 相比 `frame_end` 更靠近分区头部。分区头部是指数据按窗口定义中的 ORDER BY 语句排序之后第1行数据的位置。

### 5.1 ROWS

ROWS 类型 Frame 子句通过数据行数确定数据边界。


| frame_start/frame_end | 含义 | 说明 |
| -------- | -------- | -------- |
| UNBOUNDED PRECEDING | 表示分区的第一行，从1开始计数 | |
| UNBOUNDED FOLLOWING | 表示分区的最后一行 |
| CURRENT ROW | 当前行 | 每一行数据都会对应一个窗口函数的结果值，当前行是指在给哪一行数据计算窗口函数的结果 |
| offset PRECEDING | 从当前行位置，向分区头部位置移动offset行的位置 | 例如0 PRECEDING指当前行，1 PRECEDING指前一行。offset必须为非负整数。|
| offset FOLLOWING | 从当前行位置，向分区尾部移动offset行的位置 | 例如0 FOLLOWING指当前行，1 FOLLOWING指下一行。offset必须为非负整数。|


```sql
WITH behavior AS (
    SELECT uid, dt, score
    FROM VALUES
        ('a', '20230211', 9),
        ('a', '20230213', 7),
        ('a', '20230214', 14),
        ('a', '20230212', 6),
        ('a', '20230215', 2),
        ('a', '20230216', 1),
        ('b', '20230216', 9),
        ('b', '20230211', 8),
        ('b', '20230213', 5),
        ('b', '20230214', 1)
        t (uid, dt, score)
)
SELECT
  uid, dt, score,
  -- 只有分区无排序 默认从起点到终点
  COLLECT_SET(score) OVER (PARTITION BY uid) AS s1,
  -- 无排序默认从起点到当前行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt) AS s2,
  -- 起点到当前前1行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS s3,
  -- 起点到当前行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS s4,
  -- 起点到当前后1行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND 1 FOLLOWING) AS s5,
  -- 起点到终点，即所有行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS s6,
  -- 当前前2行到当前前1行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN 2 PRECEDING AND 1 PRECEDING) AS s7,
  -- 当前前2行到当前行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS s8,
  -- 当前前2行到当前后1行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN 2 PRECEDING AND 1 FOLLOWING) AS s9,
  -- 当前前2行到终点
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN 2 PRECEDING AND UNBOUNDED FOLLOWING) AS s10,
  -- 当前行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN CURRENT ROW AND CURRENT ROW) AS s11,
  -- 当前行到当前后一行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN CURRENT ROW AND 1 FOLLOWING) AS s12,
  -- 当前行到终点
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) AS s13,
  -- 当前后一行到当前后2行
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN 1 FOLLOWING AND 2 FOLLOWING) AS s14,
  -- 当前后一行到终点
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS s15
FROM behavior;
```

![undefined](https://intranetproxy.alipay.com/skylark/lark/0/2025/png/158678/1745466583729-52bda5ba-ae5a-4806-9e41-5fec5640164c.png)

### 5.2 RANGE

RANGE 类型 Frame 子句通过比较 ORDER BY 列值的大小关系来确定数据边界。一般在窗口定义中会指定 ORDER BY，未指定 ORDER BY 时，一个分区中的所有数据行具有相同的 ORDER BY 列值。NULL 与 NULL 被认为是相等的。

| frame_start/frame_end | 含义 | 说明 |
| -------- | -------- | -------- |
| UNBOUNDED PRECEDING | 表示分区的第一行，从1开始计数 | |
| UNBOUNDED FOLLOWING | 表示分区的最后一行 |
| CURRENT ROW | 作为 frame_start 时，指第一条与当前行具有相同 ORDER BY 列值的数据的位置;作为 frame_end 时，指最后一条与当前行具有相同 ORDER BY 列值的数据的位置 |
| UNBOUNDED FOLLOWING | 表示分区的最后一行 |

需要注意的是 ORDER BY 排序列必须是数值类型或时间类型才能支持 RANGE 窗口函数。

```sql
WITH behavior AS (
    SELECT uid, TO_DATE(dt, 'yyyymmdd') AS dt, score
    FROM VALUES
        ('a', '20230211', 9),
        ('a', '20230213', 7),
        ('a', '20230214', 14),
        ('a', '20230212', 6),
        ('a', '20230215', 2),
        ('a', '20230216', 1),
        ('b', '20230216', 9),
        ('b', '20230211', 8),
        ('b', '20230213', 5),
        ('b', '20230214', 1)
        t (uid, dt, score)
)
SELECT
  uid, dt, score,
  -- 只有分区无排序 默认为从起点日期到终点日期
  COLLECT_SET(score) OVER (PARTITION BY uid) AS s1,
  -- 无排序 默认为从起点日期到当前日期
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt) AS s2,
  -- 起点日期到当前日期前一天
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1' DAY PRECEDING) AS s3,
  -- 起点日期到当前日期
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS s4,
  -- 起点日期到当前日期后一天
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND INTERVAL '1' DAY FOLLOWING) AS s5,
  -- 起点日期到终点日期
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS s6,
  -- 当前日期前2天到当前日期前1天
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN INTERVAL '2' DAY PRECEDING AND INTERVAL '1' DAY PRECEDING) AS s7,
  -- 当前日期前2天到当前日期
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN INTERVAL '2' DAY PRECEDING AND CURRENT ROW) AS s8,
  -- 当前日期前2天到当前日期后1天
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN INTERVAL '2' DAY PRECEDING AND INTERVAL '1' DAY FOLLOWING) AS s9,
  -- 当前日期前2天到终点日期
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN INTERVAL '2' DAY PRECEDING AND UNBOUNDED FOLLOWING) AS s10,
  -- 当前日期
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN CURRENT ROW AND CURRENT ROW) AS s11,
  -- 当前日期到当前日期后1天
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN CURRENT ROW AND INTERVAL '1' DAY FOLLOWING) AS s12,
  -- 当前日期到终点日期
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) AS s13,
  -- 当前日期后前1天到当前日期后2天
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN INTERVAL '1' DAY FOLLOWING AND INTERVAL '2' DAY FOLLOWING) AS s14,
  -- 当前日期后1天到终点日期
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN INTERVAL '1' DAY FOLLOWING AND UNBOUNDED FOLLOWING) AS s15
FROM behavior;
```

![undefined](https://intranetproxy.alipay.com/skylark/lark/0/2025/png/158678/1745466708946-e222b774-8bd5-4c61-821a-3862c1d3a338.png)

### 5.3 GROUPS

GROUPS 类型 Frame 子句通过将一个分区中所有具有相同 ORDER BY 列值的数据组成一个 GROUP。未指定 ORDER BY 时，分区中的所有数据组成一个 GROUP。NULL 与 NULL 被认为是相等的。


## 6. 窗口典型模式


| 模式 | 表达式 | 适用场景 |
| -------- | -------- | -------- |
| 累计窗口 | ROWS UNBOUNDED PRECEDING | 累计求和、移动平均 |
| 滑动窗口 | ROWS 2 PRECEDING AND 1 FOLLOWING | 股票5日均线 |
| 动态窗口 | RANGE BETWEEN ... | 时间区间统计 |



## 7. 窗口典型问题

```sql
WITH behavior AS (
    SELECT uid, dt, score
    FROM VALUES
        ('a', '20230211', 9),
        ('a', '20230213', 7),
        ('a', '20230214', 14),
        ('a', '20230212', 6),
        ('a', '20230215', 2),
        ('a', '20230216', 1),
        ('b', '20230216', 9),
        ('b', '20230211', 8),
        ('b', '20230213', 5),
        ('b', '20230214', 1)
        t (uid, dt, score)
)
SELECT
  uid, dt, score,
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN 2 PRECEDING AND 1 PRECEDING) AS score_set
FROM behavior;
```
执行上述SQL时遇到如下异常：
```java
Semantic analysis exception - offset type STRING is invalid, only numeric or temporal type is allowed in RANGE windowing clause
```
该错误提示表明在 RANGE 窗口函数中使用的偏移量（offset）类型不合法，只能是数值类型或时间类型，但当前传递的是字符串类型。接下来，看一下为什么 offset 类型会变成字符串。可以看到 RANGE 窗口函数的偏移量部分定义为 `2 PRECEDING AND 1 PRECEDING`，这里的偏移量是数值类型，因此问题可能出在排序列上：
```sql
COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN 2 PRECEDING AND 1 PRECEDING)
```
`ORDER BY` 排序列用于排序和范围计算，必须是日期或时间类型才能支持 RANGE 窗口函数。而这里的排序列 dt 存储的是字符串类型而不是日期类型，导致窗口函数在处理 RANGE 时出现上述问题。

基于这个分析，解决方案是将 dt 列从字符串类型转换为日期类型，并确保 RANGE 窗口函数的偏移量类型正确：
```sql
WITH behavior AS (
    SELECT uid, TO_DATE(dt, 'yyyymmdd') AS dt, score
    FROM VALUES
        ('a', '20230211', 9),
        ('a', '20230213', 7),
        ('a', '20230214', 14),
        ('a', '20230212', 6),
        ('a', '20230215', 2),
        ('a', '20230216', 1),
        ('b', '20230216', 9),
        ('b', '20230211', 8),
        ('b', '20230213', 5),
        ('b', '20230214', 1)
        t (uid, dt, score)
)
SELECT
  uid, dt, score,
  COLLECT_SET(score) OVER (PARTITION BY uid ORDER BY dt RANGE BETWEEN 2 PRECEDING AND 1 PRECEDING) AS score_set
FROM behavior;
```
