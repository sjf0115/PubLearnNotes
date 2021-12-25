---
layout: post
author: smartsi
title: 深入理解 Kafka Connect: 转换器和序列化
date: 2021-12-24 13:55:00
tags:
  - Kafka

categories: Kafka
permalink: kafka-connect-deep-dive-converters-serialization-explained
---

Kafka Connect 是 Apache Kafka 的一部分，提供了数据存储和 Kafka 之间的流式集成。对于数据工程师来说，只需要配置 JSON 文件就可以使用 。Kafka 为一些常见数据存储的提供了 Connector，比如，JDBC、Elasticsearch、IBM MQ、S3 和 BigQuery 等等。对于开发人员来说，Kafka Connect 提供了丰富的 API，如果有必要还可以开发其他 Connector。除此之外，还提供了用于配置和管理 Connector 的 REST API。

Kafka Connect 是一种模块化组件，提供了一种非常强大的集成方法。一些关键组件包括：
- Connectors（连接器）：定义如何与数据存储集成的 JAR 文件；
- Converters（转换器）：处理数据的序列化和反序列化；
- Transforms（变换器）：可选的运行时消息操作。

人们对 Kafka Connect 最常见的误解与数据的序列化有关。Kafka Connect 使用 Converters 处理数据序列化。接下来让我们看看它们是如何工作的，并说明如何解决一些常见问题。

## 1. Kafka 消息都是字节

Kafka 消息被组织保存在 Topic 中，每条消息就是一个键值对，这些对 Kafka 已经足够了。当它们存储在 Kafka 中时，键和值都只是字节。这样 Kafka 就可以适用于各种不同场景，但这也意味着开发人员需要决定如何序列化数据。

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
- Schema：很多时候，我们的数据都有对应的 Schema。你可能不喜欢，但作为开发人员，你有责任保留和传播 Schema。Schema 为服务之间提供了一种契约。有些消息格式（例如，Avro 和 Protobuf）具有强大的 Schema 支持，然而有些消息格式支持较少（JSON）或根本不支持（CVS）。
- 生态系统兼容性：Avro、Protobuf 和 JSON 是 Confluent 平台的一等公民，拥有来自 Confluent Schema Registry、Kafka Connect、KSQL 的原生支持。
- 消息大小：JSON 是纯文本的，并且依赖了 Kafka 本身的压缩机制，Avro 和 Protobuf 是二进制格式，因此可以提供更小的消息体积。
- 语言支持：Avro 在 Java 领域得到了强大的支持，而如果你使用的是 Go 语言，那么你很可能会期望使用 Protobuf。

### 1.2 如果目标系统使用 JSON，Kafka Topic 也必须使用 JSON 吗？

完全不需要这样。从数据源读取数据或将数据写入外部数据存储的格式不需要与 Kafka 消息的序列化格式一样。Kafka Connect 中的 Connector 负责从源数据存储（例如，数据库）获取数据，并以数据内部表示将数据传给 Converter。然后，Converter 将这些源数据对象序列化到 Topic 上。

在使用 Kafka Connect 作为 Sink 时刚好相反，Converter 将来自 Topic 的数据反序列化为内部表示，然后传给 Connector 并使用针对于目标存储的适当方法将数据写入目标数据存储。也就是说，当你将数据写入 HDFS 时，Topic 中的数据可以是 Avro 格式，Sink 的 Connector 只需要使用 HDFS 支持的格式即可（不用必须是 Avro 格式）。

## 2. 配置 Converter

Kafka Connect 默认使用 Worker 级别的 Converter 配置，Connector 可以对其进行覆盖。通常在整个 Pipeline 中使用相同的序列化格式是一种更好的选择，所以一般只需要在 Worker 级别配置 Converter，不需要在 Connector 中指定。但你可能需要从别人的 Topic 中拉取数据，而他们使了用不同的序列化格式，对于这种情况，你需要在 Connector 配置中设置 Converter。即使你在 Connector 的配置中进行了覆盖，但执行实际任务的仍然是 Converter。正确编写的 Connector 一般不会序列化或反序列化存储在 Kafka 中的消息，最终还是会让 Converter 来完成这项工作。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-connect-deep-dive-converters-serialization-explained-2.png?raw=true)

需要记住的是，Kafka 的消息是键值对字节，你需要使用 key.converter 和 value.converter 分别为键和值指定 Converter。在某些情况下，你可以为键和值分别使用不同的 Converter。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-connect-deep-dive-converters-serialization-explained-3.png?raw=true)

