---
layout: post
author: smartsi
title: Flink Stream FileSink Connector
date: 2021-11-20 18:47:21
tags:
  - Flink

categories: Flink
permalink: flink-stream-file-sink-connector
---

> Flink 版本：1.14

FileSink Connector 为 BATCH 和 STREAMING 提供了统一的 Sink，并提供了相同的语义保证。FileSink Connector 将分区文件写入 Flink FileSystem 支持的文件系统中。

> FileSink 是现有 [Streaming File Sink](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/connectors/datastream/streamfile_sink/) 的演进，Streaming File Sink 旨在为 STREAMING 提供 Exactly-Once 语义保证。

## 1. 如何组织数据

FileSink 将传入的流式数据写入到 Bucket。考虑到传入的流是无限的，因此每个 Bucket 中的数据被组织成有限大小的 Part 文件。分桶行为可以配置为默认的基于时间的分桶，例如，我们每小时写入一个新的 Bucket。这意味着每个 Bucket 包含 1 小时内的数据。

Bucket 目录中的数据被拆分为不同的 Part 文件。每个 Sink 子任务在 Bucket 中都会至少包含一个 Part 文件。根据配置的滚动策略创建其他 Part 文件。对于行编码格式，默认策略根据文件大小、文件可以打开的最长持续超时时间以及文件关闭后的最长不活跃超时时间来滚动生成 Part文件。对于批量编码格式，我们在每个检查点上滚动，用户也可以根据大小或时间指定其他条件。

### 1.1 如何生成Bucket

Bucket 定义了如何将数据组织到我们指定输出目录下的子目录中，可以理解为 Bucket 对应一个输出子目录。BucketAssigner 决定了 FileSink 将传入的流式数据写入到哪个子目录下。默认使用 DateTimeBucketAssigner 作为分配器。DateTimeBucketAssigner 默认根据系统时区以及默认时间格式 yyyy-MM-dd--HH 创建小时 Bucket。我们也可以手动设置日期格式（例如，我们可以设置分钟级的 Bucket，日期格式决定了 Bucket 的大小）和时区。可以通过调用 `.withBucketAssigner(assigner)` 方法来指定 BucketAssigner。Flink 有两个内置的 BucketAssigners：
- DateTimeBucketAssigner ：降 Part 文件存储在 `/{basePath}/{dateTimePath}/` 格式创建的子目录下，dateTimePath 由当前系统时间和提供的日期格式决定。
- BasePathBucketAssigner ：将所有 Part 文件存储在指定路径 basePath 下。
```java
FileSink.forRowFormat(new Path(outputPath), new SimpleStringEncoder<String>("UTF-8"))
    // 生成 Bucket
   .withBucketAssigner(new DateTimeBucketAssigner<>("yyyyMMdd-HH-mm"))
```
如上代码所示，会生成如下样式的子目录：
```
localhost:script wy$ hadoop fs -ls hdfs://localhost:9000/flink/connector/file/row/
Found 1 items
drwxr-xr-x   - wy supergroup          0 2021-12-16 16:53 hdfs://localhost:9000/flink/connector/file/row/20211216-16-53
```

### 1.2 如何生成 Part 文件

#### 1.2.1 Part 生命周期

为了在下游系统中使用 FileSink 的输出，我们需要了解输出文件的命名和生命周期。Part 文件有三种状态：
- In-progress：正在写入的 Part 文件
- Pending ：In-progress 状态结束(根据滚动策略)，等待提交的文件
- Finished：在检查点成功 (STREAMING) 或输入结束 (BATCH) Pending 状态文件转换为 Finished 状态

只有处于 Finished 状态的文件才能被下游系统读取，因为这些文件保证后续不被修改。对于每个 Bucket 下每个子任务在任何给定时间下都只有一个 In-progress 状态的 Part 文件，但可以有多个 Pending 和 Finished 状态文件。

### 1.2.2 Part 文件示例

Finished 状态文件与 In-progress/Pending 状态文件能从文件名称上区分开。默认情况下，文件命名策略如下：
- In-progress/Pending：`part-<uid>-<partFileIndex>.inprogress.uid`
- Finished：`part-<uid>-<partFileIndex>`

