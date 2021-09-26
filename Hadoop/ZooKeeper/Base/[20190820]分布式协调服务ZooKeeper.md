---
layout: post
author: sjf0115
title: 分布式协调服务ZooKeeper
date: 2019-08-24 11:19:27
tags:
  - ZooKeeper

categories: ZooKeeper
permalink: a-distributed-coordination-service-for-distributed-applications-of-zookeeper
---

ZooKeeper 是一种用于分布式应用程序的分布式开源协调服务。它开放了一组简单的原语，分布式应用程序可以根据这些原语构建，以实现更高级的服务，例如，同步、配置维护、分组以及命名。设计上易于编程，使用类似文件系统目录树结构的数据模型。

众所周知，协调服务很难实现。特别容易出现竞争条件和死锁等错误。ZooKeeper 背后的动机是减轻分布式应用程序从头开始实现协调服务的难度。

### 2. 设计目标

#### 2.1 简单

`ZooKeeper` 允许分布式进程通过共享的分层命名空间相互协调，这种命名空间的组织方式与标准文件系统类似。命名空间由数据注册节点组成 - 在 `ZooKeeper` 称为 `znodes`  - 与文件和目录类似。与传统文件系统专为存储设计不同，`ZooKeeper` 数据保存在内存中，这意味着 `ZooKeeper` 可以实现高吞吐量和低延迟。

`ZooKeeper` 实现非常重视高性能、高可用性以及严格有序的访问。`ZooKeeper` 的性能特性意味着它可以在大型分布式系统中使用。可靠性特性使其不会有单点故障问题。严格有序意味着可以在客户端实现复杂的同步原语。

#### 2.2 副本

与它协调的分布式进程一样，`ZooKeeper` 本身也可以在一组主机上进行复制，称之为集成。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/a-distributed-coordination-service-for-distributed-applications-of-zookeeper-1.jpg?raw=true)

组成 `ZooKeeper` 服务的服务器必须彼此之间能够了解。它们维护状态内存镜像，事务日志以及持久化存储中的快照。只要大多数服务器可用，`ZooKeeper` 服务就可用。

客户端连接一个 `ZooKeeper` 服务器。客户端维护TCP连接，通过该连接发送请求，获取响应，获取监视事件以及发送心跳。如果与服务器的TCP连接中断，则客户端将连接到其他服务器。

#### 2.3 有序

`Zookeeper` 给每一次更新操作都赋予一个编号，这样可以反应 `Zookeeper` 事务发生顺序。后续操作可以使用该顺序来实现更高级别的抽象，例如同步原语。

#### 2.4 快速

`ZooKeeper` 在 '读取占主导' 工作负载中特别快。`ZooKeeper` 应用程序在数千台机器上运行，并且在读取比写入更多的情况下，特别是比率大约在 10：1 时是性能最好。

### 3. 分层空间数据模型

`ZooKeeper` 的命名空间非常类似于标准文件系统。名称是由斜杠 `/` 分隔的路径元素序列。`ZooKeeper` 命名空间中的每个节点都由路径标识。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/a-distributed-coordination-service-for-distributed-applications-of-zookeeper-2.jpg?raw=true)

### 4. 节点与临时节点

与标准文件系统不同，`ZooKeeper` 命名空间中的每个节点都可以包含与之关联的数据以及子节点。在 `ZooKeeper` 中文件也是目录（`ZooKeeper` 目的是存储协调数据：状态信息，配置，位置信息等，因此存储在每个节点的数据通常比较小，在字节到千字节之间。）我们使用 `ZNode` 来表示 `ZooKeeper` 数据节点。

`ZNodes` 维护一个 stat 结构，其中包括数据更改，ACL更改和时间戳的版本号，以允许缓存验证和协调更新。每当 `ZNode` 数据发生变化时，都会增加版本号。例如，每当客户端检索数据时，它也接收数据的版本号。

存储在命名空间中每个 `ZNode` 的数据以原子方式读取和写入。读取时获得 `ZNode` 所有关联的数据字节，写入时替换所有的数据。每个节点都有一个访问控制列表（ACL），可以限制谁能访问。

`ZooKeeper` 也有临时节点的概念。只要创建 `ZNode` 的会话处于活跃状态，`ZNode` 就会存在。会话结束时，`ZNode` 会被删除。当你想要实现 `[tbd]` 时，临时节点会很有用。

### 5. 条件更新与Watch

`ZooKeeper` 支持 `Watch` 的概念。客户端可以在 `ZNode` 上设置 `Watch`。当 `ZNode` 发生变化时，会触发并删除 `Watch`。`Watch` 被触发时，客户端会收到一个数据包，周知 `ZNode` 已发生变化。如果客户端与其中一个 `ZooKeeper` 服务器之间的连接断开，客户端会收到一个本地通知。

### 6. 保证

`ZooKeeper` 非常快速而且非常简单。但是，由于其目标是构建更复杂服务（如同步）的基础，因此必须提供一系列保证：
- 顺序一致性 - 客户端的更新会按他们发送的顺序执行。
- 原子性 - 要么全部更新成功，要么全部更新失败。没有部分成功或失败。
- 同一系统镜像 - 客户端无论连接到哪个服务器，都会看到相同的服务视图。
- 可靠性 - 一旦执行了变更，将会从那时起一直保持不变直到客户端覆盖更新。
- 及时性 - 系统的客户端视图保证在一定时间范围内是最新的。
有关这些以及如何使用它们的更多信息，请参阅[tbd]

### 7. 简单API

`ZooKeeper` 的设计目标之一是提供一个非常简单的编程接口。因此，它仅支持以下操作：
- create: 在树中指定位置创建节点
- delete: 删除节点
- exists: 判断指定位置的节点是否存在
- get data: 从一个节点读取数据
- set data: 将数据写到节点
- get children: 获取一个节点的所有子节点
- sync: 等待数据传输

### 8. 实现

`ZooKeeper Components` 展示了 `ZooKeeper` 服务的高层次组件。除请 `Request Processor` 外，构成 `ZooKeeper` 服务的每个服务器都会对自己的每个组件构建副本。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/a-distributed-coordination-service-for-distributed-applications-of-zookeeper-3.jpg?raw=true)

### 9. 使用

`ZooKeeper` 的编程接口虽然比较简单，但是使用它，你可以实现更高阶的操作，例如同步原语，组成员身份，所有权等。某些分布式应用程序已在应用。


原文:[ZooKeeper: A Distributed Coordination Service for Distributed Applications](http://zookeeper.apache.org/doc/current/zookeeperOver.html)
