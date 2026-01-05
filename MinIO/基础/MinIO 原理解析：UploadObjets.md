
## 1. MinioClient#uploadObject

```java
public ObjectWriteResponse uploadObject(UploadObjectArgs args)
    throws ErrorResponseException, InsufficientDataException, InternalException,
        InvalidKeyException, InvalidResponseException, IOException, NoSuchAlgorithmException,
        ServerException, XmlParserException {
  try {
    return asyncClient.uploadObject(args).get();
  } catch (InterruptedException e) {
    throw new RuntimeException(e);
  } catch (ExecutionException e) {
    asyncClient.throwEncapsulatedException(e);
    return null;
  }
}
```
> io.minio.MinioClient#uploadObject

## 2. MinioAsyncClient#uploadObject

```java
public CompletableFuture<ObjectWriteResponse> uploadObject(UploadObjectArgs args)
      throws InsufficientDataException, InternalException, InvalidKeyException, IOException,
          NoSuchAlgorithmException, XmlParserException {
  checkArgs(args);
  args.validateSse(this.baseUrl);
  final RandomAccessFile file = new RandomAccessFile(args.filename(), "r");
  return putObjectAsync(
          args, file, args.objectSize(), args.partSize(), args.partCount(), args.contentType())
      .exceptionally(
          e -> {
            try {
              file.close();
            } catch (IOException ex) {
              throw new CompletionException(ex);
            }

            Throwable ex = e.getCause();

            if (ex instanceof CompletionException) {
              ex = ((CompletionException) ex).getCause();
            }

            if (ex instanceof ExecutionException) {
              ex = ((ExecutionException) ex).getCause();
            }

            throw new CompletionException(ex);
          })
      .thenApply(
          objectWriteResponse -> {
            try {
              file.close();
            } catch (IOException e) {
              throw new CompletionException(e);
            }
            return objectWriteResponse;
          });
}
```

## 3. S3Base#putObjectAsync

```java
protected CompletableFuture<ObjectWriteResponse> putObjectAsync(
    PutObjectBaseArgs args, Object data, long objectSize,
    long partSize, int partCount, String contentType)
    throws InsufficientDataException, InternalException, InvalidKeyException, IOException,
        NoSuchAlgorithmException, XmlParserException {
  PartReader partReader = newPartReader(data, objectSize, partSize, partCount);
  if (partReader == null) {
    throw new IllegalArgumentException("data must be RandomAccessFile or InputStream");
  }

  Multimap<String, String> headers = newMultimap(args.extraHeaders());
  headers.putAll(args.genHeaders());
  if (!headers.containsKey("Content-Type")) headers.put("Content-Type", contentType);

  return CompletableFuture.supplyAsync(
          () -> {
            try {
              return partReader.getPart();
            } catch (NoSuchAlgorithmException | IOException e) {
              throw new CompletionException(e);
            }
          })
      .thenCompose(
          partSource -> {
            try {
              if (partReader.partCount() == 1) {
                return putObjectAsync(
                    args.bucket(),
                    args.region(),
                    args.object(),
                    partSource,
                    headers,
                    args.extraQueryParams());
              } else {
                return putMultipartObjectAsync(args, headers, partReader, partSource);
              }
            } catch (InsufficientDataException
                | InternalException
                | InvalidKeyException
                | IOException
                | NoSuchAlgorithmException
                | XmlParserException e) {
              throw new CompletionException(e);
            }
          });
}
```
根据 Part 个数决定上传对象的方式，如果只有一个 Part 则使用单文件上传对象 `putObjectAsync` 方法，否则使用多文件上传对象 `putMultipartObjectAsync` 方法：
```java
if (partReader.partCount() == 1) {
  return putObjectAsync(
      args.bucket(),
      args.region(),
      args.object(),
      partSource,
      headers,
      args.extraQueryParams());
} else {
  return putMultipartObjectAsync(args, headers, partReader, partSource);
}
```

## 4. S3Base#putMultipartObjectAsync

```java
private CompletableFuture<ObjectWriteResponse> putMultipartObjectAsync(
    PutObjectBaseArgs args,
    Multimap<String, String> headers,
    PartReader partReader,
    PartSource firstPartSource)
    throws InsufficientDataException, InternalException, InvalidKeyException, IOException,
        NoSuchAlgorithmException, XmlParserException {
  return CompletableFuture.supplyAsync(
      () -> {
        String uploadId = null;
        ObjectWriteResponse response = null;
        try {
          CreateMultipartUploadResponse createMultipartUploadResponse =
              createMultipartUploadAsync(
                      args.bucket(),
                      args.region(),
                      args.object(),
                      headers,
                      args.extraQueryParams())
                  .get();
          uploadId = createMultipartUploadResponse.result().uploadId();
          Part[] parts = uploadParts(args, uploadId, partReader, firstPartSource);
          response =
              completeMultipartUploadAsync(
                      args.bucket(), args.region(), args.object(), uploadId, parts, null, null)
                  .get();
        } catch (InsufficientDataException
            | InternalException
            | InvalidKeyException
            | IOException
            | NoSuchAlgorithmException
            | XmlParserException
            | InterruptedException
            | ExecutionException e) {
          Throwable throwable = e;
          if (throwable instanceof ExecutionException) {
            throwable = ((ExecutionException) throwable).getCause();
          }
          if (throwable instanceof CompletionException) {
            throwable = ((CompletionException) throwable).getCause();
          }
          if (uploadId == null) {
            throw new CompletionException(throwable);
          }
          try {
            abortMultipartUploadAsync(
                    args.bucket(), args.region(), args.object(), uploadId, null, null)
                .get();
          } catch (InsufficientDataException
              | InternalException
              | InvalidKeyException
              | IOException
              | NoSuchAlgorithmException
              | XmlParserException
              | InterruptedException
              | ExecutionException ex) {
            throwable = ex;
            if (throwable instanceof ExecutionException) {
              throwable = ((ExecutionException) throwable).getCause();
            }
            if (throwable instanceof CompletionException) {
              throwable = ((CompletionException) throwable).getCause();
            }
          }
          throw new CompletionException(throwable);
        }
        return response;
      });
}
```

上传流程：
- createMultipartUploadAsync
- uploadParts
- completeMultipartUploadAsync
- abortMultipartUploadAsync









...
