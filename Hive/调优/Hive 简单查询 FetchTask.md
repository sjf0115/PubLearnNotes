---
layout: post
author: sjf0115
title: Hive 简单查询 FetchTask
date: 2017-12-21 20:16:01
tags:
  - Hive
  - Hive 优化

categories: Hive
permalink: hive-tuning-fetch-task-conversion
---

在 Hadoop 生态中，Hive 作为经典的数据仓库工具，其核心是将类 SQL 查询（HQL）转化为分布式计算任务（如 MapReduce、Tez、Spark）来执行。这为处理海量数据（PB 级）提供了强大的能力。然而，启动这些分布式任务本身是有显著开销的：资源调度（YARN）、启动 JVM 容器、任务初始化、中间结果 Shuffle 等。想象一下，你只是想看一眼表的前 10 行数据，或者快速查询某个特定分区的几条记录，却需要等待几十秒甚至几分钟，仅仅因为系统启动了一整套“重装武器”来处理这个“小目标”——这无疑是巨大的资源浪费和体验痛点。

## 1. FetchTask 应运而生：轻量高效的解决方案

FetchTask 正是 Hive 为了解决上述“大炮打蚊子”问题而设计的核心优化机制。它的核心思想非常简单却极其有效：对于满足特定条件的简单查询，完全绕过复杂的 MapReduce/Tez/Spark 执行引擎，直接从数据存储（HDFS）或元存储（Metastore）读取所需数据并返回给客户端。

FetchTask 的价值：为什么它如此重要？
- 极致的低延迟： 这是 FetchTask 最核心的价值。避免了分布式任务的启动和管理开销，使得简单查询的响应时间从秒级甚至分钟级骤降至毫秒级或亚秒级。用户体验提升是质的飞跃。
- 降低资源消耗： 无需申请和占用 YARN 资源（Containers）、减少 JVM 启动/销毁开销、避免不必要的网络传输（Shuffle）。这对集群的整体资源利用率和稳定性有积极影响，尤其是在高并发执行大量小查询的场景下。
- 提升开发与探索效率： 数据分析师和工程师在进行数据探查（Data Exploration）、数据质量检查、调试 SQL 语句时，经常需要执行 SELECT * FROM ... LIMIT N 或带简单过滤的查询。FetchTask 让这些操作变得极其迅捷，大大提升了工作效率。
- 优化元数据操作： 像 SHOW TABLES, SHOW PARTITIONS, DESCRIBE TABLE 这类仅需访问 Metastore 的元数据操作，天生就通过 FetchTask 执行，快速返回结果。




通过将 SELECT 查询转换为一个 FETCH 任务，可以最大限度地减少交互的延迟。在目前情况下，查询只能是单一数据源，不能有任何的子查询，不能有任何的聚合，去重（导致RS - `ReduceSinkOperator`，会产生 MapReduce 任务），`Lateral views` 以及 `Join`。Fetch 任务是 Hive 中执行效率比较高的任务之一。直接遍历文件并输出结果，而不是启动 MapReduce 作业进行查询。对于简单的查询，如带有 `LIMIT` 语句的 `SELECT * ` 查询，这会非常快(单位数秒级)。在这种情况下，Hive 可以通过执行 HDFS 操作来返回结果。

