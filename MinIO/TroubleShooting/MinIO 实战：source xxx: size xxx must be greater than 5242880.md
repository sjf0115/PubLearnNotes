## 1. 问题

在使用 composeObject 方法合并 Object 时出现如下异常：
```java
Exception in thread "main" java.lang.IllegalArgumentException: source bucket-1/object-1: size 50 must be greater than 5242880
	at io.minio.S3Base.lambda$calculatePartCountAsync$7(S3Base.java:1190)
	at java.util.concurrent.CompletableFuture.biApply(CompletableFuture.java:1119)
	at java.util.concurrent.CompletableFuture$BiApply.tryFire(CompletableFuture.java:1084)
	at java.util.concurrent.CompletableFuture.postComplete(CompletableFuture.java:488)
	at java.util.concurrent.CompletableFuture.complete(CompletableFuture.java:1975)
	at io.minio.S3Base$1.onResponse(S3Base.java:644)
	at okhttp3.internal.connection.RealCall$AsyncCall.run(RealCall.kt:519)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
```

## 2. 分析

```
size 50 must be greater than 5242880
```
5242880 字节 = 5MB（5242880 ÷ 1024 ÷ 1024 = 5MB）。这是 MinIO/S3 API 对 composeObject 操作的一个硬性限制。你正在尝试合并的对象 `bucket-1/object-1` 大小只有 50 字节，但 MinIO 要求源对象的最小大小为 5MB。

MinIO 的 composeObject 方法实际上底层使用的是 S3 的 CopyObject API。每个源对象的最小大小必须 ≥ 5MB（除了最后一个源对象）。这是 AWS S3 规范的一部分，MinIO 遵循了相同的限制。设计目的是为了优化大对象的分块传输和合并性能。
