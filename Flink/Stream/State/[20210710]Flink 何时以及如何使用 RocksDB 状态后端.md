---
layout: post
author: sjf0115
title: Flink 何时以及如何使用 RocksDB 状态后端
date: 2021-07-10 18:08:21
tags:
  - Flink

categories: Flink
permalink: when-and-how-use-rocksdb-state-backend-in-apache-flink
---

流处理应用程序通常都是有状态的，已处理事件的信息会被记录下来来影响下一步的事件处理。在 Flink 中，这些被记录的信息，即状态，本地存储在我们配置的状态后端中。为了防止出现故障时数据丢失，状态后端会定期将其内容的快照保存到预先配置的持久存储中。RocksDB 状态后端（即 RocksDBStateBackend）是 Flink 三个内置状态后端中的一个。这篇博文将指导您了解使用 RocksDB 管理应用程序状态的好处，解释何时以及如何使用它，并澄清一些常见的误解。话虽如此，这篇博文不是来解释 RocksDB 是如何深入工作、如何进行高级故障排除以及性能调优的。

### 1. 状态

为了更好地理解 Flink 中的状态以及状态后端，我们有有必要来区分一下运行中状态（In-flight state）和状态快照（state snapshots）。运行中状态，也称为工作状态，是 Flink 作业正在工作过程中的状态。它始终存储在本地内存中（可能会溢出到磁盘），并在作业失败时可能会丢失，但不影响作业的可恢复。状态快照，即检查点和保存点，存储在远程持久化存储中，用于作业失败时恢复本地状态。生产环境中如何选择适当的状态后端取决于可扩展性、吞吐量以及延迟要求。

### 2. RocksDB 是什么

我们有一种常见的误解就是将 RocksDB 认为是一种分布式数据库，需要在集群上运行并由专业管理员管理。实际上 RocksDB 是一个用于快速存储的可嵌入持久KV存储。它通过 Java Native Interface (JNI) 与 Flink 交互。下图显示了 RocksDB 在 Flink 集群节点中的位置。详细信息将在以下部分进行说明。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/when-and-how-use-rocksdb-state-backend-in-apache-flink-1.png?raw=true)

### 3. Flink 中的 RocksDB

将 RocksDB 作为状态后端所需的一切都捆绑在 Apache Flink 发行版中，包括本机共享库：
```
$ jar -tvf lib/flink-dist_2.12-1.12.0.jar| grep librocksdbjni-linux64
8695334 Wed Nov 27 02:27:06 CET 2019 librocksdbjni-linux64.so
```

在运行时，RocksDB 会嵌入到 TaskManager 进程中。在本地线程中运行并处理本地文件。例如，如果我们在 Flink 集群中运行配置了 RocksDBStateBackend 状态后端的作业，我们将会看到类似以下内容，其中 32513 是 TaskManager 进程 ID：
```
$ ps -T -p 32513 | grep -i rocksdb
32513 32633 ?        00:00:00 rocksdb:low0
32513 32634 ?        00:00:00 rocksdb:high0
```
> 该命令仅适用于 Linux 系统。对于其他操作系统，请参阅其文档。

### 4. 何时使用 RocksDBStateBackend

除了 RocksDBStateBackend，Flink 还内置了两个状态后端：MemoryStateBackend 和 FsStateBackend。它们都是基于堆的，因为运行中状态存储在 JVM 堆中。目前，我们可以忽略 MemoryStateBackend，因为它仅用于本地开发和调试，不建议在生产环境使用。

使用 RocksDBStateBackend，运行中状态首先写入堆外/本机内存，然后在达到配置的阈值时刷新到本地磁盘。这意味着 RocksDBStateBackend 可以支持大于总配置堆容量的状态。我们可以在 RocksDBStateBackend 中存储的状态量仅受整个集群中可用磁盘空间量的限制。此外，由于 RocksDBStateBackend 不使用 JVM 堆来存储运行中状态，因此它不受 JVM 垃圾收集的影响，因此具有可预测的延迟。

除了完整的、自包含的状态快照之外，RocksDBStateBackend 还支持增量检查点进行性能调优。增量检查点仅存储自上一次检查点完成以来发生的更改。与执行完整快照相比，这大大减少了进行检查点的时间。RocksDBStateBackend 是目前唯一支持增量检查点的状态后端。

在以下情况下，RocksDB 是一个不错的选择：
- 作业的状态比本地内存大（例如，大窗口，大 Keyed State）；
- 希望使用增量检查点，以减少检查点时间；
- 希望有更可预测的延迟，而不受JVM垃圾回收的影响。

否则，如果应用程序状态比较小或者需要非常低的延迟，则应考虑 FsStateBackend。根据经验，RocksDBStateBackend 要比基于堆的状态后端慢几倍，因为它将键/值对存储为序列化字节。这意味着任何状态访问（读/写）都需要通过一个跨越 JNI 边界的反/序列化过程，这比直接使用堆上的状态代价更高。但好处是，对于相同数量的状态，与相应的堆状态相比，具有较低的内存占用。

### 5. 如何使用 RocksDBStateBackend

RocksDB 完全嵌入 TaskManager 进程并由其完全管理。RocksDBStateBackend 可以在集群级别配置为整个集群的默认值，也可以在作业级为单个作业配置。作业级别配置优先于集群级别配置。

(1) 集群级别

