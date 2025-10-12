> Flink 版本：1.13.5

Upsert Kafka Connector 可以以 upsert 的方式从 Kafka Topic 读取数据或者将数据写入 Kafka Topic。

作为 Source，upsert-kafka Connector 可以产生变更日志流(Changelog)，其中每条数据记录代表一个更新或删除事件。更准确地说，数据记录中的值被解释为相同键最后一个值的 `UPDATE`(如果有相同键的话，如果相应的键还不存在，更新将被视为一个 `INSERT`）。如果用表来类比的话，变更日志流中的数据记录被解释为 `UPSERT` 又名 `INSERT/UPDATE`，因为具有相同键的已有行都将会被覆盖。此外，NULL 值以特殊方式解释：具有空值的记录表示一个 `DELETE`。

作为 Sink，upsert-kafka Connector 可以消费变更日志流。将 `INSERT/UPDATE_AFTER` 数据以普通的 Kafka 消息值写入 Kafka，将 `DELETE` 数据以具有 NULL 值的 Kafka 消息写入 Kafka(表示对应 key 的消息被删除)。Flink 会根据主键列的值对数据进行分区，从而保证主键上消息的有序性，因此同一键上的更新/删除消息会落入同一个分区。

## 1. 依赖

为了使用 Upsert Kafka Connector，使用 Maven 构建自动化工具需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-connector-kafka_2.11</artifactId>
  <version>1.13.6</version>
</dependency>
```
如果在 SQL Client 中使用如下添加 [flink-sql-connector-kafka_2.11-1.13.6](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka_2.11/1.13.6/flink-sql-connector-kafka_2.11-1.13.6.jar) JAR 包。

## 2. 元数据

有关所有可用元数据字段，请参阅[常规Kafka连接器](https://smartsi.blog.csdn.net/article/details/153140833)

## 3. Connector 参数

| 参数选项 | 是否必填项 | 默认值 | 数据类型 | 说明 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| connector | 必填 | 无 | String | 指定使用的 Connector 名称，对于 Upsert Kafka 为 'upsert-kafka' |
| topic | Sink 必填	| 无 | String | 读取或者写入的 Kafka Topic 名称 |
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

> 不支持 topic-pattern ？

## 4. 特性

### 4.2 主键约束

Upsert Kafka 总是以 Upsert 的方式工作，因此需要在 DDL 中定义主键。假设具有相同键的记录应该在同一分区中排序，那么变更日志源上的主键语义意味着物化的变更日志在主键上是唯一的。主键定义还将控制哪些字段应该在 Kafka 的键中结束。

### 4.3 一致性保证

默认情况下，如果在启用检查点的情况下执行查询，Upsert Kafka Sink 将数据写入到 Kafka Topic 时提供至少一次语义保证。这意味着，Flink 可以将同一个键的重复记录写入 Kafka Topic 中。但是，由于 Connector 以 upsert 模式工作，同一键上的最后一条记录将在作为 Source 读入时生效。因此，upsert-kafka Connector 实现了像 HBase Sink 一样的幂等写入。

### 4.4 Source 每个分区 Watermark

Flink支持为 Upsert Kafka 输出每个分区的 Watermark。Watermark 是在 Kafka 消费者内部生成的。每个分区的 Watermark 合并的方式与在流 Shuffle 期间合并 Watermark 的方式相同。Source 的输出 Watermark 由其读取的分区中的最小 Watermark 决定。如果 Topic 中的某些分区空闲，则 Watermark 生成器不会前进。您可以通过设置 `table.exec.source. idle-timeout` 参数来缓解这个问题。

## 5. 实践

```sql
CREATE TABLE shop_sales_num (
  `category` STRING COMMENT '分类',
  `num` BIGINT COMMENT '订单数量',
  `price` BIGINT COMMENT '订单金额',
  PRIMARY KEY(`category`) NOT ENFORCED
) WITH (
  'connector' = 'upsert-kafka',
  'topic' = 'shop-sales-num',
  'properties.bootstrap.servers' = 'localhost:9092',
  'key.format' = 'json',
  'value.format'='json'
)


INSERT INTO shop_sales_num
SELECT category, COUNT(*) AS num, SUM(price) AS price
FROM shop_sales
GROUP BY category
```




原文: [Upsert Kafka SQL Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/upsert-kafka/)
