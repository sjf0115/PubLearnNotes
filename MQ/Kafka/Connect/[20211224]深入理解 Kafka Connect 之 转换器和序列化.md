---
layout: post
author: smartsi
title: 深入理解 Kafka Connect Converter 和序列化
date: 2021-12-24 13:55:00
tags:
  - Kafka

categories: Kafka
permalink: kafka-connect-deep-dive-converters-serialization-explained
---

Kafka Connect 是 Apache Kafka 的一部分，提供了数据存储和 Kafka 之间的流式集成。对于数据开发工程师来说，只需要配置 JSON 文件就可以使用。Kafka 为一些常见数据存储的提供了 Connector，比如，JDBC、Elasticsearch、IBM MQ、S3 和 BigQuery 等等。对于开发人员来说，Kafka Connect 提供了丰富的 API，还可以开发其他的 Connector。除此之外，还提供了用于配置和管理 Connector 的 REST API。

Kafka Connect 是一种模块化组件，提供了一种非常强大的集成方法。关键组件如下所示：
- Connectors（连接器）：定义如何与数据存储集成的 JAR 文件；
- Converters（转换器）：处理数据的序列化和反序列化；
- Transforms（变换器）：可选的运行时消息操作。

人们对 Kafka Connect 最常见的误解基本都与数据序列化相关。Kafka Connect 使用 Converters 来处理数据的序列化。接下来让我们看看它们是如何工作的，并说明一些常见问题是如何解决的。

## 1. Kafka 消息都是字节

Kafka 消息被组织保存在 Topic 中，每条消息就是一个键值对。当存储在 Kafka 中时，键和值都只是字节。这样 Kafka 就可以适用于各种不同场景，但这也意味着开发人员必须决定数据是如何序列化的。

在配置 Kafka Connect 时，其中最重要的一件事就是配置序列化格式。我们需要确保从 Topic 读取数据时使用的序列化格式与写入 Topic 的序列化格式相同，否则就会出现错误。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-connect-deep-dive-converters-serialization-explained-1.png?raw=true)

常见的序列化格式包括：
- JSON
- Avro
- Protobuf
- 字符串分隔（如 CSV）

每一个都有优点和缺点，除了字符串分隔，在这种情况下只有缺点。

### 1.1 选择序列化格式

选择序列化格式有一些指导原则：
- Schema：很多时候，我们的数据都有对应的 Schema。你可能不喜欢，但作为开发人员，你有责任保留和传播 Schema。Schema 为服务之间提供了一种契约。有些消息格式（例如，Avro 和 Protobuf）对 Schema 的支持较多，然而有些消息格式支持较少（JSON）或根本不支持（CVS）。
- 生态系统兼容性：Avro、Protobuf 和 JSON 是 Confluent 平台的一等公民，拥有来自 Confluent Schema Registry、Kafka Connect、KSQL 的原生支持。
- 消息大小：JSON 是纯文本的，并且依赖了 Kafka 本身的压缩机制，Avro 和 Protobuf 是二进制格式，因此可以提供更小的消息体积。
- 语言支持：Avro 在 Java 领域得到了强大的支持，而如果你使用的是 Go 语言，那么你很可能会期望使用 Protobuf。

### 1.2 如果使用 JSON 写入目标系统，Kafka Topic 也必须使用 JSON 吗？

可以不需要这样。从 Source 读取数据的格式不需要与 Kafka 消息的序列化格式一样，数据写入外部数据存储系统也是一样。Kafka Connect 中的 Connector 负责从 Source 数据存储（例如，数据库）读取数据，然后以内部表示形式将数据传给 Converter。Converter 将这些 Source 数据对象序列化到 Topic 上。

在使用 Kafka Connect 作为 Sink 时刚好相反，Converter 将来自 Topic 的数据反序列化为内部表示形式，然后传给 Connector 并使用针对于目标存储的格式将数据写入目标数据存储中。也就是说，当你将数据写入 HDFS 时，Topic 中的数据可以是 Avro 格式，Sink 的 Connector 只需要使用 HDFS 支持的格式即可（不用必须是 Avro 格式）。

## 2. 配置 Converter

