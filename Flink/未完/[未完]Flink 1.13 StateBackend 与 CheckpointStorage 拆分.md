---
layout: post
author: smartsi
title: Flink 1.13 StateBackend 与 CheckpointStorage 拆分
date: 2022-02-20 09:39:01
tags:
  - Flink

categories: Flink
permalink: disentangle-statebackends-from-checkpointing
---

## 1. 目标

Apache Flink 的持久化对许多用户来说都是一个谜。用户最常见反复提问的问题就是不理解 State、StateBackend 以及快照之间的关系。通过学习可以解答我们的一些困惑，但是这个问题如此常见，我们认为 Flink 的用户 API 应该设计的更友好一些。在过去几年中，我们经常会听到如下误解：
- 我们使用 RocksDB 是因为我们不需要容错。
- 我们不使用 RocksDB 是因为我们不想管理外部数据库。
- RocksDB 可以直接读写 S3 或者 HDFS（相对于本地磁盘）
- FsStateBackend 会溢写到磁盘，并且与本地文件系统有关系
- 将 RocksDB 指向网络附加存储，认为 StateBackend 需要容错

邮件列表中的很多问题非常能代表用户在哪里遇到问题，关键是其中许多问题都不是来自新用户！当前的 StateBackend 抽象对于我们许多用户来说太复杂了。所有这些问题的共同点就是误解了数据如何在 TM 上本地存储状态与 Checkpoint 如何持久化状态之间的关系。本文的目的就是介绍 StateBackend 与 Checkpoint 持久化剥离的原因、怎么剥离以及用户怎么迁移。

## 2. 现状

在 Flink 1.13 版本之前，StateBackend 有两个功能：
- 提供状态的访问、查询；
- 如果开启了 Checkpoint，会周期性的向远程持久化存储上传数据和返回元数据给 JobManager。

以上两个功能是混在一起的，即把状态存储(如何在 TM 上本地存储和访问状态)和 Checkpoint 持久化(Checkpoint 如何持久化状态)笼统的混在一起，导致初学者对此感觉很混乱，很难理解，如下图所示。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/disentangle-statebackends-from-checkpointing-1.png?raw=true)

### 2.1 命名

Flink 提供了三个开箱即用的 StateBackend：MemoryStateBackend、FsStateBackend 以及 RocksDBStateBackend，如下图所示。MemoryStateBackend 和 FsStateBackend 根据写出的 Checkpoint 位置来命名的（MemoryStateBackend 把 Checkpoint 数据存储到 JobManager 内存上，FsStateBackend 存储到文件系统上），但是它们都使用相同的内存数据结构在本地存储状态（状态数据都存储在内存上）。RocksDBStateBackend 是基于在本地存储状态数据的位置来命名的（状态数据存储在 RocksDB 上），同时它还快照到持久化文件系统中（Checkpoint 数据持久化到文件系统中）。

光从命名上来看，StateBackend 就已经比较混乱了，有的是基于 写出的 Checkpoint 位置来命名，有的却是基于在本地存储状态数据的位置来命名。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/disentangle-statebackends-from-checkpointing-3.png?raw=true)

### 2.2 实现

上面从命名的角度看 StateBackend 会让我们产生困惑，现在我们从 StateBackend 实现的角度来看待这个问题：StateBackend 接口因融合过多的功能而过载。目前包含四种方法：
```java
public interface StateBackend extends java.io.Serializable {
  // CheckpointStorage: 持久化存储 Checkpoint 数据
  CompletedCheckpointStorageLocation resolveCheckpoint(String externalPointer);
  CheckpointStorage createCheckpointStorage(JobID jobId);

  // StateBackend: 存储本地状态
  <K> AbstractKeyedStateBackend<K> createKeyedStateBackend(
     Environment env,
     JobID jobID,
     String operatorIdentifier,
     TypeSerializer<K> keySerializer,
     int numberOfKeyGroups,
     KeyGroupRange keyGroupRange,
     TaskKvStateRegistry kvStateRegistry,
     TtlTimeProvider ttlTimeProvider,
     MetricGroup metricGroup,
     @Nonnull Collection<KeyedStateHandle> stateHandles,
     CloseableRegistry cancelStreamRegistry
  ) throws Exception;

  OperatorStateBackend createOperatorStateBackend(
     Environment env,
     String operatorIdentifier,
     @Nonnull Collection<OperatorStateHandle> stateHandles,
     CloseableRegistry cancelStreamRegistry
  ) throws Exception;
}
```
从接口的注释可以看出，StateBackend 接口负责了两个独立且不相关的功能：Checkpoint 存储和本地状态后端。如下是现在使用 StateBackend 的几种方式：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// MemoryStateBackend
env.setStateBackend(new MemoryStateBackend())
env.setStateBackend(new MemoryStateBackend(1048))
env.setStateBackend(new MemoryStateBackend("s3://checkpoints", 1048))

