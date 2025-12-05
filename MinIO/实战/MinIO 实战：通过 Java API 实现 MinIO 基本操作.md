MinIO 是一个高性能的云原生对象存储系统，与 Amazon S3 API 完全兼容。作为现代应用程序的首选存储解决方案，MinIO 提供了简单、可靠的对象存储能力。本指南将详细介绍如何使用 MinIO Java SDK 来与 MinIO 服务器进行交互。

## 1. 环境准备

### 1.1 搭建 MinIO 服务

```

```

### 1.2 Maven 依赖

```

```

## 2. 基本操作

### 2.1 客户端初始化

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();
```
### 2.2 Bucket 操作

#### 2.2.1 BucketExists

```java
// MinIO 客户端
MinioClient minioClient = ...

String bucketName = "test-bucket";
// 构建参数
BucketExistsArgs bucketExistsArgs = BucketExistsArgs.builder().bucket(bucketName).build();
// 判断 Bucket 是否存
boolean exists = minioClient.bucketExists(bucketExistsArgs);
if (exists) {
    LOG.info("bucket {} exists", bucketName);
} else {
    LOG.info("bucket {} does not exist", bucketName);
}
```

#### 2.2.2 MakeBucket

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "test-bucket";
// 构建参数
BucketExistsArgs bucketExistsArgs = BucketExistsArgs.builder().bucket(bucketName).build();
MakeBucketArgs makeBucketArgs = MakeBucketArgs.builder().bucket(bucketName).build();
// Bucket 不存在则创建
if (!minioClient.bucketExists(bucketExistsArgs)) {
    minioClient.makeBucket(makeBucketArgs);
    LOG.info("bucket {} is created successfully", bucketName);
} else {
    LOG.info("bucket {} is already created", bucketName);
}
```

#### 2.2.3 ListBuckets

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

List<Bucket> bucketList = minioClient.listBuckets();
for (Bucket bucket : bucketList) {
    LOG.info("bucket name: {}, createDate: {}", bucket.name(), bucket.creationDate());
}
```

### 2.3 Object 操作

#### 2.3.1 StatObject

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
String objectName = "object-1";
// 详情
StatObjectArgs objectArgs = StatObjectArgs.builder().bucket(bucketName).object(objectName).build();
StatObjectResponse objectResponse = minioClient.statObject(objectArgs);
LOG.info("Bucket: {} Object: {}, Size: {}", objectResponse.bucket(), objectResponse.object(), objectResponse.size());
```

#### 2.3.2 PutObject

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
String objectName = "object-1";

// 上传数据
StringBuilder builder = new StringBuilder();
for (int i = 0;i < 10; i++) {
    builder.append(1000 + i).append("\n");
}
ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(builder.toString().getBytes(StandardCharsets.UTF_8));

// 上传
PutObjectArgs objectArgs = PutObjectArgs.builder()
        .bucket(bucketName)
        .object(objectName)
        .stream(byteArrayInputStream, byteArrayInputStream.available(), -1)
        .build();
minioClient.putObject(objectArgs);
byteArrayInputStream.close();
LOG.info("Bucket: {} Object: {} is uploaded successfully", bucketName, objectName);
```
或者
```java
// 上传数据
File file = new File("/opt/data/province_info.txt");
FileInputStream fileInputStream = new FileInputStream(file);

// 上传
PutObjectArgs objectArgs = PutObjectArgs.builder()
        .bucket(bucketName)
        .object(objectName)
        .stream(fileInputStream, file.length(), -1)
        .build();
minioClient.putObject(objectArgs);
fileInputStream.close();
LOG.info("Bucket: {} Object: {} is uploaded successfully", bucketName, objectName);
```

#### 2.3.3 UploadObject

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
String objectName = "object-3";
String fileName = "/opt/data/province_info.txt";
// 上传文件
UploadObjectArgs objectArgs = UploadObjectArgs.builder()
        .bucket(bucketName)
        .object(objectName)
        .filename(fileName)
        .build();
ObjectWriteResponse response = minioClient.uploadObject(objectArgs);
LOG.info("{} is uploaded to {}({}) successfully", fileName, response.object(), response.bucket());
```

#### 2.3.4 GetObject

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
String objectName = "object-1";

// 从 Object 中获取输入流
GetObjectArgs objectArgs = GetObjectArgs.builder().bucket(bucketName).object(objectName).build();
InputStream stream = minioClient.getObject(objectArgs);

// 从输入流中读取输出到控制台
byte[] buf = new byte[16384];
int bytesRead;
while ((bytesRead = stream.read(buf, 0, buf.length)) >= 0) {
    String result = new String(buf, 0, bytesRead, StandardCharsets.UTF_8);
    LOG.info("result: {}", result);
}
stream.close();
```

#### 2.3.5 ListObjects

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
ListObjectsArgs objectsArgs = ListObjectsArgs.builder().bucket(bucketName).build();
Iterable<Result<Item>> results = minioClient.listObjects(objectsArgs);
for (Result<Item> result : results) {
    Item item = result.get();
    LOG.info("Object: {}, Size: {}, LastModified: {}", item.objectName(), item.size(), item.lastModified());
}
```

#### 2.3.6 RemoveObject

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
ListObjectsArgs objectsArgs = ListObjectsArgs.builder().bucket(bucketName).recursive(true).build();
Iterable<Result<Item>> results = minioClient.listObjects(objectsArgs);
for (Result<Item> result : results) {
    Item item = result.get();
    LOG.info("Object: {}, Size: {}, LastModified: {}", item.objectName(), item.size(), item.lastModified());
}
```

#### 2.3.7 RemoveObjects

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
List<DeleteObject> objects = new LinkedList<>();
objects.add(new DeleteObject("object-1"));
objects.add(new DeleteObject("object-2"));

RemoveObjectsArgs objectsArgs = RemoveObjectsArgs.builder().bucket(bucketName).objects(objects).build();
Iterable<Result<DeleteError>> results = minioClient.removeObjects(objectsArgs);
for (Result<DeleteError> result : results) {
    DeleteError error = result.get();
    LOG.info("Error in deleting object {}, {}", error.objectName(), error.message());
}
```

#### 2.3.8 DownloadObject

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
String objectName = "object-3";
String fileName = "/opt/data/minio.txt";

// 下载
DownloadObjectArgs objectArgs = DownloadObjectArgs.builder()
        .bucket(bucketName)
        .object(objectName)
        .filename(fileName)
        .build();
minioClient.downloadObject(objectArgs);
LOG.info("{} is successfully downloaded to {}", objectName, fileName);
```

#### 2.3.9 CopyObject

```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String sourceBucketName = "bucket-1";
String sourceObjectName = "object-3";
String targetBucketName = "bucket-1";
String targetObjectName = "object-4";

// 复制
CopySource copySource = CopySource.builder().bucket(sourceBucketName)
        .object(sourceObjectName).build();
CopyObjectArgs objectArgs = CopyObjectArgs.builder().bucket(targetBucketName).object(targetObjectName)
        .source(copySource).build();
minioClient.copyObject(objectArgs);
LOG.info("{}/{} copied to {}/{} successfully", sourceObjectName, sourceBucketName, targetObjectName, targetBucketName);
```
