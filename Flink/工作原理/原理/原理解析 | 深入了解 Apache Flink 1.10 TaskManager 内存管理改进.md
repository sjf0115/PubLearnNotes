---
layout: post
author: wy
title: 原理解析 | 深入了解 Apache Flink 1.10 TaskManager 内存管理改进
date: 2021-07-17 21:26:01
tags:
  - Flink

categories: Flink
permalink: memory-management-improvements-flink-1.10
---

> Flink 1.10

Apache Flink 1.10 对 Task Managers 的内存模型和配置选项进行了重大调整。这些最近引入的调整能使 Flink 更加适应各种部署环境（例如 Kubernetes、Yarn、Mesos），并对内存消耗提供严格的控制。在这篇文章中，我们会讲解 Flink 的内存模型，如何设置和管理 Flink 应用程序的内存消耗，以及社区在最新版本中的变化。

### 1. Flink 的内存模型介绍

清楚的了解 Apache Flink 的内存模型可以让我们更有效地管理各种工作负载。下图描述了 Flink 的主要内存组件：

![](img-memory-management-improvements-flink-1.10-1.jpg)

Task Manager 进程是一个 JVM 进程。从高层次上理解，它的内存由 JVM Heap 和 Off-Heap 内存组成。这些类型的内存由 Flink 直接使用或用于 JVM 特殊目的（例如，metaspace 等）。Flink 中有两个主要的内存消费方：作业算子任务的用户代码以及框架本身（内部数据结构、网络缓冲区等）。

需要注意的是用户代码可以直接访问所有类型的内存：JVM Heap、Direct 内存和 Native 内存。因此，Flink 无法真正控制分配以及使用。然而，有两种类型的 Off-Heap 内存可以被任务使用并由 Flink 精确控制：
- Managed Memory（Off-Heap）
- Network Buffers

后者是 JVM Direct Memory 的一部分，用于算子任务之间的用户记录的数据交换。

### 2. 如何配置 Flink 内存

随着 Flink 1.10 的最新发布，为了提供更好的用户体验，框架对内存组件进行了高层次和细粒度的优化。在 Task Manager 中设置内存基本上有三种选择。

为 Task Manager 的 JVM 进程配置可用的总内存，需要配置以下两个选项，也是最简单的两个选项：
- Total Process Memory：Flink Java 应用程序（包括用户代码）以及为 JVM 运行整个进程所消耗的总内存。
- Total Flink Memory：仅 Flink Java 应用程序消耗的内存，包括用户代码，但不包括为 JVM 运行分配的内存。

建议为 Standalone 部署配置 Total Flink Memory，明确为 Flink 声明分配多少内存是一种常见做法，而外部 JVM 开销则无关紧要。对于在容器化环境（如 Kubernetes、Yarn 或 Mesos）中部署 Flink，推荐使用 Total Process Memory 选项，因为变成了请求容器的总内存大小。容器化环境通常会严格执行此内存上限。

如果您想对 JVM Heap 和 Managed Memory（Off-Heap）的大小进行更细粒度的控制，还有另一种选项来配置 Task Heap 和 Managed Memory。这种方法明确区分了堆内存和任何其他内存类型。

与社区统一批处理和流处理的方向一致，该模型在两种情况下都普遍适用。可以允许在算子任务用户代码与流处理场景中的堆状态后端之间共享 JVM Heap 内存。以类似的方式，Managed Memory 可用于批量溢写以及流中的 RocksDB 状态后端。

其余的内存组件会根据其默认值或者额外配置的参数来自动调整。Flink 还会检查整体一致性。您可以在相应的文档中找到有关不同内存组件的更多信息。

### 3. 其他组件

在配置 Flink 内存时，不同内存组件的大小可以通过对应选项值进行设定，也可以使用多个选项进行调整。下面我们提供有关内存配置的一些见解。

#### 3.1 按比例细分 Total Flink Memory

此方法可以按比例细分 Total Flink Memory：Managed Memory（如果未明确设置）和 Network Buffers 可以按比例进行设置，JVM Heap 和 Off-Heap 可以设置固定内存大小，最后将剩余内存分配给 Task Heap（如果未明确设置）。下图显示了此类设置的示例：

![](img-memory-management-improvements-flink-1.10-2.jpg)

Flink 会校验分配的 Network Memory 大小是否在最小值和最大值之间，否则 Flink 会启动会失败。最大值和最小值都有默认值，可以用相应的配置来覆盖。在某些情况下，真正分配的大小可能与比例不完全匹配。例如，如果 Total Flink Memory 和 Task Heap 配置为固定大小内存，Managed Memory 配置一定比例内存，那么 Network Memory 将获得与其比例不完全匹配的剩余内存。

#### 3.2 控制容器内存限制的更多提示

Heap 和 Direct 内存使用由 JVM 管理。在 Apache Flink 或其用户应用程序中还有许多其他可能的 Native 内存消耗来源，这些来源并不受 Flink 或 JVM 管理。控制它们的上限通常很困难，这使得调试潜在的内存泄漏变得很复杂。如果 Flink 的进程以不受管理的方式分配过多内存，通常会导致在容器化环境中杀死 Task Manager 容器。在这种情况下，可能很难排查是哪种类型的内存消耗超过了上限。Flink 1.10 引入了一些特定的调优选项来清楚地表示这些组件。虽然 Flink 不能始终执行严格的上限和边界，但这里的想法是明确规划内存使用。下面我们提供了一些示例来说明如何设置内存以防止容器超出其内存上限：
- RocksDB 状态不能增长得太大。RocksDB 状态后端的内存消耗记在 Managed Memory 下。RocksDB 默认遵守其上限（仅自 Flink 1.10 起）。您可以增加 Managed Memory 大小以提高 RocksDB 的性能，也可以减少以节省资源。
- 用户代码或其依赖项会消耗大量的 Off-Heap 内存。调整 Task Off-Heap 参数可以为用户代码以及其依赖项分配额外的 Direct 或 Native 内存。Flink 无法控制 Native 内存的分配，但它可以为 JVM Direct 内存分配设置上限。Direct 内存限制由 JVM 强制执行。
- JVM Metaspace 需要额外的内存。如果遇到 OutOfMemoryError: Metaspace，Flink 提供了增加其上限的选项，由 JVM 确保不超过该上限。
- JVM 需要更多的内部内存。对某些类型的 JVM 进程分配没有办法直接控制，但 Flink 提供了 JVM 开销选项。这些选项允许声明额外的内存量，这些内存是为这些分配所预期的，并且未被其他选项覆盖。

### 4. 结论

最新版本的 Flink（Flink 1.10）对内存配置进行了一些重大调整，使您可以比以前更好地管理应用程序内存和调试 Flink。该领域的未来发展还包括为 Job Mamanger 进程采用类似的内存模型，具体参阅 [FLIP-116](https://cwiki.apache.org/confluence/display/FLINK/FLIP+116%3A+Unified+Memory+Configuration+for+Job+Managers)。

原文：[Memory Management Improvements with Apache Flink 1.10](https://flink.apache.org/news/2020/04/21/memory-management-improvements-flink-1.10.html)
