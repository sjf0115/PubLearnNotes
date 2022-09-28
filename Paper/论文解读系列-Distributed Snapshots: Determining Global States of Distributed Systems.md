---
layout: post
author: smartsi
title: 论文解读系列-Distributed Snapshots: Determining Global States of Distributed Systems
date: 2022-02-14 18:04:00
tags:
  - 分布式系统

categories: 分布式系统
permalink: distributed-snapshots-determining-global-states-of-distributed-systems
---

本篇论文提出了一种算法，通过该算法，在分布式系统进程计算期间确定系统的全局状态。分布式系统中的许多问题都可以归纳为检测全局状态问题。例如，全局状态检测算法有助于解决一类重要的问题：稳定属性检测。稳定属性是持续存在的：一旦稳定属性变为真，此后会一直为真。稳定属性示例有 '计算终止'、'系统死锁'以及'令牌环中的所有令牌都已消失'。稳定属性检测问题是设计用来检测给定的稳定属性。全局状态检测也可用于 Checkpoint。


要点：系统整体状态包含进程的状态以及链路中消息的状态
难点：
- 链路中消息的状态不容易记录
- 进程时间不一定同步，无法同时记录状态
核心：每个进程记录与自己相关的状态并最终合并出全局状态
目标：
- 最终产生的快照必须保证一致性
- 快照过程不能影响系统的正常运行，更不能 Stop the world


https://www.bilibili.com/video/BV1Hq4y1X7X8/?spm_id_from=333.337.search-card.all.click&vd_source=0377bc317c7758835977a00d70e24d55
















原文:[Distributed Snapshots: Determining Global States of Distributed Systems]()
