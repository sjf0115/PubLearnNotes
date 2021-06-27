---
layout: post
author: sjf0115
title: Hive 子查询
date: 2018-05-01 15:30:01
tags:
  - Hive

categories: Hive
permalink: hive-base-sub-queries
---

### 1. FROM中的子查询

```sql
SELECT ... FROM (subquery) name ...
SELECT ... FROM (subquery) AS name ...   (Note: Only valid starting with Hive 0.13.0)
```

Hive仅在FROM子句中支持子查询（从Hive 0.12版本开始）。必须为子查询指定名称，因为FROM子句中的每个表都必须具有名称。子查询 SELECT 列表中的列必须具有独一无二的名称。子查询 SELECT 列表中的列可以在外部查询中使用，就像使用表中的列一样。子查询也可以是带 UNION 的查询表达式。Hive支持任意级别的子查询。

在Hive 0.13.0及更高版本（HIVE-6519）中可选关键字 `AS` 可以包含的子查询名称之前。使用简单子查询的示例：
```sql
SELECT col
FROM (
  SELECT a+b AS col
  FROM t1
) t2
```
包含UNION ALL的子查询示例：
```sql
SELECT t3.col
FROM (
  SELECT a+b AS col
  FROM t1
  UNION ALL
  SELECT c+d AS col
  FROM t2
) t3
```

### 2. WHERE中的子查询

从Hive 0.13开始，WHERE子句中支持某些类型的子查询。可以将这些子查询的结果视为 IN 和 NOT IN 语句中的常量（我们也称这些子查询为不相关子查询，因为子查询不引用父查询中的列）。

```sql
SELECT Id, LastName, FirstName, Address, City
FROM Persons
WHERE Id IN ( SELECT PersonId FROM Orders);
```
也可以支持 EXISTS 和 NOT EXISTS 子查询：
```sql
SELECT *
FROM Persons
WHERE EXISTS ( SELECT * FROM Orders WHERE Orders.PersonId = Persons.Id);
```
有一些限制：
- 子查询仅支持在表达式的右侧。
- IN/NOT IN 子查询只能选择一列。
- EXISTS/NOT EXISTS 必须有一个或多个相关谓词。
- 对父查询的引用仅在子查询的WHERE子句中支持。

原文：https://cwiki.apache.org/confluence/display/Hive/LanguageManual+SubQueries#LanguageManualSubQueries-SubqueriesintheWHEREClause
