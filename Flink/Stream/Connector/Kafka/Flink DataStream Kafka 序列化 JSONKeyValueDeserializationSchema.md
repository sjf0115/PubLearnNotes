在我们在使用 Flink Streaming Kafka Connector 从 Kafka 中读取时，一般会采用 SimpleStringSchema 来反序列化 Kafka 中的数据。如果是 Kafka 中的数据是 JSON 格式，然后采用 Gson 或者 FastJson 来解析数据，如下所示：
```java
String consumerTopic = "word";
FlinkKafkaConsumer<String> consumer = new FlinkKafkaConsumer<>(
        consumerTopic,
        // 使用 SimpleStringSchema 反序列化
        new SimpleStringSchema(),
        consumerProps
);
consumer.setStartFromLatest();
DataStreamSource<String> sourceStream = env.addSource(consumer);

sourceStream.map(new MapFunction<String, WordCount>() {
    @Override
    public WordCount map(String word) throws Exception {
        // 采用 Gson 方式解析来自 Kafka 中的数据
        return gson.fromJson(word, WordCount.class);
    }
});
```

除了使用这种方式之外，Flink 为我们内置实现了一个 [KafkaSerializationSchema](https://smartsi.blog.csdn.net/article/details/130179661) 来帮我们解析 Kafka 中的 JSON 格式数据，即 JSONKeyValueDeserializationSchema。

> 关于 Flink Kafka 序列化，可以参考阅读[Flink DataStream Kafka 序列化 KafkaSerializationSchema 与 KafkaDeserializationSchema](https://smartsi.blog.csdn.net/article/details/130179661)

## 1. 如何使用

JSONKeyValueDeserializationSchema 将 Kafka 中的 JSON 格式的 Value 转换为 ObjectNode 对象，进而访问元数据以及键值信息。其中键 Key 字段可以通过调用 `objectNode.get("key").get("xxx").asText()` 来访问。值 Value 字段可以通过调用 `objectNode.get("value").get("xxx").asText()` 来访问。元数据字段可以通过调用 `objectNode.get("metadata").get("xxx").asText()` 来访问，其中包括主题、分区以及偏移量的获取。

指定反序列化器 JSONKeyValueDeserializationSchema 比较简单，只需要将其实例传递给 FlinkKafkaConsumer 即可，其中需要指定一个参数 `includeMetadata` 来表示反序列化是否包含元数据。具体如下所示：
```java
// 创建 Kafka Consumer
String consumerTopic = "word";
Properties consumerProps = new Properties();
consumerProps.put("bootstrap.servers", "localhost:9092");
consumerProps.put("group.id", "word-count");
FlinkKafkaConsumer<ObjectNode> consumer = new FlinkKafkaConsumer<>(
        consumerTopic,
        // 原生 JSON 反序列化器
        new JSONKeyValueDeserializationSchema(true),
        consumerProps
);
consumer.setStartFromLatest();
DataStreamSource<ObjectNode> sourceStream = env.addSource(consumer);
```
指定反序列化器之后，从 Kafka 中消费的数据就转换为 ObjectNode 对象，下面我们具体看看如何获取 JSON 中值信息以及元数据信息：
```java
sourceStream.map(new MapFunction<ObjectNode, WordCount>() {
    @Override
    public WordCount map(ObjectNode node) throws Exception {
        // 元数据信息 主题、分区、偏移量
        String topic = node.get("metadata").get("topic").asText();
        String partition = node.get("metadata").get("partition").asText();
        String offset = node.get("metadata").get("offset").asText();
        // 键信息
        String key = node.get("key").asText();
        // 值信息
        String word = node.get("value").get("word").asText();
        Long frequency = node.get("value").get("frequency").asLong();
        LOG.info("[INFO] record topic: {}, partition: {}, offset: {}, key: {}, word: {}, frequency: {}",
                topic,
                partition,
                offset,
                key,
                word,
                frequency
        );
        return new WordCount(word, frequency);
    }
});
```
在运行过程中你可能会遇到如下异常：
```java
org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.JsonParseException: Unrecognized token 'a': was expecting (JSON String, Number, Array, Object or token 'null', 'true' or 'false')
 at [Source: (byte[])"a"; line: 1, column: 2]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.JsonParser._constructError(JsonParser.java:2337) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.base.ParserMinimalBase._reportError(ParserMinimalBase.java:720) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.json.UTF8StreamJsonParser._reportInvalidToken(UTF8StreamJsonParser.java:3593) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.json.UTF8StreamJsonParser._handleUnexpectedValue(UTF8StreamJsonParser.java:2688) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.json.UTF8StreamJsonParser._nextTokenNotInObject(UTF8StreamJsonParser.java:870) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.core.json.UTF8StreamJsonParser.nextToken(UTF8StreamJsonParser.java:762) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper._initForReading(ObjectMapper.java:4684) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper._readMapAndClose(ObjectMapper.java:4586) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper.readValue(ObjectMapper.java:3609) ~[flink-shaded-jackson-2.12.1-13.0.jar:2.12.1-13.0]
	at org.apache.flink.streaming.util.serialization.JSONKeyValueDeserializationSchema.deserialize(JSONKeyValueDeserializationSchema.java:62) ~[flink-connector-kafka_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.util.serialization.JSONKeyValueDeserializationSchema.deserialize(JSONKeyValueDeserializationSchema.java:43) ~[flink-connector-kafka_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.connectors.kafka.KafkaDeserializationSchema.deserialize(KafkaDeserializationSchema.java:79) ~[flink-connector-kafka_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.connectors.kafka.internals.KafkaFetcher.partitionConsumerRecordsHandler(KafkaFetcher.java:179) ~[flink-connector-kafka_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.connectors.kafka.internals.KafkaFetcher.runFetchLoop(KafkaFetcher.java:142) ~[flink-connector-kafka_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumerBase.run(FlinkKafkaConsumerBase.java:826) ~[flink-connector-kafka_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.StreamSource.run(StreamSource.java:110) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.StreamSource.run(StreamSource.java:66) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SourceStreamTask$LegacySourceFunctionThread.run(SourceStreamTask.java:269) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
```
这个异常与 JSONKeyValueDeserializationSchema 的设计有关系，我们会在下面的源码中讲解为什么会出现这样的异常。

## 2. 源码分析

JSONKeyValueDeserializationSchema 实现了 KafkaDeserializationSchema 接口，然后重写了 deserialize、isEndOfStream、getProducedType 三个方法：
```java
public class JSONKeyValueDeserializationSchema implements KafkaDeserializationSchema<ObjectNode> {
    @Override
    public ObjectNode deserialize(ConsumerRecord<byte[], byte[]> record) throws Exception {
        ...
    }

    @Override
    public boolean isEndOfStream(ObjectNode nextElement) {
        return false;
    }

    @Override
    public TypeInformation<ObjectNode> getProducedType() {
        return getForClass(ObjectNode.class);
    }
}
```
下面我们详细看一下反序列化 deserialize 的实现逻辑：
```java
public ObjectNode deserialize(ConsumerRecord<byte[], byte[]> record) throws Exception {
    if (mapper == null) {
        mapper = new ObjectMapper();
    }
    ObjectNode node = mapper.createObjectNode();
    // 1. 对 Key 的处理
    if (record.key() != null) {
        node.set("key", mapper.readValue(record.key(), JsonNode.class));
    }
    // 2. 对 Value 的处理
    if (record.value() != null) {
        node.set("value", mapper.readValue(record.value(), JsonNode.class));
    }
    // 3. 对元数据的处理
    if (includeMetadata) {
        node.putObject("metadata")
                .put("offset", record.offset())
                .put("topic", record.topic())
                .put("partition", record.partition());
    }
    return node;
}
```
实现对 Kafka `ConsumerRecord<byte[], byte[]>` 的反序列化，需要完成对键(Key)、值(Value)、元数据的处理。如果在构造函数中设置 includeMetadata 为 true，才会添加元数据信息。

从上面代码中可以看出 JSONKeyValueDeserializationSchema 指定 Kafka 键 key 必须是一个 JSON 字符串，但我们平时一般都是指定的是一个非 JSON 格式的字符串，所以就会遇到上面所说的问题。解决方案有两种：
- 第一种是将 Key 转为一个 JSON
- 第二种是自定义实现一个 JSONKeyValueDeserializationSchema，将 key 修改为一个字符串，如下所示：
```java
public class JsonKVDeserializationSchema implements KafkaDeserializationSchema<ObjectNode> {
    private static final long serialVersionUID = 1509391548173891955L;
    private final boolean includeMetadata;
    private ObjectMapper mapper;

    public JsonKVDeserializationSchema(boolean includeMetadata) {
        this.includeMetadata = includeMetadata;
    }

    @Override
    public boolean isEndOfStream(ObjectNode nextElement) {
        return false;
    }

    @Override
    public ObjectNode deserialize(ConsumerRecord<byte[], byte[]> record) throws Exception {
        if (mapper == null) {
            mapper = new ObjectMapper();
        }
        ObjectNode node = mapper.createObjectNode();
        if (record.key() != null) {
            //node.set("key", mapper.readValue(record.key(), JsonNode.class));
            node.put("key", new String(record.key()));
        }
        if (record.value() != null) {
            node.set("value", mapper.readValue(record.value(), JsonNode.class));
        }
        if (includeMetadata) {
            node.putObject("metadata")
                    .put("offset", record.offset())
                    .put("topic", record.topic())
                    .put("partition", record.partition());
        }
        return node;
    }

    @Override
    public TypeInformation<ObjectNode> getProducedType() {
        return getForClass(ObjectNode.class);
    }
}
```

> 完整代码请查阅[JSONDeserializationExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/connector/kafka/serializable/JSONDeserializationExample.java)
