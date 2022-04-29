
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

如下是一个使用 Kafka Connector 以及 CSV Forma 创建表的示例：
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

如下是一个使用 Kafka Connector 以及 JSON Forma 创建表的示例：
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


参考：https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/connectors/table/formats/overview/
