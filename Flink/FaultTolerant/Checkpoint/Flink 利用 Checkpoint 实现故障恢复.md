---
layout: post
author: smartsi
title: Flink 利用 Checkpoint 实现故障恢复
date: 2020-12-26 18:26:17
tags:
  - Flink

categories: Flink
permalink: flink-restore-job-from-checkpoint
---

> Flink 1.13.5 版本

在本节中，我们将介绍 Flink 如何利用检查点 Checkpoint 实现故障恢复并保证精确一次 Exactly-Once 语义的一致性状态。

## 1. 配置

如果我们的任务已经执行很长时间，突然遇到故障停止，那么中间过程处理结果就会全部丢失，重启后如果需要重新从上线开始的位置消费，那么会花费我们很长的时间。这种结局显示我们不能接受，我们希望的是作业在故障失败重启后能保留之前的状态并能从失败的位置继续消费。这就需要 Flink 利用检查点 Checkpoint 实现故障恢复并保证精确一次 Exactly-Once 语义的一致性状态。可以通过如下配置设置 Checkpoint：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 配置 状态后端
env.setStateBackend(new HashMapStateBackend());
// 配置 Checkpoint 每30s触发一次Checkpoint 实际不用设置的这么大
env.enableCheckpointing(30*1000);
env.getCheckpointConfig().setCheckpointStorage(new JobManagerCheckpointStorage());
```
在这我们为了演示效果设置每 30s 触发一次 Checkpoint，在生产环境中一般设置的比较小，具体看业务需求。Checkpoint 快照持久化存储在 JobManager 内存中，也可以使用 FileSystemCheckpointStorage 将快照持久化到远程存储上。

Checkpoint 在默认的情况下仅用于恢复失败的作业，并不保留，当程序取消时 Checkpoint 就会被删除。你可以通过配置来保留 Checkpoint，这些被保留的 Checkpoint 在作业失败或取消时不会被清除。这样你就可以使用该 Checkpoint 来恢复作业。如下所示配置来设置在作业取消后 Checkpoint 数据不被删除：
```java
env.getCheckpointConfig().enableExternalizedCheckpoints(CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
```

## 2. 故障恢复

在执行流应用程序期间，Flink 会周期性的为应用状态生成一致性检查点。一旦发生故障，Flink 会利用最新的检查点将应用状态恢复到某个时间点并重启应用从对应时间点的位置继续消费数据。生成一致性检查点 Checkpoint 以及从 Checkpoint 中恢复的流程，可以查阅[Flink 容错机制 Checkpoint 生成与恢复流程](https://smartsi.blog.csdn.net/article/details/127019291)。

我们使用经典的 WordCount 示例演示如何利用 Checkpoint 实现故障恢复。为了模拟作业遇到脏数据处理失败，当我们输入的单词是 "ERROR" 时，抛出异常迫使作业失败：
```java
// 失败信号 模拟作业遇到脏数据
if (Objects.equals(word, "ERROR")) {
    throw new RuntimeException("custom error flag, restart application");
}
```
为了确保作业在失败后能自动恢复，我们设置了重启策略，失败后最多重启3次，每次重启间隔10s：
```java
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(3, 10000));
```
> 失败重启策略具体可以查阅 [Flink 任务失败重启与恢复策略](https://smartsi.blog.csdn.net/article/details/126451162)

发生故障时，Flink 会利用最新的检查点将应用状态恢复到某个时间点，应用程序也会重启从对应时间点的位置继续消费数据。这就要求除了有一个可以持久化状态的分布式存储，还需要一个可以重放一定时间内记录的数据源 Source。至于数据源是否可以重置它的输入流，需要取决于其实现方式以及所消费的外部系统是否提供相关的接口。Apache Kafka 消息中间件就可以允许从之前的某个偏移量位置读取数据，所以在这我们从 Kafka 中消费数据：
```java
// 配置 Kafka Consumer
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("group.id", "word-count");
props.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
props.put("auto.offset.reset", "latest");
String topic = "word";
FlinkKafkaConsumer<String> consumer = new FlinkKafkaConsumer<>(topic, new SimpleStringSchema(), props);
// Kafka Source
DataStream<String> source = env.addSource(consumer).uid("KafkaSource");
```
这种数据源就可以重置到检查点 Checkpoint 生成那一刻的偏移量，重新消费数据。

如下代码所示，我们从 Kafka 中消费单词数据流计算每个单词出现的个数：
```java
// 计算单词个数
SingleOutputStreamOperator<WordCount> result = source
        .map(new MapFunction<String, WordCount>() {
            @Override
            public WordCount map(String element) throws Exception {
                WordCount wordCount = gson.fromJson(element, WordCount.class);
                String word = wordCount.getWord();
                LOG.info("word: {}, frequency: {}", word, wordCount.getFrequency());
                // 失败信号 模拟作业遇到脏数据
                if (Objects.equals(word, "ERROR")) {
                    throw new RuntimeException("custom error flag, restart application");
                }
                return wordCount;
            }
        }).uid("Map")
        .keyBy(new KeySelector<WordCount, String>() {
            @Override
            public String getKey(WordCount element) throws Exception {
                return element.getWord();
            }
        })
        .sum("frequency").uid("Sum");

