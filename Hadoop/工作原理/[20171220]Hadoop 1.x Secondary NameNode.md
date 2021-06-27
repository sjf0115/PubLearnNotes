---
layout: post
author: sjf0115
title: Hadoop MapReduce 1.x Secondary NameNode
date: 2017-12-20 20:26:01
tags:
  - Hadoop
  - Hadoop 内部原理

categories: Hadoop
permalink: hadoop-mapReduce1.x-secondary-nameNode
---

`Secondary NameNode`是`Hadoop`中命名不当的其中一个组件。不当命名很容易造成歧义，通过`Secondary NameNode`这个名字，我们很容易理解为是一个备份`NameNode`，但实际上它不是。很多`Hadoop`的初学者对`Secondary NameNode`究竟做了什么以及为什么存在于`HDFS`中感到困惑。因此，在这篇博文中，我试图解释`HDFS`中`Secondary NameNode`的作用。

通过它的名字，你可能会认为它和`NameNode`有关，它确实是`NameNode`相关。所以在我们深入研究`Secondary NameNode`之前，让我们看看`NameNode`究竟做了什么。

### 1. NameNode

`NameNode`保存HDFS的元数据，如名称空间信息，块信息等。使用时，所有这些信息都存储在主存储器中。 但是这些信息也存储在磁盘中用于持久性存储。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/Hadoop%20Secondary%20NameNode%E7%9A%84%E4%BD%9C%E7%94%A8-1.png?raw=true)

上图显示了`NameNode`如何将信息存储在磁盘中。上图中两个不同的文件是：
- `fsimage` - 它是`NameNode`启动时文件系统元数据的快照
- 编辑日志 - 它是在`NameNode`启动之后对文件系统进行更改的序列

只有在重新启动`NameNode`时，编辑日志才会合并到`fsimage`以获取文件系统元数据的最新快照。但是在线上集群上，`NameNode`重启并不是很常见，这就意味对于`NameNode`长时间运行的集群来说编辑日志可能会变得非常大(可能会无限增长)。在这种情况下我们会遇到以下问题：
- 编辑日志变得非常大，对于管理来说是一个挑战
- `NameNode`重启需要很长时间，因为很多更改需要合并(译者注:需要恢复编辑日志中的各项操作，导致`NameNode`重启会比较慢)
- 在崩溃的情况下，我们将丢失大量的元数据，因为`fsimage`是比较旧的(译者注:生成最新`fsimage`之后的各项操作都保存在编辑日志中，而不是`fsimage`，还未合并)

所以为了解决这个问题，我们需要一个机制来帮助我们减少编辑日志的大小，并且得到一个最新的`fsimage`，这样`NameNode`上的负载就会降低一些。这与`Windows`恢复点非常相似，它可以让我们获得操作系统的快照，以便在出现问题时退回到上一个恢复点。

现在我们理解了`NameNode`的功能，以及保持最新元数据的挑战。所以这一切都与`Seconadary NameNode`有关？

### 2. Seconadary NameNode

通过`Secondary NameNode`实现编辑日志与`fsimage`的合来解决上述问题。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/Hadoop%20Secondary%20NameNode%E7%9A%84%E4%BD%9C%E7%94%A8-2.png?raw=true)

上图显示了`Secondary NameNode`的工作原理：

- 它定期从`NameNode`获取编辑日志，并与`fsimage`合并成新的`fsimage`
- 一旦生成新的`fsimage`，就会复制回`NameNode`
- `NameNode`下次重新启动时将使用这个`fsimage`进行重新启动，从而减少启动时间

`Secondary NameNode`的整个目的就是在`HDFS`中提供一个检查点。它只是`NameNode`的一个帮助节点。这也是它在社区内被认为是检查点节点的原因。

所以我们现在明白所有的`Secondary NameNode`都会在文件系统中设置一个检查点，这将有助于`NameNode`更好地运行。它不可以替换`NameNode`或也不是`NameNode`的备份。所以从现在开始习惯把它叫做检查点节点。


原文:http://blog.madhukaraphatak.com/secondary-namenode---what-it-really-do/
