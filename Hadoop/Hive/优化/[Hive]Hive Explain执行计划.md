---
layout: post
author: sjf0115
title: Hive 执行计划
date: 2018-07-21 17:16:01
tags:
  - Hive
  - Hive 优化

categories: Hive
permalink: hive-optimization-how-to-use-explain
---

Hive 提供了一个 EXPLAIN 语句，不运行查询就可以返回查询的执行计划。如果我们担心查询的性能，我们可以使用它来分析查询。EXPLAIN 语句可帮助我们查看实现相同任务的不同查询语句的差异。 EXPLAIN 语法如下：
```
EXPLAIN [EXTENDED|CBO|AST|DEPENDENCY|AUTHORIZATION|LOCKS|VECTORIZATION|ANALYZE] query
```
从上面可以知道 Hive 提供的执行计划可以查看的信息有如下几种：
- 查看执行计划的基本信息，使用 EXPLAIN 命令；
- 查看执行计划的扩展信息，使用 EXPLAIN EXTENDED 命令；
- 查看 Calcite 优化器生成的查询计划信息，使用 EXPLAIN CBO 命令；
- 使用 EXPLAIN AST 命令。
- 查看 SQL 数据输入依赖的信息，使用 EXPLAIN DEPENDENCY 命令。
- 查看 SQL 操作相关权限的信息，使用 EXPLAIN AUTHORIZATION 命令。
- 使用 EXPLAIN LOCKS 命令。
- 查看 SQL 的向量化描述信息，使用 EXPLAIN VECTORIZATION 命令。

### 1. EXPLAIN

在查询语句的 SQL 前面加上关键字 EXPLAIN 可以查看执行计划的基本方法。例如，有如下 EXPLAIN 查询：
```sql
EXPLAIN
INSERT OVERWRITE TABLE dws_app_pub_user_overview_1d
SELECT uid, COUNT(wid) AS num
FROM dws_app_user_behavior_1d
GROUP BY uid;
```
用 EXPLAIN 打开的执行计划包含以下两部分：
- 作业的依赖关系图，即 STAGE DEPENDENCIES
- 每个作业的详细信息，即 STAGE PLANS
```
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1
  Stage-2 depends on stages: Stage-0

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: dws_app_user_behavior_1d
            Statistics: Num rows: 224481 Data size: 44896344 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              expressions: uid (type: string), wid (type: string)
              outputColumnNames: uid, wid
              Statistics: Num rows: 224481 Data size: 44896344 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count(wid)
                keys: uid (type: string)
                mode: hash
                outputColumnNames: _col0, _col1
                Statistics: Num rows: 224481 Data size: 44896344 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  key expressions: _col0 (type: string)
                  sort order: +
                  Map-reduce partition columns: _col0 (type: string)
                  Statistics: Num rows: 224481 Data size: 44896344 Basic stats: COMPLETE Column stats: NONE
                  value expressions: _col1 (type: bigint)
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0)
          keys: KEY._col0 (type: string)
          mode: mergepartial
          outputColumnNames: _col0, _col1
          Statistics: Num rows: 112240 Data size: 22448071 Basic stats: COMPLETE Column stats: NONE
          Select Operator
            expressions: _col0 (type: string), UDFToInteger(_col1) (type: int)
            outputColumnNames: _col0, _col1
            Statistics: Num rows: 112240 Data size: 22448071 Basic stats: COMPLETE Column stats: NONE
            File Output Operator
              compressed: false
              Statistics: Num rows: 112240 Data size: 22448071 Basic stats: COMPLETE Column stats: NONE
              table:
                  input format: org.apache.hadoop.mapred.TextInputFormat
                  output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
                  serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
                  name: default.dws_app_pub_user_overview_1d

  Stage: Stage-0
    Move Operator
      tables:
          replace: true
          table:
              input format: org.apache.hadoop.mapred.TextInputFormat
              output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
              serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
              name: default.dws_app_pub_user_overview_1d

  Stage: Stage-2
    Stats-Aggr Operator
```




### 2. EXPLAIN EXTENDED

### 3. EXPLAIN CBO

