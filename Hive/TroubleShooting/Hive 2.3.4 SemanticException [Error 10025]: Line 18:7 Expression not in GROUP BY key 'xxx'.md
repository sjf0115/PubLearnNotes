
> Hive 版本：2.3.4

## 1. 问题

假设我们有包含如下数据的 user_score 表：

```
+-----------------+-------------------+
| user_score.uid  | user_score.score  |
+-----------------+-------------------+
| a               | 10                |
| a               | 22                |
| a               | 31                |
| b               | 4                 |
| b               | 15                |
| b               | 26                |
+-----------------+-------------------+
```

通过如下 SQL 计算出每个用户的平均积分，并且保留三位有效小数（四舍五入）：
```sql
SELECT
  uid, ROUND(AVG(score), 3) AS avg_score
FROM user_score
GROUP BY uid;
```

但是运行上述 SQL 抛出如下异常：
```java
Caused by: org.apache.hadoop.hive.ql.parse.SemanticException: Line 18:7 Expression not in GROUP BY key '20'
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genAllExprNodeDesc(SemanticAnalyzer.java:11620) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genExprNodeDesc(SemanticAnalyzer.java:11568) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genExprNodeDesc(SemanticAnalyzer.java:11536) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genFilterPlan(SemanticAnalyzer.java:3303) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genFilterPlan(SemanticAnalyzer.java:3283) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genHavingPlan(SemanticAnalyzer.java:3066) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genPostGroupByBodyPlan(SemanticAnalyzer.java:9681) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genBodyPlan(SemanticAnalyzer.java:9644) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genPlan(SemanticAnalyzer.java:10549) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genPlan(SemanticAnalyzer.java:10427) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.genOPTree(SemanticAnalyzer.java:11125) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.CalcitePlanner.genOPTree(CalcitePlanner.java:481) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.SemanticAnalyzer.analyzeInternal(SemanticAnalyzer.java:11138) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.CalcitePlanner.analyzeInternal(CalcitePlanner.java:286) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.parse.BaseSemanticAnalyzer.analyze(BaseSemanticAnalyzer.java:258) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.Driver.compile(Driver.java:512) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.Driver.compileInternal(Driver.java:1317) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hadoop.hive.ql.Driver.compileAndRespond(Driver.java:1295) ~[hive-exec-2.3.4.jar:2.3.4]
	at org.apache.hive.service.cli.operation.SQLOperation.prepare(SQLOperation.java:204) ~[hive-service-2.3.4.jar:2.3.4]
	... 28 more
Error: Error while compiling statement: FAILED: SemanticException [Error 10025]: Line 18:7 Expression not in GROUP BY key '20' (state=42000,code=10025)
```

## 2. 解决方案

GROUP BY 语句通常会和聚合函数一起使用，按照一个或者多个列对结果进行分组，然后对每个组执行聚合操作。在 SELECT 子句中出现的字段，如果不是在聚合函数（比如 SUM、COUNT、AVG等）中，那就必须要放到 GROUP BY 子句中，相反没有出现在 GROUP BY 子句中的字段，只能出现在聚合函数中。在上面语句中 Hive 不认为 ROUND 是一个聚合函数，ROUND 中使用的字段必须添加到 GROUP BY 中，否则就会抛出上面的异常信息。但是 GROUP BY 语句中是不能使用 AVG 聚合函数，所以使用嵌套子查询的方式实现：
```sql
SELECT uid, ROUND(avg_score, 3) AS avg_score
FROM (
  SELECT
    uid, AVG(score) AS avg_score
  FROM user_score
  GROUP BY uid
) AS a;
```

同理，也不能直接使用 CAST 将聚合函数的结果进行类型转换：
```sql
SELECT
  uid, CAST(AVG(score) AS STRING) AS avg_score
FROM user_score
GROUP BY uid;
```

## 3. 扩展

其他场景下也会出现类似上面的异常信息。比如如下查询语句：
```sql
SELECT
  uid, dt, COUNT(1) AS num
FROM user_score
GROUP BY uid;
```
上述语句会抛出 `SemanticException [Error 10025]: Line 2:5 Expression not in GROUP BY key 'dt' (state=42000,code=10025)` 异常，从异常信息中也可以明确知道因为 dt 字段不在 Group Key 中才抛出的异常。

解决方案有两种，第一种是将 dt 添加到 GROUP BY 子句中，作为分组的其中一个维度：
```sql
SELECT
  uid, dt, COUNT(1) AS num
FROM user_score
GROUP BY uid, dt;
```
第二种方案是将 dt 放在聚合函数中，一般常用 `COLLECT_SET` 函数：
```sql
SELECT
  uid, COLLECT_SET(dt) AS days, COUNT(1) AS num
FROM user_score
GROUP BY uid;
```