其中 uid 是在子任务实例化时分配给 Sink 子任务的一个随机 ID。这个 uid 不是容错的，所以当子任务从故障中恢复时它会重新生成。为了更好地理解这些文件的生命周期，我们看一个有 2 个 Sink 子任务的简单示例：
```
└── 2019-08-25--12
    ├── part-4005733d-a830-4323-8291-8866de98b582-0.inprogress.bd053eb0-5ecf-4c85-8433-9eff486ac334
    └── part-81fc4980-a6af-41c8-9937-9939408a734b-0.inprogress.ea65a428-a1d0-4a0b-bbc5-7a436a75e575
```
当 Part 文件 part-81fc4980-a6af-41c8-9937-9939408a734b-0 滚动时（假设它变得太大），变为 Pending 状态但还未重命名。然后 Sink 创建一个新的 Part 文件：part-81fc4980-a6af-41c8-9937-9939408a734b-1：
```
└── 2019-08-25--12
    ├── part-4005733d-a830-4323-8291-8866de98b582-0.inprogress.bd053eb0-5ecf-4c85-8433-9eff486ac334
    ├── part-81fc4980-a6af-41c8-9937-9939408a734b-0.inprogress.ea65a428-a1d0-4a0b-bbc5-7a436a75e575
    └── part-81fc4980-a6af-41c8-9937-9939408a734b-1.inprogress.bc279efe-b16f-47d8-b828-00ef6e2fbd11
```
随着 part-81fc4980-a6af-41c8-9937-9939408a734b-0 的 Pending 状态结束，在下一个 Checkpoint 之后，变为 Finished 状态：
```
└── 2019-08-25--12
    ├── part-4005733d-a830-4323-8291-8866de98b582-0.inprogress.bd053eb0-5ecf-4c85-8433-9eff486ac334
    ├── part-81fc4980-a6af-41c8-9937-9939408a734b-0
    └── part-81fc4980-a6af-41c8-9937-9939408a734b-1.inprogress.bc279efe-b16f-47d8-b828-00ef6e2fbd11
```
新的 Bucket 是按照存储策略创建的，不会影响当前 In-progress 状态的文件，旧 Bucket 仍然可以接收新记录：
```
└── 2019-08-25--12
    ├── part-4005733d-a830-4323-8291-8866de98b582-0.inprogress.bd053eb0-5ecf-4c85-8433-9eff486ac334
    ├── part-81fc4980-a6af-41c8-9937-9939408a734b-0
    └── part-81fc4980-a6af-41c8-9937-9939408a734b-1.inprogress.bc279efe-b16f-47d8-b828-00ef6e2fbd11
└── 2019-08-25--13
    └── part-4005733d-a830-4323-8291-8866de98b582-0.inprogress.2b475fec-1482-4dea-9946-eb4353b475f1
```

### 1.2.3 Part 文件配置

Flink 允许为 Part 文件指定前缀或者后缀。这可以使用 OutputFileConfig 来完成。例如，对于前缀 'prefix' 和后缀 '.ext'，Sink 将创建以下文件：
```
└── 2019-08-25--12
    ├── prefix-4005733d-a830-4323-8291-8866de98b582-0.ext
    ├── prefix-4005733d-a830-4323-8291-8866de98b582-1.ext.inprogress.bd053eb0-5ecf-4c85-8433-9eff486ac334
    ├── prefix-81fc4980-a6af-41c8-9937-9939408a734b-0.ext
    └── prefix-81fc4980-a6af-41c8-9937-9939408a734b-1.ext.inprogress.bc279efe-b16f-47d8-b828-00ef6e2fbd11
```
用户可以通过以下方式指定 OutputFileConfig：
```
OutputFileConfig config = OutputFileConfig
 .builder()
 .withPartPrefix("prefix")
 .withPartSuffix(".ext")
 .build();

FileSink<Tuple2<Integer, Integer>> sink = FileSink
 .forRowFormat((new Path(outputPath), new SimpleStringEncoder<>("UTF-8"))
 .withBucketAssigner(new KeyBucketAssigner())
 .withRollingPolicy(OnCheckpointRollingPolicy.build())
 .withOutputFileConfig(config)
 .build();
```

#### 1.2.4 滚动策略

