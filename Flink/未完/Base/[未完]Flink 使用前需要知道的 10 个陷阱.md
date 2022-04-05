---
layout: post
author: smartsi
title: Flink 使用前需要知道的 10 个陷阱
date: 2021-10-12 09:39:01
tags:
  - Flink

categories: Flink
permalink: ten-flink-gotchas-we-wish-we-had-known
---

采用新框架总是会带来一些意外之喜。花几天时间来排查我们的服务为什么会以一种意想不到的方式运行，结果却发现我们只是乱用了一个功能或者只是遗漏了一个简单的配置而已。

在 Contentsquare，我们需要不断升级我们的数据 Pipeline，以满足越来越多数据上越来越苛刻的需求。这就是我们为什么决定将小时级的 Spark 作业迁移到使用 Apache Flink 构建的流服务上。这样做可以让我们为客户提供更实时的数据，也可以通过更强大的管道处理能力来丰富历史数据。不过这样并不容易，我们的团队工作了一年才确保一切按计划进行。而且，如上所述，我们遇到了很多令人惊讶的问题！如果您才刚开始这样的旅程，本文会帮助您避免这些陷阱。

### 1. 并行度设置导致负载倾斜

我们从一个简单的问题开始：在 Flink UI 中查看某个作业的子任务时，关于每个子任务处理的数据量，你可能会遇到如下这种奇怪的情况：

![](1)

从上面可以知道算子的每个子任务中没有收到相同数量的 Key Groups，这些密钥组代表了可能的密钥总数的一部分。 如果给定的操作员收到 1 个 Key Group 而另一个收到 2 个，则第二个子任务很可能有两倍的工作要做。 查看 Flink 的代码，我们可以找到这个函数：

原文:[Ten Flink Gotchas we wish we had known](https://engineering.contentsquare.com/2021/ten-flink-gotchas/)
