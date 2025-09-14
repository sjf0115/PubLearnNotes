在大规模流处理中，我们经常遇到这样的需求：“计算每个用户最近 5 次点击的平均时长” 或 “为每个订单计算其当前价格与之前最低价格的差值”。这类需求的核心在于，不仅要对数据进行分组，还要在时间或行数的维度上，为每一行数据计算一个与它附近行相关的聚合结果。

这正是 Flink SQL 中 Over 聚合（Over Aggregation） 大显身手的地方。它像是为流数据中的每一行都开了一个“滑动窗口”，让你能够进行灵活、强大的窗口内计算。

## 1. 什么是 Over 聚合？

Apache Flink 的流式 Over 聚合是一种在无界数据流上按行或范围进行滑动窗口计算的机制。简单来说，Over 聚合允许你对一个数据行窗口（称为一个 'Over Window'）应用聚合函数（如 SUM(), AVG(), ROW_NUMBER() 等）。这个窗口的范围是相对于当前处理的行而定义的。

与传统 GROUP BY 窗口不同，Over 聚合不会将每个分组的多条输入行聚合为一行，而是会为每个输入行计算一个聚合结果。Over 聚合是一种用于聚合计算的特殊聚合函数，也可以将 Over 聚合理解为一种特殊的滑动窗口。Over 聚合允许对每一行数据的某个动态范围内的数据进行聚合（如计算累计值、移动平均等）。Over 聚合中每1个元素都对应1个 Over 窗口。Over 聚合可以按照实际元素的行或实际的元素值（时间戳值）确定窗口，因此流数据元素可能分布在多个窗口中。

> 动态范围：每个输入行都会触发一次计算，计算基于该行前后的特定范围（如当前行之前的 5 行，或基于时间的 10 分钟区间）。

## 2. 语法

```sql
SELECT
    agg_func1(col1) OVER (definition1) AS colName,
    ...
    agg_funcN(colN) OVER (definitionN) AS colNameN
FROM Tab1;

SELECT
  agg_func1(agg_col1) OVER (
    [PARTITION BY col1[, col2, ...]]
    ORDER BY time_col
    range_definition) AS colName1,
  ...
  agg_funcN(agg_colN) OVER (definitionN) AS colNameN
FROM Tab1;
```
可以在 SELECT 子句中定义多个 OVER 窗口聚合。但是对于流查询，由于当前的限制，所有聚合的 OVER 窗口聚合必须相同，即 agg_func1 到 agg_funcN 所对应的 OVER definition 必须相同。下面详细介绍 OVER definition 中的参数：
- ORDER BY 子句
  - 必选，定义数据顺序，需要注意的时必须基于时间属性，如事件时间或处理时间
  - OVER 窗口聚合是在有序的行序列上定义的。由于表没有固定的顺序，所以 ORDER BY 子句是强制性的。对于流查询，Flink 目前只支持以升序时间属性顺序定义的 OVER 窗口聚合。
- PARTITION BY 子句
  - 可选，按指定字段分组
  - OVER 窗口聚合可以在分区表上定义。如果存在 PARTITION BY 子句，则仅在其分区的行上为每个输入行计算聚合。
- range_definition 范围定义子句
  - 范围定义指定窗口聚合中包含多少行。范围由 BETWEEN 子句定义，该子句定义了窗口下限和上限。这些边界之间的所有行都包含在聚合中。
  - 需要注意的是 Flink 只支持 CURRENT ROW 作为上边界。
  - 目前聚合数据的范围有两种指定方式，一种方式是按照行数聚合 ROWS OVER，另一种方式是按照时间区间聚合 RANGE OVER。

## 3. 类型

Flink SQL 中对 OVER 窗口聚合的定义遵循标准 SQL 的定义语法。按照计算行的定义方式，OVER 窗口聚合可以分为以下两类：
- ROWS OVER：每1行元素都被视为新的计算行，即每1行都是一个新的窗口。可以理解为按照行数的滑动窗口聚合计算
- RANGE OVER：具有相同时间值的所有元素行视为同一计算行，即具有相同时间值的所有行都是同一个窗口。可以理解为按照时间的滑动窗口聚合计算

| 类型     | 说明     | proctime     | eventtime     |
| :------------- | :------------- | :------------- | :------------- |
| ROWS OVER       | 按照实际元素的行确定窗口。 | 支持 | 支持 |
| RANGE OVER      | 按照实际的元素值（时间戳值）确定窗口。 | 支持 | 支持 |

