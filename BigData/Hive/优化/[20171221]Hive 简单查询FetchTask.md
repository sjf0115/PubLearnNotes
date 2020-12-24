---
layout: post
author: sjf0115
title: Hive 简单查询FetchTask
date: 2017-12-21 20:16:01
tags:
  - Hive
  - Hive 优化

categories: Hive
permalink: hive-tuning-fetch-task-conversion
---

### 1. 简介

某些 SELECT 查询可以转换为一个 FETCH 任务，从而最大限度地可以减少交互的延迟。在目前情况下，查询只能是单一数据源，不能有任何的子查询，不能有任何的聚合，去重（导致RS - `ReduceSinkOperator`，会产生 MapReduce 任务），`Lateral views` 以及 `Join`。Fetch 任务是 Hive 中执行效率比较高的任务之一。直接遍历文件并输出结果，而不是启动 MapReduce 作业进行查询。对于简单的查询，如带有 `LIMIT` 语句的 `SELECT * ` 查询，这会非常快(单位数秒级)。在这种情况下，Hive 可以通过执行 HDFS 操作来返回结果。

Example:
```
hive>  SELECT * FROM tmp_client_behavior LIMIT 1;
OK
2017-08-16      22:24:54   ...
Time taken: 0.924 seconds, Fetched: 1 row(s)
```
如果我们只想得到几列怎么办？
```
hive> select vid, gid, os from tmp_client_behavior;
WARNING: Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
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
从日志中我们可以看到会启动 MapReduce 任务，只有1个 Mapper 但没有 Reducer。有没有方法可以让我们避免启动上面的 MapReduce 作业？这就需要设置 `hive.fetch.task.conversion` 配置：
```
<property>
  <name>hive.fetch.task.conversion</name>
  <value>none|minimal|more</value>
</property>
```
Hive 已经做过优化了，从Hive 0.10.0 版本开始，对于简单的不需要聚合去重的查询语句，可以不需要运行 MapReduce 任务，直接通过查询 HDFS 获取数据:
```
hive> select vid, gid, os from tmp_client_behavior limit 10;
OK
60001 A34D4B08788A adr
...
```

### 2. 配置

#### 2.1 hive.fetch.task.conversion

```xml
<property>
  <name>hive.fetch.task.conversion</name>
  <value>none|minimal|more</value>
</property>
```
可支持的选项有 `none`,`minimal` 和 `more`，从Hive 0.10.0 版本到 Hive 0.13.1 版本起，默认值为 `minimal`，Hive 0.14.0版本以及更高版本默认值改为 `more`:
- `none`: 禁用 `hive.fetch.task.conversion`（在Hive 0.14.0版本中引入）
- `minimal`: 当使用 `LIMIT` 或在分区列上执行过滤（`WHERE` 和 `HAVING`子句），以及执行 `SELECT *` 时，可以转换为 Fetch 任务（SELECT `*`, FILTER on partition columns (WHERE and HAVING clauses), LIMIT only）。
- `more`：当使用 `SELECT`，`LIMIT` 以及过滤时，`more` 选项下也可以转换为 Fetch 任务（SELECT, FILTER, LIMIT only (including TABLESAMPLE, virtual columns)）。`more` 可以在 `SELECT` 子句中使用任何表达式，包括UDF。（UDTF和 `Lateral views`尚不支持）。

> 对具体使用条件有点疑问

#### 2.2 hive.fetch.task.conversion.threshold

```xml
<property>
  <name>hive.fetch.task.conversion.threshold</name>
  <value>1073741824</value>
</property>
```

从 Hive 0.13.0 版本到 Hive 0.13.1 版本起，默认值为`-1`（表示没有任何的限制），Hive 0.14.0 版本以及更高版本默认值改为 `1073741824`(1G)。

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

### 3. 设置Fetch任务

(1) 直接在命令行中使用`set`命令进行设置:
```
hive> set hive.fetch.task.conversion=more;
```
(2) 使用`hiveconf`进行设置
```
bin/hive --hiveconf hive.fetch.task.conversion=more
```
(3) 上面的两种方法都可以开启了Fetch Task，但是都是临时起作用的；如果你想一直启用这个功能，可以在${HIVE_HOME}/conf/hive-site.xml里面修改配置：
```xml
<property>
  <name>hive.fetch.task.conversion</name>
  <value>more</value>
</property>
```
