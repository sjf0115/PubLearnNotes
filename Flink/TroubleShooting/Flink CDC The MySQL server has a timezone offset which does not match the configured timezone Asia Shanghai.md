> Flink CDC 版本：3.5.0

## 1. 问题

在运行 Flink CDC 程序提交集群时遇到如下异常：
```java
2025-10-08 11:28:18
org.apache.flink.util.FlinkException: Global failure triggered by OperatorCoordinator for 'Source: products[3]' (operator feca28aff5a3958840bee985ee7de4d3).
	at org.apache.flink.runtime.operators.coordination.OperatorCoordinatorHolder$LazyInitializedCoordinatorContext.failJob(OperatorCoordinatorHolder.java:651)
	at org.apache.flink.runtime.operators.coordination.RecreateOnResetOperatorCoordinator$QuiesceableContext.failJob(RecreateOnResetOperatorCoordinator.java:259)
	at org.apache.flink.runtime.source.coordinator.SourceCoordinatorContext.failJob(SourceCoordinatorContext.java:432)
	at org.apache.flink.runtime.source.coordinator.SourceCoordinator.start(SourceCoordinator.java:233)
	at org.apache.flink.runtime.operators.coordination.RecreateOnResetOperatorCoordinator$DeferrableCoordinator.resetAndStart(RecreateOnResetOperatorCoordinator.java:433)
	at org.apache.flink.runtime.operators.coordination.RecreateOnResetOperatorCoordinator.lambda$resetToCheckpoint$7(RecreateOnResetOperatorCoordinator.java:157)
	at java.util.concurrent.CompletableFuture.uniWhenComplete(CompletableFuture.java:774)
	at java.util.concurrent.CompletableFuture$UniWhenComplete.tryFire(CompletableFuture.java:750)
	at java.util.concurrent.CompletableFuture.postComplete(CompletableFuture.java:488)
	at java.util.concurrent.CompletableFuture.complete(CompletableFuture.java:1975)
	at org.apache.flink.runtime.operators.coordination.ComponentClosingUtils.lambda$closeAsyncWithTimeout$0(ComponentClosingUtils.java:77)
	at java.lang.Thread.run(Thread.java:750)
Caused by: org.apache.flink.table.api.ValidationException: The MySQL server has a timezone offset (0 seconds ahead of UTC) which does not match the configured timezone Asia/Shanghai. Specify the right server-time-zone to avoid inconsistencies for time-related fields.
	at org.apache.flink.cdc.connectors.mysql.MySqlValidator.checkTimeZone(MySqlValidator.java:215)
	at org.apache.flink.cdc.connectors.mysql.MySqlValidator.validate(MySqlValidator.java:76)
	at org.apache.flink.cdc.connectors.mysql.source.MySqlSource.createEnumerator(MySqlSource.java:200)
	at org.apache.flink.runtime.source.coordinator.SourceCoordinator.start(SourceCoordinator.java:229)
	... 8 more

```
这个异常表明 MySQL 服务器的时区设置与 Flink CDC 配置的时区不匹配。

## 2. 分析

MySQL 服务器时区：UTC（0 时区偏移）:
```
mysql> show variables like '%time_zone%';
+------------------+--------+
| Variable_name    | Value  |
+------------------+--------+
| system_time_zone | UTC    |
| time_zone        | SYSTEM |
+------------------+--------+
2 rows in set (0.01 sec)
```
但是 Flink CDC 在没有配置 `server-time-zone` 时区参数时，默认通过 `ZoneId.systemDefault()` 获取系统时区，当前为 `Asia/Shanghai（UTC+8）`：
```java
ZoneId defaultZoneId = ZoneId.systemDefault();
// Asia/Shanghai
System.out.println(defaultZoneId);
```
综上可以知道 MySQL 服务器的时区与 Flink CDC 的时区不匹配。Flink CDC 需要正确处理时间类型字段（如 TIMESTAMP, DATETIME 等）。当时区配置不一致时，这种差异会导致：
- 时间字段在读取和写入时发生偏移
- 数据一致性受到影响
- 业务逻辑可能出现错误

## 3. 解决方案

你可以选择修改 Flink CDC 时区或者调整 MySQL 服务器时区。在这业务上要求使用 `Asia/Shanghai` 时区，选择修改 MySQL 配置：
```sql
mysql> SET GLOBAL time_zone = '+08:00';
Query OK, 0 rows affected (0.00 sec)

mysql> SET time_zone = '+08:00';
Query OK, 0 rows affected (0.00 sec)
```
修改完再次查看：
```sql
mysql> show variables like '%time_zone%';
+------------------+--------+
| Variable_name    | Value  |
+------------------+--------+
| system_time_zone | UTC    |
| time_zone        | +08:00 |
+------------------+--------+
2 rows in set (0.00 sec)

mysql> SELECT @@global.time_zone, @@session.time_zone;
+--------------------+---------------------+
| @@global.time_zone | @@session.time_zone |
+--------------------+---------------------+
| +08:00             | +08:00              |
+--------------------+---------------------+
1 row in set (0.00 sec)
```
> 需要注意的是这是临时修改，重启后失效。需要修改 my.cnf 配置文件

MySQL 8.0 及以上版本支持持久化系统变量，无需重启服务：
```sql
-- 设置全局时区并持久化
SET PERSIST time_zone = '+08:00';

-- 或者使用时区名称
SET PERSIST time_zone = 'Asia/Shanghai';
```
