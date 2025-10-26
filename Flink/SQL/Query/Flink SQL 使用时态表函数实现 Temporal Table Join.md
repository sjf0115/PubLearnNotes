
## 1. 时态表函数

时态表函数 Temporal Table Function 提供了在特定时间点访问时态表特定版本的功能。为了访问时态表中的数据，必须传递一个时间属性，该属性用来确定将返回的表版本。Flink 使用 Table Function  SQL 语法来提供一种表达方式。

与版本化表不同，时态表函数只能基于 Append-only 流定义，即只支持 Append-only 流，不支持 Changelog 的输入。此外，时态表函数不能通过纯 SQL DDL 定义。

## 2. 定时时态表函数

可以使用 Table API 在 Append-only 流之上定义时态表函数。该表可以注册一个或多个 Key 列以及一个用于版本控制的时间属性。

假设我们有一个 Append-only 的货币汇率表(美元与日元、欧元、英镑等货币的汇率)：
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
可以将其注册为一个时态表函数。使用 Table API，我们可以将此流注册为以 `currency` 作为 Key，以 `update_time` 作为版本时间属性的时态表：
```java
TemporalTableFunction rates = tEnv
        .from("currency_rates")
        .createTemporalTableFunction($("update_time"), $("currency"));
tEnv.createTemporarySystemFunction("rates_function", rates);
```

## 3. 时态表函数 JOIN

时态表函数 `rates_function` 定义之后就可以当做标准表函数使用。Append-only 表（左表/Probe表）可以与时态表（右表/Build表）JOIN，即随时间变化并跟踪其变化的表，以根据 Key 检索在特定时间点的值。

假设我们有一个 Append-only 表 orders，订单来自于不同的地区，所以支付的币种各不一样：
```sql
SELECT * FROM orders;

order_time amount currency
========== ====== =========
10:15        2    Euro
10:30        1    USD
10:32       50    Yen
11:32        3    Euro
11:50        5    Pounds
```

现在我们希望将订单金额统一转换为美元：
```sql  
SELECT
  FROM_UNIXTIME(o.order_time/1000, 'yyyy-MM-dd HH:mm:ss') AS order_time, o.currency, o.amount,
  r.rate, FROM_UNIXTIME(r.rate_time/1000, 'yyyy-MM-dd HH:mm:ss') AS rate_time,
  o.amount * r.rate AS rate_amount
FROM orders AS o,
LATERAL TABLE (rates_function(order_ltz)) AS r
WHERE o.currency = r.currency
```
> rate_ltz 是基于 update_time 的事件时间属性字段；order_ltz 是基于 orderTime 的事件时间属性字段

## 4. 示例

首先创建货币汇率表：
```java
DataStream<CurrencyRates> ratesStream = env.fromElements(
        new CurrencyRates(1761094800000L, "Yen", 102), // 2025-10-22 09:00:00
        new CurrencyRates(1761094800000L, "Euro", 114), // 2025-10-22 09:00:00
        new CurrencyRates(1761094800000L, "USD", 1), // 2025-10-22 09:00:00
        new CurrencyRates(1761102900000L, "Euro", 119), // 2025-10-22 11:15:00
        new CurrencyRates(1761104940000L, "Pounds", 108) // 2025-10-22 11:49:00
).assignTimestampsAndWatermarks(
        WatermarkStrategy.<CurrencyRates>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((rate, updateTime) -> rate.getUpdateTime())
).setParallelism(1);

// 注册 currency_rates 表
tEnv.createTemporaryView("currency_rates", ratesStream,
      $("updateTime").as("rate_time"), $("currency"),  $("rate"), $("rate_ltz").rowtime()
);
```
> rate_ltz 是基于 update_time 的事件时间属性字段

现在我们可以将此流注册为以 `currency` 作为 Key，以 `rate_ltz` 作为版本时间属性的时态表：
```java
TemporalTableFunction rates = tEnv
        .from("currency_rates")
        .createTemporalTableFunction($("rate_ltz"), $("currency"));
tEnv.createTemporarySystemFunction("rates_function", rates);
```

然后创建订单表：
```java
DataStream<CurrencyOrder> orderStream = env.fromElements(
        new CurrencyOrder(1761099300000L, 2, "Euro"), // 2025-10-22 10:15:00
        new CurrencyOrder(1761100200000L, 1, "USD"), // 2025-10-22 10:30:00
        new CurrencyOrder(1761100320000L, 50, "Yen"), // 2025-10-22 10:32:00
        new CurrencyOrder(1761103920000L, 3, "Euro"), // 2025-10-22 11:32:00
        new CurrencyOrder(1761105000000L, 5, "Pounds") // 2025-10-22 11:50:00
).assignTimestampsAndWatermarks(
        WatermarkStrategy.<CurrencyOrder>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((order, orderTime) -> order.getOrderTime())
).setParallelism(1);

tEnv.createTemporaryView("orders", orderStream,
        $("orderTime").as("order_time"), $("amount"),  $("currency"), $("order_ltz").rowtime()
);
```
> order_ltz 是基于 orderTime 的事件时间属性字段

有了货币汇率表和订单表，我们就可以将订单金额统一转换为美元：
```java
// 执行计算
Table table = tEnv.sqlQuery("SELECT\n" +
        "  FROM_UNIXTIME(o.order_time/1000, 'yyyy-MM-dd HH:mm:ss') AS order_time, o.currency, o.amount,\n" +
        "  r.rate, FROM_UNIXTIME(r.rate_time/1000, 'yyyy-MM-dd HH:mm:ss') AS rate_time,\n" +
        "  o.amount * r.rate AS rate_amount\n" +
        "FROM orders AS o,\n" +
        "LATERAL TABLE (rates_function(order_ltz)) AS r\n" +
        "WHERE o.currency = r.currency");
// 输出
DataStream<Row> stream = tEnv.toChangelogStream(table);
stream.print();
```
输出效果如下所示：
```
+I[2025-10-22 10:32:00, Yen, 50.0, 102.0, 2025-10-22 09:00:00, 5100.0]
+I[2025-10-22 10:15:00, Euro, 2.0, 114.0, 2025-10-22 09:00:00, 228.0]
+I[2025-10-22 11:32:00, Euro, 3.0, 119.0, 2025-10-22 11:15:00, 357.0]
+I[2025-10-22 10:30:00, USD, 1.0, 1.0, 2025-10-22 09:00:00, 1.0]
+I[2025-10-22 11:50:00, Pounds, 5.0, 108.0, 2025-10-22 11:49:00, 540.0]
```
