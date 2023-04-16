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

KafkaSerializationSchema 和 KafkaDeserializationSchema 都是接口，如果想要使用还需要自己实现序列化逻辑。

### 3.1 序列化

实现 KafkaSerializationSchema 接口来自定义序列化器比较简单如下所示：
```java
public class CustomKafkaSerializationSchema implements KafkaSerializationSchema<ProducerRecord<String, String>> {
    @Override
    public ProducerRecord<byte[], byte[]> serialize(ProducerRecord<String, String> record, @Nullable Long timestamp) {
        return new ProducerRecord<>(
                record.topic(),
                record.key().getBytes(StandardCharsets.UTF_8),
                record.value().getBytes(StandardCharsets.UTF_8)
        );
    }
}
```
在这我们只是简单的将 `ProducerRecord<String, String>` 序列化为 `ProducerRecord<byte[], byte[]>`，以便可以直接发送给 Kafka。

使用的时候也比较简单，直接将自定义序列化器实例专递给 FlinkKafkaProducer 即可：
```java
// 创建 Kafka Producer
Properties producerProps = new Properties();
producerProps.put("bootstrap.servers", "localhost:9092");
producerProps.put("transaction.timeout.ms", "5000");
FlinkKafkaProducer<ProducerRecord<String, String>> producer = new FlinkKafkaProducer<>(
        producerTopic,
        // 自定义序列化器
        new CustomKafkaSerializationSchema(),
        producerProps,
        FlinkKafkaProducer.Semantic.EXACTLY_ONCE
);
wordCountStream.addSink(producer);
```
需要注意的是上游 wordCountStream 必须输出的是 `ProducerRecord<String, String>` 格式，因为我们自定义的序列化器是将 `ProducerRecord<String, String>` 序列化为 `ProducerRecord<byte[], byte[]>`。

### 3.2 反序列化

实现 KafkaDeserializationSchema 接口来自定义反序列化器稍微比 KafkaSerializationSchema 复杂一点，不仅需要实现 deserialize 方法，还需要关注 isEndOfStream 和 getProducedType 方法。isEndOfStream 用来表示是否是流的最后一条元素，我们在这设置为 false，即需要源源不断的消费 kafka 中的记录。getProducedType 用来告诉 Flink 我们输入的数据类型, 方便 Flink 的类型推断。具体如下所示：
```java
public class CustomKafkaDeserializationSchema implements KafkaDeserializationSchema<ConsumerRecord<String, String>> {
    // 是否表示流的最后一条元素，我们要设置为 false ,因为我们需要 msg 源源不断的被消费
    @Override
    public boolean isEndOfStream(ConsumerRecord<String, String> nextElement) {
        return false;
    }

    @Override
    public ConsumerRecord<String, String> deserialize(ConsumerRecord<byte[], byte[]> record) throws Exception {
        ConsumerRecord<String, String> consumerRecord = new ConsumerRecord<>(
                record.topic(),
                record.partition(),
                record.offset(),
                new String(record.key(), "UTF-8"),
                new String(record.value(), "UTF-8")
        );
        return consumerRecord;
    }

    // 告诉 Flink 我输入的数据类型, 方便 Flink 的类型推断
    @Override
    public TypeInformation<ConsumerRecord<String, String>> getProducedType() {
        return TypeInformation.of(new TypeHint<ConsumerRecord<String, String>>() {
        });
    }
}
```
在这我们只是简单的将 `ConsumerRecord<byte[], byte[]>` 反序列化为 `ConsumerRecord<String, String>`，以便可以消费 Kafka 中的记录。相比直接使用 `SimpleStringSchema`，使用这种方式可以获取 Kafka 主题、分区、偏移量等元数据信息，这在很多场景下非常有用。

使用的时候跟 CustomKafkaSerializationSchema 基本一致，直接将自定义的反序列化器实例专递给 FlinkKafkaConsumer 即可：
```java
// 创建 Kafka Consumer
Properties consumerProps = new Properties();
consumerProps.put("bootstrap.servers", "localhost:9092");
consumerProps.put("group.id", "word-count");
FlinkKafkaConsumer<ConsumerRecord<String, String>> consumer = new FlinkKafkaConsumer<>(
        consumerTopic,
        // 自定义反序列化器
        new CustomKafkaDeserializationSchema(),
        consumerProps
);
consumer.setStartFromLatest();
DataStreamSource<ConsumerRecord<String, String>> sourceStream = env.addSource(consumer);
```

> 完整代码请查阅[KafkaCustomSerializableExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/connector/kafka/serializable/KafkaCustomSerializableExample.java)
