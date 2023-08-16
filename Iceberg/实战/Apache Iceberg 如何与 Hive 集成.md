
> Hive 版本：2.3.4
> Iceberg 版本：

Iceberg 支持通过 Hive 使用 StorageHandler 来读写 Iceberg 表。

## 1. 环境准备

Iceberg 可以与 Hive 2.x 和 Hive 3.1.2/3 兼容，并支持以下特性：
- 创建表
- 删除表
- 读取表
- 插入表(INSERT INTO)

> 需要注意的是 DML 操作只支持 MapReduce 执行引擎。

> Hive 4.0.0-alpha-1 包含了 Iceberg 0.13.1。不需要额外下载 jar 文件。

在 Hive 2.x 和 Hive 3.1.2/3 版本中，为了在 Hive 中使用 Iceberg，HiveIcebergStorageHandler 以及支持类需要在 Hive 类路径中可用。这些都可以由 iceberg-hive-runtime jar 文件来提供。如果使用的是 Hive shell，你可以通过如下语句来实现：
```
add jar /opt/jar/iceberg-hive-runtime-1.3.1.jar;
```
这种方式每次都需要添加一次，你可以将 jar 文件添加到 Hive 的辅助类路径中，使其在默认情况下可用。首先将 jar 文件拷贝到 Hive 的 auxlib 目录下：
```
mkdir auxlib
cp iceberg-hive-runtime-1.3.1.jar /opt/hive/auxlib
```
然后修改 hive-site.xml 配置文件，添加如下配置项：
```xml
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
创建表之后可以查看表的详细信息：
```sql
CREATE TABLE `iceberg_test1`(
  `i` int COMMENT 'from deserializer')
ROW FORMAT SERDE
  'org.apache.iceberg.mr.hive.HiveIcebergSerDe'
STORED BY
  'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
LOCATION
  'hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_test1'
TBLPROPERTIES (
  'current-schema'='{"type":"struct","schema-id":0,"fields":[{"id":1,"name":"i","required":false,"type":"int"}]}',
  'current-snapshot-id'='1098862127872192306',
  'current-snapshot-summary'='{"added-data-files":"1","added-records":"1","added-files-size":"404","changed-partition-count":"1","total-records":"1","total-files-size":"404","total-data-files":"1","total-delete-files":"0","total-position-deletes":"0","total-equality-deletes":"0"}',
  'current-snapshot-timestamp-ms'='1692142879041',
  'engine.hive.enabled'='true',
  'external.table.purge'='TRUE',
  'last_modified_by'='wy',
  'last_modified_time'='1692142861',
  'metadata_location'='hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_test1/metadata/00001-5c66312c-42ab-4298-bb80-de1902a356ba.metadata.json',
  'previous_metadata_location'='hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_test1/metadata/00000-85bb7d43-ad8c-421f-9d41-9da4011e5522.metadata.json',
  'snapshot-count'='1',
  'table_type'='ICEBERG',
  'transient_lastDdlTime'='1692142861',
  'uuid'='d1a076ca-9d58-4239-a3fc-1e36a2c6872b'
)
```
> 后续会专门讲解一下对应的元数据文件

可以看到表目录在默认的 hive 仓库路径下。

### 2.2 指定 Catalog 类型

如果设置了 iceberg.catalog，使用指定的 Catalog 类型创建表，具体配置如下所示：

| 配置项 | 说明 |
| :------------- | :------------- |
| iceberg.catalog.<catalog_name>.type | Catalog 的类型: hive, hadoop 等，如果使用自定义Catalog，则不设置 |
| iceberg.catalog.<catalog_name>.catalog-impl	| Catalog 的实现类, 如果上面的 type 没有设置，则此参数必须设置 |
| iceberg.catalog.<catalog_name>.<key>	| Catalog 的其他配置项 |

#### 2.2.1 Hive

下面是一些使用 Hive CLI 的示例。如下所示注册一个名为 iceberg_hive 的 HiveCatalog:
```sql
SET iceberg.catalog.iceberg_hive.type=hive;
SET iceberg.catalog.iceberg_hive.uri=thrift://localhost:9083;
SET iceberg.catalog.iceberg_hive.clients=10;
SET iceberg.catalog.iceberg_hive.warehouse=hdfs://localhost:9000/user/hive/warehouse;

