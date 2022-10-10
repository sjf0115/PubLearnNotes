---
layout: post
author: sjf0115
title: Spark Streaming 2.2.0 性能调优
date: 2018-04-06 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-performance-tuning
---

> Spark 版本：2.2.0

Spark Streaming 应用程序要获得最佳性能需要做一些调整优化。这篇文章我们介绍可以提高你应用程序性能的参数以及配置。从高层次来看，你需要关心两件事情:
- 通过充分利用集群资源，减少每批次数据的处理时间。
- 设置合理的批次大小，从而尽可能快的处理每批次的数据，即数据处理速度与数据接收速度保持一致。

## 1. 减少每批次的处理时间

在 Spark 中可以进行许多优化来减少每批次的处理时间。这些已在 [Tuning Guide](https://spark.apache.org/docs/2.2.0/tuning.html) 中详细讨论。在这重点介绍了一些最重要的优化点。

### 1.1 提升数据接收的并行度

通过网络接收数据（如Kafka，Flume，Socket等）需要将数据反序列化并存储在 Spark 中。如果数据接收成为系统的瓶颈，则需要考虑并行化接收数据。

#### 1.1.1 提升 Receiver 的并发度

每一个输入 DStream 都会创建一个 Receiver（运行在 Worker 节点上）来单独接收一个数据流。因此，可以通过创建多个输入 DStream 以及配置分别从 Source 不同分区接收数据流，从而可以实现接收多个数据流。例如，一个接收两个 Topic 数据的 Kafka 输入 DStream 可以拆分成两个 Kafka 输入 DStream，每个仅仅接收一个 Topic 数据。这样可以运行两个 Receiver 并行接收数据，从而提高整体吞吐量。这些多个 DStream 可以合并(union)在一起创建一个 DStream。这样应用在一个输入 DStream 上的转换操作可以统一应用在整合后的数据流上。具体如下所示：
```java
int numStreams = 5;
List<JavaPairDStream<String, String>> kafkaStreams = new ArrayList<>(numStreams);
for (int i = 0; i < numStreams; i++) {
  kafkaStreams.add(KafkaUtils.createStream(...));
}
JavaPairDStream<String, String> unifiedStream = streamingContext.union(kafkaStreams.get(0), kafkaStreams.subList(1, kafkaStreams.size()));
unifiedStream.print();
```

#### 1.1.2 调整 Receiver 的 Block 间隔

另一个应该考虑的参数是 Receiver 的 Block 间隔（通过 `spark.streaming.blockInterval` 配置）。对于大多数 Receiver，接收到的数据在存储到 Spark 内存之前会合并为大的 Block。每个批次中 Block 的个数决定了任务的个数，这些任务用来处理类似 map 转换操作中接收到的数据。Receiver 中每批次的任务个数大约等于 `批次间隔 / Block 间隔`。例如，200 ms 的 Block 间隔会在每 2s 的批次中生成 10 个 Block，即对应创建 10 个任务。如果任务个数太少（少于每台机器的 core 数）会导致效率变低，因为会有空闲的核没有用来处理数据。如果要增加一个批次间隔的任务个数，需要降低 Block 间隔。但是，建议 Block 间隔最小为 50 毫秒，如果低于该值，任务启动开销可能会有问题。

使用多输入流/ Receiver 接收数据的另一种方法是显式对输入数据流重新分区（使用 `inputStream.repartition（<分区个数>）`）。这会在进一步处理之前将收到的批量数据分布到集群中指定数量的机器上。

### 1.2 提升数据处理的并行度

如果在计算阶段使用的并行任务数量不够多，那么会造成集群资源不能充分利用。例如，对于像 reduceByKey 和 reduceByKeyAndWindow 这样的分布式 Reduce 操作，并行任务的默认数量由 `spark.default.parallelism` 参数控制。你可以将并行度作为参数传递进来，或者修改 `spark.default.parallelism` 参数来更改默认值。

#### 1.2.1 数据序列化

通过调整序列化格式可以减少数据序列化的开销。在流处理中，有两种类型的数据需要被序列化：
- 输入数据：默认情况下，通过 Receiver 接收的输入数据通过 `StorageLevel.MEMORY_AND_DISK_SER_2` 存储 Executor 的内存中。也就是说，将数据序列化为字节可以降低 GC 开销，并进行备份来实现 Executor 的故障容错。另外，数据首先保存在内存中，只有当内存不足以保存流式计算所需的所有输入数据时才会溢出到磁盘上。这种序列化显然开销有点大：Receiver 必须反序列化接收到的数据，并且使用 Spark 的序列化方式重新序列化它。  
- 流处理操作生成的持久 RDD：通过流式计算生成的 RDD 可以持久存储在内存中。例如，窗口操作会将数据保存在内存中，因为它们会被多次处理。但是，与 Spark Core 默认值 `StorageLevel.MEMORY_ONLY` 不同，流式计算生成的持久化 RDD 默认使用 `StorageLevel.MEMORY_ONLY_SER`（即序列化）持久化存储，来最大限度地降低 GC 开销。

在这两种情况下，使用 Kryo 序列化都可以减少 CPU 和内存开销。有关更多详细信息，请参阅[Spark性能优化指南](http://spark.apache.org/docs/latest/tuning.html#data-serialization)。对于 Kryo，需要考虑注册自定义类，并禁用对象引用跟踪。

在流应用程序保留数据量不大的情况下，将数据（两种类型）以反序列化对象保存也可能不会导致过多的 GC 开销。例如，如果您使用几秒钟的批次间隔并且没有窗口操作，那么可以尝试通过设置存储级别来禁用持久数据中的序列化。这样可以减少由于串行化而导致的 CPU 开销，从而可能会在不增加太多 GC 开销的情况下提高性能。

#### 1.2.2 任务启动开销

如果每秒启动的任务数很高（例如每秒50或更多），那么向 Slaves 发送任务的开销可能会很大，并且很难实现亚秒级别的延迟。可以通过以下更改来降低开销：
- 执行模式：在 Standalone 或粗粒度 Mesos 模式下运行 Spark 会导致比细粒度 Mesos 模式更好的任务启动时间。请参阅 [Running on Mesos指南](http://spark.apache.org/docs/latest/running-on-mesos.html) 获取更多详细信息。

这些更改可能会将批处理时间减少100毫秒，从而实现亚秒级别批处理大小。

## 2. 设置合适的批次间隔

为了确保 Spark Streaming 应用程序在集群上稳定的运行，系统应该能够以接收数据的速度处理数据。换句话说，数据批处理的速度应该跟接收速度至少一样快。查看一个应用程序是否符合预期，可以通过监控 Web UI 中的处理时间来发现，其中批处理时间应该要小于批处理间隔。

根据流式计算的性质，使用的批次间隔可能会对应用程序可以维持的数据速率产生重大影响。例如，让我们考虑一下之前的 WordCount 示例。对于一个恒定的数据速率，系统可以保持每 2 秒（即 2 秒的批次间隔）输出每个单词的出现次数，但是每 500 毫秒就无法保持。因此需要设置合理的批次间隔，以便可以保持生产中的预期数据速率。

为您的应用找出合适的批次大小的一个好方法是以保守的批次间隔（比如5-10秒）和低数据速率对其进行测试。为了验证系统是否能够跟上数据速率，可以检查每个批次处理所需要的端到端延迟（可以在 Spark 驱动程序 log4j 日志中查找 'Total delay'，也可以使用 StreamingListener 接口）。如果延迟与批次大小保持相当，那么系统就是稳定的。如果延迟一直在增加，那么意味着系统处理无法跟上，因此不稳定。一旦你有了一个稳定的配置，你就可以尝试提高数据速率和/或减少批次大小。需要注意的是只要延迟降低到低值（即小于批次大小），由于临时数据速率增加导致延迟的瞬间增加是可以接受的。

原文：http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#performance-tuning
