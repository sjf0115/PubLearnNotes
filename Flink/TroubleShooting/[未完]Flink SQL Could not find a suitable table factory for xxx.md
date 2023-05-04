```java
Exception in thread "main" org.apache.flink.table.api.ValidationException: SQL validation failed. findAndCreateTableSource failed.
	at org.apache.flink.table.calcite.FlinkPlannerImpl.validateInternal(FlinkPlannerImpl.scala:130)
	at org.apache.flink.table.calcite.FlinkPlannerImpl.validate(FlinkPlannerImpl.scala:105)
	at org.apache.flink.table.sqlexec.SqlToOperationConverter.convert(SqlToOperationConverter.java:124)
	at org.apache.flink.table.planner.ParserImpl.parse(ParserImpl.java:66)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.sqlQuery(TableEnvironmentImpl.java:464)
	at com.flink.connector.example.socket.SocketSimpleExample.main(SocketSimpleExample.java:44)
Caused by: org.apache.flink.table.api.TableException: findAndCreateTableSource failed.
	at org.apache.flink.table.factories.TableFactoryUtil.findAndCreateTableSource(TableFactoryUtil.java:55)
	at org.apache.flink.table.factories.TableFactoryUtil.findAndCreateTableSource(TableFactoryUtil.java:92)
	at org.apache.flink.table.catalog.DatabaseCalciteSchema.convertCatalogTable(DatabaseCalciteSchema.java:138)
	at org.apache.flink.table.catalog.DatabaseCalciteSchema.convertTable(DatabaseCalciteSchema.java:97)
	at org.apache.flink.table.catalog.DatabaseCalciteSchema.lambda$getTable$0(DatabaseCalciteSchema.java:86)
	at java.util.Optional.map(Optional.java:215)
	at org.apache.flink.table.catalog.DatabaseCalciteSchema.getTable(DatabaseCalciteSchema.java:76)
	at org.apache.calcite.jdbc.SimpleCalciteSchema.getImplicitTable(SimpleCalciteSchema.java:83)
	at org.apache.calcite.jdbc.CalciteSchema.getTable(CalciteSchema.java:289)
	at org.apache.calcite.sql.validate.EmptyScope.resolve_(EmptyScope.java:143)
	at org.apache.calcite.sql.validate.EmptyScope.resolveTable(EmptyScope.java:99)
	at org.apache.calcite.sql.validate.DelegatingScope.resolveTable(DelegatingScope.java:203)
	at org.apache.calcite.sql.validate.IdentifierNamespace.resolveImpl(IdentifierNamespace.java:105)
	at org.apache.calcite.sql.validate.IdentifierNamespace.validateImpl(IdentifierNamespace.java:177)
	at org.apache.calcite.sql.validate.AbstractNamespace.validate(AbstractNamespace.java:84)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validateNamespace(SqlValidatorImpl.java:1008)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validateQuery(SqlValidatorImpl.java:968)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validateFrom(SqlValidatorImpl.java:3122)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validateFrom(SqlValidatorImpl.java:3104)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validateSelect(SqlValidatorImpl.java:3376)
	at org.apache.calcite.sql.validate.SelectNamespace.validateImpl(SelectNamespace.java:60)
	at org.apache.calcite.sql.validate.AbstractNamespace.validate(AbstractNamespace.java:84)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validateNamespace(SqlValidatorImpl.java:1008)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validateQuery(SqlValidatorImpl.java:968)
	at org.apache.calcite.sql.SqlSelect.validate(SqlSelect.java:216)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validateScopedExpression(SqlValidatorImpl.java:943)
	at org.apache.calcite.sql.validate.SqlValidatorImpl.validate(SqlValidatorImpl.java:650)
	at org.apache.flink.table.calcite.FlinkPlannerImpl.validateInternal(FlinkPlannerImpl.scala:126)
	... 5 more
Caused by: org.apache.flink.table.api.NoMatchingTableFactoryException: Could not find a suitable table factory for 'org.apache.flink.table.factories.TableSourceFactory' in
the classpath.

Reason: No factory supports all properties.
The matching candidates:
com.flink.connector.socket.SocketSourceTableFactory
Unsupported property keys:
schema.#.data-type
format
schema.#.name

The following properties are requested:
connector.type=socket
delaybetweenretries=500
delimiter=\n
format=json
host=localhost
maxnumretries=3
port=9000
schema.0.data-type=VARCHAR(2147483647)
schema.0.name=word
schema.1.data-type=BIGINT
schema.1.name=frequency
update-mode=append

The following factories have been considered:
org.apache.flink.table.sources.CsvBatchTableSourceFactory
org.apache.flink.table.sources.CsvAppendTableSourceFactory
com.flink.connector.socket.SocketSourceTableFactory
```
