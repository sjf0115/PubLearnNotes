---
layout: post
author: sjf0115
title: Hive 窗口函数
date: 2017-02-22 20:16:01
tags:
  - Hive

categories: Hive
permalink: hive-base-window-functions
---

窗口函数（window functions）可以对指定开窗列的数据灵活地进行分析处理。可以对多行进行操作，并为查询中的每一行返回一个值。OVER() 子句能将窗口函数与其他分析函数（analytical functions）和报告函数（reporting functions）区分开来。

## 1. 常用窗口函数

下表列出了一些窗口函数以及描述信息：

窗口函数 | 描述
---|---
LAG() | 取当前行往前（朝分区头部方向）第 N 行数据的值
LEAD() | 返回分区中当前行后面行（可以指定第几行）的值。 如果没有行，则返回null。
FIRST_VALUE | 返回相对于窗口中第一行的指定列的值。
LAST_VALUE | 返回相对于窗口中最后一行的指定列的值。

## 2. LAG

LAG() 取当前行往前（朝分区头部方向）第 N 行数据的值。

### 2.1 命令格式
```
lag(<expr>[，bigint <offset>[, <default>]]) over([partition_clause] orderby_clause)
```
上述命令表示返回当前行往前（朝分区头部方向）第 offset 行数据对应的表达式 expr 的值。第一个参数 expr 表达式为列名、列运算或者函数运算等，第二个参数 offset 为当前行往前第 offset 行（可选，默认为1），第三个参数为缺失时默认值（当前行往前第 offset 行没有时，返回默认值，如不指定，则为 NULL）。

### 2.2 示例

假设要计算每个用户当天获取的积分(score)与前一天获取的积分来做对比，即根据用户分组(作为开窗列)，日期升序排序，每位用户的积分向前偏移一个作为前一天获取的积分。命令示例如下：
```sql
SELECT
  uid, dt, score,
  LAG(score, 1, 0) OVER (PARTITION BY uid ORDER BY dt) AS pre_score
FROM (
    SELECT 'a' AS uid, '20220812' AS dt, 18 AS score
    UNION ALL
    SELECT 'a' AS uid, '20220813' AS dt, 15 AS score
    UNION ALL
    SELECT 'b' AS uid, '20220812' AS dt, 6 AS score
    UNION ALL
    SELECT 'b' AS uid, '20220813' AS dt, 10 AS score
) AS a
```

![]()

> 如果前一天没有该用户，即该用户没有获取积分，默认为 0



## 3. LEAD

LEAD() 取当前行往后（朝分区尾部方向）第 N 行数据的值。

### 3.1 命令格式

```sql
lead(<expr>[, bigint <offset>[, <default>]]) over([partition_clause] orderby_clause)
```
上述命令表示返回当前行往后（朝分区尾部方向）第 offset 行数据对应的表达式 expr 的值。第一个参数 expr 表达式为列名、列运算或者函数运算等，第二个参数 offset 为当前行往后第 offset 行（可选，默认为1），第三个参数为缺失时默认值（当前行往前第 offset 行没有时，返回默认值，如不指定，则为 NULL）。

### 3.2 示例

假设要计算每个用户当天获取的积分(score)与后一天获取的积分来做对比，即根据用户分组(作为开窗列)，日期升序排序，每位用户的积分向后偏移一个作为后一天获取的积分。命令示例如下：
```sql
SELECT
  uid, dt, score,
  LEAD(score, 1, 0) OVER (PARTITION BY uid ORDER BY dt) AS next_score
FROM (
    SELECT 'a' AS uid, '20220812' AS dt, 18 AS score
    UNION ALL
    SELECT 'a' AS uid, '20220813' AS dt, 15 AS score
    UNION ALL
    SELECT 'b' AS uid, '20220812' AS dt, 6 AS score
    UNION ALL
    SELECT 'b' AS uid, '20220813' AS dt, 10 AS score
) AS a
```

![]()

> 如果后一天没有该用户，即该用户还没有获取积分，默认为 0

## 4. FIRST_VALUE

为了比较每个用户浏览次数与第一天浏览次数进行比较，查询返回当前浏览次数以及第一天浏览次数。第一个用户第一天浏览次数为1，第二个用户第一天浏览次数为2。

**备注**

上面例子窗口为第一行到当前行(缺失window子句有order by ，默认为rows between unbounded preceding and current row)。所以，first_value返回窗口的第一行，即第一天浏览次数。

## 5. LAST_VALUE()

为了比较每个用户浏览次数与最新一天浏览次数进行比较，查询返回当前浏览次数以及最新一天浏览次数。第一个用户最新一天（2017-02-16）浏览次数为4，第二个用户最新一天（2017-02-16）浏览次数为2。


**备注**

上面例子的窗口为当前行到最后一行（rows between current row and unbounded following）。last_value返回的是窗口最后一行，即最新一天的浏览次数。


https://help.aliyun.com/document_detail/34994.html#section-aac-ocr-pay
