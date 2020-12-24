---
layout: post
author: sjf0115
title: Hadoop 2.x HDFS架构
date: 2017-12-20 20:29:01
tags:
  - Hadoop
  - Hadoop 内部原理

categories: Hadoop
permalink: hadoop-2.x-hdfs-architecture
---

### 1. 概述

Hadoop分布式文件系统(`HDFS`)是一个分布式文件系统，设计初衷是可以在商用硬件上运行。它与现有的分布式文件系统有许多相似之处。但是，与其他分布式文件系统的也有显著的差异。`HDFS`具有高容错能力，可以部署在低成本的硬件上。`HDFS`提供对应用程序数据的高吞吐量访问，适用于具有大数据集的应用程序。`HDFS`放宽了一些POSIX要求，以便对文件系统数据进行流式访问。`HDFS`最初是作为`Apache Nutch`网络搜索引擎项目的基础架构构建的。`HDFS`是`Apache Hadoop Core`项目的一部分。项目URL为: http://hadoop.apache.org/

### 2. 设想与目标

#### 2.1 硬件故障

 硬件故障很常见不要感到意外。`HDFS`实例可能由成百上千台服务器机器组成，每台机器存储部分文件系统的数据。事实上，有大量的组件，并且每个组件具有不一定的故障概率，这意味着可能`HDFS`的某些组件总是不起作用的。因此，故障检测和快速自动恢复是`HDFS`的核心架构。

#### 2.2 流式数据访问

运行在`HDFS`上的应用程序需要流式访问其数据集。`HDFS`不是运行在通用文件系统上通用应用程序。`HDFS`设计是为了更多的批量处理，而不是与用户进行交互。重点是数据访问的高吞吐量，而不是数据访问的低延迟。

#### 2.3 大数据集

运行在`HDFS`上的应用程序具有较大的数据集。`HDFS`中的文件大小一般为几GB或几TB。因此，`HDFS`需要支持大文件。它需要提供高数据聚合带宽并可以在单个集群中扩展到的数百个节点。它需要在一个实例中支持数千万个文件。

#### 2.4 简单一致性模型

`HDFS`数据访问模式为一次写入多次读取。文件一旦创建、写入和关闭后，除了追加和截断外，文件不能更改。可以支持将内容追加到文件末尾，但不能在随意位置更新文件内容。该假设简化了数据一致性问题，并实现了数据访问的高吞吐量。`MapReduce`应用程序或Web爬虫程序应用程序与此模型完美匹配。

#### 2.5 '移动计算比移动数据便宜'

如果应用程序能够在其操作的数据附近执行，那么应用程序所请求的计算效率会更高一些。当数据集很大时，这一点更能体现。这样可以最大限度地减少网络拥塞并提高系统的整体吞吐量。我们假设将计算迁移到更靠近数据的位置比将数据转移到应用程序运行的位置更好。`HDFS`为应用程序提供接口，使其更靠近数据所在的位置。

#### 2.6 跨越异构硬件和软件平台的可移植性

`HDFS`被设计为可以从一个平台轻松地移植到另一个平台。这有助于`HDFS`作为大型应用程序的首选平台。

### 3. NameNode and DataNodes

`HDFS`是一个主/从结构。一个`HDFS`集群包含一个`NameNode`，管理文件系统命名空间以及管理客户端对文件访问的主服务。除此之外，还有一些`DataNode`，通常集群中的每个节点都有一个`DataNode`，用于管理它们所运行节点相关的存储。`HDFS`公开文件系统命名空间，并允许用户数据存储在文件中。在内部，一个文件被分成一个或多个数据块，这些数据块被存储在一组`DataNode`中。`NameNode`执行文件系统命名空间操作，例如打开，关闭和重命名文件和目录等。它也决定数据块到`DataNode`的映射。`DataNode`负责为文件系统客户端的读写请求提供服务。`DataNode`还根据来自`NameNode`的指令执行数据块的创建，删除和复制。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/Hadoop2.x%20HDFS%E6%9E%B6%E6%9E%84-1.png?raw=true)

