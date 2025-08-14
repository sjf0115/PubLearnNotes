---
layout: post
author: sjf0115
title: Hive 本地执行模式
date: 2018-06-10 20:16:01
tags:
  - Hive

categories: Hive
permalink: hive-tuning-local-mode
---

## 1. 简介

假设你正在运行一些复杂的 Hive 查询，我们都知道这会在后台触发 MapReduce 作业并为你提供输出。如果 Hive 中的数据比较大，这种方法比较有效，但如果 Hive 表中的数据比较少，这样会有一些问题。出现此问题的主要原因是 MapReduce 作业被触发，它是在服务器/集群上触发，因此每次运行查询时，它都会上传到服务器并在那里启动 MapReduce，然后输出。因此，为查询触发执行任务的时间消耗可能会比实际作业的执行时间要多的多。

在传统 Hive 执行流程中，查询会被转换为 MapReduce 提交到 Hadoop 集群执行。这种方式虽然适合处理大规模数据，但也存在一些不足：
- 启动开销大：每个查询都需要启动分布式任务，耗时较长
- 资源占用多：即使是小查询也会占用集群资源
- 调试困难：错误排查需要在分布式环境下进行

本地执行模式正是为了解决这些问题而设计的。Hive 本地执行模式是 Hive 提供的一种轻量级执行方式，通过在单台机器上执行本地任务来避免触发 MapReduce 分布式任务提交到 Hadoop 集群执行。

> Hive 0.7.0 版本开始引入

## 2. 配置

本地执行模式需要配置如下三个配置参数：

参数|默认值|描述
---|---|---
hive.exec.mode.local.auto| false | 是否自动启动本地运行模式
hive.exec.mode.local.auto.inputbytes.max | 134217728(128MB)| 设置本地模式处理的数据量阈值(默认128MB)，只有当第一个参数为 true 时才有效
hive.exec.mode.local.auto.input.files.max | 4 | 设置本地模式处理的任务数阈值，只有当第一个参数为 true 时才有效

即当满足以下条件时，Hive 会自动启用本地模式：
- `hive.exec.mode.local.auto` 设置为 true
- 输入数据量小于 `hive.exec.mode.local.auto.inputbytes.max`
- 输入任务数小于 `hive.exec.mode.local.auto.input.files.max`

### 2.1 临时启用方式

在 Hive CLI 或 Beeline 中，可以临时设置本地模式：
```sql
-- 启用本地模式
SET hive.exec.mode.local.auto=true;

-- 可选：设置本地模式处理的数据量阈值(默认128MB)
SET hive.exec.mode.local.auto.inputbytes.max=50000000;

-- 可选：设置本地模式处理的文件数阈值(默认4)
SET hive.exec.mode.local.auto.input.files.max=10;
```

### 2.2 永久配置方式

在 hive-site.xml 中添加以下配置：
```xml
<property>
  <name>hive.exec.mode.local.auto</name>
  <value>true</value>
  <description>是否自动开启本地模式</description>
</property>

<property>
  <name>hive.exec.mode.local.auto.inputbytes.max</name>
  <value>134217728</value>
  <description>本地模式处理的数据量阈值</description>
</property>

<property>
  <name>hive.exec.mode.local.auto.input.files.max</name>
  <value>4</value>
  <description>本地模式处理的任务数阈值</description>
</property>
```

### 3. Example

本地模式执行如下所示：
```sql
hive> SET hive.exec.mode.local.auto=true;
hive> SET hive.exec.mode.local.auto.inputbytes.max=50000000;
hive> SET hive.exec.mode.local.auto.input.files.max=5;
hive> select count(1) from test;
Automatically selecting local only mode for query
...
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks determined at compile time: 1
...
Job running in-process (local Hadoop)
2018-07-25 19:04:23,559 Stage-1 map = 100%,  reduce = 100%
Ended Job = job_local3079326_0001
MapReduce Jobs Launched:
Stage-Stage-1:  HDFS Read: 18214 HDFS Write: 102 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
55
Time taken: 7.542 seconds, Fetched: 1 row(s)
```
关闭本地执行模式执行如下所示：
```sql
hive> SET hive.exec.mode.local.auto=false;
hive> select count(1) from test;
...
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks determined at compile time: 1
...
Hadoop job information for Stage-1: number of mappers: 1; number of reducers: 1
2018-07-25 19:06:51,819 Stage-1 map = 0%,  reduce = 0%
2018-07-25 19:06:58,006 Stage-1 map = 100%,  reduce = 0%, Cumulative CPU 2.24 sec
2018-07-25 19:07:18,447 Stage-1 map = 100%,  reduce = 67%, Cumulative CPU 3.14 sec
2018-07-25 19:07:22,527 Stage-1 map = 100%,  reduce = 100%, Cumulative CPU 4.2 sec
MapReduce Total cumulative CPU time: 4 seconds 200 msec
Ended Job = job_1504162679223_31594449
MapReduce Jobs Launched:
Stage-Stage-1: Map: 1  Reduce: 1   Cumulative CPU: 4.2 sec   HDFS Read: 18103 HDFS Write: 102 SUCCESS
Total MapReduce CPU Time Spent: 4 seconds 200 msec
OK
55
Time taken: 89.256 seconds, Fetched: 1 row(s)
```
我们可以看到在本地模式下只需执行7.542s，而在远程模式下执行却需要执行89.256s。
