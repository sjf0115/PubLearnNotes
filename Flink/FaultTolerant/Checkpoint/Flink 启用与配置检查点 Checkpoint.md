---
layout: post
author: sjf0115
title: Flink 检查点启用与配置
date: 2020-12-12 21:24:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-development-checkpointing-enable-config
---

> Flink版本：1.11

Flink 中每个函数和算子都可以是有状态的（请参阅[状态分类](https://smartsi.blog.csdn.net/article/details/123296073)了解详细信息）。有状态函数在处理单个元素/事件时会存储数据。为了能够使状态可以容错，Flink 需要对状态进行 Checkpoint。Checkpoint 可以允许 Flink 在流中恢复状态以及消费位置。

> 关于 Flink 容错机制背后的技术请参阅[流式容错](https://smartsi.blog.csdn.net/article/details/126551467)的详细文档。

### 1. 前提条件

Flink Checkpoint 机制可以与流和状态的持久化存储进行交互。一般来说，需要：
- 一个可持久化（或保存很长时间）的数据源：可以重新消费指定时间段的记录。持久化消息队列（例如，Apache Kafka，RabbitMQ，Amazon Kinesis，Google PubSub）或者文件系统（例如，HDFS，S3，GFS，NFS，Ceph）可以满足这样的需求。
- 状态的持久化存储。通常是分布式文件系统（例如，HDFS，S3，GFS，NFS，Ceph）。

### 2. 启用检查点

默认情况下，Checkpoint 不会被启用。如果要启用 Checkpoint，需要在 StreamExecutionEnvironment 上调用 enableCheckpointing 方法：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.enableCheckpointing(1000);
```
表示每 1s 触发一个新的 Checkpoint 流程，即下一个 Checkpoint 将在上一个 Checkpoint 触发后的 1 秒触发。

> 检查点的间隔时间是对处理性能和故障恢复速度的一个权衡。如果我们希望对性能的影响 更小，可以调大间隔时间;而如果希望故障重启后迅速赶上实时的数据处理，就需要将间隔时 间设小一些。

除了设置 Checkpoint 的触发(启动)时间间隔，我们还可以提供一个可选的 Checkpoint 模式（CheckpointingMode），可以选择 Exactly-Once 或 At-Least-Once 处理语义：
```java
StreamExecutionEnvironment enableCheckpointing(long interval);
StreamExecutionEnvironment enableCheckpointing(long interval, CheckpointingMode mode);
```
对于大多数应用来说，选择 Exactly-Once 处理语义即满足需求。只有某些超低延迟（持续几毫秒）的应用程序才会选择 At-Least-Once 处理语义：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.enableCheckpointing(1000, CheckpointingMode.EXACTLY_ONCE);
```
或者使用如下代码：
```java
env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
```
> 如果不显示提供 CheckpointingMode，默认是 Exactly-Once 语义。

### 3. 配置检查点

除了配置启动时间间隔和处理语义之外，我们还可以配置其他参数。

#### 3.1 Checkpoint 超时时间

超时时间指定了每次 Checkpoint 执行上限时间。一旦超过该阈值，Flink 将会中断 Checkpoint，并按照超时处理。如下所示配置，必须在一分钟内完成 Checkpoint，否则将会中止正在进行的 Checkpoint：
```java
// checkpoints have to complete within one minute, or are discarded
env.getCheckpointConfig().setCheckpointTimeout(60000);
```

### 3.2 最大并行执行 Checkpoint 个数

这个配置指定了能够最大同时执行的 Checkpoint 个数。在默认情况下只有一个 Checkpoint 可以运行，即当一个 Checkpoint 正在运行时，系统不会触发另一个 Checkpoint。这确保了拓扑结构不会在 Checkpoint 上花费太多时间，并且不会影响流应用程序的处理。我们可以指定并行个数，同时触发多个 Checkpoint，进而提升 Checkpoint 的整体效率：
```java
// allow only one checkpoint to be in progress at the same time
env.getCheckpointConfig().setMaxConcurrentCheckpoints(1);
```
> 如果配置 Checkpoint 之间最小时间间隔，不能使用此配置。

#### 3.3 Checkpoint 之间最小时间间隔

主要目的是设置两个 Checkpoint 之间的最小时间间隔，防止出现例如状态过大而导致 Checkpoint 执行时间过长，从而导致 Checkpoint 积压过多，最终导致 Flink 应用程序密集的触发 Checkpoint 操作，会占用大量计算资源从而影响到整个应用的性能。在大状态下，如果 Checkpoint 每次完成时长都超过系统设定 Checkpoint 启动时间间隔，那么会一直在做 Checkpoint，因为当应用发现它刚刚做完一次 Checkpoint 后，又已经到了下次 Checkpoint 的时间，会又开始新的一次 Checkpoint。如下所示，如果配置为 5000，不论 Checkpoint 持续时间和启动时间间隔是多少，下一个 Checkpoint 将在上一个 Checkpoint 完成之后的5000毫秒内启动，即两个 Checkpoint 之间最少有5000毫秒的时间间隔。这意味着 Checkpoint 启动时间间隔要大于此参数：
```java
// make sure 500 ms of progress happen between checkpoints
env.getCheckpointConfig().setMinPauseBetweenCheckpoints(500);
```
> 通过配置 Checkpoint 之间最小时间间隔而不是配置 Checkpoint 启动时间间隔，这样更容易配置应用程序，因为 Checkpoint 之间最小时间间隔不容易受到 Checkpoint 完成时长的影响。
> 请注意，这个值也意味着最大只能同时执行一个 Checkpoint。

#### 3.4 外部 Checkpoint

可以配置 Checkpoint 定期持久化到从外部存储中。使用这种方式不会在任务正常停止的过程中清理 Checkpoint 数据，而是会一直保存在外部存储中，另外我们也可以通过从外部 Checkpoint 中对任务进行恢复：
```java
env.getCheckpointConfig().enableExternalizedCheckpoints(CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
```
> 详细信息请参阅[外部检查点](http://smartsi.club/flink-stream-deployment-externalized-checkpoints.html)

#### 3.5 可容忍的 Checkpoint 失败次数

默认值为0，这意味着我们不容忍任何 Checkpoint 失败。
```java
// Set the tolerable checkpoint failure number
env.getCheckpointConfig().setTolerableCheckpointFailureNumber(0);
```

#### 3.6 优先从 Checkpoint 恢复

配置优先从 Checkpoint 恢复。即使有更多可用的最近 Savepoint 可以减少恢复时间，但也可以配置作业优先从最新的 Checkpoint 恢复：
```java
// allow job recovery fallback to checkpoint when there is a more recent savepoint
env.getCheckpointConfig().setPreferCheckpointForRecovery(true);
```

#### 3.7 非对齐的 Checkpoint

我们可以启用非对齐的 Checkpoint，可以大大减少 Checkpoint 时间。这个配置仅适用于 EXACTLY-ONCE Checkpoint，并且同时并发为1：
```java
// enables the experimental unaligned checkpoints
env.getCheckpointConfig().enableUnalignedCheckpoints();
```

### 4. 相关配置选项

其他参数和默认值也可以通过 `conf/flink-conf.yaml` 配置文件进行设置（请参阅完整指南的[配置](https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/config.html)）：

| 配置项     | 默认值     | 类型 | 描述 |
| :------------- | :------------- | :------------- | :------------- |
| state.backend | (none) | String | 状态后端用来存储状态和 Checkpoint 状态 |
| state.backend.async | true | Boolean | 状态后端是否使用异步快照方法。某些状态后端可能不支持异步快照，或仅支持异步快照，而忽略此选项。|
| state.backend.fs.memory-threshold | 20 kb	| MemorySize | |
| state.backend.incremental | false	| Boolean | 状态后端是否使用增量 Checkpoint。对于增量 Checkpoint，仅存储与前一个 Checkpoint 的差异，而不存储完整的 Checkpoint 状态。启用后，在 Web UI 中显示的状态大小或从 rest API 获取的状态大小仅是增量 Checkpoint 大小，而不是完整的 Checkpoint 大小。某些状态后端可能不支持增量检查点，因此会忽略此选项。|
| state.backend.local-recovery | false | Boolean | 配置状态后端本地恢复。默认是关闭的。目前本地恢复仅涵盖 Keyed 状态后端。MemoryStateBackend 目前不支持本地恢复，请忽略此选项。|
| state.checkpoints.dir | (none) | String | 用于在 Flink 支持的文件系统中存储 Check 的数据文件和元数据的默认目录。必须从所有参与的进程/节点（即所有TaskManager和JobManager）访问存储路径。|
| state.checkpoints.num-retained | 1 | Integer | 最多保留已完成的检查点实例的数量 |
| state.savepoints.dir | (none)	| String | Savepoint的默认目录。状态后端用于将 Savepoint 写入文件系统（MemoryStateBackend，FsStateBackend，RocksDBStateBackend）。|

### 5. 选择状态后端

Flink 的[检查点机制](http://smartsi.club/flink-data-streaming-fault-tolerance.html)会存储所有状态的一致性快照。Checkpoint 存储的位置（例如，JobManager 的内存，文件系统，数据库）取决于状态后端的配置。

默认情况下，状态保存在 TaskManager 的内存中，Checkpoint 存储在 JobManager 的内存中。为了能够存储较大的状态，Flink 支持多种方法在其他状态后端存储状态以及对状态进行 Checkpoint。状态后端的选择可以通过 `StreamExecutionEnvironment.setStateBackend（...）` 来配置。

> 有关状态后端如何选择，请参阅[有状态流处理:Flink状态后端](http://smartsi.club/stateful-stream-processing-apache-flink-state-backends.html)。

### 6. 迭代作业中的状态检查点

目前 Flink 只为没有迭代的作业提供处理保证。在迭代作业上启用检查点会导致异常。为了能够在迭代作业上强制进行 Checkpoint，用户需要在启用 Checkpoint 时设置强制标志：
```java
env.enableCheckpointing(interval，CheckpointingMode.EXACTLY_ONCE, true);
```
