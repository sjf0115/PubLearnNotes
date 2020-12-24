### 1. YarnException

```
smartsi:flink smartsi$ ./bin/yarn-session.sh -n 3  -jm 2048  -tm 8192 -s 8
Error: A JNI error has occurred, please check your installation and try again
Exception in thread "main" java.lang.NoClassDefFoundError: org/apache/hadoop/yarn/exceptions/YarnException
	at java.lang.Class.getDeclaredMethods0(Native Method)
	at java.lang.Class.privateGetDeclaredMethods(Class.java:2701)
	at java.lang.Class.privateGetMethodRecursive(Class.java:3048)
	at java.lang.Class.getMethod0(Class.java:3018)
	at java.lang.Class.getMethod(Class.java:1784)
	at sun.launcher.LauncherHelper.validateMainClass(LauncherHelper.java:544)
	at sun.launcher.LauncherHelper.checkAndLoadMain(LauncherHelper.java:526)
Caused by: java.lang.ClassNotFoundException: org.apache.hadoop.yarn.exceptions.YarnException
	at java.net.URLClassLoader.findClass(URLClassLoader.java:381)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:349)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:357)
	... 7 more
```



### 1.

```
org.apache.flink.client.program.ProgramInvocationException: The program execution failed: Could not upload the jar files to the job manager.
	at org.apache.flink.client.program.ClusterClient.run(ClusterClient.java:478)
	at org.apache.flink.client.program.StandaloneClusterClient.submitJob(StandaloneClusterClient.java:105)
	at org.apache.flink.client.program.ClusterClient.run(ClusterClient.java:442)
	at org.apache.flink.streaming.api.environment.StreamContextEnvironment.execute(StreamContextEnvironment.java:73)
	at com.qunar.mobile.flink.stream.example.SocketAdvPushParse.main(SocketAdvPushParse.java:41)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.flink.client.program.PackagedProgram.callMainMethod(PackagedProgram.java:528)
	at org.apache.flink.client.program.PackagedProgram.invokeInteractiveModeForExecution(PackagedProgram.java:419)
	at org.apache.flink.client.program.ClusterClient.run(ClusterClient.java:381)
	at org.apache.flink.client.CliFrontend.executeProgram(CliFrontend.java:838)
	at org.apache.flink.client.CliFrontend.run(CliFrontend.java:259)
	at org.apache.flink.client.CliFrontend.parseParameters(CliFrontend.java:1086)
	at org.apache.flink.client.CliFrontend$2.call(CliFrontend.java:1133)
	at org.apache.flink.client.CliFrontend$2.call(CliFrontend.java:1130)
	at org.apache.flink.runtime.security.HadoopSecurityContext$1.run(HadoopSecurityContext.java:43)
	at java.security.AccessController.doPrivileged(Native Method)
	at javax.security.auth.Subject.doAs(Subject.java:422)
	at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1657)
	at org.apache.flink.runtime.security.HadoopSecurityContext.runSecured(HadoopSecurityContext.java:40)
	at org.apache.flink.client.CliFrontend.main(CliFrontend.java:1130)
Caused by: org.apache.flink.runtime.client.JobSubmissionException: Could not upload the jar files to the job manager.
	at org.apache.flink.runtime.client.JobSubmissionClientActor$1.call(JobSubmissionClientActor.java:154)
	at akka.dispatch.Futures$$anonfun$future$1.apply(Future.scala:95)
	at scala.concurrent.impl.Future$PromiseCompletingRunnable.liftedTree1$1(Future.scala:24)
	at scala.concurrent.impl.Future$PromiseCompletingRunnable.run(Future.scala:24)
	at akka.dispatch.TaskInvocation.run(AbstractDispatcher.scala:40)
	at akka.dispatch.ForkJoinExecutorConfigurator$AkkaForkJoinTask.exec(AbstractDispatcher.scala:397)
	at scala.concurrent.forkjoin.ForkJoinTask.doExec(ForkJoinTask.java:260)
	at scala.concurrent.forkjoin.ForkJoinPool$WorkQueue.runTask(ForkJoinPool.java:1339)
	at scala.concurrent.forkjoin.ForkJoinPool.runWorker(ForkJoinPool.java:1979)
	at scala.concurrent.forkjoin.ForkJoinWorkerThread.run(ForkJoinWorkerThread.java:107)
Caused by: java.io.IOException: Could not retrieve the JobManager's blob port.
	at org.apache.flink.runtime.blob.BlobClient.uploadJarFiles(BlobClient.java:746)
	at org.apache.flink.runtime.jobgraph.JobGraph.uploadUserJars(JobGraph.java:584)
	at org.apache.flink.runtime.client.JobSubmissionClientActor$1.call(JobSubmissionClientActor.java:148)
	... 9 more
Caused by: java.io.IOException: PUT operation failed: Connection reset
	at org.apache.flink.runtime.blob.BlobClient.putInputStream(BlobClient.java:512)
	at org.apache.flink.runtime.blob.BlobClient.put(BlobClient.java:374)
	at org.apache.flink.runtime.blob.BlobClient.uploadJarFiles(BlobClient.java:772)
	at org.apache.flink.runtime.blob.BlobClient.uploadJarFiles(BlobClient.java:741)
	... 11 more
Caused by: java.net.SocketException: Connection reset
	at java.net.SocketOutputStream.socketWrite(SocketOutputStream.java:113)
	at java.net.SocketOutputStream.write(SocketOutputStream.java:153)
	at org.apache.flink.runtime.blob.BlobUtils.writeLength(BlobUtils.java:324)
	at org.apache.flink.runtime.blob.BlobClient.putInputStream(BlobClient.java:498)
	... 14 more
```
### 2. ResultTypeQueryable
```
The return type of function 'MQSource' could not be determined automatically, due to type erasure. You can give type information hints by using the returns(...) method on the result of the transformation call, or by letting your function implement the 'ResultTypeQueryable' interface.
        org.apache.flink.streaming.api.transformations.StreamTransformation.getOutputType(StreamTransformation.java:382)
        org.apache.flink.streaming.api.datastream.DataStream.getType(DataStream.java:174)
        org.apache.flink.streaming.api.datastream.DataStream.map(DataStream.java:528)
        com.xxqg.flink.main.TestStream.main(TestStream.java:57)
```
### 3. No buffer