`NameNode`和`DataNode`是设计用于在商业机器上运行的软件。这些机器通常运行GNU/Linux操作系统(OS)。`HDFS`是使用`Java`语言构建的; 任何支持`Java`的机器都可以运行`NameNode`或`DataNode`。使用高可移植性的`Java`语言意味着`HDFS`可以部署在各种机器上。一个典型的部署是有一台专用机器来运行`NameNode`。集群中的其他机器运行`DataNode`实例。该体系结构并不排除在同一台计算机上运行多个`DataNode`，但在实际部署中很少出现这种情况。

集群中`NameNode`的存在大大简化了系统的体系结构。`NameNode`是所有`HDFS`元数据的决策者和存储仓库。系统的这种设计方式可以允许用户数据不会经过`NameNode`，直接与`DataNode`进行连接。

### 4. 文件系统命名空间

`HDFS`支持传统的分层文件组织方式。用户或应用程序可以创建目录以及在这些目录内存储文件。文件系统命名空间层次结构与大多数其他文件系统类似；可以创建和删除文件，将文件从一个目录移动到另一个目录，或者重命名文件。`HDFS`支持用户配额和访问权限。`HDFS`不支持硬链接或软链接。但是，`HDFS`体系结构并不排除实现这些功能。

`NameNode`维护文件系统的命名空间。对文件系统命名空间或其属性的任何更改都会在`NameNode`中记录。应用程序可以指定`HDFS`应该维护的文件的副本数量。文件的副本数称为该文件的复制因子。这个信息由`NameNode`存储。

### 5. 数据复制

`HDFS`旨在大型集群多台机器上可靠地存储非常大的文件。将每个文件存储为一系列的数据块。文件的数据块被复制多份以实现容错。数据块大小和副本因子是可以通过配置文件进行配置。

一个文件的数据块除最后一个块以外的所有其他块的大小都相同，在添加对可变长度块和`hsync`的支持后，用户可以不用填充最后一个块到配置大小而启动一个新块。

应用程序可以指定文件的副本数量。复制因子可以在文件创建时指定，也可以在以后更改。`HDFS`中的文件是一次性编写的(追加和截断除外)，并且严格限定在任何时候都只能有一个编写者。

`NameNode`做出关于块复制的所有决定。它周期性的从集群中的每个`DataNode`接收`Heartbeat`和`Blockreport`。收到`Heartbeat`意味着`DataNode`运行正常。`Blockreport`包含`DataNode`上所有块的列表。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/Hadoop2.x%20HDFS%E6%9E%B6%E6%9E%84-2.png?raw=true)

#### 5.1 副本安置

副本的放置对`HDFS`的可靠性和性能至关重要。优化副本放置能将`HDFS`与大多数其他分布式文件系统区分开来。这是一个需要大量调整和体验的功能。机架感知副本放置策略的目的是提高数据可靠性，可用性和网络带宽利用率。副本放置策略的目前实现是朝这个方向迈进的第一步。实施这一策略的短期目标是在生产环境上进行验证，更多地了解其行为，并为测试和研究更复杂的策略奠定基础。

大型`HDFS`实例运行在通常分布在多个机架上的一组计算机上。不同机架中的两个节点之间的通信必须经过交换机。在大多数情况下，同一机架中的机器之间的网络带宽大于不同机架中的机器之间的网络带宽。

`NameNode`通过`Hadoop`机架感知中概述的过程确定每个`DataNode`所属的机架Id。一个简单但不是最佳的策略是将副本放在不同的机架上。这可以防止整个机架出现故障时丢失数据，并允许在读取数据时使用多个机架的带宽。此策略在集群中均匀分配副本，以便轻松平衡组件故障的负载(This policy evenly distributes replicas in the cluster which makes it easy to balance load on component failure)。但是，此策略会增加写入成本，因为写入需要将数据块传输到多个机架。

正常情况下，当复制因子为3时，`HDFS`的放置策略是将一个副本放在本地机架的同一个节点上，另一个放在本地机架的不同节点上，最后放在另一个机架的不同节点上。这个政策降低了机架间写入流量，这通常会提高写入性能。机架故障的几率远远小于节点故障的几率;此策略不会影响数据可靠性和可用性的保证。但是，它降低了读取数据时使用的总体网络带宽，因为数据块仅放置在两个不同的机架中，而不是三个。使用此策略，文件的副本不会均匀分布在机架上。三分之一的副本在同一个节点上，三分之二的副本在同一个机架上，另外三分之一在其它机架上均匀分布。此策略可提高写入性能，而不会影响数据可靠性或读取性能。

这里描述的就是当前默认副本放置策略。

