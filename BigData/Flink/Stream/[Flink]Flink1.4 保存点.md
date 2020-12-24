---
layout: post
author: sjf0115
title: Flink1.4 保存点
date: 2018-01-30 15:30:17
tags:
  - Flink
  - Flink 容错

categories: Flink
permalink: flink-stream-deployment-savepoints
---

### 1. 概述

保存点是存储在外部的独立检查点，你可以使用它来停止，恢复或更新你的 `Flink` 程序。他们使用 `Flink` 的检查点机制来创建流处理程序状态的快照（非增量），并将检查点数据和元数据写入外部文件系统。

这篇文章涵盖了所有步骤包括触发，恢复和销毁保存点。有关 `Flink` 如何处理状态和故障的更多详细信息，请查看。

备注:
```
为了允许在程序和Flink版本之间升级，请务必查看下面有关为算子分配ID的章节。
```

### 2. 分配算子ID

强烈建议你按本节描述的去调整程序，以便将来可以升级程序。主要的变化是通过`uid（String）`方法手动指定算子ID。这些ID用于限定每个算子的状态。

```
DataStream<String> stream = env.
  // Stateful source (e.g. Kafka) with ID
  .addSource(new StatefulSource())
  .uid("source-id") // ID for the source operator
  .shuffle()
  // Stateful mapper with ID
  .map(new StatefulMapper())
  .uid("mapper-id") // ID for the mapper
  // Stateless printing sink
  .print(); // Auto-generated ID
```
如果你没有手动指定这些ID，它们会自动生成。只要这些ID不改变，你就可以自动从保存点进行恢复。如果自动生成ID，生成的ID取决于你程序的结构，如果程序改变，ID也会发生变化。因此，强烈建议手动分配这些ID。

#### 2.1 保存点状态

对于每个有状态的算子，你可以将保存点理解为算子ID到状态的映射：
```
Operator ID | State
------------+------------------------
source-id   | State of StatefulSource
mapper-id   | State of StatefulMapper
```
在上面的例子中，`print`接收器是无状态的，因此不是保存点状态的一部分。默认情况下，我们尝试将保存点的每个条目映射回到一个新程序(we try to map each entry of the savepoint back to the new program)。

### 3. 操作

你可以使用命令行客户端来触发保存点，使用保存点取消作业，从保存点中恢复，并释放保存点。

`Flink`版本大于 `1.2.0` 时，也可以使用`webui`从保存点中恢复。

#### 3.1 触发保存点

触发保存点时，会在指定目录下创建一个新的保存点目录。数据以及元数据将被存储该目录下。例如在`FsStateBackend`或`RocksDBStateBackend`下：
```
# Savepoint target directory
/savepoints/

# Savepoint directory
/savepoints/savepoint-:shortjobid-:savepointid/

# Savepoint file contains the checkpoint meta data
/savepoints/savepoint-:shortjobid-:savepointid/_metadata

# Savepoint state
/savepoints/savepoint-:shortjobid-:savepointid/...
```
备注:
```
尽管看起来保存点可以进行移动，但是由于_metadata文件中的绝对路径，所以目前还不可能。请遵循FLINK-5778取消此限制。
```

请注意，如果使用 `MemoryStateBackend`，则元数据和保存点状态将存储在`_metadata`文件中。由于它是独立的，你可以移动文件并从任何位置进行恢复。

##### 3.1.1 触发保存点

```
$ bin/flink savepoint :jobId [:savepointDirectory]
```
这将触发作业ID为`:jobId`的作业的保存点，并返回创建的保存点的路径。你需要此路径来恢复和销毁保存点。

此外，你可以选择一个指定目标文件系统目录来存储保存点。`JobManager`必须有权访问该目录。

如果你不指定目标目录，则需要配置默认目录。 否则，触发保存点失败。

##### 3.1.2 使用YARN触发保存点

```
$ bin/flink savepoint :jobId [:savepointDirectory] -yid :yarnAppId
```
这将触发作业ID为`：jobId`，YARN应用程序ID为`：yarnAppId`的作业的保存点，并返回创建的保存点的路径。

其他的与上面触发保存点描述的相同。

##### 3.1.3 使用保存点取消作业

