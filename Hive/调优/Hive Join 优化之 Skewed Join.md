---
layout: post
author: sjf0115
title: Hive Join 优化之 Skewed Join
date: 2018-07-22 20:30:01
tags:
  - Hive

categories: Hive
permalink: hive-optimization-how-to-use-skewed-join
---

Skewed Join 可以解决这个问题。在运行时，它会扫描数据并检测具有较大倾斜的 key，Hive 在运行时是没有办法判断哪个 key 会产生多大的倾斜，所以使用参数 `hive.skewjoin.key` 来控制倾斜的阈值。不是处理这些 key，而是将它们临时存储在一个 HDFS 目录中。后面会启动一个新的 MapReduce 作业来处理那些倾斜的 key。对于所有表来说，相同的 key 有可能不都是倾斜的，因此会是一个 map-join，这个新的 MapReduce 作业（对于倾斜的 key）执行会更快一些。

例如，假设我们A表和B表在id列上进行 Join：
```sql
SELECT	A.*
FROM	A
JOIN B
ON A.id	=	B.id;
```

A表有一个 id　列，在数值 `k1` 上有数据倾斜，即相对于这一列的其他值来说 `k1` 数据量比较大。B表 id 列也有 `k1` 值，但是数据量远没有A表的大。这种情形下，第一步是扫描B表并将 `k1` 对应的所有行数据保存在内存中的 HashTable 中。完成后，然后运行一组 Mapper 来读取A表 `k1` 的数据完成一个 map-join。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hive/hive-optimization-how-to-use-skewed-join-1.png?raw=true)

> 黄色的 A表的 `k1` 有数据倾斜，对应的B表 `k1`　没有数据倾斜，因此后续的 MapReduce 作业(Job2) 是一个 `map-join`。

我们可以看到B表在 Skewed Join 期间被扫描两次。A表中的倾斜 key 只通过 Mapper 读取和处理，不需要发送到 Reducer。对于A表中的其余 key，它们使用常规的 common-join。

要使用 Skewed Join，你需要了解你的数据和查询。将参数 `hive.optimize.skewjoin` 设置为true。参数 `hive.skewjoin.key` 是可选的，默认为100000。
```
set hive.optimize.skewjoin = true;
set hive.skewjoin.key=100000;
```

如何识别 是否使用了 Skewed Join？使用 EXPLAIN 命令时，你将会在 Join Operator 和 Reduce Operator Tree 下面看到 `handleSkewJoin：true`。

有几种方法可以优化 HIVE 中的 Skew join 问题。 以下是一些：

### 单独的查询

我们可以将查询拆分为多个查询并单独运行以避免数据倾斜。考虑到我们的示例表，我们需要编写 2 个查询来避免 skew join：

执行不包括 SKEWED 值的查询，如下所示：
```sql
SELECT *
FROM FACT AS a
LEFT JOIN DIMENSION b
ON a.code_id = b.code_id
WHERE a.code_id <> 250;
```
仅使用 SKEWED 值执行查询，如下所示：
```sql
SELECT *
FROM FACT AS a
LEFT JOIN DIMENSION b
ON a.code_id = b.code_id
WHERE a.code_id = 250 AND b.code_id = 250;
```

优势：
- 对查询最一点简单的更改就可以避免 JOIN 时的数据倾斜。
- 当查询很简单时很有帮助。

劣势：
- 我们需要编写两次相同的查询。
- 如果原始查询很复杂，那么编写 2 个单独的查询也会比较困难。
- 如果我们想修改查询时，需要在 2 个不同的地方进行修改。

### 使用 Hive 配置

我们可以使用 Hive 配置开启 Skew Join 优化，如下所示：
```sql
SET hive.optimize.skewjoin=true;
SET hive.skewjoin.key=500000;
SET hive.skewjoin.mapjoin.map.tasks=10000;
SET hive.skewjoin.mapjoin.min.split=33554432;
```

下面我们详细看一下配置项：
- hive.optimize.skewjoin：是否开启 Skew JOIN 优化，默认值为 false。在运行时，检测倾斜较大的 Key。不会处理这些 Key，而是将它们临时存储在 HDFS 目录中。在后续的 MapReduce 作业中，再处理这些倾斜的 Key。
- hive.skewjoin.key：判断我们 JOIN 中是否有倾斜 Key。如果相同 Key 的行超过了指定阈值，那么我们认为该 Key 是一个 Skew JOIN Key。默认值为 100000。
- hive.skewjoin.mapjoin.map.tasks：用来处理倾斜 Key 的 Map JOIN 作业的 Map 任务数，默认值为 10000。与 hive.skewjoin.mapjoin.min.split 参数配合使用。
- hive.skewjoin.mapjoin.min.split：用来处理倾斜 Key 的 Map JOIN 的最小数据切分大小，以字节为单位，默认为 33554432(32M)。与 hive.skewjoin.mapjoin.map.tasks 参数配合使用。
- hive.optimize.skewjoin.compiletime：

hive.optimize.skewjoin.compiletime 和 hive.optimize.skewjoin 区别为前者为编译时参数，后者为运行时参数。前者在生成执行计划时根据元数据生成 skewjoin，此参数要求倾斜值一定；后者为运行过程中根据数据条数进行skewjoin优化。



> 上述参数在 Hive 0.6.0 版本中引入。




参考：
- https://weidongzhou.wordpress.com/2017/06/08/join-type-in-hive-skewed-join/
- https://medium.com/expedia-group-tech/skew-join-optimization-in-hive-b66a1f4cc6ba
