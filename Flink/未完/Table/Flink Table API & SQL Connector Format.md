
Flink 提供了一组 Table Format，可以与 Table Connector 一起使用。Table Format 是一种存储格式，定义了二进制数据如何与 Table 列 进行映射的。

Flink 支持以下格式：

| Formats     | 支持的 Connectors     |
| :------------- | :------------- |
| CSV   | Apache Kafka, Upsert Kafka, Amazon Kinesis Data Streams, Filesystem |
| JSON	| Apache Kafka, Upsert Kafka, Amazon Kinesis Data Streams, Filesystem, Elasticsearch |
| Apache Avro	| Apache Kafka, Upsert Kafka, Amazon Kinesis Data Streams, Filesystem |
| Confluent Avro	| Apache Kafka, Upsert Kafka |
| Debezium CDC	| Apache Kafka, Filesystem |
| Canal CDC	| Apache Kafka, Filesystem |
| Maxwell CDC	| Apache Kafka, Filesystem |
| Apache Parquet	| Filesystem |
| Apache ORC	| Filesystem |
| Raw	| Apache Kafka, Upsert Kafka, Amazon Kinesis Data Streams, Filesystem |

## 1. CSV

CSV Format 允许基于 CSV Schema 读写 CSV 数据。目前，CSV Schema 从 Table Schema 派生而来。

### 1.1 依赖

使用 CSV Format 需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-csv</artifactId>
  <version>1.13.5</version>
</dependency>
```

### 1.2 使用

如下是一个使用 Kafka Connector 以及 CSV Format 创建表的示例：
```sql
CREATE TABLE user_behavior (
  user_id BIGINT,
  item_id BIGINT,
  category_id BIGINT,
  behavior STRING,
  ts TIMESTAMP(3)
) WITH (
 'connector' = 'kafka',
 'topic' = 'user_behavior',
 'properties.bootstrap.servers' = 'localhost:9092',
 'properties.group.id' = 'testGroup',
 'format' = 'csv',
 'csv.ignore-parse-errors' = 'true',
 'csv.allow-comments' = 'true'
)
```

### 1.3 参数说明

| 参数     | 是否必选     | 默认值	| 类型	| 描述 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| format              | 必选 | (none) | String | 格式 Format 名称 'csv'。|
| csv.field-delimiter | 可选 | `,` | String | 字段分隔符，必须为单字符。你可以使用反斜杠字符指定一些特殊字符，例如 '\t' 代表制表符。 你也可以通过 unicode 编码在纯 SQL 文本中指定一些特殊字符，例如 'csv.field-delimiter' = U&'\0001' 代表 0x01 字符。|
| csv.array-element-delimiter | 可选 | `;` | String	| 分隔数组和行元素的字符串。|
| csv.allow-comments | 可选 | false | Boolean | 是否忽略以 '#' 开头的注释行，默认不忽略。如果忽略，需要确保 csv.ignore-parse-errors 开启从而允许空行。|
| csv.ignore-parse-errors | 可选 | false | Boolean | 是否跳过(忽略)解析异常的字段或者行(而不是抛出错误)，默认为 false，即抛出异常。如果忽略字段的解析异常，该字段值会设置为null。|
| csv.disable-quote-character | 可选 | false | Boolean | 是否禁用包裹字段值引号字符，默认是 false。如果禁用，csv.quote-character 也不能设置。|
| csv.quote-character | 可选 | `"` | String | 用于包裹字段值的引号字符，默认为`"`。|
| csv.escape-character | 可选 | (none) | String | 转义字符(默认关闭). |
| csv.null-literal | 可选 | (none) | String | 是否将 "null" 字符串转化为 null 值。|

### 1.4 数据类型映射

目前 CSV 的 schema 都是从 table schema 推断而来的。显式地定义 CSV schema 暂不支持。 Flink 的 CSV Format 数据使用 jackson databind API 去解析 CSV 字符串。

下面的表格列出了flink数据和CSV数据的对应关系。

![](1)

## 2. JSON

JSON Format 允许基于 JSON Schema 读写 JSON 数据。目前，JSON Schema 是从 Table Schema 派生而来。

### 2.1 依赖

使用 JSON Format 需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-json</artifactId>
  <version>1.13.5</version>
</dependency>
```

### 2.2 使用

如下是一个使用 Kafka Connector 以及 JSON Format 创建表的示例：
```sql
CREATE TABLE user_behavior (
  user_id BIGINT,
  item_id BIGINT,
  category_id BIGINT,
  behavior STRING,
  ts TIMESTAMP(3)
) WITH (
 'connector' = 'kafka',
 'topic' = 'user_behavior',
 'properties.bootstrap.servers' = 'localhost:9092',
 'properties.group.id' = 'testGroup',
 'format' = 'json',
 'json.fail-on-missing-field' = 'false',
 'json.ignore-parse-errors' = 'true'
)
```

### 2.3 参数说明

