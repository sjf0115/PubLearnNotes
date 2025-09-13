## 1. 介绍

窗口函数（Window Function）是一种特殊的分析函数，能够在特定数据窗口（行集合）上执行计算，同时保留原始数据行的完整信息。与传统GROUP BY聚合不同，窗口函数不会合并结果行，而是为每行返回独立计算结果。常用于处理时间序列数据、排名、移动平均等场景。

## 2. 窗口函数语法

窗口函数的语法声明如下:
```sql
<function_name>([distinct][<expression> [, ...]]) over (<window_definition>)
<function_name>([distinct][<expression> [, ...]]) over <window_name>
```
- function_name：内建窗口函数、聚合函数或用户自定义聚合函数UDAF。
- expression：函数格式，具体格式以实际函数语法为准。
- windowing_definition：窗口定义。
- window_name：命名窗口。可以使用 window 关键字自定义命名窗口，为 windowing_definition 定义名称。

> 窗口定义请查阅[]()


### 2.1 非命名窗口

非命名窗口语法如下所示:
```sql
<function_name>([distinct][<expression> [, ...]]) over (<window_definition>)
```

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
  MAX(score) OVER (PARTITION BY uid ORDER BY dt) AS max_score,
  MIN(score) OVER (PARTITION BY uid ORDER BY dt) AS min_score,
  SUM(score) OVER (PARTITION BY uid ORDER BY dt) AS sum_score,
  COUNT(*) OVER (PARTITION BY uid ORDER BY dt) AS count_score,
  COLLECT_LIST(score) OVER (PARTITION BY uid ORDER BY dt) AS collect_score
FROM behavior;
```

### 2.2 命名窗口

命名窗口语法如下所示:
```sql
<function_name>([distinct][<expression> [, ...]]) over <window_name>
```
使用 window 关键字自定义命名窗口，为 windowing_definition 定义名称:
```sql
window <window_name> AS (<window_definition>)
```
- window_name: 窗口命名
- window_definition: 窗口定义


自定义命名窗口语句 named_window 在 SQL 中的位置：
```sql
select ... from ... [where ...] [group by ...] [having ...] named_window [order by ...] [limit ...]
```

示例：
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
  MAX(score) OVER user_group_window AS max_score,
  MIN(score) OVER user_group_window AS min_score,
  SUM(score) OVER user_group_window AS sum_score,
  COUNT(*) OVER user_group_window AS count_score,
  COLLECT_LIST(score) OVER user_group_window AS collect_score
FROM behavior
WINDOW user_group_window AS (PARTITION BY uid ORDER BY dt);
```
在这定义了一个名为 `user_group_window` 的窗口。

| uid | dt | score | max_score | min_score | sum_score | count_score | collect_score |
| -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- |
| a | 20230211 | 9 | 9 | 9 | 9 | 1 | [9] |
| a | 20230212 | 6 | 9 | 6 | 15 | 2 | [9, 6] |
| a | 20230213 | 7 | 9 | 6 | 22 | 3 | [9, 6, 7] |
| a | 20230214 | 14 | 14 | 6 | 36 | 4 | [9, 6, 7, 14] |
| a | 20230215 | 2 | 14 | 2 | 38 | 5 | [9, 6, 7, 14, 2] |
| a | 20230216 | 1 | 14 | 1 | 39 | 6 | [9, 6, 7, 14, 2, 1] |
| b | 20230211 | 8 | 8 | 8 | 8 | 1 | [8] |
| b | 20230213 | 5 | 8 | 5 | 13 | 2 | [8, 5] |
| b | 20230214 | 1 | 8 | 1 | 14 | 3 | [8, 5, 1] |
| b | 20230216 | 9 | 9 | 1 | 23 | 4 | [8, 5, 1, 9] |

![undefined](https://intranetproxy.alipay.com/skylark/lark/0/2025/png/158678/1745464424036-f3073891-1fa3-427b-b8e6-764f9e5e3dca.png)


## 4. 常用窗口函数
### 4.1 排名函数

| 函数            | 特性                          |
|-----------------|------------------------------|
| ROW_NUMBER()    | 连续唯一序号（1,2,3,...）     |
| RANK()          | 并列跳号（1,2,2,4,...）       |
| DENSE_RANK()    | 并列不跳号（1,2,2,3,...）     |


**示例**：部门薪资排名
```sql
SELECT
    emp_name,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;
```

### 4.2 聚合函数

支持所有标准聚合函数（SUM/AVG/COUNT/MAX/MIN等）

**示例**：计算累计占比
```sql
SELECT
    product,
    revenue,
    revenue/SUM(revenue) OVER () AS total_ratio,
    SUM(revenue) OVER (ORDER BY sale_date) AS cumulative_rev
FROM sales;
```

### 4.3 分布函数

- `CUME_DIST()`：累积分布值
- `PERCENT_RANK()`：百分比排名
- `NTILE(n)`：数据分桶

---

## 5. 典型应用场景

### 5.1 移动平均计算
```sql
SELECT
    stock_date,
    closing_price,
    AVG(closing_price) OVER (
        ORDER BY stock_date
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS 5_day_ma
FROM stock_prices;
```

### 5.2 异常值检测
```sql
SELECT
    sensor_id,
    read_time,
    temperature,
    AVG(temperature) OVER (
        PARTITION BY sensor_id
        ORDER BY read_time
        RANGE BETWEEN INTERVAL '1' HOUR PRECEDING AND CURRENT ROW
    ) AS hourly_avg,
    temperature - AVG(temperature) OVER (...) AS deviation
FROM sensor_readings;
```

### 5.3 会话划分
```sql
SELECT
    user_id,
    event_time,
    event_type,
    SUM(session_flag) OVER (PARTITION BY user_id ORDER BY event_time) AS session_id
FROM (
    SELECT *,
        CASE WHEN event_time - LAG(event_time) OVER (...) > INTERVAL '30' MINUTE
             THEN 1 ELSE 0 END AS session_flag
    FROM user_events
) tmp;
```

---
