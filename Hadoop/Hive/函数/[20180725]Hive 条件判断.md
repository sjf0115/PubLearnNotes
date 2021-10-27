---
layout: post
author: sjf0115
title: Hive 条件判断
date: 2018-07-25 20:16:01
tags:
  - Hive

categories: Hive
permalink: hive-base-condition-judgment
---

Hive中可能会遇到根据值的不同产生不同结果场景，可以使用以下几个方案解决。

### 1. IF

语法：
```
IF(expr1,expr2,expr3)
```
返回值：
```
返回值具体取决于表达式 expr2 和 expr3。
```
说明：
```
如果表达式 expr1 为 TRUE 则 IF() 返回 expr2 否则返回 expr3。
```
> `expr1` 不能为 `0` 和 `NULL`，应该是一个布尔值

举例：
```
hive> SELECT IF(TRUE, "this is true", "this is false") FROM test LIMIT 1;
OK
this is true
hive> SELECT IF(FALSE, "this is true", "this is false") FROM test LIMIT 1;
OK
this is false
```

### 2. COALESCE

语法：
```sql
COALESCE(a1, a2, ...)
```
说明：
```
返回第一个不为NULL的参数。如果所有值都为NULL，那么返回NULL。
```
举例：
```
hive> SELECT COALESCE(null, "second") FROM test LIMIT 1;
OK
second
hive> SELECT COALESCE(null, null, "third") FROM test LIMIT 1;
OK
third
```
### 3. CASE WHEN

语法：
```sql
CASE a WHEN b THEN expr1 WHEN c THEN expr2 ... ELSE expr3 END
CASE WHEN expr1 THEN expr2 ... ELSE expr3 END
```
说明：
```
第一个语句：如果 a 等于 b，那么返回 expr1；如果 a 等于 c，那么返回expr2；否则返回 expr3。
第二个语句：如果 expr1 为 TRUE，那么返回 expr2；否则返回 expr3。
```
举例：
```
hive> SELECT CASE 100 WHEN 50 THEN 'Equal' ELSE 'Not Equal' END FROM test LIMIT 1;
OK
Not Equal
hive> SELECT CASE 100 WHEN 100 THEN 'Equal' ELSE 'Not Equal' END FROM test LIMIT 1;
OK
Equal
hive> SELECT CASE WHEN 100=100 THEN 'Equal' ELSE 'Not Equal' END FROM test LIMIT 1;
OK
Equal    
hive> SELECT CASE WHEN 100=50 THEN 'Equal' ELSE 'Not Equal' END FROM test LIMIT 1;
OK
Not Equal
```
