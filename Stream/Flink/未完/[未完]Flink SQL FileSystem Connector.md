---
layout: post
author: smartsi
title: Flink SQL FileSystem Connector
date: 2021-08-08 15:47:21
tags:
  - Flink

categories: Flink
permalink: flink-sql-filesystem-connector
---

> Flink 版本：1.14

FileSystem Connector 提供了对 Flink 支持的文件系统中分区文件的访问，允许从本地或者分布式文件系统进行读写操作。FileSystem Connector 已经包含在 Flink 中，不需要引入其他的依赖。Flink FileSystem 表可以定义如下样例所示:
```sql
CREATE TABLE MyUserTable (
  column_name1 INT,
  column_name2 STRING,
  ...
  part_name1 INT,
  part_name2 STRING
) PARTITIONED BY (part_name1, part_name2) WITH (
  'connector' = 'filesystem',           -- required: 指定 connector
  'path' = 'file:///path/to/whatever',  -- required: 文件路径
  'format' = '...',                     -- required: 格式
  ...
)
```

> 文件系统 Source 仍在开发中。未来，社区将增加对常见流用例的支持，例如，分区和目录监控。

## 1. 分区文件

Flink 的文件系统分区支持标准的 Hive 格式。但是，不要求将分区预先注册到表 Catalog 中。可以根据目录结构来发现和推断分区。例如，基于下面目录推断出包含 datetime 和 hour 分区：
```
path
└── datetime=2019-08-25
    └── hour=11
        ├── part-0.parquet
        ├── part-1.parquet
    └── hour=12
        ├── part-0.parquet
└── datetime=2019-08-26
    └── hour=6
        ├── part-0.parquet
```
文件系统表支持分区插入以及分区覆盖插入。当我们向分区表覆盖插入时，只会覆盖相应的分区，不会覆盖整个表。

## 2. 文件格式

