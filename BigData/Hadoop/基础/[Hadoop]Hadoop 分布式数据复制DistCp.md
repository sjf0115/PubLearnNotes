---
layout: post
author: sjf0115
title: Hadoop 分布式数据复制DistCp
date: 2017-01-22 11:01:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-distributed-copy-distcp
---

## 1.需求

我们项目中需要复制一个大文件，最开始使用的是 `hadoop cp` 命令，但是随着文件越来越大，拷贝的时间也水涨船高。此时发现了 Hadoop 一个比较实用的工具 `DistCp` 可以用来实现分布式拷贝，加速拷贝的速度。下面就进行 `hadoop cp` 与 `hadoop distcp` 拷贝时间上的一个对比。我们将 `data_group/adv/day=20180509` 目录下 11.9G 的文件复制到 `tmp/data_group/adv/` 目录下

### 1.1 查看文件大小
```
hadoop fs -du -s -h data_group/adv/day=20180509
11.9 G  data_group/adv/day=20180509
```
### 1.2 复制
```
hadoop distcp data_group/adv/day=20180509 tmp/data_group/adv/

hadoop fs -cp data_group/adv/day=20180509 tmp/data_group/adv/
```

### 1.3 时间对比

使用 hadoop distcp 命令 仅耗时1分钟；而 hadoop cp 命令耗时14分钟

## 2. 概述

DistCp（分布式拷贝）是用于大规模集群内部和集群之间拷贝的工具。 它使用 Map/Reduce 实现文件分发，错误处理和恢复，以及报告生成。它把文件和目录的列表作为 map 任务的输入，每个任务都会复制源列表中指定文件的一个分区。

```
17/01/19 14:30:07 INFO tools.DistCp: Input Options: DistCpOptions{atomicCommit=false, syncFolder=false, deleteMissing=false, ignoreFailures=false, maxMaps=20, sslConfigurationFile='null', copyStrategy='uniformsize', sourceFileListing=null, sourcePaths=[data_group/adv/day=20180509], targetPath=tmp/data_group/adv/day=20180509}
...
17/01/19 14:30:17 INFO mapreduce.Job:  map 0% reduce 0%
17/01/19 14:30:29 INFO mapreduce.Job:  map 6% reduce 0%
17/01/19 14:30:34 INFO mapreduce.Job:  map 41% reduce 0%
17/01/19 14:30:35 INFO mapreduce.Job:  map 94% reduce 0%
17/01/19 14:30:36 INFO mapreduce.Job:  map 100% reduce 0%
17/01/19 14:31:34 INFO mapreduce.Job: Job job_1472052053889_8081193 completed successfully
17/01/19 14:31:34 INFO mapreduce.Job: Counters: 30
        File System Counters
                FILE: Number of bytes read=0
                FILE: Number of bytes written=1501420
                FILE: Number of read operations=0
                FILE: Number of large read operations=0
                FILE: Number of write operations=0
                HDFS: Number of bytes read=12753350866
                HDFS: Number of bytes written=12753339159
                HDFS: Number of read operations=321
                HDFS: Number of large read operations=0
                HDFS: Number of write operations=69
        Job Counters
                Launched map tasks=17
                Other local map tasks=17
                Total time spent by all maps in occupied slots (ms)=485825
                Total time spent by all reduces in occupied slots (ms)=0
        Map-Reduce Framework
                Map input records=17
                Map output records=0
                Input split bytes=2414
                Spilled Records=0
                Failed Shuffles=0
                Merged Map outputs=0
                GC time elapsed (ms)=1634
                CPU time spent (ms)=156620
                Physical memory (bytes) snapshot=5716221952
                Virtual memory (bytes) snapshot=32341671936
                Total committed heap usage (bytes)=12159811584
        File Input Format Counters
                Bytes Read=9293
        File Output Format Counters
                Bytes Written=0
        org.apache.hadoop.tools.mapred.CopyMapper$Counter
                BYTESCOPIED=12753339159
                BYTESEXPECTED=12753339159
                COPY=17
```
是不是很熟悉，这就是我们经常看见到的 MapReduce 任务的输出信息，这从侧面说明了 Distcp 使用 Map/Reduce 实现。

## 3. 使用方法

### 3.1 集群间拷贝

DistCp最常用在集群之间的拷贝：
```
hadoop distcp hdfs://xxx1:8020/user/xiaosi/tmp/data_group/example hdfs://xxx2:8020/user/xiaosi/data_group
```
上述命令会将 xx1 集群 `tmp/data_group/example` 目录下的所有文件以及 `example` 目录本身拷贝到 xx2 集群 `data_group` 目录下。在集群 xx2 上查看一下文件:
```
sudo -uxiaosi hadoop fs -ls data_group/example
Found 1 items
-rw-r--r--   3 xiaosi xiaosi  32 2018-05-10 18:03 data_group/example/secondary.gz
```
这些文件内容的拷贝工作被分配给多个 map 任务。

