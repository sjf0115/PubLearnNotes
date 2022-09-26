---
layout: post
author: sjf0115
title: Flink 启用与配置检查点 Checkpoint
date: 2022-09-25 21:24:17
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

超时时间指定了每次 Checkpoint 执行上限时间。一旦超过该阈值，Flink 将会中断 Checkpoint 并放弃这次 Checkpoint。如下所示配置，必须在一分钟内完成 Checkpoint，否则将会中止正在进行的 Checkpoint：
```java
env.getCheckpointConfig().setCheckpointTimeout(60000);
```
如果不设置，默认超时时间为 10 分钟。需要注意的是，Checkpoint 超时时间最低不能小于10毫秒。

#### 3.2 最多同时执行的 Checkpoint 个数

这个配置指定了可以同时执行的最多 Checkpoint 个数。由于每个任务的处理进度不同，有可能出现后面的任务还没完成前一个 Checkpoint，但是前面任务已经触发了下一个 Checkpoint 了。这个参数就是限制同时进行的最大数量，可以通过 setMaxConcurrentCheckpoints 方法设置：
```java
env.getCheckpointConfig().setMaxConcurrentCheckpoints(1);
```
> 如果配置 Checkpoint 之间最小时间间隔，不能使用此配置。

默认情况下只有一个 Checkpoint 在运行，即当一个 Checkpoint 正在运行时，系统不会触发另一个 Checkpoint。这确保了拓扑结构不会在 Checkpoint 上花费太多时间，并且不会影响流应用程序的处理。我们可以指定并行个数，同时触发多个 Checkpoint，进而提升 Checkpoint 的整体效率。

需要注意的是，如果设置了 minPauseBetweenCheckpoints，那么 maxConcurrentCheckpoints 这个参数就不起作用了。

#### 3.3 Checkpoint 之间最小时间间隔

用于指定在上一个 Checkpoint 完成之后，检查点协调器 CheckpointCoordinator 最快等多久可以触发下一个 Checkpoint。主要目的是设置两个 Checkpoint 之间的最小时间间隔。一般情况下，Checkpoint 生成比较快，不会等到下一个 Checkpoint 触发之前就结束了。但有时候你可能会遇到状态过大导致 Checkpoint 生成时间过长。在大状态下，如果 Checkpoint 每次完成时长都超过系统设定 Checkpoint 时间间隔，那么会一直在做 Checkpoint，因为当应用发现它刚刚做完一次 Checkpoint 后，又已经到了下次 Checkpoint 的时间，会又开始新的一次 Checkpoint。最终导致 Flink 应用程序密集的触发 Checkpoint 操作，会占用大量计算资源从而影响到整个应用的性能。

我们可以通过设定 Checkpoint 之间最小时间间隔，来改善这一问题。这就意味着即使已经达到了周期触发的时间点，只要距离上一个 Checkpoint 完成的间隔不够，就依然不能开启下一次 Checkpoint。这就为正常处理数据留下了充足的间隙。如下所示，如果配置为 5000 毫秒，不论 Checkpoint 持续时间和启动时间间隔是多少，下一个 Checkpoint 将在上一个 Checkpoint 完成之后的 5000 毫秒后启动，即两个 Checkpoint 之间最少有 5000 毫秒的时间间隔：
```java
env.getCheckpointConfig().setMinPauseBetweenCheckpoints(5000);
```
> 通过配置 Checkpoint 之间最小时间间隔而不是配置 Checkpoint 启动时间间隔，这样更容易配置应用程序，因为 Checkpoint 之间最小时间间隔不容易受到 Checkpoint 完成时长的影响。

需要注意的是，当指定这个参数时，maxConcurrentCheckpoints 的值只能为 1，即最多只能同时执行一个 Checkpoint。

#### 3.4 外部持久化存储

Checkpoint 在默认的情况下仅用于恢复失败的作业，并不保留，当程序取消时 Checkpoint 就会被删除。你可以通过配置来保留 Checkpoint，这些被保留的 Checkpoint 在作业失败或取消时不会被清除。这样，你就可以使用该 Checkpoint 来恢复失败的作业。通过 ExternalizedCheckpointCleanup 参数指定当作业失败或取消时外部 Checkpoint 该如何清理：
- DELETE_ON_CANCELLATION：在作业取消的时候会自动删除外部 Checkpoint，但是如果是作业失败退出，则会保留 Checkpoint。
- RETAIN_ON_CANCELLATION：作业取消的时候也会保留外部 Checkpoint。

如下所示，使用 RETAIN_ON_CANCELLATION 清除策略配置 Checkpoint 定期持久化到从外部存储中。使用这种方式不会在任务正常停止的过程中清理 Checkpoint 数据，而是会一直保存在外部存储中，另外我们也可以通过外部 Checkpoint 对任务进行恢复：
```java
env.getCheckpointConfig().enableExternalizedCheckpoints(CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
```

#### 3.5 可容忍的 Checkpoint 失败次数

定义了在整个作业失败之前可以容忍多少次连续 Checkpoint 失败。默认值为 0，这意味着不允许任何 Checkpoint 失败，只要 Checkpoint 失败则任务直接失败：
```java
env.getCheckpointConfig().setTolerableCheckpointFailureNumber(0);
```

> setFailOnCheckpointingErrors 已经废弃，推荐使用 setTolerableCheckpointFailureNumber

#### 3.6 优先从 Checkpoint 恢复

配置优先从 Checkpoint 恢复。即使有更多可用的最近 Savepoint 可以减少恢复时间，但也可以配置作业优先从最新的 Checkpoint 恢复：
```java
env.getCheckpointConfig().setPreferCheckpointForRecovery(true);
```
> 在后续版本中已经被废弃，不建议使用

#### 3.7 非对齐的 Checkpoint

我们可以启用非对齐的 Checkpoint，即不再执行 Checkpoint Barrier 对齐操作，可以大大减少 Checkpoint 的时间。这个配置仅适用于 EXACTLY-ONCE 的 Checkpoint 模式下，并且同时并发的 Checkpoint 的个数为1：
```java
env.getCheckpointConfig().enableUnalignedCheckpoints();
```

> 完整代码请查阅:[CheckpointExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/checkpoint/CheckpointExample.java)

### 4. 相关配置选项

其他参数和默认值也可以通过 `conf/flink-conf.yaml` 配置文件进行设置（请参阅完整指南的[配置](https://nightlies.apache.org/flink/flink-docs-release-1.11/zh/docs/deployment/config/)）：

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

Flink 的[检查点机制](https://smartsi.blog.csdn.net/article/details/127019291)会存储所有状态的一致性快照。Checkpoint 存储的位置（例如，JobManager 的内存，文件系统，数据库）取决于状态后端的配置。

默认情况下，状态保存在 TaskManager 的内存中，Checkpoint 存储在 JobManager 的内存中。为了能够存储较大的状态，Flink 支持多种方法在其他状态后端存储状态以及对状态进行 Checkpoint。状态后端的选择可以通过 `StreamExecutionEnvironment.setStateBackend（...）` 来配置。

> 有关状态后端如何选择，请参阅[有状态流处理:Flink状态后端](https://smartsi.blog.csdn.net/article/details/126682122)。