在 EXPLAIN 语句中使用 CBO 可以查看 Calcite 优化器生成的查询计划信息。可以选择包含有关使用 Calcite 默认成本模型和用于连接重新排序的成本模型的查询计划成本的信息。 从 Hive 4.0.0 版本开始提供支持，具体查阅 [HIVE-17503](https://issues.apache.org/jira/browse/HIVE-17503) 和 [HIVE-21184](https://issues.apache.org/jira/browse/HIVE-21184)。

### 4. EXPLAIN AST

在 EXPLAIN 语句中使用 AST 可以

AST 在 Hive 2.1.0 版本中从 EXPLAIN EXTENDED 中删除，主要是因为对于非常大的查询，转储 AST 会导致 OOM 错误，具体查阅[HIVE-13533](https://issues.apache.org/jira/browse/HIVE-13533)。在 HIVE 0.14.0 版本开始提供 AST 的单独命令，对于 Hive 开发人员和高级用户来说，查看 AST 来诊断问题会很有用，具体查阅 [HIVE-15932](https://issues.apache.org/jira/browse/HIVE-15932)。

### 5. EXPLAIN DEPENDENCY

在 EXPLAIN 语句中使用 DEPENDENCY 可以查看执行计划的扩展信息。显示了输入的各种属性，例如，对于像这样的查询：

### 6. EXPLAIN AUTHORIZATION

在 EXPLAIN 语句中使用 AUTHORIZATION 可以查看 SQL 操作相关权限的信息。AUTHORIZATION 从 HIVE 0.14.0 版本开始提供支持，具体查阅[HIVE-5961](https://issues.apache.org/jira/browse/HIVE-5961)。

### 7. EXPLAIN LOCKS

LOCKS 从 Hive 3.2.0 版本开始提供支持，具体查阅 [HIVE-17683](HIVE-17683)。

### 8. EXPLAIN VECTORIZATION

VECTORIZATION 从 Hive 2.3.0 版本开始提供支持，具体查阅[HIVE-11394](https://issues.apache.org/jira/browse/HIVE-11394)。

### 9. EXPLAIN ANALYZE









我们通过下面的案例6.1，来看下基本执行计划包含的内容。


Explain 功能可以帮助我们学习 Hive 是如何转换成 MapReduce 任务的。

一个MR的执行计划分为两个部分：
- Map Operator Tree：MAP端的执行计划
- Reduce Operator Tree：Reduce端的执行计划

### 1. Operator

Operator|描述
---|---
TableScanOperator| 从表中读取数据
ReduceOutputOperator| Map阶段结束，将结果数据输出到Reducer
JoinOperator| Join操作
SelectOperator| Reduce阶段输出select中的列
FileSinkOperator| 将结果数据输出到输出文件
FilterOperator| 过滤输入数据
GroupByOperator|*
MapJoinOperator|*
LimitOperator|*
UnionOperator|*

### 2. 执行流程

![]()

- 语法分析阶段，Hive利用Antlr将用户提交的SQL语句解析成一棵抽象语法树（Abstract Syntax Tree，AST）。
- 生成逻辑计划包括通过Metastore获取相关的元数据，以及对AST进行语义分析。得到的逻辑计划为一棵由Hive操作符组成的树，Hive操作符即Hive对表数据的处理逻辑，比如对表进行扫描的TableScanOperator，对表做Group的GroupByOperator等。
- 逻辑优化即对Operator Tree进行优化，与之后的物理优化的区别主要有两点：一是在操作符级别进行调整；二是这些优化不针对特定的计算引擎。比如谓词下推（Predicate Pushdown）就是一个逻辑优化：尽早的对底层数据进行过滤以减少后续需要处理的数据量，这对于不同的计算引擎都是有优化效果的。
- 生成物理计划即针对不同的引擎，将Operator Tree划分为若干个Task，并按照依赖关系生成一棵Task的树（在生成物理计划之前，各计算引擎还可以针对自身需求，对Operator Tree再进行一轮逻辑优化）。比如，对于MapReduce，一个GROUP BY+ORDER BY的查询会被转化成两个MapReduce的Task，第一个进行Group，第二个进行排序。
- 物理优化则是各计算引擎根据自身的特点，对Task Tree进行优化。比如对于MapReduce，Runtime Skew Join的优化就是在原始的Join Task之后加入一个Conditional Task来处理可能出现倾斜的数据。
-最后按照依赖关系，依次执行Task Tree中的各个Task，并将结果返回给用户。每个Task按照不同的实现，会把任务提交到不同的计算引擎上执行。














- [LanguageManual Explain](https://cwiki.apache.org/confluence/display/Hive/LanguageManual+Explain)

.....
