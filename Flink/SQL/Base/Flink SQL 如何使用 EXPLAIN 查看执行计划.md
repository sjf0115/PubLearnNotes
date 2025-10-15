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
EXPLAIN [PLAN FOR | (ESTIMATED_COST | CHANGELOG_MODE | JSON_EXECUTION_PLAN | ANALYZED_PHYSICAL_PLAN) (,(ESTIMATED_COST | CHANGELOG_MODE | JSON_EXECUTION_PLAN | PLAN_ADVICE))*] STATEMENT
```

主要参数说明:

| 参数 | 说明 |
| :------------- | :------------- |
| ESTIMATED_COST | 显示估算的执行成本 |
| CHANGELOG_MODE | 显示变更日志模式 |
| JSON_EXECUTION_PLAN | 以JSON格式显示执行计划 |
| ANALYZED_PHYSICAL_PLAN | 显示分析后的物理计划 |
| PLAN_ADVICE | 显示执行计划建议 |



## 2. 如何使用 EXPLAIN

### 2.1 SQL Cli

### 2.1 Java 环境

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