result.print().uid("Print");
```
> [代码地址](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/checkpoint/RestoreCheckpointExample.java)

> Source 任务会将输入流的当前偏移量存储为状态，而求和任务则将当前单词出现个数存储为状态。

实际效果如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-restore-job-from-checkpoint.png?raw=true)

下面我们结合运行日志，具体看一下实际是如何运行的。如下所示，应用程序上线之后从 Kafka Offset 25 开始消费数据，相继消费 'a', 'b', 'a' 三个单词后触发了第二次 Checkpoint。应用程序完成了最新一次的检查点，所有算子都将它们全部的状态写入检查点：
```java
14:27:08,425 INFO  org.apache.kafka.clients.consumer.internals.ConsumerCoordinator [] - [Consumer clientId=consumer-word-count-2, groupId=word-count] Setting offset for partition word-0 to the committed offset FetchPosition{offset=25, offsetEpoch=Optional.empty, currentLeader=LeaderAndEpoch{leader=Optional[127.0.0.1:9092 (id: 0 rack: null)], epoch=0}}
14:27:11,446 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 1 (type=CHECKPOINT) @ 1664519231424 for job be490495e90a14c2a924a89d6c99f5e1.
14:27:11,618 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 1 for job be490495e90a14c2a924a89d6c99f5e1 (3070 bytes in 191 ms).
14:27:18,029 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: a, frequency: 1
14:27:18,032 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: b, frequency: 1
14:27:18,032 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: a, frequency: 1
WordCount{word='a', frequency=1}
WordCount{word='b', frequency=1}
WordCount{word='a', frequency=2}
14:27:41,424 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Triggering checkpoint 2 (type=CHECKPOINT) @ 1664519261423 for job be490495e90a14c2a924a89d6c99f5e1.
14:27:41,446 INFO  org.apache.flink.runtime.checkpoint.CheckpointCoordinator    [] - Completed checkpoint 2 for job be490495e90a14c2a924a89d6c99f5e1 (3102 bytes in 21 ms).
```
继续消费数据，当任务消费到单词为 'ERROR' 时表示接收到了触发失败信号，任务抛出异常导致应用发生故障，如下所示：
```java
14:27:46,740 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: a, frequency: 1
14:27:46,741 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: c, frequency: 1
14:27:46,741 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: ERROR, frequency: 1
WordCount{word='a', frequency=3}
WordCount{word='c', frequency=1}
14:27:46,753 WARN  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Custom Source -> Map (1/1)#0 (bc761fd6563887dbdd72a2f6d4edecb7) switched from RUNNING to FAILED with failure cause: java.lang.RuntimeException: custom error flag, restart application
	at com.flink.example.stream.state.checkpoint.RestoreCheckpointExample$2.map(RestoreCheckpointExample.java:67)
	at com.flink.example.stream.state.checkpoint.RestoreCheckpointExample$2.map(RestoreCheckpointExample.java:59)
	at org.apache.flink.streaming.api.operators.StreamMap.processElement(StreamMap.java:38)
	at org.apache.flink.streaming.runtime.tasks.CopyingChainingOutput.pushToOperator(CopyingChainingOutput.java:71)
	at org.apache.flink.streaming.runtime.tasks.CopyingChainingOutput.collect(CopyingChainingOutput.java:46)
	at org.apache.flink.streaming.runtime.tasks.CopyingChainingOutput.collect(CopyingChainingOutput.java:26)
	at org.apache.flink.streaming.api.operators.CountingOutput.collect(CountingOutput.java:50)
	at org.apache.flink.streaming.api.operators.CountingOutput.collect(CountingOutput.java:28)
	at org.apache.flink.streaming.api.operators.StreamSourceContexts$ManualWatermarkContext.processAndCollectWithTimestamp(StreamSourceContexts.java:322)
	at org.apache.flink.streaming.api.operators.StreamSourceContexts$WatermarkContext.collectWithTimestamp(StreamSourceContexts.java:426)
	at org.apache.flink.streaming.connectors.kafka.internals.AbstractFetcher.emitRecordsWithTimestamps(AbstractFetcher.java:365)
	at org.apache.flink.streaming.connectors.kafka.internals.KafkaFetcher.partitionConsumerRecordsHandler(KafkaFetcher.java:183)
	at org.apache.flink.streaming.connectors.kafka.internals.KafkaFetcher.runFetchLoop(KafkaFetcher.java:142)
	at org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumerBase.run(FlinkKafkaConsumerBase.java:826)
	at org.apache.flink.streaming.api.operators.StreamSource.run(StreamSource.java:110)
	at org.apache.flink.streaming.api.operators.StreamSource.run(StreamSource.java:66)
	at org.apache.flink.streaming.runtime.tasks.SourceStreamTask$LegacySourceFunctionThread.run(SourceStreamTask.java:269)
