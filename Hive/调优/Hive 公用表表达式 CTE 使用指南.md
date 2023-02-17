
## 1. 概述

Common Table Expression（公用表表达式），简称 CTE，由 WITH 子句中指定的简单查询派生的临时结果集，用于简化 SQL。CTE 默认是不对数据进行物化，即相当于视图，只是为一个 SQL 语句定义了一个变量，每次使用这个 SQL 语句时只需要这个 SQL 变量即可。开发过程中结合 CTE，可以提高 SQL 语句可读性，便于轻松维护复杂查询。

CTE 仅在单个语句的执行范围内定义。CTE 子句紧跟在 SELECT 或者 INSERT 关键字之前，可以在 SELECT、INSERT、CREATE TABLE AS SELECT 或者 CREATE VIEW AS SELECT 语句中使用一个或多个 CTE。

Hive 从 0.13.0 版本开始支持标准 SQL 的 CTE，具体细看使[HIVE-1180](https://issues.apache.org/jira/browse/HIVE-1180)。CTE 的出现可以更好地提高 SQL 语句的可读性与执行效率。

## 2. 语法

CTE 由表示 CTE 的表达式名称，AS 关键字以及 SELECT 语句组成。CTE 的基本语法结构如下所示：
```sql
WITH
  cte_name AS (cte_query)
  [,cte_name2 AS (cte_query2),……]
```
说明:
- cte_name：CTE 的名称，不能与当前 WITH 子句中的其他 CTE 的名称相同。查询中任何使用到 cte_name 标识符的地方，均指 CTE。
- cte_query：一个 SELECT 语句。它产生的结果集用于填充 CTE。

> 在视图、CTAS 以及 INSERT 语句中支持 CTE。但是需要注意的是在子查询块中不支持 WITH 子句，此外也不支持递归查询。

## 3. Example

```sql
-- App用户学习总时长
SELECT
    SUM(duration) AS duration
FROM (
    SELECT user_id, duration
    FROM dws_app_study_user_td
    WHERE dt = '${date}'
) AS study
LEFT SEMI JOIN (
    SELECT user_id
    FROM dim_app_user_df
    WHERE dt = '${date}'
) AS user
ON study.user_id = user.user_id
UNION ALL
-- App用户学习总积分
SELECT
    SUM(score) AS score
FROM (
    SELECT user_id, score
    FROM dws_app_score_user_td
    WHERE dt = '${date}'
) AS study
LEFT SEMI JOIN (
    SELECT user_id
    FROM dim_app_user_df
    WHERE dt = '${date}'
) AS user
ON study.user_id = user.user_id;
```
顶层的 UNION 两侧各为一个 JOIN，JOIN 的右表是相同的查询。通过写子查询的方式，只能重复这段代码。可以使用 CTE 的方式重写以上语句：
```sql
WITH
user AS (
    SELECT user_id
    FROM dim_app_user_td
    WHERE dt = '${date}'
),
study_duration AS (
    SELECT user_id, duration
    FROM dws_app_study_user_td
    WHERE dt = '${date}'
),
study_score AS (
    SELECT user_id, score
    FROM dws_app_score_user_td
    WHERE dt = '${date}'
),
user_study_duration AS (
    SELECT SUM(a.duration) AS duration
    FROM study_duration AS a
    LEFT SEMI JOIN user AS b
    ON a.user_id = b.user_id
),
user_study_score AS (
    SELECT SUM(a.score) AS score
    FROM study_score AS a
    LEFT SEMI JOIN user AS b
    ON a.user_id = b.user_id
)
SELECT * FROM user_study_duration
UNION ALL
SELECT * FROM user_study_score;
```
重写后，user 对应的子查询只需写一次，便可在后面进行重用。你可以在 CTE 的 WITH 子句中指定多个子查询，像使用变量一样在整个语句中反复重用。除重用外，不必反复嵌套。

## 4. 使用场景

### 4.1 在 SELECT 语句中使用

在 SELECT 语句中使用 CTE：
```sql
WITH user AS (
  SELECT uid, COUNT(*) AS num
  FROM behavior
  WHERE uid LIKE 'a%'
  GROUP BY uid
)
SELECT uid, num
FROM user;
```
在 SELECT 语句中使用多个 CTE：
```sql
WITH user AS (
  SELECT uid, COUNT(*) AS num
  FROM behavior
  WHERE uid LIKE 'a%'
  GROUP BY uid
),
user_num AS (
  SELECT SUM(num) AS num
  FROM user
)
SELECT num
FROM user_num;
```
在 SELECT 语句中可以支持对两个 CTE 进行 UNION：
```sql
WITH user_a AS (
  SELECT uid, COUNT(*) AS num
  FROM behavior
  WHERE uid LIKE 'a%'
  GROUP BY uid
),
user_b AS (
  SELECT uid, COUNT(*) AS num
  FROM behavior
  WHERE uid LIKE 'b%'
  GROUP BY uid
),
SELECT uid, num
FROM user_a
UNION ALL
SELECT uid, num
FROM user_b;
```

### 4.2 在 INSERT 语句中使用

```sql
WITH user AS (
  SELECT uid, COUNT(*) AS num
  FROM behavior
  WHERE uid LIKE 'a%'
  GROUP BY uid
)
FROM user
INSERT OVERWRITE TABLE user_num
SELECT uid, num;
```

### 4.3 在 CTAS 语句中使用

```sql
CREATE TABLE user_num AS
WITH user AS (
  SELECT uid, COUNT(*) AS num
  FROM behavior
  WHERE uid LIKE 'a%'
  GROUP BY uid
)
SELECT uid, num FROM user;
```

### 4.4 在视图中使用

在创建视图中使用 CTE:
```sql
CREATE VIEW user_num_view AS
WITH user AS (
  SELECT uid, COUNT(*) AS num
  FROM behavior
  WHERE uid LIKE 'a%'
  GROUP BY uid
)
SELECT uid, num FROM user;
```

## 5. 使用CTE的好处

- 提高可读性：使用 CTE 可以提高可读性并简化复杂查询的维护。不是将所有查询逻辑都集中到一个大型查询中，而是创建几个简单逻辑构建块的 CTE，然后可以使用它们构建更复杂的 CTE，直到生成最终结果集。
- 替代视图或表：定义CTE后，可以用作表或视图，并可以 SELECT，INSERT，UPDATE 或 DELETE 数据。如果你没有创建视图或表的权限，或者你根本不想创建一个视图或表，因为它仅在这一个查询中使用，这种情形使用 CTE 很方便。
- 排名：每当你想使用排名函数，如ROW_NUMBER()，RANK()，NTILE()等。
