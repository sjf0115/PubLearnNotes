Apache Flink 作为流处理领域的领军者，其 SQL API 让用户能够以声明式的方式处理数据流。理解 Flink SQL 的执行计划对于优化查询性能、调试复杂任务至关重要。本文将深入探讨如何使用 EXPLAIN 语句分析 Flink SQL 的执行计划。

## 1. 什么是 Flink SQL 执行计划？

执行计划是 Flink 优化器将 SQL 语句转换为实际执行任务的蓝图。它展示了查询的逻辑和物理执行结构，包括算子的排列顺序、数据流转换方式以及资源分配策略。而 EXPLAIN 语句就是 Flink 为我们提供的用于解释 Query 或 INSERT 语句逻辑和优化查询计划的工具。


## 2. EXPLAIN 语法

Flink SQL 的 EXPLAIN 语句在 Flink 1.13 版本只支持如下语法：
```sql
EXPLAIN PLAN FOR <query_statement_or_insert_statement>
```
Flink 1.20 已经发展到支持多种参数，用于生成不同类型的执行计划信息。根据源码定义，其基本语法如下：
```sql
EXPLAIN [PLAN FOR | (ESTIMATED_COST | CHANGELOG_MODE | JSON_EXECUTION_PLAN) (,(ESTIMATED_COST | CHANGELOG_MODE | JSON_EXECUTION_PLAN | PLAN_ADVICE))*] STATEMENT
```

主要参数说明:

| 参数 | 说明 |
| :------------- | :------------- |
| ESTIMATED_COST | 显示估算的执行成本 |
| CHANGELOG_MODE | 显示变更日志模式 |
| JSON_EXECUTION_PLAN | 以JSON格式显示执行计划 |
| PLAN_ADVICE | 显示执行计划建议 |



## 2. 如何使用 EXPLAIN

### 2.1 SQL Cli

```sql
CREATE TABLE datagen_table (
    word STRING,
    frequency int
) WITH (
  'connector' = 'datagen',
  'rows-per-second' = '1',
  'fields.word.kind' = 'random',
  'fields.word.length' = '1',
  'fields.frequency.min' = '1',
  'fields.frequency.max' = '9'
);
```

```sql
EXPLAIN PLAN FOR
SELECT frequency, COUNT(*) AS num
FROM (
  SELECT word, SUM(frequency) AS frequency
  FROM datagen_table
  GROUP BY word
)
GROUP BY frequency;
```
输出结果：
```
== Abstract Syntax Tree ==
LogicalAggregate(group=[{0}], num=[COUNT()])
+- LogicalProject(frequency=[$1])
   +- LogicalAggregate(group=[{0}], frequency=[SUM($1)])
      +- LogicalTableScan(table=[[default_catalog, default_database, datagen_table]])

== Optimized Physical Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])

== Optimized Execution Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])
```


```sql
EXPLAIN JSON_EXECUTION_PLAN
SELECT frequency, COUNT(*) AS num
FROM (
  SELECT word, SUM(frequency) AS frequency
  FROM datagen_table
  GROUP BY word
)
GROUP BY frequency;
```
输出结果：
```
== Abstract Syntax Tree ==
LogicalAggregate(group=[{0}], num=[COUNT()])
+- LogicalProject(frequency=[$1])
   +- LogicalAggregate(group=[{0}], frequency=[SUM($1)])
      +- LogicalTableScan(table=[[default_catalog, default_database, datagen_table]])

== Optimized Physical Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])

== Optimized Execution Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])

== Physical Execution Plan ==
{
  "nodes" : [ {
    "id" : 33,
    "type" : "Source: datagen_table[25]",
    "pact" : "Data Source",
    "contents" : "[25]:TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])",
    "parallelism" : 1
  }, {
    "id" : 35,
    "type" : "GroupAggregate[27]",
    "pact" : "Operator",
    "contents" : "[27]:GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])",
    "parallelism" : 1,
    "predecessors" : [ {
      "id" : 33,
      "ship_strategy" : "HASH",
      "side" : "second"
    } ]
  }, {
    "id" : 36,
    "type" : "Calc[28]",
    "pact" : "Operator",
    "contents" : "[28]:Calc(select=[frequency])",
    "parallelism" : 1,
    "predecessors" : [ {
      "id" : 35,
      "ship_strategy" : "FORWARD",
      "side" : "second"
    } ]
  }, {
    "id" : 38,
    "type" : "GroupAggregate[30]",
    "pact" : "Operator",
    "contents" : "[30]:GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])",
    "parallelism" : 1,
    "predecessors" : [ {
      "id" : 36,
      "ship_strategy" : "HASH",
      "side" : "second"
    } ]
  } ]
}
```

```sql
EXPLAIN CHANGELOG_MODE
SELECT frequency, COUNT(*) AS num
FROM (
  SELECT word, SUM(frequency) AS frequency
  FROM datagen_table
  GROUP BY word
)
GROUP BY frequency;
```

