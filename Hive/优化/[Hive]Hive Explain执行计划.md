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
















.....
