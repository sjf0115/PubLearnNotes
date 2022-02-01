---
layout: post
author: sjf0115
title: Hive 分组TopN
date: 2018-01-01 19:16:01
tags:
  - Hive

categories: Hive
permalink: hive-base-group-top-n
---

### 1. TopN

这个场景下我们很容易想到的一个解决方案就是全局排序之后取前N个。Hive 提供了 LIMIT 关键字，再配合 ORDER BY 可以很容易地实现。如下代码所示：
```sql
SELECT score FROM tmp_student_score ORDER BY score LIMIT 10;
```
但是，在 Hive 中，ORDER BY 保证数据的全局有序，为此将所有的数据发送到一个 Reducer 中。因为只有一个 Reducer ，所以当输入规模较大时，需要较长的计算时间。假设数据表有1亿条数据，而我们只想取TOP 10，那在1个 Reducer 中对1亿条数据惊醒全局排序显然不合理。

这时我们可以选用 SORT BY 而不是 ORDER BY。前者虽然不会保证全局有序，但是会保证每个 Reducer 输出的有序。
```sql
SELECT score FROM tmp_student_score SORT BY score LIMIT 10;
```

### 2. 分组TopN

```
1班     数学    76.0
1班     语文    95.0
2班     数学    97.0
2班     语文    91.0
3班     数学    83.0
3班     语文    92.0
4班     数学    77.0
4班     语文    81.0
5班     数学    77.0
5班     语文    83.0
6班     数学    94.0
6班     语文    79.0
7班     数学    80.0
7班     语文    90.0
8班     数学    94.0
8班     语文    72.0
9班     数学    76.0
9班     语文    80.0
10班    数学    73.0
10班    语文    78.0
```
如上数据所示，我们想要每个科目前5名的班级，结果如下所示：
```
数学    97.0    2班     1
数学    94.0    8班     2
数学    94.0    6班     3
数学    83.0    3班     4
数学    80.0    7班     5
语文    95.0    1班     1
语文    92.0    3班     2
语文    91.0    2班     3
语文    90.0    7班     4
语文    83.0    5班     5
```
最常用的解决方案是使用 `ROW_NUMBER()` 函数，代码所示：
```sql
SELECT *
FROM
(
  SELECT subject, score, class, ROW_NUMBER() OVER (PARTITION BY subject ORDER BY score DESC) AS ranks
  FROM tmp_student_score
) score
WHERE ranks < 5;
```
