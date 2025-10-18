## 1. 简介

DataGen Connector 是一个内置的 Source Connector，基于生成的内存数据来创建表。这在本地开发查询而不访问外部系统（如 Kafka）时很有用。

```sql
CREATE TABLE Orders (
    order_number BIGINT,
    price        DECIMAL(32,2),
    buyer        ROW<first_name STRING, last_name STRING>,
    order_time   TIMESTAMP(3)
) WITH (
  'connector' = 'datagen'
)
```

DataGen Connector 有两种生成数据的生成器：
- random：随机生成器
- sequence：序列生成器

随机生成器（random），是默认的生成器。可以指定随机生成的最大和最小值。char、varchar、string （类型）可以指定长度。随机生成器是一种无界的生成器，如果指定了总行数，从而变成了一个有界生成器。

序列生成器（sequence），可以指定序列的起始和结束值。由于指定了序列的区间，所以序列生成器是有界生成器。当序列数字达到结束值时读取结束。

当表中字段的数据全部生成完成后，Source 读取就结束了。因此，表的有界性取决于字段的有界性。需要注意的是如果表中的某一列通过序列生成器生成，那么表是一个有界表并以第一个序列完成而结束。

> 时间类型始终是本地机器当前系统时间。

## 2. 参数

| 参数 | 是否必选 | 默认值 | 数据类型 | 描述 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| connector          | 必填 | 无    | String | 指定要使用的连接器，这里为 'datagen' |
| rows-per-second    | 可选 | 10000	| Long	| 每秒生成的行数，用以控制数据发出速率 |
| number-of-rows     | 可选 | 无   | Long | 输出的总行数 |
| fields.#.kind      | 可选 | random	| String	| 指定 '#' 字段的生成器：序列生成器 sequence 或者随机生成器 random |
| fields.#.min       | 可选 |  |  | 随机生成器的最小值，适用于数字类型 |
| fields.#.max       | 可选 |  |  | 随机生成器的最大值，适用于数字类型 |
| fields.#.max-past  | 可选 | 0 | Duration | 随机生成器生成相对当前时间向过去偏移的最大值，适用于 timestamp 类型 |
| fields.#.length    | 可选 | 100 | Integer | 随机生成器生成字符的长度，适用于 char、varchar、string |
| fields.#.start     | 可选	| 无 |  | 序列生成器的起始值 |
| fields.#.end       | 可选	| 无 |  | 序列生成器的结束值 |

## 3. 数据类型

| 数据类型	| 支持的生成器	| 备注 |
| :------------- | :------------- | :------------- |
| BOOLEAN	| random | |
| CHAR	| random / sequence | |
| VARCHAR	| random / sequence | |
| STRING	| random / sequence | |
| DECIMAL	| random / sequence | |
| TINYINT	| random / sequence | |
| SMALLINT	| random / sequence | |
| INT	| random / sequence | |
| BIGINT	| random / sequence | |
| FLOAT	| random / sequence | |
| DOUBLE	| random / sequence | |
| DATE	| random	| 始终解析为本地机器的当前日期 |
| TIME	| random	| 始终解析为本地机器的当前时间 |
| TIMESTAMP	| random	| 始终解析为本地机器的当前时间戳 |
| TIMESTAMP_LTZ	| random	| 始终解析为本地机器的当前时间戳 |
| INTERVAL YEAR TO MONTH	| random | |
| INTERVAL DAY TO MONTH	| random | |
| ROW	| random	| 生成带有随机子字段的 ROW |
| ARRAY	| random	| 生成带有随机条目的 ARRAY |
| MAP	| random	| 生成带有随机条目的 MAP |
| MULTISET	| random	| 生成带有随机条目的 MULTISET |

## 3. 示例

### 3.1 随机生成器

如下所示使用 Datagen Connector 的随机生成器生成订单测试数据：
```sql
CREATE TABLE order_behavior (
  order_id STRING COMMENT '订单Id',
  uid BIGINT COMMENT '用户Id',
  amount DOUBLE COMMENT '订单金额',
  `timestamp` TIMESTAMP_LTZ(3) COMMENT '下单时间戳',
  WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '5' SECOND -- 在 ts_ltz 上定义watermark，ts_ltz 成为事件时间列
) WITH (
  'connector' = 'datagen',
  'rows-per-second' = '1',
  'fields.order_id.kind' = 'random',
  'fields.order_id.length' = '6',
  'fields.uid.kind' = 'random',
  'fields.uid.min' = '10000001',
  'fields.uid.max' = '99999999',
  'fields.amount.kind' = 'random',
  'fields.amount.min' = '1',
  'fields.amount.max' = '1000'
)
```
其中 order_id、uid、amount 三个字段均使用随机生成器来生成。order_id 为字符长度 6 位的随机字符串，uid 为`[10000001, 99999999]`区间的随机数字，amount 为 `[1, 100]` 区间的随机数字。

我们从 Datagen Connector 中读取并输出打印到控制台如下所示：
```
+I[ddbe38, 34043311, 943.119660546621, 2022-10-07T14:51:34.775Z, 2022-10-07 22:51:34]
+I[6f9ee5, 21829173, 676.8071038855844, 2022-10-07T14:51:35.767Z, 2022-10-07 22:51:35]
+I[bdca0f, 74363273, 170.15399769411923, 2022-10-07T14:51:36.767Z, 2022-10-07 22:51:36]
+I[720f09, 97040658, 152.54343773708368, 2022-10-07T14:51:37.765Z, 2022-10-07 22:51:37]
+I[678ccf, 26963755, 526.719829931194, 2022-10-07T14:51:38.768Z, 2022-10-07 22:51:38]
+I[771d9f, 26816385, 605.0194613937896, 2022-10-07T14:51:39.767Z, 2022-10-07 22:51:39]
+I[413bbb, 30187320, 48.88868724022406, 2022-10-07T14:51:40.767Z, 2022-10-07 22:51:40]
+I[685881, 53069445, 952.7262584143115, 2022-10-07T14:51:41.768Z, 2022-10-07 22:51:41]
...
```
> 在这 order_behavior 为一个无界表

> 完整代码请查阅 [RandomDatagenExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/connectors/datagen/RandomDatagenExample.java)

### 3.2 序列生成器

如下所示使用 Datagen Connector 的序列生成器生成订单测试数据：
```sql
CREATE TABLE order_behavior (
  order_id BIGINT COMMENT '订单Id'
) WITH (
  'connector' = 'datagen',
  'rows-per-second' = '1',
  'fields.order_id.kind' = 'sequence',
  'fields.order_id.start' = '10000001',
  'fields.order_id.end' = '10000010'
)
```
其中 order_id 字段均使用序列生成器来生成，为 `[10000001, 10000010]` 区间的递增序列。

我们从 Datagen Connector 中读取并输出打印到控制台如下所示：
```
+I[10000001]
+I[10000002]
+I[10000003]
+I[10000004]
+I[10000005]
+I[10000006]
+I[10000007]
+I[10000008]
+I[10000009]
+I[10000010]
```
> 在这 order_behavior 为一个有界表

> 完整代码请查阅 [SequenceDataGenExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/connectors/datagen/SequenceDataGenExample.java)
