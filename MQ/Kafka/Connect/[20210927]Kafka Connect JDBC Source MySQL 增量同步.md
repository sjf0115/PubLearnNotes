---
layout: post
author: smartsi
title: Kafka Connect JDBC Source MySQL 增量同步
date: 2021-09-27 21:56:00
tags:
  - Kafka

categories: Kafka
permalink: mysql-inc-with-kafka-connect-jdbc-source
---

> Kafka 版本：2.4.0

上一篇文章 [Kafka Connect JDBC Source MySQL 全量同步](http://smartsi.club/mysql-bulk-with-kafka-connect-jdbc-source.html) 中，我们只是将整个表数据导入 Kafka。这对于获取数据快照很有用，但并不是所有场景都需要批量全部同步，有时候我们可能想要获取自上次之后发生的变更以实现增量同步。JDBC Connector 提供了这样的能力，将表中自上次轮询以来发生更改的行流式传输到 Kafka 中。可以基于递增的列（例如，递增的主键）或者时间戳列（例如，上次更新的时间戳）来进行操作。Kafka Connect JDBC Source  提供了三种增量同步模式：
- incrementing
- timestamp
- timestamp+incrementing

下面我们详细介绍每一种模式。

### 1. incrementing 模式

```sql
CREATE TABLE IF NOT EXISTS `stu`(
   `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
   `stu_id` VARCHAR(100) NOT NULL,
   `stu_name` VARCHAR(100) NOT NULL,
   `gmt_create` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
   `gmt_modified` DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   PRIMARY KEY (`id` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

incrementing 模式基于表上严格递增的列来检测是否是新行。如果添加了具有新 ID 的新行，该行会被导入到 Kafka 中。需要使用 incrementing.column.name 参数指定严格递增列。如下所示使用 id 字段作为自增列：
```json
curl -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" -d '{
    "name": "jdbc_source_connector_mysql_increment",
    "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "connection.url": "jdbc:mysql://localhost:3306/kafka_connect_sample",
            "connection.user": "root",
            "connection.password": "root",
            "topic.prefix": "connect-mysql-increment-",
            "mode":"incrementing",
            "incrementing.column.name":"id",
            "catalog.pattern" : "kafka_connect_sample",
            "table.whitelist" : "stu"
        }
    }'
```

创建 Connector 成功之后如下显示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-1.png?raw=true)

在 incrementing 模式下，每次都是根据 incrementing.column.name 参数指定的列，查询大于自上次拉取的最大id：
```sql
SELECT * FROM stu
WHERE id > ?
ORDER BY id ASC
```
现在我们向 stu 数据表新添加 stu_id 分别为 00001 和 00002 的两条数据：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-2.png?raw=true)

我们在使用如下命令消费 connect-mysql-increment-stu Topic 时，会连续得到两条记录，如下图所示：
```
bin/kafka-console-consumer.sh --topic connect-mysql-increment-stu --from-beginning --bootstrap-server localhost:9092
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-3.png?raw=true)

这种模式的缺点是无法捕获行上更新操作（例如，UPDATE、DELETE）的变更，因为无法增大该行的 id。如下所示我们删除了 stud_id 为 00002 的行、修改了 stud_id 为 00001 的行以及新添加了 stu_id 为 00003 的行：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-4.png?raw=true)

但是只有新添加的 stu_id 为 00003 的行导入了 kafka：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-5.png?raw=true)

### 2. timestamp 模式

```sql
CREATE TABLE IF NOT EXISTS `stu_timestamp`(
   `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
   `stu_id` VARCHAR(100) NOT NULL,
   `stu_name` VARCHAR(100) NOT NULL,
   `gmt_create` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `gmt_modified` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   PRIMARY KEY (`id` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

timestamp 模式基于表上时间戳列来检测是否是新行或者修改的行。该列最好是随着每次写入而更新，并且值是单调递增的。需要使用 timestamp.column.name 参数指定时间戳列。如下所示使用 gmt_modified 字段作为时间戳列：
```json
curl -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" -d '{
    "name": "jdbc_source_connector_mysql_timestamp",
    "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "connection.url": "jdbc:mysql://localhost:3306/kafka_connect_sample",
            "connection.user": "root",
            "connection.password": "root",
            "topic.prefix": "connect-mysql-timestamp-",
            "mode":"timestamp",
            "timestamp.column.name":"gmt_modified",
            "catalog.pattern" : "kafka_connect_sample",
            "table.whitelist" : "stu_timestamp"
        }
    }'
```
需要注意的是时间戳列在数据表中不能设置为可 NULL，否则抛出如下异常：
```java
org.apache.kafka.connect.errors.ConnectException: Cannot make incremental queries using timestamp columns
[gmt_modified] on `kafka_connect_sample`.`stu_timestamp` because all of these columns nullable.
	at io.confluent.connect.jdbc.source.JdbcSourceTask.validateNonNullable(JdbcSourceTask.java:497)
	at io.confluent.connect.jdbc.source.JdbcSourceTask.start(JdbcSourceTask.java:168)
	at org.apache.kafka.connect.runtime.WorkerSourceTask.execute(WorkerSourceTask.java:208)
	at org.apache.kafka.connect.runtime.WorkerTask.doRun(WorkerTask.java:177)
	at org.apache.kafka.connect.runtime.WorkerTask.run(WorkerTask.java:227)
	at java.util.concurrent.Executors$RunnableAdapter.call(Executors.java:511)
	at java.util.concurrent.FutureTask.run(FutureTask.java:266)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:748)
