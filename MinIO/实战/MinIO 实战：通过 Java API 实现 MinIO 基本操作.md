MinIO 是一个高性能的云原生对象存储系统，与 Amazon S3 API 完全兼容。作为现代应用程序的首选存储解决方案，MinIO 提供了简单、可靠的对象存储能力。本指南将详细介绍如何使用 MinIO Java SDK 来与 MinIO 服务器进行交互，并介绍 Bucket 和 Object 的基本操作。

## 1. 环境准备

### 1.1 搭建 MinIO 服务

请详细查阅[MinIO 实战：使用 Docker Compose 部署 MinIO 集群](https://smartsi.blog.csdn.net/article/details/138742646)。

### 1.2 Maven 依赖

在 Java 中使用如下添加如下依赖：
```xml
<dependency>
    <groupId>io.minio</groupId>
    <artifactId>minio</artifactId>
    <version>8.5.14</version>
</dependency>
```

## 2. 基本操作

### 2.1 客户端初始化

在进行 Bucket 和 Object 操作之前，需要先初始化 MinIO 客户端 MinioClient：
```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();
```
AK 和 SK 可以通过如下方式在控制台创建：

![](img-minio-quick-start-1.png)

### 2.2 Bucket 操作

下面详细介绍 Bucket 的基本操作：
- MakeBucket：创建 Bucket
- BucketExists：检查 Bucket 是否存在
- ListBuckets：列出所有 Bucket
- RemoveBucket：删除 Bucket

#### 2.2.1 MakeBucket

`MakeBucket` 用于创建 Bucket 的基础方法，它是使用 MinIO 对象存储服务的首要步骤，用于在存储系统中建立逻辑隔离的容器来组织和存储对象数据。Bukcet 类似于传统文件系统中的顶级目录，但具有更强的隔离性和策略控制能力。如下所示创建一个名为 `bucket-1` 的 Bucket：
```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
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
> bucketExists 用来检查 Bucket 是否存在，下面会详细介绍。

创建 Bucket 所需要的参数通过 MakeBucketArgs 来构造，在这只需要通过 `bucket` 方法填充要创建的 Bucket 名称即可。

运行上述代码之后可以通过控制台查看我们创建的 Bucket，当然也可以通过 API 来查看(下面会详细介绍)：

![](img-minio-quick-start-2.png)

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/bucket/MakeBucket.java)

#### 2.2.2 BucketExists

`BucketExists` 用于验证 Bukcet 是否存在的轻量级检查方法，它通过请求来确定指定 Bucket 是否可访问和存在，而不需要获取 Bucket 的完整详细信息或内容列表：
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
检查 Bucket 是否存在所需要的参数通过 BucketExistsArgs 来构造，在这只需要通过 `bucket` 方法填充要检查的 Bucket 名称即可。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/bucket/BucketExists.java)

#### 2.2.3 ListBuckets

`ListBuckets` 用于列出当前用户有权访问的所有 Bucket 的方法：
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
列出所有 Bucket 不需要任何参数。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/bucket/ListBuckets.java)

#### 2.2.4 RemoveBucket

`RemoveBucket` 用于永久删除空 Bucket 的方法，通常在 Bucket 不再需要且所有内容已清空时使用：
```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
// 构建参数
BucketExistsArgs bucketExistsArgs = BucketExistsArgs.builder().bucket(bucketName).build();
RemoveBucketArgs bucketArgs = RemoveBucketArgs.builder().bucket(bucketName).build();
// Bucket 存在则删除
if (minioClient.bucketExists(bucketExistsArgs)) {
    minioClient.removeBucket(bucketArgs);
    LOG.info("bucket {} is removed successfully", bucketName);
} else {
    LOG.info("bucket {} does not exist", bucketName);
}
```
删除 Bucket 所需要的参数通过 RemoveBucketArgs 来构造，在这只需要通过 `bucket` 方法填充要删除的 Bucket 名称即可。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/bucket/RemoveBucket.java)

### 2.3 Object 操作

下面详细介绍 Object 的基本操作：
- `PutObject`：通用上传 Object
- `UploadObject`：文件上传 Object
- `StatObject`：获取 Object 元数据
- `GetObject`：通用下载 Object
- `DownloadObject`：下载 Object 到本地文件
- `ListObjects`：列出所有 Object
- `RemoveObject`：删除单个 Object
- `RemoveObjects`：批量删除多个 Object
- `CopyObject`：复制 Object

#### 2.3.1 PutObject

可以通过 `PutObject` 实现上传对象：
```java
// 示例1：上传内存数据
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
> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/PutObject.java)