### 3.1 ROWS OVER

#### 3.1.1 语法

ROWS OVER Window 的每个元素都确定一个窗口。窗口语法如下所示：
```sql
SELECT
    agg1(col1) OVER(
     [PARTITION BY (value_expression1,..., value_expressionN)]
     ORDER BY timeCol
     ROWS
     BETWEEN (UNBOUNDED | rowCount) PRECEDING AND CURRENT ROW) AS colName, ...
FROM Tab1;       
```
- value_expression：分区值表达式。
- timeCol：元素排序的时间字段。
- rowCount：定义根据当前行开始向前追溯几行元素。

ROWS OVER 是一个基于计数的窗口，精确定义聚合中包含多少行。下面的 ROWS OVER 定义当前行和当前行之前的10行（总共11行）包含在聚合中:
```sql
ROWS BETWEEN 10 PRECEDING AND CURRENT ROW
```

#### 3.1.2 示例

假设有一张商品上架表，包含商品ID、商品类目、商品价格以及商品上架时间：
```sql
CREATE TABLE shop_sales (
  product_id BIGINT COMMENT '商品Id',
  category STRING COMMENT '商品类目',
  price BIGINT COMMENT '商品价格',
  `timestamp` BIGINT COMMENT '商品上架时间',
  ts_ltz AS TO_TIMESTAMP_LTZ(`timestamp`, 3), -- 事件时间
  WATERMARK FOR ts_ltz AS ts_ltz - INTERVAL '5' SECOND -- 在 ts_ltz 上定义watermark，ts_ltz 成为事件时间列
) WITH (
  'connector' = 'kafka',
  'topic' = 'shop_sales',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'shop_sales',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'false',
  'json.fail-on-missing-field' = 'true'
));
```
要求输出在当前商品上架之前同类的最近3个商品中的最高价格：
```sql
SELECT
  product_id, category, price, DATE_FORMAT(ts_ltz, 'yyyy-MM-dd HH:mm:ss') AS time,
  MAX(price) OVER (PARTITION BY category ORDER BY ts_ltz ROWS BETWEEN 2 preceding AND CURRENT ROW) AS max_price
FROM shop_sales;
```

假设输入数据为：

| product_id | category | price | timestamp | 备注 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| 1001 | 图书 | 40  | 1665360300000 | 2022-10-10 08:05:00 |
| 2001 | 生鲜 | 80  | 1665360360000 | 2022-10-10 08:06:00 |
| 1002 | 图书 | 30  | 1665360420000 | 2022-10-10 08:07:00 |
| 2002 | 生鲜 | 80  | 1665360480000 | 2022-10-10 08:08:00 |
| 2003 | 生鲜 | 150 | 1665360540000 | 2022-10-10 08:09:00 |
| 1003 | 图书 | 100 | 1665360470000 | 2022-10-10 08:05:50 |
| 2004 | 生鲜 | 70  | 1665360660000 | 2022-10-10 08:11:00 |
| 2005 | 生鲜 | 20  | 1665360720000 | 2022-10-10 08:12:00 |
| 1004 | 图书 | 10  | 1665360780000 | 2022-10-10 08:13:00 |
| 2006 | 生鲜 | 120 | 1665360840000 | 2022-10-10 08:14:00 |
| 1005 | 图书 | 20  | 1665360900000 | 2022-10-10 08:15:00 |
| 1006 | 图书 | 60  | 1665360896000 | 2022-10-10 08:14:56 |
| 1007 | 图书 | 90  | 1665361080000 | 2022-10-10 08:18:00 |

实际效果如下所示：
```java
+I[1001, 图书, 40, 2022-10-10 08:05:00, 40, 1001]
+I[2001, 生鲜, 80, 2022-10-10 08:06:00, 80, 2001]
+I[1002, 图书, 30, 2022-10-10 08:07:00, 40, 1001:1002]
+I[2002, 生鲜, 80, 2022-10-10 08:08:00, 80, 2001:2002]
+I[2003, 生鲜, 150, 2022-10-10 08:09:00, 150, 2001:2002:2003]
+I[2004, 生鲜, 70, 2022-10-10 08:11:00, 150, 2002:2003:2004]
+I[2005, 生鲜, 20, 2022-10-10 08:12:00, 150, 2003:2004:2005]
+I[1004, 图书, 10, 2022-10-10 08:13:00, 40, 1001:1002:1004]
+I[2006, 生鲜, 120, 2022-10-10 08:14:00, 120, 2004:2005:2006]
+I[1006, 图书, 60, 2022-10-10 08:14:56, 60, 1002:1004:1006]
+I[1005, 图书, 20, 2022-10-10 08:15:00, 60, 1004:1006:1005]
```