```
== Abstract Syntax Tree ==
LogicalAggregate(group=[{0}], num=[COUNT()])
+- LogicalProject(frequency=[$1])
   +- LogicalAggregate(group=[{0}], frequency=[SUM($1)])
      +- LogicalTableScan(table=[[default_catalog, default_database, datagen_table]])

== Optimized Physical Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num], changelogMode=[I,UA,D])
+- Exchange(distribution=[hash[frequency]], changelogMode=[I,UB,UA])
   +- Calc(select=[frequency], changelogMode=[I,UB,UA])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency], changelogMode=[I,UB,UA])
         +- Exchange(distribution=[hash[word]], changelogMode=[I])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency], changelogMode=[I])

== Optimized Execution Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])
```



```sql
EXPLAIN ESTIMATED_COST
SELECT frequency, COUNT(*) AS num
FROM (
  SELECT word, SUM(frequency) AS frequency
  FROM datagen_table
  GROUP BY word
)
GROUP BY frequency;
```

```
== Abstract Syntax Tree ==
LogicalAggregate(group=[{0}], num=[COUNT()])
+- LogicalProject(frequency=[$1])
   +- LogicalAggregate(group=[{0}], frequency=[SUM($1)])
      +- LogicalTableScan(table=[[default_catalog, default_database, datagen_table]])

== Optimized Physical Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num]): rowcount = 1.0E8, cumulative cost = {6.0E8 rows, 3.39E10 cpu, 1.6E9 io, 2.0E9 network, 0.0 memory}
+- Exchange(distribution=[hash[frequency]]): rowcount = 1.0E8, cumulative cost = {5.0E8 rows, 3.38E10 cpu, 1.6E9 io, 2.0E9 network, 0.0 memory}
   +- Calc(select=[frequency]): rowcount = 1.0E8, cumulative cost = {4.0E8 rows, 1.7E10 cpu, 1.6E9 io, 1.6E9 network, 0.0 memory}
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency]): rowcount = 1.0E8, cumulative cost = {3.0E8 rows, 1.7E10 cpu, 1.6E9 io, 1.6E9 network, 0.0 memory}
         +- Exchange(distribution=[hash[word]]): rowcount = 1.0E8, cumulative cost = {2.0E8 rows, 1.69E10 cpu, 1.6E9 io, 1.6E9 network, 0.0 memory}
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency]): rowcount = 1.0E8, cumulative cost = {1.0E8 rows, 1.0E8 cpu, 1.6E9 io, 0.0 network, 0.0 memory}

== Optimized Execution Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])
```

```sql
EXPLAIN PLAN_ADVICE
SELECT frequency, COUNT(*) AS num
FROM (
  SELECT word, SUM(frequency) AS frequency
  FROM datagen_table
  GROUP BY word
)
GROUP BY frequency;
```

```
== Abstract Syntax Tree ==
LogicalAggregate(group=[{0}], num=[COUNT()])
+- LogicalProject(frequency=[$1])
   +- LogicalAggregate(group=[{0}], frequency=[SUM($1)])
      +- LogicalTableScan(table=[[default_catalog, default_database, datagen_table]])

== Optimized Physical Plan With Advice ==
GroupAggregate(advice=[1], groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(advice=[1], groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])

advice[1]: [ADVICE] You might want to enable local-global two-phase optimization by configuring ('table.exec.mini-batch.enabled' to 'true', 'table.exec.mini-batch.allow-latency' to a positive long value, 'table.exec.mini-batch.size' to a positive long value).

== Optimized Execution Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])
```


```sql
EXPLAIN ESTIMATED_COST, CHANGELOG_MODE, PLAN_ADVICE, JSON_EXECUTION_PLAN
SELECT frequency, COUNT(*) AS num
FROM (
  SELECT word, SUM(frequency) AS frequency
  FROM datagen_table
  GROUP BY word
)
GROUP BY frequency;
```

