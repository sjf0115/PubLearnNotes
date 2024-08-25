
JDBC Connector 连接器提供一个 Sink 接收器来将数据写入 JDBC 数据库。在这使用 JDBC Connector 连接器实现将数据写入 MySQL 数据库。

## 1. 依赖

要使用 JDBC Connector 连接器，需要将如下依赖项添加到项目中：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-connector-jdbc_2.11</artifactId>
    <version>1.13.6</version>
</dependency>
```
除此之外还需要添加 MySQL 的 JDBC 驱动程序：
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.22</version>
</dependency>
```
如果不添加上述 MySQL 驱动程序会抛出如下异常信息：
```java
Caused by: java.io.IOException: unable to open JDBC writer
	at org.apache.flink.connector.jdbc.internal.AbstractJdbcOutputFormat.open(AbstractJdbcOutputFormat.java:56)
	at org.apache.flink.connector.jdbc.internal.JdbcBatchingOutputFormat.open(JdbcBatchingOutputFormat.java:115)
	at org.apache.flink.connector.jdbc.internal.GenericJdbcSinkFunction.open(GenericJdbcSinkFunction.java:49)
	at org.apache.flink.api.common.functions.util.FunctionUtils.openFunction(FunctionUtils.java:34)
	at org.apache.flink.streaming.api.operators.AbstractUdfStreamOperator.open(AbstractUdfStreamOperator.java:102)
	at org.apache.flink.streaming.api.operators.StreamSink.open(StreamSink.java:46)
	at org.apache.flink.streaming.runtime.tasks.OperatorChain.initializeStateAndOpenOperators(OperatorChain.java:442)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restoreGates(StreamTask.java:585)
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$1.call(StreamTaskActionExecutor.java:55)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeRestore(StreamTask.java:565)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restore(StreamTask.java:540)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:759)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566)
	at java.lang.Thread.run(Thread.java:748)
Caused by: java.lang.ClassNotFoundException: com.mysql.cj.jdbc.Driver
	at java.net.URLClassLoader.findClass(URLClassLoader.java:381)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
	at org.apache.flink.util.FlinkUserCodeClassLoader.loadClassWithoutExceptionHandling(FlinkUserCodeClassLoader.java:64)
	at org.apache.flink.util.ChildFirstClassLoader.loadClassWithoutExceptionHandling(ChildFirstClassLoader.java:74)
	at org.apache.flink.util.FlinkUserCodeClassLoader.loadClass(FlinkUserCodeClassLoader.java:48)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:357)
	at org.apache.flink.runtime.execution.librarycache.FlinkUserCodeClassLoaders$SafetyNetWrapperClassLoader.loadClass(FlinkUserCodeClassLoaders.java:172)
	at java.lang.Class.forName0(Native Method)
	at java.lang.Class.forName(Class.java:348)
	at org.apache.flink.connector.jdbc.internal.connection.SimpleJdbcConnectionProvider.loadDriver(SimpleJdbcConnectionProvider.java:90)
	at org.apache.flink.connector.jdbc.internal.connection.SimpleJdbcConnectionProvider.getLoadedDriver(SimpleJdbcConnectionProvider.java:100)
	at org.apache.flink.connector.jdbc.internal.connection.SimpleJdbcConnectionProvider.getOrEstablishConnection(SimpleJdbcConnectionProvider.java:117)
	at org.apache.flink.connector.jdbc.internal.AbstractJdbcOutputFormat.open(AbstractJdbcOutputFormat.java:54)
	... 14 more
```

## 2. JdbcSink.sink


```java
JdbcSink.sink(
      	sqlDmlStatement,                       // 必填
      	jdbcStatementBuilder,                  // 必填   	
      	jdbcExecutionOptions,                  // 可选
      	jdbcConnectionOptions                  // 必填
);
```


需要注意的是 JDBC 接收器只提供了 `At-Least-Once` 语义保证。但是，可以通过编写 upsert SQL 语句或幂等 SQL 更新，可以有效地实现 `Exactly-Once`。


SQL DML语句和JDBC语句构建器

### 2.2 JDBC 执行参数

SQL DML 语句是分批执行的，可以选择使用以下实例进行配置：
```java
JdbcExecutionOptions.builder()
        .withBatchIntervalMs(200)             // optional: default = 0, meaning no time-based execution is done
        .withBathSize(1000)                   // optional: default = 5000 values
        .withMaxRetries(5)                    // optional: default = 3
.build()
```



...