// FsStateBackend
env.setStateBackend(new FsStateBackend("s3://checkpoints", 1048))

// RocksDBStateBackend
RocksDBStateBackend rocksDB = new RocksDBStateBackend("s3://checkpoints", 1028);
rocksDB.setOptionsFactory(/** blah **/);
RocksDBStateBackend rocksDB = new RocksDBStateBackend(new FsStateBackend("s3://checkpoints", 1048));
rocksDB.setOptionsFactory(/** blah **/);
RocksDBStateBackend rocksDB = new RocksDBStateBackend(new MemoryStateBackend());
rocksDB.setOptionsFactory(/** blah **/);
env.setStateBackend(rocksDB);
```
由于概念的混乱以及实现上的过载，导致之前的写法中包含了本地状态后端以及 Checkpoint 存储的参数。特别是 RocksDBStateBackend 中可以嵌入 MemoryStateBackend 或 FsStateBackend。实际上，RocksDBStateBackend 里面嵌入的 StateBackend，只是描述的是其内部 Checkpoint 数据传输方向。

> 上述 RocksDBStateBackend 示例中，很多人可能会认为 RocksDB 会直接与 S3 操作，但实际上 RocksDB 会将数据存储在本地磁盘上并将 Checkpoint 存储到 S3。

对于 MemoryStateBackend，在原始构建下未指定任何的文件路径，且在不开启 HA 的模式下，会将所有 Checkpoint 数据返回给 JobManager。当 MemoryStateBackend 指定文件路径时，Checkpoint 数据直接上传到指定文件路径下，数据内容不会返回给 JobManager。对于 FsStateBackend，数据会直接上传到所定义的文件路径下。当然，大家线上用的最多的还是 RocksDBStateBackend 搭配上一个远程 fs 地址，旧的写法对于使用 Flink 的用户来说，容易造成状态和 Checkpoint 理解混乱。

## 3. 重构拆分

为了解决这种混乱的问题，Flink 1.13 提供更容易理解的名字以及将之前 StateBackend 的两个功能拆分开，如下图所示：
- StateBackend 的概念变窄，只描述状态访问和存储，定义状态在 TM 本地存储的位置和方式。
- CheckpointStorage 描述了 Checkpoint 行为，定义 Checkpoint 的存储位置和方式以进行故障恢复。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/disentangle-statebackends-from-checkpointing-2.png?raw=true)

### 3.1 功能拆分：CheckpointStorage

我们删除 StateBackend 接口中 Checkpoint 存储相关的方法，并将它们放入一个新接口 CheckpointStorage 中，如下图所示。Flink 运行时当前会包含一个名为 CheckpointStorage 的内部接口：
```java
public interface CheckpointStorage extends java.io.Serializable {
  CompletedCheckpointStorageLocation resolveCheckpoint(String externalPointer);
  CheckpointStorageAccess createCheckpointStorage(JobID jobId);
}
```
Flink 会提供两个默认实现：JobManagerCheckpointStorage 和 FileSystemCheckpointStorage。JobManagerCheckpointStorage 和 FileSystemCheckpointStorage 会保持与 MemoryStateBackend 和 FsStateBackend 中实现的相同功能。这意味着 JobManagerCheckpointStorage 是基于现有的 MemoryBackendCheckpointStorageAccess 实现，而 FileSystemCheckpointStorage 是基于现有的 FsCheckpointStorageAccess 实现。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/disentangle-statebackends-from-checkpointing-4.png?raw=true)

### 3.2 重新命名：新 StateBackend API

为了更好的理解我们重新命名，弃用了 MemoryStateBackend、FsStateBackend 和 RocksDBStateBackend 类。StateBackend 的状态存储功能使用 HashMapStateBackend 和 EmbeddedRocksDBStateBackend 代替，Checkpoint 持久化功能使用 FileSystemCheckpointStorage 和 JobManagerCheckpointStorage 来代替。需要明确的是，我们不会更改任何运行时数据结构或特征，这些只是面向用户的新 API。当前不仅需要指定 StateBackend ，还需要指定 CheckpointStorage，如下是重构后使用的几种方式：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new HashMapStateBackend())

EmbeddedRocksDBStateBackend rocksDB = new EmbeddedRocksDBStateBackend();
rocksDB.setOptionsFactory(/** blah **/);

env.setStateBackend(rocksDB);
env.setDefaultSavepointDirectory("s3://savepoint");

env.getCheckpointConfig().setCheckpointStorage(new JobManagerCheckpointStorage());
env.getCheckpointConfig().setCheckpointStorage(new FileSystemCheckpointStorage("s3://checkpoints"));

// shortcut for env.getCheckpointConfig().setCheckpointStorage(new FileSystemCheckpointStorage("s3://checkpoints"));
env.getCheckpointConfig().setCheckpointStorage("s3://checkpoints");
```
默认的 StateBackend 为 HashMapStateBackend，默认的 Checkpoint 存储为 JobManagerCheckpointStorage。这相当于之前的默认 MemoryStateBackend 语义。

