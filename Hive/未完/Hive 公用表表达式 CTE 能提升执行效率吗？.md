
## 1. 开启

```sql
hive.optimize.cte.materialize.threshold
```
这个参数在默认情况下是-1（关闭的）；当开启（大于0），比如设置为2，则如果with..as语句被引用2次及以上时，会把with..as语句生成的table物化，从而做到with..as语句只执行一次，来提高效率。

测试：
```sql
EXPLAIN
WITH user AS (
  SELECT uid
  FROM behavior
)
SELECT 'A' AS type, COUNT(*) AS uv
FROM user WHERE uid LIKE 'a%'
UNION ALL
SELECT 'B' AS type, COUNT(*) AS uv
FROM user WHERE uid LIKE 'b%';

SELECT COUNT(*)
FROM
(
  SELECT uid
  FROM behavior
) as
where uid like 'a%';
```
