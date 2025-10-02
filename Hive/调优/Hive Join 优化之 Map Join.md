---
layout: post
author: sjf0115
title: Hive Join 优化之 Map Join
date: 2017-11-02 20:30:01
tags:
  - Hive

categories: Hive
permalink: hive-optimization-how-to-use-map-join
---

### 1. Join 如何运行

首先，让我们讨论一下 Join 如何在 Hive 中运行。Common Join 操作如下图所示被编译为 MapReduce 任务。Common Join 任务涉及 Map 阶段和 Reduce 阶段。Mapper 从 Join 表中读取数据并将 Join 的 key 和 value 以键值对形式输出到中间文件中。Hadoop 在 Shuffle 阶段对这些键值对进行排序和合并。Reducer 将排序结果作为输入，并进行 Join。因为在 Shuffle 阶段需要排序和合并，因此代价非常昂贵。减少 Shuffle 和 Reduce 阶段的代价可以提高任务性能。

![](img-hive-optimization-how-to-use-map-join-1.jpg)

Map Join 的目的是减少 Shuffle 和 Reducer 阶段的代价，并仅在 Map 阶段进行 Join。当其中一个 Join 表足够小可以装进内存时，所有 Mapper 都可以将数据保存在内存中并完成 Join。因此，所有 Join 操作都可以在 Mapper 阶段完成。但是，这种类型的 Map Join 存在一些扩展问题。当成千上万个 Mapper 同时从 HDFS 将小的 Join 表读入内存时，Join 表很容易成为性能瓶颈，导致 Mapper 在读取操作期间超时。

### 2. 使用分布式缓存

[Hive-1641](https://issues.apache.org/jira/browse/HIVE-1641) 解决了这个扩展问题。优化的基本思想是在原始 Join 的 MapReduce 任务之前创建一个新的 MapReduce 本地任务。这个新任务是将小表数据从 HDFS 上读取到内存中的哈希表中。读完后，将内存中的哈希表序列化为哈希表文件。在下一阶段，当 MapReduce 任务启动时，会将这个哈希表文件上传到 Hadoop 分布式缓存中，该缓存会将这些文件发送到每个 Mapper 的本地磁盘上。因此，所有 Mapper 都可以将此持久化的哈希表文件加载回内存，并像之前一样进行 Join。优化的 Map Join 的执行流程如下图所示。优化后，小表只需要读取一次。此外，如果多个 Mapper 在同一台机器上运行，则分布式缓存只需将哈希表文件的一个副本发送到这台机器上。

![](img-hive-optimization-how-to-use-map-join-2.jpg)
76

由于 Map Join 比 Common Join 更快，因此最好尽可能运行 Map Join。以前，Hive用户需要在查询中给出提示来指定哪一个是小表。例如：
```sql
SELECT　/*+MAPJOIN（a）*/
FROM src1 x
JOIN src2 y
ON x.key = y.key;。
```
这种方式用户体验不好，因为有时用户可能会提供错误的提示或者根本不提供任何提示。在没有用户提示的情况下将 Common Join 转换为 Map Join 用户体验会更好。

### 3. 根据文件大小将 Join 转换为 MapJoin

[Hive-1642](https://issues.apache.org/jira/browse/HIVE-1642) 通过自动将 Common Join 转换为 Map Join 来解决此问题。对于 Map Join，查询处理器知道哪个输入表是大表，哪些是小表，并将这些小表保存在内存中。然而，查询处理器在编译时不知道输入文件大小，因为一些表可能是从子查询生成的中间表。因此查询处理器只能在执行期间计算出输入文件的大小。

![](img-hive-optimization-how-to-use-map-join-3.jpg)

如上图所示，左侧流程展示了之前 Common Join 的执行流程，这非常简单。右侧流程是新的 Common Join 执行流程。在编译期间，查询处理器生成一个包含任务列表的 Conditional Task。在执行期间运行其中一个任务。首先，应将原始的 Common Join 任务放入任务列表中。然后，查询处理器通过假设每个输入表可能是大表来生成一系列的 Map Join 任务。例如，`select * from src1 x join src2 y on x.key=y.key`。因为表 src2 和 src1 都可以是大表，所以处理器生成两个 Map Join 任务，其中一个假设 src1 是大表，另一个假设 src2 是大表。

在执行阶段，Conditional Task 知道每个输入表的确切文件大小，即使该表是中间表。如果所有表都太大而无法转换为 Map Join，那么只能像以前一样运行 Common Join 任务。如果其中一个表很大，而其他表足够小可以运行 Map Join，则将 Conditional Task 选择相应 Map Join 本地任务来运行。通过这种机制，可以自动以及动态地将 Common Join 转换为 Map Join。

目前，如果小表的总大小大于 25MB，Conditional Task 会选择原始 Common Join 来运行。25MB 是一个非常保守的数字，你可以使用 `set hive.smalltable.filesize` 来修改。

### 4. Example

我们具体看一个 Map Join:
```sql
SELECT
  active.md5KeyId, active.active_time, click.click_time
FROM (
  SELECT md5KeyId, active_time
  FROM adv_push_active
  WHERE month = '201711' AND substr(activeTime, 1, 10) = '2017-11-02'
) active
JOIN (
  SELECT md5KeyId, click_time
  FROM adv_push_click
  WHERE dt = '20171102'
) click
ON upper(active.md5KeyId) = upper(click.md5KeyId);
```
输出信息如下：
```
2017-11-02 17:32:55  Starting to launch local task to process map join; maximum memory = 514850816
2017-11-02 17:33:01  Dump the side-table for tag: 0 with group count: 162 into file: file:/tmp/smartsi/xxx/hive_2017-11-02_17-32-16_498_230990327610539360-1/-local-10004/HashTable-Stage-3/MapJoin-mapfile70--.hashtable
2017-11-02 17:33:01  Uploaded 1 File to: file:/tmp/smartsi/xxx/hive_2017-11-02_17-32-16_498_230990327610539360-1/-local-10004/HashTable-Stage-3/MapJoin-mapfile70--.hashtable (17191 bytes)
2017-11-02 17:33:01  End of local task; Time Taken: 5.852 sec.
Execution completed successfully
MapredLocal task succeeded
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there no reduce operator
...
Hadoop job information for Stage-3: number of mappers: 789; number of reducers: 0
2017-11-02 17:33:13,789 Stage-3 map = 0%,  reduce = 0%
2017-11-02 17:34:14,076 Stage-3 map = 0%,  reduce = 0%, Cumulative CPU 3229.1 sec
```
我们可以看到在原始 Join 的 MapReduce 任务之前创建了一个 MapReduce Local Task。这个新任务是将小表数据从 HDFS 上读取到内存中的哈希表中，并列化为哈希表文件。后面会将这个哈希表文件上传到 Hadoop 分布式缓存中。该缓存会将这些文件发送到每个 Mapper 的本地磁盘上。这些完成之后才会启动一个只有 Map Task 的 MapReduce 作业来完成 Join。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg)

原文：https://www.facebook.com/note.php?note_id=470667928919
