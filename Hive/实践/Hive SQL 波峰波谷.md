
## 1. 需求

波峰：当天的股票价格大于前一天和后一天
波谷：当天的股票价格小于前一天和后一天

## 2. 数据准备

stock 表有3个字段： id（股票id）、price（股票价格）、dt（日期）。

| id | price | dt |
| :------------- | :------------- | :------------- |
| 1	| 20	| 2023-01-01 |
| 1	| 21	| 2023-01-02 |
| 1	| 19	| 2023-01-03 |
| 1	| 20	| 2023-01-04 |
| 1	| 18	| 2023-01-05 |
| 2	| 98	| 2023-01-01 |

## 3. 分析

```sql
WITH stock AS (
  SELECT 1 AS id, 20 AS price, '2023-01-01' AS dt
  UNION ALL
  SELECT 1 AS id, 21 AS price, '2023-01-02' AS dt
  UNION ALL
  SELECT 1 AS id, 19 AS price, '2023-01-03' AS dt
  UNION ALL
  SELECT 1 AS id, 20 AS price, '2023-01-04' AS dt
  UNION ALL
  SELECT 1 AS id, 18 AS price, '2023-01-05' AS dt
  UNION ALL
  SELECT 2 AS id, 98 AS price, '2023-01-01' AS dt
)
SELECT
  id, price, dt, before_price, after_price,
  CASE
    WHEN price > before_price AND price > after_price THEN '波峰'
	  WHEN price < before_price AND price < after_price THEN '波谷'
	  ELSE '其他'
  END AS type
FROM (
  SELECT
    id, price, dt,
    LAG(price, 1, price) OVER(PARTITION BY id ORDER BY dt) AS before_price,
    LEAD(price, 1, price) OVER(PARTITION BY id ORDER BY dt) AS after_price
  FROM stock
) AS a;
```
输出结果如下所示：
```
+-----+--------+-------------+---------------+--------------+-------+
| id  | price  |     dt      | before_price  | after_price  | type  |
+-----+--------+-------------+---------------+--------------+-------+
| 1   | 20     | 2023-01-01  | 20            | 21           | 其他    |
| 1   | 21     | 2023-01-02  | 20            | 19           | 波峰    |
| 1   | 19     | 2023-01-03  | 21            | 20           | 波谷    |
| 1   | 20     | 2023-01-04  | 19            | 18           | 波峰    |
| 1   | 18     | 2023-01-05  | 20            | 18           | 其他    |
| 2   | 98     | 2023-01-01  | 98            | 98           | 其他    |
+-----+--------+-------------+---------------+--------------+-------+
```
