---
layout: post
author: sjf0115
title: Hadoop 提升MapReduce性能的七点建议
date: 2018-04-22 09:32:17
tags:
  - Hadoop
  - Hadoop 优化

categories: Hadoop
permalink: hadoop-7-tips-for-improving-mapreduce-performance
---
在这篇文章里，我会重点介绍一些提高 MapReduce 性能的技巧。前几个技巧是面向整个集群的，对于操作人员和开发人员都很有用。后面的技巧适用于使用Java编写 MapReduce 作业的开发人员。在每一个建议中，我列出一些 '症状' 或是 '诊断测试' 来说明一些针对这些问题的改进措施。

请注意，这些建议中包含基于我在各种不同场景下总结出来的经验。它们可能不适用于你特定工作负载，数据集或集群，如果你想使用它，需要测试使用前和使用后它在你的集群中的表现。我将在4个节点的集群上展示在40GB数据上运行 wordcount 作业的一些对比数字。优化调整后，此作业中的每个 map 任务运行时间约为33秒，总作业运行时间约为8分30秒。

### 1. 正确地配置你的集群
诊断结果/症状：
- Linux top命令的结果显示slave节点在所有map和reduce slot都有task运行时依然很空闲。
- top命令显示内核的进程，如RAID(mdX_raid*)或pdflush占去大量的CPU时间。
- Linux的平均负载通常是系统CPU数量的2倍。
- 即使系统正在运行job，Linux平均负载总是保持在系统CPU数量的一半的状态。
- 一些节点上的swap利用率超过几MB

优化你的MapReduce性能的第一步是确保你整个cluster的配置文件被调整过。对于新手，请参考这里关于配置参数的一篇blog：配置参数。 除了这些配置参数 ，在你想修改job参数以期提高性能时，你应该参照下我这里的一些你应该注意的项：
- 确保你正在DFS和MapReduce中使用的存储mount被设置了noatime选项。这项如果设置就不会启动对磁盘访问时间的记录，会显著提高IO的性能。
- 避免在TaskTracker和DataNode的机器上执行RAID和LVM操作，这通常会降低性能
- 在这两个参数mapred.local.dir和dfs.data.dir 配置的值应当是分布在各个磁盘上目录，这样可以充分利用节点的IO读写能力。运行 Linux sysstat包下的iostat -dx 5命令可以让每个磁盘都显示它的利用率。
- 你应该有一个聪明的监控系统来监控磁盘设备的健康状态。MapReduce job的设计是可容忍磁盘失败，但磁盘的异常会导致一些task重复执行而使性能下降。如果你发现在某个TaskTracker被很多job中列入黑名单，那么它就可能有问题。
- 使用像Ganglia这样的工具监控并绘出swap和网络的利用率图。如果你从监控的图看出机器正在使用swap内存，那么减少mapred.child.java.opts属性所表示的内存分配。
































原文：http://blog.cloudera.com/blog/2009/12/7-tips-for-improving-mapreduce-performance/