```
在应用发生故障后，应用程序重新启动并将所有有状态任务的状态重置为最新一次检查点的状态，Source 任务的所有输入流的消费位置也重置到检查点生成那一刻的 Offset，即消费位置 28：
```
14:27:56,865 INFO  org.apache.kafka.clients.consumer.KafkaConsumer              [] - [Consumer clientId=consumer-word-count-4, groupId=word-count] Subscribed to partition(s): word-0
14:27:56,865 INFO  org.apache.kafka.clients.consumer.KafkaConsumer              [] - [Consumer clientId=consumer-word-count-4, groupId=word-count] Seeking to offset 28 for partition word-0
14:27:56,868 INFO  org.apache.kafka.clients.Metadata                            [] - [Consumer clientId=consumer-word-count-4, groupId=word-count] Cluster ID: LTQOkEmPSuO-kRNROoxpHg
14:27:56,872 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: a, frequency: 1
14:27:56,872 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: c, frequency: 1
WordCount{word='a', frequency=3}
WordCount{word='c', frequency=1}
```
应用程序重启后会重新消费数据并重新处理从检查点生成到系统发生故障之间的所有数据，在这会重新消费单词 'a'、'c' 以及 'ERROR'。这意味着这部分数据记录会被 Flink 重复处理，但仍然可以实现 Exactly-Once 语义的一致性状态，因为所有算子的状态都会重置到过去还没处理过那些数据的时间点，即这些数据记录只会对状态作用一次。注意此时计算的输出结果，不是从 0 开始计数，也不是基于失败时那一刻的状态计数，而是基于最新一次检查点的状态计算的。这时的计算结果正是我们想要的正确结果。

当任务再次消费到 'ERROR' 时应用再次发生故障：
```java
14:27:56,872 INFO  com.flink.example.stream.state.checkpoint.RestoreCheckpointExample [] - word: ERROR, frequency: 1
14:27:56,879 WARN  org.apache.flink.runtime.taskmanager.Task                    [] - Source: Custom Source -> Map (1/1)#1 (82f61c405cecd3242a5c7d0c3535ccad) switched from RUNNING to FAILED with failure cause: java.lang.RuntimeException: custom error flag, restart application
	at com.flink.example.stream.state.checkpoint.RestoreCheckpointExample$2.map(RestoreCheckpointExample.java:67)
	at com.flink.example.stream.state.checkpoint.RestoreCheckpointExample$2.map(RestoreCheckpointExample.java:59)
	at org.apache.flink.streaming.api.operators.StreamMap.processElement(StreamMap.java:38)
	at org.apache.flink.streaming.runtime.tasks.CopyingChainingOutput.pushToOperator(CopyingChainingOutput.java:71)
	at org.apache.flink.streaming.runtime.tasks.CopyingChainingOutput.collect(CopyingChainingOutput.java:46)
	at org.apache.flink.streaming.runtime.tasks.CopyingChainingOutput.collect(CopyingChainingOutput.java:26)
	at org.apache.flink.streaming.api.operators.CountingOutput.collect(CountingOutput.java:50)
	at org.apache.flink.streaming.api.operators.CountingOutput.collect(CountingOutput.java:28)
	at org.apache.flink.streaming.api.operators.StreamSourceContexts$ManualWatermarkContext.processAndCollectWithTimestamp(StreamSourceContexts.java:322)
	at org.apache.flink.streaming.api.operators.StreamSourceContexts$WatermarkContext.collectWithTimestamp(StreamSourceContexts.java:426)
	at org.apache.flink.streaming.connectors.kafka.internals.AbstractFetcher.emitRecordsWithTimestamps(AbstractFetcher.java:365)
	at org.apache.flink.streaming.connectors.kafka.internals.KafkaFetcher.partitionConsumerRecordsHandler(KafkaFetcher.java:183)
	at org.apache.flink.streaming.connectors.kafka.internals.KafkaFetcher.runFetchLoop(KafkaFetcher.java:142)
	at org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumerBase.run(FlinkKafkaConsumerBase.java:826)
	at org.apache.flink.streaming.api.operators.StreamSource.run(StreamSource.java:110)
	at org.apache.flink.streaming.api.operators.StreamSource.run(StreamSource.java:66)
	at org.apache.flink.streaming.runtime.tasks.SourceStreamTask$LegacySourceFunctionThread.run(SourceStreamTask.java:269)
