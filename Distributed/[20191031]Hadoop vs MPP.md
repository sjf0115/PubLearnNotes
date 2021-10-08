---
layout: post
author: sjf0115
title: Hadoop vs MPP
date: 2019-10-31 15:43:13
tags:
  - Architecture

categories: Architecture
permalink: hadoop-vs-mpp
---

最近我听到了很多关于此话题的讨论。同样，这也是一个大数据领域经验不足的客户非常喜欢提问的问题。实际上，我不喜欢这个含糊不清的词语，但是通常客户会找到我们使用它们，因此我不得不使用。

如果回头看5年前(原文发表于2015年)，那时候大多数公司都不会选择 Hadoop，尤其是对于那些要求稳定和成熟平台的企业。因此那时选型非常简单：当你分析的数据库大小达到5-7TB时，我们只需要启动一个 MPP 迁移项目，迁移到一种成熟的企业 MPP 解决方案即可。那时没人听说过非结构化数据，如果我们要分析日志，需要使用 Perl/Python/Java/C++ 对其进行分析并加载到分析 DBMS 中即可。没有人听说过高速数据，简单的使用传统的 OLTP RDBMS 进行频繁的更新，然后将它们分块以插入到分析 DWH 中即可。

但是随着时间的流转，大数据开始火热起来，在大众媒体和社交网络中开始流行。这是大数据的 Google 趋势图：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Architecture/hadoop-vs-mpp-1.png?raw=true)

人们开始讨论 '3V' 以及处理这些海量数据的方法。Hadoop 已从专利技术发展成为用于数据处理的顶级工具，越来越多的公司投入到 Hadoop 中、给 Hadoop 供应商进行投资，或让自己成为 Hadoop 供应商。随着 Hadoop 越来越流行，MPP 数据库开始受到冷落。我们可以以 Teradata 股票为例，在过去三年中，它们一直在下跌，其主要原因是新的参与者瓜分了他们的市场，而这个参与者就是 Hadoop。

> 3V:Volume(规模性)、Varity(多样性)、Velocity(高速性)

因此，关于'我应该选择 MPP 解决方案还是基于 Hadoop 的解决方案？'的问题变得非常流行。许多供应商都将 Hadoop 定位为替代传统数据仓库，这意味着可以替代 MPP 解决方案。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Architecture/hadoop-vs-mpp-2.jpg?raw=true)

那么什么是 MPP？MPP 表示大规模并行处理，网格的所有独立节点都参与协调计算，这就是网格计算的方法。MPP DBMS 是基于此方法构建的数据库管理系统。在这些系统中，我们所关注的每个查询被分解为由 MPP 网格节点并行执行的一组协调处理，从而以比传统 SMP RDBMS 系统更快的速度运行计算。该体系结构为我们提供的另一个优势是可扩展性，因为我们可以通过在网格中添加新节点来轻松扩展网格。为了能够处理大量数据，这些数据通常按每个节点仅处理其本地数据的方式在节点之间拆分（分片）。这进一步加快了数据的处理速度，因为如果这种设计使用共享存储将会更复杂，成本更高，可扩展性更低，网络利用率更高，并行性更低。这就是为什么大多数 MPP DBMS 解决方案都是不共享的(shared-nothing)，并且不能在DAS存储或共享小型服务器组的一组存储机架上工作的原因。Teradata，Greenplum，Vertica，Netezza 以及其他类似解决方案都采用了这种方法。它们都具有专门为MPP解决方案开发的复杂成熟的SQL优化器。所有这些都可以通过内置语言和围绕这些解决方案的工具集进行扩展，无论是地理空间分析还是数据挖掘的全文搜索，这些工具集几乎都可以满足任何客户的需求。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Architecture/hadoop-vs-mpp-3.gif?raw=true)

Hadoop 不是一项单独的技术，而是一个生态系统，它有其自己的优点和缺点。最大的优点是可扩展性，出现了许多新组件（例如，Spark），并且它们与 Hadoop 的核心技术保持集成。缺点就是我们自己构建不同技术的平台是一项艰巨的工作，自己手动搭建成本比较高，大多数公司都在运行由 Cloudera 或 Hortonworks 提供的平台。

Hadoop 存储技术基于完全不同的方法。不再是基于某种主键来分片数据，而是将数据分为固定大小（可配置）的块，分布在不同节点之间。这些数据块以及整个文件系统（HDFS）都只是可读的。简单来说，将一个小的只有100行的表加载到 MPP 中，引擎会根据表的主键将数据分片，这样在一个足够大的集群中，每个节点仅存储一行记录的可能性会非常大。相反，在 HDFS 中整个小表都会被写入一个块中，在 DataNode 的文件系统上被表示为一个文件。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Architecture/hadoop-vs-mpp-4.jpg?raw=true)