> DistCp在集群间的拷贝时需要使用绝对路径进行操作。

#### 3.2 集群内部拷贝

DistCp也可以集群内部之间的拷贝：
```
hadoop distcp tmp/data_group/example/weather data_group
```
上述命令会把本集群 `tmp/data_group/example/weather` 目录下的所有文件以及 `weather` 目录本身拷贝到 `data_group` 目录下，原理同集群之间的拷贝一样。


> 备注
```
hadoop distcp tmp/data_group/test/weather tmp/data_group/example
```
上述命令默认情况下是复制 weather 目录下所有文件以及 weather 目录本身到 tmp/data_group/example 目录下。
```
hadoop fs -ls tmp/data_group/example/weather
Found 4 items
drwxr-xr-x   - xiaosi xiaosi    0 2018-05-14 19:52 tmp/data_group/example/weather/year=1945
drwxr-xr-x   - xiaosi xiaosi    0 2018-05-14 19:52 tmp/data_group/example/weather/year=2014
drwxr-xr-x   - xiaosi xiaosi    0 2018-05-14 19:52 tmp/data_group/example/weather/year=2015
drwxr-xr-x   - xiaosi xiaosi    0 2018-05-14 19:52 tmp/data_group/example/weather/year=2016
```
而有时我们的需求只是复制 weather 目录下的所有文件而不包含 weather 目录本身，这时可以使用后面介绍的 `-update` 参数：
```
hadoop distcp -update tmp/data_group/test/weather tmp/data_group/example
```

#### 3.3 多数据源目录拷贝

命令行中可以指定多个源数据目录：
```
hadoop distcp tmp/data_group/test/weather/year=2015 tmp/data_group/test/weather/year=2016 tmp/data_group/example/weather
```
上述命令会把本集群中的 `tmp/data_group/example/weather/year=2015` 以及 `tmp/data_group/test/weather/year=2016` 目录下的所有文件以及目录本身拷贝到 `data_group/example/weather` 目录下。
```
hadoop fs -ls tmp/data_group/example/weather/
Found 2 items
drwxr-xr-x   - xiaosi xiaosi  0 2018-05-14 20:12 tmp/data_group/example/weather/year=2015
drwxr-xr-x   - xiaosi xiaosi  0 2018-05-14 20:13 tmp/data_group/example/weather/year=2016
```
如果源数据文件较多，你也可以使用 `-f` 选项，从文件里获得多个源数据文件：
```
hadoop distcp -f tmp/data_group/test/src_list/src_list.txt tmp/data_group/example/weather
```
其中 `src_list.txt` 的内容是
```
hadoop fs -cat tmp/data_group/test/src_list/* | less
tmp/data_group/test/weather/year=2015
tmp/data_group/test/weather/year=2016
```

> 当从多个源数据文件拷贝时，如果两个源数据文件产生冲突，DistCp会停止拷贝并提示出错信息
Example：
```
hadoop distcp tmp/data_group/example/source_new/aa.txt tmp/data_group/example/source_old/aa.txt tmp/data_group/example/source
```
我们分别复制 source_new 和 source_old 目录下的 aa.txt 文件到 source 文件夹下，报错如下：
```
17/01/21 15:15:05 ERROR tools.DistCp: Duplicate files in input path:
org.apache.hadoop.tools.CopyListing$DuplicateFileException: File hdfs://XXX/user/XXX/tmp/data_group/example/source_new/aa.txt and \
hdfs://XXX/user/XXX/tmp/data_group/example/source_old/aa.txt would cause duplicates. Aborting
        at org.apache.hadoop.tools.CopyListing.checkForDuplicates(CopyListing.java:151)
        at org.apache.hadoop.tools.CopyListing.buildListing(CopyListing.java:87)
        at org.apache.hadoop.tools.GlobbedCopyListing.doBuildListing(GlobbedCopyListing.java:90)
        at org.apache.hadoop.tools.CopyListing.buildListing(CopyListing.java:80)
        at org.apache.hadoop.tools.DistCp.createInputFileListing(DistCp.java:327)
        at org.apache.hadoop.tools.wenjianDistCp.execute(DistCp.java:151)
```

每个 NodeManager 必须可以访问并与源文件系统和目标文件系统进行通信。对于 HDFS 来说，源文件系统和目标文件系统都必须运行相同版本协议或使用向后兼容的协议。

> 在两个不同版本的Hadoop之间（例如1.X和2.X之间）进行拷贝，通常会使用 `WebHdfsFileSystem`。与之前的 `HftpFileSystem` 不同，因为 `webhdfs` 可用于读取和写入操作，DistCp 可以在源和目标群集上运行。

> 远程集群指定为 `webhdfs://<namenode_hostname>:<http_port>`。当 webhdfs 使用 SSL 进行安全保护时，请使用 `swebhdfs：//`。在 Hadoop 集群的相同主要版本（例如2.X和2.X之间）之间进行拷贝时，使用 hdfs 协议来获得更好的性能。

