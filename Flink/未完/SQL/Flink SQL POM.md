
该模块包含 Table/SQL 的扩展 API。实现用户定义的函数、自定义 Format 等的最小依赖。
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-common</artifactId>
    <version>${flink-version}</version>
    <scope>provided</scope>
</dependency>
```
该模块包含编写 Table 程序所需要的 Table/SQL API，使用 Java 编程语言与其他 Flink API 进行交互。
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-api-java-bridge_2.11</artifactId>
    <version>${flink-version}</version>
    <scope>provided</scope>
</dependency>
```
该模块包含使用 Java 编程语言在 Table 生态系统中编写 Table 程序的 Table/SQL API。
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-api-java</artifactId>
    <version>${flink-version}</version>
</dependency>
```

```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-planner-blink_2.11</artifactId>
    <version>${flink-version}</version>
    <scope>test</scope>
</dependency>
```

```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-planner_2.11</artifactId>
    <version>${flink-version}</version>
    <scope>provided</scope>
</dependency>
```

```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table</artifactId>
    <version>${flink-version}</version>
    <type>pom</type>
    <scope>provided</scope>
</dependency>
```

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
