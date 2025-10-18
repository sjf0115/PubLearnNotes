


### 1.2 程序依赖

如果你正在构建自己的应用程序，那么需要在 mvn 文件中包含以下依赖项。建议不要在生成的 jar 文件中包含这些依赖项：
```xml
<!-- Flink 依赖 -->
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-connector-hive_2.11</artifactId>
  <version>1.13.5</version>
  <scope>provided</scope>
</dependency>

<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-api-java-bridge_2.11</artifactId>
  <version>1.13.5</version>
  <scope>provided</scope>
</dependency>

<!-- Hive 依赖 -->
<dependency>
    <groupId>org.apache.hive</groupId>
    <artifactId>hive-exec</artifactId>
    <version>${hive.version}</version>
    <scope>provided</scope>
</dependency>
```

## 2. 连接 Hive

通过表环境或 YAML 配置使用 Catalog 接口和 HiveCatalog 连接到现有的 Hive 上。如下是如何连接到 Hive 的示例：
```java
EnvironmentSettings settings = EnvironmentSettings.inStreamingMode();
TableEnvironment tableEnv = TableEnvironment.create(settings);

String name            = "myhive";
String defaultDatabase = "mydatabase";
String hiveConfDir     = "/opt/hive-conf";

HiveCatalog hive = new HiveCatalog(name, defaultDatabase, hiveConfDir);
tableEnv.registerCatalog("myhive", hive);

// set the HiveCatalog as the current catalog of the session
tableEnv.useCatalog("myhive");
```