拷贝完成后，建议生成源端和目的端文的列表，并交叉检查，来确认拷贝是否真正成功。因为 DistCp 使用 Map/Reduce 和文件系统API进行操作，如果它们之间有任何问题都会影响拷贝操作。

值得注意的是，当另一个客户端同时在向源文件写入时，拷贝很有可能会失败。尝试覆盖HDFS上正在被写入的文件的操作也会失败。如果一个源文件在拷贝之前被移动或删除了，拷贝失败同时输出异常 `FileNotFoundException`。

## 4. 更新与覆盖

`-update` 用于拷贝目标目录中不存在源目录或与目标目录中文件版本不同的文件。
`-overwrite` 覆盖目标目录上存在的目标文件。

更新和覆盖选项值得特别关注，因为它们的处理源路径与默认值的差异非常微妙。考虑来自　`/source/first/` 和 `/source/second/to/target/` 的副本，其中源路径具有以下内容：
```
hdfs://nn1:8020/foo/a
hdfs://nn1:8020/foo/a/aa
hdfs://nn1:8020/foo/a/ab
hdfs://nn1:8020/foo/b
hdfs://nn1:8020/foo/b/ba
hdfs://nn1:8020/foo/b/ab
```
如果没设置-update或 -overwrite选项， 那么两个源都会映射到目标端的 /bar/foo/ab。 如果设置了这两个选项，每个源目录的内容都会和目标目录的 内容 做比较。DistCp碰到这类冲突的情况会终止操作并退出。

默认情况下，/bar/foo/a 和 /bar/foo/b 目录都会被创建，所以并不会有冲突。

现在考虑一个使用-update合法的操作:
```
hadoop distcp -update tmp/data_group/test/source/ \
               tmp/data_group/test/target/
```
其中源路径/大小:
```
11 tmp/data_group/test/source/aa.txt
23 tmp/data_group/test/source/ab.txt
34 tmp/data_group/test/source/ba.txt
```
和目的路径/大小:
```
11 tmp/data_group/test/target/aa.txt
9  tmp/data_group/test/target/ba.txt
```
会产生:
```
11 tmp/data_group/test/target/aa.txt
23 tmp/data_group/test/target/ab.txt
34 tmp/data_group/test/target/ba.txt
```
只有target目录的aa.txt文件没有被覆盖。上面以及提到过，update不是"同步"操作。执行覆盖的唯一标准是源文件和目标文件大小是否相同；如果不同，则源文件替换目标文件。source中的aa.txt大小与target中的aa.txt大小一样，所以不会覆盖。

*==备注==*

实际测试的过程中，target目录下的aa.txt也会被覆盖，不得其解。求解......

如果指定了 -overwrite选项，所有文件都会被覆盖。

## 4. 选项

#### 4.1 -i 忽略失败
这个选项会比默认情况提供关于拷贝的更精确的统计， 同时它还将保留失败拷贝操作的日志，这些日志信息可以用于调试。最后，如果一个map失败了，但并没完成所有分块任务的尝试，这不会导致整个作业的失败。

#### 4.2 -log <logdir> 记录日志
DistCp为每个文件的每次尝试拷贝操作都记录日志，并把日志作为map的输出。 如果一个map失败了，当重新执行时这个日志不会被保留。

#### 4.3 -overwrite 覆盖目标
如果一个map失败并且没有使用-i选项，不仅仅那些拷贝失败的文件，这个分块任务中的所有文件都会被重新拷贝。 就像下面提到的，它会改变生成目标路径的语义，所以 用户要小心使用这个选项。

#### 4.4 -update 源和目标的大小不一样则进行覆盖
这不是"同步"操作。 执行覆盖的唯一标准是源文件和目标文件大小是否相同；如果不同，则源文件替换目标文件。 像 下面提到的，它也改变生成目标路径的语义， 用户使用要小心。



## 6. Map数目
DistCp会尝试着均分需要拷贝的内容，这样每个map拷贝差不多相等大小的内容。 但因为文件是最小的拷贝粒度，所以配置增加同时拷贝（如map）的数目不一定会增加实际同时拷贝的数目以及总吞吐量。

如果没使用-m选项，DistCp会尝试在调度工作时指定map的数目 为 min (total_bytes / bytes.per.map, 20 * num_task_trackers)， 其中bytes.per.map默认是256MB。

建议对于长时间运行或定期运行的作业，根据源和目标集群大小、拷贝数量大小以及带宽调整map的数目。

## 8. Map/Reduce和副效应
像前面提到的，map拷贝输入文件失败时，会带来一些副效应。

- 除非使用了-i，任务产生的日志会被新的尝试替换掉。
- 除非使用了-overwrite，文件被之前的map成功拷贝后当又一次执行拷贝时会被标记为 "被忽略"。
- 如果map失败了mapred.map.max.attempts次，剩下的map任务会被终止（除非使用了-i)。
- 如果mapred.speculative.execution被设置为 final和true，则拷贝的结果是未定义的。
