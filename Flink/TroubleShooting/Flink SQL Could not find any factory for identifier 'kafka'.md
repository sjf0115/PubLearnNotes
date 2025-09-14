> Flink: 1.13.6

## 1. 问题

在运行从 Kafka 中读取数据的 Flink SQL 时，遇到如下异常：
```java
The program finished with the following exception:

org.apache.flink.client.program.ProgramInvocationException: The main method caused an error: Unable to create a source for reading table 'default_catalog.default_database.shop_sales'.

Table options are:

'connector'='kafka'
'format'='json'
'json.fail-on-missing-field'='true'
'json.ignore-parse-errors'='false'
'properties.bootstrap.servers'='localhost:9092'
'properties.group.id'='shop_sales'
'scan.startup.mode'='latest-offset'
'topic'='shop_sales'
 at org.apache.flink.client.program.PackagedProgram.callMainMethod(PackagedProgram.java:372)
 at org.apache.flink.client.program.PackagedProgram.invokeInteractiveModeForExecution(PackagedProgram.java:222)
 at org.apache.flink.client.ClientUtils.executeProgram(ClientUtils.java:114)
 at org.apache.flink.client.cli.CliFrontend.executeProgram(CliFrontend.java:812)
 at org.apache.flink.client.cli.CliFrontend.run(CliFrontend.java:246)
 at org.apache.flink.client.cli.CliFrontend.parseAndRun(CliFrontend.java:1054)
 at org.apache.flink.client.cli.CliFrontend.lambda$main$10(CliFrontend.java:1132)
 at org.apache.flink.runtime.security.contexts.NoOpSecurityContext.runSecured(NoOpSecurityContext.java:28)
 at org.apache.flink.client.cli.CliFrontend.main(CliFrontend.java:1132)
Caused by: org.apache.flink.table.api.ValidationException: Unable to create a source for reading table 'default_catalog.default_database.shop_sales'.

Table options are:

'connector'='kafka'
'format'='json'
'json.fail-on-missing-field'='true'
'json.ignore-parse-errors'='false'
'properties.bootstrap.servers'='localhost:9092'
'properties.group.id'='shop_sales'
'scan.startup.mode'='latest-offset'
'topic'='shop_sales'
 at org.apache.flink.table.factories.FactoryUtil.createTableSource(FactoryUtil.java:137)
 at org.apache.flink.table.planner.plan.schema.CatalogSourceTable.createDynamicTableSource(CatalogSourceTable.java:116)
 at org.apache.flink.table.planner.plan.schema.CatalogSourceTable.toRel(CatalogSourceTable.java:82)
 at org.apache.calcite.sql2rel.SqlToRelConverter.toRel(SqlToRelConverter.java:3585)
 at org.apache.calcite.sql2rel.SqlToRelConverter.convertIdentifier(SqlToRelConverter.java:2507)
 at org.apache.calcite.sql2rel.SqlToRelConverter.convertFrom(SqlToRelConverter.java:2144)
 at org.apache.calcite.sql2rel.SqlToRelConverter.convertFrom(SqlToRelConverter.java:2093)
 at org.apache.calcite.sql2rel.SqlToRelConverter.convertFrom(SqlToRelConverter.java:2050)
 at org.apache.calcite.sql2rel.SqlToRelConverter.convertSelectImpl(SqlToRelConverter.java:663)
 at org.apache.calcite.sql2rel.SqlToRelConverter.convertSelect(SqlToRelConverter.java:644)
 at org.apache.calcite.sql2rel.SqlToRelConverter.convertQueryRecursive(SqlToRelConverter.java:3438)
 at org.apache.calcite.sql2rel.SqlToRelConverter.convertQuery(SqlToRelConverter.java:570)
 at org.apache.flink.table.planner.calcite.FlinkPlannerImpl.org$apache$flink$table$planner$calcite$FlinkPlannerImpl$$rel(FlinkPlannerImpl.scala:169)
 at org.apache.flink.table.planner.calcite.FlinkPlannerImpl.rel(FlinkPlannerImpl.scala:161)
 at org.apache.flink.table.planner.operations.SqlToOperationConverter.toQueryOperation(SqlToOperationConverter.java:989)
 at org.apache.flink.table.planner.operations.SqlToOperationConverter.convertSqlQuery(SqlToOperationConverter.java:958)
 at org.apache.flink.table.planner.operations.SqlToOperationConverter.convert(SqlToOperationConverter.java:283)
 at org.apache.flink.table.planner.operations.SqlToOperationConverter.convertSqlInsert(SqlToOperationConverter.java:603)
 at org.apache.flink.table.planner.operations.SqlToOperationConverter.convert(SqlToOperationConverter.java:272)
 at org.apache.flink.table.planner.delegation.ParserImpl.parse(ParserImpl.java:101)
 at org.apache.flink.table.api.internal.TableEnvironmentImpl.executeSql(TableEnvironmentImpl.java:724)
 at com.flink.example.sql.funciton.over.RowsOverWindowExample.main(RowsOverWindowExample.java:59)
 at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
 at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
 at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
 at java.lang.reflect.Method.invoke(Method.java:498)
 at org.apache.flink.client.program.PackagedProgram.callMainMethod(PackagedProgram.java:355)
 ... 8 more
Caused by: org.apache.flink.table.api.ValidationException: Cannot discover a connector using option: 'connector'='kafka'
 at org.apache.flink.table.factories.FactoryUtil.enrichNoMatchingConnectorError(FactoryUtil.java:467)
 at org.apache.flink.table.factories.FactoryUtil.getDynamicTableFactory(FactoryUtil.java:441)
 at org.apache.flink.table.factories.FactoryUtil.createTableSource(FactoryUtil.java:133)
 ... 34 more
Caused by: org.apache.flink.table.api.ValidationException: Could not find any factory for identifier 'kafka' that implements 'org.apache.flink.table.factories.DynamicTableFactory' in the classpath.

Available factory identifiers are:

blackhole
datagen
filesystem
print
 at org.apache.flink.table.factories.FactoryUtil.discoverFactory(FactoryUtil.java:319)
 at org.apache.flink.table.factories.FactoryUtil.enrichNoMatchingConnectorError(FactoryUtil.java:463)
 ... 36 more
```

## 2. 解决方案

当您使用 CREATE TABLE DDL 语句声明一张连接 Kafka 的表时，Flink 会根据 connector 选项的值（这里是 kafka）去它的 classpath 中寻找一个实现了 DynamicTableFactory 接口的工厂类。从上面可以看到 Flink 在当前的 classpath 下只找到了四个内置的连接器工厂（blackhole, datagen, filesystem, print），唯独没有找到 Kafka 连接器的工厂类。问题在于 Flink 集群（JobManager 和 TaskManager）的 lib 目录下缺少 Flink Kafka SQL Connector 的 Jar 包。

根据你的 Flink 和 Scala 版本，下载正确的 `flink-sql-connector-kafka_${scala.version}_${flink.version}.jar`。将其放入所有集群节点的 `$FLINK_HOME/lib/` 目录。重启 Flink 集群，重新提交作业即可。
