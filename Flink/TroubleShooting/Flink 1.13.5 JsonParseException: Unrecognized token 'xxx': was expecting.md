## 1. 问题

在使用 Flink Streaming Kafka Connector 从 Kafka 中读取时，反序列化器指定的是 `JSONKeyValueDeserializationSchema`：
```java
// 创建 Kafka Consumer
String consumerTopic = "word";
Properties consumerProps = new Properties();
consumerProps.put("bootstrap.servers", "localhost:9092");
consumerProps.put("group.id", "word-count");
FlinkKafkaConsumer<ObjectNode> consumer = new FlinkKafkaConsumer<>(
        consumerTopic,
        new JSONKeyValueDeserializationSchema(true),
        consumerProps
);
consumer.setStartFromLatest();
DataStreamSource<ObjectNode> sourceStream = env.addSource(consumer);
```
但是在运行过程中抛出如下异常：
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

## 2. 解决方案

报错发生在 JSONKeyValueDeserializationSchema 中的第 62 行，即 `node.set("key", mapper.readValue(record.key(), JsonNode.class));` 这一行：
```java
public ObjectNode deserialize(ConsumerRecord<byte[], byte[]> record) throws Exception {
    if (mapper == null) {
        mapper = new ObjectMapper();
    }
    ObjectNode node = mapper.createObjectNode();
    if (record.key() != null) {
        node.set("key", mapper.readValue(record.key(), JsonNode.class));
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
```
从 JSONKeyValueDeserializationSchema 的源代码中可以发现 JSONKeyValueDeserializationSchema 期望我们的 Key 是一个 JSON 而不是一个字符串。所以解决方案有两种：
- 第一种是将 Key 转为一个 JSON
- 第二种是自己实现一个 JSONKeyValueDeserializationSchema，将 key 修改为一个字符串：
```java
node.put("key", new String(record.key()));
```
