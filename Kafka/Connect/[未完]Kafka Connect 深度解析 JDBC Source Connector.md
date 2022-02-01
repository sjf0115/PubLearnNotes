

人们希望与 Apache Kafka® 进行的最常见的集成之一是从数据库中获取数据。这是因为关系数据库是一个丰富的事件源。数据库中的现有数据以及对该数据的任何变更都可以流式传输到 Kafka Topic 中。从那里，这些事件可用于驱动应用程序，流式传输到其他数据存储（例如搜索副本或缓存）并流式传输到存储以进行分析。

实现这个需求有很多种做法，在这里，我们主要深入研究 Kafka Connect 的 JDBC Connector。下面将会展示如何配置以及在此过程中提供一些故障排除技巧。

### 1. 简介

Kafka Connect 的 JDBC Connector 包含在 Confluent Platform 中，也可以与 Confluent Hub 分开安装。JDBC Connector 能够将数据（Source）从数据库导入 Kafka，并将数据（Sink）从 Kafka Topic 导出到数据库。几乎所有关系数据库都提供了 JDBC 驱动程序，包括 Oracle、Microsoft SQL Server、DB2、MySQL 和 Postgres。

![](1)

我们将从最简单的 Kafka Connect 配置开始，然后在此基础上进行搭建。在这里我们以 MySQL 数据库为例。数据库有两个 schema，每个 schema 都有几个表：
```
mysql> SELECT table_schema, table_name FROM INFORMATION_SCHEMA.tables WHERE TABLE_SCHEMA != 'information_schema';
+--------------+--------------+
| TABLE_SCHEMA | TABLE_NAME   |
+--------------+--------------+
| demo         | accounts     |
| demo         | customers    |
| demo         | transactions |
| security     | firewall     |
| security     | log_events   |
+--------------+--------------+
```

### 2. 安装 Connect Plugins


### 2. JDBC 驱动

在开始配置之前，我们需要确保 Kafka Connect 可以连接到数据库，这需要通过 JDBC 驱动程序来保证。具体可以参考这个[视频](https://www.youtube.com/watch?v=vI_L9irU9Pc) 。如果使用的是 SQLite 或 Postgres，那么驱动程序已经包含在内，我们可以跳过这一步。对于其他数据库，我们需要将相关的 JDBC 驱动 JAR 放在与 kafka-connect-jdbc JAR 本身相同的文件夹中。此文件夹的标准位置是：



### 配置

#### Database

connection.url：JDBC 连接 URL。
connection.user：JDBC 连接账号。
connection.password：JDBC 连接密码。
connection.attempts：检索有效 JDBC 连接的最大尝试次数。必须是正整数。默认值为 3。
connection.backoff.ms：连接尝试之间的间隔时间（以毫秒为单位）。默认值为 10000。
catalog.pattern：从数据库中获取表元数据的 Catalog 范式。
table.whitelist：需要拷贝的表列表。如果设置此参数，则不需要设置 table.blacklist。使用逗号分隔指定多个表（例如，table.whitelist："User, Address, Email"）。
table.blacklist：不需要拷贝的表列表。如果设置此参数，则不需要设置 table.whitelist。使用逗号分隔指定多个表（例如，table.blacklist："User, Address, Email"）。
schema.pattern：从数据库中获取表元数据的 Schema 模式。
numeric.mapping：按精度映射 NUMERIC 值，并可选择缩放到整数或小数类型。
dialect.name：Connector 使用到的数据库方言名称。默认情况下，这是空的，Connector 会根据 JDBC 连接 URL 自动确定方言。如果您想覆盖该行为并使用特定方言，请使用此选项。

#### mode

每次轮询时更新表的模式：
- bulk：每次轮询时批量加载整个表的数据
- timestamp：基于每个表上严格递增的列来检测新行。请注意，这不会检测对现有行的修改或删除。
- incrementing：使用时间戳（或类似时间戳）列来检测新的以及修改过的行。假设列随着每次写入而更新，并且值是单调递增的，但不一定是唯一的。
- timestamp+incrementing：使用两列：一个时间戳列检测新的和修改的行；一个严格递增的列，它为更新提供一个全局唯一的 ID，这样每一行都可以被分配一个唯一的流偏移量。


incrementing.column.name：严格递增列的名称，用于检测是否是新行。如果该参数为空值表示应通过查找自增列来自动检测是一列。该列可能为 NULL。
timestamp.column.name：以逗号分隔时间戳列，用于使用 COALESCE SQL 函数检测是新行还是修改行。每次轮询都会发现第一个非空时间戳值大于所看到的最大先前时间戳值的行。 至少一列不能为空。
timestamp.initial：用于使用时间戳标准的初始查询的纪元时间戳。 使用 -1 来使用当前时间。 如果未指定，将检索所有数据。
validate.non.null：




https://docs.confluent.io/kafka-connect-jdbc/current/source-connector/source_config_options.html#jdbc-source-configs











原文:[Kafka Connect Deep Dive – JDBC Source Connector](https://www.confluent.fr/blog/kafka-connect-deep-dive-jdbc-source-connector/)