| 参数     | 是否必选     | 默认值	| 类型	| 描述 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| format | 必选	| (none) | String | 格式 Format 名称 'json'。|
| json.fail-on-missing-field | 可选	| false	| Boolean | 当解析字段缺失时，是否跳过当前字段或者行，默认为 false，即不逃过而是抛出异常。|
| json.ignore-parse-errors | 可选 | false | Boolean | 是否忽略解析异常的字段或者行，默认为 false，即不跳过而是抛出异常。如果忽略，该字段值会设置为null。|
| json.timestamp-format.standard | 可选	| 'SQL'	| String | 为 TIMESTAMP 和 TIMESTAMP_LTZ 类型指定输入和输出格式。当前支持 'SQL' 和 'ISO-8601' 格式。<br>'SQL' 格式：将 TIMESTAMP 值解析为 "yyyy-MM-dd HH:mm:ss.s{precision}" 格式，例如 "2020-12-30 12:13:14.123"；将 TIMESTAMP_LTZ 值解析为 "yyyy-MM-dd HH:mm:ss.s{precision}'Z'" 格式，例如 "2020-12-30 12:13:14.123Z"。<br>'ISO-8601' 格式：将 TIMESTAMP 值解析为 "yyyy-MM-ddTHH:mm:ss.s{precision}" 格式，例如 "2020-12-30T12:13:14.123"；将 TIMESTAMP_LTZ 值解析为 "yyyy-MM-ddTHH:mm:ss.s{precision}'Z'" 格式，例如 "2020-12-30T12:13:14.123Z"。|
| json.map-null-key.mode | 可选 | 'FAIL' | String | 指定 Map 中 key 值为空的处理模式。当前支持 'FAIL'、'DROP' 以及 'LITERAL' 模式:<br>'FAIL' 模式：直接抛出异常；<br>'DROP' 模式：丢弃 Map 中 key 值为空的数据；<br>'LITERAL' 模式：使用 json.map-null-key.literal 参数指定的字符串常量来替换 Map 中的空 key 值。|
| json.map-null-key.literal | 可选 | 'null'	| String | 当 json.map-null-key.mode 为 LITERAL 模式时，指定字符串常量替换 Map 中的空 key 值。|
| json.encode.decimal-as-plain-number | 可选 | false | Boolean | 对于 DECIMAL 类型使用纯数字，而不是使用科学计数法表示。例：0.000000027 默认会表示为 2.7E-8。当此选项设为 true 时，则会表示为 0.000000027。|

### 2.4 数据类型映射

当前，JSON Schema 会自动从 Table Schema 推导得到。不支持显式地定义 JSON Schema。在 Flink 中，JSON Format 使用 jackson databind API 去解析和生成 JSON。

下表列出了 Flink 中的数据类型与 JSON 中的数据类型的映射关系。

![](2)

## 3. Avro

Apache Avro Format 允许基于 Avro Schema 读写 Avro 数据。目前，Avro Schema 从 Table Scheam 派生而来。

### 3.1 依赖

使用 Apache Avro Format 需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-avro</artifactId>
  <version>1.13.5</version>
</dependency>
```

### 3.2 使用

如下是一个使用 Kafka Connector 以及 Apache Avro Format 创建表的示例：
```sql
CREATE TABLE user_behavior (
  user_id BIGINT,
  item_id BIGINT,
  category_id BIGINT,
  behavior STRING,
  ts TIMESTAMP(3)
) WITH (
 'connector' = 'kafka',
 'topic' = 'user_behavior',
 'properties.bootstrap.servers' = 'localhost:9092',
 'properties.group.id' = 'testGroup',
 'format' = 'avro'
)
```

### 3.3 参数说明

| 参数     | 是否必选     | 默认值	| 类型	| 描述 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| format | 必选	| (none) | String | 格式 Format 名称 'avro'。|
| avro.codec | 可选	| (none) | String	| avro 压缩编解码器，仅能用于 Filesystem Connector。默认不压缩。目前支持：deflate、snappy、bzip2、xz。|

### 3.4 数据类型映射

当前，Apache Avro Schema 会自动从 Table Schema 推导得到。不支持显式地定义 Apache Avro Schema。因此，下表列出了从 Flink 类型到 Avro 类型的类型映射：

![](3)

除了上面列出的类型，Flink 还支持读写 nullable 的类型。Flink 将 nullable 类型映射到 Avro union(something, null)，其中 something 是从 Flink 类型转换的 Avro 类型。

## 4. Parquet

Apache Parquet Format 允许基于 Parquet Schema 读写 Parquet 数据。目前，Parquet Schema 从 Table Scheam 派生而来。

### 4.1 依赖

使用 Apache Parquet Format 需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-parquet_2.11</artifactId>
  <version>1.13.5</version>
</dependency>
```

### 4.2 使用

