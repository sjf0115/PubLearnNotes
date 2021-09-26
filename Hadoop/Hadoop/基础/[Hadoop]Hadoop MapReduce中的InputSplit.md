---
layout: post
author: sjf0115
title: Hadoop MapReduce中的InputSplit
date: 2017-12-06 13:20:17
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-mapreduce-inputsplit
---

Hadoop的初学者经常会有这样两个问题：
- Hadoop的一个`Block`默认是128M(或者64M)，那么对于一条记录来说，会不会造成一条记录被分到两个`Block`中？
- 从`Block`中读取数据进行切分时，会不会造成一条记录被分到两个`InputSplit`中？

对于上面的两个问题，首先要明确两个概念：`Block`和`InputSplit`。在Hadoop中，文件由一个一个的记录组成，最终由mapper任务一个一个的处理。
例如，示例数据集包含有关1987至2008年间美国境内已完成航班的信息。如果要下载数据集可以打开如下网址： http://stat-computing.org/dataexpo/2009/the-data.html 。每一年都会生成一个大文件（例如：2008年文件大小为108M），在每个文件中每单独的一行都代表一次航班信息。换句话说，一行代表一个记录。
`HDFS`以固定大小的`Block`为基本单位存储数据，而对于`MapReduce`而言，其处理单位是`InputSplit`。

### 1. Block

块是以`block size`进行划分数据。因此，如果集群的`block size`为128MB，则数据集的每个块将为128MB，除非最后一个块小于`block size`（文件大小不能被 block size 完全整除）。例如下图中文件大小为513MB，513%128=1，最后一个块`e`小于`block size`，大小为1MB。因此，块是以`block size`进行切割，并且块甚至可以在到逻辑记录结束之前结束(blocks can end even before a logical record ends)。

假设我们的集群中`block size`是128MB，每个逻辑记录大约100MB（假设为巨大的记录）。所以第一个记录将完全在一个块中，因为记录大小为100MB小于块大小128 MB。但是，第二个记录不能完全在一个块中，第二条记录将出现在两个块中，从块1开始，溢出到块2中。

### 2.InputSplit

但是如果每个`Map`任务都处理特定数据块中的所有记录，那怎么处理这种跨越块边界的记录呢？如果分配一个`Mapper`给块1，在这种情况下，`Mapper`不能处理第二条记录，因为块1中没有完整的第二条记录。因为`HDFS`对文件块内部并不清楚，它不知道一个记录会什么时候可能溢出到另一个块(because HDFS has no conception of what’s inside the file blocks, it can’t gauge when a record might spill over into another block)。`InputSplit`就是解决这种跨越块边界记录问题的，Hadoop使用逻辑表示存储在文件块中的数据，称为输入拆分`InputSplit`。`InputSplit`是一个逻辑概念，并没有对实际文件进行切分，它只包含一些元数据信息，比如数据的起始位置，数据长度，数据所在的节点等。它的划分方法完全取决于用户自己。但是需要注意的是`InputSplit`的多少决定了`MapTask`的数目，因为每个`InputSplit`会交由一个`MapTask`处理。

当`MapReduce`作业客户端计算`InputSplit`时，它会计算出块中第一个记录的开始位置和最后一个记录的结束位置。在最后一个记录不完整的情况下，`InputSplit`包括下一个块的位置信息和完成该记录所需的数据的字节偏移（In cases where the last record in a block is incomplete, the input split includes location information for the next block and the byte offset of the data needed to complete the record）。下图显示了数据块和InputSplit之间的关系：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/hadoop-mapreduce-inputsplit-1.jpg?raw=true)

块是磁盘中的数据存储的物理块，其中`InputSplit`不是物理数据块。它只是一个逻辑概念，并没有对实际文件进行切分，指向块中的开始和结束位置。因此，当`Mapper`尝试读取数据时，它清楚地知道从何处开始读取以及在哪里停止读取。`InputSplit`的开始位置可以在一个块中开始，在另一个块中结束。`InputSplit`代表了逻辑记录边界，在`MapReduce`执行期间，`Hadoop`扫描块并创建`InputSplits`，并且每个`InputSplit`将被分配给一个`Mapper`进行处理。


原文：http://www.dummies.com/programming/big-data/hadoop/input-splits-in-hadoops-mapreduce/
http://hadoopinrealworld.com/inputsplit-vs-block/

http://hadoopinrealworld.com/inputsplit-vs-block/
