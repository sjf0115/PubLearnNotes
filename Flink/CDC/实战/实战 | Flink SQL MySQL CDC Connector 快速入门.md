在实时数据处理场景中，如何将 MySQL 数据库的变更数据实时同步到下游系统，一直是一个核心需求。传统方案通常需要部署 Debezium + Kafka Connect 等一套复杂的 CDC 管道，运维成本高、链路长。Flink SQL MySQL CDC Connector 提供了一种更轻量级的方案：无需额外部署组件，Flink 直接连接 MySQL 读取 binlog，将数据变更以 Changelog 流的形式接入 Flink SQL 生态。

本文作为 Flink SQL MySQL CDC 系列的第一篇，将从零开始介绍 MySQL CDC Connector 的基本概念、环境准备和快速入门，帮助你快速搭建起第一个 CDC 实时同步任务。

> 本文基于 Flink 1.13 + flink-sql-connector-mysql-cdc 2.2.1 版本。

## 1. MySQL CDC Connector 简介

### 1.1 什么是 MySQL CDC Connector

MySQL CDC Connector 是 Flink CDC 项目提供的一个 Source Connector，它基于 Debezium 引擎实现，能够：
- **全量读取**：首次启动时，对 MySQL 表执行一次全量快照（Snapshot），捕获表中已有的所有数据
- **增量读取**：快照完成后，自动切换为增量模式，持续消费 MySQL 的 binlog，捕获后续的 INSERT、UPDATE、DELETE 操作

整个过程对 Flink SQL 用户完全透明——你只需在 DDL 中声明 `'connector' = 'mysql-cdc'`，Flink 就能像读一张普通表一样，实时获取 MySQL 的数据变更。

### 1.2 核心优势

与传统 CDC 方案（Debezium → Kafka Connect → Kafka → Flink）相比，Flink MySQL CDC Connector 有以下优势：

| 对比维度 | 传统方案 | Flink CDC 方案 |
|:---------|:---------|:--------------|
| 组件数量 | Debezium + Kafka Connect + Kafka + Flink | 仅 Flink |
| 链路延迟 | 多跳中转，秒级~分钟级 | 直连 binlog，毫秒级~秒级 |
| 运维成本 | 多组件运维、版本兼容 | 单组件，SQL 声明式 |
| 开发门槛 | 需配置多个系统 | 纯 SQL，无需编码 |
| 一致性 | 需各环节配合保证 | 内置 Exactly-Once 语义 |

### 1.3 适用场景

- **实时数仓同步**：将业务 MySQL 的数据实时同步到数据仓库（如 Hive、ClickHouse、StarRocks）
- **实时物化视图**：基于 CDC 数据构建实时聚合视图，替代定时批量计算
- **异构数据库迁移**：MySQL → PostgreSQL / Elasticsearch / HBase 等异构存储的在线迁移
- **实时数据分发**：将 MySQL 变更实时推送到 Kafka，供多个下游消费

## 2. 工作原理概述

### 2.1 两阶段模型

MySQL CDC Connector 的工作过程分为两个阶段：

```
┌─────────────────────────────────────────────────────┐
│                  MySQL CDC Connector                  │
│                                                       │
│  阶段1: Snapshot Phase          阶段2: Binlog Phase  │
│  ┌───────────────────┐         ┌──────────────────┐  │
│  │  SELECT * FROM t  │  ─────→ │  读取 binlog     │  │
│  │  (全量快照)        │         │  (增量变更)       │  │
│  └───────────────────┘         └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

- **Snapshot Phase（全量快照阶段）**：对目标表执行全表扫描（SELECT），将已有数据全部读取出来，每条记录标记为 `+I`（INSERT）
- **Binlog Phase（增量读取阶段）**：快照完成后，从 binlog 的相应位点开始持续消费增量变更

### 2.2 Changelog 事件映射

MySQL 的 binlog 操作会被映射为 Flink 的 Changelog 事件：

| MySQL 操作 | Flink RowKind | 含义 |
|:-----------|:---:|:-----|
| INSERT | `+I` | 新增一行 |
| UPDATE | `-U` + `+U` | 先回撤旧值，再发送新值 |
| DELETE | `-D` | 删除一行 |

这使得下游算子（如 JOIN、GROUP BY）能够正确处理 MySQL 的 CRUD 操作，维护实时计算结果的准确性。

### 2.3 整体架构

```
MySQL (binlog)
     │
     ▼
