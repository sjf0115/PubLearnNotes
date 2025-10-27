## 1. 什么是版本表？

版本表 Versioned Tables 是 Apache Flink 中处理时态数据的一个核心概念。版本表是一种特殊类型的更新表，代表一个随着时间推移不断变化、且每个版本都有特定有效时间范围的表。这种表能够追踪数据在整个生命周期中的变化历史，让我们能够查询数据在任意时间点的状态。


核心特征
- 版本追踪：记录每个数据条目的多个版本
- 时间旅行：支持查询历史任意时间点的数据状态
- 时态关联：能够与其他表进行基于时间点的关联

## 2. 为什么需要版本表？

在实际业务场景中，数据是动态变化的。如下所示是商品价格变化历史：

| 时间点 | 商品ID | 价格 | 备注 |
| :------------- | :------------- | :------------- | :------------- |
| 2024-01-01 | P001 | 100.0  | 版本1 |
| 2024-01-15 | P001 | 95.0   | 版本2 |
| 2024-02-01 | P001 | 110.0  | 版本3 |

如果用户查询 2024-01-20 时商品 P001 的价格是多少，期望得到的答案不是 110.0 而是 95.0（版本2）。

> 没有版本表 Versioned Tables，这种时间旅行查询将极其复杂。

## 3. 核心概念

Flink SQL 可以在任何带有 PRIMARY KEY 约束和时间属性的动态表上定义版本表。意味着每个版本表必须定义：
- 主键：标识唯一实体的字段
- 时间属性：版本时间，定义版本有效性的时间属性

Flink 中的主键约束意味着表或视图的一列或者一组列是唯一且非空的。更新表上的主键语义意味着特定键（INSERT/UPDATE/DELETE）的实体化更改表示随时间变化对单行的更改。更新表上的time属性定义每次更改发生的时间。


总之，Flink 可以跟踪一段时间内对一行的更改，并维护每个值对该键有效的时间段。



假设一个表跟踪商店中不同产品的价格。

```
(changelog kind)  update_time  product_id product_name price
================= ===========  ========== ============ =====
+(INSERT)         00:01:00     p_001      scooter      11.11
+(INSERT)         00:02:00     p_002      basketball   23.11
-(UPDATE_BEFORE)  12:00:00     p_001      scooter      11.11
+(UPDATE_AFTER)   12:00:00     p_001      scooter      12.99
-(UPDATE_BEFORE)  12:00:00     p_002      basketball   23.11
+(UPDATE_AFTER)   12:00:00     p_002      basketball   19.99
-(DELETE)         18:00:00     p_001      scooter      12.99
```
考虑到这些变化，我们跟踪了一辆滑板车的价格是如何随时间变化的。在 00:01:00 添加到目录时，初始价格为 11.11 美元。然后价格在 12:00:00 上升到12.99美元，然后在 18:00:00 从目录中删除。

如果我们在不同时间查询不同产品的价格，我们将检索到不同的结果。在 10:00:00 查询产品价格如下：

```
update_time  product_id product_name price
===========  ========== ============ =====
00:01:00     p_001      scooter      11.11
00:02:00     p_002      basketball   23.11
```

而在 13:00:00 查询，产品价格发生了变化：
```
update_time  product_id product_name price
===========  ========== ============ =====
12:00:00     p_001      scooter      12.99
12:00:00     p_002      basketball   19.99
```


## 4. 创建版本表

可以将定义成变更日志的 Source 或 Format 的任何表隐式定义为版本表。示例包括 upsert Kafka 源以及数据库变更日志格式，如 debezium 和 canal。如上所述，惟一的附加要求是 CREATE 表语句必须包含 PRIMARY KEY 和事件时间属性。

### 4.1 基于 CDC 数据源创建

