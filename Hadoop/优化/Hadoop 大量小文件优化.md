---
layout: post
author: sjf0115
title: Hadoop 大量小文件优化
date: 2018-04-23 19:32:17
tags:
  - Hadoop
  - Hadoop 优化

categories: Hadoop
permalink: hadoop-small-files-problem
---

### 1. HDFS 上的小文件问题

小文件是指文件大小明显小于 HDFS 上块 Block 大小（默认 64MB，在 Hadoop2.x 中默认为 128MB）的文件。如果存储小文件，必定会有大量这样的小文件，否则你也不会使用 Hadoop，这样的文件给 Hadoop 的扩展性和性能带来严重问题。当一个文件的大小小于 HDFS 的块大小（默认64MB）就认定为小文件，否则就是大文件。为了检测输入文件的大小，可以浏览 Hadoop DFS 主页 http://machinename:50070/dfshealth.jsp ，并点击 `Browse filesystem`（浏览文件系统）。

首先，HDFS 中任何一个文件，目录或者数据块在 NameNode 节点内存中均以一个对象形式表示（元数据），而这受到 NameNode 物理内存容量的限制。每个元数据对象约占 150 byte，所以如果有1千万个小文件，每个文件占用一个块 Block，则 NameNode 大约需要 2G 空间。如果存储1亿个文件，则 NameNode 需要 20G 空间，这毫无疑问1亿个小文件是不可取的。

其次，处理小文件并非 Hadoop 的设计目标，HDFS 的设计目标是流式访问大数据集（TB级别）。因而，在 HDFS 中存储大量小文件是很低效的。访问大量小文件经常会导致大量的 seek，以及不断的在 DatanNde 间跳跃去检索小文件。这不是一个很有效的访问模式，严重影响性能。处理大量小文件速度远远小于处理同等大小的大文件的速度。每一个小文件要占用一个 slot，而任务启动将耗费大量时间甚至大部分时间都耗费在启动任务和释放任务上。

### 2. MapReduce上 的小文件问题

Map 任务一般一次只处理一个块的输入（input）（默认使用 FileInputFormat）。如果文件非常小并且有很多，那么每一个 Map 任务处理的输入数据都非常小，因此会产生大量的 Map 任务，每一个 Map 任务都会额外增加　bookkeeping 开销。一个 1GB 大小的文件拆分成 16 个 64M 大小的块，相对于拆分成 10000 个 100KB 的块，后者每一个小文件启动一个 Map 任务，作业的运行时间将会十倍甚至百倍慢于前者。

Hadoop 中有一些特性可以用来减轻 bookkeeping 开销：可以在一个 JVM 中允许 task JVM 重用，以支持在一个 JVM 中运行多个 Map 任务，以此来减少 JVM 的启动开销(译者注：MR1中通过设置 `mapred.job.reuse.jvm.num.tasks` 属性)。

### 3. 为什么会产生大量的小文件

至少在两种场景下会产生大量的小文件：
- 小文件是一个大逻辑文件的一部分。由于 HDFS 在 2.x 版本开始支持对文件进行追加，所以在此之前保存无边界文件（例如，日志文件）一种常用的方式就是将这些数据以块的形式写入 HDFS 中（译者注：持续产生的文件，例如日志每天都会生成）。
- 文件本身就是很小。设想一下，我们有一个很大的图片语料库，每一个图片都是一个单独的文件，并且没有一种很好的方法来将这些文件合并为一个大的文件。

### 4. 解决方案

这两种情况需要有不同的解决方式。

#### 4.1 第一种情况

对于第一种情况，文件是许多记录组成的，那么可以通过调用 HDFS 的 `sync()` 方法(和 `append` 方法结合使用)，每隔一定时间生成一个大文件。或者，可以通过写一个 MapReduce 程序来来合并这些小文件。

#### 4.2 第二种情况