或者
```java
// 示例2：上传本地文件
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
> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/PutObjectFromFile.java)

`PutObject` 方法是一个通用的上传对象的方法，它允许你从 InputStream 上传数据。这意味着你可以上传任何数据，而不仅仅是本地文件，比如从网络流、内存中的数据等。上 Object 所需要的参数通过 PutObjectArgs 来构造，在这需要填充要上传的 Bucket、Object 以及输入流 InputStream。

> 需要注意的是，使用 `PutObject` 上传大文件时，需要自己处理分片上传，或者确保数据量不大。

#### 2.3.2 UploadObject

除了可以通过 `PutObject` 实现上传对象，也可以通过 `UploadObject` 实现上传对象，主要用于上传本地文件：
```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
String objectName = "object-1";
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
`UploadObject` 是对 `PutObject` 方法的一个封装，但更专注于处理本地文件。该方法会自动处理文件的分片上传（如果文件较大），并且在上传过程中会计算文件的MD5校验和以确保数据完整性。上传 Object 所需要的参数通过 UploadObjectArgs 来构造，在这需要填充要上传的 Bucket、Object 以及输入的本地文件。

运行上述代码之后可以通过控制台查看我们创建的 Object，当然也可以通过 API 来查看(下面会详细介绍)：

![](img-minio-quick-start-3.png)

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/UploadObject.java)

#### 2.3.3 StatObject

`StatObject` 用于获取 Object 元数据信息的关键方法，它不会下载 Object 内容，仅返回 Object 的元数据和属性信息：
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
获取 Object 元数据所需要的参数通过 StatObjectArgs 来构造，在这需要填充要获取的 Bucket 以及 Object 名称。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/StatObject.java)

#### 2.3.4 GetObject

`GetObject` 用于下载 Object 内容的核心方法。与 `StatObject` 仅获取元数据不同，`GetObject` 会实际传输对象的数据内容，并返回一个 InputStream 供读取：
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
下载 Object 内容所需要的参数通过 GetObjectArgs 来构造，在这需要填充要下载的 Bucket 以及 Object 名称。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/GetObject.java)

#### 2.3.5 DownloadObject

`DownloadObject` 用于将对象直接下载到本地文件的便捷方法。它封装了从 MinIO 获取对象数据并写入本地文件的完整流程，提供了开箱即用的下载功能：
```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
String objectName = "object-1";
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
`DownloadObject` 简化文件下载，专注"对象→本地文件"场景，而 `GetObject` 提供原始数据流，可以最大化的灵活获取数据。下载 Object 所需要的参数通过 DownloadObjectArgs 来构造，在这需要填充要下载的 Bucket、Object 名称以及下载到目标文件。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/DownloadObject.java)

#### 2.3.6 ListObjects

`ListObjects` 用于列出 Bucket 内所有 Object 的核心方法，它提供了类似文件系统的目录浏览功能，能够高效地查询 Bucket 的 Object 信息而不需要实际下载 Object 内容：
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
该方法返回一个可迭代的结果集，每个结果包含 Object 的元数据信息，但不包含 Object 数据本身。列出所有 Object 所需要的参数通过 ListObjectsArgs 来构造，在这需要填充要展示的 Bucket 名称。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/ListObjects.java)

#### 2.3.7 RemoveObject

`RemoveObject` 用于删除 Bucket 中单个 Object 的核心方法。它提供了一种简单直接的方式从对象存储中移除不再需要的文件：
```java
// MinIO 客户端
MinioClient minioClient = MinioClient.builder()
        .endpoint(ENDPOINT)
        .credentials(AK, SK)
        .build();

String bucketName = "bucket-1";
String objectName = "object-1";
RemoveObjectArgs objectArgs = RemoveObjectArgs.builder().bucket(bucketName).object(objectName).build();
minioClient.removeObject(objectArgs);
LOG.info("Bucket: {}, Object: {} is removed successfully", bucketName, objectName);
```
删除单个 Object 所需要的参数通过 RemoveObjectArgs 来构造，在这需要填充要删除的 Bucket 和 Object 名称。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/RemoveObject.java)

#### 2.3.8 RemoveObjects

`RemoveObjects` 用于批量删除多个 Object 的专业方法。它专门设计用于高效处理大量 Object 的删除操作，相比逐个调用 `RemoveObject`，它在性能上具有显著优势，特别适合大规模数据清理和存储空间管理场景：
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
批量删除多个 Object 所需要的参数通过 RemoveObjectsArgs 来构造，在这需要填充要删除的 Bucket 和 Object 名称。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/RemoveObjects.java)

#### 2.3.9 CopyObject

`CopyObject` 用于 Object 复制的核心方法，它能够在不经过客户端传输数据的情况下，直接在 MinIO 服务器内部完成 Object 的复制操作。这种方法通过高效的服务器端数据传输机制，特别适合大文件复制和跨存储桶数据迁移场景：
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
待复制 Object 通过 CopySource 来构造，需要指定要复制的 Bucket 和 Object 名称。具体复制操作所需要的参数通过 CopyObjectArgs 来构造，需要填充要复制到的目标 Bucket 和 Object 名称。

> [完整示例](https://github.com/sjf0115/minio-example/blob/main/minio-quick-start/src/main/java/com/example/object/CopyObject.java)