```sql
-- 使用 MySQL CDC 连接器创建版本化表
CREATE TABLE products (
    product_id STRING,
    product_name STRING,
    price DECIMAL(10, 2),
    update_time TIMESTAMP_LTZ(3),
    PRIMARY KEY (product_id) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'localhost',
    'port' = '3306',
    'username' = 'flink_user',
    'password' = 'flink_pwd',
    'database-name' = 'ecommerce',
    'table-name' = 'products'
);

-- 创建版本化视图
CREATE VIEW versioned_products AS
SELECT
    product_id,
    product_name,
    price,
    update_time
FROM products
FOR SYSTEM_TIME AS OF update_time;
```

### 4.2 基于变更日志流创建

```sql
-- 假设有产品变更数据流
CREATE TABLE product_changelog (
    product_id STRING,
    product_name STRING,
    price DECIMAL(10, 2),
    update_time TIMESTAMP_LTZ(3),
    op_type STRING, -- 'INSERT', 'UPDATE', 'DELETE'
    PRIMARY KEY (product_id) NOT ENFORCED
) WITH (
    'connector' = 'kafka',
    'topic' = 'product-changelog',
    'properties.bootstrap.servers' = 'localhost:9092',
    'format' = 'debezium-json'
);
```



```sql
CREATE TABLE products (
	product_id    STRING,
	product_name  STRING,
	price         DECIMAL(32, 2),
	update_time   TIMESTAMP(3) METADATA FROM 'value.source.timestamp' VIRTUAL,
	PRIMARY KEY (product_id) NOT ENFORCED,
	WATERMARK FOR update_time AS update_time
) WITH (...);
```

如果底层查询包含唯一键约束和事件时间属性，Flink 还支持定义版本化视图。想象一个仅能附加的汇率表。

```
CREATE TABLE currency_rates (
	currency      STRING,
	rate          DECIMAL(32, 10),
	update_time   TIMESTAMP(3),
	WATERMARK FOR update_time AS update_time
) WITH (
	'connector' = 'kafka',
	'topic'	    = 'rates',
	'properties.bootstrap.servers' = 'localhost:9092',
	'format'    = 'json'
);
```

## 5. Versioned Tables 的查询操作

### 5.1 时间旅行查询 (Time Travel)

```
-- 查询特定时间点的产品信息
SELECT *
FROM versioned_products
FOR SYSTEM_TIME AS OF TIMESTAMP '2024-01-20 10:00:00'
WHERE product_id = 'P001';

-- 使用相对时间
SELECT *
FROM versioned_products  
FOR SYSTEM_TIME AS OF CURRENT_TIMESTAMP - INTERVAL '1' HOUR
WHERE product_id IN ('P001', 'P002');
```

### 5.2 时态表关联 (Temporal Table Join)

```sql
-- 订单表
CREATE TABLE orders (
    order_id STRING,
    product_id STRING,
    quantity INT,
    order_time TIMESTAMP_LTZ(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'orders',
    'properties.bootstrap.servers' = 'localhost:9092',
    'format' = 'json'
);

-- 时态表关联：获取下单时刻的产品价格
SELECT
    o.order_id,
    o.product_id,
    o.quantity,
    o.order_time,
    p.product_name,
    p.price AS price_at_order_time
FROM orders o
LEFT JOIN versioned_products FOR SYSTEM_TIME AS OF o.order_time AS p
ON o.product_id = p.product_id;
```

### 5.3 版本变化分析

```sql
-- 分析价格变化趋势
WITH price_changes AS (
    SELECT
        product_id,
        price,
        update_time,
        LAG(price) OVER (PARTITION BY product_id ORDER BY update_time) as prev_price
    FROM (
        SELECT DISTINCT product_id, price, update_time
        FROM product_changelog
        WHERE op_type IN ('INSERT', 'UPDATE')
    )
)
SELECT
    product_id,
    update_time as change_time,
    price as current_price,
    prev_price,
    ((price - prev_price) / prev_price) * 100 as change_percentage
FROM price_changes
WHERE prev_price IS NOT NULL;
```

> https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/table/concepts/versioned_tables/
