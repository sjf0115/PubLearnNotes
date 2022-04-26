

## 1. 支持的 Hive 版本

| Hive 大版本 | Hive 小版本 |
| :------------- | :------------- |
| 1.0       | 1.0.0 <br> 1.0.1 |
| 1.1       | 1.1.0 <br> 1.1.1 |
| 1.2       | 1.2.0 <br> 1.2.1 <br> 1.2.2 |
| 2.0       | 2.0.0 <br> 2.0.1 |
| 2.1       | 2.1.0 <br> 2.1.1 |
| 2.2       | 2.2.0 |
| 2.3       | 2.3.0 <br> 2.3.1 <br> 2.3.2 <br> 2.3.3 <br> 2.3.4 <br> 2.3.5 <br> 2.3.6 |
| 3.1       | 3.1.0 <br> 3.1.1 <br> 3.1.2 |

需要注意 Hive 在不同版本会有不同的功能：
- 1.2.0 及更高版本支持 Hive 内置函数。
- 3.1.0 及更高版本支持列约束，即 PRIMARY KEY 和 NOT NULL。
- 1.2.0 及更高版本支持更改表统计信息。
- 1.2.0 及更高版本支持 DATE 列统计信息。
- 2.0.x 不支持写入 ORC 表。

### 1.1 依赖

要与 Hive 集成，需要在 Flink 的 /lib/ 目录中添加一些额外的依赖项，以便在 Table API 或 SQL Client 中与 Hive 集成。或者，也可以将这些依赖项放在一个专门文件夹下，在使用 Table API 或者 SQL Client 时候分别使用 -C 或 -l 选项将它们添加到类路径中。

Apache Hive 构建在 Hadoop 之上，因此需要通过设置 HADOOP_CLASSPATH 环境变量来提供 Hadoop 依赖项：
```
export HADOOP_CLASSPATH=`hadoop classpath`
```
有两种方法可以添加 Hive 依赖项。第一种是使用 Flink 捆绑的 Hive jars。根据使用的 Metastore 版本选择捆绑的 Hive jar。第二种是分别添加每个所需的 jar。如果你使用的 Hive 版本在上面表格未列出，那么第二种方法比较适合。

> 推荐使用 Flink 捆绑的 Hive jars 的方式添加依赖项。仅当捆绑的 jar 不能满足你的需求时，才应使用单独的 jar。

#### 1.1.1 捆绑方式

下表列出了所有可用的捆绑 Hive jar。你可以在 Flink 中的 /lib/ 目录中选择一个。

| Metastore 版本  | Maven 依赖  | SQL Client JAR |
| :------------- | :----------------------------- | :------------- |
| 1.0.0 - 1.2.2	 | flink-sql-connector-hive-1.2.2 |	[下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-hive-1.2.2_2.11/1.13.5/flink-sql-connector-hive-1.2.2_2.11-1.13.5.jar) |
| 2.0.0 - 2.2.0	 | flink-sql-connector-hive-2.2.0	| [下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-hive-2.2.0_2.11/1.13.5/flink-sql-connector-hive-2.2.0_2.11-1.13.5.jar) |  
| 2.3.0 - 2.3.6	 | flink-sql-connector-hive-2.3.6	| [下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-hive-2.3.6_2.11/1.13.5/flink-sql-connector-hive-2.3.6_2.11-1.13.5.jar) |
| 3.0.0 - 3.1.2	 | flink-sql-connector-hive-3.1.2	| [下载](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-hive-3.1.2_2.11/1.13.5/flink-sql-connector-hive-3.1.2_2.11-1.13.5.jar) |

#### 1.1.2 用户自定义依赖

在下面找到不同 Hive 主要版本所需的依赖项：
- Hive 3.1.0：
 - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
 - hive-exec-3.1.0.jar：Hive 依赖
 - libfb303-0.9.3.jar：在部分版本中没有打包到 hive-exec 中，需要单独添加
 - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 2.3.4：
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector。包含 flink-hadoop-compatibility 和 flink-orc jars
  - hive-exec-2.3.4.jar：Hive 依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 2.2.0：
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-exec-2.2.0.jar：Hive 依赖
  - orc-core-1.4.3.jar：Orc 依赖
  - aircompressor-0.8.jar：orc-core 传递依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 2.1.0
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-exec-2.1.0.jar：Hive 依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 2.0.0
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-exec-2.0.0.jar：Hive 依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 1.2.1
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-metastore-1.2.1.jar：Hive 依赖
  - hive-exec-1.2.1.jar：Hive 依赖
  - libfb303-0.9.2.jar：在部分版本中没有打包到 hive-exec 中，需要单独添加
  - orc-core-1.4.3-nohive.jar：Orc 依赖
  - aircompressor-0.8.jar：orc-core 传递依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 1.1.0
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-metastore-1.1.0.jar：Hive 依赖
  - hive-exec-1.1.0.jar：Hive 依赖
  - libfb303-0.9.2.jar：在部分版本中没有打包到 hive-exec 中，需要单独添加
  - orc-core-1.4.3-nohive.jar：Orc 依赖
  - aircompressor-0.8.jar：orc-core 传递依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加
- Hive 1.0.0
  - flink-connector-hive_2.11-1.13.5.jar：Flink 的 Hive Connector
  - hive-metastore-1.0.0.jar：Hive 依赖
  - hive-exec-1.0.0.jar：Hive 依赖
  - libfb303-0.9.0.jar：在部分版本中没有打包到 hive-exec 中，需要单独添加
  - orc-core-1.4.3-nohive.jar：Orc 依赖
  - aircompressor-0.8.jar：orc-core 传递依赖
  - antlr-runtime-3.5.2.jar：使用 hive 方言需要添加

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

以下是使用 YAML 文件或 DDL 创建 HiveCatalog 实例时支持的选项：

| 选项 | 是否必填 | 默认值 | 类型 | 描述 |
| :--------------- | :------ | :------ | :------ | :------ |
| type             | 是 | (none)  | String | Catalog 的类型。创建 HiveCatalog 时必须设置为 'hive' |
| name             | 是 | (none)  | String | Catalog 的唯一名称。仅适用于 YAML 文件 |
| hive-conf-dir    | 否 | (none)  | String | 包含 hive-site.xml 的配置文件的 conf 目录路径。如果未指定该选项，则在类路径中搜索 hive-site.xml |
| default-database | 否 | default | String | 将 Catalog 设置为当前 Catalog 时使用的默认数据库 |
| hive-version     | 否 | (none)  | String | HiveCatalog 能够自动检测正在使用的 Hive 版本。建议不要指定 Hive 版本，除非自动检测失败 |
| hadoop-conf-dir  | 否 | (none)  | String | Hadoop conf 目录的路径。仅支持本地文件系统路径。设置 Hadoop conf 的推荐方法是通过 HADOOP_CONF_DIR 环境变量。仅当环境变量不起作用时才使用该选项，例如如果要单独配置每个 HiveCatalog。|







..
