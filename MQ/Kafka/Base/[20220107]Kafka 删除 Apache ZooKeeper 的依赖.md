---
layout: post
author: smartsi
title: Kafka 删除 Apache ZooKeeper 的依赖
date: 2022-01-07 22:11:01
tags:
  - Kafka

categories: Kafka
permalink: removing-zookeeper-dependency-in-kafka
---

目前，Apache Kafka 使用 Apache ZooKeeper 来存储元数据，分区位置和主题配置之类的数据存储在 Kafka 之外一个单独的 ZooKeeper 集群中。2019 年，为了打破这种依赖关系并将元数据管理交由 Kafka，为此引入这个[KIP-500 计划](https://cwiki.apache.org/confluence/display/KAFKA/KIP-500%3A+Replace+ZooKeeper+with+a+Self-Managed+Metadata+Quorum)[1]。

那么 ZooKeeper 有什么问题吗？其实，问题不在于 ZooKeeper，而在于外部元数据管理的理念。

拥有两个系统会导致大量的重复。毕竟，Kafka 是一个分布式日志系统，在此之上提供了发布-订阅 API。ZooKeeper 也是一个分布式日志系统，在此之上提供了文件系统 API。这两个系统都有自己的网络通信、安全、监控和配置方法。同时使用这两个系统会给开发人员操作的复杂性增加一倍，这增加了不必要的学习成本，并增加了错误配置导致安全漏洞的风险。

在外部存储元数据并不是一种很有效的方式。我们至少需要运行三个额外的 Java 进程，有时可能更多。事实上，我们会经常看到 Kafka 集群的 ZooKeeper 节点与 Kafka 节点一样多！另外 ZooKeeper 中的数据也会反映到 Kafka 控制器上，会导致双重缓存。更糟糕的是，在外部存储元数据限制了 Kafka 的可扩展性。当 Kafka 集群启动，或者选举新的控制器时，控制器必须从 ZooKeeper 上加载集群的完整状态。随着元数据量的增加，加载过程也会变的更长。这限制了 Kafka 可以存储的分区数量。最后，在外部存储元数据可能会造成控制器内存状态与外部状态的不同步。

## 1. KIP-500

### 1.1 处理元数据

在 KIP-500 提出了一种在 Kafka 中处理元数据的更好方法。我们可以将其称为 'Kafka on Kafka'，因为 Kafka 将元数据存储在 Kafka 自己本身中，而不是存储在 ZooKeeper 等外部系统中。使用 KIP-500 提出的方法，元数据存储在 Kafka 分区中，而不是存储在 ZooKeeper 中。控制器将成为该分区的 Leader。不需要外部元数据系统来配置和管理元数据，只需要 Kafka 本身即可。我们会将元数据视为日志。Brokers 如果需要最新更新的元数据，只需要读取日志的末尾即可。这类似于只需要最新日志的消费者仅需要读取最后的日志而不用读取全部日志。Brokers 还可以在进程重新启动时持久化元数据缓存。

### 1.2 控制器架构

Kafka 集群选择一个控制器节点来管理分区 Leader 和集群元数据。我们拥有的分区和元数据越多，控制器的可扩展性就变得越重要。我们希望尽量减少操作次数，所需要的时间与主题和分区数量成线性关系。控制器 Failover 就是这样的一种操作。目前，当 Kafka 选择一个新的控制器时，需要加载之前处理的全部集群状态。随着集群元数据量的增长，这个过程需要的时间就越长。

相比之下，使用 KIP-500 提出的方法，会准备好几个备用控制器可以在活跃控制器挂掉时接管。这些备用控制器只是元数据分区 Raft 仲裁中的其他节点。这种设计确保我们在选择新控制器时不需要花费很长时间来加载。KIP-500 会加快主题的创建和删除。目前，当创建或删除主题时，控制器必须从 ZooKeeper 中重新加载集群中所有主题的完整列表。这样做是有必要的，因为当集群中的主题发生变化时，ZooKeeper 会通知我们，但它并没有告诉我们添加或删除了哪些主题。相比之下，在使用 KIP-500 提出的方法中创建或删除主题只会在元数据分区中创建一个新条目，这是一个 O(1) 的操作。

元数据的扩展性是未来扩展 Kafka 的关键部分。我们预计单个 Kafka 集群最终能够支持一百万个或更多的分区。

## 2. Roadmap

### 2.1 从 Kafka 管理工具中删除 ZooKeeper

Kafka 的一些管理工具（作为 Kafka 发行版本中一部分）仍然允许与 ZooKeeper 直接通信。更糟糕的是，仍然有一两个操作必须经过 ZooKeeper 这种直接通信才能完成。我们一直在努力缩小这些差距。在不久之后，之前需要直接访问 ZooKeeper 的每个操作都会提供一个公共的 Kafka API。我们还将在 Kafka 的下一个主版本中禁用或删除不必要的 --zookeeper 标志。

### 2.2 自我管理的元数据仲裁

在 KIP-500 提出的方法中，Kafka 控制器将元数据存储在 Kafka 分区，而不是存储在 ZooKeeper 中。但是，因为控制器依赖于这个分区，所以分区本身不能再依赖控制器来进行领导者选举这种事情。取而代之的方法是管理这个分区的节点必须实现自我管理的 Raft 仲裁。

在 [KIP-595：元数据仲裁的 Raft 协议](https://cwiki.apache.org/confluence/x/Li7cC) [2]中讲述了如何将 Raft 协议适配到 Kafka 中，使其真正与 Kafka 融合来更好的工作。这涉及将 Raft [论文](https://raft.github.io/raft.pdf) [3]中描述的基于推送的模型更改为基于拉取的模型，这与传统的 Kafka 复制是一致的。其他节点将连接到这些节点，而不是将数据推送到其他节点。同样，我们保持与 Kafka 一致的术语 epochs 而不是使用原始 Raft 论文中的 terms 等等。

最初的实现侧重于支持元数据分区。不支持将常规分区转换为 Raft 所需的全部操作。但是，这是我们将来可能会谈到的话题。

### 2.3 KIP-500 模式

当然，这个项目最令人兴奋的部分是能够以 KIP-500 模式在没有 ZooKeeper 的情况下运行 Kafka。当 Kafka 在此模式下运行时，我们将使用 Raft 仲裁来存储我们的元数据，而不是 ZooKeeper。刚开始的时候，KIP-500 模式还处于实验阶段。大多数用户还是继续使用 '传统模式'，还在使用 ZooKeeper。部分原因是 KIP-500 模式一开始不支持所有可能的功能。另一个原因是因为我们希望在有足够的信心将 KIP-500 模式设为默认模式之后使用。最后，我们需要时间来完善从传统模式到 KIP-500 模式的升级过程。

启用 KIP-500 模式的大部分工作会在控制器中进行。我们必须将控制器中与 ZooKeeper 交互的部分与实现更通用逻辑部分(副本集管理等)分离开。我们需要定义和实现更多的控制器 API 来替换当前与 ZooKeeper 的通信机制。这方面的一个例子是新的 AlterIsr API。此 API 允许副本在不使用 ZooKeeper 的情况下将同步副本集的更改通知控制器。

### 2.4 升级

KIP-500 引入了一个桥接版本(bridge release)的概念，可以与 KIP-500 之前和之后的 Kafka 版本共存。Bridge 版本很重要，因为可以实现对 ZooKeeper 替换的不停机升级。使用旧版本 Kafka 的用户只需升级到桥接版本即可。然后，再可以执行第二次升级到完全实现 KIP-500 的版本。正如它的名字所暗示的那样，桥接版本就像一座通往新世界的桥梁。

那么这是如何工作的呢？考虑一个处于部分升级状态的群集，有一些 Broker 处于桥接版本，有一些 Broker 处于 KIP-500 之后的版本中。但控制器始终是 KIP-500 后的 Broker。在这个集群中，Broker 不能依靠直接修改 ZooKeeper 来通知他们正在做的变更（例如，配置更改或 ACL 更改）。KIP-500 之后的 Broker 不会收到此类通知，因为他们没有在 ZooKeeper 上监听。只有控制器仍在与 ZooKeeper 交互，通过将其更改镜像到 ZooKeeper。因此，在桥接版本中，除了控制器之外的所有 Broker 都必须将 ZooKeeper 视为只读的（有一些非常有限的例外）。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

引用：
- [1] https://cwiki.apache.org/confluence/display/KAFKA/KIP-500%3A+Replace+ZooKeeper+with+a+Self-Managed+Metadata+Quorum
- [2] https://cwiki.apache.org/confluence/x/Li7cC
- [3] Raft 论文: https://raft.github.io/raft.pdf

原文：[Apache Kafka Needs No Keeper: Removing the Apache ZooKeeper Dependency](https://www.confluent.io/blog/removing-zookeeper-dependency-in-kafka/)