> 最重要的是 1003 迟到记录的丢弃

### 2.2 RANGE OVER

#### 2.2.1 语法

```sql
SELECT
    agg1(col1) OVER(
     [PARTITION BY (value_expression1,..., value_expressionN)]
     ORDER BY timeCol
     RANGE
     BETWEEN (UNBOUNDED | timeInterval) PRECEDING AND CURRENT ROW) AS colName,
...
FROM Tab1;
```

RANGE OVER 是在 ORDER BY 列的值上定义的，在 Flink 中总是一个时间属性。下面的 RANGE OVER 定义时间属性最多比当前行少30分钟的所有行都包含在聚合中:
```sql
RANGE BETWEEN INTERVAL '30' MINUTE PRECEDING AND CURRENT ROW
```

#### 2.2.2 示例

假设一张商品上架表，包含有商品ID、商品类型、商品上架时间、商品价格数据。需要求比当前商品上架时间早2分钟的同类商品中的最高价格。

```sql

```

假设输入数据为：

| product_id | category | price | timestamp | 备注 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| 1001 | 图书 | 40  | 1665360300000 | 2022-10-10 08:05:00 |
| 2001 | 生鲜 | 80  | 1665360360000 | 2022-10-10 08:06:00 |
| 1002 | 图书 | 30  | 1665360420000 | 2022-10-10 08:07:00 |
| 2002 | 生鲜 | 80  | 1665360480000 | 2022-10-10 08:08:00 |
| 2003 | 生鲜 | 150 | 1665360540000 | 2022-10-10 08:09:00 |
| 1003 | 图书 | 100 | 1665360470000 | 2022-10-10 08:05:50 |
| 2004 | 生鲜 | 70  | 1665360660000 | 2022-10-10 08:11:00 |
| 2005 | 生鲜 | 20  | 1665360720000 | 2022-10-10 08:12:00 |
| 1004 | 图书 | 10  | 1665360780000 | 2022-10-10 08:13:00 |
| 2006 | 生鲜 | 120 | 1665360840000 | 2022-10-10 08:14:00 |
| 1005 | 图书 | 20  | 1665360900000 | 2022-10-10 08:15:00 |
| 1006 | 图书 | 60  | 1665360896000 | 2022-10-10 08:14:56 |
| 1007 | 图书 | 90  | 1665361080000 | 2022-10-10 08:18:00 |

实际效果如下所示：
```java
+I[1001, 图书, 40, 2022-10-10 08:05:00, 40, 1001]
+I[2001, 生鲜, 80, 2022-10-10 08:06:00, 80, 2001]
+I[1002, 图书, 30, 2022-10-10 08:07:00, 40, 1001:1002]
+I[2002, 生鲜, 80, 2022-10-10 08:08:00, 80, 2001:2002]
+I[2003, 生鲜, 150, 2022-10-10 08:09:00, 150, 2001:2002:2003]
+I[2004, 生鲜, 70, 2022-10-10 08:11:00, 150, 2002:2003:2004]
+I[2005, 生鲜, 20, 2022-10-10 08:12:00, 150, 2003:2004:2005]
+I[1004, 图书, 10, 2022-10-10 08:13:00, 10, 1004]
+I[2006, 生鲜, 120, 2022-10-10 08:14:00, 120, 2004:2005:2006]
+I[1006, 图书, 60, 2022-10-10 08:14:56, 60, 1004:1006]
+I[1005, 图书, 20, 2022-10-10 08:15:00, 60, 1004:1006:1005]
```


## 4. 流式处理中的特殊要求

### 4.1 时间属性

Over 窗口必须基于时间属性字段（事件时间或处理时间），需在 DDL 中定义：
```sql
CREATE TABLE Events (
  user_id STRING,
  amount DOUBLE,
  event_time TIMESTAMP(3),
  -- 定义事件时间及水位线
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (...);
```
### 4.2 范围限制

流式 Over 窗口的结束边界必须是 CURRENT ROW（不能使用 UNBOUNDED FOLLOWING），因为无法预知未来数据。


https://help.aliyun.com/zh/flink/developer-reference/over-windows
https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/sql/queries/over-agg/
