---
layout: post
author: zhangpeng
title: Hive Count Distinct优化
date: 2018-06-28 20:16:01
tags:
  - Hive

categories: Hive
permalink: hive-tuning-count-distinct
---

目前，Hive底层使用MapReduce作为实际计算框架，SQL的交互方式隐藏了大部分MapReduce的细节。这种细节的隐藏在带来便利性的同时，也对计算作业的调优带来了一定的难度。未经优化的SQL语句转化后的MapReduce作业，它的运行效率可能大大低于用户的预期。本文我们就来分析一个简单语句的优化过程。

日常统计场景中，我们经常会对一段时期内的字段进行去重并统计数量，SQL语句类似于
```sql
SELECT COUNT( DISTINCT id )
FROM TABLE_NAME
WHERE ...;
```
这条语句是从一个表的符合WHERE条件的记录中统计不重复的id的总数。该语句转化为MapReduce作业后执行示意图如下，图中还列出了我们实验作业中Reduce阶段的数据规模：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hive/hive-tuning-count-distinct-1.jpg?raw=true)
由于引入了DISTINCT，因此在Map阶段无法利用Combine对输出结果去重，必须将id作为Key输出，在Reduce阶段再对来自于不同Map Task、相同Key的结果进行去重，计入最终统计值。

我们看到作业运行时的Reduce Task个数为1，对于统计大数据量时，这会导致最终Map的全部输出由单个的ReduceTask处理。这唯一的Reduce Task需要Shuffle大量的数据，并且进行排序聚合等处理，这使得它成为整个作业的IO和运算瓶颈。

经过上述分析后，我们尝试显式地增大Reduce Task个数来提高Reduce阶段的并发，使每一个Reduce Task的数据处理量控制在2G左右。具体设置如下：
```
# Hadoop1.x
set mapred.reduce.tasks=100;
# Hadoop2.x
set mapreduce.job.reduces=100;
```
调整后我们发现这一参数并没有影响实际Reduce Task个数，Hive运行时输出 `Number of reduce tasks determined at compile time: 1`。原来Hive在处理COUNT这种`全聚合(full aggregates)`计算时，会忽略用户指定的Reduce Task数，而强制使用1。我们只能采用变通的方法来绕过这一限制。我们利用Hive对嵌套语句的支持，将原来一个MapReduce作业转换为两个作业，在第一阶段选出全部的非重复id，在第二阶段再对这些已去重的id进行计数。这样在第一阶段我们可以通过增大Reduce的并发数，并发处理Map输出。在第二阶段，由于id已经去重，因此 `COUNT(*)` 操作在Map阶段不需要输出原id数据，只输出一个合并后的计数即可。这样即使第二阶段Hive强制指定一个Reduce Task，极少量的Map输出数据也不会使单一的Reduce Task成为瓶颈。改进后的SQL语句如下：
```sql
SELECT COUNT(*)
FROM
(
  SELECT DISTINCT id
  FROM TABLE_NAME
  WHERE …
) t;
```
在实际运行时，我们发现Hive还对这两阶段的作业做了额外的优化。它将第二个MapReduce作业Map中的Count过程移到了第一个作业的Reduce阶段。这样在第一阶段Reduce就可以输出计数值，而不是去重的全部id。这一优化大幅地减少了第一个作业的Reduce输出IO以及第二个作业Map的输入数据量。最终在同样的运行环境下优化后的语句执行只需要原语句20%左右的时间。优化后的MapReduce作业流如下：
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hive/hive-tuning-count-distinct-2.jpg?raw=true)

从上述优化过程我们可以看出，一个简单的统计需求，如果不理解Hive和MapReduce的工作原理，它可能会比优化后的执行过程多四、五倍的时间。我们在利用Hive简化开发的同时，也要尽可能优化SQL语句，提升计算作业的执行效率。

> 注：文中测试环境Hive版本为0.9

原文：http://bigdata-blog.net/2013/11/08/hive-sql%E4%BC%98%E5%8C%96%E4%B9%8B-count-distinct/
