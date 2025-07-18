---
layout: post
author: sjf0115
title: Hadoop MapReduce 新一代架构 MRv2
date: 2017-12-08 13:49:01
tags:
  - Hadoop
  - Hadoop 内部原理

categories: Hadoop
permalink: hadoop-mapReduce-new-generation-architecture-mrv2
---

`MapReduce`在`hadoop-0.23`中经历了彻底的改变，现在我们称之为`MapReduce 2.0`(MRv2)或者`YARN`。

`MRv2`的基本思想是将`JobTracker`的两个主要功能，资源管理和作业调度/监视的功能拆分为独立的守护进程。设计思想是将`MRv1`中的`JobTracker`拆分成了两个独立的服务：一个全局的资源管理器`ResourceManager`(`RM`)和每个应用程序特有的`ApplicationMaster`(`AM`)。每个应用程序要么是单个作业，要么是`DAG`作业。

![](img-hadoop-mapreduce-yarn-architecture-mrv2-1.gif)

### 1. ResourceManager

`ResourceManager`(`RM`)和每个从节点以及`NodeManager`(`NM`)构成了数据计算框架。`ResourceManager` 是系统中所有应用程序资源分配的最终决策者。

`ResourceManager`有两个主要组件:`Scheduler`(调度器) 和 `ApplicationsManager`。

#### 1.1 Scheduler

`Scheduler` 根据容量，队列等限制条件将资源分配给各种正在运行的应用程序。`Scheduler`是'纯调度器'，因为它负责监视或跟踪应用程序的状态。此外，它也不保证会重启由于应用程序错误或硬件故障原因导致失败的任务。`Scheduler`仅根据应用程序的资源请求来执行调度。它基于'资源容器'(Resource Container)这一抽象概念来实现的，资源容器包括如内存，cpu，磁盘，网络等。

`Scheduler`是一个可插拔的组件，它负责将集群资源分配给不同队列和应用程序。目前`Scheduler`支持诸如`CapacityScheduler`和`FairScheduler`。`CapacityScheduler`支持分层队列，以便更可预测地共享群集资源

#### 1.2 ApplicationsManager

`ApplicationsManager`(`ASM`)主要负责接受作业提交，协商获取第一个容器来执行应用程序的`ApplicationMaster`，并提供在故障时重新启动`ApplicationMaster`的服务。

### 2. NodeManager

`NodeManager`是每个节点上框架代理，主要负责启动应用所需要的容器，监视它们的资源使用情况(cpu，内存，磁盘，网络)，并将其报告给`ResourceManager`的`Scheduler`。

### 3. ApplicationMaster

事实上，每一个应用程序的`ApplicationMaster`是一个框架库，负责与`Scheduler`协商合适的资源容器以及与`NodeManager`一起跟踪他们的状态并监视进度。

`MRV2`保持与以前稳定版本(hadoop-1.x)API的兼容性。这意味着所有的`Map-Reduce`作业仍然可以在`MRv2`上运行，只需重新编译即可。


原文:http://hadoop.apache.org/docs/r2.4.1/hadoop-yarn/hadoop-yarn-site/YARN.html
