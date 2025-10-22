在之前的版本中，用户需要通过创建时态表函数（temporal table function） 来支持时态表 JOIN（temporal table join） ，而在 Flink 1.12 中，用户可以使用标准的 SQL 语句 FOR SYSTEM_TIME AS OF（SQL：2011）来支持 JOIN。此外，现在任意包含时间列和主键的表，都可以作为时态表，而不仅仅是 append-only 表。这带来了一些新的应用场景，比如将 Kafka compacted topic 或数据库变更日志（来自 Debezium 等）作为时态表。


## 1. 利用时态表函数 JOIN

### 1.1 

时态表函数提供了在特定时间点访问时态表特定版本的功能。为了访问时态表中的数据，必须传递一个时间属性，该属性用来确定将返回的表版本。Flink 使用 Table Function  SQL 语法来提供一种表达方式。

与版本化表不同，时态表函数只能基于 Append-only 流定义，即只支持 Append-only 流，不支持 Changelog 的输入。此外，时态表函数不能通过纯 SQL DDL 定义。


定时时态表

可以使用 Table API 在 Append-only 流之上定义时态表函数。该表可以注册一个或多个 Key 列以及一个用于版本控制的时间属性。

假设我们有一个 Append-only 的货币汇率表，我们希望将其注册为一个时态表函数。

```
SELECT * FROM currency_rates;

update_time   currency   rate
============= =========  ====
09:00:00      Yen        102
09:00:00      Euro       114
09:00:00      USD        1
11:15:00      Euro       119
11:49:00      Pounds     108
```

使用 Table API，我们可以将此流注册为以 `currency` 作为 Key，以 `update_time` 作为版本时间属性的时态表：
```java
TemporalTableFunction rates = tEnv
    .from("currency_rates").
    .createTemporalTableFunction("update_time", "currency");

tEnv.registerFunction("rates", rates);   
```

时态表函数 JOIN

一旦定义，时态表函数就可以当做标准表函数使用。Append-only 表（左表/Probe表）可以与时态表（右表/Build表）JOIN，即随时间变化并跟踪其变化的表，以根据 Key 检索在特定时间点的值。

考虑一个 Append-only 表 orders，以不同汇率跟踪客户订单。

```
SELECT * FROM orders;

order_time amount currency
========== ====== =========
10:15        2    Euro
10:30        1    USD
10:32       50    Yen
10:52        3    Euro
11:04        5    USD
```

根据这些表格，我们希望将订单转换为通用货币-美元。

```sql
SELECT
  SUM(amount * rate) AS amount
FROM orders,
LATERAL TABLE (rates(order_time))
WHERE rates.currency = orders.currency
```

```java
Table result = orders
    .joinLateral($("rates(order_time)"), $("orders.currency = rates.currency"))
    .select($("(o_amount * r_rate).sum as amount"));
```



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