#### 5.2 副本选择

为了尽量减少全局带宽消耗和读取延迟，`HDFS`会尝试将读取请求发送到离读取者最近的副本上(HDFS tries to satisfy a read request from a replica that is closest to the reader.)。 如果在与读取者节点相同的机架上存在副本，则该副本优选满足读取请求。如果`HDFS`进群跨越多个数据中心，则保存在本地数据中心的副本优先于任何远程副本。

#### 5.3 安全模式

在启动时，`NameNode`进入一个称为`Safemode`(安全模式)的特殊状态。当`NameNode`处于安全模式状态时，不会发生数据块的复制。`NameNode`接收来自`DataNode`的`Heartbeat`和`Blockreport`消息。`Blockreport`包含`DataNode`托管的数据块列表。每个块都有指定的最小数量的副本。当该数据块的最小副本数与`NameNode`签入时，将认为该块被安全地复制。在安全复制数据块的可配置百分比检入`NameNode`（再加上30秒）之后，`NameNode`退出安全模式状态。然后确定仍然少于指定副本数量的数据块列表（如果有的话）。`NameNode`然后将这些块复制到其他`DataNode`。

### 6. 文件系统元数据持久化

`HDFS`命名空间存储在`NameNode`中。`NameNode`使用称之为`EditLog`编辑日志的事务日志来持久化存储在文件系统元数据上发生的每一个变化。例如，在`HDFS`中创建一个新文件会导致`NameNode`向`EditLog`编辑日志中插入一条记录。同样，更改文件的复制因子也会导致将新记录插入到`EditLog`编辑日志中。`NameNode`使用其本地主机OS文件系统中的文件来存储`EditLog`编辑日志。整个文件系统命名空间，包括数据块到文件的映射以及文件系统属性，都存储在一个名为`FsImage`的文件中。`FsImage`作为文件存储在`NameNode`的本地文件系统中。

`NameNode`将整个文件系统命名空间和文件`Blockmap`的快照(image)保存在内存中。这个关键的元数据被设计得很紧凑，这样一个具有4GB内存的`NameNode`足以支持大量的文件和目录。当`NameNode`启动时，它会从磁盘中读取`FsImage`和`EditLog`编辑日志，将`EditLog`编辑日志中的所有事务应用到内存中的`FsImage`(applies all the transactions from the EditLog to the in-memory representation of the FsImage)，并将这个新版本刷新到磁盘上生成一个新`FsImage`。它可以截断旧的`EditLog`编辑日志，因为它的事务已经被应用到持久化的`FsImage`上。这个过程被称为检查点。在目前的实现中，只有在`NameNode`启动时才会出现检查点。在未来版本中正在进行工作的`NameNode`也会支持周期性的检查点。

`DataNode`将`HDFS`数据存储在本地文件系统的文件中。`DataNode`不了解`HDFS`文件(The DataNode has no knowledge about HDFS files)。它将每个`HDFS`数据块存储在本地文件系统中的单个文件中。`DataNode`不会在同一目录中创建所有文件。相反，它使用启发式来确定每个目录的最佳文件数量并适当地创建子目录。由于本地文件系统可能无法有效地支持单个目录中的大量文件，因此在同一目录中创建所有本地文件并不是最佳选择。当`DataNode`启动时，它会扫描其本地文件系统，生成一个包含所有`HDFS`数据块(与每个本地文件相对应)的列表，并将此报告发送给`NameNode`：这是`Blockreport`。

### 7. 通信协议

所有的`HDFS`通信协议都是基于`TCP/IP`协议的。客户端建立到`NameNode`机器上的可配置TCP端口的连接。它使用`ClientProtocol`与`NameNode`交谈。`DataNode`使用`DataNode`协议与`NameNode`进行通信。远程过程调用(RPC)抽象包装客户端协议和数据节点协议。根据设计，`NameNode`永远不会启动任何RPC。而是只响应由`DataNode`或客户端发出的RPC请求。

### 8. 稳定性

`HDFS`的主要目标是即使在出现故障时也能可靠地存储数据。三种常见的故障类型是`NameNode`故障，`DataNode`故障和网络分裂(network partitions)。

#### 8.1 数据磁盘故障，心跳和重新复制