Example:
```sql
hive>  SELECT * FROM tmp_client_behavior LIMIT 1;
OK
2017-08-16      22:24:54   ...
Time taken: 0.924 seconds, Fetched: 1 row(s)
```
如果我们只想得到几列怎么办？
```
hive> select vid, gid, os from tmp_client_behavior;
Query ID = wirelessdev_20170817203931_02392cd8-5df7-42e6-87ea-aaa1418e000c
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there's no reduce operator
Starting Job = job_1472052053889_23316306, Tracking URL = xxx
Kill Command = /home/q/hadoop/hadoop-2.2.0/bin/hadoop job  -kill job_1472052053889_23316306
Hadoop job information for Stage-1: number of mappers: 1; number of reducers: 0
2017-08-17 20:39:39,886 Stage-1 map = 0%,  reduce = 0%
2017-08-17 20:39:46,000 Stage-1 map = 100%,  reduce = 0%, Cumulative CPU 1.32 sec
MapReduce Total cumulative CPU time: 1 seconds 320 msec
Ended Job = job_1472052053889_23316306
MapReduce Jobs Launched:
Stage-Stage-1: Map: 1   Cumulative CPU: 1.32 sec   HDFS Read: 581021 HDFS Write: 757 SUCCESS
Total MapReduce CPU Time Spent: 1 seconds 320 msec
OK
...
```
从上面日志中我们可以看到会启动 MapReduce 任务，只有 1 个 Mapper 并且没有 Reducer。有没有方法可以让我们避免启动上面的 MapReduce 作业？这就需要设置 `hive.fetch.task.conversion` 配置：
```xml
<property>
  <name>hive.fetch.task.conversion</name>
  <value>none|minimal|more</value>
</property>
```
Hive 已经做过优化了，从Hive 0.10.0 版本开始，对于简单的不需要聚合去重的查询语句，可以不需要运行 MapReduce 任务，直接通过查询 HDFS 获取数据:
```sql
hive> select vid, gid, os from tmp_client_behavior limit 10;
OK
60001 A34D4B08788A adr
...
```

## 2. 配置

### 2.1 hive.fetch.task.conversion

FetchTask 并非对所有查询都生效。它的行为由关键参数 `hive.fetch.task.conversion` 严格掌控：
```xml
<property>
  <name>hive.fetch.task.conversion</name>
  <value>none|minimal|more</value>
</property>
```
可支持的选项有 `none`,`minimal` 和 `more`，从 Hive 0.10.0 版本到 Hive 0.13.1 版本起，默认值为 `minimal`，Hive 0.14.0版本以及更高版本默认值改为 `more`。理解这个参数的不同模式至关重要。

#### 2.1.1 none

> 在Hive 0.14.0版本中引入

禁用任何形式的 Fetch Task 优化。所有查询，无论多么简单（包括 SELECT * FROM table LIMIT 1;），都强制走 MapReduce（或 Tez/Spark）执行引擎。

优点：
- 行为绝对一致，完全避免了直接 Fetch 大量数据的风险。

缺点：
- 对简单查询的性能影响极其巨大。即使是看一眼表的前几行数据，也可能需要等待几十秒甚至几分钟（等待资源调度、启动任务等）。
- 用户体验极差，不适合交互式操作。

#### 2.1.2 minimal

> 从 Hive 0.10.0 版本到 Hive 0.13.1 版本起，默认值为 `minimal`。

仅对以下两种极其简单的查询进行优化：
- `SELECT * FROM table_name;`
  - 没有任何 WHERE 子句，没有聚合，没有 LIMIT 时
  - 注意：这在实际中很少单独使用，因为会返回全表数据)
- `SELECT * FROM table_name WHERE partition_column = 'value' ... LIMIT N;`
  - 仅当 WHERE 子句是基于分区字段的等值过滤，并且查询包含 LIMIT 时。


优点：
- 适用范围非常窄，几乎不会出现意外行为。

缺点：
- 对大多数常见的简单查询（如带非分区字段过滤或 LIMIT 的查询）无效，优化效果有限。

#### 2.1.3 more

> Hive 0.14.0 版本以及更高版本默认值改为 `more`。推荐值，最常用且最实用。

当使用 `SELECT`，`LIMIT` 以及过滤时，`more` 选项下也可以转换为 Fetch 任务（SELECT, FILTER, LIMIT only (including TABLESAMPLE, virtual columns)）。`more` 可以在 `SELECT` 子句中使用任何表达式，包括UDF。（UDTF和 `Lateral views`尚不支持）。

优点：
- 覆盖了绝大多数交互式查询、数据探查场景，性能提升效果显著。

