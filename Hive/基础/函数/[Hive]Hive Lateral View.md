---
layout: post
author: sjf0115
title: Hive Lateral View
date: 2019-11-24 12:42:01
tags:
  - Hive

categories: Hive
permalink: hive-lateral-view
---

### 1. 语法

```
lateralView: LATERAL VIEW udtf(expression) tableAlias AS columnAlias (',' columnAlias)*
fromClause: FROM baseTable (lateralView)*
```
### 2. 描述

Lateral View 一般与用户自定义表生成函数(split、explode等UDTF)一起使用，它能够将一行数据拆成多行数据，并在此基础上对拆分后的数据进行聚合。

在 Hive 0.6.0 之前，Lateral View 不支持谓词下推优化。在 Hive 0.5.0 以及更早版本中，如果你使用 WHERE 子句，可能不会被编译。解决方法是在你查询之前添加 `set hive.optimize.ppd = false` 。这个问题在 Hive 0.6.0 版本得到修复。从 Hive 0.12.0 中，可以省略列别名。

### 3. 单个Lateral View语句

假设我们有一张表 pageAds，它有两列数据，第一列 `page_id`（网页名称），第二列 `adid_list`（网页上显示的广告数组）：

| 名称 | 类型 |
| --- | --- |
| page_id | STRING |
| adid_list | Array<int> |

表中有两行实例数据：

| page_id | adid_list |
| --- | --- |
| contact_page | [3, 4, 5] |
| front_page | [1, 2, 3] |

假设我们要统计各个广告在所有网页中展现的次数。

(1) 拆分广告ID，如下所示：
```sql
SELECT page_id, ad_id
FROM pageAds LATERAL VIEW explode(adid_list) ad_table AS ad_id;
```
> Lateral View 与 explode()函数结合使用可以将 adid_list 转换为单独的行。

执行结果如下：

| page_id | ad_id |
| --- | --- |
| front_page | 1 |
| front_page | 2 |
| front_page | 3 |
| contact_page | 3 |
| contact_page | 4 |
| contact_page | 5 |

(2) 然后，计算各个广告的展示次数，进行聚合的统计：

```sql
SELECT ad_id, count(1)
FROM pageAds LATERAL VIEW explode(adid_list) ad_table AS ad_id
GROUP BY ad_id;
```

执行结果如下：

| adid | count(1) |
| --- | --- |
| 1 | 1 |
| 2 | 1 |
| 3 | 2 |
| 4 |	1 |
| 5 |	1 |


### 4. 多个Lateral View语句

FROM 子句可以有多个 LATERAL VIEW 子句。后面的 LATERAL VIEWS 子句可以引用出现在 LATERAL VIEWS 左侧表的任何列。

以下面的表为例：

| Array<int> pageid_list  |  Array<string> adid_list |
| --- | --- |
| [1, 2, 3] | ["a", "b", "c"] |
| [3, 4] | ["c", "d"] |

例如，如下查询：
```sql
SELECT page_id, ad_id
FROM pageAds
LATERAL VIEW explode(pageid_list) page_table AS page_id
LATERAL VIEW explode(adid_list) ad_table AS ad_id;
```
LATERAL VIEW 子句会按照它们出现的顺序执行。下面我们分部执行以下。

(1) 执行单个 Lateral View 查询：
```sql
SELECT page_id, adid_list
FROM pageAds
LATERAL VIEW explode(pageid_list) page_table AS page_id;
```
执行结果如下所示：

| page_id |	adid_list |
| --- | --- |
| 1	| ['a', 'b', 'c'] |
| 2	| ['a', 'b', 'c'] |
| 3	| ['d', 'e', 'f'] |
| 4	| ['d', 'e', 'f'] |

(2) 再加上一个 Lateral View 语句，如下所示：
```sql
SELECT page_id, ad_id
FROM pageAds
LATERAL VIEW explode(pageid_list) page_table AS page_id
LATERAL VIEW explode(adid_list) ad_table AS ad_id;
```

执行结果如下所示：

| page_id |	ad_id |
| --- | --- |
| 1	| a |
| 1	| b |
| 1	| c |
| 2	| a |
| 2	| b |
| 2 |	c |
| 3	| d |
| 3 |	e |
| 3	| f |
| 4	| d |
| 4	| e |
| 4 |	f |

### 5. Outer Lateral Views

> 在 Hive 0.12.0 版本后引入。

当 LATERAL VIEW 不会生成行时，用户可以指定可选的 OUTER 关键字来生成对应的行。当使用 EXPLODE 函数，拆分的列为空时，就会发生这种情况。在这种情况下，源数据行不会出现在结果中。如果想让源数据行继续出现在结果中，可以使用 OUTER 关键字，并且 UDTF 的空列使用 NULL 值代替。

例如，如下数据表：

| page_id |	adid_list |
| --- | --- |
| bottom_page	| [] |
| front_page | [1, 2, 3] |

例如，如下 `LATERAL VIEW` 查询：
```sql
SELECT page_id, ad_id
FROM tmp_page_ads
LATERAL VIEW EXPLODE(adid_list) ad_table AS ad_id;
```

执行结果如下所示，`bottom_page` 对应数据行不会出现在结果中：

| page_id |	ad_id |
| --- | --- |
| front_page | 1 |
| front_page | 2 |
| front_page | 3 |


例如，使用 OUTER 关键词查询：
```sql
SELECT page_id, ad_id
FROM tmp_page_ads
LATERAL VIEW OUTER EXPLODE(adid_list) ad_table AS ad_id;
```

执行结果如下所示，`bottom_page` 对应数据会出现在结果中：

| page_id |	ad_id |
| --- | --- |
| front_page | 1 |
| front_page | 2 |
| front_page | 3 |
| bottom_page | NULL |

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文：[LanguageManual LateralView](https://cwiki.apache.org/confluence/display/Hive/LanguageManual+LateralView)
