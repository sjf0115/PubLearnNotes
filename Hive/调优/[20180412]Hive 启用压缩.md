---
layout: post
author: sjf0115
title: Hive 启用压缩
date: 2018-04-12 20:16:01
tags:
  - Hive

categories: Hive
permalink: hive-enable-compression
---

对于数据密集型任务，I/O操作和网络数据传输需要花费相当长的时间才能完成。通过在 Hive 中启用压缩功能，我们可以提高 Hive 查询的性能，并节省 HDFS 集群上的存储空间。

### 1. Hive中的可用压缩编解码器

要在 Hive 中启用压缩，首先我们需要找出 Hadoop 集群上可用的压缩编解码器，我们可以使用下面的 set 命令列出可用的压缩编解码器。
```
hive> set io.compression.codecs;
io.compression.codecs=
  org.apache.hadoop.io.compress.GzipCodec,
  org.apache.hadoop.io.compress.DefaultCodec,
  org.apache.hadoop.io.compress.BZip2Codec,
  org.apache.hadoop.io.compress.SnappyCodec,
  com.hadoop.compression.lzo.LzoCodec,
  com.hadoop.compression.lzo.LzopCodec
```
### 2. 在中间数据上启用压缩

提交后，一个复杂的 Hive 查询通常会转换为一系列多阶段 MapReduce 作业，这些作业将通过 Hive 引擎进行链接以完成整个查询。因此，这里的 '中间输出' 是指前一个 MapReduce 作业的输出，将会作为下一个 MapReduce 作业的输入数据。

可以通过使用 Hive Shell 中的 set 命令或者修改 hive-site.xml 配置文件来修改 `hive.exec.compress.intermediate` 属性，这样我们就可以在 Hive Intermediate 输出上启用压缩。

```xml
<property>
   <name>hive.exec.compress.intermediate</name>
   <value>true</value>
   <description>
     This controls whether intermediate files produced by Hive between multiple map-reduce jobs are compressed.
     The compression codec and other options are determined from Hadoop config variables mapred.output.compress*
   </description>
</property>
<property>
   <name>hive.intermediate.compression.codec</name>
   <value>org.apache.hadoop.io.compress.SnappyCodec</value>
   <description/>
</property>
<property>
   <name>hive.intermediate.compression.type</name>
   <value>BLOCK</value>
   <description/>
</property>
```
或者我们可以使用 set 命令在 hive shell 中设置这些属性，如下所示:
```
set hive.exec.compress.intermediate=true;
set hive.intermediate.compression.codec=org.apache.hadoop.io.compress.SnappyCodec;
set hive.intermediate.compression.type=BLOCK;
```
### 3. 在最终输出上启用压缩

通过设置以下属性，我们可以在 Hive shell 中的最终输出上启用压缩:
```xml
<property>
  <name>hive.exec.compress.output</name>
  <value>true</value>
  <description>
    This controls whether the final outputs of a query (to a local/HDFS file or a Hive table) is compressed.
    The compression codec and other options are determined from Hadoop config variables mapred.output.compress*
  </description>
</property>
```
或者
```
set hive.exec.compress.output=true;
set mapreduce.output.fileoutputformat.compress=true;
set mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.GzipCodec;  
set mapreduce.output.fileoutputformat.compress.type=BLOCK;
```
### 4. Example

在下面的 shell 代码片段中，我们在 hive shell 中将压缩属性设置为 true 后，根据现有表 tmp_order_id 创建一个压缩后的表 tmp_order_id_compress。

为了对比，我们先根据现有表 tmp_order_id 创建一个不经压缩的表 tmp_order_id_2:
```
CREATE TABLE tmp_order_id_2 ROW FORMAT DELIMITED LINES TERMINATED BY '\n'
AS SELECT * FROM tmp_order_id;
```
我们看一下不设置压缩属性输出:
```
[xiaosi@ying:~]$  sudo -uxiaosi hadoop fs -ls /user/hive/warehouse/xiaosidata.db/tmp_order_id_2/
Found 1 items
-rwxr-xr-x   3 xiaosi xiaosi       2565 2018-04-18 20:38 /user/hive/warehouse/hivedata.db/tmp_order_id_2/000000_0
```
在 Hive Shell 中设置压缩属性：
```
hive> set hive.exec.compress.output=true;
hive> set mapreduce.output.fileoutputformat.compress=true;
hive> set mapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.GzipCodec;
hive> set mapreduce.output.fileoutputformat.compress.type=BLOCK;
hive> set hive.exec.compress.intermediate=true;
```
根据现有表 tmp_order_id 创建一个压缩后的表 tmp_order_id_compress:
```
hive> CREATE TABLE tmp_order_id_compress ROW FORMAT DELIMITED LINES TERMINATED BY '\n'
    > AS SELECT * FROM tmp_order_id;
Query ID = xiaosi_20180418204750_445d742f-be89-47fb-9d2c-2b0eeac76c09
Total jobs = 3
Launching Job 1 out of 3
Number of reduce tasks is set to 0 since there's no reduce operator
Starting Job = job_1504162679223_21624651, Tracking URL = http://xxx:9981/proxy/application_1504162679223_21624651/
Kill Command = /home/xiaosi/hadoop-2.2.0/bin/hadoop job  -kill job_1504162679223_21624651
Hadoop job information for Stage-1: number of mappers: 1; number of reducers: 0
2018-04-18 20:47:59,575 Stage-1 map = 0%,  reduce = 0%
2018-04-18 20:48:04,711 Stage-1 map = 100%,  reduce = 0%, Cumulative CPU 1.28 sec
MapReduce Total cumulative CPU time: 1 seconds 280 msec
Ended Job = job_1504162679223_21624651
Stage-4 is selected by condition resolver.
Stage-3 is filtered out by condition resolver.
Stage-5 is filtered out by condition resolver.
Moving data to directory hdfs://cluster/user/hive/warehouse/hivedata.db/.hive-staging_hive_2018-04-18_20-47-50_978_2339056359585839454-1/-ext-10002
Moving data to directory hdfs://cluster/user/hive/warehouse/hivedata.db/tmp_order_id_compress
MapReduce Jobs Launched:
Stage-Stage-1: Map: 1   Cumulative CPU: 1.28 sec   HDFS Read: 6012 HDFS Write: 1436 SUCCESS
Total MapReduce CPU Time Spent: 1 seconds 280 msec
OK
Time taken: 14.902 seconds
```
我们在看一下设置压缩属性后输出:
```
[xiaosi@ying:~]$  sudo -uxiaosi hadoop fs -ls /user/hive/warehouse/hivedata.db/tmp_order_id_compress/
Found 1 items
-rwxr-xr-x   3 xiaosi xiaosi       1343 2018-04-18 20:48 /user/hive/warehouse/hivedata.db/tmp_order_id_compress/000000_0.gz
```

因此，我们可以使用 gzip 格式创建输出文件。

原文：http://hadooptutorial.info/enable-compression-in-hive/
