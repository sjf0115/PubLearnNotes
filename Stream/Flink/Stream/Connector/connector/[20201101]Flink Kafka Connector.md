---
layout: post
author: sjf0115
title: Flink Kafka Connector
date: 2020-11-01 16:19:17
tags:
  - Flink
  - Flink Stream

categories: Flink
permalink: flink-kafka-connector
---

## 1. 依赖

> Flink版本：1.11.2

Apache Flink 内置了多个 Kafka Connector：通用、0.10、0.11等。这个通用的 Kafka Connector 会尝试追踪最新版本的 Kafka 客户端。不同 Flink 发行版之间其使用的客户端版本可能会发生改变。现在的 Kafka 客户端可以向后兼容 0.10.0 或更高版本的 Broker。对于大多数用户使用通用的 Kafka Connector 就可以了。但对于 0.11.x 和 0.10.x 版本的 Kafka 用户，我们建议分别使用专用的 0.11 和 0.10 Connector。有关 Kafka 兼容性的详细信息，请参阅 [Kafka官方文档](https://kafka.apache.org/protocol.html#protocol_compatibility)。

通用 Connector：
```xml
<dependency>
	<groupId>org.apache.flink</groupId>
	<artifactId>flink-connector-kafka_2.11</artifactId>
	<version>1.11.2</version>
</dependency>
```
0.11 Connector：
```xml
<dependency>
	<groupId>org.apache.flink</groupId>
	<artifactId>flink-connector-kafka-011_2.11</artifactId>
	<version>1.11.2</version>
</dependency>
```
0.10 Connector：
```xml
<dependency>
	<groupId>org.apache.flink</groupId>
	<artifactId>flink-connector-kafka-010_2.11</artifactId>
	<version>1.11.2</version>
</dependency>
```
> 0.10 Connector 不支持对 Kafka 的 Exactly-once 写入。

下面是老版本的 Connector 介绍：

| Maven|开始支持版本|消费者与生产者类名|Kafka版本|备注
|---|---|---|---|---
| flink-connector-kafka-0.8_2.11|1.0.0|FlinkKafkaConsumer08、FlinkKafkaProducer08|0.8.x|使用 [SimpleConsumer](https://cwiki.apache.org/confluence/display/KAFKA/0.8.0+SimpleConsumer+Example) API。偏移量被提交到ZooKeeper上。|
| flink-connector-kafka-0.9_2.11|1.0.0|FlinkKafkaConsumer09、FlinkKafkaProducer09|0.9.x|使用新版 [Consumer](http://kafka.apache.org/documentation.html#newconsumerapi) API。|
| flink-connector-kafka-0.10_2.11|1.2.0|FlinkKafkaConsumer010、FlinkKafkaProducer010|0.10.x|这个连接器支持生产与消费的[带时间戳的Kafka消息](https://cwiki.apache.org/confluence/display/KAFKA/KIP-32+-+Add+timestamps+to+Kafka+message)。|
| flink-connector-kafka-0.11_2.11|1.4.0|FlinkKafkaConsumer011、FlinkKafkaProducer011|0.11.x| Kafka 0.11.x 版本不支持 scala 2.10 版本。此连接器支持 [Kafka 事务消息](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging) 可以为生产者提供 Exactly-Once 语义。|
| flink-connector-kafka_2.11 | 1.7.0 | FlinkKafkaConsumer、FlinkKafkaProducer | >= 1.0.0 | 这是一个通用的 Kafka 连接器，会追踪最新版本的 Kafka 客户端。|

## 2. Kafka消费者

Flink 的 Kafka 消费者：FlinkKafkaConsumer（对于 Kafka 0.11.x 版本为 FlinkKafkaConsumer011，对于 Kafka 0.10.x 版本为 FlinkKafkaConsumer010) 提供了可以访问一个或多个 Kafka Topic 的功能。

Kafka 消费者的构造函数接受如下参数:
- Kafka Topic 名称或者 Kafka Topic 名称列表
- 用于反序列化 Kafka 数据的 DeserializationSchema / KafkaDeserializationSchema
- Kafka 消费者的配置。需要以下属性：`bootstrap.servers`(逗号分隔的 Kafka broker 列表、`zookeeper.connect`(逗号分隔的 Zookeeper 服务器)(对于 Kafka 0.8 是必需的)、`group.id`(消费组的Id)。

Java版本:
```Java
Properties properties = new Properties();
properties.setProperty("bootstrap.servers", "localhost:9092");
// 根据版本判断是否使用
properties.setProperty("zookeeper.connect", "localhost:2181");
properties.setProperty("group.id", "test");
properties.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
properties.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
FlinkKafkaConsumer consumer = new FlinkKafkaConsumer<>("topic", new SimpleStringSchema(), properties);
DataStream<String> stream = env.addSource(consumer);
```

Scala版本:
```
val properties = new Properties()
properties.setProperty("bootstrap.servers", "localhost:9092")
properties.setProperty("group.id", "test")
properties.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
properties.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
stream = env
    .addSource(new FlinkKafkaConsumer[String]("topic", new SimpleStringSchema(), properties))
```

### 2.1 DeserializationSchema

Flink Kafka 消费者需要知道如何将 Kafka 中的二进制数据转换为 Java/Scala 对象。DeserializationSchema 可以允许用户指定这样的一个 Schema。每个 Kafka 消息都会调用 `T deserialize(ConsumerRecord<byte[], byte[]> record)` 方法。

为了使用方便，Flink 提供如下开箱即用的 Schema：
- TypeInformationSerializationSchema(以及 TypeInformationKeyValueSerializationSchema) 会基于 Flink 的 TypeInformation 创建 Schema。对 Flink 读写数据会非常有用。这个 Schema 是其他通用序列化方法的高性能替代方案。
- JsonDeserializationSchema(以及 JSONKeyValueDeserializationSchema)将序列化的 JSON 转换为 ObjectNode 对象，可以使用 `objectNode.get("field").as(Int/String/...)()` 方法访问某个字段。KeyValue objectNode 包含一个"key"和"value"字段，这包含了所有字段，以及一个可选的"metadata"字段，可以用来查询此消息的偏移量/分区/主题。
- AvroDeserializationSchema 使用静态 Schema 读取 Avro 格式的序列化的数据。可以从 Avro 生成的类(`AvroDeserializationSchema.forSpecific(...)`) 中推断出 Schema，也可以使用 GenericRecords 手动提供 Schema（`AvroDeserializationSchema.forGeneric(...)`）。这个反序列化 Schema 要求序列化记录不能包含嵌套 Schema。

如果要使用 Avro 这种 Schema，必须添加如下依赖：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-avro</artifactId>
    <version>1.11.2</version>
</dependency>
```

当遇到由于某种原因无法反序列化某个损坏消息时，反序列化 Schema 会返回 null，这会导致这条记录被跳过。由于 Consumer 的容错能力，如果在损坏的消息上让作业失败，那么 Consumer 会再次尝试反序列化该消息。如果反序列化仍然失败，则 Consumer 会陷入该消息的不断重启与失败的循环中。

### 2.2 起始位置配置

Flink Kafka Consumer 可以配置如何确定 Kafka 分区的起始位置。

Java版本:
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

FlinkKafkaConsumer<String> myConsumer = new FlinkKafkaConsumer<>(...);
// 从最早的记录开始消费
myConsumer.setStartFromEarliest();
// 从最近的记录开始消费
myConsumer.setStartFromLatest();
// 从指定时间戳(毫秒)开始消费
myConsumer.setStartFromTimestamp(...);
// 默认行为 从指定消费组偏移量开始消费
myConsumer.setStartFromGroupOffsets();

DataStream<String> stream = env.addSource(myConsumer);
...
```
Scala版本:
```scala
val env = StreamExecutionEnvironment.getExecutionEnvironment()

val myConsumer = new FlinkKafkaConsumer[String](...)
myConsumer.setStartFromEarliest()      // start from the earliest record possible
myConsumer.setStartFromLatest()        // start from the latest record
myConsumer.setStartFromTimestamp(...)  // start from specified epoch timestamp (milliseconds)
myConsumer.setStartFromGroupOffsets()  // the default behaviour

val stream = env.addSource(myConsumer)
...
```

Flink 所有版本的 Kafka Consumer 都具有上述配置起始位置的方法：
- setStartFromGroupOffsets（默认行为）：从消费者组（通过消费者属性 `group.id` 配置）提交到 Kafka Broker（Kafka 0.8 版本提交到 ZooKeeper）的偏移量开始读取分区。如果找不到分区的偏移量，会使用 `auto.offset.reset` 属性中的配置。
- setStartFromEarliest()/setStartFromLatest()：读取最早/最新记录。在这个模式下，提交到 Kafka 偏移量可以忽略，不用作起始位置。
- setStartFromTimestamp(long)：从指定的时间戳开始读取。对于每个分区，第一个大于或者等于指定时间戳的记录会被用作起始位置。如果分区的最新记录早于时间戳，则分区简单的读取最新记录即可。在这个模式下，提交到 Kafka 偏移量可以忽略，不用作起始位置。

你还可以为 Consumer 指定每个分区应该开始的确切偏移量：

Java版本:
```java
Map<KafkaTopicPartition, Long> specificStartOffsets = new HashMap<>();
specificStartOffsets.put(new KafkaTopicPartition("myTopic", 0), 23L);
specificStartOffsets.put(new KafkaTopicPartition("myTopic", 1), 31L);
specificStartOffsets.put(new KafkaTopicPartition("myTopic", 2), 43L);

myConsumer.setStartFromSpecificOffsets(specificStartOffsets);
```
Scala版本:
```scala
val specificStartOffsets = new java.util.HashMap[KafkaTopicPartition, java.lang.Long]()
specificStartOffsets.put(new KafkaTopicPartition("myTopic", 0), 23L)
specificStartOffsets.put(new KafkaTopicPartition("myTopic", 1), 31L)
specificStartOffsets.put(new KafkaTopicPartition("myTopic", 2), 43L)

myConsumer.setStartFromSpecificOffsets(specificStartOffsets)
```

上面的示例配置 Consumer 从 myTopic 主题的 0、1 和 2 分区的指定偏移量开始消费。偏移量是 Consumer 读取每个分区的下一条记录。需要注意的是如果 Consumer 需要读取的分区在提供的偏移量 Map 中没有指定偏移量，那么自动转换为默认的消费组偏移量。

> 当作业从故障中自动恢复或使用保存点手动恢复时，这些起始位置配置方法不会影响起始位置。在恢复时，每个 Kafka 分区的起始位置由存储在保存点或检查点中的偏移量确定。

### 2.3 容错

当 Flink 启动检查点时，Consumer 会从 Topic 中消费记录，并定期对 Kafka 偏移量以及其他算子的状态进行 Checkpoint。如果作业失败，Flink 会从最新检查点的状态恢复流处理程序，并从保存在检查点中的偏移量重新开始消费来自 Kafka 的记录。

因此，检查点间隔定义了程序在发生故障时最多可以回退多少。要使用容错的 Kafka Consumer，需要在作业中开启拓扑的检查点。如果禁用了检查点，Kafka Consumer 会定期将偏移量提交给 Zookeeper。

Java版本:
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 每5s进行一次checkpoint
env.enableCheckpointing(5000);
```

Scala版本:
```scala
val env = StreamExecutionEnvironment.getExecutionEnvironment()
// 每5s进行一次checkpoint
env.enableCheckpointing(5000)
```

> 如果有足够的 slot 可用于重新启动拓扑，那么 Flink 才能重新启动拓扑。因此，如果拓扑由于与 TaskManager 断开而失败，那么必须有足够的可用 slot。

### 2.4 分区与主题发现

#### 2.4.1 分区发现

Flink Kafka Consumer 支持发现动态创建的 Kafka 分区，并使用 Exactly-Once 语义来消费。当作业开始运行，首次检索分区元数据后发现的所有分区会从最早的偏移量开始消费。

默认情况下，分区发现是禁用的。如果要启用它，需要设置 `flink.partition-discovery.interval-millis` 为一个非负值，表示发现间隔（以毫秒为单位的）。

> 当使用 Flink 1.3.x 之前的版本，消费者从保存点恢复时，无法在恢复的运行启用分区发现。如果要启用，恢复将失败并抛出异常。在这种情况下，为了使用分区发现，需要在 Flink 1.3.x 版本中生成保存点，然后再从中恢复。

#### 2.4.2  主题发现

Flink Kafka Consumer 还能够使用正则表达式匹配 Topic 名称来自动发现 Topic。

Java 版本：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

Properties properties = new Properties();
properties.setProperty("bootstrap.servers", "localhost:9092");
properties.setProperty("group.id", "test");

FlinkKafkaConsumer<String> myConsumer = new FlinkKafkaConsumer<>(
    java.util.regex.Pattern.compile("test-topic-[0-9]"),
    new SimpleStringSchema(),
    properties);

DataStream<String> stream = env.addSource(myConsumer);
...
```
Scala版本：
```
val env = StreamExecutionEnvironment.getExecutionEnvironment()

val properties = new Properties()
properties.setProperty("bootstrap.servers", "localhost:9092")
properties.setProperty("group.id", "test")

val myConsumer = new FlinkKafkaConsumer[String](
  java.util.regex.Pattern.compile("test-topic-[0-9]"),
  new SimpleStringSchema,
  properties)

val stream = env.addSource(myConsumer)
...
```
在上面的示例中，当作业开始运行时，Consumer 会订阅名称与正则表达式相匹配的所有主题（以 test-topic- 开头并以一位数字结尾）。

### 2.5 偏移量提交

Flink Kafka Consumer 可以配置如何将偏移量提交回 Kafka Broker。需要注意的是 Flink Kafka Consumer 不需要依赖提交的偏移量来提供容错保证。提交的偏移量仅是用来展示消费者的进度。

有不同的方式配置偏移量提交，具体取决于作业是否启用了检查点：
- 禁用检查点：如果禁用了检查点，那么 Flink Kafka Consumer 依赖于 Kafka 客户端的定期自动提交偏移量的功能。因此，要禁用或启用偏移量提交，只需在 Properties 配置中将 `enable.auto.commit` / `auto.commit.interval.ms` 设置为适当的值。
- 启用检查点：如果启用检查点，那么 Flink Kafka Consumer 会在检查点完成时提交偏移量存储在检查点状态中。这样可以确保 Kafka Broker 中的已提交偏移量与检查点状态中的偏移量一致。用户可以通过调用 `setCommitOffsetsOnCheckpoints(boolean)` 方法来选择禁用或启用偏移提交（默认情况下为true）。请注意，在这种情况下，Properties 配置中的自动定期提交偏移设置将被忽略。

### 2.6 时间戳提取与Watermark输出

在许多情况下，记录的时间戳会存在记录本身中或在 ConsumerRecord 的元数据中。另外，用户可能希望周期性地或不定期地发出 Watermark。对于这些情况，Flink Kafka Consumer 可以指定 Watermark 策略。我们可以按照如下所述指定自定义策略，也可以使用内置策略。

Java版本：
```java
Properties properties = new Properties();
properties.setProperty("bootstrap.servers", "localhost:9092");
properties.setProperty("group.id", "test");

FlinkKafkaConsumer<String> myConsumer =
    new FlinkKafkaConsumer<>("topic", new SimpleStringSchema(), properties);
myConsumer.assignTimestampsAndWatermarks(
    WatermarkStrategy.
        .forBoundedOutOfOrderness(Duration.ofSeconds(20)));

DataStream<String> stream = env.addSource(myConsumer);
```

### 3. Kafka生产者

Flink 的 Kafka 生产者：FlinkKafkaProducer（对于 Kafka 0.11.x 版本为 FlinkKafkaProducer011，对于 Kafka 0.10.x 版本为 FlinkKafkaProducer010) 提供了可以写入一个或多个 Kafka Topic 的功能。

Kafka 生产者的构造函数接受如下参数:
- 一个默认的输出Topic
- 用于序列数据到 Kafka 的 SerializationSchema / KafkaSerializationSchema
- Kafka 生产者的配置。需要以下属性：`bootstrap.servers`(逗号分隔的 Kafka broker 列表、`zookeeper.connect`(逗号分隔的 Zookeeper 服务器)(对于 Kafka 0.8 是必需的)
- 容错语义

Java版本：
```java
DataStream<String> stream = ...

Properties properties = new Properties();
properties.setProperty("bootstrap.servers", "localhost:9092");

FlinkKafkaProducer<String> myProducer = new FlinkKafkaProducer<>(
        "my-topic",                  // target topic
        new SimpleStringSchema(),    // serialization schema
        properties,                  // producer config
        FlinkKafkaProducer.Semantic.EXACTLY_ONCE); // fault-tolerance

stream.addSink(myProducer);
```

Scala版本：
```
val stream: DataStream[String] = ...

Properties properties = new Properties
properties.setProperty("bootstrap.servers", "localhost:9092")

val myProducer = new FlinkKafkaProducer[String](
        "my-topic",                  // target topic
        new SimpleStringSchema(),    // serialization schema
        properties,                  // producer config
        FlinkKafkaProducer.Semantic.EXACTLY_ONCE) // fault-tolerance

stream.addSink(myProducer)
```
#### 3.1 SerializationSchema

Flink Kafka 生产者需要知道如何将 Java/Scala 对象转换为 Kafka 中的二进制数据。KafkaSerializationSchema 可以允许用户指定这样的一个 Schema。每个 Kafka 消息都会调用 `ProducerRecord<byte[], byte[]> serialize(T element, @Nullable Long timestamp)` 方法，生成一个 ProducerRecord 写入 Kafka。

用户可以对如何将数据写到 Kafka 进行细粒度的控制。通过生产者记录，我们可以：
- 设置标题值
- 为每个记录定义Key
- 指定数据的自定义分区

#### 3.2 容错

当启用 Flink 的检查点后，FlinkKafkaProducer 与 FlinkKafkaProducer011（适用于Kafka >= 1.0.0 版本的 FlinkKafkaProducer）都可以提供 Exactly-once 的语义保证。FlinkKafkaProducer010 只能提供 At-Least-once 语义的保证。

除了启用 Flink 的检查点之外，我们还可以通过将语义参数传递给 FlinkKafkaProducer 与 FlinkKafkaProducer011（适用于Kafka >= 1.0.0 版本的FlinkKafkaProducer）来选择三种不同的操作模式：
- Semantic.NONE：Flink 不做任何保证。产生的记录可能会丢失或重复。
- Semantic.AT_LEAST_ONCE（默认设置）：保证了不会丢失任何记录（可能重复）。
- Semantic.EXACTLY_ONCE：通过 Kafka 事务提供 Exactly-once 的语义。每当我们使用事务写入 Kafka 时，请不要忘记为所有使用 Kafka 记录的应用程序设置所需的隔离等级（read_committed 或 read_uncommitted，后者为默认值）。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[Apache Kafka Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/connectors/kafka.html)
