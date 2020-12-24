---
layout: post
author: sjf0115
title: Hive Union使用指南
date: 2017-03-07 20:30:01
tags:
  - Hive

categories: Hive
permalink: hive-base-how-to-use-union
---

#### 1. union语法

```sql
select_statement UNION [ALL | DISTINCT] select_statement UNION [ALL | DISTINCT] select_statement ...
```
UNION 将多个 SELECT 语句的结果集合并为一个独立的结果集。当前只能支持 UNION ALL(bag union)。不消除重复行。每个select语句返回的列的数量和名字必须一样，否则，一个语法错误会被抛出。

从语法中可以看出 UNION 有两个可选的关键字：
- 使用 DISTINCT 关键字与使用 UNION 默认值效果一样，都会删除重复行
- 使用 ALL 关键字，不会删除重复行，结果集包括所有 SELECT 语句的匹配行（包括重复行）

> 注意
Hive 1.2.0之前的版本仅支持UNION ALL，其中重复的行不会被删除。
Hive 1.2.0和更高版本中，UNION的默认行为是从结果中删除重复的行。

DISTINCT union可以显式使用UNION DISTINCT，也可以通过使用UNION而不使用以下DISTINCT或ALL关键字来隐式生成。


```
每个select_statement返回的列的数量和名称必须相同。 否则，将抛出错误。
```

**注意**
```
在Hive 0.12.0和更低版本中，UNION只能在子查询中使用，例如“SELECT * FROM（select_statement UNION ALL select_statement）unionResult”。
从Hive 0.13.0开始，UNION也可以在顶级查询中使用：例如“select_statement UNION ALL select_statement UNION ALL ...”。 （见HIVE-6189。）
在Hive 1.2.0之前，仅支持UNION ALL。
Hive 1.2.0以后版本可以支持支持UNION（或UNION DISTINCT）。 （见HIVE-9039。）
```

#### 2. UNION在FROM子句内

如果还需要对UNION的结果集进行一些其他的处理，整个语句表达式可以嵌入到FROM子句中，如下所示：
```
SELECT *
FROM (
  select_statement
  UNION ALL
  select_statement
) unionResultAlias
```
例如，假设我们有两个不同的表分别表示哪个用户发布了一个视频，以及哪个用户发布了一个评论，那么下面的查询将UNION ALL的结果与用户表join在一起，为所有视频发布和评论发布创建一个注释流：
```
SELECT u.id, actions.date
FROM (
    SELECT av.uid AS uid
    FROM action_video av
    WHERE av.date = '2008-06-03'
    UNION ALL
    SELECT ac.uid AS uid
    FROM action_comment ac
    WHERE ac.date = '2008-06-03'
 ) actions JOIN users u ON (u.id = actions.uid)
```
#### 3. DDL和插入语句的联合

UNION 可以在视图，插入和CTAS（创建表作为select）语句中使用。 查询可以包含多个UNION子句，如上面的语法中所示。

#### 4. Applying Subclauses

如果要对单个SELECT语句应用ORDER BY，SORT BY，CLUSTER BY，DISTRIBUTE BY或LIMIT，请将该子句放在括在SELECT中的括号内：
```
SELECT key FROM (SELECT key FROM src ORDER BY key LIMIT 10)subq1
UNION
SELECT key FROM (SELECT key FROM src1 ORDER BY key LIMIT 10)subq2
```
如果要对整个UNION结果应用ORDER BY，SORT BY，CLUSTER BY，DISTRIBUTE BY或LIMIT子句，请在最后一个之后放置ORDER BY，SORT BY，CLUSTER BY，DISTRIBUTE BY或LIMIT。 以下示例使用ORDER BY和LIMIT子句：
```
SELECT key FROM src
UNION
SELECT key FROM src1
ORDER BY key LIMIT 10
```

#### 5. 模式匹配的列别名
UNION期望在表达式列表的两侧有相同的模式。 因此，以下查询可能会失败，并显示一条错误消息，例如“FAILED：SemanticException 4:47 union的两边的模式应该匹配”。
```
INSERT OVERWRITE TABLE target_table
  SELECT name, id, category FROM source_table_1
  UNION ALL
  SELECT name, id, "Category159" FROM source_table_2
```
在这种情况下，列别名可使UNION两侧的模式相同：

```
INSERT OVERWRITE TABLE target_table
  SELECT name, id, category FROM source_table_1
  UNION ALL
  SELECT name, id, "Category159" as category FROM source_table_2
```
#### 6. 列类型转换

在2.2.0版本HIVE-14251之前，Hive尝试在Hive类型组（Hive type group）之间执行隐式转换。 随着HIVE-14251的改变，Hive将仅在每个类型组（包括字符串组，数字组或日期组，而不是组间）中执行隐式转换。 为了合并来自不同组的类型，例如字符串类型和日期类型，在查询中需要从字符串到日期或从日期到字符串的显式转换。
```
SELECT name, id, cast('2001-01-01' as date) d FROM source_table_1
UNION ALL
SELECT name, id, hiredate as d FROM source_table_2
```
#### 7. Example

aa数据：
```
hive> select * from tmp_union_aa;
OK
ios	aa
ios	ab
adr	ac
adr	ad
adr	ad
ios	ab
```
ab数据：
```
hive> select * from tmp_union_ab;
OK
ios	ba
ios	bb
adr	ac
adr	bd
adr	bd
ios	ab
```
union all合并：
```
hive> select * from
(
   select platform, id from tmp_union_aa
   union all
   select platform, id from tmp_union_ab
) u;

ios	aa
ios	ab
adr	ac
adr	ad
adr	ad
ios	ab
ios	ba
ios	bb
adr	ac
adr	bd
adr	bd
ios	ab

```
union 合并：
```
hive>select * from
(
   select platform, id from tmp_union_aa
   union
   select platform, id from tmp_union_ab
) u;

adr	ac
adr	ad
adr	bd
ios	aa
ios	ab
ios	ba
ios	bb

```
