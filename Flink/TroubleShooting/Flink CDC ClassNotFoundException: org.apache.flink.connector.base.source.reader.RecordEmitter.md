> Flink CDC: 3.5.0

## 1. 问题

使用如下代码捕获 MySQL 变更：
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// enable checkpoint
env.enableCheckpointing(3000);
env.setParallelism(1);

MySqlSource<String> mySqlSource = MySqlSource.<String>builder()
        .hostname("localhost")
        .port(3306)
        .databaseList("test")
        .tableList("user_level")
        .username("root")
        .password("root")
        .deserializer(new JsonDebeziumDeserializationSchema()) // converts SourceRecord to JSON String
        .build();


env.fromSource(mySqlSource, WatermarkStrategy.noWatermarks(), "MySQL Source")
        .setParallelism(4)
        .print().setParallelism(1); // use parallelism 1 for sink to keep message ordering

env.execute("Print MySQL Snapshot + Binlog");
```
运行如上程序抛出如下异常：
```java
Exception in thread "main" java.lang.BootstrapMethodError: java.lang.NoClassDefFoundError: org/apache/flink/connector/base/source/reader/RecordEmitter
	at org.apache.flink.cdc.connectors.mysql.source.MySqlSource.<init>(MySqlSource.java:127)
	at org.apache.flink.cdc.connectors.mysql.source.MySqlSourceBuilder.build(MySqlSourceBuilder.java:301)
	at com.flink.cdc.stream.MySQLCdcSourceExample.main(MySQLCdcSourceExample.java:23)
Caused by: java.lang.NoClassDefFoundError: org/apache/flink/connector/base/source/reader/RecordEmitter
	at java.lang.ClassLoader.defineClass1(Native Method)
	at java.lang.ClassLoader.defineClass(ClassLoader.java:756)
	at java.security.SecureClassLoader.defineClass(SecureClassLoader.java:142)
	at java.net.URLClassLoader.defineClass(URLClassLoader.java:473)
	at java.net.URLClassLoader.access$100(URLClassLoader.java:74)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:369)
	at java.net.URLClassLoader$1.run(URLClassLoader.java:363)
	at java.security.AccessController.doPrivileged(Native Method)
	at java.net.URLClassLoader.findClass(URLClassLoader.java:362)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:418)
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:371)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:351)
	... 3 more
Caused by: java.lang.ClassNotFoundException: org.apache.flink.connector.base.source.reader.RecordEmitter
	at java.net.URLClassLoader.findClass(URLClassLoader.java:387)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:418)
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:371)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:351)
	... 15 more
```


## 2. 解决方案

RecordEmitter 类是 Flink 1.14+ 中引入的新类，属于 flink-connector-base 模块。这个错误常出现于缺少 flink-connector-base 依赖：
```xml
<!-- Connector Base (解决 RecordEmitter 问题) -->
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-connector-base</artifactId>
    <version>1.16.0</version>
</dependency>
```

flink-connector-base 模块主要是提供连接外部系统和数据源的基础功能，为其他具体的连接器模块提供了通用的接口和类。通过使用 flink-connector-base，可以方便地实现自定义的连接器，并将 Flink 与各种外部系统集成起来，所以与外部组件集成一般需要加上此依赖。
