---
layout: post
author: sjf0115
title: Hadoop 如何使用 Archives 实现归档
date: 2017-03-15 19:01:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-base-how-to-use-hadoop-archives
---

### 1. 什么是 Hadoop Archives?

Hadoop Archives 是一种特殊的归档格式。Hadoop Archive 对应一个文件系统目录，扩展名为 `*.har`。Hadoop Archive 目录下包含元数据（形式是 `_index` 和 `_masterindx`）和数据（part）文件。`index` 文件包含了归档中文件的文件名和位置信息。

### 2. 如何创建归档文件

具体语法如下所示：
```
hadoop archive -archiveName name -p <parent> [-r <replication factor>] <src>* <dest>
```
参数说明：
- `-archiveName name` 参数指定你要创建归档的名字 `name`。比如 `user_order.har`，扩展名必须为 `*.har`。
- `-p <parent>` 参数指定待归档文件的父路径。例如，`-p /a a1 a2`。这里的 `/a` 是 `a1` 和 `a2` 的父路径，所以需要归档的目录是 `/a/a1` 和 `/a/a2`。
- `-r <replication factor>` 表示所需的复制因子，此参数为可选参数。如果不指定，复制因子默认为3。
- `src` 表示待归档文件的目录。
- `dest` 表示归档到的目标目录。

下面我们具体看一个实际的例子，在下面的例子中将 `/data/word-count/word-count-output-v1` 和 `/data/word-count/word-count-output-v2` 归档到 `/data/archive` 目录下，归档文件名称为 `word-count`：
```
hadoop archive -archiveName word-count.har -p /data/word-count word-count-output-v1 word-count-output-v2 /data/archive
```
> 当创建归档时，源文件不会被更改或删除。

如果你只想存档单个目录 `/data/word-count/word-count-output-v1`，那么你可以运行如下命令：
```
hadoop archive -archiveName word-count.har -p /data/word-count/word-count-output-v1 /data/archive
```

需要注意的是创建归档会触发一个 MapReduce 作业，所以你需要在 Hadoop 集群上运行归档命令：
```
localhost:script wy$ hadoop archive -archiveName word-count.har -p /data/word-count word-count-output-v1 word-count-output-v2 /data/archive
22/07/04 21:52:35 INFO client.RMProxy: Connecting to ResourceManager at /0.0.0.0:8032
22/07/04 21:52:36 INFO client.RMProxy: Connecting to ResourceManager at /0.0.0.0:8032
22/07/04 21:52:36 INFO client.RMProxy: Connecting to ResourceManager at /0.0.0.0:8032
22/07/04 21:52:37 INFO mapreduce.JobSubmitter: number of splits:1
22/07/04 21:52:37 INFO mapreduce.JobSubmitter: Submitting tokens for job: job_1656942601721_0001
22/07/04 21:52:37 INFO impl.YarnClientImpl: Submitted application application_1656942601721_0001
22/07/04 21:52:37 INFO mapreduce.Job: The url to track the job: http://localhost:8088/proxy/application_1656942601721_0001/
22/07/04 21:52:37 INFO mapreduce.Job: Running job: job_1656942601721_0001
22/07/04 21:52:43 INFO mapreduce.Job: Job job_1656942601721_0001 running in uber mode : false
22/07/04 21:52:43 INFO mapreduce.Job:  map 0% reduce 0%
22/07/04 21:52:48 INFO mapreduce.Job:  map 100% reduce 0%
22/07/04 21:52:53 INFO mapreduce.Job:  map 100% reduce 100%
22/07/04 21:52:53 INFO mapreduce.Job: Job job_1656942601721_0001 completed successfully
22/07/04 21:52:53 INFO mapreduce.Job: Counters: 49
	File System Counters
		FILE: Number of bytes read=758
		FILE: Number of bytes written=250565
		FILE: Number of read operations=0
		FILE: Number of large read operations=0
		FILE: Number of write operations=0
		HDFS: Number of bytes read=936
		HDFS: Number of bytes written=829
		HDFS: Number of read operations=25
		HDFS: Number of large read operations=0
		HDFS: Number of write operations=7
	Job Counters
		Launched map tasks=1
		Launched reduce tasks=1
		Other local map tasks=1
		Total time spent by all maps in occupied slots (ms)=2262
		Total time spent by all reduces in occupied slots (ms)=2199
		Total time spent by all map tasks (ms)=2262
		Total time spent by all reduce tasks (ms)=2199
		Total vcore-milliseconds taken by all map tasks=2262
		Total vcore-milliseconds taken by all reduce tasks=2199
		Total megabyte-milliseconds taken by all map tasks=2316288
		Total megabyte-milliseconds taken by all reduce tasks=2251776
	Map-Reduce Framework
		Map input records=8
		Map output records=8
		Map output bytes=736
		Map output materialized bytes=758
		Input split bytes=114
		Combine input records=0
		Combine output records=0
		Reduce input groups=8
		Reduce shuffle bytes=758
		Reduce input records=8
		Reduce output records=0
		Spilled Records=16
		Shuffled Maps =1
		Failed Shuffles=0
		Merged Map outputs=1
		GC time elapsed (ms)=94
		CPU time spent (ms)=0
		Physical memory (bytes) snapshot=0
		Virtual memory (bytes) snapshot=0
		Total committed heap usage (bytes)=328728576
	Shuffle Errors
		BAD_ID=0
		CONNECTION=0
		IO_ERROR=0
		WRONG_LENGTH=0
		WRONG_MAP=0
		WRONG_REDUCE=0
	File Input Format Counters
		Bytes Read=720
	File Output Format Counters
		Bytes Written=0
```

