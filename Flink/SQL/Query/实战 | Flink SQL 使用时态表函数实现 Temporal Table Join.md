
## 1. 时态表函数

时态表函数 Temporal Table Function 提供了在特定时间点访问时态表特定版本的功能。为了访问时态表中的数据，必须传递一个时间属性，该属性用来确定将返回的表版本。Flink 使用 Table Function  SQL 语法来提供一种表达方式。

与版本化表不同，时态表函数只能基于 Append-only 流定义，即只支持 Append-only 流，不支持 Changelog 的输入。此外，时态表函数不能通过纯 SQL DDL 定义。

## 2. 定时时态表函数

可以使用 Table API 在 Append-only 流之上定义时态表函数。该表可以注册一个或多个 Key 列以及一个用于版本控制的时间属性。

假设我们有一个 Append-only 的货币汇率表，我们希望将其注册为一个时态表函数。

```sql
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

## 3. 时态表函数 JOIN

一旦定义，时态表函数就可以当做标准表函数使用。Append-only 表（左表/Probe表）可以与时态表（右表/Build表）JOIN，即随时间变化并跟踪其变化的表，以根据 Key 检索在特定时间点的值。

考虑一个 Append-only 表 orders，以不同汇率跟踪客户订单。

```sql
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
