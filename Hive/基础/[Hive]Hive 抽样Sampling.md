---
layout: post
author: sjf0115
title: Hive 抽样Sampling
date: 2018-05-12 19:16:01
tags:
  - Hive

categories: Hive
permalink: hive-base-how-to-use-sampling
---

### 1. Block 抽样

Block 抽样功能在 Hive 0.8 版本开始引入。具体参阅JIRA - [Input Sampling By Splits](https://issues.apache.org/jira/browse/HIVE-2121)

```
block_sample: TABLESAMPLE (n PERCENT)
```
该语句允许至少抽取 n% 大小的数据（注意：不是行数，而是数据大小）做为输入，仅支持 `CombineHiveInputFormat` ，不能够处理一些特殊的压缩格式。如果抽样失败，MapReduce 作业的输入将是整个表或者是分区的数据。由于在 HDFS 块级别进行抽样，所以抽样粒度为块大小。例如如果块大小为256MB，即使 n% 的输入仅为100MB，那也会得到 256MB 的数据。

在下面例子中 0.1% 或更多的输入数据用于查询：
```sql
SELECT *
FROM source TABLESAMPLE(0.1 PERCENT) s;
```
如果希望在不同的块中抽取相同大小的数据，可以改变下面的参数：
```
set hive.sample.seednumber=<INTEGER>;
```
或者可以指定要读取的总长度，但与 `PERCENT` 抽样具有相同的限制。（从Hive 0.10.0开始 - https://issues.apache.org/jira/browse/HIVE-3401）
```
block_sample: TABLESAMPLE (ByteLengthLiteral)

ByteLengthLiteral : (Digit)+ ('b' | 'B' | 'k' | 'K' | 'm' | 'M' | 'g' | 'G')
```
在下面例子中中 100M 或更多的输入数据用于查询：
```sql
SELECT *
FROM source TABLESAMPLE(100M) s;
```
Hive 还支持按行数对输入进行限制，但它与上述两种行为不同。首先，它不需要 `CombineHiveInputFormat`，这意味着这可以在 non-native 表上使用。其次，用户给定的行数应用到每个 InputSplit 上。 因此总行数还取决于输入 InputSplit 的个数（不同 InputSplit 个数得到的总行数也会不一样）。（从Hive 0.10.0开始 - https://issues.apache.org/jira/browse/HIVE-3401）
```
block_sample: TABLESAMPLE (n ROWS)
```
例如，以下查询将从每个输入 InputSplit 中取前10行：
```sql
SELECT * FROM source TABLESAMPLE(10 ROWS);
```
因此如果有20个 InputSplit 就会输出200条记录。

### 2. 分桶表抽样

语法：
```
table_sample: TABLESAMPLE (BUCKET x OUT OF y [ON colname])
```

`TABLESAMPLE` 子句允许用户编写对抽样数据的查询，而不是对整个表格进行查询。`TABLESAMPLE` 子句可以添加到任意表中的 `FROM` 子句中。桶从1开始编号。`colname` 表明在哪一列上对表的每一行进行抽样。`colname` 可以是表中的非分区列，也可以使用 `rand()` 表明在整行上抽样而不是在单个列上。表中的行在 `colname` 上进行分桶，并随机分桶到编号为1到y的桶上。返回属于第x个桶的行。下面的例子中，返回32个桶中的第3个桶中的行，`s` 是表的别名：
```sql
SELECT * FROM source TABLESAMPLE(BUCKET 3 OUT OF 32 ON rand()) s;
```
通常情况下，`TABLESAMPLE` 将扫描整个表并抽取样本。但是，这并不是一种有效率的方式。相反，可以使用 `CLUSTERED BY` 子句创建该表，表示在该表的一组列上进行哈希分区/分簇。如果 `TABLESAMPLE子` 句中指定的列与 `CLUSTERED BY` 子句中的列匹配，则 `TABLESAMPLE` 仅扫描表中所需的哈希分区。

所以在上面的例子中，如果使用 `CLUSTERED BY id INTO 32 BUCKETS` 创建表 `source`（根据id将数据分到32个桶中）：
```
TABLESAMPLE(BUCKET 3 OUT OF 16 ON id)
```
会返回第3个和第19个簇，因为每个桶由（32/16）= 2个簇组成（创建表时指定了32个桶，会对应32个簇）。为什么选择3和19呢，因为要返回的是第3个桶，而每个桶由原来的2个簇组成，`3%16=3 19%16=3`，第3个桶就由原来的第3个和19个簇组成。
另一个例子:
```
TABLESAMPLE(BUCKET 3 OUT OF 64 ON id)
```
会返回第三个簇的一半，因为每个桶将由（32/64）= 1/2个簇组成。

原文:https://cwiki.apache.org/confluence/display/Hive/LanguageManual+Sampling
