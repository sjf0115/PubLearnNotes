---
layout: post
author: sjf0115
title: Hadoop 如何使用Hadoop Archives
date: 2017-03-15 19:01:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-base-how-to-use-hadoop-archives
---

### 1. 什么是Hadoop Archives?

Hadoop Archives 是特殊的归档格式。Hadoop Archive 对应一个文件系统目录。Hadoop Archive 的扩展名为 `*.har`。Hadoop Archive 目录下包含元数据（形式是 `_index` 和 `_masterindx`）和数据（part）文件。`index` 文件包含了归档中文件的文件名和位置信息。

### 2. 如何创建Archive?

#### 2.1 语法

```
hadoop archive -archiveName name -p <parent> [-r <replication factor>] <src>* <dest>
```
参数说明：
- `-archiveName name` 参数指定你要创建归档的名字 `name`，比如 `user_order.har`。其扩展名为 `*.har`。
- `-p <parent` 参数指定文件应归档到的相对路径，例如，`-p /foo/bar a/b/c e/f/g`。这里的 `/foo/bar` 是 `a/b/c` 与 `e/f/g` 的父路径，所以完整路径为 `/foor/bar/a/b/c` 与 `/foo/bar/e/f/g`。
- `-r <replication factor>` 表示所需的复制因子，此参数为可选参数。如果不指定，复制因子默认为3。
- `src` 表示待归档文件的目录。
- `dest` 表示归档到的目标目录。

如果你只想存档单个目录 `/foo/bar`，那么你可以使用：
```
hadoop archive -archiveName zoo.har -p /foo/bar -r 3 /outputdir
```

#### 2.2 Example

```
 hadoop archive -archiveName user_order.har -p /user/smartsi user/user_active_new_user order/entrance_order test/archive
```
在上面的例子中 `/user/smartsi/user/user_active_new_user` 和 `/user/smartsi/order/entrance_order` 会被归档到 `test/aarchive/` 下，归档文件名称为 `user_order.har`。当创建归档时，源文件不会被更改或删除。注意创建归档会触发一个 MapReduce 作业。你应该在 Hadoop 集群上运行这个命令：
```
smartsi@ying:~/opt/hadoop-2.7.3$ hadoop archive -archiveName user_order.har -p /user/smartsi user/user_active_new_user order/entrance_order test/archive
...
16/12/26 20:45:37 INFO mapreduce.Job: The url to track the job: http://localhost:8080/
16/12/26 20:45:37 INFO mapreduce.Job: Running job: job_local133687258_0001
...
16/12/26 20:45:38 INFO mapred.LocalJobRunner: reduce task executor complete.
16/12/26 20:45:39 INFO mapreduce.Job:  map 100% reduce 100%
16/12/26 20:45:39 INFO mapreduce.Job: Job job_local133687258_0001 completed successfully
16/12/26 20:45:39 INFO mapreduce.Job: Counters: 35
...
```
### 3. 如何查看Archives中的文件?

Archive 作为文件系统层暴露给外界。所以所有的 `fs shell` 命令都能在 archive 上运行，但是要使用不同的URI。 另外，archive 是不可改变的。所以重命名，删除和创建都会返回错误。

Hadoop Archives 的URI是
```
har://scheme-hostname:port/archivepath/fileinarchive
```
如果没提供 `scheme-hostname`，它会使用默认的文件系统。这种情况下URI是这种形式：
```
har:///archivepath/fileinarchive
```
获得创建的archive中的文件列表，使用命令：
```
hadoop dfs -ls har:///user/smartsi/test/archive/user_order.har
```
Example：
```
smartsi@ying:~/opt/hadoop-2.7.3$ hadoop dfs -ls har:///user/smartsi/test/archive/user_order.har
DEPRECATED: Use of this script to execute hdfs command is deprecated.
Instead use the hdfs command for it.
Found 2 items
drwxr-xr-x   - smartsi supergroup          0 2016-12-13 13:39 har:///user/smartsi/test/archive/user_order.har/order
drwxr-xr-x   - smartsi supergroup          0 2016-12-24 15:51 har:///user/smartsi/test/archive/user_order.har/user
```
查看archive中的 `entrance_order.txt` 文件的命令：
```
hadoop dfs -cat har:///user/smartsi/test/archive/user_order.har/order/entrance_order/entrance_order.txt
```
输出如下：
```
smartsi@ying:~/opt/hadoop-2.7.3$ hadoop dfs -cat har:///user/smartsi/test/archive/user_order.har/order/entrance_order/entrance_order.txt
DEPRECATED: Use of this script to execute hdfs command is deprecated.
Instead use the hdfs command for it.
{"clickTime":"20161210 14:47:35.000","entrance":"306","actionTime":"20161210 14:48:14.000","orderId":"qgpww161210144814ea9","businessType":"TRAIN","gid":"0005B9C5-3B24-A63A-02C2-B4F1B369BF1D","uid":"866184028471741","vid":"60001151","income":105.5,"status":140}
{"clickTime":"20161210 14:47:35.000","entrance":"306","actionTime":"20161210 14:48:18.000","orderId":"huany161210144818e46","businessType":"TRAIN","gid":"0005B9C5-3B24-A63A-02C2-B4F1B369BF1D","uid":"866184028471741","vid":"60001151","income":105.5,"status":140}
```
### 4.archives 缺点

- 创建archives文件后，无法更新文件来添加或删除文件。 换句话说，har文件是不可变的。
- archives文件是所有原始文件的副本，所以一旦一个.har文件创建之后，它将会比原始文件占据更大的空间。不要误以为.har文件是原始文件的压缩文件。
- 当.har文件作为MapReduce作业的输入文件时，.har文件中的小文件将由单独的Mapper处理，这不是一种有效的方法。

参考：[Hadoop Archives　Guide](http://hadoop.apache.org/docs/current/hadoop-archives/HadoopArchives.html)
