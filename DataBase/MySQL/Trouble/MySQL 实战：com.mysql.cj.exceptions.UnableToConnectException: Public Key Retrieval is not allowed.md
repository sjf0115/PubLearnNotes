
```
java.lang.IllegalStateException: Failed to execute CommandLineRunner
	at org.springframework.boot.SpringApplication.callRunner(SpringApplication.java:774) [spring-boot-2.7.3.jar:2.7.3]
	at org.springframework.boot.SpringApplication.callRunners(SpringApplication.java:755) [spring-boot-2.7.3.jar:2.7.3]
	at org.springframework.boot.SpringApplication.run(SpringApplication.java:315) [spring-boot-2.7.3.jar:2.7.3]
	at org.springframework.boot.SpringApplication.run(SpringApplication.java:1306) [spring-boot-2.7.3.jar:2.7.3]
	at org.springframework.boot.SpringApplication.run(SpringApplication.java:1295) [spring-boot-2.7.3.jar:2.7.3]
	at org.apache.dolphinscheduler.tools.datasource.UpgradeDolphinScheduler.main(UpgradeDolphinScheduler.java:36) [dolphinscheduler-tools-3.2.1.jar:3.2.1]
Caused by: java.sql.SQLNonTransientConnectionException: Public Key Retrieval is not allowed
	at com.mysql.cj.jdbc.exceptions.SQLError.createSQLException(SQLError.java:110) ~[mysql-connector-java-8.0.16.jar:8.0.16]
	at com.mysql.cj.jdbc.exceptions.SQLError.createSQLException(SQLError.java:97) ~[mysql-connector-java-8.0.16.jar:8.0.16]
	at com.mysql.cj.jdbc.exceptions.SQLExceptionsMapping.translateException(SQLExceptionsMapping.java:122) ~[mysql-connector-java-8.0.16.jar:8.0.16]
	at com.mysql.cj.jdbc.ConnectionImpl.createNewIO(ConnectionImpl.java:835) ~[mysql-connector-java-8.0.16.jar:8.0.16]
	at com.mysql.cj.jdbc.ConnectionImpl.<init>(ConnectionImpl.java:455) ~[mysql-connector-java-8.0.16.jar:8.0.16]
	at com.mysql.cj.jdbc.ConnectionImpl.getInstance(ConnectionImpl.java:240) ~[mysql-connector-java-8.0.16.jar:8.0.16]
	at com.mysql.cj.jdbc.NonRegisteringDriver.connect(NonRegisteringDriver.java:199) ~[mysql-connector-java-8.0.16.jar:8.0.16]
	at com.zaxxer.hikari.util.DriverDataSource.getConnection(DriverDataSource.java:138) ~[HikariCP-4.0.3.jar:na]
	at com.zaxxer.hikari.pool.PoolBase.newConnection(PoolBase.java:364) ~[HikariCP-4.0.3.jar:na]
	at com.zaxxer.hikari.pool.PoolBase.newPoolEntry(PoolBase.java:206) ~[HikariCP-4.0.3.jar:na]
	at com.zaxxer.hikari.pool.HikariPool.createPoolEntry(HikariPool.java:476) ~[HikariCP-4.0.3.jar:na]
	at com.zaxxer.hikari.pool.HikariPool.checkFailFast(HikariPool.java:561) ~[HikariCP-4.0.3.jar:na]
	at com.zaxxer.hikari.pool.HikariPool.<init>(HikariPool.java:115) ~[HikariCP-4.0.3.jar:na]
	at com.zaxxer.hikari.HikariDataSource.getConnection(HikariDataSource.java:112) ~[HikariCP-4.0.3.jar:na]
	at org.apache.dolphinscheduler.dao.plugin.mysql.dialect.MysqlDialect.tableExists(MysqlDialect.java:44) ~[dolphinscheduler-dao-mysql-3.2.1.jar:3.2.1]
	at org.apache.dolphinscheduler.tools.datasource.DolphinSchedulerManager.schemaIsInitialized(DolphinSchedulerManager.java:69) ~[dolphinscheduler-tools-3.2.1.jar:3.2.1]
	at org.apache.dolphinscheduler.tools.datasource.UpgradeDolphinScheduler$UpgradeRunner.run(UpgradeDolphinScheduler.java:52) ~[dolphinscheduler-tools-3.2.1.jar:3.2.1]
	at org.springframework.boot.SpringApplication.callRunner(SpringApplication.java:771) [spring-boot-2.7.3.jar:2.7.3]
	... 5 common frames omitted
```
