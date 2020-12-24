

### 1. Replica

`DataNode`上下文中的副本拥有以下几种状态(请参阅`org.apache.hadoop.hdfs.server.common.HdfsServerConstants.java`中的`ReplicaState`枚举)：

#### 1.1 FINALIZED

当副本处于这种状态时，表示写数据到副本的操作已经完成，并且副本中的数据被`冻结`(副本数据长度固定不变了)，除非重新打开副本追加数据。所有具有相同生成标记(下面我们称之为`GS`)的`finalized`副本(一个块的)具有相同的数据。`finalized`副本的`GS`可能由于数据恢复而增加。

#### 1.2 RBW (Replica Being Written)

当副本处于这种状态时，表示正在往某些副本中写入数据，不管是创建文件写入数据还是重新打开文件追加数据。处于`RBW`状态的副本肯定是打开文件的最后一个块。数据仍在写入副本，但尚未完成。 阅读器客户端可以看到RBW副本的数据（不一定是全部）。 如果发生任何故障，将尝试保存RBW副本中的数据。

#### 1.3 RWR (Replica Waiting to be Recovered)

如果`DataNode`崩溃并重新启动，那么其所有`RBW`状态副本都将更改为`RWR`状态。一个`RWR`副本要么变得过时因此被丢弃，要么加入租约恢复中。

#### 1.4 RUR (Replica Under Recovery)

一个非`TEMPORARY`副本在加入租约恢复时将更改为`RUR`状态。

#### 1.5 TEMPORARY

为了块复制创建临时副本(通过副本监视器或进群平衡器创建)。它类似于一个`RBW`状态副本，只是它的数据对所有读者客户端是不可见的。如果块复制失败，`TEMPORARY`状态副本被删除。

### 2. Block

`NameNode`上下文中的`Block`拥有以下几种状态(请参阅`org.apache.hadoop.hdfs.server.common.HdfsServerConstants.java`中的`BlockUCState`)：

#### 2.1 UNDER_CONSTRUCTION

当块处于这种状态时，表示正在写入数据。`UNDER_CONSTRUCTION`状态块是打开文件的最后一个块；它的长度和生成标记仍然是可变的，它的数据(没有必要是全部的数据)对读者是可见的。`NameNode`中的`UNDER_CONSTRUCTION`状态块会跟踪写入管道(有效的`RBW`副本的位置)以及`RWR`副本的位置。

#### 2.2 UNDER_RECOVERY

如果当对应的客户端的租约过期时，文件的最后一个块正处于`UNDER_CONSTRUCTION`状态，然后当块开始恢复时块转换为`UNDER_RECOVERY`状态。

#### 2.3 COMMITTED

`COMMITTED`表示块的数据和生成标记不再可变(除非重新打开进行追加数据)，there are fewer than the minimal-replication number of DataNodes that have reported FINALIZED replicas of same GS/length。为了服务读取请求，`COMMITTED`块必须跟踪`RBW`副本的位置，`GS`以及`FINALIZED`副本的长度。当客户端要求`NameNode`添加一个新块到文件或者关闭文件时，`UNDER_CONSTRUCTION`块更改为`COMMITTED`。如果最后或倒数第二个块处于`COMMITTED`状态，则不能关闭文件，客户端必须重试。

#### 2.4 COMPLETE





参考:http://blog.cloudera.com/blog/2015/02/understanding-hdfs-recovery-processes-part-1/
