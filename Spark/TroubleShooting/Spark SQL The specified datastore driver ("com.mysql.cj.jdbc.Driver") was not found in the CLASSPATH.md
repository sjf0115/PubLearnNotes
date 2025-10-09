## 1. 问题

```java
String warehouseLocation = new File("spark-warehouse").getAbsolutePath();
SparkSession spark = SparkSession
        .builder()
        .master("local[*]")
        .appName("Java Spark Hive Example")
        .config("spark.sql.warehouse.dir", warehouseLocation)
        .enableHiveSupport()
        .getOrCreate();

// 读取
spark.sql("show databases").show();
spark.sql("show tables").show();
spark.sql("SELECT COUNT(*) FROM tb_order").show();
```
出现如下异常：
```java
Error creating transactional connection factory
org.datanucleus.exceptions.NucleusException: Error creating transactional connection factory
	at org.datanucleus.store.AbstractStoreManager.registerConnectionFactory(AbstractStoreManager.java:214)
	at org.datanucleus.store.AbstractStoreManager.<init>(AbstractStoreManager.java:162)
	at org.datanucleus.store.rdbms.RDBMSStoreManager.<init>(RDBMSStoreManager.java:285)
	at sun.reflect.NativeConstructorAccessorImpl.newInstance0(Native Method)
	at sun.reflect.NativeConstructorAccessorImpl.newInstance(NativeConstructorAccessorImpl.java:62)
	at sun.reflect.DelegatingConstructorAccessorImpl.newInstance(DelegatingConstructorAccessorImpl.java:45)
  ...
	at com.spark.example.sql.source.HiveExample.main(HiveExample.java:19)
Caused by: java.lang.reflect.InvocationTargetException
	at sun.reflect.NativeConstructorAccessorImpl.newInstance0(Native Method)
	at sun.reflect.NativeConstructorAccessorImpl.newInstance(NativeConstructorAccessorImpl.java:62)
	at sun.reflect.DelegatingConstructorAccessorImpl.newInstance(DelegatingConstructorAccessorImpl.java:45)
	at java.lang.reflect.Constructor.newInstance(Constructor.java:423)
	at org.datanucleus.plugin.NonManagedPluginRegistry.createExecutableExtension(NonManagedPluginRegistry.java:606)
	at org.datanucleus.plugin.PluginManager.createExecutableExtension(PluginManager.java:330)
	at org.datanucleus.store.AbstractStoreManager.registerConnectionFactory(AbstractStoreManager.java:203)
	... 104 more
Caused by: org.datanucleus.exceptions.NucleusException: Attempt to invoke the "HikariCP" plugin to create a ConnectionPool gave an error : The specified datastore driver ("com.mysql.cj.jdbc.Driver") was not found in the CLASSPATH. Please check your CLASSPATH specification, and the name of the driver.
	at org.datanucleus.store.rdbms.ConnectionFactoryImpl.generateDataSources(ConnectionFactoryImpl.java:232)
	at org.datanucleus.store.rdbms.ConnectionFactoryImpl.initialiseDataSources(ConnectionFactoryImpl.java:117)
	at org.datanucleus.store.rdbms.ConnectionFactoryImpl.<init>(ConnectionFactoryImpl.java:82)
	... 111 more
Caused by: org.datanucleus.store.rdbms.connectionpool.DatastoreDriverNotFoundException: The specified datastore driver ("com.mysql.cj.jdbc.Driver") was not found in the CLASSPATH. Please check your CLASSPATH specification, and the name of the driver.
	at org.datanucleus.store.rdbms.connectionpool.AbstractConnectionPoolFactory.loadDriver(AbstractConnectionPoolFactory.java:58)
	at org.datanucleus.store.rdbms.connectionpool.HikariCPConnectionPoolFactory.createConnectionPool(HikariCPConnectionPoolFactory.java:66)
	at org.datanucleus.store.rdbms.ConnectionFactoryImpl.generateDataSources(ConnectionFactoryImpl.java:213)
	... 113 more
```

## 2. 解决方案

根本原因：Spark 使用 Hive 元数据存储时，需要连接到 MySQL 数据库来存储元数据信息，但是 `com.mysql.cj.jdbc.Driver` 类不在 Spark 的 classpath 中。所以导致所有涉及 Hive 元数据操作的 Spark SQL 操作都会失败。

以编程方式查询 Hive 时需要添加如下 MySQL 驱动依赖：
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
</dependency>
```
