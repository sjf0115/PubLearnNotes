
根据我们使用的编程语言，需要将 Java 或者 Scala API 添加到项目中，以便在程序中使用 Table API 和 SQL：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-api-java-bridge_2.11</artifactId>
  <version>${flink.version}</version>
  <scope>provided</scope>
</dependency>
```
此外，如果你想在 IDE 中本地运行 Table API 或者 SQL 程序，那么必须添加如下依赖：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner_2.11</artifactId>
  <version>${flink.version}</version>
  <scope>provided</scope>
</dependency>

<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-streaming-scala_2.11</artifactId>
  <version>${flink.version}</version>
  <scope>provided</scope>
</dependency>
```

```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner-blink_2.11</artifactId>
  <version>1.13.6</version>
  <scope>provided</scope>
</dependency>
```