对于第二种情况，就需要容器通过某种方式来对这些文件进行分组。Hadoop 提供了一些选择：

##### 4.2.1 HAR File

Hadoop Archives（HAR files）是在 0.18.0 版本中引入到 HDFS 中的，它的出现就是为了缓解大量小文件消耗 NameNode 内存的问题。HAR 文件是通过在 HDFS 上构建一个分层文件系统来工作。HAR 文件通过 `hadoop archive` 命令来创建，而这个命令实际上是运行 MapReduce 作业来将小文件打包成少量的 HDFS 文件（译者注：将小文件进行合并成几个大文件）。对于客户端来说，使用 HAR 文件系统没有任何的变化：所有原始文件都可见以及可以访问（只是使用 `har://URL`，而不是 `hdfs://URL`），但是在 HDFS 中中文件个数却减少了。

读取 HAR 文件不如读取 HDFS 文件更有效，并且实际上可能更慢，因为每个 HAR 文件访问需要读取两个索引文件以及还要读取数据文件本。

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-small-files-problem-1.png?raw=true)

尽管 HAR 文件可以用作 MapReduce 的输入，但是 Map 没有办法直接对共同驻留在 HDFS 块上的 HAR 所有文件操作。可以考虑通过创建一种 InputFormat，充分利用 HAR 文件的局部性优势，但是目前还没有这种 InputFormat。需要注意的是：MultiFileInputSplit，即使在 [HADOOP-4565](https://issues.apache.org/jira/browse/HADOOP-4565) 进行了改进，选择节点本地分割中的文件，但始终还是需要每个小文件的搜索。在目前看来，HAR 可能最好仅用于存储文档。

> Hadoop Archives 参考 [Hadoop 如何使用 Archives 实现归档](https://smartsi.blog.csdn.net/article/details/53889284) 博文

##### 4.2.2 SequenceFile

通常解决"小文件问题"的回应是：使用 SequenceFile。这种方法的思路是，使用文件名作为 key，文件内容作为 value，如下图。

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-small-files-problem-2.png?raw=true)

在实践中这种方式非常有效。我们回到 10,000 个 100KB 大小的小文件问题上，你可以编写一个程序将合并为一个 SequenceFile，然后你可以以流式方式处理（直接处理或使用 MapReduce） SequenceFile。这样会带来两个优势：
- SequenceFiles 是可拆分的，因此 MapReduce 可以将它们分成块，分别对每个块进行操作；
- 与 HAR 不同，它们支持压缩。在大多数情况下，块压缩是最好的选择，因为它直接对几个记录组成的块进行压缩，而不是对每一个记录进行压缩。

将现有数据转换为 SequenceFile 可能会很慢。但是，完全可以并行创建一个一个的 SequenceFile 文件。Stuart Sierra 写了一篇关于将 tar 文件转换为 SequenceFile 的[文章](https://stuartsierra.com/2008/04/24/a-million-little-files)，像这样的工具是非常有用的，我们应该多看看。向前看，最好设计好数据管道，如果可能的话，将源数据直接写入 SequenceFile，而不是作为中间步骤写入小文件。

与 HAR 文件不同，没有办法列出 SequenceFile 中的所有键，所以不能读取整个文件。Map File，类似于对键进行排序的 SequenceFile，维护部分索引，所以他们也不能列出所有的键，如下图。

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-small-files-problem-3.png?raw=true)

##### 4.2.3 HBase

如果你产生很多小文件，根据访问模式的不同，应该进行不同类型的存储。HBase 将数据存储在 Map Files（带索引的 SequenceFile）中，如果你需要随机访问来执行 MapReduce 流式分析，这是一个不错的选择。如果延迟是一个问题，那么还有很多其他选择 - 参见Richard Jones对键值存储的[调查](https://www.metabrew.com/article/anti-rdbms-a-list-of-distributed-key-value-stores)。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文：http://blog.cloudera.com/blog/2009/02/the-small-files-problem/
