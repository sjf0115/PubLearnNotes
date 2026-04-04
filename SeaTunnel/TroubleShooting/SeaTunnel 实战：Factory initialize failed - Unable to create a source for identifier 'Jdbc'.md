## 1. 问题

提交 SeaTunnel MySQL 到 MySQL 表数据同步任务时，遇到如下异常：
```
Exception in thread "main" org.apache.seatunnel.core.starter.exception.CommandExecuteException: SeaTunnel job executed failed
	at org.apache.seatunnel.core.starter.seatunnel.command.ClientExecuteCommand.execute(ClientExecuteCommand.java:213)
	at org.apache.seatunnel.core.starter.SeaTunnel.run(SeaTunnel.java:40)
	at org.apache.seatunnel.core.starter.seatunnel.SeaTunnelClient.main(SeaTunnelClient.java:34)
Caused by: org.apache.seatunnel.api.table.factory.FactoryException: ErrorCode:[API-06], ErrorDescription:[Factory initialize failed] - Unable to create a source for identifier 'Jdbc'.
	at org.apache.seatunnel.api.table.factory.FactoryUtil.createAndPrepareSource(FactoryUtil.java:101)
	at org.apache.seatunnel.engine.core.parse.MultipleTableJobConfigParser.parseSource(MultipleTableJobConfigParser.java:375)
	at org.apache.seatunnel.engine.core.parse.MultipleTableJobConfigParser.parse(MultipleTableJobConfigParser.java:209)
	at org.apache.seatunnel.engine.client.job.ClientJobExecutionEnvironment.getLogicalDag(ClientJobExecutionEnvironment.java:114)
	at org.apache.seatunnel.engine.client.job.ClientJobExecutionEnvironment.execute(ClientJobExecutionEnvironment.java:182)
	at org.apache.seatunnel.core.starter.seatunnel.command.ClientExecuteCommand.execute(ClientExecuteCommand.java:160)
	... 2 more
Caused by: java.lang.IllegalArgumentException
	at com.google.common.base.Preconditions.checkArgument(Preconditions.java:127)
	at org.apache.seatunnel.connectors.seatunnel.jdbc.catalog.AbstractJdbcCatalog.<init>(AbstractJdbcCatalog.java:92)
	at org.apache.seatunnel.connectors.seatunnel.jdbc.catalog.mysql.MySqlCatalog.<init>(MySqlCatalog.java:65)
	at org.apache.seatunnel.connectors.seatunnel.jdbc.catalog.mysql.MySqlCatalogFactory.createCatalog(MySqlCatalogFactory.java:53)
	at org.apache.seatunnel.api.table.factory.FactoryUtil.lambda$createOptionalCatalog$0(FactoryUtil.java:174)
	at java.base/java.util.Optional.map(Optional.java:260)
	at org.apache.seatunnel.api.table.factory.FactoryUtil.createOptionalCatalog(FactoryUtil.java:173)
	at org.apache.seatunnel.connectors.seatunnel.jdbc.utils.JdbcCatalogUtils.findCatalog(JdbcCatalogUtils.java:385)
	at org.apache.seatunnel.connectors.seatunnel.jdbc.utils.JdbcCatalogUtils.getTables(JdbcCatalogUtils.java:74)
	at org.apache.seatunnel.connectors.seatunnel.jdbc.source.JdbcSource.<init>(JdbcSource.java:57)
	at org.apache.seatunnel.connectors.seatunnel.jdbc.source.JdbcSourceFactory.lambda$createSource$0(JdbcSourceFactory.java:80)
	at org.apache.seatunnel.api.table.factory.FactoryUtil.createAndPrepareSource(FactoryUtil.java:113)
	at org.apache.seatunnel.api.table.factory.FactoryUtil.createAndPrepareSource(FactoryUtil.java:74)
	... 7 more
```

## 2. 分析

问题定位：在 AbstractJdbcCatalog 构造函数中，某个参数校验失败。常见原因有多个。

### 2.1 原因 1：缺少 catalog 相关配置

SeaTunnel 2.3.x 版本后，JDBC Source 需要额外的 catalog 配置。
