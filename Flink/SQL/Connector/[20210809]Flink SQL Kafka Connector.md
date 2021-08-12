---
layout: post
author: smartsi
title: Flink SQL Kafka Connector
date: 2021-08-08 15:47:21
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-kafka-connector
---

> Flink 版本：1.13

Kafka Connector 提供了从 Kafka topic 中消费和写入数据的能力。

### 1. 依赖

无论是使用构建自动化工具（例如 Maven 或 SBT）的项目还是带有 SQL JAR 包的 SQL 客户端，如果想使用 Kafka Connector，都需要引入如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-connector-kafka_2.11</artifactId>
  <version>1.13.0</version>
</dependency>
```
如果是使用的 SQL 客户端，需要[下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka_2.11/1.13.0/flink-sql-connector-kafka_2.11-1.13.0.jar)对应的 Jar 包放在 flink 安装目录的 lib 文件夹下。

### 2. 创建Kafka表

下面的示例显示了如何创建 Kafka 表：
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

### 3. 可用的元数据

如下 Connector 元数据可以在表定义中通过元数据列来获取：

| Key | 数据类型 | 说明 | R/W |
| :------------- | :------------- | :------------- | :------------- |
| topic | STRING NOT NULL | Kafka 记录的 Topic 名称 | R |
| partition	| INT NOT NULL | Kafka 记录的 Partition ID | R |
| headers	| MAP NOT NULL | 二进制 Map 类型的 Kafka 记录头（Header）| R/W |
| leader-epoch | INT NULL | Kafka 记录的 Leader epoch（如果可用）|	R |
| offset | BIGINT NOT NULL | Kafka 记录在 Partition 中的偏移量 |	R |
| timestamp | TIMESTAMP_LTZ(3) NOT NULL | Kafka 记录的时间戳 | R/W |
| timestamp-type | STRING NOT NULL | Kafka 记录的时间戳类型。可能的类型有 NoTimestampType、CreateTime（会在写入元数据时设置）以及 LogAppendTime | R |

> R/W 列定义了一个元数据是可读（R）还是可写（W）。只读列必须声明为 VIRTUAL 以在 INSERT INTO 操作中排除它们。

以下扩展的 CREATE TABLE 示例展示了使用这些元数据字段的语法：
```sql

