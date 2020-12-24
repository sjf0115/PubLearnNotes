---
layout: post
author: sjf0115
title: Flink1.4 外部检查点
date: 2018-01-30 14:22:17
tags:
  - Flink
  - Flink 容错

categories: Flink
permalink: flink-stream-deployment-externalized-checkpoints
---

### 1. 概述

检查点通过恢复状态和对应流位置来实现 `Flink` 状态容错，从而为应用程序提供与无故障执行相同的语义。

请参阅[检查点](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/stream/state/checkpointing.html)以了解如何为你的应用程序启用和配置检查点。

### 2. 外部检查点 Externalized Checkpoints

默认情况下检查点不会持久化存储在外部系统中，只是用来从故障中恢复作业。当一个程序被取消时它们会被删除。但是，你可以配置检查点定期持久化存储在外部系统中，类似于保存点(`savepoints`)。这些外部持久化的检查点将其元数据写入持久性存储中，即使在作业失败时也不会自动清除。这样，如果你的作业失败时，你会有一个检查点用于恢复作业。

```java
CheckpointConfig config = env.getCheckpointConfig();
config.enableExternalizedCheckpoints(ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
```
`ExternalizedCheckpointCleanup`模式配置当你取消作业时外部检查点如何操作：

(1) `ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION`：作业取消时保留外部检查点。请注意，在这种情况下，你必须手动清除取消后的检查点状态。

(2) `ExternalizedCheckpointCleanup.DELETE_ON_CANCELLATION`: 作业取消时删除外部检查点。检查点状态只有在作业失败时才可用。

#### 2.1 目录结构

与保存点类似，外部检查点由元数据文件组成，一些其他数据文件（取决于状态后端）。外部检查点元数据的目标目录是由配置属性`state.checkpoints.dir`确定的，目前它只能通过配置文件来设置。

```
state.checkpoints.dir: hdfs:///checkpoints/
```

该目录包含恢复检查点所需的检查点元数据。对于`MemoryStateBackend`，这个元数据文件是独立的(`self-contained`)，不需要其他文件。

`FsStateBackend` 和 `RocksDBStateBackend` 需要写到不同的数据文件中，只需将这些文件的路径写入元数据文件。这些数据文件存储在状态后端指定的路径上。

```
env.setStateBackend(new RocksDBStateBackend("hdfs:///checkpoints-data/");
```

#### 2.2 与保存点的区别

外部检查点与保存点有一些差异。他们
- 使用状态后端指定的（低层次）数据格式
- 可能是增量存储的
- 不支持 `Flink` 部分功能（如重新调整）。

#### 2.3 从外部检查点恢复

作业可以通过使用检查点的元数据文件从外部检查点中恢复，就像从保存点恢复一样（请参阅[保存点恢复](https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/cli.html#restore-a-savepoint)）。请注意，如果元数据文件不是独立的，`jobmanager` 需要访问它所引用的数据文件（参见上面的目录结构）。

```
$ bin/flink run -s :checkpointMetaDataPath [:runArgs]
```


备注:
```
Flink版本:1.4
```

术语翻译:

术语|翻译
---|---
Checkpoints|检查点
Externalized Checkpoints|外部检查点
savepoints|保存点

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/state/checkpoints.html
