
> Flink 1.13.5

## 1. 问题

在运行如下 Flink SQL 时发现 Checkpoint 失败：
```sql
INSERT INTO order_cnt
SELECT
  uid, COUNT(*) AS cnt
FROM order_behavior
GROUP BY uid
```

查看运行日志发现抛出如下异常：
```java
java.util.concurrent.ExecutionException: java.io.IOException: Size of the state is larger than the maximum permitted memory-backed state. Size=6150807, maxSize=5242880. Consider using a different checkpoint storage, like the FileSystemCheckpointStorage.
	at java.util.concurrent.FutureTask.report(FutureTask.java:122) ~[?:1.8.0_161]
	at java.util.concurrent.FutureTask.get(FutureTask.java:192) ~[?:1.8.0_161]
	at org.apache.flink.runtime.concurrent.FutureUtils.runIfNotDoneAndGet(FutureUtils.java:636) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.OperatorSnapshotFinalizer.<init>(OperatorSnapshotFinalizer.java:54) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.AsyncCheckpointRunnable.run(AsyncCheckpointRunnable.java:128) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149) [?:1.8.0_161]
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624) [?:1.8.0_161]
	at java.lang.Thread.run(Thread.java:748) [?:1.8.0_161]
Caused by: java.io.IOException: Size of the state is larger than the maximum permitted memory-backed state. Size=6150807, maxSize=5242880. Consider using a different checkpoint storage, like the FileSystemCheckpointStorage.
	at org.apache.flink.runtime.state.memory.MemCheckpointStreamFactory.checkSize(MemCheckpointStreamFactory.java:63) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.memory.MemCheckpointStreamFactory$MemoryCheckpointOutputStream.closeAndGetBytes(MemCheckpointStreamFactory.java:140) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.memory.MemCheckpointStreamFactory$MemoryCheckpointOutputStream.closeAndGetHandle(MemCheckpointStreamFactory.java:120) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.CheckpointStreamWithResultProvider$PrimaryStreamOnly.closeAndFinalizeCheckpointStreamResult(CheckpointStreamWithResultProvider.java:75) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.heap.HeapSnapshotStrategy.lambda$asyncSnapshot$3(HeapSnapshotStrategy.java:177) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.SnapshotStrategyRunner$1.callInternal(SnapshotStrategyRunner.java:91) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.SnapshotStrategyRunner$1.callInternal(SnapshotStrategyRunner.java:88) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.AsyncSnapshotCallable.call(AsyncSnapshotCallable.java:78) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at java.util.concurrent.FutureTask.run(FutureTask.java:266) ~[?:1.8.0_161]
	at org.apache.flink.runtime.concurrent.FutureUtils.runIfNotDoneAndGet(FutureUtils.java:633) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	... 5 more
```

## 2. 解决方案

错误日志提示已经很明显，状态大小超过 Checkpoint 持久化存储默认最大值。由于代码中没有指定 CheckpointStorage，因此默认使用 JobManagerCheckpointStorage 存储在内存中，默认大小为 5MB。日志中建议切换到 FileSystemCheckpointStorage 中。如下所示使用 FileSystemCheckpointStorage：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setStateBackend(new HashMapStateBackend());
String checkpointPath = "hdfs://localhost:9000/flink/checkpoint";
env.getCheckpointConfig().setCheckpointStorage(new FileSystemCheckpointStorage(checkpointPath));
```

> 注意的是 Flink 1.13 版本将之前的 StateBackend 拆分成新的 StateBackend 和 CheckpointStorage 两个功能。详细请查阅 [Flink 1.13 新版状态后端 StateBackend 详解](https://smartsi.blog.csdn.net/article/details/127118745)


。。