滚动策略 RollingPolicy 定义了文件如何滚动，包括 In-progress 状态的 Part 文件 何时关闭并把变为 Pending 状态以及控制文件大小等。只有处于 Finished 状态的 Part 文件才可以被查看。在 STREAMING 模式下，滚动策略与 Checkpoint 间隔（Pending 状态的文件在下一个 Checkpoint 之后变为 Finished 状态）共同控制 Part 文件多久之后可以让下游使用以及这些文件的大小和数量。在 BATCH 模式下，Part 文件在作业结束时可见，但滚动策略可以控制它们的最大大小。Flink 有两个内置的 RollingPolicies 策略：
- DefaultRollingPolicy
- OnCheckpointRollingPolicy

## 2. 文件格式

FileSink 支持按行(Row-Encoded)和批量(Bulk-Encoded)编码格式。这两个变体带有各自的构建器，可以使用以下静态方法创建：
- 行编码 Sink：FileSink.forRowFormat(basePath, rowEncoder)
- 批量编码 Sink：FileSink.forBulkFormat(basePath, bulkWriterFactory)

> 在创建行或者批量编码 Sink 时，我们必须指定 Bucket 的基础路径以及数据的编码逻辑。

### 2.1 Row-Encoded

Row-Encoded 格式需要指定一个 Encoder，用于将一行数据序列化到 Part 文件（In-progress 状态）的 OutputStream 中。除了 Bucket 分配器之外，RowFormatBuilder 还允许用户指定：
- RollingPolicy ：覆盖 DefaultRollingPolicy 的滚动策略
- bucketCheckInterval : 默认 1 min，基于滚动策略的检查时间毫秒间隔
```java
String outputPath = "hdfs://localhost:9000/flink/connector/file/row/";
final FileSink<String> sink = FileSink
        .forRowFormat(new Path(outputPath), new SimpleStringEncoder<String>("UTF-8"))
        // 生成 Bucket
        .withBucketAssigner(new DateTimeBucketAssigner<>("yyyyMMdd-HH-mm"))
        .withBucketCheckInterval(60L * 1000L)
        // 滚动策略
        .withRollingPolicy(
                DefaultRollingPolicy.builder()
                        // 包含至少 15 分钟的数据
                        .withRolloverInterval(TimeUnit.MINUTES.toMillis(15))
                        // 最近 5 分钟没有收到新记录
                        .withInactivityInterval(TimeUnit.MINUTES.toMillis(5))
                        // 文件大小已达到 1 GB
                        .withMaxPartSize(1024 * 1024 * 1024)
                        .build()
        )
        .build();
```
上面示例创建了一个简单的 Sink，将记录分配给默认的小时 Bucket。此外还指定了一个滚动策略，只要满足如下 3 个条件中的任何一个条件都会滚动生成 新的 Part 文件：
- 包含至少 15 分钟的数据（Part 文件最大打开持续时长）
- 最近 5 分钟没有收到新记录（不活跃的时间间隔）
- 文件大小已达到 1 GB（写入最后一条记录后）

### 2.2 Bulk-Encoded

Bulk-Encoded Sink 的创建类似于 Row-Encoded Sink，我们需要指定的是 BulkWriter.Factory 而不是 Encoder。BulkWriter 定义了如何添加和刷新新元素，以及如何最终确定一批记录以进一步编码。Flink 内置了四个 BulkWriter 工厂：
- ParquetWriterFactory
- AvroWriterFactory
- SequenceFileWriterFactory
- CompressWriterFactory
- OrcBulkWriterFactory

#### 2.2.1 Parquet 格式

Flink 包含内置的便捷方法，为 Avro 数据创建 Parquet 编写器工厂。为了写入其他 Parquet 兼容的数据格式，用户需要使用 ParquetBuilder 接口的自定义实现来创建 ParquetWriterFactory。如果要使用 Parquet 批量编码器，需要添加以下依赖项：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-parquet_2.11</artifactId>
    <version>1.14.0</version>
</dependency>
```
将 Avro 数据写入 Parquet 格式的 FileSink 可以这样创建：
```java
import org.apache.flink.connector.file.sink.FileSink;
import org.apache.flink.formats.parquet.avro.ParquetAvroWriters;
import org.apache.avro.Schema;

Schema schema = ...;
DataStream<GenericRecord> input = ...;