下面是一个使用字符串 Converter 的例子。因为只是一个字符串，没有数据的 Schema，因此使用它的值不是很有用:
```json
"key.converter": "org.apache.kafka.connect.storage.StringConverter",
```
有些 Converter 有一些额外的配置。对于 Avro，你需要指定 Schema Registry。对于 JSON，你需要指定是否希望 Kafka Connect 将 Schema 嵌入到 JSON 消息中。在指定特定于 Converter 的配置时，请始终使用 key.converter. 或 value.converter. 前缀。例如，要将 Avro 用于消息载荷，你需要指定以下内容：
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

如果你正在设置 Kafka Connect Source，并希望 Kafka Connect 在写入 Kafka 消息时包含 Schema，你需要如下设置：
```
value.converter=org.apache.kafka.connect.json.JsonConverter
value.converter.schemas.enable=true
```
最终生成的 Kafka 消息看起来像下面这样，其中包含 schema 和 payload 元素：
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
需要注意的是消息的大小以及消消息由 playload 和 schema 组成。每条消息中都会重复这些数据，这也就是为什么说 JSON Schema 或者 Avro 这样的格式会更好，因为 Schema 是单独存储的，消息中只包含 payload（并进行了压缩）。

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
那么你必须通过设置 schemas.enable = false 告诉 Kafka Connect 不要查找 Schema：
```
value.converter=org.apache.kafka.connect.json.JsonConverter
value.converter.schemas.enable=false
```
和之前一样，Converter 配置选项（这里是 schemas.enable）需要使用 key.converter 或 value.converter 前缀。

## 4. 常见错误

如果你错误地配置了 Converter，将会遇到如下的一些常见错误。这些消息会出现在你为 Kafka Connect 配置的 Sink 中，因为你试图在 Sink 中反序列化 Kafka 消息。这些错误会导致 Connector 失败，主要错误消息如下所示：
```java
ERROR WorkerSinkTask{id=sink-file-users-json-noschema-01-0} Task threw an uncaught and unrecoverable exception (org.apache.kafka.connect.runtime.WorkerTask)
org.apache.kafka.connect.errors.ConnectException: Tolerance exceeded in error handler
   at org.apache.kafka.connect.runtime.errors.RetryWithToleranceOperator. execAndHandleError(RetryWithToleranceOperator.java:178)
   at org.apache.kafka.connect.runtime.errors.RetryWithToleranceOperator.execute (RetryWithToleranceOperator.java:104)
```
在错误消息的后面，你将看到进一步的堆栈信息，详细描述了出错的原因。需要注意的是，对于 Connector 中任何致命的错误，都会抛出上述异常，因此你可能会看到与序列化无关的错误。为了快速可视化你可以预见的错误配置，这里有一个快速参考:

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/kafka-connect-deep-dive-converters-serialization-explained-4.png?raw=true)

### 4.1 使用 JsonConverter 读取非 JSON 数据

如果你的 Source Topic 上有非 JSON 数据，但你尝试使用 JsonConverter 读取，你将看到如下错误：
```java
org.apache.kafka.connect.errors.DataException: Converting byte[] to Kafka Connect data failed due to serialization error:
…
org.apache.kafka.common.errors.SerializationException: java.io.CharConversionException: Invalid UTF-32 character 0x1cfa7e2 (above 0x0010ffff) at char #1, byte #7)
```
这有可能是因为 Source Topic 使用了 Avro 或其他格式。解决方案是如果数据是 Avro 格式的，那么将 Kafka Connect Sink 的配置改为：
```json
"value.converter": "io.confluent.connect.avro.AvroConverter",
"value.converter.schema.registry.url": "http://schema-registry:8081",
```
或者，如果 Topic 数据是通过 Kafka Connect 填充的，那么你也可以这么做，让上游 Source 也发送 JSON 数据：
```json
"value.converter": "org.apache.kafka.connect.json.JsonConverter",
"value.converter.schemas.enable": "false",
```

### 4.2 使用 AvroConverter 读取非 Avro 数据

