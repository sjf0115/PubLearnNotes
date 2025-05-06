
Over 聚合为一组有序行的每个输入行都会计算聚合值。与 GROUP BY 分组聚合相反，Over 聚合不会将每个分组的多条输入行聚合为一行，而是会为每个输入行计算一个聚合结果。Over 聚合是一种特殊的聚合函数，用于聚合计算，也可以将 Over 聚合理解为一种特殊的滑动窗口。

## 1. 语法

```sql
SELECT
  agg_func1(agg_col1) OVER (
    [PARTITION BY col1[, col2, ...]]
    ORDER BY time_col
    range_definition) AS colName1,
  ...
  agg_funcN(agg_colN) OVER (definitionN) AS colNameN
FROM ...
```
可以在 SELECT 子句中定义多个 OVER 窗口聚合。但是，对于流查询，由于当前的限制，所有聚合的 OVER 窗口聚合必须相同，即 OVER 子句中的 definition 必须相同。

- ORDER BY 子句
  - OVER 窗口聚合是在有序的行序列上定义的。由于表没有固定的顺序，所以 ORDER BY 子句是强制性的。对于流查询，Flink 目前只支持以升序时间属性顺序定义的 OVER 窗口聚合。
- PARTITION BY 子句
  - OVER 窗口聚合可以在分区表上定义。如果存在 PARTITION BY 子句，则仅在其分区的行上为每个输入行计算聚合。
- range_definition 范围定义子句
  - 范围定义指定窗口聚合中包含多少行。范围由 BETWEEN 子句定义，该子句定义了窗口下限和上限。这些边界之间的所有行都包含在聚合中。
  - 需要注意的是 Flink 只支持 CURRENT ROW 作为上边界。

## 2. 类型

Flink SQL 中对 OVER 窗口聚合的定义遵循标准 SQL 的定义语法。按照计算行的定义方式，OVER 窗口聚合可以分为以下两类：
- ROWS OVER：每1行元素都被视为新的计算行，即每1行都是一个新的窗口。
- RANGE OVER：具有相同时间值的所有元素行视为同一计算行，即具有相同时间值的所有行都是同一个窗口。

| 类型     | 说明     | proctime     | eventtime     |
| :------------- | :------------- | :------------- | :------------- |
| ROWS OVER       | 按照实际元素的行确定窗口。 | 支持 | 支持 |
| RANGE OVER      | 按照实际的元素值（时间戳值）确定窗口。 | 支持 | 支持 |

### 2.1 ROWS OVER



语法:
```sql
SELECT
    agg1(col1) OVER(
     [PARTITION BY (value_expression1,..., value_expressionN)]
     ORDER BY timeCol
     ROWS
     BETWEEN (UNBOUNDED | rowCount) PRECEDING AND CURRENT ROW) AS colName, ...
FROM Tab1;       
```
ROWS OVER 是一个基于计数的窗口，精确定义聚合中包含多少行。下面的 ROWS OVER 定义当前行和当前行之前的10行（总共11行）包含在聚合中:
```sql
ROWS BETWEEN 10 PRECEDING AND CURRENT ROW
```

假设有一张商品上架表，包含商品ID、商品类型、商品上架时间、商品价格数据。要求输出在当前商品上架之前同类的最近3个商品中的最高价格。

```sql
CREATE TEMPORARY TABLE tmall_item(
  itemid VARCHAR,
  itemtype VARCHAR,
  eventtime varchar,                            
  onselltime AS TO_TIMESTAMP(eventtime),
  price DOUBLE,
  WATERMARK FOR onselltime AS onselltime - INTERVAL '2' SECOND  -- 为Rowtime定义Watermark
) WITH (
  'connector' = 'kafka',
  'topic' = '<yourTopic>',
  'properties.bootstrap.servers' = '<brokers>',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'csv'
);

SELECT
    itemid,
    itemtype,
    onselltime,
    price,  
    MAX(price) OVER (
        PARTITION BY itemtype
        ORDER BY onselltime
        ROWS BETWEEN 2 preceding AND CURRENT ROW
    ) AS maxprice
FROM tmall_item;
```

### 2.2 RANGE OVER

语法:
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

假设一张商品上架表，包含有商品ID、商品类型、商品上架时间、商品价格数据。需要求比当前商品上架时间早2分钟的同类商品中的最高价格。

```sql
CREATE TEMPORARY TABLE tmall_item(
  itemid VARCHAR,
  itemtype VARCHAR,
  eventtime varchar,                            
  onselltime AS TO_TIMESTAMP(eventtime),
  price DOUBLE,
  WATERMARK FOR onselltime AS onselltime - INTERVAL '2' SECOND  -- 为Rowtime定义Watermark
) WITH (
  'connector' = 'kafka',
  'topic' = '<yourTopic>',
  'properties.bootstrap.servers' = '<brokers>',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'csv'
);

SELECT  
    itemid,
    itemtype,
    onselltime,
    price,  
    MAX(price) OVER (
        PARTITION BY itemtype
        ORDER BY onselltime
        RANGE BETWEEN INTERVAL '2' MINUTE preceding AND CURRENT ROW
    ) AS maxprice
FROM tmall_item;  
```


https://help.aliyun.com/zh/flink/developer-reference/over-windows
