---
layout: post
author: sjf0115
title: Hive Grouping Sets,CUBE与ROLLUP
date: 2018-07-05 19:16:01
tags:
  - Hive

categories: Hive
permalink: hive-base-grouping-sets
---

这篇文章描述了 SELECT 语句 GROUP BY 子句的增强聚合功能 GROUPING SETS。GROUPING SETS 子句是 SELECT 语句的 GROUP BY 子句的扩展。通过 GROUPING SETS 子句，你可采用多种方式对结果分组，而不必使用多个 SELECT 语句来实现这一目的。这就意味着，能够减少响应时间并提高性能。

> 在Hive 0.10.0版本中添加了 Grouping sets，CUBE 和 ROLLUP 运算符以及 GROUPING__ID 函数。参见[HIVE-2397](https://issues.apache.org/jira/browse/HIVE-2397)，[HIVE-3433](https://issues.apache.org/jira/browse/HIVE-3433)，[HIVE-3471](https://issues.apache.org/jira/browse/HIVE-3471)和 [HIVE-3613](https://issues.apache.org/jira/browse/HIVE-3613)。另外在Hive 0.11.0版本进行的优化 [HIVE-3552](https://issues.apache.org/jira/browse/HIVE-3552)。


### 1. GROUPING SETS

GROUP BY 中的 GROUPING SETS 子句允许我们在同一记录集中指定多个 GROUP BY 选项。所有 GROUPING SET 子句都可以逻辑表示为 UNION 连接的几个 GROUP BY 查询。下面展示了几个这样的等价示例。这有助于我们了解 GROUPING SETS 子句的思想。GROUPING SETS 子句中的空白set`（）`计算整体聚合。

```sql
SELECT a, b, SUM(c) FROM tab1 GROUP BY a, b GROUPING SETS ( (a,b) )
```
等价于:
```sql
SELECT a, b, SUM(c) FROM tab1 GROUP BY a, b
```

```sql
SELECT a, b, SUM( c ) FROM tab1 GROUP BY a, b GROUPING SETS ( (a,b), a)
```
等价于:
```sql
SELECT a, b, SUM( c ) FROM tab1 GROUP BY a, b
UNION
SELECT a, null, SUM( c ) FROM tab1 GROUP BY a
```

```sql
SELECT a,b, SUM( c ) FROM tab1 GROUP BY a, b GROUPING SETS (a,b)
```
等价于:
```sql
SELECT a, null, SUM( c ) FROM tab1 GROUP BY a
UNION
SELECT null, b, SUM( c ) FROM tab1 GROUP BY b
```

```sql
SELECT a, b, SUM( c ) FROM tab1 GROUP BY a, b GROUPING SETS ( (a, b), a, b, ( ) )
```
等价于:
```sql
SELECT a, b, SUM( c ) FROM tab1 GROUP BY a, b
UNION
SELECT a, null, SUM( c ) FROM tab1 GROUP BY a, null
UNION
SELECT null, b, SUM( c ) FROM tab1 GROUP BY null, b
UNION
SELECT null, null, SUM( c ) FROM tab1
```

### 2. Grouping__ID

GROUPING SETS　会对 GROUP BY 子句中的列进行多维组合，结果整体展现，对于没有参与 GROUP BY 的那一列置为 `NULL` 值。如果列本身值就为 `NULL`，则可能会发生冲突。这样我们就没有办法去区分该列显示的 `NULL` 值是列本身就是 `NULL` 值，还是因为该列没有参与 GROUP BY 而被置为 `NULL` 值。所以需要一些方法来识别列中的NULL，`GROUPING__ID` 函数就是为了解决这个问题而引入的。

此函数返回一个位向量，与每列是否存在对应。用二进制形式中的每一位来标示对应列是否参与 GROUP BY。Hive2.3.0版本之前，如果某一列参与了 GROUP BY，对应位就被置为`1`，否则为`0`。在这一版本，GROUPING__ID 与位向量之间的关系比较别扭，GROUPING__ID实际为位向量先反转之后再转为十进制的值。这一点，在Hive2.3.0版本得到解决，如果某一列参与了 GROUP BY，对应位就被置为`0`，否则为`1`。所以在使用 GROUPING__ID 时注意一下版本号。

> GROUPING__ID 的值与 GROUP BY 表达式中列的取值和顺序有关，所以如果重新排列，GROUPING__ID 对应的含义也会变化。

具体看一个例子（数据内容以及表结构可以在文章末尾查看）：
```sql
SELECT GROUPING__ID, dt, platform, channel, SUM(pv), COUNT(DISTINCT userName)
FROM tmp_read_pv
GROUP BY dt, platform, channel GROUPING SETS ( dt, (dt, platform), (dt, channel), (dt, platform, channel));
```
输出结果如下：

序号|GROUPING__ID|位向量|日期|平台|渠道|浏览量|用户数
---|---|---|---|---|---|---|---
1|1|100|20180627|NULL|NULL|242.0|8
2|1|100|20180628|NULL|NULL|282.0|9
3|3|110|20180627|adr|NULL|137.0|6
4|3|110|20180627|ios|NULL|105.0|2
5|3|110|20180628|NULL|NULL|26.0|1
6|3|110|20180628|adr|NULL|96.0|4
7|3|110|20180628|ios|NULL|160.0|4
8|5|101|20180627|NULL|toutiao|149.0|6
9|5|101|20180627|NULL|uc|93.0|6
10|5|101|20180628|NULL|NULL|96.0|1
11|5|101|20180628|NULL|toutiao|89.0|7
12|5|101|20180628|NULL|uc|97.0|6
13|7|111|20180627|adr|toutiao|82.0|5
14|7|111|20180627|adr|uc|55.0|4
15|7|111|20180627|ios|toutiao|67.0|1
16|7|111|20180627|ios|uc|38.0|2
17|7|111|20180628|NULL|uc|26.0|1
18|7|111|20180628|adr|toutiao|35.0|4
19|7|111|20180628|adr|uc|61.0|3
20|7|111|20180628|ios|NULL|96.0|1
21|7|111|20180628|ios|toutiao|54.0|3
22|7|111|20180628|ios|uc|10.0|2

> Hive2.1.1版本下生成的数据

例如上面的第5，10，17，20行所示，有些字段本身值就为 `NULL`。

如果希望没有参与 GROUP BY 的列不显示 `NULL` 而是显示一个自定义值（例如，`total` 表示对应分组的全量），
```sql
SELECT
  GROUPING__ID,
  CASE WHEN (CAST (GROUPING__ID AS INT) & 1) == 0 THEN 'total' ELSE dt END,
  CASE WHEN (CAST (GROUPING__ID AS INT) & 2) == 0 THEN 'total' ELSE platform END,
  CASE WHEN (CAST (GROUPING__ID AS INT) & 4) == 0 THEN 'total' ELSE channel END,
  dt, platform, channel, SUM(pv), COUNT(DISTINCT userName)
FROM tmp_read_pv
GROUP BY dt, platform, channel GROUPING SETS ( dt, (dt, platform), (dt, channel), (dt, platform, channel));
```
结果如下:

GROUPING__ID|日期昵称|平台昵称|渠道昵称|日期|平台|渠道|浏览量|用户数
---|---|---|---|---|---|---|---|---
1|20180627| total|total|20180627| NULL| NULL| 242.0|8
1|20180628| total|total|20180628| NULL| NULL| 282.0|9
3|20180628| adr|total|20180628| adr|NULL| 96.0| 4
3|20180627| ios|total|20180627| ios|NULL| 105.0|2
3|20180628| NULL| total|20180628| NULL| NULL| 26.0| 1
3|20180627| adr|total|20180627| adr|NULL| 137.0|6
3|20180628| ios|total|20180628| ios|NULL| 160.0|4
5|20180628| total|NULL| 20180628| NULL| NULL| 96.0| 1
5|20180628| total|toutiao|20180628| NULL| toutiao|89.0| 7
5|20180627| total|toutiao|20180627| NULL| toutiao|149.0|6
5|20180628| total|uc| 20180628| NULL| uc| 97.0| 6
5|20180627| total|uc| 20180627| NULL| uc| 93.0| 6
7|20180627| adr|uc| 20180627| adr|uc| 55.0| 4
7|20180627| ios|toutiao|20180627| ios|toutiao|67.0| 1
7|20180628| ios|uc| 20180628| ios|uc| 10.0| 2
7|20180628| NULL| uc| 20180628| NULL| uc| 26.0| 1
7|20180628| adr|uc| 20180628| adr|uc| 61.0| 3
7|20180628| ios|NULL| 20180628| ios|NULL| 96.0| 1
7|20180627| adr|toutiao||20180627| adr|toutiao|82.0| 5
7|20180628| adr|toutiao||20180628| adr|toutiao|35.0| 4
7|20180627| ios|uc| 20180627| ios|uc| 38.0| 2
7|20180628| ios|toutiao|20180628| ios|toutiao|54.0| 3

> Hive2.1.1版本下生成的数据

如果对于列本身值没有为 `NULL` 的情况，可以使用如下简单方式来实现：
```sql
SELECT
  GROUPING__ID,
  CASE WHEN dt IS NULL THEN 'total' ELSE dt END,
  CASE WHEN platform IS NULL THEN 'total' ELSE platform END,
  CASE WHEN channel IS NULL THEN 'total' ELSE channel END,
  SUM(pv), COUNT(DISTINCT userName)
FROM tmp_read_pv
GROUP BY dt, platform, channel GROUPING SETS ( dt, (dt, platform), (dt, channel), (dt, platform, channel));
```

### 4. CUBE与ROLLUP

通用语法是 `WITH CUBE/ROLLUP`。只能 GROUP BY 一起使用。

#### 4.1 CUBE

CUBE 简称数据魔方，可以实现 Hive 多个任意维度的查询。CUBE 创建集合中所有可能组合。例如：
```sql
GROUP BY a，b，c WITH CUBE
```
等价于
```sql
GROUP BY a，b，c GROUPING SETS（（a，b，c），（a，b），（b，c），（a，c），（a），（b），（c），（））。
```

#### 4.2 ROLLUP

ROLLUP 子句与 GROUP BY 一起使用用来计算维度上层次结构级别的聚合。ROLLUP 可以实现从右到左递减多级的统计。

具有 ROLLUP 的 `GROUP BY a，b，c` 假定层次结构为 `a` 向下钻取到(drilling down) `b`，向下钻取到 `c`。例如：
```sql
GROUP BY a，b，c WITH ROLLUP
```
等价于:
```sql
GROUP BY a，b，c GROUPING SETS（（a，b，c），（a，b），（a），（））
```

### 5. 数据

演示数据：
```
20180627	adr	toutiao	d918	7
20180627  adr uc  d918  30
20180628	adr	uc	d918	15
20180628	adr	toutiao	d918	10
20180627	ios	uc	828b	16
20180628	ios	uc	828b	6
20180628	ios	toutiao	828b	18
20180627	adr	toutiao	cece	5
20180628	adr	toutiao	cece	8
20180627	ios	toutiao	6428	67
20180627	ios	uc	6428	22
20180627	adr	uc	e962	9
20180627	adr	uc	e962	8
20180628	ios	toutiao	953c	13
20180628	ios	toutiao	953c	7
20180627	adr	toutiao	f930	54
20180628	adr	toutiao	f930	8
20180627	adr	uc	f930	4
20180628	adr	uc	f930	40
20180627	adr	uc	2bfa	4
20180627	adr	toutiao	2bfa	7
20180628	adr	uc	2bfa	6
20180628	adr	toutiao	2bfa	9
20180627	adr	toutiao	2f3d	5
20180627	adr	toutiao	2f3d	4
20180628	ios	\N	2f3d	62
20180628	ios	\N	2f3d	34
20180628	\N	uc	5f02	12
20180628	\N	uc	5f02	14
20180628	ios	uc	f215	4
20180628	ios	toutiao	f215	16
```
演示表：
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS tmp_read_pv (
  dt string,
  platform string,
  channel string,
  userName string,
  pv string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
LOCATION '/user/xiaosi/tmp/data_group/example/input/read_pv/';
```

> Hive版本:2.1.1

参考：https://stackoverflow.com/questions/29577887/grouping-in-hive

https://cwiki.apache.org/confluence/display/Hive/Enhanced+Aggregation%2C+Cube%2C+Grouping+and+Rollup
