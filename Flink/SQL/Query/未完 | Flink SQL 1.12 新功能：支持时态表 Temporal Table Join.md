时态表是一个随时间变化的表，在 Flink 中也称为[动态表]()。时态表中的行与一个或多个时态周期相关联，所有 Flink 表都是时态的（动态的）。时态表包含一个或多个版本表快照，它可以是一个不断变化的历史表，用于跟踪变化(例如：数据库变更日志，包含所有快照)或一个变化的维度表，它具体化了变化(例如：包含最新快照的数据库表)。




在之前的版本中，用户需要通过创建时态表函数 Temporal Table Function 来支持时态表 JOIN (Temporal Table Join)，而在 Flink 1.12 中，用户可以使用标准的 SQL 语句 FOR SYSTEM_TIME AS OF 来支持 JOIN。此外，现在任意包含时间列和主键的表，都可以作为时态表，而不仅仅是 append-only 表。这带来了一些新的应用场景，比如将 Kafka compacted topic 或数据库变更日志（来自 Debezium 等）作为时态表。

## 1. Event Time Temporal Join

事件时间时态 JOIN 允许与版本表进行 JOIN。这意味着可以通过更改元数据以及根据值在特定时间点检索来丰富表。




```sql
SELECT [column_list]
FROM table1 [AS <alias1>]
[LEFT] JOIN table2 FOR SYSTEM_TIME AS OF table1.{ proctime | rowtime } [AS <alias2>]
ON table1.column-name1 = table2.column-name1
```

```sql
-- Create a table of orders. This is a standard
-- append-only dynamic table.
CREATE TABLE orders (
    order_id    STRING,
    price       DECIMAL(32,2),
    currency    STRING,
    order_time  TIMESTAMP(3),
    WATERMARK FOR order_time AS order_time
) WITH (/* ... */);

-- Define a versioned table of currency rates.
-- This could be from a change-data-capture
-- such as Debezium, a compacted Kafka topic, or any other
-- way of defining a versioned table.
CREATE TABLE currency_rates (
    currency STRING,
    conversion_rate DECIMAL(32, 2),
    update_time TIMESTAMP(3) METADATA FROM `values.source.timestamp` VIRTUAL,
    WATERMARK FOR update_time AS update_time,
    PRIMARY KEY(currency) NOT ENFORCED
) WITH (
   'connector' = 'kafka',
   'value.format' = 'debezium-json',
   /* ... */
);

SELECT
     order_id,
     price,
     currency,
     conversion_rate,
     order_time
FROM orders
LEFT JOIN currency_rates FOR SYSTEM_TIME AS OF orders.order_time
ON orders.currency = currency_rates.currency;
```