```
> 请注意，因为 Connector 要求时间戳列为 NOT NULL，我们可以将这些列设置为 NOT NULL，或者我们可以通过设置 validate.not.null 为 false 来禁用此验证。

创建 Connector 成功之后如下显示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-6.png?raw=true)

在 timestamp 模式下，每次都是根据 timestamp.column.name 参数指定的列，查询大于自上次拉取成功的 gmt_modified：
```sql
SELECT * FROM stu_timestamp
WHERE gmt_modified > ? AND gmt_modified < ?
ORDER BY gmt_modified ASC
```
现在我们向 stu_timestamp 数据表新添加 stu_id 分别为 00001 和 00002 的两条数据：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-7.png?raw=true)

导入到 Kafka connect-mysql-increment-stu_timestamp Topic 中的记录如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-8.png?raw=true)

这种模式可以捕获行上 UPDATE 变更，同样也不能捕获 DELETE 变更：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-9.png?raw=true)

只有更新的行导入了 kafka：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-10.png?raw=true)

这种模式的缺点是可能造成数据的丢失。由于时间戳列不是唯一列字段，可能存在相同时间戳的两列或者多列，假设在导入第二条的过程中发生了崩溃，在恢复重新导入时，拥有相同时间戳的第二条以及后面几条数据都会丢失。这是因为第一条导入成功后，对应的时间戳会被记录已成功消费，恢复后会从大于该时间戳的记录开始同步。此外，也需要确保时间戳列是随着时间递增的，如果人为的修改时间戳列小于当前同步成功的最大时间戳，也会导致该变更不能同步。

### 3. timestamp+incrementing 混合模式

```sql
CREATE TABLE IF NOT EXISTS `stu_timestamp_inc`(
   `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
   `stu_id` VARCHAR(100) NOT NULL,
   `stu_name` VARCHAR(100) NOT NULL,
   `gmt_create` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `gmt_modified` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   PRIMARY KEY (`id` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

如上所述，仅使用 incrementing 或 timestamp 模式都存在缺陷。将 timestamp 和 incrementing 一起使用，可以充分利用 incrementing 模式不丢失数据的优点以及 timestamp 模式捕获更新操作变更的优点。需要使用 incrementing.column.name 参数指定严格递增列、使用 timestamp.column.name 参数指定时间戳列。如下所示使用 id 字段作为自增列、gmt_modified 字段作为时间戳列的示例：
```json
curl -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" -d '{
    "name": "jdbc_source_connector_mysql_timestamp_inc",
    "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "connection.url": "jdbc:mysql://localhost:3306/kafka_connect_sample",
            "connection.user": "root",
            "connection.password": "root",
            "topic.prefix": "connect-mysql-timestamp-inc-",
            "mode":"timestamp+incrementing",
            "timestamp.column.name":"gmt_modified",
            "incrementing.column.name":"id",
            "catalog.pattern" : "kafka_connect_sample",
            "table.whitelist" : "stu_timestamp_inc"
        }
    }'
```
创建 Connector 成功之后如下显示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-11.png?raw=true)

在 timestamp+incrementing 模式下，需要根据自增列 id 和时间戳列 gmt_modified 一起来决定拉取哪些数据：
```sql
SELECT * FROM stu_timestamp_inc
WHERE gmt_modified < ?
  AND ((gmt_modified = ? AND id > ?) OR gmt_modified > ?)
ORDER BY gmt_modified, id ASC
```

现在我们向 stu_timestamp_inc 数据表新添加 stu_id 分别为 00001 和 00002 的两条数据：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-12.png?raw=true)

导入到 Kafka connect-mysql-timestamp-inc-stu_timestamp_inc Topic 中的记录如下图所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-13.png?raw=true)

这种模式可以捕获行上 UPDATE 变更，还是也不能捕获 DELETE 变更：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-14.png?raw=true)

只有更新的行导入了 kafka：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/mysql-inc-with-kafka-connect-jdbc-source-15.png?raw=true)

### 4. 总结

incrementing 模式的缺点是无法捕获行上更新操作（例如，UPDATE、DELETE）、timestamp 模式存在丢数据的风险。timestamp+incrementing 混合模式充分利用了各自的优点，做到既能捕捉 UPDATE 操作变更，也能做到不丢数据。这三种模式对开发者比较友好，易配置和使用，但这三种模式还存在一些问题：
- 无法获取 DELETE 操作变更，因为这三种模式都是使用 SELECT 查询来检索数据，并没有复杂的机制来检测已删除的行。
- 由于最需要增量时间戳，处理历史遗留数据时需要额外添加时间戳列。如果无法更新 Schema，则不能使用本文中的模式。
- 因为需要不断地运行查询，因此会对数据库产生一些负载。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- [Kafka Connect JDBC Source Connector](https://turkogluc.com/kafka-connect-jdbc-source-connector/)

相关推荐：
- [Kafka Connect 构建大规模低延迟的数据管道](http://smartsi.club/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines.html)
- [Kafka Connect 如何构建实时数据管道](http://smartsi.club/how-to-build-a-pipeline-with-kafka-connect.html)
- [Kafka Connect JDBC Source MySQL 全量同步](http://smartsi.club/mysql-bulk-with-kafka-connect-jdbc-source.html)