### 3. 如何查看归档文件?

Hadoop Archive 作为一个文件系统层暴露给外界，所以所有的 `fs` shell 命令都可以对归档使用。在归档中查看文件就像在文件系统上执行 ls 一样简单，需要注意的是要使用不同的 URI。Hadoop Archives 的 URI 是：
```
har://scheme-hostname:port/archivepath/fileinarchive
```
如上例所示归档了 /data/word-count/word-count-output-v1 和 /data/word-count/word-count-output-v2 两个文件，那么要查看归档中的文件，只需运行如下命令：
```
localhost:script wy$ hadoop fs -ls har://hdfs-localhost:9000/data/archive/word-count.har
Found 2 items
drwxr-xr-x   - wy supergroup          0 2022-07-02 17:27 har://hdfs-localhost:9000/data/archive/word-count.har/word-count-output-v1
drwxr-xr-x   - wy supergroup          0 2022-07-03 09:40 har://hdfs-localhost:9000/data/archive/word-count.har/word-count-output-v2
```
在这 scheme 为 hdfs，hostname 为 localhost，port 为 9000。如果没提供 `scheme-hostname:port`，那么会使用默认的文件系统。此时要查看归档中的文件，只需运行如下命令
```
localhost:script wy$ hadoop fs -ls har:///data/archive/word-count.har
Found 2 items
drwxr-xr-x   - wy supergroup          0 2022-07-02 17:27 har:///data/archive/word-count.har/word-count-output-v1
drwxr-xr-x   - wy supergroup          0 2022-07-03 09:40 har:///data/archive/word-count.har/word-count-output-v2
```

这里明确 URI 必须使用 har，如果我们把它当做一个正常的 HDFS 文件来访问，会有什么样的效果呢？运行如下命令查看 HDFS 文件内容：
```
localhost:script wy$ hadoop fs -ls hdfs:///data/archive/word-count.har
Found 4 items
-rw-r--r--   1 wy supergroup          0 2022-07-04 21:52 hdfs:///data/archive/word-count.har/_SUCCESS
-rw-r--r--   5 wy supergroup        704 2022-07-04 21:52 hdfs:///data/archive/word-count.har/_index
-rw-r--r--   5 wy supergroup         23 2022-07-04 21:52 hdfs:///data/archive/word-count.har/_masterindex
-rw-r--r--   1 wy supergroup        102 2022-07-04 21:52 hdfs:///data/archive/word-count.har/part-0
```
前面我们了解到 Hadoop Archive 目录下会包含元数据和数据文件，此时这里的 `_index` 和 `_masterindx` 对应的是归档的元数据文件，part-0 是归档的数据文件。归档文件在 HDFS 中实际上是以一个目录形式存在的，在该目录下又包含了多个文件。

如果要查看归档文件中的 word-count-output-v1 文件的内容，只需要运行如下命令：
```
localhost:script wy$ hadoop fs -cat har:///data/archive/word-count.har/word-count-output-v1/*
Hadoop	1
I	3
a	1
student	1
studying	2
Flink	1
am	3
```

此外需要注意的是归档文件是不可变，所以重命名，删除和创建都会返回错误：

### 4. 解归档

解归档其实是一个复制问题。只需要按顺序解归档复制即可：
```
hadoop fs -cp har:///data/archive/word-count.har/word-count-output-v1 hdfs:/data/word-count/bak-word-count-output-v1
```
要并行解归档，需要使用 DistCp 命令：
```
hadoop distcp -cp har:///data/archive/word-count.har/word-count-output-v1 hdfs:/data/word-count/bak-word-count-output-v1
```

### 5. Archives 缺点

- 创建 archives 文件后，无法通过添加或删除文件来更新文件。换句话说，har 文件是不可变文件。
- archives 文件是原始文件的副本，所以一旦一个 `.har` 文件创建之后，它将会比原始文件占据更大的空间。不要误以为 `.har` 文件是原始文件的压缩文件。
- 当 `.har` 文件作为 MapReduce 作业的输入文件时，`.har` 文件中的小文件将由单独的 Mapper 处理，这不是一种有效的方法。


参考：[Hadoop Archives　Guide](http://hadoop.apache.org/docs/current/hadoop-archives/HadoopArchives.html)
