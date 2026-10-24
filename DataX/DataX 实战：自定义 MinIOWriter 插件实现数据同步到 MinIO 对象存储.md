# DataX MinIOWriter 插件：实现数据同步到 MinIO 对象存储

## 一、背景

[DataX](https://github.com/alibaba/DataX) 是阿里开源的离线数据同步工具，支持 MySQL、PostgreSQL、MongoDB 等数十种异构数据源之间的数据同步。DataX 采用 **Reader + Writer** 插件架构，Reader 负责从源端读取数据，Writer 负责将数据写入目标端。

[MinIO](https://min.io/) 是一个高性能的 S3 兼容对象存储服务器，以其轻量部署和兼容 Amazon S3 API 著称，广泛应用于私有化对象存储场景。

然而 DataX 原生并不支持 MinIO 作为写入目标。本文将详细介绍如何为 DataX 实现一个 **miniowriter** 插件，打通 DataX → MinIO 的数据同步链路。

## 二、整体架构

### 2.1 DataX Writer 插件模型

DataX 的 Writer 插件遵循 `Job + Task` 两级生命周期模型：

```
                    ┌──────────────────────────────────────┐
                    │           DataX Engine               │
                    │                                      │
                    │  Reader ──► Channel ──► Writer       │
                    │  (source)   (transport)  (target)    │
                    └──────────────────────────────────────┘
```

- **Job**：全局唯一，负责参数校验、前置准备（清理/检查冲突）、分片拆分、全局收尾
- **Task**：每个数据分片一个实例，负责实际的数据读取与写入

### 2.2 生命周期方法调用顺序

```
Job.init()          → 初始化配置、构建 MinioClient
  ↓
Job.prepare()       → 校验 Bucket 存在性、处理 writeMode 策略
  ↓
Job.split(N)        → 拆分为 N 个分片，每个分片一个 Task
  ↓
Task.init()         → 每个 Task 独立初始化 MinioClient
  ↓
Task.startWrite()   → 从 Channel 接收数据，序列化为文本/CSV，上传 MinIO
  ↓
Job.post()          → 全局收尾（本插件为空）
  ↓
Job.destroy()       → 释放资源（本插件为空）
```

### 2.3 模块文件结构

```
minio-writer/
├── pom.xml                                          # Maven 构建配置
├── src/main/
│   ├── assembly/
│   │   └── package.xml                              # 打包描述文件
│   ├── java/com/alibaba/datax/plugin/writer/miniowriter/
│   │   ├── Key.java                                 # 配置键定义
│   │   ├── MinIOWriterErrorCode.java                # 错误码枚举
│   │   └── MinIOWriter.java                         # 核心实现（Job + Task）
│   └── resources/
│       ├── plugin.json                              # 插件注册描述
│       └── plugin_job_template.json                 # 作业配置模板
```

## 三、核心实现详解

### 3.1 MinIOWriter.java — 主入口

`MinIOWriter` 继承 DataX 的 `Writer` 抽象类，内部定义 `Job` 和 `Task` 两个静态内部类：
```java
public class MinIOWriter extends Writer {

    public static class Job extends Writer.Job { ... }

    public static class Task extends Writer.Task { ... }

    // 公共工具方法：构建 MinioClient
    static MinioClient buildMinioClient(Configuration config) {
        return MinioClient.builder()
                .endpoint(config.getString(Key.ENDPOINT))
                .credentials(
                    config.getString(Key.ACCESS_KEY),
                    config.getString(Key.SECRET_KEY))
                .build();
    }
}
```

`buildMinioClient()` 作为静态方法被 Job 和 Task 共享调用，避免重复代码。MinIO 的 endpoint 中已包含协议信息（`http://` 或 `https://`），SDK 自动判断安全连接。

### 3.2 Job.init() — 参数校验与客户端初始化

```java
@Override
public void init() {
    this.writerSliceConfig = this.getPluginJobConf();
    validateParameter();
    this.minioClient = buildMinioClient(this.writerSliceConfig);
}
```

`validateParameter()` 做两件事：

1. **MinIO 专属参数校验**：确保 `endpoint`、`accessKey`、`secretKey`、`bucket`、`object` 这五个必填项存在
2. **委托通用校验**：调用 `UnstructuredStorageWriterUtil.validateParameter()` 校验 `writeMode`（必须是 truncate/append/nonConflict）、`encoding`、`fileFormat`（text/csv）、`fieldDelimiter` 等通用参数

### 3.3 Job.prepare() — 写入策略分发

这是 Job 阶段最核心的方法，根据 `writeMode` 决定写入前如何处理目标端已有数据：

```java
@Override
public void prepare() {
    String writeMode = ...;

    // 1. 先检查 Bucket 是否存在
    boolean bucketExists = this.minioClient.bucketExists(
            BucketExistsArgs.builder().bucket(bucket).build());
    if (!bucketExists) {
        throw DataXException.asDataXException(
                MinIOWriterErrorCode.ILLEGAL_VALUE,
                String.format("您配置的 Bucket [%s] 不存在，请确认配置项。", bucket));
    }

    // 2. 按 writeMode 执行不同策略
    if (TRUNCATE.equals(writeMode)) {
        deleteObjectsByPrefix(bucket, object);       // 删除前缀匹配的所有对象
    } else if (APPEND.equals(writeMode)) {
        // 不做任何清理，直接追加写入
    } else if (NOCONFLICT.equals(writeMode)) {
        List<String> existObjects = listObjectsByPrefix(bucket, object);
        if (!existObjects.isEmpty()) {
            throw ...;  // 存在同名前缀对象，拒绝写入
        }
    }
}
```

三种模式的语义：

| writeMode | 语义 | 典型场景 |
|-----------|------|----------|
| `truncate` | 先清理同前缀的旧对象，再写入 | 全量覆盖 |
| `append` | 不清理，直接追加写入 | 增量追加 |
| `nonConflict` | 检查是否存在同名前缀对象，存在则报错 | 确保不覆盖 |

`deleteObjectsByPrefix()` 通过 MinIO 的 `listObjects` + `removeObject` 组合实现前缀批量清理：

```java
private void deleteObjectsByPrefix(String bucket, String prefix) throws Exception {
    Iterable<Result<Item>> results = this.minioClient.listObjects(
            ListObjectsArgs.builder()
                .bucket(bucket).prefix(prefix).recursive(true).build());
    for (Result<Item> result : results) {
        this.minioClient.removeObject(
                RemoveObjectArgs.builder()
                    .bucket(bucket)
                    .object(result.get().objectName())
                    .build());
    }
}
```

### 3.4 Job.split() — 并发分片策略

DataX Engine 会传入 `mandatoryNumber`（期望的分片数，由 `channel` 数决定）。`split()` 为每个分片克隆一份配置，并生成唯一的 object 名称，避免多个 Task 并发写入同一个对象：

```java
@Override
public List<Configuration> split(int mandatoryNumber) {
    List<Configuration> writerSplitConfigs = new ArrayList<>();
    for (int i = 0; i < mandatoryNumber; i++) {
        Configuration splitedTaskConfig = this.writerSliceConfig.clone();
        String suffix = UUID.randomUUID().toString().replace('-', '_');
        String fullObjectName = String.format("%s__%s", this.object, suffix);
        splitedTaskConfig.set(Key.OBJECT, fullObjectName);
        writerSplitConfigs.add(splitedTaskConfig);
    }
    return writerSplitConfigs;
}
```

**设计要点**：使用 `UUID` 而非序号来生成后缀，确保即使作业重试后 object 名称也不会冲突。例如配置 `object = "data/export"`，拆分为 3 个分片后：

```
data/export__a1b2c3d4e5f6
data/export__f7e8d9c0b1a2
data/export__x3y4z5w6v7u8
```

### 3.5 Task.startWrite() — 数据序列化与上传

Task 是真正干活的地方，核心流程分三步：

```
接收数据 ──► 内存序列化 ──► 上传 MinIO
```

```java
@Override
public void startWrite(RecordReceiver lineReceiver) {
    String currentObject = appendSuffix(this.object);

    try (ByteArrayOutputStream baos = new ByteArrayOutputStream()) {
        // Step 1: 将 Record 流序列化为文本字节
        UnstructuredStorageWriterUtil.writeToStream(
                lineReceiver, baos, this.writerSliceConfig,
                currentObject, this.getTaskPluginCollector());

        // Step 2: 获取字节数组，上传到 MinIO
        byte[] data = baos.toByteArray();
        this.minioClient.putObject(
                PutObjectArgs.builder()
                        .bucket(this.bucket)
                        .object(currentObject)
                        .stream(new ByteArrayInputStream(data), data.length, -1)
                        .contentType(resolveContentType(this.fileFormat))
                        .build());
    } catch (...) { ... }
}
```

**关键设计决策**：

1. **委托通用序列化**：调用 `UnstructuredStorageWriterUtil.writeToStream()` 完成 Record → 文本的转换。该方法内部自动从 config 读取 `header`（表头）、`nullFormat`（空值表示）、`encoding`（编码）、`fieldDelimiter`（字段分隔符）、`fileFormat`（text/csv）等通用参数。Task 无需重复处理这些逻辑。

2. **内存缓冲上传**：将数据先写入 `ByteArrayOutputStream`，完成后一次性 `putObject`。实现简洁，适合中小数据量场景。

3. **ContentType 自适应**：

```java
private String resolveContentType(String fileFormat) {
    if (Constant.FILE_FORMAT_CSV.equalsIgnoreCase(fileFormat)) {
        return "text/csv";
    }
    return "text/plain";
}
```

4. **文件后缀拼接**：

```java
private String appendSuffix(String objectName) {
    if (StringUtils.isNotBlank(this.suffix)) {
        if (!this.suffix.startsWith(".")) {
            return objectName + "." + this.suffix;
        }
        return objectName + this.suffix;
    }
    return objectName;
}
```

支持用户配置 `suffix = "csv"` 或 `suffix = ".csv"` 两种写法。

### 3.6 异常处理与脏数据

```java
} catch (DataXException e) {
    throw e;  // DataX 框架异常直接透传
} catch (IOException e) {
    throw DataXException.asDataXException(
            MinIOWriterErrorCode.WRITE_OBJECT_ERROR, e.getMessage(), e);
} catch (Exception e) {
    throw DataXException.asDataXException(
            MinIOWriterErrorCode.WRITE_OBJECT_ERROR, e.getMessage(), e);
}
```

所有异常统一包装为 `DataXException`，携带对应的 `MinIOWriterErrorCode`，便于排查定位。

脏数据（如类型不匹配的 Record）由 `UnstructuredStorageWriterUtil.writeToStream()` 内部通过 `TaskPluginCollector.collectDirtyRecord()` 收集并跳过，不会中断整个同步任务。

## 四、配置参数一览

### 4.1 MinIO 专属参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `endpoint` | String | 是 | - | MinIO 服务地址，如 `http://127.0.0.1:9000` |
| `accessKey` | String | 是 | - | MinIO Access Key（用户名） |
| `secretKey` | String | 是 | - | MinIO Secret Key（密码） |
| `bucket` | String | 是 | - | 目标 Bucket 名称 |
| `object` | String | 是 | - | 目标对象路径前缀 |

### 4.2 通用参数（由 plugin-unstructured-storage-util 处理）

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `writeMode` | String | 是 | - | 写入模式：`truncate` / `append` / `nonConflict` |
| `fileFormat` | String | 否 | `text` | 文件格式：`text` / `csv` |
| `encoding` | String | 否 | `UTF-8` | 文件编码 |
| `fieldDelimiter` | String | 否 | `,` | 字段分隔符（CSV 格式下） |
| `header` | List | 否 | - | CSV 表头 |
| `nullFormat` | String | 否 | `\N` | 空值表示 |
| `suffix` | String | 否 | 空 | 文件后缀，如 `.csv` |
| `compress` | String | 否 | - | 压缩格式：`gzip` / `bzip2` |

## 五、完整使用示例

### 5.1 从 MySQL 读取数据写入 MinIO

```json
{
    "job": {
        "setting": {
            "speed": {
                "channel": 3
            }
        },
        "content": [
            {
              "reader": {
                  "name": "mysqlreader",
                  "parameter": {
                      "username": "root",
                      "password": "root",
                      "column": [
                          "id",
                          "name",
                          "age",
                          "email"
                      ],
                      "splitPk": "id",
                      "connection": [
                          {
                              "table": [
                                  "datax_user"
                              ],
                              "jdbcUrl": [
                                  "jdbc:mysql://127.0.0.1:3306/test"
                              ]
                          }
                      ]
                  }
              },
              "writer": {
                    "name": "miniowriter",
                    "parameter": {
                        "endpoint": "http://localhost:8000",
                        "accessKey": "EYA66D4zqFm6mWx9v15l",
                        "secretKey": "CwmmfKe4hzZsIXdUruwInIrvCVcat4UnWqYPJT1F",
                        "bucket": "datax",
                        "object": "table/user_order",
                        "writeMode": "truncate",
                        "fileFormat": "csv",
                        "fieldDelimiter": ",",
                        "header": ["id", "name", "age", "email"],
                        "suffix": ".csv"
                    }
                }
            }
        ]
    }
}
```

执行后，MinIO 中会生成 3 个 CSV 文件（`channel=3` 意味着 3 个并发 Task）：

```
data-warehouse/export/user_order__a1b2c3d4.csv
data-warehouse/export/user_order__e5f6g7h8.csv
data-warehouse/export/user_order__i9j0k1l2.csv
```

## 六、构建与部署

### 6.1 构建

```bash
# 在 DataX 项目根目录下执行
mvn clean package -pl minio-writer -am -DskipTests
```

构建产物输出在：
```
minio-writer/target/datax/plugin/writer/miniowriter/
├── minio-writer-0.0.1-SNAPSHOT.jar
├── plugin.json
├── plugin_job_template.json
└── libs/                      # 88 个运行时依赖
```

### 6.2 部署

将 `datax/plugin/writer/miniowriter/` 整个目录拷贝到 DataX 安装目录的 `plugin/writer/` 下即可：

```bash
cp -r minio-writer/target/datax/plugin/writer/miniowriter /opt/workspace/datax/plugin/writer/
```

### 6.3 运行

```bash
python3 bin/datax.py job/minio/mysql_minio_csv.json
```

## 七、关键设计总结

| 设计点 | 方案 | 原因 |
|--------|------|------|
| 序列化层 | 委托 `UnstructuredStorageWriterUtil` | 复用 text/csv 格式解析、header 写入、脏数据收集等通用逻辑，避免重复造轮子 |
| 分片策略 | `UUID` 后缀 | 避免并发写入冲突，且重试安全 |
| 上传方式 | 内存缓冲 + `putObject` | 实现简洁，适合中小数据量；MinIO SDK 自动处理分块 |
| ContentType | 按 `fileFormat` 自动推断 | 便于下游工具（如 Spark/Hive）正确识别文件格式 |
| writeMode | truncate/append/nonConflict | 与 osswriter 等插件保持语义一致，降低用户学习成本 |
| 异常处理 | 统一包装为 `DataXException` | 与 DataX 框架的脏数据计数和任务失败处理机制对齐 |

## 八、已知局限与后续优化方向

1. **大表 OOM 风险**：当前采用 `ByteArrayOutputStream` 全量内存缓冲，同步超大表（GB 级别）时可能内存溢出。后续可引入 MinIO 的流式上传（`PipedInputStream` + 后台线程写入）实现零内存缓冲。

2. **不支持 Parquet/ORC**：当前仅支持 text/csv 文本格式。如需支持列式存储格式，可参考 osswriter 中 `HdfsParquetUtil` 的实现，借助 `hdfswriter` 代理完成转换后再上传。

3. **不支持数据压缩上传**：虽然 `UnstructuredStorageWriterUtil` 支持 `gzip`/`bzip2` 压缩参数，但 `MinIO` 的 `putObject` 未设置对应的 Content-Encoding 头。

4. **generateEmptyFile 开关**：当源端无数据时，当前行为会生成一个仅含 header（或空）的文件。可参考 osswriter 增加此开关配置。
