---
layout: post
author: sjf0115
title: 分布式事务之两阶段提交(2PC)
date: 2018-09-14 20:16:01
tags:
  - 分布式

categories: 分布式
permalink: two-phase-commit-of-distributed-transaction
---

### 1. 概述

在计算机网络以及数据库领域内，二阶段提交（`Two-phase Commit`）是指，为了使基于分布式系统架构下的`所有节点在进行事务提交时保持一致性`而设计的一种算法。通常，二阶段提交也被称为是一种协议。在分布式系统中，虽然每个节点可以知道自己的操作是成功还是失败，但却无法知道其他节点的操作是成功还是失败。当一个事务跨越多个节点时，为了保持事务的ACID特性，需要引入一个作为协调者的组件来统一协调所有节点(称作参与者)的操作结果并最终指示这些节点是否要把操作结果进行真正的提交(比如将更新后的数据写入磁盘等等)。因此，二阶段提交的算法思路可以概括为： 参与者将操作成败通知协调者，再由协调者根据所有参与者的反馈情况决定各参与者是否要提交操作还是中止操作。

### 2. 前提

二阶段提交算法的成立基于以下假设：
- 分布式系统中，存在一个节点作为协调者，其他节点作为参与者。且节点之间可以进行网络通信。
- 所有节点都采用预写式日志，且日志被写入后即被保持在可靠的存储设备上，即使节点损坏也不会导致日志数据的消失。
- 所有节点不会永久性损坏，即使损坏后仍然可以恢复。

### 3. 两阶段提交

所谓的两个阶段是指：第一阶段的提交请求阶段(投票阶段)和第二阶段的提交阶段（完成阶段）。

#### 3.1 第一阶段：提交请求阶段

可以进一步将提交请求阶段分为以下三个步骤：
- 协调者节点向所有参与者节点询问是否可以执行提交操作，并开始等待各参与者节点的响应。
- 参与者节点执行询问发起为止的所有事务操作，并将Undo信息和Redo信息写入日志。
- 各参与者节点返回协调者节点发起询问的响应。如果参与者节点的事务操作实际执行成功，则它返回一个"同意"消息；如果参与者节点的事务操作实际执行失败，则它返回一个"中止"消息。

> 有时候，第一阶段也被称作投票阶段，即各参与者投票是否要继续接下来的提交操作。


#### 3.2 第二阶段：提交执行阶段

如果协调者从所有参与者节点获得的相应消息都为"同意"，则向所有参与者节点发出"正式提交"的请求，否则发出"回滚操作"的请求。参与者根据协调者的指令执行提交或者回滚操作，释放所有事务处理过程中使用的锁资源。

(1) 当协调者节点从所有参与者节点获得的相应消息都为"同意"时（成功）：
- 协调者节点向所有参与者节点发出"正式提交"的请求。
- 参与者节点正式完成操作，并释放在整个事务期间内占用的资源。
- 参与者节点向协调者节点发送"完成"消息。
- 协调者节点收到所有参与者节点反馈的"完成"消息后，完成事务。

![](img-two-phase-commit-of-distributed-transaction-1.png)

(2) 如果任一参与者节点在第一阶段返回的响应消息为"终止"，或者协调者节点在第一阶段的询问超时之前无法获取所有参与者节点的响应消息时（失败）：
- 协调者节点向所有参与者节点发出"回滚操作"的请求。
- 参与者节点利用之前写入的Undo信息执行回滚，并释放在整个事务期间内占用的资源。
- 参与者节点向协调者节点发送"回滚完成"消息。
- 协调者节点收到所有参与者节点反馈的"回滚完成"消息后，取消事务。

> 有时候，第二阶段也被称作完成阶段，因为无论结果怎样，协调者都必须在此阶段结束当前事务。


![](img-two-phase-commit-of-distributed-transaction-2.png)

### 4. 缺点

(1) 同步阻塞：两阶段提交的最大缺点就在于它的执行过程中间节点都处于阻塞状态。即节点之间在等待对方的相应消息时，它将什么也做不了。特别是，当一个节点在已经占有了某项资源的情况下，为了等待其他节点的响应消息而陷入阻塞状态时，当第三个节点尝试访问该节点占有的资源时，这个节点也将连带陷入阻塞状态。

(2) 超时机制：协调者节点指示参与者节点进行提交等操作时，如有参与者节点出现了崩溃等情况而导致协调者始终无法获取所有参与者的响应信息，这时协调者将只能依赖协调者自身的超时机制来处理。但往往超时机制处理时，协调者都会指示参与者进行回滚操作。这样的策略显得比较保守。

(3) 单点故障：由于协调者的重要性，一旦协调者发生故障。参与者会一直阻塞下去。尤其在第二阶段，协调者发生故障，那么所有的参与者都处于锁定事务资源的状态中，而无法继续完成事务操作。（如果是协调者挂掉，可以重新选举一个协调者，但是无法解决因为协调者宕机导致的参与者处于阻塞状态的问题）

(4) 数据不一致：在第二阶段中，当协调者向参与者发送提交请求之后，如果发生了局部网络异常或者在发送提交请求过程中协调者发生了故障，这会导致只有一部分参与者接受到了提交请求。而在这部分参与者接到提交请求之后就会执行提交操作。但是其他未接到提交请求的机器则无法执行事务提交。于是整个分布式系统便出现了数据不一致性的现象。

参考：
- [维基百科：二阶段提交](https://zh.wikipedia.org/wiki/%E4%BA%8C%E9%98%B6%E6%AE%B5%E6%8F%90%E4%BA%A4)
- [2PC 两阶段提交协议](https://blog.csdn.net/lezg_bkbj/article/details/52149863)
