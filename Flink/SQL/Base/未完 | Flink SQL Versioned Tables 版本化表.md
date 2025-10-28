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

### 4.1 版本化表数据源

可以将定义成变更日志的 Source 或 Format 的任何表隐式定义为版本表。示例包括 upsert Kafka 源以及数据库变更日志格式，如 debezium 和 canal。如上所述，惟一的附加要求是 CREATE 表语句必须包含 PRIMARY KEY 和事件时间属性。

#### 4.1.1 基于 CDC 数据源创建

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

#### 4.1.2 基于变更日志流创建

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



### 4.2 版本化表视图

如果底层查询包含唯一键约束和事件时间属性，Flink 还支持定义版本化视图。假设有一个 Append-only 的汇率表：
```sql
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
currency_rates 表包含每种货币相对于美元的汇率记录，并且每次汇率变化时都会接收一条新记录。JSON 格式不支持原生的变更日志 Changelog 语义，因此 Flink 只能以 Append-only 模式读取此表。
```
(changelog kind) update_time   currency   rate
================ ============= =========  ====
+(INSERT)        09:00:00      Yen        102
+(INSERT)        09:00:00      Euro       114
+(INSERT)        09:00:00      USD        1
+(INSERT)        11:15:00      Euro       119
+(INSERT)        11:49:00      Pounds     108
```
Flink 将每一行解释为对表的一次插入，这意味着我们无法在 currency 字段上定义主键。但是对我们（查询开发者）来说很清楚，这个表包含了定义版本表所需的所有信息。Flink 可以通过定义一个去重查询，将此表重新解释为一个版本表，该查询生成一个带有推断的主键 `currency` 和事件时间 `update_time` 的有序变更日志流。

```sql
-- 定义版本化视图
CREATE VIEW versioned_rates AS              
SELECT currency, rate, update_time              -- (1) `update_time` keeps the event time
  FROM (
      SELECT *,
      ROW_NUMBER() OVER (PARTITION BY currency  -- (2) the inferred unique key `currency` can be a primary key
         ORDER BY update_time DESC) AS rownum
      FROM currency_rates)
WHERE rownum = 1;

-- versioned_rates 视图产生如下 Changelog
(changelog kind) update_time currency   rate
================ ============= =========  ====
+(INSERT)        09:00:00      Yen        102
+(INSERT)        09:00:00      Euro       114
+(INSERT)        09:00:00      USD        1
+(UPDATE_AFTER)  10:45:00      Euro       116
+(UPDATE_AFTER)  11:15:00      Euro       119
+(INSERT)        11:49:00      Pounds     108
```
Flink 有一个特殊的优化步骤，可以将此查询高效地转换为可用于后续查询的版本化表。一般来说，具有以下格式的查询结果会产生一个版本化表：
```sql
SELECT [column_list]
FROM (
   SELECT [column_list],
     ROW_NUMBER() OVER ([PARTITION BY col1[, col2...]]
       ORDER BY time_attr DESC) AS rownum
   FROM table_name)
WHERE rownum = 1
```
参数规范
- `ROW_NUMBER()`：为每一行分配一个唯一的、连续的数字，从1开始。
- `PARTITION BY col1[, col2...]`：指定分区列，即去重键。这些列形成后续版本化表的主键。
- `ORDER BY time_attr DESC`：指定排序列，必须是一个时间属性。
- `WHERE rownum = 1`：`rownum = 1` 是 Flink 识别此查询旨在生成版本化表所必需的。



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

> https://blog.csdn.net/bluishglc/article/details/136392632
> https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/table/concepts/versioned_tables/
