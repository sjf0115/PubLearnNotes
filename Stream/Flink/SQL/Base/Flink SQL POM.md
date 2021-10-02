
该模块包含 Table/SQL 的扩展 API。实现用户定义的函数、自定义 Format 等的最小依赖。
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-common</artifactId>
    <version>1.14.0</version>
    <scope>provided</scope>
</dependency>
```
该模块包含编写 Table 程序所需要的 Table/SQL API，使用 Java 编程语言与其他 Flink API 进行交互。
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-api-java-bridge_2.12</artifactId>
    <version>1.14.0</version>
    <scope>provided</scope>
</dependency>
```
该模块包含使用 Java 编程语言在 Table 生态系统中编写 Table 程序的 Table/SQL API。
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-api-java</artifactId>
    <version>1.14.0</version>
</dependency>
```

```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table-planner_2.12</artifactId>
    <version>1.14.0</version>
    <scope>provided</scope>
</dependency>
```

```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-table</artifactId>
    <version>1.14.0</version>
    <type>pom</type>
    <scope>provided</scope>
</dependency>
```
