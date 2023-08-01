

Iceberg 支持通过 Hive 使用 StorageHandler 来读写 Iceberg 表。

## 1. 环境准备

| Hive 版本  | 官方推荐Hive版本  | Iceberg 版本 |
| :------------- | :------------- | :------------- |
| 2.x | 2.3.8 | 0.8.0-incubating – 1.1.0 |
| 3.x | 3.1.2 | 0.10.0 – 1.1.0 |

Iceberg 与 Hive 2 和 Hive 3.1.2/3 的集成，支持以下特性：
- 创建表
- 删除表
- 读取表
- 插入表(INSERT INTO)

> 需要注意的是 DML 操作只支持 MapReduce 执行引擎。

### 1.1 Hive 4.0.0-alpha-1

Hive 4.0.0-alpha-1 包含了 Iceberg 0.13.1。不需要额外下载 jar 文件。

### 1.2 Hive 2.3.x, Hive 3.1.x

为了在 Hive 中使用 Iceberg，HiveIcebergStorageHandler 以及支持类需要在 Hive 类路径中可用。这些都可以由 iceberg-hive-runtime jar 文件来提供。如果使用的是 Hive shell，你可以通过如下语句来实现：
```
add jar /opt/jar/iceberg-hive-runtime-1.3.1.jar;
```
这种方式每次都需要添加一次，你可以将 jar 文件添加到 Hive 的辅助类路径中，使其在默认情况下可用。首先将 jar 文件拷贝到 Hive 的 auxlib 目录下：
```
mkdir auxlib
cp iceberg-hive-runtime-1.3.1.jar /opt/hive/auxlib
```
然后修改 hive-site.xml 配置文件，添加如下配置项：
```
<property>
    <name>iceberg.engine.hive.enabled</name>
    <value>true</value>
</property>

<property>
    <name>hive.aux.jars.path</name>
    <value>/opt/hive/auxlib</value>
</property>
```

## 2. Catalog 管理

Iceberg 支持多种不同的 Catalog 类型，例如 Hive、Hadoop、亚马逊的 AWS Glue 以及自定义 Catalog 实现。Iceberg 还允许根据表在文件系统中的路径直接加载表。这些表不属于任何 Catalog。用户可能只是希望通过 Hive 引擎读取这些跨 Catalog，基于路径的表来进行 Join 等用例。

根据不同配置，分为不同的方式来加载 Iceberg 表，具体取决于 iceberg.catalog 属性：
- 如果没有设置 iceberg.catalog，默认使用 HiveCatalog
- 如果设置了 iceberg.catalog，使用指定的 Catalog 类型来加载表
- 如果设置 iceberg.catalog=location_based_table，直接通过指定的根路径来加载表

### 2.1 默认使用 HiveCatalog

如果没有设置 iceberg.catalog，默认使用 HiveCatalog。如下所示使用 HiveCatalog 创建一个 Iceberg 表：
```sql
CREATE TABLE iceberg_test1 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler';

INSERT INTO iceberg_test1 values(1);
```
查看HDFS可以发现，表目录在默认的 hive 仓库路径下。

### 2.2 指定 Catalog 类型

如果设置了 iceberg.catalog，使用指定的 Catalog 类型创建表，具体配置如下所示：

| 配置项 | 说明 |
| :------------- | :------------- |
| iceberg.catalog.<catalog_name>.type | Catalog 的类型: hive, hadoop 等，如果使用自定义Catalog，则不设置 |
| iceberg.catalog.<catalog_name>.catalog-impl	| Catalog 的实现类, 如果上面的 type 没有设置，则此参数必须设置 |
| iceberg.catalog.<catalog_name>.<key>	| Catalog 的其他配置项 |

下面是一些使用 Hive CLI 的示例。如下所示注册一个名为 iceberg_hive 的 HiveCatalog:
```sql
SET iceberg.catalog.iceberg_hive.type=hive;
SET iceberg.catalog.iceberg_hive.uri=thrift://example.com:9083;
SET iceberg.catalog.iceberg_hive.clients=10;
SET iceberg.catalog.iceberg_hive.warehouse=hdfs://example.com:8020/warehouse;

CREATE TABLE iceberg_test2 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
TBLPROPERTIES('iceberg.catalog'='iceberg_hive');

INSERT INTO iceberg_test2 values(1);
```
如下所示注册一个名为 iceberg_hadoop 的 HadoopCatalog:
```sql
SET iceberg.catalog.iceberg_hadoop.type=hadoop;
SET iceberg.catalog.iceberg_hadoop.warehouse=hdfs://example.com:8020/warehouse;

CREATE TABLE iceberg_test3 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
LOCATION 'hdfs://hadoop1:8020/warehouse/iceberg-hadoop/default/iceberg_test3'
TBLPROPERTIES('iceberg.catalog'='iceberg_hadoop');

INSERT INTO iceberg_test3 values(1);
```

如下所示注册一个名为 iceberg_glue 的 GlueCatalog:
```sql
SET iceberg.catalog.iceberg_glue.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog;
SET iceberg.catalog.iceberg_glue.warehouse=s3://my-bucket/my/key/prefix;
SET iceberg.catalog.iceberg_glue.lock.table=myGlueLockTable;

CREATE TABLE iceberg_test4 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
LOCATION 'hdfs://hadoop1:8020/warehouse/iceberg-hadoop/default/iceberg_test3'
TBLPROPERTIES('iceberg.catalog'='iceberg_glue');

INSERT INTO iceberg_test3 values(1);
```

### 2.3 指定路径

如果 HDFS 中已经存在 iceberg 格式表，我们可以通过在 Hive 中创建 Icerberg 格式表指定对应的路径来映射数据。此时你需要设置 `iceberg.catalog=location_based_table`：
```sql
CREATE EXTERNAL TABLE iceberg_test5 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
LOCATION 'hdfs://hadoop1:8020/warehouse/iceberg-hadoop/default/iceberg_test3'
TBLPROPERTIES ('iceberg.catalog'='location_based_table');
```

## 3. DDL


## 4. DML
