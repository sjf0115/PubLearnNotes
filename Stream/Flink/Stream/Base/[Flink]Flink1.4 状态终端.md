---
layout: post
author: sjf0115
title: Flink 如何选择状态后端
date: 2018-01-17 12:30:17
tags:
  - Flink
  - Flink 容错

categories: Flink
permalink: flink-stream-state-backends
---

### 1. 概述

`Flink` 提供了不同的状态后端，可以指定状态的存储方式和位置。

状态可以存储在`Java`的堆内或堆外。根据你的状态后端，`Flink` 也可以管理应用程序的状态，这意味着 `Flink` 可以处理内存管理（可能会溢出到磁盘，如果有必要），以允许应用程序存储非常大的状态。默认情况下，配置文件 `flink-conf.yaml` 为所有`Flink`作业决定其状态后端。

但是，默认的状态后端配置也可以被每个作业的配置覆盖，如下所示。

Java版本:
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(...);
```
Scala版本:
```Scala
val env = StreamExecutionEnvironment.getExecutionEnvironment()
env.setStateBackend(...)
```

### 2. 可用的状态后端

开箱即用，`Flink` 内置了如下状态后端：
- `MemoryStateBackend`
- `FsStateBackend`
- `RocksDBStateBackend`

如果没有配置，系统默认使用`MemoryStateBackend`。

#### 2.1 MemoryStateBackend

`MemoryStateBackend` 将数据以对象的形式保存在 `Java` 堆上。键值对状态和窗口算子拥有保存值，触发器等的哈希表。

在进行检查点操作时，状态后端对状态进行快照，并将其作为检查点确认消息的一部分发送给 `JobManager`（master），并将存储在其堆上。

`MemoryStateBackend`  可以配置为使用异步快照。尽管我们强烈建议使用异步快照来避免阻塞管道，但请注意，这是一项新功能，目前默认情况下不会启用。要启用此功能，用户可以在实例化 `MemoryStateBackend`的构造函数中设置相应的布尔值 `true`，例如：
```java
new MemoryStateBackend(MAX_MEM_STATE_SIZE, true);
```

`MemoryStateBackend` 的使用限制：
- 每个单独状态的大小默认限制为5 MB。这个值可以在 `MemoryStateBackend` 的构造函数中增加。
- 不考虑配置的最大状态大小，状态不能大于`akka frame`大小。
- 聚合状态必须能够放进 `JobManager` 内存中。

`MemoryStateBackend` 适用场景：
- 本地开发和调试
- 只存储较小状态的作业，例如只包含 `record-at-a-time` 函数的作业（`Map`，`FlatMap`，`Filter`，...）。 `Kafka`消费者只需要很少的状态。

#### 2.2 FsStateBackend

`FsStateBackend` 使用文件系统URL（类型，地址，路径）进行配置，如 `hdfs://namenode:40010/flink/checkpoints` 或 `file:///data/flink/checkpoints`。

`FsStateBackend` 将正在使用的数据保存在 `TaskManager` 的内存中。在进行检查点操作时，将状态快照写入配置的文件系统文件和目录中。较小的元数据存储在 `JobManager` 的内存中（或者在高可用性模式下，存储在元数据检查点中）。

`FsStateBackend` 默认使用异步快照，以避免在写入状态检查点时阻塞处理管道。如果要禁用此功能，用户可以在实例化 `FsStateBackend` 的构造函数中将对应的布尔值设置为 `false`，例如：
```Java
new FsStateBackend（path，false）;
```

`FsStateBackend` 适用场景：
- 具有大状态，长窗口，大的键/值状态的作业。
- 所有高可用配置。

#### 2.3 RocksDBStateBackend

`RocksDBStateBackend` 使用文件系统URL（类型，地址，路径）进行配置，例如 `hdfs://namenode:40010/flink/checkpoints` 或 `file:///data/flink/checkpoints`。

`RocksDBStateBackend` 将 正在使用的数据保存在 `RocksDB` 数据库中，其位于 `TaskManager` 数据目录下（默认情况下）。进行检查点操作时，整个 `RocksDB` 数据库进行检查点操作存储到配置的文件系统和目录中。较小的元数据存储在 `JobManager` 的内存中（或者在高可用性模式下，存储在元数据检查点中）。

`RocksDBStateBackend` 总是执行异步快照。

`RocksDBStateBackend` 使用限制：
- 由于 `RocksDB` 的`JNI`桥接API基于 `byte []`，每个键和每个值支持的最大大小为 `2^31` 个字节。重要的是在 `RocksDB` 中使用合并操作的状态（例如`ListState`）可以累积超过`2^31`字节，然后在下一次检索时会失败。目前这是 `RocksDB JNI` 的限制。

`RocksDBStateBackend` 适用场景：
- 具有非常大的状态，长时间窗口，大键/值状态的作业。
- 所有高可用配置。

请注意，你可以保存的状态数量仅受可用磁盘空间的限制。与保存状态到内存的 `FsStateBackend` 相比，这可以保存非常大的状态。但是，这也意味着在这个状态后端下可以达到的最大吞吐量将会降低。

`RocksDBStateBackend` 是目前唯一个提供增量检查点的后端（见[这里](https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/state/large_state_tuning.html)）。

### 3. 配置状态后端

如果你不指定，默认的状态后端是 `jobmanager`。如果你希望为集群中的所有作业建立不同的默认值，可以在 `flink-conf.yaml` 中定义一个新的默认状态后端来完成。默认的状态后端可以被每个作业的配置覆盖，如下所示。

#### 3.1 设置每个作业的状态后端

作业状态后端在作业的 `StreamExecutionEnvironment` 上设置，如下例所示：

Java版本:
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new FsStateBackend("hdfs://namenode:40010/flink/checkpoints"));
```
Scala版本:
```scala
val env = StreamExecutionEnvironment.getExecutionEnvironment()
env.setStateBackend(new FsStateBackend("hdfs://namenode:40010/flink/checkpoints"))
```

#### 3.2 设置默认状态后端

可以使用配置键 `state.backend` 在 `flink-conf.yaml` 配置文件中配置默认状态后端。

配置的值可以是 `jobmanager`（`MemoryStateBackend`），`filesystem`（`FsStateBackend`），`rocksdb`（`RocksDBStateBackend`），或实现状态后端工厂 `FsStateBackendFactory` 类的全限定类名，例如 `RocksDBStateBackend` 的 `org.apache.flink.contrib.streaming.state.RocksDBStateBackendFactory`。

如果默认状态后端设置为 `filesystem`，`state.backend.fs.checkpointdir` 定义了检查点数据存储目录。

配置文件中的示例部分可能如下所示：
```
# The backend that will be used to store operator state checkpoints

state.backend: filesystem

# Directory for storing checkpoints

state.backend.fs.checkpointdir: hdfs://namenode:40010/flink/checkpoints
```


> 备注:

> Flink版本:1.4


原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/state/state_backends.html