FileSystem Connector 支持多种格式:
- CSV：[RFC-4180](https://tools.ietf.org/html/rfc4180)。未压缩。
- JSON：注意 FileSystem Connector 的 JSON 格式不是传统的 JSON 文件，而是一个未压缩换行分隔的 JSON。
- Avro：[Apache Avro](http://avro.apache.org/)。通过配置 avro.codec 支持压缩。
- Parquet：[Apache Parquet](http://parquet.apache.org/)。与 Hive 兼容。
- Orc：[Apache Orc](http://orc.apache.org/)。与 Hive 兼容。
- Debezium-JSON: [Debezium-JSON](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/connectors/table/formats/debezium/)。
- Canal-JSON: [Canal-JSON](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/connectors/table/formats/canal/)。

## 4. Source

FileSystem Connector 可以将单个文件或整个目录读入一个表。当使用目录作为源路径时，目录内文件读取没有严格的顺序。

## 5. Streaming Sink

FileSystem Connector 支持流式写入，基于 Flink 的 Streaming File Sink 将记录写入文件。Row-encoded Formats 可以是 csv 或者 json。Bulk-encoded Formats 可以是 parquet、orc 或者 avro。我们可以直接通过 SQL 的方式将数据流式插入到非分区表中。如果是分区表，可以配置分区相关操作。

### 5.1 滚动策略

分区目录中的数据被拆分为 Part 文件。每个分区下的每个子任务(接收每个分区的数据)至少有一个 Part 文件。正在进行写入的 Part 文件在写完之后被关闭，并根据配置的滚动策略创建另外一个 Part 文件。滚动策略根据文件大小、文件打开最大持续时间来滚动生成 Part 文件：
- sink.rolling-policy.file-size：Part 文件最大大小。超过这个大小，会新生成一个新 Part 文件。默认值为 128 MB。
- sink.rolling-policy.rollover-interval：Part 文件最大打开时长。超过这个时长，会新生成一个新的 Part 文件。默认为 30 分钟，避免生成大量小文件。
- sink.rolling-policy.check-interval：检查时间间隔，默认值为 1 min。根据上面配置的策略，每1分钟去检查是否应该滚动生成新 Part 文件。

Bulk-encoded Formats（parquet、orc、avro），滚动策略与检查点间隔相结合来控制 Part 文件的大小和数量。对于 Row-encoded Formats（csv、json），可以在 Connector 属性中设置 sink.rolling-policy.file-size 或者 sink.rolling-policy.rollover-interval 参数，如果不想等待很长时间才能观察文件系统中存在的数据，请一起在 flink-conf.yaml 中设置参数 execution.checkpointing.interval。

### 5.2 文件压缩

FileSystem Connector 支持文件压缩，这允许应用程序具有更小的 Checkpoint 间隔，从而不会生成大量文件。

| Key | 默认值 | 类型 | 说明 |
| :------------- | :------------- |
| auto-compaction | false | Boolean | 是否在流 Sink 中启用自动压缩。数据先写入临时文件。Checkpoint 完成后，临时文件会被压缩，压缩前是不可见的。|
| compaction.file-size | (none) | MemorySize | 目标文件压缩大小，默认值为滚动文件大小。|

如果启用文件压缩，文件压缩将根据目标文件大小将多个小文件合并为更大的文件。在生产环境中运行文件压缩时，请注意：
- 仅压缩单个 Checkpoint 中的文件，即至少生成与 Checkpoint 数量相同数量的文件。
- 合并前的文件是不可见的，所以文件的可见是：Checkpoint 间隔 + 压缩时间。
- 如果压缩时间过长，则会对作业产生背压并延长 Checkpoint 的时长。

### 5.3 分区提交

写入分区后，通常需要通知下游应用程序。例如，将分区添加到 Hive MetaStore 或者在目录中写入 `_SUCCESS` 文件。 Filesystem Sink 包含允许配置自定义策略的分区提交功能。基于触发器和策略的组合来提交：
- Trigger：控制分区提交的时机。分区提交的时间可以通过 Watermark 和从分区中提取的时间来确定，也可以通过处理时间来确定。你可以控制：是想先尽快看到没写完的分区；还是保证写完分区之后，再让下游看到它。
- Policy：控制分区提交策略。内置支持 SUCCESS 文件和 Metastore 的提交，你也可以自定义实现自己的策略，比如，触发 Hive 的 analysis 来生成统计信息，或者进行小文件的合并等等。

> 分区提交仅适用于动态分区插入。

#### 5.3.1 分区提交触发器

要定义何时提交分区，需要提供分区提交触发器：
- sink.partition-commit.trigger：分区提交触发器类型，默认为 process-time。一共有两种类型：
  - process-time：基于机器时间，既不需要提取分区时间，也不需要依赖 Watermark。一旦当前系统时间超过分区创建系统时间加上延迟的时间，就会提交分区。
  - partition-time：基于从分区值中提取的时间，依赖 Watermark 的生成。一旦 Watermar 大于从分区值中提取的时间加上延迟时间，就会提交分区。
- sink.partition-commit.delay：延迟多久时间才提交分区。如果是日分区，可以设置为 '1 d'，如果是小时分区，可以设置为 '1 h'。
- sink.partition-commit.watermark-time-zone：

有两种类型的触发器：
- 首先是分区处理时间，既不需要分区时间提取器也不需要依赖 Watermark 的生成。根据分区创建时间和当前系统时间触发分区提交。 这个触发器更通用，但不是那么精确。 例如，数据延迟或故障转移会导致过早的分区提交。
第二个是根据从分区值和水印中提取的时间触发分区提交。 这就要求你的job有水印生成，按照时间划分分区，比如每小时分区或者每天分区。



#### 5.3.2 分区时间提取

时间提取器定义了如何从分区值中提取时间：
- partition.time-extractor.kind：时间提取器定义了如何从分区值中提取时间。目前支持两种模式：
  - default：默认提取器，需要配置一个时间戳表达式。
  - custom：自定义提取器，需要提供一个自定义提取器类。
- partition.time-extractor.class：custom 模式下实现 PartitionTimeExtractor 接口的提取器类。
- partition.time-extractor.timestamp-pattern：default 模式下允许用户使用分区字段来获取合法的时间戳表达式。默认支持来自第一个字段的 'yyyy-mm-dd hh:mm:ss'。如果时间戳从单个分区字段 'dt' 中提取，可以配置：'$dt'。如果时间戳从多个分区字段中提取，比如 'year'、'month'、'day' 以及 'hour'，可以配置：'$year-$month-$day $hour:00:00'。如果时间戳从两个分区字段 'dt' 和 'hour' 中提取，可以配置：'$dt $hour:00:00'。

默认提取器基于由分区字段组成的时间戳表达式。此外，还可以实现 PartitionTimeExtractor 接口自定义实现分区提取：
```java
public class HourPartTimeExtractor implements PartitionTimeExtractor {
    @Override
    public LocalDateTime extract(List<String> keys, List<String> values) {
        String dt = values.get(0);
        String hour = values.get(1);
		return Timestamp.valueOf(dt + " " + hour + ":00:00").toLocalDateTime();
	}
}
```

#### 5.3.3 分区提交策略

分区提交策略定义了提交分区时进行的操作：
- 第一个是 Metastore，只有 hive 表支持 Metastore 策略，文件系统通过目录结构管理分区。
- 第二个是成功文件，会在分区对应的目录下写一个空文件。

- sink.partition-commit.policy.kind：提交分区的策略是通知下游应用该分区已经写完可以被读取了。目前有两种策略：
  - metastore：将分区添加到 Metastore。只有 hive 表支持 Metastore 策略。
  - success-file：将 `_success` 文件添加到目录中。Metastore 和 成功文件策略可以同时配置：'metastore,success-file'。
  - custom：可以自定义策略类来创建提交策略。支持配置多个策略：'custom,metastore,success-file'。
- sink.partition-commit.policy.class：custom 分区提交策略实现 PartitionCommitPolicy 接口的自定义分区提交策略类。仅当第一个参数设置为自定义提交策略(custom)时有效。
- sink.partition-commit.success-file.name：success-file 分区提交策略的文件名，默认为 `_SUCCESS`。仅当第一个参数设置为成功文件策略(success-file)时有效。

我们可以扩展提交策略的实现，如下所示实现一个自定义提交策略：
```java
public class AnalysisCommitPolicy implements PartitionCommitPolicy {
    private HiveShell hiveShell;

    @Override
	public void commit(Context context) throws Exception {
	    if (hiveShell == null) {
	        hiveShell = createHiveShell(context.catalogName());
	    }

        hiveShell.execute(String.format(
            "ALTER TABLE %s ADD IF NOT EXISTS PARTITION (%s = '%s') location '%s'",
	        context.tableName(),
	        context.partitionKeys().get(0),
	        context.partitionValues().get(0),
	        context.partitionPath()));
	    hiveShell.execute(String.format(
	        "ANALYZE TABLE %s PARTITION (%s = '%s') COMPUTE STATISTICS FOR COLUMNS",
	        context.tableName(),
	        context.partitionKeys().get(0),
	        context.partitionValues().get(0)));
	}
}
```

## 6. Sink 并行度

将文件写入外部文件系统（例如，Hive）的并行度可以通过相应的 Table 选项 sink.parallelism 进行配置，在流模式和批处理模式都可以支持。默认情况下，并行度与其最后一个上游链算子的并行度相同。当配置了不同于上游并行度时，写入文件和压缩文件的算子（如果使用）使用该并行度。

> 当前，当且仅当上游的更改日志模式为 INSERT-ONLY 时，才支持配置 Sink 并行度，否则会抛出异常。

## 7. Example

```sql
CREATE TABLE kafka_table (
  user_id STRING,
  order_amount DOUBLE,
  log_ts TIMESTAMP(3),
  WATERMARK FOR log_ts AS log_ts - INTERVAL '5' SECOND
) WITH (...);

CREATE TABLE fs_table (
  user_id STRING,
  order_amount DOUBLE,
  dt STRING,
  `hour` STRING
) PARTITIONED BY (dt, `hour`) WITH (
  'connector'='filesystem',
  'path'='...',
  'format'='parquet',
  'sink.partition-commit.delay'='1 h',
  'sink.partition-commit.policy.kind'='success-file'
);

-- streaming sql, insert into file system table
INSERT INTO fs_table
SELECT
    user_id,
    order_amount,
    DATE_FORMAT(log_ts, 'yyyy-MM-dd'),
    DATE_FORMAT(log_ts, 'HH')
FROM kafka_table;

-- batch sql, select with partition pruning
SELECT * FROM fs_table WHERE dt='2020-05-20' and `hour`='12';
```

原文：[FileSystem SQL Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/filesystem/)
