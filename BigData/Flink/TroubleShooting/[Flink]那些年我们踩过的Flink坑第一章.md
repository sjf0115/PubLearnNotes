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

...