如下是一个使用 Filesystem Connector 以及 Apache Parquet Format 创建表的示例：
```sql
CREATE TABLE user_behavior (
  user_id BIGINT,
  item_id BIGINT,
  category_id BIGINT,
  behavior STRING,
  ts TIMESTAMP(3),
  dt STRING
) PARTITIONED BY (dt) WITH (
 'connector' = 'filesystem',
 'path' = '/tmp/user_behavior',
 'format' = 'parquet'
)
```

### 4.3 参数说明

| 参数     | 是否必选     | 默认值	| 类型	| 描述 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| format | 必选	| (none) | String | 格式 Format 名称 'parquet'。|
| parquet.utc-timezone | 可选	| false	| Boolean	| 使用 UTC 时区或本地时区在纪元时间和 LocalDateTime 之间进行转换。Hive 0.x/1.x/2.x 使用本地时区，但 Hive 3.x 使用 UTC 时区。|

Parquet Format 也支持 [ParquetOutputFormat](https://www.javadoc.io/doc/org.apache.parquet/parquet-hadoop/1.10.0/org/apache/parquet/hadoop/ParquetOutputFormat.html) 的配置。例如, 可以配置 parquet.compression=GZIP 来开启 gzip 压缩。

### 4.4 数据类型映射

目前，Parquet Format 类型映射与 Apache Hive 兼容，但与 Apache Spark 有所不同：
- Timestamp：无论精度是多少，timestamp 类型都会映射为 int96。
- Decimal：根据精度，decimal 类型映射为固定长度字节数组。

下表列举了 Flink 中的数据类型与 Parquet 中的数据类型的映射关系。

![](4)

> 暂不支持复合数据类型（Array、Map 与 Row）。

## 5. Orc

Apache Orc Format 允许基于 Orc Schema 读写 Orc 数据。

### 5.1 依赖

使用 Apache Orc Format 需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-orc_2.11</artifactId>
  <version>1.13.5</version>
</dependency>
```

### 5.2 使用

如下是一个使用 Filesystem Connector 以及 Apache Orc Format 创建表的示例：
```sql
CREATE TABLE user_behavior (
  user_id BIGINT,
  item_id BIGINT,
  category_id BIGINT,
  behavior STRING,
  ts TIMESTAMP(3),
  dt STRING
) PARTITIONED BY (dt) WITH (
 'connector' = 'filesystem',
 'path' = '/tmp/user_behavior',
 'format' = 'orc'
)
```

### 5.3 参数说明

| 参数     | 是否必选     | 默认值	| 类型	| 描述 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| format | 必选	| (none) | String | 格式 Format 名称 'orc'。|

Orc 格式也支持表属性。举个例子，你可以设置 orc.compress=SNAPPY 来允许spappy压缩。

### 5.4 数据类型映射

Orc 格式类型的映射和 Apache Hive 是兼容的。下面的表格列出了 Flink 类型的数据和 Orc 类型的数据的映射关系。

![](5)

> 暂不支持复合数据类型（Array、Map 与 Row）。

## 6. Raw

Raw Format 允许读写以单列存储的原始（基于字节）值。

> 这种格式将 null 值编码成 byte[] 类型的 null。这样在 upsert-kafka 中使用时可能会有限制，因为 upsert-kafka 将 null 值视为墓碑消息（键上的 DELETE）。因此，如果该字段具有 null 值，我们建议不要使用 upsert-kafka Connector 以及 Raw Format 不要作为 value.format。

### 6.1 依赖

Raw Format 是内置的，不需要额外的依赖项。

### 6.2 使用

你可能在 Kafka 中具有如下原始日志数据，并希望使用 Flink SQL 读取以及分析数据：
```
47.29.201.179 - - [28/Feb/2019:13:17:10 +0000] "GET /?p=1 HTTP/2.0" 200 5316 "https://domain.com/?p=1" "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36" "2.75"
```
下面的代码创建了一张表，使用 Raw Format 以 UTF-8 编码的形式从 Kafka topic 中读取（也可以写入）数据：
```sql
CREATE TABLE nginx_log (
  log STRING
) WITH (
  'connector' = 'kafka',
  'topic' = 'nginx_log',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'testGroup',
  'format' = 'raw'
)
```
然后，将原始数据读取为字符串，使用用户自定义函数将其分为多个字段进一步分析：
```sql
SELECT t.hostname, t.datetime, t.url, t.browser, ...
FROM(
  SELECT my_split(log) as t FROM nginx_log
);
```

### 6.3 参数说明

| 参数     | 是否必选     | 默认值	| 类型	| 描述 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| format | 必选	| (none) | String | 格式 Format 名称 'raw'。|
| raw.charset | 可选	| UTF-8	| String | 指定字符集来编码文本字符串。|
| raw.endianness | 可选	| big-endian | String	| 指定字节序来编码数字值的字节。有效值为'big-endian'和'little-endian'。|

### 6.4 数据类型映射

下表详细说明了这种格式支持的 SQL 类型，包括用于编码和解码的序列化类和反序列化类的详细信息。

![](6)

参考：https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/connectors/table/formats/overview/