在 conf/flink-conf.yaml 添加如下配置：
```
state.backend: rocksdb
state.backend.incremental: true
state.checkpoints.dir: hdfs:///flink-checkpoints # location to store checkpoints
```
(2) 作业级别

创建 StreamExecutionEnvironment 后，将以下内容添加到您的作业代码中：
```java
env.setStateBackend(new RocksDBStateBackend("hdfs:///fink-checkpoints", true));   
```
> 除了 HDFS，如果在 FLINK_HOME/plugins 下添加相应的依赖项，您还可以使用其他本地或基于云的对象存储。

### 6. 最佳实践和高级配置

我们希望这篇概述能帮助您更好地了解 RocksDB 在 Flink 中的作用以及如何使用 RocksDBStateBackend。最后，我们将探索一些最佳实践和一些参考点，以进一步进行故障排除和性能调整。

#### 6.1 RocksDB 中的状态位置

如前所述，RocksDBStateBackend 中的运行中状态会溢出到磁盘上的文件。这些文件位于 Flink 配置的 state.backend.rocksdb.localdir 指定目录下。因为磁盘性能直接影响到 RocksDB 的性能，所以建议将该目录放在本地磁盘上。不鼓励将其配置到基于远程网络的位置，如 NFS 或 HDFS，因为写入远程磁盘通常较慢。高可用性也不是运行中状态的要求。如果需要高磁盘吞吐量，则首选本地 SSD 磁盘。

状态快照被持久化到远程持久化存储上。在状态快照期间，TaskManager 会对运行中状态生成快照并将其远程存储。将状态快照传输到远程存储完全由 TaskManager 本身处理，状态后端不参与。因此，state.checkpoints.dir 或者您在代码中为特定作业设置的参数可以是不同的位置，例如本地 HDFS 集群或基于云的对象存储，例如 Amazon S3、Azure Blob Storage、Google Cloud Storage、Alibaba OSS等。

#### 6.2 RocksDB 故障排查

要检查 RocksDB 在生产环境中的行为，我们应该查找名为 LOG 的 RocksDB 日志文件。默认情况下，此日志文件与我们的数据文件位于同一目录中，即 Flink 配置 state.backend.rocksdb.localdir 指定的目录。启用后，RocksDB 统计信息也会记录在那里以帮助诊断潜在的问题。如果您对 RocksDB 时间行为序列感兴趣，可以考虑为我们的 Flink 作业启用 RocksDB 原生指标。

> 从Flink1.10开始，通过将日志级别设置为HEADER，RocksDB日志记录被有效地禁用。要启用它，请查看 [How to get RocksDB’s LOG file back for advanced troubleshooting](https://ververica.zendesk.com/hc/en-us/articles/360015933320-How-to-get-RocksDB-s-LOG-file-back-for-advanced-troubleshooting)。

> 警告：在 Flink 中启用 RocksD B的原生指标可能会对我们的作业产生负面影响。

#### 6.3 RocksDB 调优

从 Flink 1.10 开始，Flink 默认将 RocksDB 的内存分配配置为每个任务槽的托管内存(managed memory)量。改善内存相关性能问题的主要机制是通过 Flink 配置 taskmanager.memory.managed.size 或 taskmanager.memory.managed.fraction 来增加 Flink 的托管内存。对于更细粒度的控制，你应该首先通过将 state.backend.rocksdb.memory.managed 设置为 false 来禁用自动内存管理，然后配置以下参数：
- state.backend.rocksdb.block.cache-size：RocksDB 中的 block_cache_size
- state.backend.rocksdb.writebuffer.size：RocksDB 中的 write_buffer_size
- state.backend.rocksdb.writebuffer.count：RocksDB 中的 max_write_buffer_number。

> 有关更多详细信息，请查看[如何在 Flink 中管理 RocksDB 内存](https://www.ververica.com/blog/manage-rocksdb-memory-size-apache-flink)以及 [RocksDB 内存使用](https://github.com/facebook/rocksdb/wiki/Memory-usage-in-RocksDB) 博客文章。

在 RocksDB 中写入或覆盖写入数据时，从内存刷新到本地磁盘以及数据压缩都是由 RocksDB 后台线程管理。在多核 CPU 的机器上，可以通过设置 Flink 配置 state.backend.rocksdb.thread.num（对应 RocksDB 中的 max_background_jobs）来增加后台刷新和压缩的并行度。对于生产设置，默认配置通常太小。如果我们的作业频繁从 RocksDB 读取数据，则应考虑启用布隆过滤器。

对于其他 RocksDBStateBackend 配置，请查看Flink 文档[Advanced RocksDB State Backends Options](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/deployment/config/#advanced-rocksdb-state-backends-options)。

### 7. 结论

RocksDB 状态后端（即 RocksDBStateBackend）是 Flink 内置的三个状态后端之一，是配置流处理程序的一强大的选择。可以使可扩展应用程序能够保持高达数 TB 的状态，并保证 Exactly-Once 处理语义。如果我们的 Flink 作业的状态太大而无法放入 JVM 堆，我们对增量检查点感兴趣，或者希望具有可预测的延迟，则应该使用 RocksDBStateBackend。由于 RocksDB 作为本机线程嵌入到 TaskManager 进程中并处理本地磁盘上的文件，因此 RocksDBStateBackend 支持开箱即用，无需进一步设置和管理任何外部系统或进程。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文:[Using RocksDB State Backend in Apache Flink: When and How](https://flink.apache.org/2021/01/18/rocksdb.html)
