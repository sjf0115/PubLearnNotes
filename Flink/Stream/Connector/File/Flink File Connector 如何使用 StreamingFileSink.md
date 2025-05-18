
Connector 提供了一个 Sink，可以将分区文件写入 Flink 支持的 FileSystem 抽象文件系统。

由于在流式处理应用中输入可能是无限的，因此流式文件接收器将数据写入分桶中。分桶行为是可配置的，但有用的默认值是基于时间的分桶，我们每小时都会写到一个新的分桶中，从而获得每个包含无限输出流一部分的单个文件。

在一个分桶中，我们根据滚动策略进一步将输出拆分为较小的部分文件。这对于防止单个分桶文件变得太大非常有用。这也是可配置的，但默认策略是根据文件大小和超时时间来滚动文件，例如，没有新数据写入部分文件。

StreamingFileSink 支持行式编码格式和批量编码格式，例如 Apache Parquet。

### 1. 行式编码输出格式

唯一需要我们配置的是我们要输出数据的基本路径以及为每个文件将记录序列化到 OutputStream 的编码器。基本用法如下所示：

Java版本：
```java
import org.apache.flink.api.common.serialization.SimpleStringEncoder;
import org.apache.flink.core.fs.Path;
import org.apache.flink.streaming.api.functions.sink.filesystem.StreamingFileSink;

DataStream<String> input = ...;

final StreamingFileSink<String> sink = StreamingFileSink
	.forRowFormat(new Path(outputPath), new SimpleStringEncoder<>("UTF-8"))
	.build();

input.addSink(sink);
```
Scala版本:
```Scala
import org.apache.flink.api.common.serialization.SimpleStringEncoder
import org.apache.flink.core.fs.Path
import org.apache.flink.streaming.api.functions.sink.filesystem.StreamingFileSink

val input: DataStream[String] = ...

val sink: StreamingFileSink[String] = StreamingFileSink
    .forRowFormat(new Path(outputPath), new SimpleStringEncoder[String]("UTF-8"))
    .build()

input.addSink(sink)
```
上面会创建一个流式接收器，使用默认滚动策略每小时创建一个分桶。默认存储分配器是 [DateTimeBucketAssigner](https://ci.apache.org/projects/flink/flink-docs-release-1.8/api/java/org/apache/flink/streaming/api/functions/sink/filesystem/bucketassigners/DateTimeBucketAssigner.html)，默认滚动策略是 [DefaultRollingPolicy](https://ci.apache.org/projects/flink/flink-docs-release-1.8/api/java/org/apache/flink/streaming/api/functions/sink/filesystem/rollingpolicies/DefaultRollingPolicy.html)。

### 2. 批量编码输出格式

在上面的例子中，我们使用了一个可以单独编码或序列化每个记录的编码器。流式文件接收器还支持批量编码的输出格式，例如 Apache Parquet。 要使用这个编码格式，只需要我们使用 `StreamingFileSink.forBulkFormat()` 代替 `StreamingFileSink.forRowFormat()`，并指定 `BulkWriter.Factory`。

`ParquetAvroWriters` 有一个静态方法可以为各种类型创建 `BulkWriter.Factory`。

> 批量编码格式只能与 `OnCheckpointRollingPolicy` 结合使用，它会在每个检查点上滚动正在进行的部分文件。

https://issues.apache.org/jira/browse/FLINK-9749

英译对照
- 分桶：buckets
- 部分文件：part file
- 行式编码格式：row-wise encoding formats
- 批量编码格式：bulk-encoding encoding formats

原文:[Streaming File Sink](https://ci.apache.org/projects/flink/flink-docs-stable/dev/connectors/streamfile_sink.html)
