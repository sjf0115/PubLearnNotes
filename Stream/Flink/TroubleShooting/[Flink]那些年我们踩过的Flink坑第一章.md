---
layout: post
author: smartsi
title: 那些年我们踩过的Flink坑第一章
date: 2020-12-26 08:16:17
tags:
  - Flink

categories: Flink
permalink: flink-trouble-shooting-one
---

### 1. Could not start rest endpoint

【现象】启动集群报如下错误：
```java
2020-10-31 23:07:13,961 ERROR org.apache.flink.runtime.entrypoint.ClusterEntrypoint        [] - Could not start cluster entrypoint StandaloneSessionClusterEntrypoint.
org.apache.flink.runtime.entrypoint.ClusterEntrypointException: Failed to initialize the cluster entrypoint StandaloneSessionClusterEntrypoint.
        at org.apache.flink.runtime.entrypoint.ClusterEntrypoint.startCluster(ClusterEntrypoint.java:190) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.ClusterEntrypoint.runClusterEntrypoint(ClusterEntrypoint.java:520) [flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.StandaloneSessionClusterEntrypoint.main(StandaloneSessionClusterEntrypoint.java:64) [flink-dist_2.12-1.11.2.jar:1.11.2]
Caused by: org.apache.flink.util.FlinkException: Could not create the DispatcherResourceManagerComponent.
        at org.apache.flink.runtime.entrypoint.component.DefaultDispatcherResourceManagerComponentFactory.create(DefaultDispatcherResourceManagerComponentFactory.java:255) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.ClusterEntrypoint.runCluster(ClusterEntrypoint.java:219) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.ClusterEntrypoint.lambda$startCluster$0(ClusterEntrypoint.java:172) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.security.contexts.NoOpSecurityContext.runSecured(NoOpSecurityContext.java:30) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.ClusterEntrypoint.startCluster(ClusterEntrypoint.java:171) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        ... 2 more
Caused by: java.net.BindException: Could not start rest endpoint on any port in port range 8081
        at org.apache.flink.runtime.rest.RestServerEndpoint.start(RestServerEndpoint.java:222) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.component.DefaultDispatcherResourceManagerComponentFactory.create(DefaultDispatcherResourceManagerComponentFactory.java:163) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.ClusterEntrypoint.runCluster(ClusterEntrypoint.java:219) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.ClusterEntrypoint.lambda$startCluster$0(ClusterEntrypoint.java:172) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.security.contexts.NoOpSecurityContext.runSecured(NoOpSecurityContext.java:30) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        at org.apache.flink.runtime.entrypoint.ClusterEntrypoint.startCluster(ClusterEntrypoint.java:171) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
        ... 2 more
```
【解决方案】端口冲突，修改默认端口。从错误信息中可以发现是端口被占用问题，修改配置文件 flink-conf.yaml 中的默认端口：
```
# The port to which the REST client connects to. If rest.bind-port has
# not been specified, then the server will bind to this port as well.
#
#rest.port: 8081
rest.port: 8090
```

### 2. Could not find a file system implementation for scheme 'hdfs'

