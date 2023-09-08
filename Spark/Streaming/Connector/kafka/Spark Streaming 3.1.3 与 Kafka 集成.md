Spark Streaming 与 Kafka 0.10 的集成提供了简单的并行性，Kafka 分区和 Spark 分区之间的是 1:1 对应关系，以及可以对偏移量和元数据访问。然而，由于这种集成使用了新的 Kafka 消费者 API 而不是简单 API，所以在使用上有明显的差异。

## 1. 引入依赖

对于使用 SBT/Maven 项目定义的 Scala/Java 应用程序，请引入如下依赖：
```xml
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-streaming-kafka-0-10_2.12</artifactId>
    <version>3.1.3</version>
</dependency>
```
不要手动添加 `org.apache.kafka` (例如 kafka-clients ) 的依赖项。`spark-streaming-kafka-0-10` 依赖具有传递依赖关系，并且不同版本可能难兼容。

## 2. 创建 Direct Stream

需要注意的是导入的命名空间包括版本，例如如下所示：
```java
import org.apache.spark.streaming.kafka010.ConsumerStrategies;
import org.apache.spark.streaming.kafka010.KafkaUtils;
import org.apache.spark.streaming.kafka010.LocationStrategies;
```

```

```

关于 kafkaParams 中的参数，请参阅 [Kafka 消费者配置文档](http://kafka.apache.org/documentation.html#newconsumerconfigs)。如果您的 Spark批处理持续时间大于默认的 Kafka 心跳会话超时时间(30秒)，需要适当增加 `heartbeat.interval.ms` 和 `session.timeout.ms` 参数的值。对于大于 5 分钟的批处理，这需要在 broker 上更改 `group.max.session.timeout.ms`。注意，该示例将enable.auto.commit设置为false，有关讨论，请参见下面的存储偏移量。

## 3. LocationStrategies

新的 Kafka 消费者 API 需要把消息预取到缓冲区中。因此，出于性能考虑，Spark 集成将消费者缓存在 Executor 上(而不是为每个批处理重新创建)是很重要的，并且更倾向于将分区调度到具有对应消费者的主机位置上，即控制指定分区在哪个 Executor 上消费。位置的选择是相对的，位置策略 LocationStrategies 目前有如下三种策略：
- PreferConsistent：首选一致性策略
- PreferBrokers：首选 Kafka Broker 策略
- PreferFixed：首选固定策略

在大多数情况下，使用 PreferConsistent 策略就可以满足需求。这种策略可以在可用的 Executor 之间均匀地分配分区。如果 Executor 和 Kafka Broker 在同一主机上，可以使用 PreferBrokers 策略。这种策略可以优先将分区调度到 Kafka Leader 上。最后，如果分区之间的负载有明显的倾斜(负载不均衡)，可以使用 PreferFixed 策略。这种策略可以指定分区到主机的显式映射关系，即特定主机使用指定的分区，手动控制(没有显示指定的分区仍然使用 PreferConsistent 首选一致性策略)。

默认 Executor 上缓存的消费者个数最大为 64。如果你希望处理更多的(64 * Executor 数量)的 Kafka 分区，可以通过 `spark.streaming.kafka.consumer.cache.maxCapacity` 来设置。如果你想禁用 Kafka 消费者的缓存，可以将 `spark.streaming.kafka.consumer.cache.enabled` 设置为 false。

缓存由 topicpartition 和 group.id 控制。Id，所以为 createDirectStream 调用使用单独的 group.id。

## 4. ConsumerStrategies

Kafka 新的消费者 API 有许多不同的方式来指定 Topic，其中一些需要大量的对象实例化后设置。ConsumerStrategies 提供了一个抽象，允许 Spark 即使在从检查点重新启动后也能获得正确配置的消费者。消费者策略 ConsumerStrategies 目前有如下三种策略：
- Subscribe：可以订阅指定的 Topic 集合
- SubscribePattern：可以使用正则表达式来指定感兴趣的 Topic
- Assign：可以指定一个固定的分区集合

这三种策略都有重载的构造函数，允许您为特定分区指定起始偏移量。如果您有上述选项无法满足的特定消费者设置需求，那么 ConsumerStrategy 是一个您可以扩展的公共类。

## 5. Creating an RDD

如果您有一个更适合批处理的用例，您可以为已定义的偏移量范围创建 RDD：
```java
// Import dependencies and create kafka params as in Create Direct Stream above

OffsetRange[] offsetRanges = {
  // topic, partition, inclusive starting offset, exclusive ending offset
  OffsetRange.create("test", 0, 0, 100),
  OffsetRange.create("test", 1, 0, 100)
};

JavaRDD<ConsumerRecord<String, String>> rdd = KafkaUtils.createRDD(
  sparkContext,
  kafkaParams,
  offsetRanges,
  LocationStrategies.PreferConsistent()
);
```
需要注意的是您不能使用 PreferBrokers 策略，因为没有流，就没有驱动端消费者自动为您查找 Broker 元数据。如有必要，将 PreferFixed 用于您自己的元数据查找。

## 6. Obtaining Offsets

```java
stream.foreachRDD(rdd -> {
  OffsetRange[] offsetRanges = ((HasOffsetRanges) rdd.rdd()).offsetRanges();
  rdd.foreachPartition(consumerRecords -> {
    OffsetRange o = offsetRanges[TaskContext.get().partitionId()];
    System.out.println(
      o.topic() + " " + o.partition() + " " + o.fromOffset() + " " + o.untilOffset());
  });
});
```
需要注意的是对 HasOffsetRanges 的类型转换只有在对 createDirectStream 的结果调用的第一个方法中才会成功，在之后的方法链中不会成功。另外，RDD 分区和 Kafka 分区之间的一对一映射不会在 shuffle 或 repartition (例如reduceByKey()或window())方法之后保留。

## 7. Storing Offsets

Kafka 在失败情况下的交付语义取决于如何以及何时存储偏移量 Offset。Spark 的输出操作是 At-Least-Once 语义。因此，如果您想要 Exactly-once 语义，则必须在幂等输出之后存储偏移量，或者在输出操作的原子事务中存储偏移量。对于如何存储偏移量，按照可靠性(和代码复杂性)的顺序，您有3种选择：
- Checkpoints
- Kafka
- 自己的存储

### 7.1 Checkpoints

如果要启用 Spark Checkpoints，偏移量可以存储在 Checkpoints 中。这很容易实现，但也有缺点。你的输出操作必须是幂等的，因为你会得到重复的输出。此外，如果应用程序代码发生更改，则无法从检查点恢复。对于有计划的升级，您可以通过同时运行新代码和旧代码来缓解这种情况(因为输出无论如何都需要是幂等的，它们不应该冲突)。但是对于需要更改代码的计划外故障，可能会丢失数据，除非您有另一种方法来识别已知的良好起始偏移量。

### 7.2 Kafka

Kafka 有一个偏移量提交 API，可以将偏移量存储在一个特殊的 Kafka Topic 中。默认情况下，新消费者 API 会定期自动提交偏移量。这几乎肯定不是您想要的，因为消费者成功轮询的消息 Spark 可能还没有输出。这就是为什么上面的流示例将 `enable.auto.commit` 设置为 false 的原因。你可以在知道你的输出已经被存储之后，使用 commitAsync API 向 Kafka 提交偏移量。与 Checkpoints 相比，Kafka 是一个持久的存储，无论你的应用程序代码如何变化，存储的 Offset 都不会丢失。然而，Kafka 不是事务性的，所以你的输出仍然必须是幂等的。

```java
stream.foreachRDD(rdd -> {
  OffsetRange[] offsetRanges = ((HasOffsetRanges) rdd.rdd()).offsetRanges();
  // some time later, after outputs have completed
  ((CanCommitOffsets) stream.inputDStream()).commitAsync(offsetRanges);
});
```

### 7.3 自己的存储

对于支持事务的数据存储，在同一个事务中保存偏移量可以使结果和偏移量保持同步，即使在出现故障的情况下也是如此。如果您注意检测重复或跳过的偏移范围，则回滚事务可以防止重复或丢失的消息影响结果。这相当于 Exactly-Once 语义。甚至对于聚合产生的输出也可以使用这种策略，因为聚合通常很难使其幂等。

```java
// The details depend on your data store, but the general idea looks like this

// begin from the offsets committed to the database
Map<TopicPartition, Long> fromOffsets = new HashMap<>();
for (resultSet : selectOffsetsFromYourDatabase)
  fromOffsets.put(new TopicPartition(resultSet.string("topic"), resultSet.int("partition")), resultSet.long("offset"));
}

JavaInputDStream<ConsumerRecord<String, String>> stream = KafkaUtils.createDirectStream(
  streamingContext,
  LocationStrategies.PreferConsistent(),
  ConsumerStrategies.<String, String>Assign(fromOffsets.keySet(), kafkaParams, fromOffsets)
);

stream.foreachRDD(rdd -> {
  OffsetRange[] offsetRanges = ((HasOffsetRanges) rdd.rdd()).offsetRanges();

  Object results = yourCalculation(rdd);

  // begin your transaction

  // update results
  // update offsets where the end of existing offsets matches the beginning of this batch of offsets
  // assert that offsets were updated correctly

  // end your transaction
});
```




> 原文:[Spark Streaming + Kafka Integration Guide (Kafka broker version 0.10.0 or higher)](https://spark.apache.org/docs/3.1.3/streaming-kafka-0-10-integration.html)