```
就这样重新启动重置为最新一次检查点的状态（重置消费位点），消费到 'ERROR' 时再次发生故障，一直反复直到到达最大重启次数时程序彻底失败。整个运行过程可以用如下表格表示：

| 记录Id | 数据记录 | 输出结果 | 备注 |
| :------------- | :------------- | :------------- | :------------- |
|         |         |       | 触发 Checkpoint 1 |
| 1       | a       | (a,1) | Offset 25 |
| 2       | b       | (b,1) | Offset 26 |
| 3       | a       | (a,2) | Offset 27 |
|         |         |       | 触发 Checkpoint 2 |
| 4       | a       | (a,3) | Offset 28 |
| 5       | c       | (c,1) | Offset 29 |
| 6       | ERROR   |       | Offset 30 作业第一次重启 |
| 4       | a       | (a,3) | 重置 Offset 为 28 |
| 5       | c       | (c,1) | 继续消费 Offset 29 |
| 6       | ERROR   |       | 继续消费 Offset 30 作业第二次重启 |
| 4       | a       | (a,3) | 重置 Offset 为 28 |
| 5       | c       | (c,1) | 继续消费 Offset 29 |
| 6       | ERROR   |       | 继续消费 Offset 30 作业第三次重启 |

从上表中可以看出单词 'a'、'c' 以及 'ERROR'（分别对应记录Id为 4、5、6的数据记录）会被 Flink 重复处理，虽然可以实现 Exactly-Once 语义的一致性状态，并输出正确结果。但这些结果记录会向下游系统发送多次，所以需要根据业务需求选择对应的策略，例如采用具有精确一次输出的 Sink 算子或者使用支持幂等更新的存储系统。

> 检查点和恢复机制仅能重置流式应用内部的状态，只能实现状态的 Exactly-Once 语义，并不能保证端到端的处理 Exactly-Once 语义。
