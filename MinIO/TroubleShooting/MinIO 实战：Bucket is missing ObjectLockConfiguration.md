## 1. 问题

使用 `setObjectRetention` API 为 Object 设置保留 Retention 策略，如下所示:
```java
SetObjectRetentionArgs retentionArgs = SetObjectRetentionArgs.builder()
      .bucket(bucketName)
      .object(objectName)
      .config(config)
      .bypassGovernanceMode(true)
      .build();
minioClient.setObjectRetention(retentionArgs);
```
遇到如下问题：
```java
Exception in thread "main" error occurred
ErrorResponse(code = InvalidRequest, message = Bucket is missing ObjectLockConfiguration, bucketName = bucket-1, objectName = object-1, resource = /bucket-1/object-1, requestId = 187D1FABB67CF8C3, hostId = e0c385c033c4356721cc9121d3109c9b9bfdefb22fd2747078acd22328799e36)
request={method=PUT, url=http://localhost:9000/bucket-1/object-1?retention=, headers=x-amz-bypass-governance-retention: True
Host: localhost:8000
Accept-Encoding: identity
User-Agent: MinIO (Mac OS X; aarch64) minio-java/8.5.14
Content-MD5: cdw2FIacf8y5Mc+Vi07Dcg==
x-amz-content-sha256: e376a48b0162a0c76bb3624585df08f8c541d57f7a941f1c9aa3d7537c45ffef
x-amz-date: 20251201T150411Z
Authorization: ██
}
response={code=400, headers=Accept-Ranges: bytes
Content-Length: 352
Content-Type: application/xml
Server: MinIO
Strict-Transport-Security: max-age=31536000; includeSubDomains
Vary: Origin
Vary: Accept-Encoding
X-Amz-Id-2: e0c385c033c4356721cc9121d3109c9b9bfdefb22fd2747078acd22328799e36
X-Amz-Request-Id: 187D1FABB67CF8C3
X-Content-Type-Options: nosniff
X-Xss-Protection: 1; mode=block
Date: Mon, 01 Dec 2025 15:04:11 GMT
}

	at io.minio.S3Base$1.onResponse(S3Base.java:775)
	at okhttp3.internal.connection.RealCall$AsyncCall.run(RealCall.kt:519)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:750)
```

## 2. 解决方案

遇到这个错误是因为尝试对一个没有启用对象锁（Object Lock）的 Bucket 设置对象保留（Retention）策略。在 MinIO 中，要使用对象保留功能，必须在创建 Bucket 时启用对象锁（Object Lock）功能：
```java
MakeBucketArgs makeBucketArgs = MakeBucketArgs.builder().bucket(bucketName).objectLock(true).build();
```