接下来，集群资源如何管理？与 MPP 设计相比，Hadoop 资源管理器（YARN）为我们提供了更细粒度的资源管理，MapReduce 作业不需要并行运行所有计算任务。它还具有一系列不错的功能，例如可扩展性持等。但是实际上，它比 MPP 资源管理器要慢，有时在并发性管理方面也不那么好。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Architecture/hadoop-vs-mpp-5.jpg?raw=true)

接下来是 Hadoop 的 SQL 接口。在这里，我们有各种各样的工具：它可能是运行在 MR/Tez/Spark 上的 Hive，也可能是 SparkSQL，也可能是 Impala、HAWQ 或 IBM BigSQL。我们的选择非常多，很容易不知道如何选择。

第一个选择是 Hive，它是将 SQL 查询转换为 MR/Tez/Spark 作业并在集群上执行的一个引擎。所有作业均基于相同的 MapReduce 概念构建，并为我们提供了良好的集群利用率以及与其他 Hadoop 栈的良好集成。但是缺点也很大，执行查询的延迟大，性能差尤其是对于表联接时。下面这张图片涵盖了过时的 MR1 设计，但在我们的背景下并不重要：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Architecture/hadoop-vs-mpp-6.jpg?raw=true)

诸如 Impala 和 HAWQ 之类的解决方案则不同，它们是 Hadoop 之上的 MPP 执行引擎，可处理 HDFS 中存储的数据。与其他 MPP 引擎一样，它们可以为我们提供更低的延迟以及更少的查询处理时间，但代价是可扩展性以及稳定性较低。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Architecture/hadoop-vs-mpp-7.png?raw=true)

SparkSQL 介于 MapReduce 和 MPP-over-Hadoop 两者之间，试图吸收两者的优点，但也有其自身的缺点。与 MR 相似，它将 Job 分解为一组单独计划的任务，以提供更好的稳定性。与 MPP 一样，尝试在执行阶段之间流式传输数据以加快处理速度。但是它也结合了这些解决方案的缺点，速度不如 MPP，稳定和可扩展性不如 MapReduce。

下面详细看一下 MPP 与 Hadoop 的对比：

|     | MPP     | Hadoop     |
| --- | ---     | ---        |
| 平台开放性 | 专有，也有例外 | 完全开源 |
| 硬件 | 许多解决方案有特有设备，我们无法在自己的集群上部署软件。所有解决方案都需要特定的企业级硬件。| 任何硬件都可以使用，供应商提供了一些配置准则。大多数建议是将便宜的商品硬件与DAS结合使用 |
| 扩展性(节点) | 平均数十个节点，最大100-200 | 平均100个节点，最大数千个 |
| 扩展性(用户) | 平均数十TB，最大PB | 平均几百TB，最大数十PB |
| 查询延迟  |  10-20毫秒 | 10-20秒 |
| 查询平均运行时间 | 5-7秒 | 10-15分钟 |
| 查询最大运行时间 | 1-2小时 | 1-2周 |
| 查询优化 | 复杂的企业查询优化器引擎 | 没有优化器或优化器功能比较局限 |
| 查询调试与分析 | 有查询执行计划、查询执行统计信息以及解释性错误消息 | OOM问题和Java堆 dump 分析、集群GC暂停组件，每个任务的单独日志 |
| 技术价格 | 每个节点数十至数十万美元 | 免费或每个节点高达数千美元 |
| 访问友好性 | 简单友好的SQL接口和简单可解释的数据库内函数 | SQL并不完全符合ANSI，用户应注意执行逻辑，底层数据布局。函数通常需要用Java编写，编译并放在集群中 |
| 目标用户 | 业务分析师 | Java开发人员和经验丰富的DBA |
| 目标系统 | 通用DWH和分析系统 | 专用数据处理引擎 |
| 最小建议大小 | 任意 | GB |
| 最大并发 | 数十到数百个查询 | 最多10-20个作业 |
| 技术可扩展性 | 仅使用供应商提供的工具 | 与介绍的任何开源工具（Spark，Samza，Tachyon等）兼容 |
| 解决方案实施复杂度 | 中等 | 高 |

有了所有这些信息，我们就可以得出结论，为什么 Hadoop 不能完全替代传统企业数据仓库，而可以用作分布式处理大量数据并从数据中获得重要信息的引擎。Facebook 安装了300PB 规模的 Hadoop，但他们仍使用小型 50TB Vertica 集群，LinkedIn 拥有庞大的 Hadoop 集群，仍使用 Aster Data 集群。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[Hadoop vs MPP](https://0x0fff.com/hadoop-vs-mpp/)