【现象】启动Flink集群的时候报如下错误：
```
Caused by: org.apache.flink.core.fs.UnsupportedFileSystemSchemeException: Could not find a file system implementation for scheme 'hdfs'. The scheme is not directly supported by Flink and no Hadoop file system to support this scheme could be loaded. For a full list of supported file systems, please see https://ci.apache.org/projects/flink/flink-docs-stable/ops/filesystems/.
	at org.apache.flink.core.fs.FileSystem.getUnguardedFileSystem(FileSystem.java:491)
	at org.apache.flink.core.fs.FileSystem.get(FileSystem.java:389)
	at org.apache.flink.core.fs.Path.getFileSystem(Path.java:292)
	at org.apache.flink.runtime.state.filesystem.FsCheckpointStorage.<init>(FsCheckpointStorage.java:64)
	at org.apache.flink.runtime.state.filesystem.FsStateBackend.createCheckpointStorage(FsStateBackend.java:501)
	at org.apache.flink.runtime.checkpoint.CheckpointCoordinator.<init>(CheckpointCoordinator.java:302)
	... 22 more
Caused by: org.apache.flink.core.fs.UnsupportedFileSystemSchemeException: Hadoop is not in the classpath/dependencies.
	at org.apache.flink.core.fs.UnsupportedSchemeFactory.create(UnsupportedSchemeFactory.java:58)
	at org.apache.flink.core.fs.FileSystem.getUnguardedFileSystem(FileSystem.java:487)
	... 27 more
```
【解决方案】需要添加如下环境变量：
```
export HADOOP_CLASSPATH=`hadoop classpath`
```
> 修改 /etc/profile 配置文件，使用 source 命令并刷新

### 3. No ExecutorFactory found to execute the application

【现象】Idea中启动程序报如下错误：
```java
Exception in thread "main" java.lang.IllegalStateException: No ExecutorFactory found to execute the application.
	at org.apache.flink.core.execution.DefaultExecutorServiceLoader.getExecutorFactory(DefaultExecutorServiceLoader.java:84)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.executeAsync(StreamExecutionEnvironment.java:1801)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1711)
	at org.apache.flink.streaming.api.environment.LocalStreamEnvironment.execute(LocalStreamEnvironment.java:74)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1697)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1679)
	at com.flink.example.stream.state.savepoint.SavepointExample.main(SavepointExample.java:36)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
```
【解决方案】添加如下依赖：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-clients_${scala.binary.version}</artifactId>
    <version>${flink.version}</version>
</dependency>
```
从 Flink 1.11.0 版本开始，flink-streaming-java 模块不再依赖 flink-clients。如果我们的项目对 flink-clients 有依赖，需要手动添加 flink-clients 依赖项。
> 具体参阅:[Reversed dependency from flink-streaming-java to flink-client](https://ci.apache.org/projects/flink/flink-docs-master/release-notes/flink-1.11.html#reversed-dependency-from-flink-streaming-java-to-flink-client-flink-15090)

### 4. Hadoop is not in the classpath/dependencies

【现象】在Idea中启动程序报如下错误：
```java
Caused by: org.apache.flink.core.fs.UnsupportedFileSystemSchemeException: Could not find a file system implementation for scheme 'hdfs'. The scheme is not directly supported by Flink and no Hadoop file system to support this scheme could be loaded. For a full list of supported file systems, please see https://ci.apache.org/projects/flink/flink-docs-stable/ops/filesystems/.
	at org.apache.flink.core.fs.FileSystem.getUnguardedFileSystem(FileSystem.java:491)
	at org.apache.flink.core.fs.FileSystem.get(FileSystem.java:389)
	at org.apache.flink.core.fs.Path.getFileSystem(Path.java:292)
	at org.apache.flink.runtime.state.filesystem.FsCheckpointStorage.<init>(FsCheckpointStorage.java:64)
	at org.apache.flink.runtime.state.filesystem.FsStateBackend.createCheckpointStorage(FsStateBackend.java:501)
	at org.apache.flink.runtime.checkpoint.CheckpointCoordinator.<init>(CheckpointCoordinator.java:302)
	... 22 more
Caused by: org.apache.flink.core.fs.UnsupportedFileSystemSchemeException: Hadoop is not in the classpath/dependencies.
	at org.apache.flink.core.fs.UnsupportedSchemeFactory.create(UnsupportedSchemeFactory.java:58)
	at org.apache.flink.core.fs.FileSystem.getUnguardedFileSystem(FileSystem.java:487)
	... 27 more
```
【解决方案】添加如下依赖：
```xml
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-client</artifactId>
    <version>${hadoop.version}</version>
    <scope>provided</scope>
