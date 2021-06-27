---
layout: post
author: sjf0115
title: Hive SORT BY vs ORDER BY vs DISTRIBUTE BY vs CLUSTER BY
date: 2018-06-21 13:30:01
tags:
  - Hive

categories: Hive
permalink: hive-base-sort-order-distribute-cluster
---

在这篇文章中，我们主要来了解一下 SORT BY，ORDER BY，DISTRIBUTE BY 和 CLUSTER BY 在 Hive 中的表现。

### 1. Order By

在 Hive 中，ORDER BY 保证数据的全局有序，为此将所有的数据发送到一个 Reducer 中。因为只有一个 Reducer ，所以当输入规模较大时，需要较长的计算时间。

Hive 中的 ORDER BY 语法与 SQL 中 ORDER BY 的语法相似，按照某一项或者几项排序输出，可以指定是升序或者是降序排序。ORDER BY 子句有一些限制。在严格模式下（即，`hive.mapred.mode = strict`），ORDER BY 子句后面必须跟一个 LIMIT 子句。如果将 `hive.mapred.mode` 设置为 `nonstrict`，可以不用 LIMIT 子句。原因是为了实现所有数据的全局有序，只能使用一个 reducer 来对最终输出进行排序。如果输出中的行数太大，单个 Reducer 可能需要很长时间才能完成。

如果在严格模式不指定 LIMIT 子句，会报如下错误：
```
hive> set hive.mapred.mode=strict;
hive> select * from adv_push_click order by click_time;
FAILED: SemanticException 1:47 order by-s without limit are disabled for safety reasons. If you know what you are doing, please make sure that hive.strict.checks.large.query is set to false and that hive.mapred.mode is not set to 'strict' to enable them.. Error encountered near token 'click_time'
```
> hive.mapred.mode 在 Hive 0.3.0 版本加入，默认值如下:
- Hive 0.x: nonstrict
- Hive 1.x: nonstrict
- Hive 2.x: strict (HIVE-12413)

请注意，列是按名称指定的，而不是按位置编号指定的。在 Hive 0.11.0 以及更高版本中，实现如下配置时，可以按位置指定列：
- 对于 Hive 0.11.0 到 2.1.x，将 `hive.groupby.orderby.position.alias` 设置为 `true`（默认值为false）。
- 对于 Hive 2.2.0 以及更高版本，`hive.orderby.position.alias` 默认为 `true`。

默认的排序顺序是升序（ASC）。

在 Hive 2.1.0 以及更高版本中，支持在 ORDER BY 子句中指定每个列的 NULL 排序顺序。`ASC` 的默认 NULL 排序顺序为 `NULLS FIRST`，`DESC` 的默认 NULL 排序顺序为 `NULLS LAST`。

### 2. Sort By

SORT BY 语法与 SQL 中 ORDER BY 的语法类似。

Hive 根据 SORT BY 中的列对行进行排序，然后发送到 Reducer 中 排序顺序将取决于列类型。如果该列是数字类型的，则排序顺序也是数字顺序。如果该列是字符串类型，那么排序顺序是字典顺序。

#### 2.1 Sort By 与 Order By 的区别

ORDER BY 和 SORT BY 之间的区别在于，前者保证输出的全局有序，而后者仅保证每个 Reducer 输出的有序，不保证全局有序。如果有多个 Reducer，SORT BY 输出的最终结果可能只是部分有序。

> 可能会混淆在单独列上的 SORT BY 和 CLUSTER BY 之间的区别。不同之处在于，CLUSTER BY 按字段进行分区，如果在多个 Reducer 随机分配数据(加载)使用 SORT BY。

每个 Reducer 的输出将根据用户指定的列进行排序。如下显示：
```
SELECT key, value FROM src SORT BY key ASC, value DESC
```
查询有2个 Reducer，每个的输出为：
```
# First Reducer
0   5
0   3
3   6
9   1
# Second Reducer
0   4
0   3
1   1
2   5
```
正如我们看到的那样，每个 Reducer 的输出是有序的，但是全局并没有序，因为每个 Reducer 都有一个输出。

#### 2.2 设置排序方式

应用 Transform 之后，变量类型通常被认为是字符串，这意味着数字数据将按照字典顺序排序。为了解决这个问题，可以在使用SORT BY之前使用带有强制转换的第二个SELECT语句。
```sql
FROM
(
  FROM
  (
    FROM src
    SELECT TRANSFORM(value)
    USING 'mapper'
    AS value, count
  ) mapped
  SELECT cast(value as double) AS value, cast(count as int) AS count
  SORT BY value, count
) sorted
SELECT TRANSFORM(value, count)
USING 'reducer'
AS whatever
```

> 更多关于 TRANSFORM 请查阅[LanguageManual Transform](https://cwiki.apache.org/confluence/display/Hive/LanguageManual+Transform#LanguageManualTransform-TRANSFORMExamples)

### 3. Distribute By

Distribute By 可以确保每个 Reducer 都获得列的非重叠范围，即 Distribute By 子句中的列在各个Reducer中没有重叠，但不会对每个 Reducer 的输出进行排序。最终会得到N个或更多未排序的文件。

Hive 根据 Distribute By 子句中的列将行划分到 Reducer 中。具有相同分布的列的所有行会划分到同一个 Reducer 中。例如，我们下面5行数据分配给2个 Reducer：
```
x1
x2
x4
x3
x1
```
Reducer 1：
```
x1
x2
x1
```
Reducer 2：
```
x4
x3
```
注意，所有具有相同键 x1 的行都保证被分配到同一个 Reducer 中（上例中为 Reducer 1），但不保证它们在相邻的位置(即没有对每个 Reducer 的输出进行排序)。

### 4. Cluster By

CLUSTER BY 确保每个 Reducer 都获得非重叠范围，然后在 Reducer 上对这些范围进行排序。上面例子中没有对每个 Reducer 中的数据进行排序。如果我们使用 `Cluster By x`，则每个 Reducer 将进一步对 x 进行排序。

Reducer 1：
```
x1
x1
x2
```
Reducer 2：
```
x3
x4
```
Cluster By 是 Distribute By 和 Sort By 的缩写。你也可以不使用 Cluster By，而是使用 Distribute By 和 Sort By 来代替，这样分区列和排序列可以不同。通常的情况是分区列是排序列的前缀，但这不是必需的。
```sql
SELECT col1, col2 FROM t1 CLUSTER BY col1
SELECT col1, col2 FROM t1 DISTRIBUTE BY col1
SELECT col1, col2 FROM t1 DISTRIBUTE BY col1 SORT BY col1 ASC, col2 DESC
```



参考：https://cwiki.apache.org/confluence/display/Hive/LanguageManual+SortBy#LanguageManualSortBy-SyntaxofOrderBy

https://saurzcode.in/2015/01/hive-sort-order-distribute-cluster/
