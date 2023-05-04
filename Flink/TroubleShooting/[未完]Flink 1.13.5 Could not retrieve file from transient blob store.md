```java
java.util.concurrent.CompletionException: org.apache.flink.util.FlinkException: Could not retrieve file from transient blob store.
	at org.apache.flink.runtime.rest.handler.taskmanager.AbstractTaskManagerFileHandler.lambda$respondToRequest$0(AbstractTaskManagerFileHandler.java:138) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at java.util.concurrent.CompletableFuture.uniAccept(CompletableFuture.java:656) [?:1.8.0_161]
	at java.util.concurrent.CompletableFuture$UniAccept.tryFire(CompletableFuture.java:632) [?:1.8.0_161]
	at java.util.concurrent.CompletableFuture$Completion.run(CompletableFuture.java:442) [?:1.8.0_161]
	at org.apache.flink.shaded.netty4.io.netty.util.concurrent.AbstractEventExecutor.safeExecute(AbstractEventExecutor.java:164) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.shaded.netty4.io.netty.util.concurrent.SingleThreadEventExecutor.runAllTasks(SingleThreadEventExecutor.java:472) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.shaded.netty4.io.netty.channel.nio.NioEventLoop.run(NioEventLoop.java:500) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.shaded.netty4.io.netty.util.concurrent.SingleThreadEventExecutor$4.run(SingleThreadEventExecutor.java:989) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.shaded.netty4.io.netty.util.internal.ThreadExecutorMap$2.run(ThreadExecutorMap.java:74) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at java.lang.Thread.run(Thread.java:748) [?:1.8.0_161]
Caused by: org.apache.flink.util.FlinkException: Could not retrieve file from transient blob store.
	... 10 more
Caused by: java.io.FileNotFoundException: Local file /var/folders/54/crgqfp1n52s6560cqcjp7y9h0000gn/T/blobStore-9ffd5a51-18b7-42bb-b9ff-025abc035761/no_job/blob_t-98fd6bb66be9d3b8f46bc6de7a992db25b092898-491a1cea0360d8d111d4074923ab8fd0 does not exist and failed to copy from blob store.
	at org.apache.flink.runtime.blob.BlobServer.getFileInternal(BlobServer.java:504) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.blob.BlobServer.getFileInternal(BlobServer.java:433) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.blob.BlobServer.getFile(BlobServer.java:374) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.rest.handler.taskmanager.AbstractTaskManagerFileHandler.lambda$respondToRequest$0(AbstractTaskManagerFileHandler.java:136) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	... 9 more
2022-07-30 14:41:40,641 ERROR org.apache.flink.runtime.rest.handler.taskmanager.TaskManagerLogFileHandler [] - Unhandled exception.
org.apache.flink.util.FlinkException: Could not retrieve file from transient blob store.
	at org.apache.flink.runtime.rest.handler.taskmanager.AbstractTaskManagerFileHandler.lambda$respondToRequest$0(AbstractTaskManagerFileHandler.java:138) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at java.util.concurrent.CompletableFuture.uniAccept(CompletableFuture.java:656) [?:1.8.0_161]
	at java.util.concurrent.CompletableFuture$UniAccept.tryFire(CompletableFuture.java:632) [?:1.8.0_161]
	at java.util.concurrent.CompletableFuture$Completion.run(CompletableFuture.java:442) [?:1.8.0_161]
	at org.apache.flink.shaded.netty4.io.netty.util.concurrent.AbstractEventExecutor.safeExecute(AbstractEventExecutor.java:164) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.shaded.netty4.io.netty.util.concurrent.SingleThreadEventExecutor.runAllTasks(SingleThreadEventExecutor.java:472) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.shaded.netty4.io.netty.channel.nio.NioEventLoop.run(NioEventLoop.java:500) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.shaded.netty4.io.netty.util.concurrent.SingleThreadEventExecutor$4.run(SingleThreadEventExecutor.java:989) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.shaded.netty4.io.netty.util.internal.ThreadExecutorMap$2.run(ThreadExecutorMap.java:74) [flink-dist_2.11-1.13.5.jar:1.13.5]
	at java.lang.Thread.run(Thread.java:748) [?:1.8.0_161]
Caused by: java.io.FileNotFoundException: Local file /var/folders/54/crgqfp1n52s6560cqcjp7y9h0000gn/T/blobStore-9ffd5a51-18b7-42bb-b9ff-025abc035761/no_job/blob_t-98fd6bb66be9d3b8f46bc6de7a992db25b092898-491a1cea0360d8d111d4074923ab8fd0 does not exist and failed to copy from blob store.
	at org.apache.flink.runtime.blob.BlobServer.getFileInternal(BlobServer.java:504) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.blob.BlobServer.getFileInternal(BlobServer.java:433) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.blob.BlobServer.getFile(BlobServer.java:374) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.rest.handler.taskmanager.AbstractTaskManagerFileHandler.lambda$respondToRequest$0(AbstractTaskManagerFileHandler.java:136) ~[flink-dist_2.11-1.13.5.jar:1.13.5]
	... 9 more
```
https://blog.csdn.net/qq_41768325/article/details/121081717
