---
layout: post
author: sjf0115
title: Hive 性能调优
date: 2018-04-12 20:16:01
tags:
  - Hive
  - Hive 优化

categories: Hive
permalink: hive-performance-tuning
---

在本文中，我们将简要讨论如何优化Hive查询，以及Hive性能调优的几点建议。

### 1. 在Hive中启用压缩

通过在各个阶段（即最终输出，中间数据）启用压缩，实现 Hive 查询中的性能改进。有关如何启用压缩Hive的更多详细信息，请参阅[Hive 启用压缩](http://smartsi.club/2018/04/12/hive-enable-compression/)。

### 2. 优化Join

我们可以通过启用 `Auto Convert Map Joins` 以及 启用 `skew joins` 的优化来提高 Join 的性能。

#### 2.1 Auto Map Joins

当一个大表与一个小表 Join 时，`Auto Map-Join` 是一个非常有用的功能。如果我们启用此功能，则小表将保存在每个节点的本地缓存中，然后在 Map 阶段与大表连接。启用 `Auto Map Join` 提供了两点优势。首先，将一个小表加载到缓存中将节省每个数据节点上的读取时间。 其次，它避免了Hive查询中的 `skew joins `，因为连接操作已经在Map阶段已经完成了。

启用 `Auto Map Join ` 功能，我们需要设置下面的属性：
```xml
<property>
   <name>hive.auto.convert.join</name>
   <value>true</value>
   <description>Whether Hive enables the optimization about converting common join into mapjoin based on the input file size</description>
 </property>
 <property>
   <name>hive.auto.convert.join.noconditionaltask</name>
   <value>true</value>
   <description>
     Whether Hive enables the optimization about converting common join into mapjoin based on the input file size.
     If this parameter is on, and the sum of size for n-1 of the tables/partitions for a n-way join is smaller than the
     specified size, the join is directly converted to a mapjoin (there is no conditional task).
   </description>
 </property>
 <property>
   <name>hive.auto.convert.join.noconditionaltask.size</name>
   <value>10000000</value>
   <description>
     If hive.auto.convert.join.noconditionaltask is off, this parameter does not take affect.
     However, if it is on, and the sum of size for n-1 of the tables/partitions for a n-way join is smaller than this size,
     the join is directly converted to a mapjoin(there is no conditional task). The default is 10MB
   </description>
 </property>
 <property>
   <name>hive.auto.convert.join.use.nonstaged</name>
   <value>false</value>
   <description>
     For conditional joins, if input stream from a small alias can be directly applied to join operator without
     filtering or projection, the alias need not to be pre-staged in distributed cache via mapred local task.
     Currently, this is not working with vectorization or tez execution engine.
   </description>
 </property>
```






































原文：http://hadooptutorial.info/hive-performance-tuning/#1_Enable_Compression_in_Hive