CREATE TABLE iceberg_test2 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
TBLPROPERTIES('iceberg.catalog'='iceberg_hive');

INSERT INTO iceberg_test2 values(1);
```
创建表之后可以查看表的详细信息：
```sql
CREATE TABLE `iceberg_test2`(
  `i` int COMMENT 'from deserializer')
ROW FORMAT SERDE
  'org.apache.iceberg.mr.hive.HiveIcebergSerDe'
STORED BY
  'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
LOCATION
  'hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_test2'
TBLPROPERTIES (
  'current-schema'='{"type":"struct","schema-id":0,"fields":[{"id":1,"name":"i","required":false,"type":"int"}]}',
  'current-snapshot-id'='7431247190671036215',
  'current-snapshot-summary'='{"added-data-files":"1","added-records":"1","added-files-size":"404","changed-partition-count":"1","total-records":"1","total-files-size":"404","total-data-files":"1","total-delete-files":"0","total-position-deletes":"0","total-equality-deletes":"0"}',
  'current-snapshot-timestamp-ms'='1692143521627',
  'engine.hive.enabled'='true',
  'external.table.purge'='TRUE',
  'iceberg.catalog'='iceberg_hive',
  'last_modified_by'='wy',
  'last_modified_time'='1692143506',
  'metadata_location'='hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_test2/metadata/00001-f5f12084-6ab5-48e7-b9fd-b4b2d1343d5e.metadata.json',
  'previous_metadata_location'='hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_test2/metadata/00000-61b4ac8a-92b0-4420-9a26-9e82f2582920.metadata.json',
  'snapshot-count'='1',
  'table_type'='ICEBERG',
  'transient_lastDdlTime'='1692143506',
  'uuid'='2c35f375-089e-4948-b59a-ed1053dd6a43')
```
与使用默认 HiveCatalog 相比，TBLPROPERTIES 中多了个一个 `iceberg.catalog` 配置。

#### 2.2.2 Hadoop

如下所示注册一个名为 iceberg_hadoop 的 HadoopCatalog:
```sql
SET iceberg.catalog.iceberg_hadoop.type=hadoop;
SET iceberg.catalog.iceberg_hadoop.warehouse=hdfs://localhost:9000/user/hadoop/warehouse;

CREATE TABLE iceberg_test3 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
LOCATION 'hdfs://localhost:9000/user/hadoop/warehouse/iceberg/iceberg_test3'
TBLPROPERTIES('iceberg.catalog'='iceberg_hadoop');

INSERT INTO iceberg_test3 values(1);
```

> 需要注意的是 LOCATION 路径为 `{iceberg.catalog.iceberg_hadoop.warehouse}/{database}/{table}` 的格式

创建表之后可以查看表的详细信息：
```sql
CREATE TABLE `iceberg_test3`(
  `i` int COMMENT 'from deserializer')
ROW FORMAT SERDE
  'org.apache.iceberg.mr.hive.HiveIcebergSerDe'
STORED BY
  'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
WITH SERDEPROPERTIES (
  'serialization.format'='1')
LOCATION
  'hdfs://localhost:9000/user/hadoop/warehouse/iceberg/iceberg_test3'
TBLPROPERTIES (
  'external.table.purge'='TRUE',
  'iceberg.catalog'='iceberg_hadoop',
  'last_modified_by'='wy',
  'last_modified_time'='1692144472',
  'table_type'='ICEBERG',
  'transient_lastDdlTime'='1692144472')
```
相比之前，这个变化还是比较大的。

#### 2.2.3 Glue

如下所示注册一个名为 iceberg_glue 的 GlueCatalog:
```sql
SET iceberg.catalog.iceberg_glue.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog;
SET iceberg.catalog.iceberg_glue.warehouse=s3://my-bucket/my/key/prefix;
SET iceberg.catalog.iceberg_glue.lock.table=myGlueLockTable;