Kafka Connect 默认使用 Worker 级别的 Converter 配置，Connector 可以对其进行覆盖。通常在整个 Pipeline 中使用相同的序列化格式是一种更好的选择，所以通常只需要在 Worker 级别配置 Converter，不需要在 Connector 中指定。但你可能需要从别人的 Topic 中拉取数据，并且他们使了用不同的序列化格式，对于这种情况，你需要在 Connector 配置中配置 Converter。即使你在 Connector 的配置中进行了覆盖，但实际执行的仍然是 Converter。正确编写的 Connector 一般不会序列化或反序列化存储在 Kafka 中的消息，最终还是会让 Converter 来完成这项工作。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-connect-deep-dive-converters-serialization-explained-2.png?raw=true)

需要记住的是，Kafka 的消息是键值对字节，你需要使用 key.converter 和 value.converter 分别为键和值指定 Converter。在某些情况下，你可以为键和值分别使用不同的 Converter。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-connect-deep-dive-converters-serialization-explained-3.png?raw=true)

下面是一个使用字符串 Converter 的例子。因为只是一个字符串，没有数据的 Schema，因此使用它的值不是很有用:
```json
"key.converter": "org.apache.kafka.connect.storage.StringConverter",
```
有些 Converter 有一些额外的配置。对于 Avro，你需要指定 Schema Registry。对于 JSON，你需要指定是否希望 Kafka Connect 将 Schema 嵌入到 JSON 消息中。在指定 Converter 特有配置时，必须始终使用 `key.converter.` 或 `value.converter.` 前缀。例如，要将 Avro 用于消息 payload，你需要指定以下内容：
```json
"value.converter": "io.confluent.connect.avro.AvroConverter",
"value.converter.schema.registry.url": "http://schema-registry:8081",
```
常见的 Converter 包括：
- Avro：io.confluent.connect.avro.AvroConverter
- Protobuf：io.confluent.connect.protobuf.ProtobufConverter
- JSON：org.apache.kafka.connect.json.JsonConverter
- JSON Schema：io.confluent.connect.json.JsonSchemaConverter
- ByteArray：org.apache.kafka.connect.converters.ByteArrayConverter

## 3. JSON 和 Schema

虽然 JSON 默认不支持嵌入 Schema，但 Kafka Connect 提供了两种方式使用 JSON 时声明 Schema。第一种是使用 Confluent Schema Registry 来使用 JSON Schema。如果你不能使用 Confluent Schema Registry，第二种方式提供了一种可以将 Schema 嵌入到消息中的特定 JSON 格式。由于 Schema 被包含在消息中，因此生成的消息大小可能会变大。

如果你正在设置 Kafka Connect Source，并期望 Kafka Connect 在写入 Kafka 消息时包含 Schema，你需要如下设置：
```
value.converter=org.apache.kafka.connect.json.JsonConverter
value.converter.schemas.enable=true
```
最终生成的 Kafka 消息看起来如下所示：
```json
{
  "schema": {
    "type": "struct",
    "fields": [
      {
        "type": "int64",
        "optional": false,
        "field": "registertime"
      },
      {
        "type": "string",
        "optional": false,
        "field": "userid"
      },
      {
        "type": "string",
        "optional": false,
        "field": "regionid"
      },
      {
        "type": "string",
        "optional": false,
        "field": "gender"
      }
    ],
    "optional": false,
    "name": "ksql.users"
  },
  "payload": {
    "registertime": 1493819497170,
    "userid": "User_1",
    "regionid": "Region_5",
    "gender": "MALE"
  }
}
```
需要注意的是消息大小以及消息组成部分（playload 和 schema）。每条消息中都会重复这些数据，这也就是为什么说 JSON Schema 或者 Avro 这样的格式会更好，因为 Schema 是单独存储的，消息中只包含 payload。

如果你正在使用 Kafka Connect 消费 Kafka Topic 中的 JSON 数据，你需要了解 JSON 是如何序列化的。如果使用的是 JSON Schema 序列化器，那么你需要在 Kafka Connect 中设置使用 JSON Schema Converter (io.confluent.connect.json.JsonSchemaConverter)。如果 JSON 数据是作为普通字符串写入的，那么你需要确定数据是否包含嵌套模式。如果包含了，并且格式与上述的格式相同，那么你可以这样设置：
```
value.converter=org.apache.kafka.connect.json.JsonConverter
value.converter.schemas.enable=true
```
然而，如果你正在消费的 JSON 数据，并没有 schema/payload 结构，如下所示：
```json
{
  "registertime": 1489869013625,
  "userid": "User_1",
  "regionid": "Region_2",
  "gender": "OTHER"
}
```
那么你必须通过设置 schemas.enable = false 来告诉 Kafka Connect 不要寻找 Schema：
```
value.converter=org.apache.kafka.connect.json.JsonConverter
value.converter.schemas.enable=false
```

