

在这篇文章中，我们将介绍`Hadoop`中的磁盘均衡器，`HDFS`中的磁盘均衡器的操作，`HDFS`中的内部数据节点均衡器的必要性，以及磁盘均衡器在`HDFS`中的功能是什么。

`HDFS`提供了一个名为`Diskbalancer`的命令行工具。它以统一的方式在`DataNode`的所有磁盘上分发数据。

磁盘均衡器与`Balancer`不同，它可以分析数据块的位置并平衡`DataNode`间的数据。

由于以下原因，`HDFS`并不总是以统一的方式在磁盘上放置数据：
- 大量的写入和删除
- 磁盘更换

这可能会导致`DataNode`内的数据歪斜。这种情况不是由现有的`HDFS`磁盘均衡其处理的，它涉及到`Inter，Non-Intra，DN skew`。

这种情况由新的Intra-DataNode Balancing功能处理，该功能通过HDFS磁盘均衡器CLI调用。

`Hadoop`中的`HDFS`磁盘均衡器针对给定的数据节点工作，并将块从一个磁盘移动到另一个磁盘。

### 2. 磁盘均衡器操作

`Hadoop` `HDFS`磁盘均衡器通过创建一个计划(一组语句)并在`DataNode`上执行该计划。一个计划描述了两个磁盘之间应该移动多少数据。一个计划有很多步骤。移动步骤包括源磁盘移动，目标磁盘移动和一些字节移动。计划可以针对可操作的`DataNode`执行。

默认情况下，磁盘均衡器未启用。要启用磁盘均衡器，`dfs.disk.balancer.enabled`必须在`hdfs-site.xml`配置文件中设置为`true`。

### 3. HDFS Intra-DataNode Disk Balancer

当我们在HDFS中写入新块时，`DataNode`使用卷选择一个策略来为块选择磁盘。每个目录都是HDFS术语中的一个卷。有两个可选策略是：
- 循环法：它以统一的方式在可用磁盘上分配新块。
- 可用空间：将数据写入空余空间最多的磁盘(按百分比)。


























原文:
资料:https://www.iteblog.com/archives/1905.html

https://blog.cloudera.com/blog/2016/10/how-to-use-the-new-hdfs-intra-datanode-disk-balancer-in-apache-hadoop/
