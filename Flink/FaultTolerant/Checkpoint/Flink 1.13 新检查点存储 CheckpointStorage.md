在 Flink 1.13 版本之前，StateBackend 提供了三个开箱即用的 StateBackend：MemoryStateBackend、FsStateBackend 以及 RocksDBStateBackend。该版本下的 StateBackend 把状态存储(如何在 TM 上本地存储和访问状态)和 Checkpoint 持久化(Checkpoint 如何持久化状态)笼统的混在一起，导致初学者对此感觉很混乱，很难理解。

为了解决这种混乱的问题，Flink 1.13 版本将之前的 StateBackend 拆分成新的 StateBackend 和 CheckpointStorage 两个功能：
- 新的 StateBackend 的概念变窄，只描述状态访问和存储，定义状态在 TM 本地存储的位置和方式。
- CheckpointStorage 描述了 Checkpoint 行为，定义 Checkpoint 的存储位置和方式以进行故障恢复。

为了更好的理解，我们弃用了老的 MemoryStateBackend、FsStateBackend 和 RocksDBStateBackend。StateBackend 的状态存储功能使用 HashMapStateBackend 和 EmbeddedRocksDBStateBackend 代替，Checkpoint 持久化功能使用 FileSystemCheckpointStorage 和 JobManagerCheckpointStorage 来代替。
> 详细请查阅[Flink 1.13 StateBackend 与 CheckpointStorage 拆分](https://smartsi.blog.csdn.net/article/details/123057769)

在这篇文章中我们重点介绍新版本的 StateBackend。Flink 中提供了两种不同的实现，一种是 FileSystemCheckpointStorage，另一种是 JobManagerCheckpointStorage。如果没有特别配置，系统默认是 JobManagerCheckpointStorage。


```java
// 设置Checkpoint存储
env.enableCheckpointing(1000L);
FileSystemCheckpointStorage checkpointStorage = new FileSystemCheckpointStorage("hdfs://localhost:9000/flink/checkpoint");
env.getCheckpointConfig().setCheckpointStorage(checkpointStorage);
```
