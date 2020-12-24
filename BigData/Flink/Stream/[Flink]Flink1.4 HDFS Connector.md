---
layout: post
author: sjf0115
title: Flink HDFS Connector
date: 2018-03-02 14:30:17
tags:
  - Flink
  - Flink Stream

categories: Flink
permalink: flink-stream-hdfs-connector
---

此连接器提供一个 `Sink`，将分区文件写入 `Hadoop FileSystem` 支持的任何文件系统。要使用此连接器，添加以下依赖项：
```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-connector-filesystem_2.11</artifactId>
  <version>1.7.0</version>
</dependency>
```

### 分桶文件Sink

分桶(Bucketing)行为以及写入数据操作都可以配置，我们稍后会讲到。下面展示如何通过默认配置创建分桶Sink，输出到按时间切分的滚动文件中：

Java版本:
```java
DataStream<String> input = ...;
input.addSink(new BucketingSink<String>("/base/path"));
```

Scala版本:
```scala
val input: DataStream[String] = ...
input.addSink(new BucketingSink[String]("/base/path"))
```

这里唯一需要的参数是这些分桶存储的基本路径 `/base/path`。可以通过指定自定义 `bucketer`，`writer` 和 `batch size` 来进一步配置 `sink`。

默认情况下，分桶 `Sink` 根据元素到达时的系统时间来进行切分，并使用 `yyyy-MM-dd--HH` 时间格式来命名这些分桶。这个时间格式会跟当前系统时间一起传递给 `SimpleDateFormat` 来命名分桶路径。用户还可以为 `bucketer` 指定时区以格式化分桶路径。每当遇到一个新的时间就会创建一个新的分桶。例如，如果你有一个包含分钟的最细粒度时间格式，那么你每分钟都会获得一个新的分桶。每个分桶本身就是一个包含部分文件的目录：`Sink` 的每个并行实例都会创建自己的那部分文件，当部分文件变得太大时，会紧挨着其他文件创建一个新的部分文件。当一个分桶最近没有被写入数据时被视为非活跃，将刷写(flush)并关闭打开的部分文件。默认情况下，`Sink` 每分钟都会检查非活跃的分桶，并关闭一分钟以上没有写入数据的分桶。可以在 `BucketingSink上` 使用 `setInactiveBucketCheckInterval()` 和 `setInactiveBucketThreshold()` 配置这些行为。

你还可以在 `BucketingSink上` 上使用 `setBucketer()` 指定自定义的 `bucketer`。如果需要，`bucketer` 可以使用元素或元组的属性来确定 `bucket`目录。

默认的 `writer` 是`StringWriter`。对传入的元素调用 `toString()`，并将它们写入部分文件，并用换行符进行分隔。要在 `BucketingSink` 上指定一个自定义的 `writer`，使用 `setWriter()` 方法即可。如果要写入 `Hadoop SequenceFiles` 文件中，可以使用提供的 `SequenceFileWriter`，并且可以配置使用压缩格式。

有两个配置参数可以指定何时应关闭部分文件并启动一个新的部分文件：
- 通过设置批量大小(`batch size`)（默认部件文件大小为384 MB）。
- 通过设置批次滚动时间间隔（默认滚动间隔为`Long.MAX_VALUE`）。

当满足这两个条件中的任何一个时，会启动一个的部分文件。

Java版本:
```java
DataStream<Tuple2<IntWritable,Text>> input = ...;

BucketingSink<String> sink = new BucketingSink<String>("/base/path");
sink.setBucketer(new DateTimeBucketer<String>("yyyy-MM-dd--HHmm", ZoneId.of("America/Los_Angeles")));
sink.setWriter(new SequenceFileWriter<IntWritable, Text>());
sink.setBatchSize(1024 * 1024 * 400); // this is 400 MB,
sink.setBatchRolloverInterval(20 * 60 * 1000); // this is 20 mins

input.addSink(sink);
```

Scala版本:
```scala
val input: DataStream[Tuple2[IntWritable, Text]] = ...

val sink = new BucketingSink[String]("/base/path")
sink.setBucketer(new DateTimeBucketer[String]("yyyy-MM-dd--HHmm", ZoneId.of("America/Los_Angeles")))
sink.setWriter(new SequenceFileWriter[IntWritable, Text]())
sink.setBatchSize(1024 * 1024 * 400) // this is 400 MB,
sink.setBatchRolloverInterval(20 * 60 * 1000); // this is 20 mins

input.addSink(sink)
```
上面例子将创建一个 `Sink`，写入遵循下面格式的分桶文件中：
```
/base/path/{date-time}/part-{parallel-task}-{count}
```
其中 `date-time` 是从日期/时间格式获得的字符串，`parallel-task` 是并行 `Sink` 实例的索引，`count` 是由于批次大小或者滚动时间间隔而创建的部分文件的运行编号。

> Flink 版本:1.7

原文:[HDFS Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/connectors/filesystem_sink.html)