```
$ bin/flink cancel -s [:targetDirectory] :jobId
```
这将原子性的触发作业ID为`：jobid`作业的保存点并取消该作业。此外，你可以指定目标文件系统目录来存储保存点。`JobManager`必须有权访问该目录。

如果你不指定目标目录，则需要配置默认目录。 否则，使用保存点取消作业失败。

#### 3.2 从保存点恢复

```
$ bin/flink run -s :savepointPath [:runArgs]
```
这将提交一个作业并从指定保存点中恢复。你可以指定保存点的目录或`_metadata`文件的路径。

##### 3.2.1 允许非恢复状态

默认情况下，恢复操作将尝试将保存点的所有状态映射回正在恢复的程序(the resume operation will try to map all state of the savepoint back to the program you are restoring with)。如果你删除了一个算子，可以允许通过`--allowNonRestoredState`（简称：`-n`）选项跳过无法映射到新程序的状态：

#### 3.3 释放保存点

```
$ bin/flink savepoint -d :savepointPath
```
这将释放在`:savepointPath`中的保存点。

请注意，也可以通过常规文件系统操作手动删除保存点，而不影响其他保存点或检查点（回想一下每个保存点是独立的）。

#### 3.4 配置

您可以通过`state.savepoints.dir`属性配置默认的保存点目标目录。当触发保存点时，这个目录将被用来存储保存点。你可以通过使用触发器命令指定一个自定义目标目录来覆盖默认值。

```
# Default savepoint target directory
state.savepoints.dir: hdfs:///flink/savepoints
```

如果你既不配置默认值也不指定自定义目标目录，那么触发保存点失败。

### 4. FAQ

(1) 应该为作业中的所有算子分配ID吗？

根据经验来说，是的。严格来说，仅通过 `uid` 方法将ID分配给作业中的有状态算子就足够了。保存点只包含这些算子的状态，无状态算子不是保存点的一部分。

实际上，建议给所有的算子分配ID，因为一些 `Flink` 的内置算子（如 `Window` 算子）也是有状态的，并且不清楚哪些内置算子是有状态的，哪些是没有状态的。如果你完全确定算子是无状态的，则可以跳过 `uid` 方法。

(2) 如果在作业中添加一个需要状态到新算子会发生什么？

当你添加一个新的算子到你的作业中时，算子将被初始化并且没有任何状态。保存点包含每个有状态算子的状态。无状态的算子根本就不是保存点的一部分。新算子的行为与无状态算子的类似。

(3) 如果从作业中删除了一个具有状态的算子，会发生什么？

默认情况下，保存点恢复将尝试将所有状态恢复到原来的作业。如果从包含已删除算子状态的保存点进行恢复，将会失败。

你可以通过设置`--allowNonRestoredState`（简称：`-n`）来允许非恢复状态：
```
$ bin/flink run -s :savepointPath -n [:runArgs]
```

(4) 如果在作业中对有状态的算子进行重新排序会怎样？

如果你为这些算子分配了ID，将照常恢复。

如果你没有分配ID，那么在重新排序后，有状态算子自动生成的ID很可能会发生变化。这将导致你无法从以前的保存点进行恢复。

(5) 如果在作业中添加，删除或重新排序没有状态的算子，会发生什么情况？

如果你给有状态的算子分配了ID，那么无状态算子不会影响保存点的恢复。

如果你没有分配ID，那么在重新排序后，有状态算子自动生成的ID很可能会发生变化。这将导致你无法从以前的保存点进行恢复。

(6) 当在恢复时改变了程序的并行度会发生什么？

如果在 `Flink`版本 大于`1.2.0`，保存点被触发，并且没有使用已经弃用的状态API（如 `Checkpointed`），则可以简单地从保存点恢复程序并指定新的并行度。

如果在 `Flink`版本 小于`1.2.0`，从被触发的保存点恢复，或者使用已经弃用的API，那么首先必须将作业和保存点迁移到 `Flink` 大于等于 `1.2.0`版本，然后才能更改并行度。请参阅升[级作业和Flink版本指南](https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/upgrading.html)。


备注:
```
Flink版本:1.4
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/state/savepoints.html
