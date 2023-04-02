## 1. 问题

本地运行 Flink SQL 示例时，抛出如下异常：
```java
...
Caused by: java.lang.ClassNotFoundException: org.apache.flink.table.factories.StreamTableSourceFactory
	at java.net.URLClassLoader.findClass(URLClassLoader.java:381)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:338)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:357)
	... 38 more
```

## 2. 解决方案

在 pom 中查看 flink-table-api-java-bridge_xxx 依赖的 scope 属性是否为 `provided`：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-api-java-bridge_${scala.binary.version}</artifactId>
  <version>${flink.version}</version>
  <scope>provided</scope>
</dependency>
```
在本地运行模式下需要注释 `provided`：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-api-java-bridge_${scala.binary.version}</artifactId>
  <version>${flink.version}</version>
</dependency>
```