```
java.lang.Exception: Error while triggering checkpoint 51 for Source: MQSource (1/1)
        at org.apache.flink.runtime.taskmanager.Task$2.run(Task.java:1210)
        at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
        at java.util.concurrent.FutureTask.run(FutureTask.java:266)
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
        at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
        at java.lang.Thread.run(Thread.java:748)
Caused by: java.lang.Exception: Could not perform checkpoint 51 for operator Source: MQSource (1/1).
        at org.apache.flink.streaming.runtime.tasks.StreamTask.triggerCheckpoint(StreamTask.java:544)
        at org.apache.flink.streaming.runtime.tasks.SourceStreamTask.triggerCheckpoint(SourceStreamTask.java:111)
        at org.apache.flink.runtime.taskmanager.Task$2.run(Task.java:1199)
        ... 5 more
Caused by: java.lang.IllegalStateException: No buffer, but serializer has buffered data.
        at org.apache.flink.runtime.io.network.api.writer.RecordWriter.broadcastEvent(RecordWriter.java:152)
        at org.apache.flink.streaming.runtime.io.RecordWriterOutput.broadcastEvent(RecordWriterOutput.java:146)
        at org.apache.flink.streaming.runtime.tasks.OperatorChain.broadcastCheckpointBarrier(OperatorChain.java:182)
        at org.apache.flink.streaming.runtime.tasks.StreamTask.performCheckpoint(StreamTask.java:602)
        at org.apache.flink.streaming.runtime.tasks.StreamTask.triggerCheckpoint(StreamTask.java:538)
        ... 7 more
```

### 4. Could not start rest endpoint

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
看错误信息，发现是端口被占用问题，修改配置文件 flink-conf.yaml 中的默认端口：
```
#==============================================================================
# Rest & web frontend
#==============================================================================

# The port to which the REST client connects to. If rest.bind-port has
# not been specified, then the server will bind to this port as well.
#
#rest.port: 8081
rest.port: 8090
```

### 5. Could not find a file system implementation for scheme 'hdfs'

启动Flink集群的时候报如下错误：
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







...
