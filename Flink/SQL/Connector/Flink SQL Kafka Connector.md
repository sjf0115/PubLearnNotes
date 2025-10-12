---
layout: post
author: smartsi
title: Flink SQL Kafka Connector
date: 2021-08-15 15:47:21
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-kafka-connector
---

> Flink 版本：1.13

Kafka Connector 提供了从 Kafka topic 中消费和写入数据的能力。

### 1. 依赖

使用 Maven 构建自动化工具的项目，如果想使用 Kafka Connector 需要引入如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-connector-kafka_2.11</artifactId>
  <version>1.13.0</version>
</dependency>
```
如果是使用的 SQL 客户端，需要[下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka_2.11/1.13.0/flink-sql-connector-kafka_2.11-1.13.0.jar)对应的 Jar 包放在 flink 安装目录的 lib 文件夹下。

### 2. 创建Kafka表

如下示例展示了如何创建一个 Kafka Source 表：
```sql
CREATE TABLE kafka_source_table (
  uid STRING COMMENT '用户Id',
  wid STRING COMMENT '微博Id',
  tm STRING COMMENT '发微博时间',
  content STRING COMMENT '微博内容'
) WITH (
  'connector' = 'kafka',
  'topic' = 'behavior',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'kafka-example',
  'scan.startup.mode' = 'earliest-offset',
  'value.format' = 'json',
  'value.json.ignore-parse-errors' = 'true'
);
```

### 3. 获取元数据

如下 Connector 元数据可以在表定义中通过元数据列来获取：

| Key | 数据类型 | 说明 | R/W |
| :------------- | :------------- | :------------- | :------------- |
| topic | STRING NOT NULL | Kafka 记录的 Topic 名称 | R |
| partition	| INT NOT NULL | Kafka 记录的 Partition ID | R |
| headers	| MAP NOT NULL | 二进制 Map 类型的 Kafka 记录头（Header）| R/W |
| leader-epoch | INT NULL | Kafka 记录的 Leader epoch（如果可用）|	R |
| offset | BIGINT NOT NULL | Kafka 记录在 Partition 中的偏移量 | R |
| timestamp | TIMESTAMP_LTZ(3) NOT NULL | Kafka 记录的时间戳 | R/W |
| timestamp-type | STRING NOT NULL | Kafka 记录的时间戳类型。可能的类型有 NoTimestampType、CreateTime（会在写入元数据时设置）以及 LogAppendTime | R |

> R/W 列定义了一个元数据是可读（R）还是可写（W）。只读列必须声明为 VIRTUAL 以在 INSERT INTO 操作中排除它们。

如下示例展示了如何使用这些元数据字段：
```sql
CREATE TABLE kafka_meta_source_table (
  -- 元数据字段
  `topic` STRING METADATA VIRTUAL, -- 不指定 FROM
  `partition_id` STRING METADATA FROM 'partition' VIRTUAL, -- 指定 FROM
  `offset` BIGINT METADATA VIRTUAL,  -- 不指定 FROM
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL, -- 指定 FROM
  -- 业务字段
  `uid` STRING COMMENT '用户Id',
  `wid` STRING COMMENT '微博Id',
  `tm` STRING COMMENT '发微博时间',
  `content` STRING COMMENT '微博内容'
) WITH (
  'connector' = 'kafka',
  'topic' = 'behavior',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'kafka-meta-example',
  'scan.startup.mode' = 'earliest-offset',
  'value.format' = 'json',
  'value.json.ignore-parse-errors' = 'true'
);
```
> 如果表字段名称与元数据字段名称相同，可以不用指定 FROM，例如，offset。如果想使用不同的字段名称，需要指定 FROM，比如，partition_id。

实际效果如下所示：
```java
behavior:2> +I[weibo_user_behavior, 0, 18, 2025-09-06T22:13:15.297, c01014739c046cd31d6f1b4fb71b440f, 0cd5ef13eb11ed0070f7625b14136ec9, 2015-08-19 22:44:55]
behavior:2> +I[weibo_user_behavior, 0, 19, 2025-09-06T22:13:15.861, fa5aed172c062c61e196eac61038a03b, 7cce78a4ad39a91ec1f595bcc7fb5eba, 2015-08-01 14:06:31]
behavior:2> +I[weibo_user_behavior, 0, 20, 2025-09-06T22:13:16.850, 77fc723c196a45203e70f4d359c96946, a3494d8cf475a92739a2ffd421640ddf, 2015-08-04 10:51:38]
behavior:2> +I[weibo_user_behavior, 0, 21, 2025-09-06T22:13:17.854, e4097b07f34366399b623b94f174f60c, 6b89aea5aa7af093dde0894156c49dd3, 2015-08-16 14:59:19]
behavior:2> +I[weibo_user_behavior, 0, 22, 2025-09-06T22:13:18.854, d43f7557c303b84070b13aa4eeeb21d3, 0bdeff19392e15737775abab46dc5437, 2015-08-04 22:30:46]
behavior:2> +I[weibo_user_behavior, 0, 23, 2025-09-06T22:13:19.852, 87465974e53e9f047e355e6e9b135b55, 545c14094cbe50679daa63fe16419111, 2015-08-20 19:42:50]
behavior:2> +I[weibo_user_behavior, 0, 24, 2025-09-06T22:13:20.855, 1425c7ee0ddf04e56cfe1af1443a45c8, d84ec9d2ca0c71b88385e11310c3bfa7, 2015-08-28 00:34:31]
behavior:2> +I[weibo_user_behavior, 0, 25, 2025-09-06T22:13:21.858, fd17277c9db465ff66612b3bdd0faf85, e3fafecf482b3ad2f899ea971feae4c6, 2015-08-18 22:11:37]
behavior:2> +I[weibo_user_behavior, 0, 26, 2025-09-06T22:13:22.858, bcbb49cd919fd563a424e9651a1e54c6, 7e24ef184b183339b68900282e095bdf, 2015-08-29 18:51:49]
```

> 完整示例代码请查阅： [KafkaMetaExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/sql/connector/kafka/KafkaMetaExample.java)

### 4. Connector 参数

| 参数选项 | 是否必填项 | 默认值 | 数据类型 | 说明 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| connector | 必填 | 无 | String | 指定使用的 Connector 名称，对于 Kafka 为 'kafka' |
| topic | Sink 必填	| 无 | String | 当用作 Source 时为读取数据的 topic 名。也支持用分号间隔的 topic 列表，如 'topic-1;topic-2'。注意，对 Source 表而言，'topic' 和 'topic-pattern' 两个选项只能使用其中一个；当被用作 Sink 时为数据写入的 topic 名。注意 Sink 不支持分号间隔的 topic 列表 |
| topic-pattern | 可选 | 无 | String | 匹配读取 topic 名称的正则表达式。在作业开始运行时，所有匹配该正则表达式的 topic 都将被 Kafka consumer 订阅。注意，对 source 表而言，'topic' 和 'topic-pattern' 两个选项只能使用其中一个 |
| properties.bootstrap.servers | 必填 | 无 | String | 逗号分隔的 Kafka Broker 列表 |
| properties.group.id | Source 必填 | 无 | String | Kafka Source 的消费组id |
| properties.* | 可选	| 无 |	String | 可以设置和传递的任意 Kafka 配置项。后缀名必须与 Kafka 文档中的相匹配。Flink 会删除 "properties." 前缀并将变换后的配置键和值传入底层的 Kafka 客户端。例如，你可以通过 'properties.allow.auto.create.topics' = 'false' 来禁用 topic 的自动创建。但是某些配置项不支持进行配置，因为 Flink 会覆盖这些配置，例如 'key.deserializer' 和 'value.deserializer'。|
| format | 必填 |	无	| String | 序列化或反序列化 Kafka 消息 Value 部分的 Format。注意：该配置项和 'value.format' 二者必需其一。|
| key.format | 可选	| 无 |	String | 序列化和反序列化 Kafka 消息 Key 部分的 Format。注意：该配置项与 'key.fields' 配置项必须成对出现。否则 Kafka 记录将使用空值作为键。|
| key.fields | 可选	| [] | `List<String>`	| Kafka 消息 Key 字段列表。默认情况下该列表为空，即消息 Key 没有定义。列表格式为 'field1;field2'。|
| value.format | 必填 |	无 |	String | 序列化和反序列化 Kafka 消息 Value 部分的 Format。注意：该配置项和 'format' 二者必需其一。|
| value.fields-include | 可选	| ALL |	枚举类型：ALL, EXCEPT_KEY | 指定在解析 Kafka 消息 Value 部分时是否包含消息 Key 字段的策略。默认值为 'ALL' 表示所有字段都包含在消息 Value 中。EXCEPT_KEY 表示消息消息 Key 不包含在消息 Value 中。|
| scan.startup.mode | 可选 | group-offsets | String |	Kafka Consumer 的启动模式。有效值为：'earliest-offset'，'latest-offset'，'group-offsets'，'timestamp' 和 'specific-offsets'。|
| scan.startup.specific-offsets | 可选 | 无 | String | 在使用 'specific-offsets' 启动模式时为每个 partition 指定 offset，例如 'partition:0,offset:42;partition:1,offset:300'。|
| scan.startup.timestamp-millis | 可选 | 无 | Long | 在使用 'timestamp' 启动模式时指定启动的时间戳（单位毫秒）。|
| scan.topic-partition-discovery.interval | 可选 | 无 | Duration	| Consumer 周期自动发现动态创建的 Kafka topic 和 partition 的时间间隔。|
| sink.partitioner | 可选 | default | String | Flink partition 到 Kafka partition 的映射关系。default：使用 Kafka 默认的分区器对消息进行分区。fixed：每个 Flink partition 对应最多一个 Kafka partition。round-robin：Flink partition 按轮循（round-robin）的模式对应到 Kafka partition。只有当未指定消息 Key 时生效。|
| sink.semantic | 可选 | at-least-once | String	| 定义 Kafka Sink 的语义。有效值为 'at-least-once'，'exactly-once' 和 'none'。|
| sink.parallelism | 可选	| 无 | Integer |	定义 Kafka Sink 算子的并行度。默认情况下，并行度由框架定义为与上游串联的算子相同。|

### 5. Key 与 Value Format

Kafka 消息 Key 和 Value 部分都可以使用指定的 [Format](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/formats/overview/) 来序列化或反序列化。Key Format 用来序列化和反序列化 Kafka 消息的 Key 部分，Value Format 用来序列化和反序列化 Kafka 消息的 Value 部分。

#### 5.1 只有 Value Format

由于 Kafka 消息中 Key 是可选的，因此以下语句只配置 Value Format 来读取和写入记录。'format' 选项与 'value.format' 意义相同，两个配置项选择其中一个配置即可。所有的 Format 配置使用 Format 标识符作为前缀，例如，Json Foramt 配置均以 json 作为前缀：
```sql
CREATE TABLE kafka_value_source_table (
  uid STRING COMMENT '用户Id',
  wid STRING COMMENT '微博Id',
  tm STRING COMMENT '发微博时间'
) WITH (
  'connector' = 'kafka',
  'topic' = 'behavior',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'kafka-connector-value',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true',
  'json.fail-on-missing-field' = 'true'
);
```

#### 5.2 Key 与 Value Format

如下示例展示了如何配置一起使用 Key 和 Value Format。Format 配置使用 'key' 或 'value' 再加上 Format 标识符作为前缀。对于 Json Format，Key Format 均以 'key.json' 作为前缀，Value Format 均以 'value.json' 作为前缀：
```sql
CREATE TABLE kafka_key_value_source_table (
  uid STRING COMMENT '用户Id',
  wid STRING COMMENT '微博Id',
  tm STRING COMMENT '发微博时间'
) WITH (
  'connector' = 'kafka',
  'topic' = 'behavior',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'kafka-connector-key-value',
  'scan.startup.mode' = 'earliest-offset',
  -- Key Format
  'key.format' = 'json',
  'key.json.ignore-parse-errors' = 'true',
  'key.fields' = 'uid;wid',
  -- Value Format
  'value.format' = 'json',
  'value.json.fail-on-missing-field' = 'false',
  'value.fields-include' = 'EXCEPT_KEY'
);
```

假设 Kafka 消息 Key 数据如下所示：
```json
{
  "uid": "fa5aed172c062c61e196eac61038a03b",
  "wid": "7cce78a4ad39a91ec1f595bcc7fb5eba"
}
```
Kafka 消息 Value 数据如下所示：
```json
{
  "tm": "2015-08-01 14:06:31",
  "content": "卖水果老人"
}
```
在解析上述 Kafka 消息时，需要添加 'value.fields-include' = 'EXCEPT_KEY' 参数，指定 Key 相关字段不在 Value 中，否则 uid、wid 会被当成 Value 的一部分进行解析，从而导致解析不出数据。

假设 Kafka Key 数据格式如下：
```json
{
  "uid": "fa5aed172c062c61e196eac61038a03b",
  "wid": "7cce78a4ad39a91ec1f595bcc7fb5eba"
}
```
Kafka Value 数据格式如下：
```json
{
  "uid": "fa5aed172c062c61e196eac61038a03b",
  "wid": "7cce78a4ad39a91ec1f595bcc7fb5eba",
  "tm": "2015-08-01 14:06:31",
  "content": "卖水果老人"
}
```
在解析上述 Kafka 消息时，使用 'EXCEPT_KEY' 或者 'ALL' 均可以。

#### 5.1.3 重名字段

如果 Key Format 和 Value Format 中包含了相同名称的字段，那么 Connnector 无法根据 Schema 信息将这些列区分为 Key 字段和 Value 字段。'key.fields-prefix' 配置项可以在表结构中为 Key 字段指定一个唯一名称，并在配置 Key Format 的时候保留原名。如下示例展示了在 Key 和 Value Format 中同时包含 version 字段的情况：
```sql
CREATE TABLE kafka_same_name_source_table (
  `key_uid` STRING COMMENT 'kafka消息的key',
  `uid` STRING COMMENT '用户Id',
  `wid` STRING COMMENT '微博Id',
  `tm` STRING COMMENT '发微博时间'
) WITH (
  'connector' = 'kafka',
  'topic' = 'behavior',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'kafka-connector-same-name',
  'scan.startup.mode' = 'earliest-offset',
  -- Key Format
  'key.format' = 'json',
  'key.fields-prefix' = 'key_',
  'key.fields' = 'key_uid',
  'key.json.ignore-parse-errors' = 'true',
  -- Value Format
  'value.format' = 'json',
  'value.json.ignore-parse-errors' = 'true',
  'value.json.fail-on-missing-field' = 'false',
  'value.fields-include' = 'EXCEPT_KEY' --key 字段不在消息 Value 部分中
);
```

### 6. 特性

#### 6.1 Topic 和 Partition 自动发现

topic 和 topic-pattern 配置项决定了 Source 消费的 topic 或 topic 的匹配规则。topic 配置项可接受使用分号间隔的 topic 列表，例如 topic-1;topic-2。topic-pattern 配置项使用正则表达式来发现可以匹配的 topic。例如 topic-pattern 设置为 test-topic-[0-9]，那么在作业启动时，与这个正则表达式相匹配的 topic（以 test-topic- 开头，以一位数字结尾）都会被消费者订阅。

为了允许消费者在作业启动之后能够自动发现创建的 topic，需要将 scan.topic-partition-discovery.interval 配置为一个非负值。这能够使消费者发现与指定模式相匹配的新 topic 中的 partition。

> 注意 topic 列表和 topic 匹配规则只适用于 source。对于 sink 端，Flink 目前只支持单一 topic。

#### 6.2 起始消费位点

scan.startup.mode 配置项决定了 Kafka 消费者的启动模式。具体值如下所示：
- group-offsets：从指定的消费组提交到 Zookeeper 或者 Kafka Broker 的偏移量开始消费。
- earliest-offset：从最早的偏移量开始消费。
- latest-offset：从最末尾偏移量开始消费。
- timestamp：从用户为每个 partition 指定的时间戳开始消费。
- specific-offsets：从用户为每个 partition 指定的偏移量开始消费。

默认值为 group-offsets 表示从 Zookeeper 或者 Kafka Broker 中最近一次提交的偏移量开始消费。

如果使用了 timestamp，必须也要配置另外一个配置项 scan.startup.timestamp-millis，来指定一个从格林尼治标准时间 1970 年 1 月 1 日 00:00:00.000 开始计算的毫秒单位时间戳作为起始时间。如果使用了 specific-offsets，必须也要配置另外一个配置项 scan.startup.specific-offsets，来为每个 partition 指定起始偏移量，例如，选项值 partition:0,offset:42;partition:1,offset:300 表示 partition 0 从偏移量 42 开始，partition 1 从偏移量 300 开始。

#### 6.3 Sink 分区

配置项 sink.partitioner 指定了从 Flink 分区到 Kafka 分区的映射关系。默认情况下，Flink 使用 Kafka 默认分区器来对消息进行分区。默认分区器对没有消息 Key 的消息使用[粘性分区策略](https://www.confluent.io/blog/apache-kafka-producer-improvements-sticky-partitioner/)（sticky partition strategy） 进行分区，对含有消息 Key 的消息使用 murmur2 哈希算法计算分区。为了控制消息到分区的路由，也可以提供一个自定义的 Sink 分区器。'fixed' 分区器会将相同 Flink 分区中的消息写入同一个 Kafka 分区，从而减少网络连接的开销。

#### 6.4 一致性保证

默认情况下，如果在未启用 Checkpoint 模式下执行查询，Kafka Sink 会按照 At-Least-Once 语义保证将数据写入到 Kafka Topic 中。当 Flink Checkpoint 启用时，kafka Sink 可以提供 Exactly-Once 语义保证。除了启用 Flink Checkpoint，还可以通过选择不同的 sink.semantic 选项来选择三种不同的运行模式：
- None：不保证任何语义。输出的记录可能重复或者丢失。
- At-Least-Once (默认设置)：保证不会有记录丢失，但可能会重复。
- Exactly-Once：使用 Kafka 事务提供 Exactly-Once 语义。当使用事务向 Kafka 写入数据时，不要忘记设置所需的隔离级别（read_committed 或者 read_uncommitted，后者是默认值）。

#### 6.5 数据类型映射

Kafka 将消息 Key 和值存储为字节，因此 Kafka 没有 Schema 以及数据类型。Kafka 消息按照配置 Format 进行反序列化和序列化，例如 csv、json、avro。因此，数据类型映射由特定 Format 决定。

原文：[Apache Kafka SQL Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/kafka/)