## 4. 常见错误

如果你错误地配置了 Converter，你将会遇到如下的一些常见错误。这些消息会出现在 Kafka Connect 配置的 Sink 中，因为你试图在 Sink 中反序列化 Kafka 消息。这些错误会导致 Connector 失败，主要错误消息如下所示：
```java
ERROR WorkerSinkTask{id=sink-file-users-json-noschema-01-0} Task threw an uncaught and unrecoverable exception (org.apache.kafka.connect.runtime.WorkerTask)
org.apache.kafka.connect.errors.ConnectException: Tolerance exceeded in error handler
   at org.apache.kafka.connect.runtime.errors.RetryWithToleranceOperator. execAndHandleError(RetryWithToleranceOperator.java:178)
   at org.apache.kafka.connect.runtime.errors.RetryWithToleranceOperator.execute (RetryWithToleranceOperator.java:104)
```
在错误消息的后面，你将看到进一步的堆栈信息，详细描述了出错的原因。需要注意的是，Connector 中任何致命的错误，都会抛出如上异常，因此你很可能会在与序列化无关的错误中看到这种错误。为了快速可视化你可以预见的错误配置，这里有一个快速参考：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-connect-deep-dive-converters-serialization-explained-4.png?raw=true)

### 4.1 问题:使用 JsonConverter 读取非 JSON 数据

如果你的 Source Topic 上有非 JSON 数据，但你尝试使用 JsonConverter 去读取，你将看到如下错误：
```java
org.apache.kafka.connect.errors.DataException: Converting byte[] to Kafka Connect data failed due to serialization error:
…
org.apache.kafka.common.errors.SerializationException: java.io.CharConversionException: Invalid UTF-32 character 0x1cfa7e2 (above 0x0010ffff) at char #1, byte #7)
```
这可能是因为 Source Topic 使用了 Avro 或其他格式造成的。解决方案是如果数据是 Avro 格式的，那么需要修改 Kafka Connect Sink 为：
```json
"value.converter": "io.confluent.connect.avro.AvroConverter",
"value.converter.schema.registry.url": "http://schema-registry:8081",
```
或者，如果 Topic 是通过 Kafka Connect 写入的，那么你也可以让上游 Source 输出 JSON 数据：
```json
"value.converter": "org.apache.kafka.connect.json.JsonConverter",
"value.converter.schemas.enable": "false",
```

### 4.2 问题:使用 AvroConverter 读取非 Avro 数据

这可能是我在 Confluent Community 邮件组和 Slack 组中经常会看到的错误。当你试图使用 Avro Converter 从非 Avro Topic 读取数据时，就会发生这种错误。这包括使用其他 Avro 序列化器而不是 Confluent Schema Registry 的 Avro 序列化器，后者有自己的特殊格式：
```java
org.apache.kafka.connect.errors.DataException: my-topic-name
at io.confluent.connect.avro.AvroConverter.toConnectData(AvroConverter.java:97)
…
org.apache.kafka.common.errors.SerializationException: Error deserializing Avro message for id -1
org.apache.kafka.common.errors.SerializationException: Unknown magic byte!
```
解决方案是检查 Source Topic 的序列化格式，修改 Kafka Connect Sink Connector 使用正确的 Converter，或者将上游格式切换为 Avro(这是一个更好的主意)。如果上游 Topic 是通过 Kafka Connect 写入的，那么你可以按如下方式配置 Source Connector 的 Converter：
```json
"value.converter": "io.confluent.connect.avro.AvroConverter",
"value.converter.schema.registry.url": "http://schema-registry:8081",
```

### 4.3 问题:读取 JSON 消息时没有预期的 schema/payload 结构