┌─────────────────┐     ┌────────────────┐     ┌──────────┐
│ CDC Source       │────→│ Flink SQL 算子  │────→│  Sink    │
│ (mysql-cdc)     │     │ (Filter/Join/  │     │ (Kafka/  │
│                 │     │  Aggregate...) │     │  JDBC/ES)│
└─────────────────┘     └────────────────┘     └──────────┘
```

Flink 直连 MySQL，无需中间消息队列。CDC Source 产生的 Changelog 流可以直接参与 Flink SQL 的各种计算，最终写入到目标 Sink。

## 3. 前置条件

### 3.1 开启 MySQL binlog

MySQL CDC Connector 依赖 binlog 来捕获增量变更，因此必须确保 MySQL 已正确开启 binlog。

**第一步**：修改 MySQL 配置文件（`my.cnf` 或 `my.ini`）：

```ini
[mysqld]
# 开启 binlog
log_bin = mysql-bin
# 必须使用 ROW 格式（CDC 要求）
binlog_format = ROW
# 记录完整的行数据（包含所有列，而非仅变更列）
binlog_row_image = FULL
# server-id 必须唯一（集群中每个 MySQL 实例不同）
server-id = 1
```

**第二步**：重启 MySQL 后验证配置：

```sql
-- 验证 binlog 是否开启
SHOW VARIABLES LIKE 'log_bin';
-- 预期结果：log_bin = ON

-- 验证 binlog 格式
SHOW VARIABLES LIKE 'binlog_format';
-- 预期结果：binlog_format = ROW

-- 验证行镜像模式
SHOW VARIABLES LIKE 'binlog_row_image';
-- 预期结果：binlog_row_image = FULL
```

> **为什么必须是 ROW 格式？** STATEMENT 格式只记录 SQL 语句，无法还原具体的行数据变更；MIXED 格式不稳定。只有 ROW 格式才会逐行记录变更前后的完整数据，CDC 才能正确解析。

### 3.2 创建 CDC 用户并授权

建议为 CDC 创建一个专用的 MySQL 用户，避免使用 root 账号：

```sql
-- 创建用户
CREATE USER 'flink_cdc'@'%' IDENTIFIED BY '12345678';

-- 授予必要权限
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT
ON *.* TO 'flink_cdc'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

各权限的用途说明：

| 权限 | 用途 |
|:-----|:-----|
| `SELECT` | 全量快照阶段读取表数据 |
| `RELOAD` | 执行 `FLUSH` 操作（获取 binlog 位点） |
| `SHOW DATABASES` | 获取数据库列表 |
| `REPLICATION SLAVE` | 读取 binlog 数据 |
| `REPLICATION CLIENT` | 获取 binlog 文件列表和当前位点 |

### 3.3 server-id 说明

MySQL 的 `server-id` 用于在主从复制中唯一标识每个实例。CDC Connector 会模拟一个 MySQL Slave 来读取 binlog，因此需要一个不与其他实例冲突的 `server-id`。

在 Flink CDC 的 DDL 中可以通过 `'server-id' = '5401-5404'` 指定一个范围，Connector 会自动从中选取。如果不指定，默认会随机生成。

## 4. 环境准备

**下载 Flink 1.13**：

```bash
wget https://archive.apache.org/dist/flink/flink-1.13.6/flink-1.13.6-bin-scala_2.11.tgz
tar -xzf flink-1.13.6-bin-scala_2.11.tgz
cd flink-1.13.6
```

**下载 CDC Connector JAR**：

```bash
wget -P lib/ https://repo1.maven.org/maven2/com/ververica/flink-sql-connector-mysql-cdc/2.2.1/flink-sql-connector-mysql-cdc-2.2.1.jar
```

**启动 Flink 集群**：

```bash
./bin/start-cluster.sh
```

**启动 SQL Client**：

```bash
./bin/sql-client.sh
```

### 4.3 准备示例数据

进入 MySQL 并创建示例数据：
```sql
CREATE DATABASE IF NOT EXISTS test;
USE test;

-- 订单表
CREATE TABLE orders (
  order_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  order_date DATETIME NOT NULL,
  customer_name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 5) NOT NULL,
  product_id INT NOT NULL,
  order_status BOOLEAN NOT NULL
) AUTO_INCREMENT = 10001;

-- 插入初始数据
INSERT INTO orders VALUES
  (default, '2023-01-15 10:08:22', '张三', 50.50, 102, false),
  (default, '2023-01-15 10:11:09', '李四', 15.00, 105, false),
  (default, '2023-01-15 12:00:30', '王五', 25.25, 106, false);
```

## 5. 快速入门

### 5.1 设置 Checkpoint

在 Flink SQL Client 中首先开启 Checkpoint，这是 CDC Connector 保证 Exactly-Once 语义的前提：