每个`DataNode`定期向`NameNode`发送一个`Heartbeat`消息。网络分裂可能导致一组`DataNode`与`NameNode`失去联系。`NameNode`通过丢失`Heartbeat`消息来检测这种情况。`NameNode`将最近没有`Heartbeats`的`DataNode`标记为死亡，并且不会将任何新的IO请求转发给它们。任何注册在标记为死亡的`DataNode`中的数据不再可用。`DataNode`死亡可能导致某些块的复制因子降到其指定值以下。`NameNode`不断跟踪哪些块需要复制，并在需要时启动复制。重新复制可能由于许多原因而产生：`DataNode`可能变得不可用，副本可能被破坏，`DataNode`上的硬盘可能出现故障，或者文件的复制因子可能需要增加。

为了避免由于`DataNode`的状态震荡而导致的复制风暴，标记`DataNode`死亡的超时时间设置的比较保守(The time-out to mark DataNodes dead is conservatively long)(默认超过10分钟)。用户可以设置较短的时间间隔以将`DataNode`标记为陈旧，并避免陈旧节点在读取或按配置写入时性能出现负载(Users can set shorter interval to mark DataNodes as stale and avoid stale nodes on reading and/or writing by configuration for performance sensitive workloads)。

#### 8.2 集群重新平衡

`HDFS`体系结构与数据重新平衡方案兼容。如果某个`DataNode`上的可用空间低于某个阈值，那么会自动将数据从一个`DataNode`移动到另一个`DataNode`。对于特定文件突然高需求(sudden high demand)的情况下，可能会动态创建额外的副本并重新平衡集群中的其他数据。这些类型的数据重新平衡方案尚未实现。

#### 8.3 数据完整性

从`DataNode`上获取的数据块可能会损坏。发生损坏可能是由存储设备故障，网络故障或软件错误引起。`HDFS`客户端实现了对`HDFS`上文件内容进行校验和检查。当客户端创建一个`HDFS`文件时，它会计算每个文件的对应数据块的校验和，并将这些校验和存储在同一个`HDFS`命名空间中的单独隐藏文件中。当客户端检索文件内容时，它会验证从每个`DataNode`收到的数据是否与存储在相关校验和文件中的校验和相匹配。如果不匹配，那么客户端可以选择从另一个具有该数据块副本的`DataNode`中检索该数据块。

#### 8.4 元数据磁盘故障

`FsImage`和`EditLog`编辑日志是`HDFS`中的中心数据结构。这些文件的损坏可能会导致`HDFS`实例无法正常运行。为此，`NameNode`可以配置为支持维护`FsImage`和`EditLog`编辑日志的多个副本。任何对`FsImage`或`EditLog`编辑日志的更新都会引起每个`FsImages`和`EditLogs`编辑日志同步更新。同步更新`FsImage`和`EditLog`编辑日志的多个副本可能会降低`NameNode`支持的每秒的命名空间事务的速度(degrade the rate of namespace transactions per second)。但是，这种降低是可以接受的，因为尽管`HDFS`应用程序实质上是非常密集的数据，但是它们也不是元数据密集型的。当`NameNode`重新启动时，它会选择最新的一致的`FsImage`和`EditLog`编辑日志来使用。

