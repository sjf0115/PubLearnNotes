---
layout: post
author: smartsi
title: Flink Savepoint机制
date: 2021-01-01 18:13:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-deployment-savepoints
---

### 1. 概述

Savepoint 是 Checkpoint 的一种特殊实现，底层其实也是使用 Checkpoint 的机制。Savepoint 是用户以手工命令的方式触发 Checkpoint，并将结果持久化到指定的存储路径中，其主要目的是帮助用户在升级和维护集群过程中保存系统中的状态数据，避免因为停机维护或者升级应用等正常终止应用的操作导致系统无法恢复到原有的计算状态的情况，从而无法实现端到端的 Exactly-Once 语义保证。

> Savepoint 与 Checkpoint 的具体区别，可以参阅[Flink Savepoints和Checkpoints的3个不同点](http://smartsi.club/differences-between-savepoints-and-checkpoints-in-flink.html)

### 2. 分配算子ID

当使用 Savepoint 对整个集群进行升级或者运维操作的时候，需要停止整个 Flink 应用程序，此时用户可能会对应用的代码逻辑进行修改，即使 Flink 能够通过 Savepoint 将应用中的状态数据同步到磁盘然后恢复任务，但由于代码逻辑发生变化，在升级过程中有可能导致算子的状态无法通过 Savepoint 中的数据进行恢复。在这种情况下就需要通过唯一的ID标记算子。

在 Flink 中默认支持自动生成算子ID，但是这种方式不利于对代码层面的维护和升级，建议用户尽可能的使用手工的方式对算子进行唯一ID标记。如下所示可以通过 `uid()` 方法指定唯一ID：

```java
env.addSource(new SimpleCustomSource()).uid("source-uid") // 为Source指定ID
.keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
    @Override
    public String getKey(Tuple2<String, Integer> value) throws Exception {
        return value.getField(0);
    }
})
.map(new MyStatefulMapFunction()).uid("map-uid") // 为Map指定ID
.print(); // 自动生成ID
```

如果你没有手动指定这些ID，它们会自动生成。只要这些ID不变，您就可以从保存点中恢复。生成的ID取决于我们程序的拓扑结构，并对程序修改敏感，如果程序发生改变，ID也会发生改变。因此，强烈建议手动分配这些ID。

> 强烈建议你按本节描述的去调整程序，以便将来可以升级程序。主要的变化是通过 `uid（String）` 方法手动指定算子ID。

对于每个有状态的算子，你可以将保存点理解为算子ID到状态的映射：
```
Operator ID | State
------------+------------------------
source-uid   | State of StatefulSource
map-uid      | State of StatefulMapper
```

在上面的例子中，print Sink是无状态的，因此不是保存点状态的一部分。默认情况下，我们会尝试将保存点下的每个条目映射到我们新程序下的算子。如果用户在新程序中删除了某个算子，这时会出现任务不能恢复的情况，此时我们可以设置忽略无法匹配的状态，让程序正常启动起来。

### 3. 操作

Savepoint 可以使用命令行来操作，命令行提供了触发 Savepoint、取消作业时生成 Savepoint、从 Savepoint 中恢复作业以及释放 Savepoint 等操作。在 Flink 1.2.0 版本之后也可以使用 Web 页面从 Savepoint 中恢复作业。

#### 3.1 手动触发Savepoint

使用如下命令来触发 Savepoint，同时需要在命令行中指定 jobId 以及可选的 targetDirectory 两个参数，jobId 是需要触发 Savepoint 操作的作业Id，targetDirectory 是 Savepoint 数据的存储路径：
```
bin/flink savepoint :jobId [:targetDirectory]
```
![](1)

> 如果你不指定 targetDirectory，则需要配置一个默认目录，否则触发 Savepoint 失败。

如果你是在 Hadoop YARN 上提交应用，需要指定 jobId 的同时也需要通过使用 yid 指定 YarnAppIdId，其他参数跟普通模式一样：
```
bin/flink savepoint :jobId [:targetDirectory] -yid :yarnAppId
```

##### 3.2 取消作业并触发Savepoint

可以使用如下 cancel 命令在取消作业时并自动触发 Savepoint：
```
bin/flink cancel -s [:targetDirectory] :jobId
```
![](2)

此外，您可以指定 targetDirectory 来存储 Savepoint，但是 JobManager 和 TaskManager 必须有访问该目录的权限。

#### 3.3 从Savepoint恢复作业

可以使用如下 run 命令从 Savepoint 中恢复作业，其中 -s 参数指定了 Savepoint 数据的存储路径：
```
bin/flink run -s :savepointPath [:runArgs]
```
![](3)

默认情况下，恢复操作会尝试将 Savepoint 下的所有状态映射回待恢复的新程序。如果我们在新程序中删除了某个算子，这时会出现任务不能恢复的情况，此时我们可以通过 `--allowNonRestoredState` （简写-n）参数跳过无法匹配的状态，让程序正常启动起来：
```
bin/flink run -s :savepointPath -n [:runArgs]
```

#### 3.4 释放Savepoint

可以使用如下命令释放保存在 savepointPath 中的 Savepoint 数据：
```
bin/flink savepoint --dispose :savepointPath
```

![](4)

官方文档给出如下也可以释放Savepoint：
```
bin/flink savepoint -d :savepointPath
```
但是实际执行遇到如下问题，暂时没有找到原因：

![](5)

> 有知道的朋友可以留言

需要注意的是我们还可以通过常规文件系统手动删除 Savepoint 数据，而不会影响其他 Savepoint 或 Checkpoint。在 Flink 1.2 之前，这是一个比较繁琐的任务，必须通过上面的 savepoint 命令执行的。

### 4. 配置

通过上面我们知道在执行 Savepoint 操作时需要指定 targetDirectory 目录，这个目录除了可以通过上面命令行方式指定外，也可以在系统环境中配置默认的 targetDirectory，这样就不需要每次在命令行中指定了。需要注意的时，默认路径和命令行中必须至少指定一个，否则无法正常执行 Savepoint 操作。

我们可以通过修改 flink-conf.yaml 配置文件的 state.savepoints.dir 参数来修改默认路径：
```
# Default target directory for savepoints, optional.
#
state.savepoints.dir: hdfs://localhost:9000/flink/savepoints
```
> 需要注意的是配置的路径必须是 JobManager 和 TaskManager 有权限访问的路径，例如，分布式文件系统上的路径。

### 5. Savepoint 数据

触发 Savepoint 时，会在指定目录 targetDirectory 或者 state.savepoints.dir 配置参数下创建一个新的保存点目录。数据以及元数据将被存储该目录下：

![](6)

其中 b2f649 是 jobId 简写，0ac0837b40ce 是 SavepointId。具体格式如下：
```
/savepoints/savepoint-:shortjobid-:savepointid/_metadata
```

### 6. FAQ

(1) 应该为作业中的所有算子分配ID吗？

根据经验来说，是的。严格来说，仅为有状态算子分配算子ID就足够了。Savepoint 只包含这些算子的状态，并不包含无状态的算子。实际上，建议给所有的算子分配ID，因为一些内置算子也是有状态的，比如，窗口算子。但是有时候我们并且不清楚哪些内置算子是有状态的，哪些是没有状态的。如果你确定算子是无状态的，那么可以不分配ID。

(2) 如果在作业中添加一个新的有状态算子会发生什么？

当你添加一个新的算子到你的作业时，算子在初始化时没有任何状态。新的算子类似一个无状态算子。

(3) 如果从作业中删除了一个有状态算子会发生什么？

默认情况下，Savepoint 会尝试将所有状态进行恢复。如果从 Savepoint 进行恢复时，发现某个算子已经被删除（Savepoint 包含了这个算子的状态），恢复操作将会失败。但是你可以通过设置 `--allowNonRestoredState`（简称：`-n`） 参数来跳过无法恢复的状态：
```
flink run -s :savepointPath -n [:runArgs]
```

(4) 如果在作业中对有状态的算子进行重新排序会怎样？

如果你为这些算子分配了ID，将照常恢复。如果你没有为它们分配ID，那么在重新排序后，有状态算子自动生成的ID很可能会发生变化。这将导致你无法从以前的 Savepoint 进行恢复。

(5) 如果在作业中添加、删除或重新排序没有状态的算子会发生什么情况？

如果你给有状态算子分配了ID，那么无状态算子不会影响 Savepoint 的恢复。如果你没有分配ID，那么在重新排序后，有状态算子自动生成的ID很可能会发生变化。这会导致你无法从以前的 Savepoint 进行恢复。所以还是建议给所有的算子分配ID。

(6) 当在恢复时改变了程序的并行度会发生什么？

如果 Savepoint 是在 Flink 大于 1.2.0 版本下被触发的，并且没有使用已经弃用的状态API（如 Checkpointed），那么是可以从 Savepoint 恢复程序并指定新的并行度。但是如果小于 1.2.0 版本 或者使用了已经弃用的状态API，那么必须先将作业和 Savepoint 迁移到大于等于 1.2.0 版本上，然后才能更改并行度。

> 请参考[升级作业和Flink版本指南](https://ci.apache.org/projects/flink/flink-docs-release-1.12/ops/upgrading.html)。




原文:[Savepoints](https://ci.apache.org/projects/flink/flink-docs-release-1.12/ops/state/savepoints.html)
