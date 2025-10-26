在之前的版本中，用户需要通过创建时态表函数（temporal table function） 来支持时态表 JOIN（temporal table join） ，而在 Flink 1.12 中，用户可以使用标准的 SQL 语句 FOR SYSTEM_TIME AS OF（SQL：2011）来支持 JOIN。此外，现在任意包含时间列和主键的表，都可以作为时态表，而不仅仅是 append-only 表。这带来了一些新的应用场景，比如将 Kafka compacted topic 或数据库变更日志（来自 Debezium 等）作为时态表。



## 2. Temporal Table Join



在之前的版本中，用户需要通过创建时态表函数（temporal table function） 来支持时态表 join（temporal table join） ，而在 Flink 1.12 中，用户可以使用标准的 SQL 语句 FOR SYSTEM_TIME AS OF（SQL：2011）来支持 join。此外，现在任意包含时间列和主键的表，都可以作为时态表，而不仅仅是 append-only 表。这带来了一些新的应用场景，比如将 Kafka compacted topic 或数据库变更日志（来自 Debezium 等）作为时态表。

```sql
CREATE TABLE orders (
    order_id STRING,
    currency STRING,
    amount INT,              
    order_time TIMESTAMP(3),                
    WATERMARK FOR order_time AS order_time - INTERVAL '30' SECOND
) WITH (
  …
);

-- Table backed by a Kafka compacted topic
CREATE TABLE latest_rates (
    currency STRING,
    rate DECIMAL(38, 10),
    currency_time TIMESTAMP(3),
    WATERMARK FOR currency_time AS currency_time - INTERVAL ‘5’ SECOND,
    PRIMARY KEY (currency) NOT ENFORCED      
) WITH (
  'connector' = 'upsert-kafka',
  …
);

-- Event-time temporal table join
SELECT
  o.order_id,
  o.order_time,
  o.amount * r.rate AS amount,
  r.currency
FROM orders AS o, latest_rates FOR SYSTEM_TIME AS OF o.order_time r
ON o.currency = r.currency;
```
上面的示例同时也展示了如何在 temporal table join 中使用 Flink 1.12 中新增的 upsert-kafka connector。
