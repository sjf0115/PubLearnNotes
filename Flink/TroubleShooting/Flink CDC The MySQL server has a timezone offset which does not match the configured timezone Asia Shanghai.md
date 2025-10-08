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
这个异常表明 MySQL 服务器的时区设置与 Flink CDC 配置的时区不匹配，可能导致时间相关字段处理出现不一致。

## 2. 分析

Flink CDC 需要正确处理时间类型字段（如 TIMESTAMP, DATETIME 等）。当时区配置不一致时：
- MySQL 服务器时区：UTC（0 时区偏移）
- Flink CDC 配置时区：Asia/Shanghai（UTC+8）

这种差异会导致：
- 时间字段在读取和写入时发生偏移
- 数据一致性受到影响
- 业务逻辑可能出现错误




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