缺点：
- 无 LIMIT 且可能返回大量数据的查询，直接 Fetch 可能对 HS2 或客户端造成压力（OOM/网络拥堵）。强烈建议配合 `hive.fetch.task.conversion.threshold` 使用！

### 2.2 hive.fetch.task.conversion.threshold

为了防止 more 模式下对“语法简单但数据量巨大”的查询意外触发 FetchTask（导致 HS2 尝试扫描海量文件），Hive 提供了 `hive.fetch.task.conversion.threshold` 参数作为安全阀：
```xml
<property>
  <name>hive.fetch.task.conversion.threshold</name>
  <value>1073741824</value>
</property>
```

> 从 Hive 0.13.0 版本到 Hive 0.13.1 版本起，默认值为`-1`（表示没有任何的限制），Hive 0.14.0 版本以及更高版本默认值改为 `1073741824`(1G)。

使用 `hive.fetch.task.conversion` 的输入阈值（以字节为单位）。如果目标表在本机，则输入长度通过文件长度的总和来计算。如果不在本机，则表的存储处理程序可以选择实现 `org.apache.hadoop.hive.ql.metadata.InputEstimator` 接口。负阈值意味着使用 `hive.fetch.task.conversion` 没有任何的限制。

Example:
```
hive> set hive.fetch.task.conversion.threshold=100000000;
hive> select * from passwords limit 1;
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there's no reduce operator
Starting Job = job_201501081639_0046, Tracking URL = http://n1a.mycluster2.com:50030/jobdetails.jsp?jobid=job_201501081639_0046
Kill Command = /opt/mapr/hadoop/hadoop-0.20.2/bin/../bin/hadoop job  -kill job_201501081639_0046
Hadoop job information for Stage-1: number of mappers: 1; number of reducers: 0
2015-01-15 12:19:06,474 Stage-1 map = 0%,  reduce = 0%
2015-01-15 12:19:11,496 Stage-1 map = 100%,  reduce = 100%, Cumulative CPU 0.85 sec
MapReduce Total cumulative CPU time: 850 msec
Ended Job = job_201501081639_0046
MapReduce Jobs Launched:
Job 0: Map: 1   Cumulative CPU: 0.85 sec   MAPRFS Read: 0 MAPRFS Write: 0 SUCCESS
Total MapReduce CPU Time Spent: 850 msec
OK
root x 0 0 root /root /bin/bash
Time taken: 6.698 seconds, Fetched: 1 row(s)
```
调整阈值变大则会使用 Fetch 任务:
```
hive> set hive.fetch.task.conversion.threshold=600000000;
hive> select * from passwords limit 1;
OK
root x 0 0 root /root /bin/bash
Time taken: 0.325 seconds, Fetched: 1 row(s)
```

> 此参数根据表大小而不是结果集大小来计算或估计。

## 3. 设置 Fetch 任务

第一种方式是直接在命令行中使用 `set` 命令进行设置:
```
hive> set hive.fetch.task.conversion=more;
```
第二种方式是使用 `hiveconf` 进行设置:
```
bin/hive --hiveconf hive.fetch.task.conversion=more
```
上面的两种方法虽然都可以开启 Fetch Task，但是都是临时的。如果你想一直启用这个功能，可以在 `${HIVE_HOME}/conf/hive-site.xml` 里面修改配置：
```xml
<property>
  <name>hive.fetch.task.conversion</name>
  <value>more</value>
</property>
```




hive.fetch.task.conversion

默认值为none。参数取值如下：

none：关闭Fetch task优化。

在执行语句时，执行MapReduce程序。

minimal：只在SELECT、FILTER和LIMIT的语句上进行优化。

more：在minimal的基础上更强大，SELECT不仅仅是查看，还可以单独选择列，FILTER也不再局限于分区字段，同时支持虚拟列（别名）。


https://help.aliyun.com/zh/emr/emr-on-ecs/user-guide/optimize-hive-jobs#section-hu0-vq2-tdi
