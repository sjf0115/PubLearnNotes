## 1. 问题

```java
Exception in thread "main" org.apache.flink.table.api.TableException: Could not instantiate the executor. Make sure a planner module is on the classpath
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.lookupExecutor(StreamTableEnvironmentImpl.java:194)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.create(StreamTableEnvironmentImpl.java:156)
	at org.apache.flink.table.api.bridge.java.StreamTableEnvironment.create(StreamTableEnvironment.java:128)
	at com.flink.example.table.base.SQLWordCount.main(SQLWordCount.java:31)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
Caused by: org.apache.flink.table.api.NoMatchingTableFactoryException: Could not find a suitable table factory for 'org.apache.flink.table.delegation.ExecutorFactory' in
the classpath.

Reason: No factory supports the additional filters.

The following properties are requested:
class-name=org.apache.flink.table.planner.delegation.BlinkExecutorFactory
streaming-mode=true

The following factories have been considered:
org.apache.flink.table.executor.StreamExecutorFactory
	at org.apache.flink.table.factories.ComponentFactoryService.find(ComponentFactoryService.java:76)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.lookupExecutor(StreamTableEnvironmentImpl.java:185)
	... 8 more
```

原先的 pom 引入的是：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-planner_2.11</artifactId>
    <version>1.13.0</version>
    <scope>provided</scope>
</dependency>
```
但是
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner-blink_2.11</artifactId>
  <version>1.13.0</version>
  <scope>provided</scope>
</dependency>
```
