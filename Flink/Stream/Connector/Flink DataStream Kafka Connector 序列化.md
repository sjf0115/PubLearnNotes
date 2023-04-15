- SerializationSchema
- KeyedSerializationSchema
- KafkaSerializationSchema


## 1. 序列化

序列化 Schema 描述了如何将传入的数据对象转换为不同的序列化表示。大多数 Sink（例如 Apache Kafka）需要将数据转为特定格式（例如字节字符串）传递给它们。比如，Apahce kafka 需要将传入的对象转换为字节数组传递给 Kafka。

### 1.1 KeyedSerializationSchema

Flink 1.9 版本之前，推荐使用 KeyedSerializationSchema 将传入的数据对象转换为字节数组：
```java
public interface KeyedSerializationSchema<T> extends Serializable {
    byte[] serializeKey(T element);
    byte[] serializeValue(T element);
    String getTargetTopic(T element);
}
```
上面接口存在三个方法，每个输入的参数都是一样的，代码复用性低。此外，只能给 Kafka 提供 Key、Value 以及 Topic 三个属性。

### 1.2 KafkaSerializationSchema

在 Flink 1.9 版本，通用的 FlinkKafkaProducer（在 flink-connector-kafka 中）引入了一个新的 KafkaSerializationSchema，定义了如何将传入的数据对象序列化为 ProducerRecord：
```java
public interface KafkaSerializationSchema<T> extends Serializable {
	ProducerRecord<byte[], byte[]> serialize(T element, @Nullable Long timestamp);
}
```
目前 KeyedSerializationSchema 已经被标注为 `@Deprecated`，表示已经废弃。将由 KafkaSerializationSchema 来完全取代 KeyedSerializationSchema。Flink 官方推荐使用 KafkaSerializationSchema。KafkaSerializationSchema 可以直接生成 Kafka ProducerRecord 发送给 Kafka，从而使用户能够使用所 Kafka 更多的功能。

## 2. 反序列化

### 2.1 KeyedDeserializationSchema

Flink 1.8 版本之前，推荐使用 KeyedDeserializationSchema 将从 Kafka 消费到字节数组转换为数据对象：
```java
public interface KeyedDeserializationSchema<T> extends Serializable, ResultTypeQueryable<T> {
  boolean isEndOfStream(T nextElement);
	T deserialize(byte[] messageKey, byte[] message, String topic, int partition, long offset) throws IOException;
}
```
在 Flink 1.11 版本，为了增强反序列化接口，增加 open 接口，具体可以参阅[FLIP-124](https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=148645988) 和 [FLINK-17306](https://issues.apache.org/jira/browse/FLINK-17306)：
```java
public interface KafkaSerializationSchema<T> extends Serializable {
	default void open(SerializationSchema.InitializationContext context) throws Exception {
	}
	ProducerRecord<byte[], byte[]> serialize(T element, @Nullable Long timestamp);
}
```

### 2.1 KafkaDeserializationSchema

在 Flink 1.8 版本，通用的 FlinkKafkaConsumer（在 flink-connector-kafka 中）引入了一个新的 KafkaDeserializationSchema，它可以直接访问 Kafka ConsumerRecord，具体可以查看 [FLINK-8354](https://issues.apache.org/jira/browse/FLINK-8354)。KafkaDeserializationSchema 定义了如何将 Kafka ConsumerRecord 反序列化为数据对象：
```java
public interface KafkaDeserializationSchema<T> extends Serializable, ResultTypeQueryable<T> {
	boolean isEndOfStream(T nextElement);
	T deserialize(ConsumerRecord<byte[], byte[]> record) throws Exception;
}
```
目前 KeyedDeserializationSchema 已经被标注为 `@Deprecated`，表示已经废弃。将由 KafkaDeserializationSchema 完全取代 KeyedDeserializationSchema。Flink 官方推荐使用 KafkaDeserializationSchema。KafkaDeserializationSchema 可以直接以 Kafka ConsumerRecord 的形式消费 Kafka 中的数据，从而使用户能够使用所 Kafka 更多的功能，比如获取 Topic 以及 Headr 信息等。

在 Flink 1.11 版本，为了增强序列化接口，增加 open 接口以及通过 Collector 来支持返回多条数据，具体可以参阅[FLIP-124](https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=148645988) 和 [FLINK-17305](https://issues.apache.org/jira/browse/FLINK-17305)：
```java
public interface KafkaDeserializationSchema<T> extends Serializable, ResultTypeQueryable<T> {
    default void open(DeserializationSchema.InitializationContext context) throws Exception {}
    boolean isEndOfStream(T nextElement);
    T deserialize(ConsumerRecord<byte[], byte[]> record) throws Exception;
    default void deserialize(ConsumerRecord<byte[], byte[]> message, Collector<T> out) throws Exception {
        T deserialized = deserialize(message);
        if (deserialized != null) {
            out.collect(deserialized);
        }
    }
}
```

## 3. 自定义序列化与反序列化器




```
[INFO] record topic: word, partition: 0, offset: 3, key: a, value: {"word":"a","frequency":1}, timestamp: -1
[INFO] record topic: word, partition: 0, offset: 4, key: b, value: {"word":"b","frequency":1}, timestamp: -1
[INFO] record topic: word, partition: 0, offset: 5, key: a, value: {"word":"a","frequency":1}, timestamp: -1
```




https://issues.apache.org/jira/browse/FLINK-8354