如上所述，Kafka Connect 支持一种特殊的 JSON 消息结构，该结构包含 payload 和 schema。如果你读取的 JSON 数据不包含这种结构，你会看到如下错误：
```java
org.apache.kafka.connect.errors.DataException: JsonConverter with schemas.enable requires "schema" and "payload" fields and may not contain additional fields. If you are trying to deserialize plain JSON data, set schemas.enable=false in your converter configuration.
```
需要说明的是，当 schemas.enable=true 时，唯一有效的 JSON 结构需要包含 schema 和 payload 这两个顶级元素。如果你只有纯 JSON 数据，需要修改 Connector 的配置为：
```json
"value.converter": "org.apache.kafka.connect.json.JsonConverter",
"value.converter.schemas.enable": "false",
```
如果你想在数据中包含 Schema，你可以使用 Avro（推荐），或者配置上游的 Kafka Connect 让消息中包含 Schema：
```json
"value.converter": "org.apache.kafka.connect.json.JsonConverter",
"value.converter.schemas.enable": "true",
```

## 5. 故障排除技巧

### 5.1 查找 Kafka Connect Worker 日志

要从 Kafka Connect 中找到错误日志，你需要找到 Kafka Connect Worker 的输出。输出位置取决于你是如何启动 Kafka Connect 的。有几种安装 Kafka Connect 的方法，包括 Docker、Confluent CLI、systemd 和手动下载压缩包：
- Docker：`docker logs container_name`
- Confluent CLI：`confluent log connect`
- systemd：日志文件写到 `/var/log/confluent/kafka-connect`
- 其他：默认情况下，Kafka Connect 将其输出发送到 stdout，因此你可以在启动 Kafka Connect 的终端中找到它们。

### 5.2 查看 Kafka Connect 配置文件

要改变 Kafka Connect Worker 的配置属性(适用于所有运行的 Connector)，需要设置相应的配置。

(1) Docker：设置环境变量，例如，在 Docker Compose 中：
```
CONNECT_KEY_CONVERTER: io.confluent.connect.avro.AvroConverter
CONNECT_KEY_CONVERTER_SCHEMA_REGISTRY_URL: 'http://schema-registry:8081'
CONNECT_VALUE_CONVERTER: io.confluent.connect.avro.AvroConverter
CONNECT_VALUE_CONVERTER_SCHEMA_REGISTRY_URL: 'http://schema-registry:8081'
```
(2) Confluent CLI：使用 etc/schema-registry/connect-avro-distributed.properties 配置文件

(3) systemd（deb/rpm）：使用 /etc/kafka/connect-distributed.properties 配置文件

(4) 其他：在启动 Kafka Connect 时指定 Worker 的配置文件，例如：
```
$ cd confluent-5.5.0
$ ./bin/connect-distributed ./etc/kafka/connect-distributed.properties
```

## 6. 内部 Converter

在分布式模式下运行时，Kafka Connect 使用 Kafka 本身来存储有关其操作的元数据，包括 Connector 配置、偏移量等。这些 Kafka Topic 本身可以通过 internal.key.converter/internal.value.converter 使用不同的 Converter。不过这些设置仅供内部使用，并且在 Apache Kafka 2.0 中已被弃用。你不需要修改这些配置，从 Apache Kafka 2.0 版开始，如果你修改这些配置，将会收到报警。

## 7. 结论

Kafka Connect 是一个非常简单但功能强大的工具，可以用来与 Kafka 集成其他系统。一个最常见的误解是 Kafka Connect 提供的 Converter。我们已经讲过 Kafka 的消息只是键/值对，重要的是要理解你应该使用哪种序列化，然后在你的 Kafka Connect Connector 中标准化它。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文：
- [Kafka Connect Deep Dive – Converters and Serialization Explained](https://www.confluent.io/blog/kafka-connect-deep-dive-converters-serialization-explained/)

相关推荐：
- [Kafka Connect 构建大规模低延迟的数据管道](http://smartsi.club/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines.html)
- [Kafka Connect 如何构建实时数据管道](http://smartsi.club/how-to-build-a-pipeline-with-kafka-connect.html)
- [Kafka Connect JDBC Source MySQL 全量同步](http://smartsi.club/mysql-bulk-with-kafka-connect-jdbc-source.html)
- [Kafka Connect JDBC Source MySQL 增量同步](http://smartsi.club/mysql-inc-with-kafka-connect-jdbc-source.html)
