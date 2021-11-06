
Flink 从 1.9 版本开始支持支持 Hive，不过作为 beta 版，不推荐在生产环境中使用。在 Flink 1.10 版本中，对 Hive 的集成也达到了生产级别的要求。值得注意的是，不同版本的 Flink 对于 Hive 的集成有所差异。

## 1. 什么是 HiveCatalog

近年来，Hive Metastore 已经发展成为 Hadoop 生态系统元数据中心的标准。许多公司在生产环境中使用 Hive Metastore 服务来管理元数据(无论是 Hive 元数据还是非 Hive 元数据)。对于部署 Hive 和 Flink 的用户来说，HiveCatalog 能够让他们使用 Hive Metastore 来管理 Flink 的元数据。

对于刚刚部署 Flink 的用户，HiveCatalog 是 Flink 提供的唯一一个开箱即用的持久化 Catalog。在没有持久化 Catalog 的情况下，使用 Flink SQL CREATE DDL 必须在每个会话中重复创建元对象，例如 Kafka 表，这会浪费大量的时间。HiveCatalog 通过授权用户仅创建一次表和其他元对象来填补这一空白，并在以后跨会话时方便地引用和管理它们。

## 2. 如何配置 HiveCatalog

在 Flink中 配置 HiveCatalog 需要与整体flint - hive集成相同的依赖关系。

## 3. 如何使用 HiveCatalog

一旦配置完成，HiveCatalog 就可以开箱即用。用户可以使用 DDL 语句创建 Flink 元对象，并且在此之后可以立即看到。

HiveCatalog 可用于处理两种类型的表：Hive 兼容表(Hive-compatible Tables)以及通用表(Generic Tables)。Hive 兼容表是指以 Hive 兼容的方式存储的表，包括存储层中的元数据和数据。因此，通过 Flink 创建与 Hive 兼容的表可以从 Hive 侧查询。另一方面，通用表是只针对于 Flink 的。当使用 HiveCatalog 创建通用表时，我们只是使用 HMS 持久化存储元数据。虽然这些表对 Hive 是可见的，但是 Hive 不能理解这些元数据。因此，在 Hive 中使用这样的表会导致未定义的行为。

建议使用 Hive Dialect 来创建与 Hive 兼容的表。如果您想使用默认 Dialect 来创建 Hive 兼容表，请确保在表属性中设置 'connector'='hive'，否则在 HiveCatalog 中，默认情况下表被认为是通用的。需要注意的是，如果使用 Hive Dialect，则不需要 connector 属性。

### 3.1 设置 Hive Metastore

运行一个 Hive Metastore。

在这里，我们建立了一个本地 Hive Metastore 和我们的Hive -site.xml文件在本地路径/opt/ Hive -conf/ Hive -site.xml。我们有如下的配置:
```xml
<configuration>
   <property>
      <name>javax.jdo.option.ConnectionURL</name>
      <value>jdbc:mysql://localhost/metastore?createDatabaseIfNotExist=true</value>
      <description>metadata is stored in a MySQL server</description>
   </property>

   <property>
      <name>javax.jdo.option.ConnectionDriverName</name>
      <value>com.mysql.jdbc.Driver</value>
      <description>MySQL JDBC driver class</description>
   </property>

   <property>
      <name>javax.jdo.option.ConnectionUserName</name>
      <value>...</value>
      <description>user name for connecting to mysql server</description>
   </property>

   <property>
      <name>javax.jdo.option.ConnectionPassword</name>
      <value>...</value>
      <description>password for connecting to mysql server</description>
   </property>

   <property>
       <name>hive.metastore.uris</name>
       <value>thrift://localhost:9083</value>
       <description>IP address (or fully-qualified domain name) and port of the metastore host</description>
   </property>

   <property>
       <name>hive.metastore.schema.verification</name>
       <value>true</value>
   </property>

</configuration>
```
使用 Hive CLI 测试与 HMS 的连接。运行一些命令，我们可以看到我们有一个名为 default 的数据库，其中没有表。
```
hive> show databases;
OK
default
Time taken: 0.032 seconds, Fetched: 1 row(s)

hive> show tables;
OK
Time taken: 0.028 seconds, Fetched: 0 row(s)
```

### 3.2 配置Flink集群和SQL CLI

将 Hive 依赖项添加到 Flink 安装目录下的 lib 目录下，并修改 SQL CLI 的 yaml 配置文件 sql-cli-defaults.yaml 如下:
```xml
execution:
    type: streaming
    ...
    current-catalog: myhive  # set the HiveCatalog as the current catalog of the session
    current-database: mydatabase

catalogs:
   - name: myhive
     type: hive
     hive-conf-dir: /opt/hive-conf  # contains hive-site.xml
```

## 4. 支持的数据类型

HiveCatalog 支持通用表的所有 Flink 类型。对于 Hive 兼容表，HiveCatalog 需要将 Flink 数据类型映射到对应的 Hive 数据类型，具体如下表所示:

![](1)

注意：
- Hive CHAR(p) 类型的最大长度为 255
- Hive VARCHAR(p) 类型的最大长度为 65535
- Hive MAP 类型的 key 仅支持基本类型，而 Flink 的 MAP 中的 key 可以是任意类型
- Hive 不支持 UNION 数据类型，比如，STRUCT
- Hive TIMESTAMP 类型精度为 9，不支持其他精度。Hive UDFs 函数只能处理精度小于 9 的 TIMESTAMP 值
- Hive 不支持 Flink 提供的 TIMESTAMP_WITH_TIME_ZONE、TIMESTAMP_WITH_LOCAL_TIME_ZONE 以及 MULTISET 类型
- Hive INTERVAL 类型不能映射为 Flink 的 INTERVAL 类型


参考：[]()