```

Connector 可以读出消息格式的元数据。格式元数据的配置键以 'value.' 作为前缀。以下示例展示了如何获取 Kafka 和 Debezium 的元数据字段：
```sql
CREATE TABLE KafkaTable (
  `event_time` TIMESTAMP(3) METADATA FROM 'value.source.timestamp' VIRTUAL,  -- from Debezium format
  `origin_table` STRING METADATA FROM 'value.source.table' VIRTUAL, -- from Debezium format
  `partition_id` BIGINT METADATA FROM 'partition' VIRTUAL,  -- from Kafka connector
  `offset` BIGINT METADATA VIRTUAL,  -- from Kafka connector
  `user_id` BIGINT,
  `item_id` BIGINT,
  `behavior` STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'user_behavior',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'testGroup',
  'scan.startup.mode' = 'earliest-offset',
  'value.format' = 'debezium-json'
);
```

### 4. Connector 参数

| 参数选项 | 是否必填项 | 默认值：无 | 数据类型 | 说明 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| connector | 必填 | 无 | String | 指定使用 Connector，对于 Kafka 使用 'kafka' |
| topic | 对于 Sink 必填	| 无 | String | 当表用作 Source 时读取数据的 topic 名。也支持用分号间隔的 topic 列表，如 'topic-1;topic-2'。注意，对 Source 表而言，'topic' 和 'topic-pattern' 两个选项只能使用其中一个；当表被用作 Sink 时数据写入的 topic 名。注意 Sink 表不支持分号间隔的 topic 列表 |
| topic-pattern | 可选 | 无 | String | 匹配读取 topic 名称的正则表达式。在作业开始运行时，所有匹配该正则表达式的 topic 都将被 Kafka consumer 订阅。注意，对 source 表而言，'topic' 和 'topic-pattern' 两个选项只能使用其中一个 |

### 5. 特性

#### 5.1 Key 与 Value 格式

Kafka 记录的 Key 和 Value 部分都可以使用指定[格式](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/formats/overview/)来序列化或反序列化成二进制数据。

##### 5.1.1 Value 格式

由于 Kafka 记录中 Key 是可选的，因此以下语句只使用配置的 Value 格式读取和写入记录，但没有使用 Key 格式。'format' 选项与 'value.format' 意义相同。所有的格式配置使用格式识别符作为前缀：
```sql
CREATE TABLE KafkaTable (
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp',
  `user_id` BIGINT,
  `item_id` BIGINT,
  `behavior` STRING
) WITH (
  'connector' = 'kafka',
  ...

  'format' = 'json',
  'json.ignore-parse-errors' = 'true'
)
```
Value 格式将配置为如下的数据类型：
```
ROW<`user_id` BIGINT, `item_id` BIGINT, `behavior` STRING>
```

##### 5.1.2 Key 与 Value 格式

如下示例展示了如何配置和使用 Key 和 Value 格式。格式配置使用 'key' 或 'value' 格式识别符作为前缀：
```sql
CREATE TABLE KafkaTable (
  `ts` TIMESTAMP(3) METADATA FROM 'timestamp',
  `user_id` BIGINT,
  `item_id` BIGINT,
  `behavior` STRING
) WITH (
  'connector' = 'kafka',
  ...

  'key.format' = 'json',
  'key.json.ignore-parse-errors' = 'true',
  'key.fields' = 'user_id;item_id',

  'value.format' = 'json',
  'value.json.fail-on-missing-field' = 'false',
  'value.fields-include' = 'ALL'
)
```
Key 格式中使用 'key.fields' 参数选项指定与 Key 相同顺序的字段列表（使用 ';' 分隔）。因此将配置为如下的数据类型：
```
ROW<`user_id` BIGINT, `item_id` BIGINT>
```
由于 Value 格式配置了 'value.fields-include' = 'ALL'，所以 Key 字段也会出现在 Value 格式的数据类型中：
```
ROW<`user_id` BIGINT, `item_id` BIGINT, `behavior` STRING>
```
##### 5.1.3 重名的格式字段

如果 Key 格式和 Value 格式中包含了相同名称的字段，那么 Connnector 无法根据 Schema 信息将这些列区分为 Key 字段和 Value 字段。'key.fields-prefix' 配置项可以在表结构中为 Key 字段指定一个唯一名称，并在配置 Key 格式的时候保留原名。如下示例展示了在 Key 和 Value 格式中同时包含 version 字段的情况：
```sql
CREATE TABLE KafkaTable (
  `k_version` INT,
  `k_user_id` BIGINT,
  `k_item_id` BIGINT,
  `version` INT,
  `behavior` STRING
) WITH (
  'connector' = 'kafka',
  ...

  'key.format' = 'json',
  'key.fields-prefix' = 'k_',
  'key.fields' = 'k_version;k_user_id;k_item_id',

  'value.format' = 'json',
  'value.fields-include' = 'EXCEPT_KEY'
)
```
Value 格式必须配置为 'EXCEPT_KEY' 模式。格式将被配置为如下的数据类型：
```
Key 格式：
ROW<`version` INT, `user_id` BIGINT, `item_id` BIGINT>

Value 格式：
ROW<`version` INT, `behavior` STRING>
```

#### 5.2 Topic 和 Partition 自动发现

topic 和 topic-pattern 配置项决定了 Source 消费的 topic 或 topic 的匹配规则。topic 配置项可接受使用分号间隔的 topic 列表，例如 topic-1;topic-2。topic-pattern 配置项使用正则表达式来发现可以匹配的 topic。例如 topic-pattern 设置为 test-topic-[0-9]，那么在作业启动时，与这个正则表达式相匹配的 topic（以 test-topic- 开头，以一位数字结尾）都会被消费者订阅。

为了允许消费者在作业启动之后能够自动发现创建的 topic，需要将 scan.topic-partition-discovery.interval 配置为一个非负值。这能够使消费者发现与指定模式相匹配的新 topic 中的 partition。

> 注意 topic 列表和 topic 匹配规则只适用于 source。对于 sink 端，Flink 目前只支持单一 topic。

#### 5.3 起始消费位点

scan.startup.mode 配置项决定了 Kafka 消费者的启动模式。具体值如下所示：
- group-offsets：从指定的消费组提交到 Zookeeper 或者 Kafka Broker 的偏移量开始消费。
- earliest-offset：从最早的偏移量开始消费。
- latest-offset：从最末尾偏移量开始消费。
- timestamp：从用户为每个 partition 指定的时间戳开始消费。
- specific-offsets：从用户为每个 partition 指定的偏移量开始消费。

默认值为 group-offsets 表示从 Zookeeper 或者 Kafka Broker 中最近一次提交的偏移量开始消费。

如果使用了 timestamp，必须也要配置另外一个配置项 scan.startup.timestamp-millis，来指定一个从格林尼治标准时间 1970 年 1 月 1 日 00:00:00.000 开始计算的毫秒单位时间戳作为起始时间。如果使用了 specific-offsets，必须也要配置另外一个配置项 scan.startup.specific-offsets，来为每个 partition 指定起始偏移量，例如，选项值 partition:0,offset:42;partition:1,offset:300 表示 partition 0 从偏移量 42 开始，partition 1 从偏移量 300 开始。




原文：[Apache Kafka SQL Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/kafka/)
