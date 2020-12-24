---
layout: post
author: sjf0115
title: Apache HBase 1.0:一个新时代的开始
date: 2019-10-19 20:00:07
tags:
  - HBase

categories: HBase
permalink: start-of-a-new-era-apache-hBase-1.0
---

> 在学习 HBase API 时了解到 1.0 版本是一个里程碑式的版本， API 也发生了很多变化。在此我们回顾一下这个重要的版本的发布。

Apache HBase 社区在2015年2月份发布了 Apache HBase 1.0.0 版本。Apache HBase 在花费了将近七年的时间后取得了里程碑式的发展，这次发布提供了一些令人兴奋的特性以及并未牺牲稳定性的新API。

在此文章中，我们介绍一下 Apache HBase 项目的过去，现在以及将来。

### 1. 版本

在列举这个版本的详细特性之前，我们先回顾一下历史版本以及版本号演变。HBase 2007 年始于 Apache Hadoop 的一个子项目，并随同 Hadoop 一起发布。三年后，HBase 成为了一个独立的顶级 Apache 项目。由于 HBase 依赖于 HDFS，所以社区让 HBase 与 Hadoop 的主版本号保持一致。例如，HBase 0.19.x 版本与 Hadoop 0.19.x 版本一起使用，等等。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/HBase/start-of-a-new-era-apache-hBase-1.0.jpeg?raw=true)

但是，HBase 社区希望一个 HBase 版本可以与多个 Hadoop 版本一起使用，不仅仅能与其所匹配的主版本号一起使用。因此，一个新的命名方案就诞生了，新版本将从接近 1.0 版本的 0.90 主版本开始，就像上面时间线中展示的一样。我们也运用了一种'偶数-奇数'版本的约定，即奇数版本是开发者预览版本，偶数版本是可以在生产环境中使用的稳定版本。稳定版本系列包括0.90、0.92、0.94、0.96和0.98（详见[HBase版本](https://hbase.apache.org/book.html#hbase.versioning)）。

在 0.98 版本之后，我们把主干版本命名为 `0.99-SNAPSHOT`，但是官方已经用完了所有的数字！欠考虑了，2014年 HBase 社区一致认为这个项目已经足够成熟稳和定，可以发布 1.0.0 版本了。在三个 0.99.x 开发者预览版本以及六个 Apache HBase 1.0.0 备选版本之后，HBase 1.0.0 开始发布了。看上面的图表，显示了每个版本的发布时间、支持的生命周期以及开发者预览版本（例如0.99->1.0.0），如果有的话。

### 2. HBase 1.0.0，开启了一个新时代

1.0.0版本有三个目标
- 为将来的1.x系列版本奠定稳定基础
- 提供稳定运行的 HBase 集群及客户端
- 让版本和兼容性方面更加明确

包括之前的 0.99.x 系列版本，1.0.0 版本解决了超过1500个 JIRA 跟踪的问题。其中一些主要的修改如下所示。

#### 2.1 API 整理和改变

HBase 的客户端 API 已经发展多年了。为了简化语义、支持并提供可扩展性以及在将来更容易使用，我们重构了 1.0 版本之前的API。为此，1.0.0 版本引进了新的 API，并且废弃了一些常用的客户端 API（`HTableInterface`, `HTable` 以及 `HBaseAdmin`）。

建议更新我们的应用程序使用新风格的 API，因为在以后的 2.x 发行版本中会被删除这些废弃 API。更多资料，可以访问这个链接：http://www.slideshare.net/xefyr/apache-hbase-10-release 和 http://s.apache.org/hbase-1.0-api。

所有的客户端 API 都标识有 `InterfaceAudience.Public` 类注解，表明是 HBase 官方的客户端 API。接下来，对于以注解声明为客户端公开的类，所有的 1.x 版本将会对其 API 兼容。

#### 2.2 使用时间轴一致的Region副本提高可读性

作为第一阶段的一部分，这个版本包含了一个实验功能'使用时间轴一致的Region副本提高可读性'(`Read availability using timeline consistent region replicas`)。也就是说，一个 Region 可以以只读模式在多个 Region Server 上存在。Region 的其中一个副本作为主副本，可以写入数据，其它副本只能共享相同的数据。由于时间轴一致性保证的高可用，读请求可以发送到 Region 的任意一个副本上。查看 [JIRA HBASE-10070](https://issues.apache.org/jira/browse/HBASE-10070) 了解更多信息。

#### 2.3 在线配置修改及合并0.89-fb分支的一些功能

Apache HBase 项目中的 0.89-fb 分支是 Facebook 用于发布修改的分支。[JIRA HBASE-12147](https://issues.apache.org/jira/browse/HBASE-12147)合入了其中的补丁，可以在不用重启 Region Server 的情况下重新加载 HBase 服务器的一些配置。

除此之外，还有几百项性能优化（优化WAL管道、使用disruptor、多WAL、更多的使用off-heap、bug修复以及还有很多没展示的好东西。详细介绍请查看官方的[发布日志](http://markmail.org/message/u43qluenc7soxloe)。发布日志和白皮书也包含了二进制、源代码和协议的兼容性说明、所支持的 Hadoop 和 Java 版本，从0.94、0.96和0.98版本升级的说明以及其它重要细节。

HBase-1.0.0 版本也是 HBase 使用'语义版本'([semantic versioning](http://semver.org/)）的开始。简单的说，将来的 HBase 版本会使用显示兼容语义的 `MAJOR.MINOR.PATCH` 版本号。HBase 白皮书包含了所有兼容性方面的内容以及不同版本之间的区别。

### 3. 未来

我们已经将 HBase 1.0.0 版本标记为 HBase 的下一个稳定版本，这就意味着所有新用户都应该开始使用这个版本。然而我们明白，作为一个数据库，切换到更新的版本可能会花费一些时间。我们将会继续维护 0.98.x 版本，直到社区用户已经做好结束老版本的准备。预计 1.0.x、1.1.0、1.2.0 等发行版会从相应的分支进行发布，而 2.0.0 版本以及其他主版本也将会如期到达。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[Start of a new era: Apache HBase 1.0](https://blogs.apache.org/hbase/entry/start_of_a_new_era)