```
== Abstract Syntax Tree ==
LogicalAggregate(group=[{0}], num=[COUNT()])
+- LogicalProject(frequency=[$1])
   +- LogicalAggregate(group=[{0}], frequency=[SUM($1)])
      +- LogicalTableScan(table=[[default_catalog, default_database, datagen_table]])

== Optimized Physical Plan With Advice ==
GroupAggregate(advice=[1], groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num], changelogMode=[I,UA,D]): rowcount = 1.0E8, cumulative cost = {6.0E8 rows, 3.39E10 cpu, 1.6E9 io, 2.0E9 network, 0.0 memory}
+- Exchange(distribution=[hash[frequency]], changelogMode=[I,UB,UA]): rowcount = 1.0E8, cumulative cost = {5.0E8 rows, 3.38E10 cpu, 1.6E9 io, 2.0E9 network, 0.0 memory}
   +- Calc(select=[frequency], changelogMode=[I,UB,UA]): rowcount = 1.0E8, cumulative cost = {4.0E8 rows, 1.7E10 cpu, 1.6E9 io, 1.6E9 network, 0.0 memory}
      +- GroupAggregate(advice=[1], groupBy=[word], select=[word, SUM(frequency) AS frequency], changelogMode=[I,UB,UA]): rowcount = 1.0E8, cumulative cost = {3.0E8 rows, 1.7E10 cpu, 1.6E9 io, 1.6E9 network, 0.0 memory}
         +- Exchange(distribution=[hash[word]], changelogMode=[I]): rowcount = 1.0E8, cumulative cost = {2.0E8 rows, 1.69E10 cpu, 1.6E9 io, 1.6E9 network, 0.0 memory}
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency], changelogMode=[I]): rowcount = 1.0E8, cumulative cost = {1.0E8 rows, 1.0E8 cpu, 1.6E9 io, 0.0 network, 0.0 memory}

advice[1]: [ADVICE] You might want to enable local-global two-phase optimization by configuring ('table.exec.mini-batch.enabled' to 'true', 'table.exec.mini-batch.allow-latency' to a positive long value, 'table.exec.mini-batch.size' to a positive long value).

== Optimized Execution Plan ==
GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])
+- Exchange(distribution=[hash[frequency]])
   +- Calc(select=[frequency])
      +- GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
         +- Exchange(distribution=[hash[word]])
            +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])

== Physical Execution Plan ==
{
  "nodes" : [ {
    "id" : 57,
    "type" : "Source: datagen_table[43]",
    "pact" : "Data Source",
    "contents" : "[43]:TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])",
    "parallelism" : 1
  }, {
    "id" : 59,
    "type" : "GroupAggregate[45]",
    "pact" : "Operator",
    "contents" : "[45]:GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])",
    "parallelism" : 1,
    "predecessors" : [ {
      "id" : 57,
      "ship_strategy" : "HASH",
      "side" : "second"
    } ]
  }, {
    "id" : 60,
    "type" : "Calc[46]",
    "pact" : "Operator",
    "contents" : "[46]:Calc(select=[frequency])",
    "parallelism" : 1,
    "predecessors" : [ {
      "id" : 59,
      "ship_strategy" : "FORWARD",
      "side" : "second"
    } ]
  }, {
    "id" : 62,
    "type" : "GroupAggregate[48]",
    "pact" : "Operator",
    "contents" : "[48]:GroupAggregate(groupBy=[frequency], select=[frequency, COUNT_RETRACT(*) AS num])",
    "parallelism" : 1,
    "predecessors" : [ {
      "id" : 60,
      "ship_strategy" : "HASH",
      "side" : "second"
    } ]
  } ]
}
```

### 2.2 Java 环境

EXPLAIN 语句可以通过 TableEnvironment 的 `executeSql()` 方法执行。对于一个执行成功的 EXPLAIN 操作，`executeSql()` 方法会返回一个解释结果，否则会抛出一个异常。下面的例子展示了如何在 TableEnvironment 中使用 `executeSql()` 运行 EXPLAIN 语句:
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);

// 创建表
String sourceSql = "CREATE TABLE datagen_table (\n" +
        "    word STRING,\n" +
        "    frequency int\n" +
        ") WITH (\n" +
        "  'connector' = 'datagen',\n" +
        "  'rows-per-second' = '1',\n" +
        "  'fields.word.kind' = 'random',\n" +
        "  'fields.word.length' = '1',\n" +
        "  'fields.frequency.min' = '1',\n" +
        "  'fields.frequency.max' = '9'\n" +
        ")";
tableEnv.executeSql(sourceSql);

// Query 语句
String sql = "SELECT word, SUM(frequency) AS frequency\n" +
        "FROM datagen_table\n" +
        "GROUP BY word";

// 使用 executeSql 查看执行计划方式
TableResult plainExplain = tableEnv.executeSql("EXPLAIN PLAN FOR " + sql);
plainExplain.print();
```
执行计划如下所示：
```
== Abstract Syntax Tree ==
LogicalAggregate(group=[{0}], frequency=[SUM($1)])
+- LogicalTableScan(table=[[default_catalog, default_database, datagen_table]])

== Optimized Physical Plan ==
GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
+- Exchange(distribution=[hash[word]])
   +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])

== Optimized Execution Plan ==
GroupAggregate(groupBy=[word], select=[word, SUM(frequency) AS frequency])
+- Exchange(distribution=[hash[word]])
   +- TableSourceScan(table=[[default_catalog, default_database, datagen_table]], fields=[word, frequency])
```
如果只是通过 `EXPLAIN PLAN FOR` 命令查看执行计划，也可以使用如下方式替代方式：
```java
// 使用 explainSql 查看执行计划方式
String explainResult = tableEnv.explainSql(sql);
System.out.println(explainResult);
```