```sql
-- 每 3 秒做一次 checkpoint
Flink SQL> SET 'execution.checkpointing.interval' = '3s';
-- 2. 设置 tableau 结果模式
Flink SQL> SET 'sql-client.execution.result-mode' = 'tableau';
```

### 5.2 创建 CDC Source 表

```sql
Flink SQL> CREATE TABLE orders (
    order_id INT,
    order_date TIMESTAMP(0),
    customer_name STRING,
    price DECIMAL(10, 5),
    product_id INT,
    order_status BOOLEAN,
    PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'localhost',
    'port' = '3306',
    'username' = 'root',
    'password' = 'root',
    'database-name' = 'test',
    'table-name' = 'orders',
    'scan.startup.mode' = 'initial'  -- 默认值，可省略
);
```

关键点说明：
- `'connector' = 'mysql-cdc'`：指定使用 MySQL CDC Connector
- `PRIMARY KEY (order_id) NOT ENFORCED`：必须声明主键，CDC 依赖主键来标识行
- `NOT ENFORCED`：Flink 不强制检查主键唯一性约束，仅作为语义声明

### 5.3 查询 CDC 数据

执行查询，观察实时 tableau 输出：
```sql
Flink SQL> SELECT * FROM orders;
```

首次执行会进入 Snapshot Phase，输出当前表中的全量数据（均为 `+I` 事件）：
```
+----+-------------+---------------------+------------------+--------------+-------------+--------------+
| op |    order_id |          order_date |    customer_name |        price |  product_id | order_status |
+----+-------------+---------------------+------------------+--------------+-------------+--------------+
| +I |       10002 | 2023-01-15 10:11:09 |             李四 |     15.00000 |         105 |        false |
| +I |       10001 | 2023-01-15 10:08:22 |             张三 |     50.50000 |         102 |        false |
| +I |       10003 | 2023-01-15 12:00:30 |             王五 |     25.25000 |         106 |        false |
```

### 5.4 实时捕获 MySQL 变更

保持上面的查询运行，打开另一个 MySQL 客户端窗口执行变更操作：

**INSERT - 新增订单**：
```sql
INSERT INTO orders VALUES (default, '2023-01-15 14:30:00', '赵六', 88.00, 101, false);
```

Flink 端实时输出：
```
| +I |       10004 | 2023-01-15 14:30:00 |    赵六 |     88.00000 |         101 |        false |
```

**UPDATE - 更新订单状态**：
```sql
UPDATE orders SET order_status = true WHERE order_id = 10001;
```

Flink 端实时输出：
```
| -U |       10001 | 2023-01-15 10:08:22 |    张三 |     50.50000 |         102 |        false |
| +U |       10001 | 2023-01-15 10:08:22 |    张三 |     50.50000 |         102 |         true |
```

**DELETE - 删除订单**：
```sql
DELETE FROM orders WHERE order_id = 10003;
```

Flink 端实时输出：
```
| -D |       10003 | 2023-01-15 12:00:30 |    王五 |     25.25000 |         106 |        false |
```

### 5.5 Changelog 事件解读

通过上面的实验，可以直观看到 MySQL 操作与 Flink Changelog 事件的映射关系：

| 操作 | Flink 输出 | 说明 |
|:-----|:-----------|:-----|
| 快照读取 | `+I (全量数据)` | 首次启动时读取表中已有数据 |
| INSERT | `+I (新行)` | 新增一行 |
| UPDATE | `-U (旧值)` + `+U (新值)` | 先撤回旧值，再发送新值 |
| DELETE | `-D (被删行)` | 标记删除 |

这正是 Flink SQL Changelog 机制的体现——通过 `+I / -U / +U / -D` 四种事件类型，完整表达了 MySQL 表的所有状态变更。下游算子（如 GROUP BY、JOIN）能够基于这些事件正确维护计算结果。

## 6. 总结

本文介绍了 Flink SQL MySQL CDC Connector 的基本概念和快速入门：

- MySQL CDC Connector 基于 Debezium 引擎，通过「全量快照 + 增量 binlog」两阶段模型实现实时数据同步
- 前置条件包括：MySQL 开启 ROW 格式的 binlog、创建具有 REPLICATION 权限的用户
- 通过简单的 SQL DDL 声明即可创建 CDC Source 表，无需编写代码
- MySQL 的 INSERT / UPDATE / DELETE 操作分别映射为 Flink 的 +I / -U+U / -D 事件

> 参考资料：
> - [Flink CDC 官方文档 - MySQL CDC Connector](https://ververica.github.io/flink-cdc-connectors/release-2.2/content/connectors/mysql-cdc.html)
> - [Debezium MySQL Connector](https://debezium.io/documentation/reference/1.6/connectors/mysql.html)
