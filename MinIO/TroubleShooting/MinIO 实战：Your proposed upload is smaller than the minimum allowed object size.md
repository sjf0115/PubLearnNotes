## 1. 问题

```java
Caused by: io.minio.errors.ErrorResponseException: Your proposed upload is smaller than the minimum allowed object size.
	at io.minio.S3Base$1.onResponse(S3Base.java:775)
	at okhttp3.internal.connection.RealCall$AsyncCall.run(RealCall.kt:519)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	... 1 common frames omitted
```

## 2. 分析

MinIO 分片上传（Multipart Upload）对分片大小有严格要求：
- 除最后一个分片外，其他分片必须 ≥ 5MiB（5,242,880 字节）
- 如果整个对象小于最小分片大小，可能触发此错误