这可能是我在 Confluent Community 邮件组和 Slack 组等地方经常看到的错误。当你尝试使用 Avro Converter 从非 Avro Topic 读取数据时，就会发生这种情况。这包括使用 Avro 序列化器而不是 Confluent Schema Registry 的 Avro 序列化器（它有自己的格式）写入的数据：
```java
org.apache.kafka.connect.errors.DataException: my-topic-name
at io.confluent.connect.avro.AvroConverter.toConnectData(AvroConverter.java:97)
…
org.apache.kafka.common.errors.SerializationException: Error deserializing Avro message for id -1
org.apache.kafka.common.errors.SerializationException: Unknown magic byte!
```
解决方案是检查 Source Topic 的序列化格式，修改 Kafka Connect Sink Connector，让它使用正确的 Converter，或者将上游格式切换为 Avro。如果上游 Topic 是通过 Kafka Connect 填充的，则可以按如下方式配置 Source Connector 的 Converter：
```json
"value.converter": "io.confluent.connect.avro.AvroConverter",
"value.converter.schema.registry.url": "http://schema-registry:8081",
```

### 4.3 没有使用预期的 schema/payload 结构读取 JSON 消息

如前所述，Kafka Connect 支持一种特殊的 JSON 消息结构，该结构包含 payload 和 schema。如果你试图读取不包含这种结构的 JSON 数据，你会得到这个错误：
```java
org.apache.kafka.connect.errors.DataException: JsonConverter with schemas.enable requires "schema" and "payload" fields and may not contain additional fields. If you are trying to deserialize plain JSON data, set schemas.enable=false in your converter configuration.
```
需要说明的是，当 schemas.enable=true 时，唯一有效的 JSON 结构需要包含 schema 和 payload 这两个顶级元素。如果你只有简单的 JSON 数据，则应将 Connector 的配置改为：
```json
"value.converter": "org.apache.kafka.connect.json.JsonConverter",
"value.converter.schemas.enable": "false",
```
如果要在数据中包含 Schema，可以使用 Avro（推荐），也可以修改上游的 Kafka Connect 配置，让它在消息中包含 Schema：
```json
"value.converter": "org.apache.kafka.connect.json.JsonConverter",
"value.converter.schemas.enable": "true",
```

## 5. 故障排除技巧

### 5.1 查看 Kafka Connect 日志

要在 Kafka Connect 中查找错误日志，你需要找到 Kafka Connect Worker 的输出。输出位置取决于你是如何启动 Kafka Connect 的。有几种安装 Kafka Connect 的方法，包括 Docker、Confluent CLI、systemd 和手动下载压缩包。你可以这样查找日志的输出位置：
- Docker：docker logs container_name；
- Confluent CLI：confluent log connect；
- systemd：日志文件在 /var/log/confluent/kafka-connect；
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
(2) Confluent CLI：使用配置文件 etc/schema-registry/connect-avro-distributed.properties；
(3) systemd（deb/rpm）：使用配置文件 /etc/kafka/connect-distributed.properties；
(4) 其他：在启动 Kafka Connect 时指定 Worker 的配置文件，例如：
```
$ cd confluent-5.5.0
$ ./bin/connect-distributed ./etc/kafka/connect-distributed.properties
```

### 5.3 检查 Kafka Topic

假设我们遇到了上述当中的一个错误，并想要解决为什么我们的 Kafka Connect Sink Connector 不能读取 Topic。我们需要检查正在被读取的 Topic 数据，并确保它使用了正确的序列化格式。另外，所有消息都必须使用这种格式，所以不要想当然地认为以正确的格式向 Topic 发送消息就不会出问题。Kafka Connect 和其他消费者也会从 Topic 上读取已有的消息。下面，我将使用命令行进行故障排除，当然也可以使用其他的一些工具：
- Confluent Control Center 提供了可视化检查主题内容的功能；
- KSQL 的 PRINT 命令将主题的内容打印到控制台；
- Confluent CLI 工具提供了 consume 命令，可用于读取字符串和 Avro 数据。

### 5.4 如果你的数据是字符串或 JSON 格式

你可以使用控制台工具，包括 kafkacat 和 kafka-console-consumer。我个人的偏好是使用 kafkacat：
```
$ kafkacat -b localhost:9092 -t users-json-noschema -C -c1
{"registertime":1493356576434,"userid":"User_8","regionid":"Region_2","gender":"MALE"}
```
你也可以使用 jq 验证和格式化 JSON：
```
$ kafkacat -b localhost:9092 -t users-json-noschema -C -c1|jq '.'
{
  "registertime": 1493356576434,
  "userid": "User_8",
  "regionid": "Region_2",
  "gender": "MALE"
}
```
如果你得到一些“奇怪的”字符，你查看的很可能是二进制数据，这些数据是通过 Avro 或 Protobuf 写入的：
```
$ kafkacat -b localhost:9092 -t users-avro -C -c1
ڝ���VUser_9Region_MALE
```

