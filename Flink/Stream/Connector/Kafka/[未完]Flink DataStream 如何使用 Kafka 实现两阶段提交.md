## 1. 配置适用的 Kafka 事务超时时间

如果 Flink 应用程序崩溃和完成重启之间的时间大于 Kafka 的事务超时时间，Kafka 会自动中止超过超时时间的事务，则有可能会出现数据丢失。 考虑到这一点，请根据您的预期停机时间适当地配置您的事务超时时间。如果您为 Flink Kafka Producer 配置端到端的 Exactly-Once 语义，强烈建议将 Kafka 事务超时时间配置的要比最大检查点时间加上最大预期 Flink 作业停机时间更大的一个时间。

Kafka Broker 默认将 transaction.max.timeout.ms 设置为 15 分钟。FlinkKafkaProducer 默认将 transaction.timeout.ms 属性设置为 1 小时。但是 transaction.max.timeout.ms 参数不允许 transaction.timeout.ms 参数设置的比其还要大。因此在使用 Exactly-Once 语义之前应增加 transaction.max.timeout.ms 值的大小。






另请注意，您可能希望在夜间或周末失败后恢复 Flink 作业。需要要配置 Kafka 事务超时：
- 为 Kafka Broker 配置 transaction.max.timeout.ms，默认为 15 分钟
- 为 Kafka Producer 配置 transaction.max.timeout.ms，默认为 1 小时，实际上被 Kafka Broker 的上述 transaction.max.timeout.ms 配置所限制。

```java
Properties properties = new Properties();
properties.setProperty("bootstrap.servers", "localhost:9092");
properties.setProperty("transaction.timeout.ms", "7200000"); // e.g., 2 hours

FlinkKafkaProducer myProducer = new FlinkKafkaProducer<>(
    "topic-name",                              // target topic
    new SimpleStringSchema(),                  // serialization schema
    producerProperties,                        // producer config
    FlinkKafkaProducer.Semantic.EXACTLY_ONCE
); // fault-tolerance
```

## 2. 不同作业使用不同的事务Id

如果您为 Flink Kafka Producer 配置端到端的 Exactly-Once 语义，那么同一 Kafka 集群运行的作业中 Kafka Producer 必须使用具有唯一性的事务 ID。否则，可能会遇到 transactional.id 冲突问题，例如如下异常：
```
Caused by: org.apache.kafka.common.errors.ProducerFencedException: Producer attempted an operation with an old epoch. Either there is a newer producer with the same transactionalId, or the producer's transaction has been expired by the broker
```

查看 Flink 源码找到 TransactionalIdsGenerator 事务Id生成器如下：
```java
transactionalIdsGenerator = new TransactionalIdsGenerator(
    taskName + "-" + ((StreamingRuntimeContext) getRuntimeContext()).getOperatorUniqueID(),
    getRuntimeContext().getIndexOfThisSubtask(),
    getRuntimeContext().getNumberOfParallelSubtasks(),
    kafkaProducersPoolSize,
    SAFE_SCALE_DOWN_FACTOR
);
```
从上面可以知道 FlinkKafkaProducer 需要根据如下信息生成事务 Id：
- 任务名称和算子 UID，或 transactionalIdPrefix（如果指定）
- 子任务下标索引
- 子任务并行度
-

如果您有多个 Flink 作业写入同一个 Kafka 集群，请确保 Kafka Sink 的 Task 名称和算子 UID 在这些作业中是唯一的。

## 3. Checkpoint 时间间隔

如果您为 Flink Kafka Produce 配置端到端的 Exactly-Once 语义，Flink 将使用 Kafka 事务来确保 Exactly-Once 交付。只有在检查点完成时才会提交这些事务。但是，由于许多不同的原因，检查点可能会延迟完成，因此 Kafka 事务超时时间必须远大于配置的检查点间隔，否则检查点可能会由于 Kafka 事务超时而失败。您可以通过以下任一方式解决它：

(1) 配置检查点间隔：
```java
StreamExecutionEnvironment env = ...;
env.enableCheckpointing(1000); // unit is millisecond
```

(2) 配置 Kafka 事务超时时间：
```

```

参考：
- https://ververica.zendesk.com/hc/en-us/articles/360013269680-Best-Practices-for-Using-Kafka-Sources-Sinks-in-Flink-Jobs#h_01EH76VC986JF2ZH52DPYT0X3C
- https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/connectors/datastream/kafka/#kafka-producers-and-fault-tolerance
