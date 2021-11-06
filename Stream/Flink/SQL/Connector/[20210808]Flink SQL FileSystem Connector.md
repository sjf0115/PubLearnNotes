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

FileSystem Connector 已经包含在 Flink 中，不需要引入其他的依赖。从文件系统读写数据需要指定相应的格式。FileSystem Connector 允许从本地或者分布式文件系统进行读写操作。文件系统表可以定义为:
```sql
CREATE TABLE MyUserTable (
  column_name1 INT,
  column_name2 STRING,
  ...
  part_name1 INT,
  part_name2 STRING
) PARTITIONED BY (part_name1, part_name2) WITH (
  'connector' = 'filesystem',           -- required: specify the connector
  'path' = 'file:///path/to/whatever',  -- required: path to a directory
  'format' = '...',                     -- required: file system connector requires to specify a format,
                                        -- Please refer to Table Formats
                                        -- section for more details
  'partition.default-name' = '...',     -- optional: default partition name in case the dynamic partition
                                        -- column value is null/empty string

  -- optional: the option to enable shuffle data by dynamic partition fields in sink phase, this can greatly
  -- reduce the number of file for filesystem sink but may lead data skew, the default value is false.
  'sink.shuffle-by-partition.enable' = '...',
  ...
)
```

## 2. 分区文件

Flink 的文件系统分区支持使用标准的 Hive 格式。但是，不要求将分区预先注册到表 Catalog 中。根据目录结构来发现和推断分区。例如，基于下面目录的分区表推断出包含 datetime 和 hour 分区：
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

## 3. 文件格式

FileSystem Connector 支持多种格式:
- CSV：[RFC-4180](https://tools.ietf.org/html/rfc4180)。未压缩。
- JSON：注意 FileSystem Connector 的 JSON 格式不是传统的 JSON 文件，而是一个未压缩换行分隔的 JSON。
- Avro：[Apache Avro](http://avro.apache.org/)。通过配置 avro.codec 支持压缩。
- 拼花:Apache拼花。兼容蜂巢。
- 兽人:Apache兽人。兼容蜂巢。
- Debezium-JSON: Debezium-JSON。
- Canal-JSON: Canal-JSON。

## 4. Source

FileSystem Connector 可以将单个文件或整个目录读入一个表。当使用目录作为源路径时，目录内文件读取没有严格的顺序。

## 5. Streaming Sink

FileSystem Connector 支持流式写入，基于 Flink 的 Streaming File Sink 将记录写入文件。Row-encoded Formats 可以是 csv 或者 json。Bulk-encoded Formats 可以是 parquet、orc 或者 avro。我们可以直接通过 SQL 的方式将数据流式插入到非分区表中。如果是分区表，可以配置分区相关操作。

### 5.1 滚动策略

分区目录中的数据被拆分为部分文件。 对于接收到该分区数据的接收器的每个子任务，每个分区将包含至少一个部分文件。 正在进行的零件文件将被关闭，并根据可配置的滚动策略创建附加零件文件。 该策略根据大小滚动部分文件，超时指定文件可以打开的最大持续时间。


| Key | 默认值 | 类型 | 说明 |
| :------------- | :------------- |
| sink.rolling-policy.file-size | 128MB | MemorySize | Part 文件最大大小。超过这个大小，会新生成一个新 Part 文件。 |
| sink.rolling-policy.rollover-interval | 30 min | Duration | Part 文件最大滚动时长。超过这个时长，会新生成一个 Part 文件。默认为30分钟，避免生成大量小文件。 |
| sink.rolling-policy.check-interval | 1 min | Duration | 检查时间间隔。定期去检查上面配置指定的策略下，是否应该滚动生成新 Part 文件。 |

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

要定义何时提交分区，提供分区提交触发器：




原文：[FileSystem SQL Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/filesystem/)
