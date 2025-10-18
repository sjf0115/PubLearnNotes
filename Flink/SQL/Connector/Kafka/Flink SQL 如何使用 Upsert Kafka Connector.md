> Flink 版本：1.13.6

Upsert Kafka Connector 可以以 upsert 的方式从 Kafka Topic 读取数据或者将数据写入 Kafka Topic。

作为源表 Source，Upsert-kafka Connector 可以将 Kafka 中存储的数据转换为变更日志流(Changelog)，其中每条数据记录代表一个更新或删除事件。更准确地说，数据记录中的值被解释为同一 Key 最后一个值的 `UPDATE`(如果有相同 Key 的话，并且相应的 Key 还不存在，更新将被视为一个 `INSERT`）。如果用表来类比的话，变更日志流中的数据记录被解释为 `UPSERT` 也称为 `INSERT/UPDATE`，因为具有相同 Key 的已有行都将会被覆盖。此外，NULL 值以特殊方式解释：具有空值的记录表示一个 `DELETE`。

作为结果表 Sink，Upsert-kafka Connector 可以消费上游计算逻辑产生的变更日志流。将 `INSERT/UPDATE_AFTER` 数据以普通的 Kafka 消息值写入 Kafka，将 `DELETE` 数据以具有 NULL 值的 Kafka 消息写入 Kafka(表示对应 key 的消息被删除)。Flink 会根据主键列的值对数据进行分区，从而保证主键上消息的有序性，因此同一 Key 上的更新/删除消息会落入同一个分区。

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
| properties.bootstrap.servers | 必填 | 无 | String | 逗号分隔的 Kafka Broker 列表 |
| properties.* | 可选	| 无 |	String | 可以设置和传递的任意 Kafka 配置项。后缀名必须与 [Kafka 文档](https://kafka.apache.org/documentation/#configuration)中的相匹配。Flink 会删除 "properties." 前缀并将变换后的配置键和值传入底层的 Kafka 客户端。例如，你可以通过 'properties.allow.auto.create.topics' = 'false' 来禁用 topic 的自动创建。但是某些配置项不支持进行配置，因为 Flink 会覆盖这些配置，例如 'key.deserializer' 和 'value.deserializer'。|
| key.format | 必填	| 无 |	String | 读取或写入 Kafka 消息 key 部分时使用的格式。参数取值有 csv、json、avro 等。 |
| key.fields-prefix | 可选	|  | String	| 为所有 Kafka 消息 key 部分指定自定义前缀，以避免与消息 value 部分格式字段重名。默认情况下，前缀为空。如果定义了自定义前缀，则表 Schema 和 'key.fields' 将使用带前缀的名称。该配置项仅用于源表和结果表的列名区分，解析和生成 Kafka 消息 key 部分时，该前缀会被移除。请注意，此选项要求 'value.fields-include' 必须设置为 'EXCEPT_KEY' 。|
| value.format | 必填 |	无 |	String | 读取或写入 Kafka 消息 value 部分时使用的格式。|
| value.fields-include | 可选	| ALL |	枚举类型：ALL, EXCEPT_KEY | 指定在解析 Kafka 消息 Value 部分时是否包含消息 Key 字段的策略。默认值为 'ALL' 表示所有字段都包含在消息 Value 中。EXCEPT_KEY 表示消息消息 Key 不包含在消息 Value 中。|
| sink.parallelism | 可选	| 无 | Integer |	定义 Upsert-kafka 算子的并行度。默认情况下，并行度由框架定义为与上游串联的算子相同。该参数只能用于结果表。|
| sink.buffer-flush.max-rows | 可选 | 0（未开启） | Integer | 缓存刷新前，最多能缓存多少条记录。当结果表收到很多个同一 key 上的更新时，缓存将保留同一 key 的最后一条记录，因此结果表缓存能帮助减少发往 Kafka topic 的数据量，以及避免发送潜在的 tombstone 消息。可以设置为 '0' 来禁用此功能。默认情况下，此功能被禁用。如果要开启结果表缓存，需要同时设置 sink.buffer-flush.max-rows 和 sink.buffer-flush.interval 两个选项为大于零的值。|
| sink.buffer-flush.interval | 可选 | 0（未开启） | Duration | 缓存刷新的间隔时间。单位可以为毫秒（ms）、秒（s）、分钟（min）或小时（h）。例如'sink.buffer-flush.interval'='1 s'。当结果表收到很多同key上的更新时，缓存将保留同key的最后一条记录，因此结果表缓存能帮助减少发往 Kafka topic 的数据量，以及避免发送潜在的 tombstone 消息。如果要开启结果表缓存，需要同时设置 sink.buffer-flush.max-rows 和 sink.buffer-flush.interval 两个选项为大于零的值。|

> 请注意，upsert-kafka 目前支持的参数如上所示，与常规 kafka connector 支持有一些区别。upsert-kafka 并不支持常规 kafka 的一些参数，例如 `scan.startup.mode`

## 4. 特性

### 4.2 主键约束

Upsert Kafka 总是以 Upsert 的方式工作，因此需要在 DDL 中定义主键。假设具有相同键的记录应该在同一分区中排序，那么变更日志源上的主键语义意味着物化的变更日志在主键上是唯一的。主键定义还将控制哪些字段应该在 Kafka 的键中结束。

### 4.3 一致性保证

默认情况下，如果在启用检查点的情况下执行查询，Upsert Kafka Sink 将数据写入到 Kafka Topic 时提供至少一次语义保证。这意味着，Flink 可以将同一个键的重复记录写入 Kafka Topic 中。但是，由于 Connector 以 upsert 模式工作，同一键上的最后一条记录将在作为 Source 读入时生效。因此，upsert-kafka Connector 实现了像 HBase Sink 一样的幂等写入。

### 4.4 Source 每个分区 Watermark

Flink支持为 Upsert Kafka 输出每个分区的 Watermark。Watermark 是在 Kafka 消费者内部生成的。每个分区的 Watermark 合并的方式与在流 Shuffle 期间合并 Watermark 的方式相同。Source 的输出 Watermark 由其读取的分区中的最小 Watermark 决定。如果 Topic 中的某些分区空闲，则 Watermark 生成器不会前进。您可以通过设置 `table.exec.source. idle-timeout` 参数来缓解这个问题。

## 5. 示例

### 5.1 Upsert-kafka Sink

在这个示例中将统计每个商品类目下的订单数量和订单金额写入 Upsert Kafka 结果表 `shop_sales_num` 中：
```sql
INSERT INTO shop_sales_num
SELECT category, COUNT(*) AS num, SUM(price) AS price
FROM shop_sales
GROUP BY category
```
创建 Upsert Kafka 结果表如下所示:
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
```

代码示例如下：
```java
// 1. Source
DataStreamSource<ShopSales> sourceStream = env.fromElements(
        new ShopSales(1001, "图书", 40, 1665360300000L), // 2022-10-10 08:05:00
        new ShopSales(2001, "生鲜", 80, 1665360360000L), // 2022-10-10 08:06:00
        new ShopSales(1002, "图书", 30, 1665360420000L), // 2022-10-10 08:07:00
        new ShopSales(2002, "生鲜", 80, 1665360480000L), // 2022-10-10 08:08:00
        new ShopSales(2003, "生鲜", 150, 1665360540000L), // 2022-10-10 08:09:00
        new ShopSales(1003, "图书", 100, 1665360290000L), // 2022-10-10 08:04:50  迟到
        new ShopSales(2004, "生鲜", 70, 1665360660000L), // 2022-10-10 08:11:00
        new ShopSales(2005, "生鲜", 20, 1665360720000L), // 2022-10-10 08:12:00
        new ShopSales(1004, "图书", 10, 1665360780000L), // 2022-10-10 08:13:00
        new ShopSales(2006, "生鲜", 120, 1665360840000L), // 2022-10-10 08:14:00
        new ShopSales(1005, "图书", 20, 1665360900000L), // 2022-10-10 08:15:00
        new ShopSales(1006, "图书", 60, 1665360896000L), // 2022-10-10 08:14:56  迟到
        new ShopSales(1007, "图书", 90, 1665361080000L) // 2022-10-10 08:18:00
);
// 设置 Watermark
DataStream<ShopSales> shopSalesStream = sourceStream.assignTimestampsAndWatermarks(WatermarkStrategy
        // 定义 Watermark 最大容忍5秒的延迟
        .<ShopSales>forBoundedOutOfOrderness(Duration.ofSeconds(5))
        // 提取时间戳
        .withTimestampAssigner(new SerializableTimestampAssigner<ShopSales>() {
            @Override
            public long extractTimestamp(ShopSales sale, long recordTimestamp) {
                return sale.getTimestamp();
            }
        }));

// 注册表
tEnv.createTemporaryView("shop_sales", shopSalesStream,
        $("productId").as("product_id"), $("category"),  $("price"),  $("timestamp"), $("ts_ltz").rowtime()
);

// 2. Upsert-Kafka Sink 表
String sourceSql = "CREATE TABLE shop_sales_num (\n" +
        "  `category` STRING COMMENT '分类',\n" +
        "  `num` BIGINT COMMENT '订单数量',\n" +
        "  `price` BIGINT COMMENT '订单金额',\n" +
        "   PRIMARY KEY(`category`) NOT ENFORCED\n" +
        ") WITH (\n" +
        "  'connector' = 'upsert-kafka',\n" +
        "  'topic' = 'shop-sales-num',\n" +
        "  'properties.bootstrap.servers' = 'localhost:9092',\n" +
        "  'key.format' = 'json',\n" +
        "  'value.format'='json'\n" +
        ")";
tEnv.executeSql(sourceSql);

// 执行计算 计算订单数量和金额
tEnv.executeSql("INSERT INTO shop_sales_num\n" +
        "SELECT category, COUNT(*) AS num, SUM(price) AS price\n" +
        "FROM shop_sales\n" +
        "GROUP BY category");
```
> 完整代码请查阅：[UpsertKafkaSinkExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/sql/connector/kafka/UpsertKafkaSinkExample.java)

### 5.2 Upsert-kafka Source

上述示例中统计每个商品类目下的订单数量和订单金额写入 Upsert Kafka 结果表中。现在再从结果表中读出查阅一下 Changelog 数据是否符合预期。

创建 Upsert Kafka 源表用于读取上述示例中写入 Changelog 数据:
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
```
在这示例中简单的读取 Upsert Kafka 源表打印到控制台，示例代码如下所示：
```java
// Upsert-Kafka Source 表
String sourceSql = "CREATE TABLE shop_sales_num (\n" +
        "  `category` STRING COMMENT '分类',\n" +
        "  `num` BIGINT COMMENT '订单数量',\n" +
        "  `price` BIGINT COMMENT '订单金额',\n" +
        "   PRIMARY KEY(`category`) NOT ENFORCED\n" +
        ") WITH (\n" +
        "  'connector' = 'upsert-kafka',\n" +
        "  'topic' = 'shop-sales-num',\n" +
        "  'properties.bootstrap.servers' = 'localhost:9092',\n" +
        "  'key.format' = 'json',\n" +
        "  'value.format'='json'\n" +
        ")";
tEnv.executeSql(sourceSql);

// 创建 Print Sink 表
String sinkSql = "CREATE TABLE print_sink_table (\n" +
        "  `category` STRING COMMENT '分类',\n" +
        "  `num` BIGINT COMMENT '订单数量',\n" +
        "  `price` BIGINT COMMENT '订单金额'\n" +
        ") WITH (\n" +
        "  'connector' = 'print'\n" +
        ")";
tEnv.executeSql(sinkSql);

// 执行计算并输出
String sql = "INSERT INTO print_sink_table\n" +
        "SELECT `category`, `num`, `price`\n" +
        "FROM shop_sales_num";
tEnv.executeSql(sql);
```
> 完整代码请查阅： [UpsertKafkaSourceExample](https://github.com/sjf0115/flink-example/blob/main/flink-example-1.13/src/main/java/com/flink/example/sql/connector/kafka/UpsertKafkaSourceExample.java)

运行上述示例输出结果如下所示：
```
+I[图书, 1, 40]
+I[生鲜, 1, 80]
-U[图书, 1, 40]
+U[图书, 2, 70]
-U[生鲜, 1, 80]
+U[生鲜, 2, 160]
-U[生鲜, 2, 160]
+U[生鲜, 3, 310]
-U[图书, 2, 70]
+U[图书, 3, 170]
-U[生鲜, 3, 310]
+U[生鲜, 4, 380]
-U[生鲜, 4, 380]
+U[生鲜, 5, 400]
-U[图书, 3, 170]
+U[图书, 4, 180]
-U[生鲜, 5, 400]
+U[生鲜, 6, 520]
-U[图书, 4, 180]
+U[图书, 5, 200]
-U[图书, 5, 200]
+U[图书, 6, 260]
-U[图书, 6, 260]
+U[图书, 7, 350]
```

参考: [Upsert Kafka SQL Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/upsert-kafka/)