CREATE TABLE iceberg_test4 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
LOCATION 'hdfs://localhost:9000/user/hadoop/warehouse/iceberg/iceberg_test3'
TBLPROPERTIES('iceberg.catalog'='iceberg_glue');

INSERT INTO iceberg_test3 values(1);
```

### 2.3 指定路径

如果 HDFS 中已经存在 iceberg 格式表，我们可以通过在 Hive 中创建 Icerberg 格式表指定对应的路径来映射数据。此时你需要设置 `iceberg.catalog=location_based_table`：
```sql
CREATE EXTERNAL TABLE iceberg_test5 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
LOCATION 'hdfs://localhost:9000/user/hadoop/warehouse/iceberg/iceberg_test3'
TBLPROPERTIES ('iceberg.catalog'='location_based_table');
```
创建表之后可以查看表的详细信息：
```sql
CREATE EXTERNAL TABLE `iceberg_test5`(
  `i` int COMMENT 'from deserializer')
ROW FORMAT SERDE
  'org.apache.iceberg.mr.hive.HiveIcebergSerDe'
STORED BY
  'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'
WITH SERDEPROPERTIES (
  'serialization.format'='1')
LOCATION
  'hdfs://localhost:9000/user/hadoop/warehouse/iceberg/iceberg_test3'
TBLPROPERTIES (
  'iceberg.catalog'='location_based_table',
  'table_type'='ICEBERG',
  'transient_lastDdlTime'='1692146162')
```

## 3. DDL

Hive 2.3.x 和 Hive 3.1.x 并不能完全支持下面所有的特性。详情请参阅功能支持段落。

与 Hive 4.0.0-alpha-1 一个最大的区别是 Hive 4.0.0-alpha-1 使用 STORED BY ICEBERG 来代替旧的 STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler'。

### 3.1 CREATE TABLE

#### 3.1.1 创建外部表

可以使用 Hive 的 CREATE EXTERNAL TABLE 命令可以创建 Iceberg 外部表:
```sql
CREATE EXTERNAL TABLE iceberg_external_test1 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler';
```
可以使用 describe formatted 命令查看表的具体信息：
```sql
hive (iceberg)> describe formatted iceberg_external_test1;
OK
# col_name            	data_type           	comment

i                   	int                 	from deserializer