</dependency>
```

### 5. ctx.timestamp() is null

【现象】在使用 ProcessFunction 的时候报如下错误：
```java
java.lang.NullPointerException: null
	at com.flink.example.stream.function.KeyedProcessFunctionExample$MyKeyedProcessFunction.processElement(KeyedProcessFunctionExample.java:100) ~[blob_p-92c7e7e29847aa931e056c2af61ded61872e86e5-eb163730b1bcc759f3ea79f21ff92551:?]
	at com.flink.example.stream.function.KeyedProcessFunctionExample$MyKeyedProcessFunction.processElement(KeyedProcessFunctionExample.java:59) ~[blob_p-92c7e7e29847aa931e056c2af61ded61872e86e5-eb163730b1bcc759f3ea79f21ff92551:?]
	at org.apache.flink.streaming.api.operators.KeyedProcessOperator.processElement(KeyedProcessOperator.java:85) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.OneInputStreamTask$StreamTaskNetworkOutput.emitRecord(OneInputStreamTask.java:161) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.io.StreamTaskNetworkInput.processElement(StreamTaskNetworkInput.java:178) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.io.StreamTaskNetworkInput.emitNext(StreamTaskNetworkInput.java:153) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.io.StreamOneInputProcessor.processInput(StreamOneInputProcessor.java:67) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.processInput(StreamTask.java:351) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.runMailboxStep(MailboxProcessor.java:191) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.runMailboxLoop(MailboxProcessor.java:181) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runMailboxLoop(StreamTask.java:566) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.invoke(StreamTask.java:536) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:721) [flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:546) [flink-dist_2.12-1.11.2.jar:1.11.2]
	at java.lang.Thread.run(Thread.java:748) [?:1.8.0_161]
```
【解决方案】
根据代码行数发现根本问题是 ctx.timestamp() 为 NULL，导致注册 Timer 时候抛出空指针异常。出现该问题的原因是：
- 如果使用处理时间，ctx.timestamp() 为 null，可以使用系统时间戳 System.currentTimeMillis()。
- 如果使用事件时间，可能是因为我们没有设置事件时间戳提取以及生成 Watermark。需要添加如下代码：
```java
// 如果使用事件时间必须设置Timestamp提取和Watermark生成 否则下游 ctx.timestamp() 为null
.assignTimestampsAndWatermarks(
        WatermarkStrategy.<Tuple2<String, Long>>forBoundedOutOfOrderness(Duration.ofSeconds(10))
        .withTimestampAssigner(new SerializableTimestampAssigner<Tuple2<String, Long>>() {
            @Override
            public long extractTimestamp(Tuple2<String, Long> element, long recordTimestamp) {
                return element.f1;
            }
        })
)
```
### 6. The parallelism of non parallel operator must be 1

```java
env.socketTextStream("localhost", 9100, "\n").setParallelism(2)
  .forward()
  .map(str -> str.toUpperCase()).setParallelism(3);
```
【现象】运行如上代码时，抛出如下异常：
```java
Caused by: java.lang.IllegalArgumentException: The parallelism of non parallel operator must be 1.
	at org.apache.flink.util.Preconditions.checkArgument(Preconditions.java:139)
	at org.apache.flink.api.common.operators.util.OperatorValidationUtils.validateParallelism(OperatorValidationUtils.java:38)
	at org.apache.flink.streaming.api.datastream.DataStreamSource.setParallelism(DataStreamSource.java:85)
	at com.flink.example.stream.partitioner.ForwardPartitionerExample.main(ForwardPartitionerExample.java:19)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.flink.client.program.PackagedProgram.callMainMethod(PackagedProgram.java:288)
	... 11 more
