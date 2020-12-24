---
layout: post
author: sjf0115
title: Hive Skewed Join
date: 2018-07-22 20:30:01
tags:
  - Hive
  - Hive 优化

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


参考：https://weidongzhou.wordpress.com/2017/06/08/join-type-in-hive-skewed-join/