## 4. 迁移

> 虽然旧接口目前仍然保存，但还是推荐大家使用新接口，向新方式迁移，从概念上也更清晰一些。

三个现有的状态后端：MemoryStateBackend、FsStateBackend 和 RocksDBStateBackend 在 1.13 版本中被弃用以支持新类。下面我会指导如何以兼容的方式迁移到新的 API 上。因为使用相同的内部数据结构，我们能够轻松迁移到新 API。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/disentangle-statebackends-from-checkpointing-5.png?raw=true)

### 4.1 MemoryStateBackend

旧版本的 MemoryStateBackend 等价于使用 HashMapStateBackend 和 JobManagerCheckpointStorage。

(1) flink-conf.yaml 配置：
```
state.backend: hashmap
# 可选，当不指定 checkpoint 路径时，默认自动使用 JobManagerCheckpointStorage
state.checkpoint-storage: jobmanager
```
(2) 代码配置
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new HashMapStateBackend());
env.getCheckpointConfig().setCheckpointStorage(new JobManagerStateBackend());
```
### 4.2 FsStateBackend

旧版本的 FsStateBackend 等价于使用 HashMapStateBackend 和 FileSystemCheckpointStorage。

(1) flink-conf.yaml 配置：
```
state.backend: hashmap
state.checkpoints.dir: file:///checkpoint-dir/

# 可选，当指定 checkpoint 路径时，默认自动使用 FileSystemCheckpointStorage
state.checkpoint-storage: filesystem
```
(2) 代码配置：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new HashMapStateBackend());
env.getCheckpointConfig().setCheckpointStorage("file:///checkpoint-dir");

// Advanced FsStateBackend configurations, such as write buffer size
// can be set by manually instantiating a FileSystemCheckpointStorage object.
env.getCheckpointConfig().setCheckpointStorage(new FileSystemCheckpointStorage("file:///checkpoint-dir"));
```

### 4.3 RocksDBStateBackend

旧版本的 RocksDBStateBackend 等价于使用 EmbeddedRocksDBStateBackend 和 FileSystemCheckpointStorage。

(1) flink-conf.yaml 配置：
```
state.backend: rocksdb
state.checkpoints.dir: file:///checkpoint-dir/

# 可选，当指定 checkpoint 路径时，默认自动使用 FileSystemCheckpointStorage
state.checkpoint-storage: filesystem
```
(2) 代码配置：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new EmbeddedRocksDBStateBackend());
env.getCheckpointConfig().setCheckpointStorage("file:///checkpoint-dir");

// If you manually passed FsStateBackend into the RocksDBStateBackend constructor
// to specify advanced checkpointing configurations such as write buffer size,
// you can achieve the same results by using manually instantiating a FileSystemCheckpointStorage object.
env.getCheckpointConfig().setCheckpointStorage(new FileSystemCheckpointStorage("file:///checkpoint-dir"));
```

参考：
- [FLIP-142: Disentangle StateBackends from Checkpointing](https://cwiki.apache.org/confluence/display/FLINK/FLIP-142%3A+Disentangle+StateBackends+from+Checkpointing)
- [Flink 1.13，State Backend 优化及生产实践分享](https://mp.weixin.qq.com/s/zXdOCqtVv_7iNFngLs44dA)