```
【解决方案】socketTextStream 实现的 Source 是继承的 SourceFunction。SourceFunction 是不支持通过 setParallelism() 方法设置大于1的并行度，默认的并行度为1，否则会报上面的错误。

### 7. Forward partitioning does not allow change of parallelism

```java
// ForwardPartitioner
env.socketTextStream("localhost", 9100, "\n")
        .map(str -> str.toLowerCase()).name("LowerCaseMap").setParallelism(2)
        .forward()
        .map(str -> str.toUpperCase()).name("UpperCaseMap").setParallelism(3);
```
【现象】在运行如上代码时，抛出如下异常：
```java
Caused by: java.lang.UnsupportedOperationException: Forward partitioning does not allow change of parallelism. Upstream operation: LowerCaseMap-2 parallelism: 2, downstream operation: UpperCaseMap-4 parallelism: 3 You must use another partitioning strategy, such as broadcast, rebalance, shuffle or global.
	at org.apache.flink.streaming.api.graph.StreamGraph.addEdgeInternal(StreamGraph.java:561)
	at org.apache.flink.streaming.api.graph.StreamGraph.addEdgeInternal(StreamGraph.java:544)
	at org.apache.flink.streaming.api.graph.StreamGraph.addEdge(StreamGraph.java:504)
	at org.apache.flink.streaming.api.graph.StreamGraphGenerator.transformOneInputTransform(StreamGraphGenerator.java:696)
	at org.apache.flink.streaming.api.graph.StreamGraphGenerator.transform(StreamGraphGenerator.java:250)
	at org.apache.flink.streaming.api.graph.StreamGraphGenerator.generate(StreamGraphGenerator.java:209)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.getStreamGraph(StreamExecutionEnvironment.java:1861)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.getStreamGraph(StreamExecutionEnvironment.java:1846)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1697)
	at com.flink.example.stream.partitioner.ForwardPartitionerExample.main(ForwardPartitionerExample.java:24)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.flink.client.program.PackagedProgram.callMainMethod(PackagedProgram.java:288)
	... 11 more
```
【解决方案】使用 ForwardPartitioner 时必须保证上下游算子的并行度保持一致，否则就需要其他的分区器，比如，BroadcastPartitioner、ShufflePartitioner 或者 RebalancePartitioner 等。

### 8. cannot assign instance of org.apache.commons.collections.map.LinkedMap

【现象】在使用 Flink 消费 Kafka 时，抛出如下异常：
```java
Caused by: java.lang.ClassCastException: cannot assign instance of org.apache.commons.collections.map.LinkedMap to field org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumerBase.pendingOffsetsToCommit of type org.apache.commons.collections.map.LinkedMap in instance of org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer
	at java.io.ObjectStreamClass$FieldReflector.setObjFieldValues(ObjectStreamClass.java:2233)
	at java.io.ObjectStreamClass.setObjFieldValues(ObjectStreamClass.java:1405)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2284)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2202)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2060)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1567)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2278)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2202)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2060)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1567)
	at java.io.ObjectInputStream.defaultReadFields(ObjectInputStream.java:2278)
	at java.io.ObjectInputStream.readSerialData(ObjectInputStream.java:2202)
	at java.io.ObjectInputStream.readOrdinaryObject(ObjectInputStream.java:2060)
	at java.io.ObjectInputStream.readObject0(ObjectInputStream.java:1567)
	at java.io.ObjectInputStream.readObject(ObjectInputStream.java:427)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:615)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:600)
	at org.apache.flink.util.InstantiationUtil.deserializeObject(InstantiationUtil.java:587)
	at org.apache.flink.util.InstantiationUtil.readObjectFromConfig(InstantiationUtil.java:541)
	at org.apache.flink.streaming.api.graph.StreamConfig.getStreamOperatorFactory(StreamConfig.java:322)
	... 5 more
```
【解决方案】常见的原因是 Kafka 库与 Flink 的反向类加载方法不兼容。可以通过在 conf/flink-conf.yaml 中添加以下配置并重新启动 Flink 来解决此问题：
```
classloader.resolve-order: parent-first
```
...