# Detailed Table Information
Database:           	iceberg
Owner:              	wy
CreateTime:         	Wed Aug 16 12:16:00 CST 2023
LastAccessTime:     	UNKNOWN
Retention:          	0
Location:           	hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_external_test1
Table Type:         	EXTERNAL_TABLE
Table Parameters:
	EXTERNAL            	TRUE
	current-schema      	{\"type\":\"struct\",\"schema-id\":0,\"fields\":[{\"id\":1,\"name\":\"i\",\"required\":false,\"type\":\"int\"}]}
	engine.hive.enabled 	true
	external.table.purge	TRUE
	metadata_location   	hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_external_test1/metadata/00000-79196afd-8d5a-4d81-9441-a02c002fc527.metadata.json
	numFiles            	0
	numRows             	0
	rawDataSize         	0
	snapshot-count      	0
	storage_handler     	org.apache.iceberg.mr.hive.HiveIcebergStorageHandler
	table_type          	ICEBERG
	totalSize           	0
	transient_lastDdlTime	1692159360
	uuid                	e2865dcf-1df4-4bc6-893c-e058345fd800

# Storage Information
SerDe Library:      	org.apache.iceberg.mr.hive.HiveIcebergSerDe
InputFormat:        	org.apache.iceberg.mr.hive.HiveIcebergInputFormat
OutputFormat:       	org.apache.iceberg.mr.hive.HiveIcebergOutputFormat
Compressed:         	No
Num Buckets:        	0
Bucket Columns:     	[]
Sort Columns:       	[]
```
通过 Table Type 可以看到该表是一个外部表 EXTERNAL_TABLE。

#### 3.1.2 创建内部表

可以使用 Hive 的 CREATE TABLE 命令可以创建 Iceberg 内部表:
```sql
CREATE TABLE iceberg_internal_test1 (i int)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler';
```
可以使用 describe formatted 命令查看表的具体信息：
```sql
hive (iceberg)> describe formatted iceberg_internal_test1;
OK
# col_name            	data_type           	comment

i                   	int                 	from deserializer

# Detailed Table Information
Database:           	iceberg
Owner:              	wy
CreateTime:         	Wed Aug 16 12:21:34 CST 2023
LastAccessTime:     	UNKNOWN
Retention:          	0
Location:           	hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_internal_test1
Table Type:         	MANAGED_TABLE
Table Parameters:
	current-schema      	{\"type\":\"struct\",\"schema-id\":0,\"fields\":[{\"id\":1,\"name\":\"i\",\"required\":false,\"type\":\"int\"}]}
	engine.hive.enabled 	true
	external.table.purge	TRUE
	metadata_location   	hdfs://localhost:9000/user/hive/warehouse/iceberg.db/iceberg_internal_test1/metadata/00000-035cc7ba-f225-46e6-a57a-0941e54aff65.metadata.json
	numFiles            	0
	numRows             	0
	rawDataSize         	0
	snapshot-count      	0
	storage_handler     	org.apache.iceberg.mr.hive.HiveIcebergStorageHandler
	table_type          	ICEBERG
	totalSize           	0
	transient_lastDdlTime	1692159694
	uuid                	7ef7d4b5-b9c0-49ae-9cb2-43d8ec574255

# Storage Information
SerDe Library:      	org.apache.iceberg.mr.hive.HiveIcebergSerDe
InputFormat:        	org.apache.iceberg.mr.hive.HiveIcebergInputFormat
OutputFormat:       	org.apache.iceberg.mr.hive.HiveIcebergOutputFormat
Compressed:         	No
Num Buckets:        	0
Bucket Columns:     	[]
Sort Columns:       	[]
```
通过 Table Type 可以看到该表是一个内部表 MANAGED_TABLE。

#### 3.1.3 创建分区表

可以在使用 Hive 的 CREATE TABLE 或者 CREATE EXTERNAL TABLE 命令时通过 PARTITIONED BY 语句指定分区:
```sql
CREATE TABLE iceberg_partition_test1 (i int)
PARTITIONED BY (dt String)
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler';

INSERT INTO iceberg_partition_test1 values(1, '20230815');
```
Hive 语法创建分区表，不会在 HMS 中创建分区，而是将分区数据转换为 Iceberg 标识分区。这种情况下不能使用 Iceberg 的分区转换，例如：days(timestamp)，如果想要使用 Iceberg 格式表的分区转换标识分区，需要使用 Spark 或者 Flink 引擎创建表。

### 3.2 CREATE TABLE AS SELECT ?

`CREATE TABLE AS SELECT` 操作类似于本地 Hive 操作，但有一个重要的区别。Iceberg 表和对应的 Hive 表是在查询执行开始时创建的。当查询完成时数据才被插入/提交。因此，在一段短暂的时间内，表已经存在，但不包含任何数据。
```sql
CREATE TABLE iceberg_partition_test2
AS SELECT * FROM iceberg_partition_test1;
```
需要注意的是 CREATE-TABLE-AS-SELECT 模式不支持分区，否则会抛出如下异常：
```sql
FAILED: SemanticException [Error 10068]: CREATE-TABLE-AS-SELECT does not support partitioning in the target table
```
此外也不支持创建外部表：
```sql
FAILED: SemanticException [Error 10070]: CREATE-TABLE-AS-SELECT cannot create external table
```

### 3.3 CREATE TABLE LIKE TABLE

你可以通过 CREATE TABLE LIKE TABLE 命令来复制表结构。如果你已经有一个表，现在想创建一个一模一样的表，这个时候这个方法就很省时省力了：
```sql
CREATE TABLE iceberg_partition_test3 LIKE iceberg_partition_test1
STORED BY 'org.apache.iceberg.mr.hive.HiveIcebergStorageHandler';
```
需要注意的是复制时，只会复制表结构，不会复制表中的数据。

### 3.4 ALTER TABLE

#### 3.4.1 表属性 ?

只支持 HiveCatalog 表修改表属性。对于 HiveCatalog 表，Iceberg 表属性和存储在 HMS 中的 Hive 表属性保持同步。如下所示修改 `external.table.purge` 属性为 FALSE：
```sql
ALTER TABLE iceberg_external_test1 SET TBLPROPERTIES('external.table.purge'='FALSE');
```

```sql
FAILED: SemanticException [Error 10134]: ALTER TABLE cannot be used for a non-native table iceberg_partition_test1
```

> 需要注意的是此功能不适用于其他 Catalog 实现。

#### 3.4.2 Schema 演化

Hive 表 Schema 与 Iceberg 表保持同步。如果外部源(Impala/Spark/Java API/等)改变了 Schema，Hive 表会立即反映出这些变化。使用 Hive 命令修改表 Schema：
```sql
-- 增加列
ALTER TABLE iceberg_partition_test3 ADD COLUMNS (nickname string);
-- 重命名列
ALTER TABLE iceberg_partition_test3 CHANGE COLUMN i age int;
-- 修改列的顺序
ALTER TABLE iceberg_partition_test3 CHANGE COLUMN quantity quantity int AFTER price;
-- 修改列的类型
ALTER TABLE iceberg_partition_test3 CHANGE COLUMN price price long;
-- 删除列 使用 REPLACE COLUMN 移除列
ALTER TABLE iceberg_partition_test3 REPLACE COLUMNS (remaining string);
```

#### 3.4.3 分区演化

使用以下命令修改分区 Schema:
```sql
-- 将分区模式更改为新的标识分区
ALTER TABLE default.customers SET PARTITION SPEC (last_name);
--
ALTER TABLE order SET PARTITION SPEC (month(ts));
```

#### 3.4.4 表的迁移

您可以使用以下命令将 Avro/Parquet/ORC 外部表迁移到 Iceberg表:
```sql
ALTER TABLE t SET TBLPROPERTIES ('storage_handler'='org.apache.iceberg.mr.hive.HiveIcebergStorageHandler');
```
在迁移期间，数据文件不会更改，只会创建适当的 Iceberg 元数据文件。迁移完成后，将表作为普通 Iceberg 表处理。

### 3.5 TRUNCATE TABLE

使用如下命令清空表：
```sql
TRUNCATE TABLE iceberg_partition_test1;
```
需要注意的是不允许指定分区。

### 3.7 DROP TABLE

使用如下命令删除表：
```sql
DROP TABLE IF EXISTS iceberg_partition_test3;
DROP TABLE IF EXISTS iceberg_partition_test2 PURGE;
```

### 3.8 METADATA LOCATION

只有当新路径包含完全相同的元数据json时，才可以更改元数据位置(快照位置)。只有将表迁移到Iceberg后才能完成，这两个操作不能一步到位。

## 4. DML

### 4.1 SELECT

Iceberg 表上的 Select 语句工作方式与 Hive 相同。但是 Iceberg 在编译和执行方面要优于 Hive:
没有文件系统清单——在blob存储(如S3)上尤其重要
没有来自Metastore的分区列表
高级分区过滤—当可以计算分区键时，查询中不需要分区键
可以处理比普通Hive表更多的分区数吗
以下是冰山Hive读取支持的主要功能:

谓词下推:已经实现了Hive SQL WHERE子句的下推，以便这些过滤器可以在冰山表层以及Parquet和ORC reader上使用。
列投影:Hive SQL SELECT子句中的列被投影到冰山阅读器上，以减少读取的列数。
Hive查询引擎:
使用Hive 2.3。3.1 x。x同时支持MapReduce和Tez查询执行引擎。
Hive 4.0.0-alpha-1支持Tez查询执行引擎。
冰山表还没有实现一些高级/很少使用的优化，因此您应该检查您的单个查询。目前，存储在MetaStore中的统计信息也用于查询规划。这是我们计划在未来改进的东西。

### 4.2 INSERT INTO

Hive 支持标准的单表 INSERT INTO 操作:
```sql
INSERT INTO table_a VALUES ('a', 1);
INSERT INTO table_a SELECT...;
```
此外还支持多表插入，但它不是原子的。每次提交一个表。在提交过程中可以看到部分更改，失败可能会导致部分更改提交。单表内的更改会保持原子性。下面是一个在Hive SQL中一次插入多个表的例子:
```sql
FROM customers
   INSERT INTO target1 SELECT customer_id, first_name
   INSERT INTO target2 SELECT last_name, customer_id;
```

### 4.3 INSERT OVERWRITE

INSERT OVERWRITE 可以用查询结果替换表中的数据。覆盖是 Iceberg 表的一个原子操作。对于非分区表，会删除表的内容；对于分区表，包含 SELECT 查询生成行的分区会被替换。
```sql
INSERT OVERWRITE TABLE target SELECT * FROM source;
```

### 4.4 QUERYING METADATA TABLES

Hive 支持对 Iceberg 元数据表的查询。这些表可以作为普通的 Hive 表使用，因此可以使用投影/连接/过滤器等。如果要引用元数据表，需要使用表的全名，例如 `<DB_NAME>.<TABLE_NAME>.<METADATA_TABLE_NAME>`。目前 Hive 中可用的元数据表如下:
- files
- entries
- snapshots
- manifests
- partitions

```sql
SELECT * FROM default.table_a.files;
```

### 4.5 TIMETRAVEL

Hive 支持基于快照 id 和基于时间的时间旅行查询。对于视图，可以使用投影/连接/过滤器等。该函数的语法如下:
```sql
SELECT * FROM table_a FOR SYSTEM_TIME AS OF '2021-08-09 10:35:57';
SELECT * FROM table_a FOR SYSTEM_VERSION AS OF 1234567;
```
您可以使用 Hive 中的 ALTER table 语句来过期 Iceberg 表快照。您应该定期过期快照，以删除不再需要的数据文件，并减少表元数据的大小。每次从 Hive 写入 Iceberg 表都会创建一个表的新快照或版本。快照可以用于时间旅行查询，或者可以将表回滚到任何有效的快照。快照会不断累积，直到 expire_snapshots 操作过期。对时间戳为 `2021-12-09 05:39:18.689000000` 的快照进行过期处理：
```sql
ALTER TABLE test_table EXECUTE expire_snapshots('2021-12-09 05:39:18.689000000');
```

### 4.6 Type compatibility

Hive 和 Iceberg 支持不同的数据类型。Iceberg 可以自动执行类型转换，但不是针对所有组合，因此在设计表中列的类型之前，您应该需要了解 Iceberg 中的类型转换。您可以通过 Hadoop 配置启用自动转换(默认未启用):

| 配置 key     | 默认值     | 描述 |
| :------------- | :------------- | :------------- |
| iceberg.mr.schema.auto.conversion | false | Hive是否应该执行类型自动转换 |

### 4.7 Hive type to Iceberg type

此类型转换表描述了如何将 Hive 类型转换为 Iceberg 类型。这种转换既适用于创建 Iceberg 表，也适用于通过 Hive 写入 Iceberg 表。

| Hive | Iceberg | 备注 |
| :------------- | :------------- | :------------- |
| boolean  | boolean | |
| short	| integer	| auto-conversion |
| byte	| integer	| auto-conversion |
| integer	| integer | |
| long	| long | |
| float	| float | |
| double	| double | |
| date	| date |  |
| timestamp	| timestamp | without timezone |
| timestamplocaltz	| timestamp with timezone	| Hive 3 only |
| interval_year_month	| | not supported |
| interval_day_time	| | not supported |
| char	| string	| auto-conversion |
| varchar	| string	| auto-conversion |
| string	| string | |
| binary	| binary | |
| decimal	| decimal | |
| struct	| struct | |
| list	| list | |
| map	| map | |
| union	| | not supported |

### 4.8 Table rollback

回滚 Iceberg 表的数据到旧表快照的状态。回滚到指定时间戳之前的最后一个快照:
```sql
ALTER TABLE ice_t EXECUTE ROLLBACK('2022-05-12 00:00:00')
```
回滚到指定快照ID:
```sql
ALTER TABLE ice_t EXECUTE ROLLBACK(1111);
```















> 参考：[]()