### 5.5 如果你的数据是 Avro 格式

你应该使用专为读取和反序列化 Avro 数据而设计的控制台工具。在这里，我使用的是 kafka-avro-console-consumer。确保指定了正确的 Schema Registry URL：
```
$ kafka-avro-console-consumer --bootstrap-server localhost:9092 \
                              --property schema.registry.url=http://localhost:8081 \
                              --topic users-avro \
                              --from-beginning --max-messages 1
{"registertime":1505213905022,"userid":"User_5","regionid":"Region_4","gender":"FEMALE"}
```
和前面一样，如果你想格式化，可以使用 jq:
```
$ kafka-avro-console-consumer --bootstrap-server localhost:9092 \
                              --property schema.registry.url=http://localhost:8081 \
                              --topic users-avro \
                              --from-beginning --max-messages 1 | \
                              jq '.'
{
  "registertime": 1505213905022,
  "userid": "User_5",
  "regionid": "Region_4",
  "gender": "FEMALE"
}
```

## 6. 内部 Converter

在分布式模式下运行时，Kafka Connect 使用 Kafka 来存储有关其操作的元数据，包括 Connector 配置、偏移量等。可以通过 internal.key.converter/internal.value.converter 让这些 Kafka 使用不同的 Converter。不过这些设置只在内部使用，实际上从 Apache Kafka 2.0 开始就已被弃用。你不应该更改这些配置，从 Apache Kafka 2.0 版开始，如果你这么做了将会收到警告。

## 7. 将 Schema 应用于没有 Schema 的消息

很多时候，Kafka Connect 会从已经存在 Schema 的地方引入数据，并使用合适的序列化格式（例如，Avro）来保留这些 Schema。然后，这些数据的所有下游用户都可以从这些 Schema 中获益，同时还可以保证 Schema Registry 之类所提供的兼容性。但如果没有提供显式的 Schema 该怎么办？

或许你正在使用 FileSourceConnector 从普通文件中读取数据（不建议用于生产环境中，但可用于 PoC），或者正在使用 REST Connector 从 REST 端点提取数据。由于它们都没有固有的 Schema，因此你需要声明它。

有时候你只想传递你从 Source 读取的字节，并将它们保存在 Topic 上。但大多数情况下，你需要 Schema 来使用这些数据。在摄取时应用一次 Schema，而不是将问题推到每个消费者，这才是一种更好的处理方式。

