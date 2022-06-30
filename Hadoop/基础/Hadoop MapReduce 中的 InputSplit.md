---
layout: post
author: sjf0115
title: Hadoop MapReduce 中的 InputSplit
date: 2017-12-06 13:20:17
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-mapreduce-inputsplit
---

Hadoop 初学者经常会有这样两个问题：
- Hadoop 的一个 `Block` 默认是 128M(或者64M)，那么对于一条记录来说，会不会造成一条记录被分到两个 `Block` 中？
- 从 `Block` 中读取数据进行切分时，会不会造成一条记录被分到两个 `InputSplit` 中？

对于上面的两个问题，首先要明确两个概念：`Block` 和 `InputSplit`。在 Hadoop 中，文件由一个一个的记录组成，最终由 Mapper 任务一个一个的处理。例如，示例数据集包含有关 1987 至 2008 年间美国境内已完成航班的信息。如果要下载数据集可以打开如下网址： http://stat-computing.org/dataexpo/2009/the-data.html 。每一年都会生成一个大文件（例如：2008年文件大小为108M），在每个文件中每单独的一行都代表一次航班信息。换句话说，一行代表一个记录。`HDFS` 以固定大小的 `Block` 为基本单位存储数据，而对于 `MapReduce` 而言，其处理单位是 `InputSplit`。

### 1. Block

`Block` 是以 `block size` 进行划分数据。因此，如果集群的 `block size` 为 128MB，则数据集的每个 `Block` 将为 128MB，除非最后一个 `Block` 小于 `block size`（文件大小不能被 block size 完全整除）。例如下图中文件大小为 513 MB，513%128=1，最后一个 `Block`  `e` 小于 `block size`，大小为 1MB。因此，`Block` 是以 `block size` 进行切割，并且 `Block` 甚至在逻辑记录完全读取结束之前就结束了(该记录横跨两个 `Block` )。

假设我们的集群中 `block size` 是 128MB，每个逻辑记录大约 100MB（假设为巨大的记录）。所以第一个记录将完全在一个 `Block` 中，因为记录大小为 100 MB（小于 `Block` 大小 128 MB）。但是，第二个记录不能完全在一个 `Block` 中，第二条记录会出现在第一个和第二个 `Block` 中，第一个存储不下溢写到第二个 `Block` 中。

### 2. InputSplit

但是如果每个 `Map` 任务都处理特定数据块中的所有记录，那怎么处理这种跨越 `Block` 边界的记录呢？如果分配一个 `Mapper` 给 `Block` 1，在这种情况下，`Mapper` 不能处理第二条记录，因为 `Block` 1中没有完整的第二条记录。因为 `HDFS` 对文件 `Block` 内部并不清楚，它不知道一个记录会是不是溢出到另一个块。`InputSplit` 就是解决这种跨越 `Block` 边界记录问题的，Hadoop 使用逻辑表示存储在文件 `Block` 中的数据，称为输入拆分 `InputSplit`。`InputSplit` 是一个逻辑概念，并没有对实际文件进行切分，它只包含一些元数据信息，比如数据的起始位置，数据长度，数据所在的节点等。它的划分方法完全取决于用户自己。但是需要注意的是 `InputSplit` 的多少决定了 `MapTask` 的数目，因为每个 `InputSplit` 会交由一个 `MapTask` 处理。

当 `MapReduce` 作业客户端计算 `InputSplit` 时，它会计算出 `Block` 中第一个记录的开始位置和最后一个记录的结束位置。在最后一个记录不完整的情况下，`InputSplit` 包括下一个 `Block` 的位置信息以及该记录所需的字节偏移量。下图显示了 `Block` 和 `InputSplit` 之间的关系：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hadoop/hadoop-mapreduce-inputsplit-1.jpg?raw=true)

`Block` 是磁盘中的数据存储的物理块；`InputSplit` 不是物理数据块，只是一个逻辑概念，并没有对实际文件进行切分，指向块中的开始和结束位置。因此，当 `Mapper` 尝试读取数据时，它清楚地知道从何处开始读取以及在哪里停止读取。`InputSplit` 可以在一个块中开始，在另一个块中结束。`InputSplit` 代表了逻辑记录边界，在 `MapReduce` 执行期间，`Hadoop` 扫描块并创建 `InputSplits`，并且每个 `InputSplit` 将被分配给一个 `Mapper` 进行处理。

原文：http://www.dummies.com/programming/big-data/hadoop/input-splits-in-hadoops-mapreduce/
