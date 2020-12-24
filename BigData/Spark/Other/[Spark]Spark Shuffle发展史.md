---
layout: post
author: Dong
title: Spark Shuffle发展史
date: 2018-03-16 09:51:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-shuffle-history
---


对于大数据计算框架而言，Shuffle阶段的设计优劣是决定性能好坏的关键因素之一。本文将介绍目前Spark的shuffle实现，并将之与MapReduce进行简单对比。本文的介绍顺序是：shuffle基本概念，MapReduce Shuffle发展史以及Spark Shuffle发展史。

### 1. shuffle基本概念与常见实现方式

shuffle，是一个算子，表达的是多对多的依赖关系，在类MapReduce计算框架中，是连接Map阶段和Reduce阶段的纽带，即每个Reduce Task从每个Map Task产生数的据中读取一片数据，极限情况下可能触发M*R个数据拷贝通道（M是Map Task数目，R是Reduce Task数目）。通常shuffle分为两部分：Map阶段的数据准备和Reduce阶段的数据拷贝。首先，Map阶段需根据Reduce阶段的Task数量决定每个Map Task输出的数据分片数目，有多种方式存放这些数据分片：
- 保存在内存中或者磁盘上（Spark和MapReduce都存放在磁盘上）；
- 每个分片一个文件（现在Spark采用的方式，若干年前MapReduce采用的方式），或者所有分片放到一个数据文件中，外加一个索引文件记录每个分片在数据文件中的偏移量（现在MapReduce采用的方式）。

在Map端，不同的数据存放方式各有优缺点和适用场景。一般而言，shuffle在Map端的数据要存储到磁盘上，以防止容错触发重算带来的庞大开销（如果保存到Reduce端内存中，一旦Reduce Task挂掉了，所有Map Task需要重算）。但数据在磁盘上存放方式有多种可选方案，在MapReduce前期设计中，采用了现在Spark的方案（目前一直在改进），每个Map Task为每个Reduce Task产生一个文件，该文件只保存特定Reduce Task需处理的数据，这样会产生M*R个文件，如果M和R非常庞大，比如均为1000，则会产生100w个文件，产生和读取这些文件会产生大量的随机IO，效率非常低下。解决这个问题的一种直观方法是减少文件数目，常用的方法有：1) 将一个节点上所有Map产生的文件合并成一个大文件（MapReduce现在采用的方案），2) 每个节点产生 `{(slot数目)*R}` 个文件（Spark优化后的方案）。对后面这种方案简单解释一下：不管是MapReduce 1.0还是Spark，每个节点的资源会被抽象成若干个slot，由于一个Task占用一个slot，因此slot数目可看成是最多同时运行的Task数目。如果一个Job的Task数目非常多，限于slot数目有限，可能需要运行若干轮。这样，只需要由第一轮产生 `{(slot数目)*R}` 个文件，后续几轮产生的数据追加到这些文件末尾即可。因此，后一种方案可减少大作业产生的文件数目。

在Reduce端，各个Task会并发启动多个线程同时从多个Map Task端拉取数据。由于Reduce阶段的主要任务是对数据进行按组规约。也就是说，需要将数据分成若干组，以便以组为单位进行处理。大家知道，分组的方式非常多，常见的有：Map/HashTable（key相同的，放到同一个value list中）和Sort（按key进行排序，key相同的一组，经排序后会挨在一起），这两种方式各有优缺点，第一种复杂度低，效率高，但是需要将数据全部放到内存中，第二种方案复杂度高，但能够借助磁盘（外部排序）处理庞大的数据集。Spark前期采用了第一种方案，而在最新的版本中加入了第二种方案， MapReduce则从一开始就选用了基于sort的方案。

### 2. MapReduce Shuffle发展史

#### 2.1 阶段一

MapReduce Shuffle的发展也并不是一马平川的，刚开始（0.10.0版本之前）采用了“每个Map Task产生R个文件”的方案，前面提到，该方案会产生大量的随机读写IO，对于大数据处理而言，非常不利。

#### 2.2 阶段二

为了避免Map Task产生大量文件，[HADOOP-331](https://issues.apache.org/jira/browse/HADOOP-331) 尝试对该方案进行优化，优化方法：为每个Map Task提供一个环形buffer，一旦buffer满了后，则将内存数据spill到磁盘上（外加一个索引文件，保存每个partition的偏移量），最终合并产生的这些spill文件，同时创建一个索引文件，保存每个partition的偏移量。

这个阶段并没有对shuffle架构做调成，只是对shuffle的环形buffer进行了优化。在Hadoop 2.0版本之前，对MapReduce作业进行参数调优时，Map阶段的buffer调优非常复杂的，涉及到多个参数，这是由于buffer被切分成两部分使用：一部分保存索引（比如parition、key和value偏移量和长度），一部分保存实际的数据，这两段buffer均会影响spill文件数目，因此，需要根据数据特点对多个参数进行调优，非常繁琐。而 [MAPREDUCE-64](https://issues.apache.org/jira/browse/MAPREDUCE-64) 则解决了该问题，该方案让索引和数据共享一个环形缓冲区，不再将其分成两部分独立使用，这样只需设置一个参数控制spill频率。

#### 2.3 阶段三

目前shuffle被当做一个子阶段被嵌到Reduce阶段中的。由于MapReduce模型中，Map Task和Reduce Task可以同时运行，因此一个作业前期启动的Reduce Task将一直处于shuffle阶段，直到所有Map Task运行完成，而在这个过程中，Reduce Task占用着资源，但这部分资源利用率非常低，基本上只使用了IO资源。为了提高资源利用率，一种非常好的方法是将shuffle从Reduce阶段中独立处理，变成一个独立的阶段/服务，由专门的shuffler service负责数据拷贝，目前百度已经实现了该功能（准备开源？），且收益明显，具体参考： [MAPREDUCE-2354](https://issues.apache.org/jira/browse/MAPREDUCE-2354)。

### 3. Spark Shuffle发展史

目前看来，Spark Shuffle的发展史与MapReduce发展史非常类似。初期Spark在Map阶段采用了“每个Map Task产生R个文件”的方法，在Reduce阶段采用了map分组方法，但随Spark变得流行，用户逐渐发现这种方案在处理大数据时存在严重瓶颈问题，因此尝试对Spark进行优化和改进，相关链接有：External Sorting for Aggregator and CoGroupedRDDs，“Optimizing Shuffle Performance in Spark”，[Consolidating Shuffle Files in Spark](https://spark-project.atlassian.net/browse/SPARK-751)，优化动机和思路与MapReduce非常类似。

Spark在前期设计中过多依赖于内存，使得一些运行在MapReduce之上的大作业难以直接运行在Spark之上（可能遇到OOM问题）。目前Spark在处理大数据集方面尚不完善，用户需根据作业特点选择性的将一部分作业迁移到Spark上，而不是整体迁移。随着Spark的完善，很多内部关键模块的设计思路将变得与MapReduce升级版Tez非常类似。

### 4. 参考资料

[Spark源码分析 – Shuffle](http://www.cnblogs.com/fxjwind/p/3522219.html)

[详细探究Spark的shuffle实现](http://jerryshao.me/2014/01/04/spark-shuffle-detail-investigation/)


转载于：http://dongxicheng.org/framework-on-yarn/apache-spark-shuffle-details/