另一个增强防御故障的方法是使用多个`NameNode`以启用高可用性，或者使用[`NFS`上的共享存储](http://hadoop.apache.org/docs/r2.7.3/hadoop-project-dist/hadoop-hdfs/HDFSHighAvailabilityWithNFS.html)或使用[分布式编辑日志](http://hadoop.apache.org/docs/r2.7.3/hadoop-project-dist/hadoop-hdfs/HDFSHighAvailabilityWithQJM.html)(称为`Journal`)。后者是推荐的方法。

#### 8.5 快照

[快照](http://hadoop.apache.org/docs/r2.7.3/hadoop-project-dist/hadoop-hdfs/HdfsSnapshots.html)支持在特定时刻存储数据副本。快照功能的一种用法是将损坏的`HDFS`实例回滚到先前已知的良好时间点。

### 9. 数据组织

#### 9.1 数据块

`HDFS`为支持大文件而设计的。与`HDFS`兼容的应用程序是处理大型数据集的应用程序。这些应用程序只写入数据一次，但是读取一次或多次，并读取速度要求满足流式处理速度。`HDFS`支持在文件上一次写入多次读取语义。`HDFS`使用的一般块大小为128 MB。因此，一个`HDFS`文件被分成多个128MB的块，如果可能的话，每个块将保存在不同的`DataNode`上。

#### 9.2 分阶段

客户端创建文件的请求不会立即到达`NameNode`。事实上，最初`HDFS`客户端将文件数据缓存到本地缓冲区。应用程序写入重定向到本地缓冲区。当本地文件累积超过一个块大小的数据时，客户端才会联系`NameNode`。`NameNode`将文件名插入到文件系统层次结构中，并为其分配一个数据块。`NameNode`将`DataNode`和目标数据块的标识和返回给客户请求。然后，客户端将本地缓冲区中的数据块保存到指定的`DataNode`上。当文件关闭时，本地缓冲区中剩余的未保存数据也被传输到`DataNode`。客户端然后告诉`NameNode`该文件已关闭。此时，`NameNode`将文件创建操作提交到持久化存储中。如果`NameNode`在文件关闭之前崩溃，那么文件会丢失。

在仔细考虑在`HDFS`上运行的目标应用程序之后，采用了上述方法。这些应用程序需要流式写入文件。如果客户端直接写入远程文件目录而没有在客户端进行任何缓冲，那么网络速度和网络拥塞会大大影响吞吐量。这种方法并非没有先例。较早的分布式文件系统，例如`AFS`，已经使用客户端缓存来提高性能。`POSIX`的要求已经放宽，以实现更高的数据传输性能。

### 9.3 副本流水线

当客户端将数据写入`HDFS`文件时，首先将数据写入本地缓冲区，如上一节所述。假设`HDFS`文件复制因子为3。当本地缓冲区累积了一个块的用户数据时，客户端从`NameNode`中检索`DataNode`列表。该列表包含保存数据的数据块副本的`DataNode`。客户端然后将数据块刷新到第一个`DataNode`。第一个`DataNode`开始接收一小部分数据，将这一小部分数据写入其本地存储库，然后传输到列表中的第二个`DataNode`。第二个`DataNode`依次接收数据块的每一部分数据，将其写入存储库，然后再将刷新到第三个`DataNode`。最后，第三个`DataNode`将数据写入其本地存储库。因此，`DataNode`可以以流水线的方式从前一个`DataNode`接收数据，同时将数据转发到流水线中的下一个`DataNode`。因此，数据从一个`DataNode`流到下一个。

### 10. 访问

应用程序可以以多种不同的方式访问`HDFS`。`HDFS`为应用程序提供了一个`FileSystem Java API`。`Java API`和`REST API`的C语言包装器也可以使用。另外还有一个HTTP浏览器(HTTP browser)，也可以用来浏览`HDFS`实例的文件。通过使用`NFS`网关，可以将`HDFS`作为客户端本地文件系统的一部分。

#### 10.1 FS Shell

`HDFS`将用户数据以文件和目录的形式进行组织。它提供了一个名为`FS shell`的命令行接口，让用户可以与`HDFS`中的数据进行交互。这个命令集的语法类似于用户已经熟悉的其他`shell`(例如`bash`，`csh`)。 以下是一些示例操作/命令对：

操作|命令
---|---
创建`/foodir`目录|`bin/hadoop dfs -mkdir /foodir`
删除目录`/foodir`|`bin/hadoop fs -rm -R /foodir`
查看`/foodir/myfile.txt`中内容|`bin/hadoop dfs -cat /foodir/myfile.txt`

`FS shell`针对需要脚本语言与存储数据进行交互的应用程序。

#### 10.2 DFSAdmin

`DFSAdmin`命令集用于管理`HDFS`集群。这些是仅能由`HDFS`管理员使用的命令。以下是一些示例操作/命令对：

操作|命令
---|---
使集群处于安全模式|`bin/hdfs dfsadmin -safemode enter`
生成`DataNode`列表|`bin/hdfs dfsadmin -report`
重新投放或停用`DataNode(s)`|`bin/hdfs dfsadmin -refreshNodes`

#### 10.3 浏览器接口

一个典型的`HDFS`安装会配置一个`Web`服务器，通过一个可配置的`TCP`端口公开`HDFS`命名空间。这允许用户使用Web浏览器浏览`HDFS`命名空间并查看其文件的内容。


备注:
```
Hadoop版本: 2.7.3
```

原文:http://hadoop.apache.org/docs/r2.7.3/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html
