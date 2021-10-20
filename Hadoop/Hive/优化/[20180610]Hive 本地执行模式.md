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

### 1. 简介

假设你正在运行一些复杂的 Hive 查询，我们都知道这会在后台触发 MapReduce 作业并为你提供输出。如果 Hive 中的数据比较大，这种方法比较有效，但如果　Hive 表中的数据比较少，这样会有一些问题。出现此问题的主要原因是 MapReduce 作业被触发，它是在服务器/集群上触发，因此每次运行查询时，它都会上传到服务器并在那里启动 MapReduce，然后输出。因此，为查询触发执行任务的时间消耗可能会比实际作业的执行时间要多的多。

Hive 可以通过本地模式在单台机器上处理所有的任务。对于本地模式，如果你的查询启动的 MapReduce 作业少于4个 Mapper，那么 MapReduce 作业将在本地运行，这样可以在更短的时间内输出查询结果。

> Hive 0.7.0 版本开始引入

### 2. 配置

需要满足如下三个配置条件，才能在本地模式下运行 Hive 查询：

参数|默认值|描述
---|---|---
hive.exec.mode.local.auto|false|让Hive确定是否自动启动本地模式运行
hive.exec.mode.local.auto.inputbytes.max|134217728(128MB)|当第一个参数为true时，输入字节小于此值时才能启动本地模式
hive.exec.mode.local.auto.input.files.max|4|当一个参数为true时，任务个数小于此值时才能启动本地模式

### 3. Example

本地模式执行如下所示：
```
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
远程模式执行如下所示：
```
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


参考：https://milindjagre.co/2015/09/04/set-hive-in-local-auto-mode/
