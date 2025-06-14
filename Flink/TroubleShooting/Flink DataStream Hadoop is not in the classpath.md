
## 1. 问题

在本地 Idea 上运行 Flink 程序，抛出如下异常：
```java
Exception in thread "main" org.apache.flink.util.FlinkException: Failed to execute job 'StateBackendExample'.
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.executeAsync(StreamExecutionEnvironment.java:1918)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1796)
	at org.apache.flink.streaming.api.environment.LocalStreamEnvironment.execute(LocalStreamEnvironment.java:69)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1782)
  ...
Caused by: org.apache.flink.runtime.client.JobInitializationException: Could not instantiate JobManager.
  ...
	at java.lang.Thread.run(Thread.java:748)
Caused by: org.apache.flink.util.FlinkRuntimeException: Failed to create checkpoint storage at checkpoint coordinator side.
  ...
	at org.apache.flink.runtime.jobmaster.factories.DefaultJobMasterServiceFactory.createJobMasterService(DefaultJobMasterServiceFactory.java:39)
	at org.apache.flink.runtime.jobmaster.JobManagerRunnerImpl.<init>(JobManagerRunnerImpl.java:162)
	at org.apache.flink.runtime.dispatcher.DefaultJobManagerRunnerFactory.createJobManagerRunner(DefaultJobManagerRunnerFactory.java:86)
	at org.apache.flink.runtime.dispatcher.Dispatcher.lambda$createJobManagerRunner$5(Dispatcher.java:478)
	... 4 more
Caused by: org.apache.flink.core.fs.UnsupportedFileSystemSchemeException: Could not find a file system implementation for scheme 'hdfs'. The scheme is not directly supported by Flink and no Hadoop file system to support this scheme could be loaded. For a full list of supported file systems, please see https://ci.apache.org/projects/flink/flink-docs-stable/ops/filesystems/.
	at org.apache.flink.core.fs.FileSystem.getUnguardedFileSystem(FileSystem.java:531)
	at org.apache.flink.core.fs.FileSystem.get(FileSystem.java:408)
	at org.apache.flink.core.fs.Path.getFileSystem(Path.java:274)
	at org.apache.flink.runtime.state.filesystem.FsCheckpointStorageAccess.<init>(FsCheckpointStorageAccess.java:64)
	at org.apache.flink.runtime.state.filesystem.FsStateBackend.createCheckpointStorage(FsStateBackend.java:518)
	at org.apache.flink.contrib.streaming.state.RocksDBStateBackend.createCheckpointStorage(RocksDBStateBackend.java:476)
	at org.apache.flink.runtime.checkpoint.CheckpointCoordinator.<init>(CheckpointCoordinator.java:330)
	... 19 more
Caused by: org.apache.flink.core.fs.UnsupportedFileSystemSchemeException: Hadoop is not in the classpath/dependencies.
	at org.apache.flink.core.fs.UnsupportedSchemeFactory.create(UnsupportedSchemeFactory.java:55)
	at org.apache.flink.core.fs.FileSystem.getUnguardedFileSystem(FileSystem.java:527)
	... 25 more

Process finished with exit code 1
```

## 2. 解决方案

核心原因：Flink 本身不直接支持 HDFS 文件系统，需通过 Hadoop 客户端库实现。当代码中使用 HDFS 路径（如 Checkpoint 存储位置）但未添加 Hadoop 依赖时，Flink 无法加载 HDFS 文件系统实现。

解决方案是在 Maven 项目的 pom.xml 中添加 Hadoop 客户端依赖（版本需与集群一致）：
```xml
<dependency>
  <groupId>org.apache.hadoop</groupId>
  <artifactId>hadoop-client</artifactId>
  <version>2.10.1</version>
  <scope>provided</scope>
</dependency>
```