你可以编写自己的 Kafka Streams 应用程序，将 Schema 应用于 Kafka Topic 中的数据上，当然你也可以使用 KSQL。下面让我们来看一下将 Schema 应用于某些 CSV 数据的简单示例。假设我们有一个 Kafka Topic testdata-csv，保存着一些 CSV 数据，看起来像这样：
```
$ kafkacat -b localhost:9092 -t testdata-csv -C
1,Rick Astley,Never Gonna Give You Up
2,Johnny Cash,Ring of Fire
```
我们可以猜测它有三个字段，分别是：ID、Artist、Song。如果像这样将数据保留 Topic 中，那么任何想要使用这些数据的应用程序，无论是 Kafka Connect Sink 还是自定义的 Kafka 应用程序，每次都需要都猜测 Schema 是什么。或者，同样糟糕的是，每个消费应用程序的开发人员都需要向提供数据的团队确认 Schema 是否发生变更。正如 Kafka 可以解耦系统一样，这种 Schema 依赖让团队之间也有了硬性耦合，这并不是一件好事。因此，我们要做的是使用 KSQL 将 Schema 应用于数据上，并使用一个新的派生 Topic 来保存 Schema。这样你就可以通过 ksqlDB 检查 Topic 数据：
```
ksql> PRINT 'testdata-csv' FROM BEGINNING;
Format:STRING
11/6/18 2:41:23 PM UTC , NULL , 1,Rick Astley,Never Gonna Give You Up
11/6/18 2:41:23 PM UTC , NULL , 2,Johnny Cash,Ring of Fire
```
这里的前两个字段（11/6/18 2:41:23 PM UTC 和 NULL）分别是 Kafka 消息的时间戳和键。其余字段来自 CSV 文件。现在让我们用 ksqlDB 注册这个 Topic 并声明 Schema：
```
ksql> CREATE STREAM TESTDATA_CSV (ID INT, ARTIST VARCHAR, SONG VARCHAR) \
WITH (KAFKA_TOPIC='testdata-csv', VALUE_FORMAT='DELIMITED');

Message
----------------
Stream created
----------------
```
可以看到，ksqlDB 现在有一个数据流 schema：
```
ksql> DESCRIBE TESTDATA_CSV;

Name                 : TESTDATA_CSV
 Field   | Type
-------------------------------------
 ROWTIME | BIGINT (system)
 ROWKEY  | VARCHAR(STRING) (system)
 ID      | INTEGER
 ARTIST  | VARCHAR(STRING)
 SONG    | VARCHAR(STRING)
-------------------------------------
For runtime statistics and query details run: DESCRIBE EXTENDED <Stream,Table>;
```
通过查询 ksqlDB 流来检查数据是否符合预期。需要注意的是，在这一点上，这个时候我们只是作为现有 Kafka Topic 的消费者，并没有更改或复制任何数据。
```
ksql> SET 'auto.offset.reset' = 'earliest';
Successfully changed local property 'auto.offset.reset' from 'null' to 'earliest'
ksql> SELECT ID, ARTIST, SONG FROM TESTDATA_CSV;
1 | Rick Astley | Never Gonna Give You Up
2 | Johnny Cash | Ring of Fire
```
最后，创建一个新的 Kafka Topic，由重新序列化的数据和 Schema 填充。ksqlDB 查询是连续的，因此除了从源 Topic 向目标 Topic 发送任何现有数据外，ksqlDB 还将向 Topic 发送未来任何的数据。
```
ksql> CREATE STREAM TESTDATA WITH (VALUE_FORMAT='AVRO') AS SELECT * FROM TESTDATA_CSV;

Message
----------------------------
Stream created and running
----------------------------
```
使用 Avro 控制台消费者验证数据：
```
$ kafka-avro-console-consumer --bootstrap-server localhost:9092 \
                                --property schema.registry.url=http://localhost:8081 \
                                --topic TESTDATA \
                                --from-beginning | \
                                jq '.'
{
  "ID": {
    "int": 1
},
  "ARTIST": {
    "string": "Rick Astley"
},
  "SONG": {
    "string": "Never Gonna Give You Up"
  }
}
[…]
```
你甚至可以在 Schema Registry 中查看已注册的 Schema：
```json
$ curl -s http://localhost:8081/subjects/TESTDATA-value/versions/latest|jq '.schema|fromjson'
{
  "type": "record",
  "name": "KsqlDataSourceSchema",
  "namespace": "io.confluent.ksql.avro_schemas",
  "fields": [
    {
      "name": "ID",
      "type": [
        "null",
        "int"
      ],
      "default": null
    },
    {
      "name": "ARTIST",
      "type": [
        "null",
        "string"
      ],
      "default": null
    },
    {
      "name": "SONG",
      "type": [
        "null",
        "string"
      ],
      "default": null
    }
  ]
}
```
任何写入原始 Topic（testdata-csv）的新消息都由 KSQL 自动处理，并以 Avro 格式写入新的 TESTDATA Topic。现在，任何想要使用这些数据的应用程序或团队都可以使用 TESTDATA Topic。你还可以更改主题的分区数、分区键和复制因子。

## 8. 结论

Kafka Connect 是一个非常简单但功能强大的工具，可以用来与 Kafka 集成其他系统。一个最常见的误解是 Kafka Connect 提供的 Converter。我们已经讲过 Kafka 的消息只是键/值对，重要的是要理解你应该使用哪种序列化，然后在你的 Kafka Connect Connector 中标准化它。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- [Kafka Connect JDBC Source Connector](https://turkogluc.com/kafka-connect-jdbc-source-connector/)

相关推荐：
- [Kafka Connect 构建大规模低延迟的数据管道](http://smartsi.club/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines.html)
- [Kafka Connect 如何构建实时数据管道](http://smartsi.club/how-to-build-a-pipeline-with-kafka-connect.html)
- [Kafka Connect JDBC Source MySQL 全量同步](http://smartsi.club/mysql-bulk-with-kafka-connect-jdbc-source.html)
- [Kafka Connect JDBC Source MySQL 增量同步](http://smartsi.club/mysql-inc-with-kafka-connect-jdbc-source.html)

原文：
- [Kafka Connect Deep Dive – Converters and Serialization Explained](https://www.confluent.io/blog/kafka-connect-deep-dive-converters-serialization-explained/)
