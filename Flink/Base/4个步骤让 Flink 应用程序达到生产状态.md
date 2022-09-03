---
layout: post
author: sjf0115
title: 4个步骤让 Flink 应用程序达到生产状态
date: 2019-04-20 17:03:19
tags:
  - Flink
  - Flink 基础

categories: Flink
permalink: 4-steps-flink-application-production-ready
---

这篇文章阐述了 Flink 应用程序达到生产状态所必须的配置步骤。在以下部分中，我们介绍了在 Flink 作业达到生产状态之前技术领导、DevOps、工程师们需要仔细考虑的重要配置参数。Flink 为大多数配置选项都提供了开箱即用的默认选项，在许多情况下它们是 POC 阶段（概念验证）或探索 Flink 不同 API 和抽象的很好的起点。

然而，将 Flink 应用程序投入生产还需要额外的配置，这些配置可以高效地扩展应用程序规模，使其达到生产状态，并能与不同系统要求，Flink 版本，连接器等兼容，以保证未来迭代和升级。

下面是我们收集的需要在 Flink 应用上线前检查的一些配置点：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/4-steps-flink-application-production-ready-1.png)

### 1. 明确定义 Flink 算子的最大并发度

Flink 的 KeyedState 是由 key group 进行组织，然后分发到 Flink 算子的各个并发实例上。这是分发的最小原子单元，因此也会影响 Flink 应用程序的可伸缩性。作业的每个算子的 key group 个数只能设置一次，可以手动配置或者直接使用默认配置。默认值粗略地使用 `operatorParallelism * 1.5`，下限 128，上限 32768 。可以通过 `setMaxParallelism(int maxParallelism)` 手动地为每个作业或算子设置最大并发度。

上线的任何作业都应该指定最大并发度。但是，一定要仔细考虑这个值的大小。因为一旦设置了最大并发度，就无法在以后更新。一个作业想要改变最大并发度，就只能从全新的状态重新开始。目前还无法在更改最大并发度后，从上一个成功的检查点或保存点恢复。

> 最大并发度设置后不能修改，修改的话会从全新的状态重新开始，因此需要仔细考虑最大并发度大小。

建议将最大并发度设置的足够大以满足未来应用程序的可扩展性和可用性，同时，又要选一个相对较低的值以避免影响应用程序整体的性能。这是因为 Flink 需要维护某些元数据来进行扩容，很高的最大并发度会增加 Flink 应用程序的整体状态大小。

> 最大并发度不能太大也不能太小。

Flink 文档提供了有关使用[检查点如何配置使用大状态的应用程序](https://ci.apache.org/projects/flink/flink-docs-stable/ops/state/large_state_tuning.html)的其他信息和指导。

### 2. 为 Flink 算子分配唯一用户ID（UUID）

对于有状态的 Flink 应用程序，建议为所有算子分配唯一的用户ID（UUID）。这是非常有必要的，因为一些内置的 Flink 算子（如windows）是有状态的，而有些算子是无状态的，这就很难知道哪些内置算子是有状态的，哪些是没有状态。

可以使用 `uid（String uid）` 方法为 Flink 算子分配 UUID。算子 UUID 可以使 Flink 有效地将算子的状态从保存点映射到恰当的算子上，这是保存点在 Flink 应用程序中正常工作的一个基本要素。

### 3. 充分考虑 Flink 应用程序的状态后端

由于 Flink 目前还不支持状态后端之间的互通性，所以开发人员和工程负责人在将应用程序上线前应仔细考虑 Flink 应用程序的状态后端类型。如果从保存点恢复状态，那么保存点必须采用相同的状态后端。

在我们之前的一篇[博文](https://smartsi.blog.csdn.net/article/details/126682122?spm=1001.2014.3001.5502)中，详细说明了 Flink 目前支持的3种类型的状态后端之间的差异。

对于生产用例，强烈建议使用 RocksDB 状态后端，因为这是目前唯一一种支持大状态和异步操作（如快照）的状态后端，异步操作允许在不阻塞 Flink 操作的情况下进行快照。另一方面，使用 RocksDB 状态后端可能存在性能折衷，因为所有状态访问和检索都需要序列化（和反序列化）来跨越JNI边界，与内存状态后端相比这可能会影响应用程序的吞吐量。

### 4. 配置 Job Manager 的高可用性（HA）

高可用性（HA）配置确保了 Flink 应用程序 JobManager 组件在出现潜在故障时可以自动恢复，从而将停机时间降至最低。JobManager 的主要职责是协调 Flink 部署，例如调度和适当的资源分配。

默认情况下，Flink 为每个 Flink 集群配置一个 JobManager 实例。这会产生单点故障（SPOF）：如果 JobManager 崩溃了，就会无法提交新程序，并且正在运行的程序也会失败。因此，强烈建议为生产用例配置高可用性（HA）。

上述4个步骤遵循社区设置的最佳实践，允许 Flink 应用程序在维护状态的同时任意扩展，处理更大容量的数据流和状态大小，并增加可用性保证。

英译对照：
- 算子: operator
- 保存点: savepoint
- 状态: state

原文:[4 steps to get your Flink application ready for production](https://www.ververica.com/blog/4-steps-flink-application-production-ready)