final FileSink<GenericRecord> sink = FileSink
	.forBulkFormat(outputBasePath, ParquetAvroWriters.forGenericRecord(schema))
	.build();

input.sinkTo(sink);
```
类似地，可以像这样创建将 Protobuf 数据写入 Parquet 格式的 FileSink：
```java
import org.apache.flink.connector.file.sink.FileSink;
import org.apache.flink.formats.parquet.protobuf.ParquetProtoWriters;

// ProtoRecord is a generated protobuf Message class.
DataStream<ProtoRecord> input = ...;

final FileSink<ProtoRecord> sink = FileSink
	.forBulkFormat(outputBasePath, ParquetProtoWriters.forType(ProtoRecord.class))
	.build();

input.sinkTo(sink);
```

#### 2.2.2 Avro 格式

Flink 还提供了将数据写入 Avro 文件的内置支持。可以在 AvroWriters 类中找到创建 Avro 编写器工厂的便捷方法列表。如果要使用 Avro 编写器，需要添加以下依赖项：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-avro</artifactId>
    <version>1.14.0</version>
</dependency>
```
可以像如下所示创建将数据写入 Avro 文件的 FileSink：
```java
import org.apache.flink.connector.file.sink.FileSink;
import org.apache.flink.formats.avro.AvroWriters;
import org.apache.avro.Schema;

Schema schema = ...;
DataStream<GenericRecord> input = ...;

final FileSink<GenericRecord> sink = FileSink
	.forBulkFormat(outputBasePath, AvroWriters.forGenericRecord(schema))
	.build();

input.sinkTo(sink);
```
如果要创建自定义的 Avro 编写器，例如，启用压缩，用户需要实现 AvroBuilder 接口来创建 AvroWriterFactory：
```java
AvroWriterFactory<?> factory = new AvroWriterFactory<>((AvroBuilder<Address>) out -> {
	Schema schema = ReflectData.get().getSchema(Address.class);
	DatumWriter<Address> datumWriter = new ReflectDatumWriter<>(schema);

	DataFileWriter<Address> dataFileWriter = new DataFileWriter<>(datumWriter);
	dataFileWriter.setCodec(CodecFactory.snappyCodec());
	dataFileWriter.create(schema, out);
	return dataFileWriter;
});

DataStream<Address> stream = ...
stream.sinkTo(FileSink.forBulkFormat(
	outputBasePath,
	factory).build());
```
#### 2.2.3 ORC 格式

为了使数据能够以 ORC 格式进行批量编码，Flink 提供了 OrcBulkWriterFactory，采用了 Vectorizer 的具体实现。与任何其他批量编码格式一样，Flink 的 OrcBulkWriter 也批量写入输入元素。并使用 ORC 的 VectorizedRowBatch 来实现。

由于必须将输入元素转换为 VectorizedRowBatch，因此用户必须扩展抽象 Vectorizer 类并覆盖 vectorize(T element, VectorizedRowBatch batch) 方法。 如您所见，该方法提供了一个 VectorizedRowBatch 实例供用户直接使用，因此用户只需编写逻辑将输入元素转换为 ColumnVectors 并将它们设置在提供的 VectorizedRowBatch 实例中。

例如，如果输入元素是 Person 类型，它看起来像：

#### 2.2.4 Hadoop SequenceFile 格式

如果要使用 SequenceFile 批量编码器，我们需要添加以下依赖项：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-sequence-file</artifactId>
    <version>1.14.0</version>
</dependency>
```
可以像这样创建一个简单的 SequenceFile 编写器：
```java
import org.apache.flink.connector.file.sink.FileSink;
import org.apache.flink.configuration.GlobalConfiguration;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.SequenceFile;
import org.apache.hadoop.io.Text;

DataStream<Tuple2<LongWritable, Text>> input = ...;
Configuration hadoopConf = HadoopUtils.getHadoopConfiguration(GlobalConfiguration.loadConfiguration());
final FileSink<Tuple2<LongWritable, Text>> sink = FileSink
  .forBulkFormat(
    outputBasePath,
    new SequenceFileWriterFactory<>(hadoopConf, LongWritable.class, Text.class))
	.build();

input.sinkTo(sink);
```
> SequenceFileWriterFactory 还可以支持其他的构造函数参数来指定压缩设置。





原文:[File Sink](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/connectors/datastream/file_sink/)
