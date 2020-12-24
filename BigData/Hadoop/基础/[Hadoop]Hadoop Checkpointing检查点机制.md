
检查点(`Checkpointing`)是在`HDFS`中维护和保存文件系统元数据的重要组成部分。这对快速的恢复和重启`NameNode`是至关重要的，也是集群整体健康状况的重要指标。

在这篇文章中，将解释`HDFS`中检查点的用途，在不同集群配置下检查点工作原理的技术细节，然后介绍一系列关于此功能的操作问题和重要的bug修复。

### 1. HDFS中的文件系统元数据

我们首先介绍`NameNode`如何保存文件系统元数据。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/Hadoop%20Checkpointing%E6%A3%80%E6%9F%A5%E7%82%B9%E6%9C%BA%E5%88%B6-checkpointing1.png?raw=true)

在高层次上，`NameNode`的主要职责是存储`HDFS`的名称空间。它维护着像文件系统目录树，文件权限以及文件到块ID的映射。元数据(及其所有更改)安全地保存到稳定的存储中以实现容错是非常重要的。

文件系统元数据存储在两个不同的结构中：命名空间镜像`fsimage`和编辑日志`edit log`。`fsimage`是文件系统元数据的一个时间点的快照文件。但是，虽然`fsimage`文件格式的读取效率非常高，但并不适合进行小数据量的增量更新，例如重新命名单个文件等。因此，每次修改名称空间时，不是每次都写入`fsimage`，而是`NameNode`将修改操作永久记录在编辑日志中(NameNode instead records the modifying operation in the edit log for durability)。这样，如果`NameNode`发生故障崩溃，可以通过先把`fsimage`载入到内存重构新近的元数据，再执行编辑日志中记录的所有操作以赶上命名系统的最新状态来恢复其状态。编辑日志包含一系列称为编辑日志段的文件，它们共同表示自创建`fsimage`以来所做的所有命名系统修改。

### 2. 检查点为什么重要？

一个编辑范围从10s到100s内的字节(edit ranges from 10s to 100s of bytes)，但随着时间的推移，足够多的编辑日志累积起来可能会变得笨拙。大的编辑日志可能会产生一些问题。在极端情况下，它会占用节点上的所有可用磁盘空间，但更为重要的是，大的编辑日志会大大延迟`NameNode`的启动，因为`NameNode`将重新应用所有编辑日志。

备注:
```
编辑日志会无限增长，尽管这种情况对于NameNode的运行没有任何的影响，但是由于需要恢复(非常长的)编辑日志中的各项操作,NameNode的重启操作会比较慢。
```

检查点是一个进程，它需要一个`fsimage`和一个编辑日志，并将它们压缩成一个新的`fsimage`。这样，`NameNode`可以直接从`fsimage`加载最终的在内存中的状态，而不是重新执行一个可能是无穷大的编辑日志。这样是一个更有效的方式，并减少了`NameNode`的启动时间(译者注:定时将`fsimage`和编辑日志合并为一个新的`fsimage`，`NameNode`启动时加载最新的`fsimage`，而不是从编辑日志中加载)。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/Hadoop%20Checkpointing%E6%A3%80%E6%9F%A5%E7%82%B9%E6%9C%BA%E5%88%B6-checkpointing2.png?raw=true)

但是，创建一个新的`fsimage`是`I/O`和`CPU`密集型操作，有时需要几分钟才能完成。在检查点期间，命名系统还需要限制来自其他用户的并发访问。因此，不是暂停活动`NameNode`执行检查点，而是`HDFS`将其推迟到辅助`NameNode`或备用`NameNode`执行，这取决于是否配置了`NameNode`的高可用性。是否配置了`NameNode`的高可用性，检查点的机制也不同。我们将涵盖两个。

不管是哪种情况，检查点都由以下两个条件之一来触发：

(1) 如果自上一个检查点后已经过了足够时间(由`dfs.nameode.checkpoint.period`属性设置，以秒为单位)(译者注:创建检查点时间间隔)。通常情况下，辅助NameNode每隔一小时创建检查点。

(2) 是否有足够的新编辑日志累积到达阈值(由`dfs.nameode.checkpoint.txns`属性设置，以字节为单位)。默认情况下，当编辑日志达到64MB时，即使未到一小时也会创建检查点。

检查点节点定时(由`dfs.nameode.checkpoint.check.period`属性设置)检查是否满足上述任一条件，如果是，则启动检查点过程。

### 3. 使用备用NameNode进行Checkpointing

在处理`NodeNode`高可用配置时，检查点要简单得多，所以我们先来介绍一下这种情况。

在配置`NameNode`高可用性时，活动和备用`NameNode`可以共享存储编辑日志的存储(译者注:通过高可用的共享存储实现编辑日志的共享)。通常情况下，共享存储是三个或更多`JournalNodes`的ensemble(this shared storage is an ensemble of three or more JournalNodes)，但是这是从检查点过程中抽象出来的(that’s abstracted away from the checkpointing process)。

备用`NameNode`通过定期重新执行由活动`NameNode`写入到共享存储目录的新编辑日志来维护命名空间的当前最新版本。因此，检查点非常简单，检查之前定义的触发条件是否满足，保存命名空间到一个新的`fsimage`(大致相当于在命令行上运行`hdfs dfsadmin -saveNamespace`)，然后将新的`fsimage`通过HTTP传输到活动`NodeNode`。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/Hadoop%20Checkpointing%E6%A3%80%E6%9F%A5%E7%82%B9%E6%9C%BA%E5%88%B6-checkpointing3.png?raw=true)

在这里，`Standby` `NameNode`缩写为`SbNN`以及`Active NameNode`为`ANN`：

(1) `SbNN`检查是否满足这两个前提条件的任意一个：从上一个检查点开始经过的时间或累积的编辑日志的数量。

(2)

### 4. 使用辅助NameNode进行Checkpointing




























































原文:http://blog.cloudera.com/blog/2014/03/a-guide-to-checkpointing-in-hadoop/
