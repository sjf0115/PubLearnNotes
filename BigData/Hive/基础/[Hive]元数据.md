Hive中元数据包括表的名称，表的列和分区及其属性，表的属性（是否是外部表），表的数据所在目录等；

Hive的元数据需要面临不断的更新，修改和读取，所以它不适合使用HDFS来存储，使用关系性数据库来存储，如mysql。

下面主要介绍一下这些元数据储存的数据表（以mysql为例）：

### 1. 储存Hive版本的元数据表（VERSION）

#### 1.1 表结构
```
mysql> desc VERSION;
+-----------------+--------------+------+-----+---------+-------+
| Field           | Type         | Null | Key | Default | Extra |
+-----------------+--------------+------+-----+---------+-------+
| VER_ID          | bigint(20)   | NO   | PRI | NULL    |       |
| SCHEMA_VERSION  | varchar(127) | NO   |     | NULL    |       |
| VERSION_COMMENT | varchar(255) | YES  |     | NULL    |       |
+-----------------+--------------+------+-----+---------+-------+
3 rows in set (0.00 sec)
```

==备注==

类型 | 说明
---|---
VER_ID | 主键ID
SCHEMA_VERSION | Hive版本
VERSION_COMMENT| 版本说明


#### 1.2 数据信息
```
mysql> select * from VERSION;
+--------+----------------+----------------------------+
| VER_ID | SCHEMA_VERSION | VERSION_COMMENT            |
+--------+----------------+----------------------------+
|      1 | 2.0.0          | Hive release version 2.0.0 |
+--------+----------------+----------------------------+
1 row in set (0.00 sec)
```

==备注==

如果该表出现问题，则进不了Hive-Cli。如果该表不存在，当启动Hive-Cli时候，就会报错”Table ‘hive.version’ doesn’t exist”。


### 2. Hive数据库相关的元数据表（DBS）

#### 2.1 表结构
```
mysql> desc DBS;
+-----------------+---------------+------+-----+---------+-------+
| Field           | Type          | Null | Key | Default | Extra |
+-----------------+---------------+------+-----+---------+-------+
| DB_ID           | bigint(20)    | NO   | PRI | NULL    |       |
| DESC            | varchar(4000) | YES  |     | NULL    |       |
| DB_LOCATION_URI | varchar(4000) | NO   |     | NULL    |       |
| NAME            | varchar(128)  | YES  | UNI | NULL    |       |
| OWNER_NAME      | varchar(128)  | YES  |     | NULL    |       |
| OWNER_TYPE      | varchar(10)   | YES  |     | NULL    |       |
+-----------------+---------------+------+-----+---------+-------+
6 rows in set (0.00 sec)
```

#### 2.2 说明

元数据表字段|说明
---|---
DB_ID|	数据库ID
DESC|	数据库描述
DB_LOCATION_URI|	数据库HDFS路径
NAME|	数据库名
OWNER_NAME|	所有者用户名
OWNER_TYPE|	所有者角色


#### 2.3 数据信息
```
mysql> select * from DBS;
+-------+-----------------------+------------------------------------------------------+---------+------------+------------+
| DB_ID | DESC                  | DB_LOCATION_URI                                      | NAME    | OWNER_NAME | OWNER_TYPE |
+-------+-----------------------+------------------------------------------------------+---------+------------+------------+
|     1 | Default Hive database | hdfs://localhost:9000/user/hive/warehouse            | default | public     | ROLE       |
|     6 | NULL                  | hdfs://localhost:9000/user/hive/warehouse/test_db.db | test_db | xiaosi     | USER       |
+-------+-----------------------+------------------------------------------------------+---------+------------+------------+
2 rows in set (0.00 sec)
```

### 3. Hive表相关的元数据表（TBLS，TABLE_PARAMS）

#### 3.1 TBLS

该表中存储Hive表、视图、索引表的基本信息。

##### 3.1.1 表结构
```
mysql> desc TBLS;
+--------------------+--------------+------+-----+---------+-------+
| Field              | Type         | Null | Key | Default | Extra |
+--------------------+--------------+------+-----+---------+-------+
| TBL_ID             | bigint(20)   | NO   | PRI | NULL    |       |
| CREATE_TIME        | int(11)      | NO   |     | NULL    |       |
| DB_ID              | bigint(20)   | YES  | MUL | NULL    |       |
| LAST_ACCESS_TIME   | int(11)      | NO   |     | NULL    |       |
| OWNER              | varchar(767) | YES  |     | NULL    |       |
| RETENTION          | int(11)      | NO   |     | NULL    |       |
| SD_ID              | bigint(20)   | YES  | MUL | NULL    |       |
| TBL_NAME           | varchar(128) | YES  | MUL | NULL    |       |
| TBL_TYPE           | varchar(128) | YES  |     | NULL    |       |
| VIEW_EXPANDED_TEXT | mediumtext   | YES  |     | NULL    |       |
| VIEW_ORIGINAL_TEXT | mediumtext   | YES  |     | NULL    |       |
+--------------------+--------------+------+-----+---------+-------+
11 rows in set (0.00 sec)
```

##### 3.1.2 说明

元数据表字段|说明
---|---
TBL_ID|	表ID
CREATE_TIME|	创建时间
DB_ID|	数据库ID
LAST_ACCESS_TIME|	上次访问时间
OWNER|	所有者
RETENTION|	保留字段
SD_ID|	序列化配置信息
TBL_NAME|	表名
TBL_TYPE|	表类型
VIEW_EXPANDED_TEXT|	视图的详细HQL语句
VIEW_ORIGINAL_TEXT|	视图的原始HQL语句

#### 3.1.3 数据信息
```
mysql> select * from TBLS;
+--------+-------------+-------+------------------+--------+-----------+-------+------------------------+---------------+--------------------+--------------------+
| TBL_ID | CREATE_TIME | DB_ID | LAST_ACCESS_TIME | OWNER  | RETENTION | SD_ID | TBL_NAME               | TBL_TYPE      | VIEW_EXPANDED_TEXT | VIEW_ORIGINAL_TEXT |
+--------+-------------+-------+------------------+--------+-----------+-------+------------------------+---------------+--------------------+--------------------+
|      1 |  1464158030 |     1 |                0 | xiaosi |         0 |     1 | employee               | MANAGED_TABLE | NULL               | NULL               |
|      6 |  1464162665 |     6 |                0 | xiaosi |         0 |     6 | tb_recnet_attention_pv | MANAGED_TABLE | NULL               | NULL               |
|     11 |  1464175616 |     6 |                0 | xiaosi |         0 |    11 | manage_table           | MANAGED_TABLE | NULL               | NULL               |
|     16 |  1465802584 |     1 |                0 | xiaosi |         0 |    16 | employees              | MANAGED_TABLE | NULL               | NULL               |
|     21 |  1465803291 |     1 |                0 | xiaosi |         0 |    21 | tb_recnet_attention_pv | MANAGED_TABLE | NULL               | NULL               |
|     22 |  1465803911 |     1 |                0 | xiaosi |         0 |    22 | recent_attention       | MANAGED_TABLE | NULL               | NULL               |
|     26 |  1465805535 |     6 |                0 | xiaosi |         0 |    26 | recent_attention       | MANAGED_TABLE | NULL               | NULL               |
+--------+-------------+-------+------------------+--------+-----------+-------+------------------------+---------------+--------------------+--------------------+
7 rows in set (0.00 sec)
```
#### 3.2 TABLE_PARAMS

该表存储表/视图的属性信息。

##### 3.2.1 表结构
```
mysql> desc TABLE_PARAMS;
+-------------+---------------+------+-----+---------+-------+
| Field       | Type          | Null | Key | Default | Extra |
+-------------+---------------+------+-----+---------+-------+
| TBL_ID      | bigint(20)    | NO   | PRI | NULL    |       |
| PARAM_KEY   | varchar(256)  | NO   | PRI | NULL    |       |
| PARAM_VALUE | varchar(4000) | YES  |     | NULL    |       |
+-------------+---------------+------+-----+---------+-------+
3 rows in set (0.00 sec)
```
##### 3.2.2 说明

元数据表字段	|说明
---|---
TBL_ID	|表ID
PARAM_KEY|	属性名
PARAM_VALUE|	属性值

##### 3.3.3 数据信息
```
mysql> select * from TABLE_PARAMS;
+--------+-----------------------+------------------------+
| TBL_ID | PARAM_KEY             | PARAM_VALUE            |
+--------+-----------------------+------------------------+
|      1 | COLUMN_STATS_ACCURATE | {"BASIC_STATS":"true"} |
|      1 | comment               | employee info          |
|      1 | numFiles              | 1                      |
|      1 | totalSize             | 73                     |
|      1 | transient_lastDdlTime | 1464160894             |
|      6 | COLUMN_STATS_ACCURATE | {"BASIC_STATS":"true"} |
|      6 | comment               | UV PV detail           |
|      6 | numFiles              | 1                      |
|      6 | totalSize             | 616                    |
|      6 | transient_lastDdlTime | 1464163018             |
|     11 | COLUMN_STATS_ACCURATE | {"BASIC_STATS":"true"} |
|     11 | numFiles              | 1                      |
|     11 | totalSize             | 616                    |
|     11 | transient_lastDdlTime | 1464175716             |
|     16 | comment               | ?????                  |
|     16 | transient_lastDdlTime | 1465802584             |
|     21 | comment               | UV PV detail           |
|     21 | transient_lastDdlTime | 1465803291             |
|     22 | comment               | UV PV detail           |
|     22 | transient_lastDdlTime | 1465803911             |
|     26 | COLUMN_STATS_ACCURATE | {"BASIC_STATS":"true"} |
|     26 | comment               | UV PV detail           |
|     26 | numFiles              | 1                      |
|     26 | totalSize             | 616                    |
|     26 | transient_lastDdlTime | 1465808611             |
+--------+-----------------------+------------------------+
25 rows in set (0.00 sec)
```

#### 3.3  TBL_PRIVS

该表存储表/视图的授权信息

##### 3.3.1 表结构
```
mysql> desc TBL_PRIVS;
+----------------+--------------+------+-----+---------+-------+
| Field          | Type         | Null | Key | Default | Extra |
+----------------+--------------+------+-----+---------+-------+
| TBL_GRANT_ID   | bigint(20)   | NO   | PRI | NULL    |       |
| CREATE_TIME    | int(11)      | NO   |     | NULL    |       |
| GRANT_OPTION   | smallint(6)  | NO   |     | NULL    |       |
| GRANTOR        | varchar(128) | YES  |     | NULL    |       |
| GRANTOR_TYPE   | varchar(128) | YES  |     | NULL    |       |
| PRINCIPAL_NAME | varchar(128) | YES  |     | NULL    |       |
| PRINCIPAL_TYPE | varchar(128) | YES  |     | NULL    |       |
| TBL_PRIV       | varchar(128) | YES  |     | NULL    |       |
| TBL_ID         | bigint(20)   | YES  | MUL | NULL    |       |
+----------------+--------------+------+-----+---------+-------+
9 rows in set (0.00 sec)
```

##### 3.3.2 说明

元数据表字段	|说明
---|---
TBL_GRANT_ID|	授权ID
CREATE_TIME|	授权时间
GRANTOR|	授权执行用户
GRANTOR_TYPE|	授权者类型
PRINCIPAL_NAME|	被授权用户
PRINCIPAL_TYPE|	被授权用户类型
TBL_PRIV|	权限
TBL_ID|	表ID

##### 3.3.3 数据信息
```
mysql> select * from TBL_PRIVS;
+--------------+-------------+--------------+---------+--------------+----------------+----------------+----------+--------+
| TBL_GRANT_ID | CREATE_TIME | GRANT_OPTION | GRANTOR | GRANTOR_TYPE | PRINCIPAL_NAME | PRINCIPAL_TYPE | TBL_PRIV | TBL_ID |
+--------------+-------------+--------------+---------+--------------+----------------+----------------+----------+--------+
|            1 |  1464158031 |            1 | xiaosi  | USER         | xiaosi         | USER           | INSERT   |      1 |
|            2 |  1464158031 |            1 | xiaosi  | USER         | xiaosi         | USER           | SELECT   |      1 |
|            3 |  1464158031 |            1 | xiaosi  | USER         | xiaosi         | USER           | UPDATE   |      1 |
|            4 |  1464158031 |            1 | xiaosi  | USER         | xiaosi         | USER           | DELETE   |      1 |
|            6 |  1464162665 |            1 | xiaosi  | USER         | xiaosi         | USER           | INSERT   |      6 |
|            7 |  1464162665 |            1 | xiaosi  | USER         | xiaosi         | USER           | SELECT   |      6 |
|            8 |  1464162665 |            1 | xiaosi  | USER         | xiaosi         | USER           | UPDATE   |      6 |
|            9 |  1464162665 |            1 | xiaosi  | USER         | xiaosi         | USER           | DELETE   |      6 |
|           11 |  1464175616 |            1 | xiaosi  | USER         | xiaosi         | USER           | INSERT   |     11 |
|           12 |  1464175616 |            1 | xiaosi  | USER         | xiaosi         | USER           | SELECT   |     11 |
|           13 |  1464175616 |            1 | xiaosi  | USER         | xiaosi         | USER           | UPDATE   |     11 |
|           14 |  1464175616 |            1 | xiaosi  | USER         | xiaosi         | USER           | DELETE   |     11 |
|           16 |  1465802584 |            1 | xiaosi  | USER         | xiaosi         | USER           | INSERT   |     16 |
|           17 |  1465802584 |            1 | xiaosi  | USER         | xiaosi         | USER           | SELECT   |     16 |
|           18 |  1465802584 |            1 | xiaosi  | USER         | xiaosi         | USER           | UPDATE   |     16 |
|           19 |  1465802584 |            1 | xiaosi  | USER         | xiaosi         | USER           | DELETE   |     16 |
|           21 |  1465803292 |            1 | xiaosi  | USER         | xiaosi         | USER           | INSERT   |     21 |
|           22 |  1465803292 |            1 | xiaosi  | USER         | xiaosi         | USER           | SELECT   |     21 |
|           23 |  1465803292 |            1 | xiaosi  | USER         | xiaosi         | USER           | UPDATE   |     21 |
|           24 |  1465803292 |            1 | xiaosi  | USER         | xiaosi         | USER           | DELETE   |     21 |
|           25 |  1465803911 |            1 | xiaosi  | USER         | xiaosi         | USER           | INSERT   |     22 |
|           26 |  1465803911 |            1 | xiaosi  | USER         | xiaosi         | USER           | SELECT   |     22 |
|           27 |  1465803911 |            1 | xiaosi  | USER         | xiaosi         | USER           | UPDATE   |     22 |
|           28 |  1465803911 |            1 | xiaosi  | USER         | xiaosi         | USER           | DELETE   |     22 |
|           31 |  1465805535 |            1 | xiaosi  | USER         | xiaosi         | USER           | INSERT   |     26 |
|           32 |  1465805535 |            1 | xiaosi  | USER         | xiaosi         | USER           | SELECT   |     26 |
|           33 |  1465805535 |            1 | xiaosi  | USER         | xiaosi         | USER           | UPDATE   |     26 |
|           34 |  1465805535 |            1 | xiaosi  | USER         | xiaosi         | USER           | DELETE   |     26 |
+--------------+-------------+--------------+---------+--------------+----------------+----------------+----------+--------+
28 rows in set (0.00 sec)
```

### 4. Hive文件存储信息相关的元数据表（SDS，SD_PARAMS，SERDES，SERDE_PARAMS）

由于HDFS支持的文件格式很多，而建Hive表时候也可以指定各种文件格式，Hive在将HQL解析成MapReduce时候，需要使用哪种格式去读写HDFS文件，而这些信息就保存在这几张表中。

#### 4.1 SDS

该表保存文件存储的基本信息，如INPUT_FORMAT、OUTPUT_FORMAT、是否压缩等。TBLS表使用SD_ID字段与该表关联，可以获取Hive表的存储信息。

##### 4.1.1 表结构
```
mysql> desc SDS;
+---------------------------+---------------+------+-----+---------+-------+
| Field                     | Type          | Null | Key | Default | Extra |
+---------------------------+---------------+------+-----+---------+-------+
| SD_ID                     | bigint(20)    | NO   | PRI | NULL    |       |
| CD_ID                     | bigint(20)    | YES  | MUL | NULL    |       |
| INPUT_FORMAT              | varchar(4000) | YES  |     | NULL    |       |
| IS_COMPRESSED             | bit(1)        | NO   |     | NULL    |       |
| IS_STOREDASSUBDIRECTORIES | bit(1)        | NO   |     | NULL    |       |
| LOCATION                  | varchar(4000) | YES  |     | NULL    |       |
| NUM_BUCKETS               | int(11)       | NO   |     | NULL    |       |
| OUTPUT_FORMAT             | varchar(4000) | YES  |     | NULL    |       |
| SERDE_ID                  | bigint(20)    | YES  | MUL | NULL    |       |
+---------------------------+---------------+------+-----+---------+-------+
9 rows in set (0.00 sec)
```
##### 4.1.2 说明

元数据表字段|	说明
---|---
SD_ID|	存储信息ID
CD_ID|	字段信息表主键ID
INPUT_FORMAT|	文件输入格式
IS_COMPRESSED|	是否压缩
IS_STOREDASSUBDIRECTORIES|	是否以子目录存储
LOCATION|	HDFS路径
NUM_BUCKETS|	分桶数量
OUTPUT_FORMAT|	文件输出格式
SERDE_ID|	序列化类ID

##### 4.1.3 数据信息

```
mysql> select * from SDS;
+-------+-------+------------------------------------------+---------------+---------------------------+-----------------------------------------------------------------------------+-------------+------------------------------------------------------------+----------+
| SD_ID | CD_ID | INPUT_FORMAT                             | IS_COMPRESSED | IS_STOREDASSUBDIRECTORIES | LOCATION                                                                    | NUM_BUCKETS | OUTPUT_FORMAT                                              | SERDE_ID |
+-------+-------+------------------------------------------+---------------+---------------------------+-----------------------------------------------------------------------------+-------------+------------------------------------------------------------+----------+
|     1 |     1 | org.apache.hadoop.mapred.TextInputFormat |               |                           | hdfs://localhost:9000/user/hive/warehouse/employee                          |          -1 | org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat |        1 |
|     6 |     6 | org.apache.hadoop.mapred.TextInputFormat |               |                           | hdfs://localhost:9000/user/hive/warehouse/test_db.db/tb_recnet_attention_pv |          -1 | org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat |        6 |
|    11 |    11 | org.apache.hadoop.mapred.TextInputFormat |               |                           | hdfs://localhost:9000/user/hive/warehouse/test_db.db/manage_table           |          -1 | org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat |       11 |
|    16 |    16 | org.apache.hadoop.mapred.TextInputFormat |               |                           | hdfs://localhost:9000/home/xiaosi/hive/warehouse/employees                  |          -1 | org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat |       16 |
|    21 |    21 | org.apache.hadoop.mapred.TextInputFormat |               |                           | hdfs://localhost:9000/home/xiaosi/hive/warehouse/tb_recnet_attention_pv     |          -1 | org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat |       21 |
|    22 |    22 | org.apache.hadoop.mapred.TextInputFormat |               |                           | hdfs://localhost:9000/home/xiaosi/hive/warehouse/recent_attention           |          -1 | org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat |       22 |
|    26 |    26 | org.apache.hadoop.mapred.TextInputFormat |               |                           | hdfs://localhost:9000/user/hive/warehouse/test_db.db/rece
```

#### 4.2  SD_PARAMS

该表存储Hive存储的属性信息，在创建表时候使用。STORED BY ‘storage.handler.class.name’ [WITH SERDEPROPERTIES (…)指定。

##### 4.2.1 表结构
```
mysql> desc SD_PARAMS;
+-------------+---------------+------+-----+---------+-------+
| Field       | Type          | Null | Key | Default | Extra |
+-------------+---------------+------+-----+---------+-------+
| SD_ID       | bigint(20)    | NO   | PRI | NULL    |       |
| PARAM_KEY   | varchar(256)  | NO   | PRI | NULL    |       |
| PARAM_VALUE | varchar(4000) | YES  |     | NULL    |       |
+-------------+---------------+------+-----+---------+-------+
3 rows in set (0.00 sec)
```
##### 4.2.2 说明

元数据表字段|	说明
---|---
SD_ID|	SDS主键D
PARAM_KEY|	存储属性名
PARAM_VALUE|存储属性值

#### 4.3 SERDES 

该表存储序列化使用的类信息

##### 4.3.1 表结构
```
mysql> desc SERDES;
+----------+---------------+------+-----+---------+-------+
| Field    | Type          | Null | Key | Default | Extra |
+----------+---------------+------+-----+---------+-------+
| SERDE_ID | bigint(20)    | NO   | PRI | NULL    |       |
| NAME     | varchar(128)  | YES  |     | NULL    |       |
| SLIB     | varchar(4000) | YES  |     | NULL    |       |
+----------+---------------+------+-----+---------+-------+
3 rows in set (0.01 sec)
```
##### 4.3.2 说明

元数据表字段|	说明
---|---
SERDE_ID|	序列化类配置ID
NAME|	序列化类别名
SLIB|	序列化类

##### 4.3.3 数据信息
```
mysql> select * from SERDES;
+----------+------+----------------------------------------------------+
| SERDE_ID | NAME | SLIB                                               |
+----------+------+----------------------------------------------------+
|        1 | NULL | org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe |
|        6 | NULL | org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe |
|       11 | NULL | org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe |
|       16 | NULL | org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe |
|       21 | NULL | org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe |
|       22 | NULL | org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe |
|       26 | NULL | org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe |
+----------+------+----------------------------------------------------+
7 rows in set (0.00 sec)
```

### 5. Hive表字段相关的元数据表（COLUMNS_V2）

该表存储表中字段信息。

#### 5.1 表结构
```
mysql> desc COLUMNS_V2;
+-------------+---------------+------+-----+---------+-------+
| Field       | Type          | Null | Key | Default | Extra |
+-------------+---------------+------+-----+---------+-------+
| CD_ID       | bigint(20)    | NO   | PRI | NULL    |       |
| COMMENT     | varchar(256)  | YES  |     | NULL    |       |
| COLUMN_NAME | varchar(767)  | NO   | PRI | NULL    |       |
| TYPE_NAME   | varchar(4000) | YES  |     | NULL    |       |
| INTEGER_IDX | int(11)       | NO   |     | NULL    |       |
+-------------+---------------+------+-----+---------+-------+
5 rows in set (0.00 sec)
```
#### 5.2 说明

元数据表字段|	说明
---|---
CD_ID|	字段信息ID
COMMENT|	字段注释
COLUMN_NAME|	字段名
TYPE_NAME|	字段类型
INTEGER_IDX|	字段顺序

#### 5.3 数据信息
```
mysql> select * from COLUMNS_V2;
+-------+---------+--------------+-------------------------------------+-------------+
| CD_ID | COMMENT | COLUMN_NAME  | TYPE_NAME                           | INTEGER_IDX |
+-------+---------+--------------+-------------------------------------+-------------+
|     1 | NULL    | department   | string                              |           2 |
|     1 | NULL    | id           | int                                 |           0 |
|     1 | NULL    | name         | string                              |           1 |
|     6 | NULL    | dt           | string                              |           0 |
|     6 | NULL    | platform     | string                              |           1 |
|     6 | NULL    | pv           | int                                 |           2 |
|     6 | NULL    | uv           | int                                 |           3 |
|    11 | NULL    | dt           | string                              |           0 |
|    11 | NULL    | platform     | string                              |           1 |
|    11 | NULL    | pv           | int                                 |           2 |
|    11 | NULL    | uv           | int                                 |           3 |
|    16 | ????    | address      | struct<city:string,province:string> |           4 |
|    16 | ????    | deductions   | map<string,float>                   |           3 |
|    16 | ??      | name         | string                              |           0 |
|    16 | ??      | salary       | float                               |           1 |
|    16 | ??      | subordinates | array<string>                       |           2 |
|    21 | NULL    | dt           | string                              |           0 |
|    21 | NULL    | platform     | string                              |           1 |
|    21 | NULL    | pv           | int                                 |           2 |
|    21 | NULL    | v            | int                                 |           3 |
|    22 | NULL    | dt           | string                              |           0 |
|    22 | NULL    | platform     | string                              |           1 |
|    22 | NULL    | pv           | int                                 |           2 |
|    22 | NULL    | v            | int                                 |           3 |
|    26 | NULL    | dt           | string                              |           0 |
|    26 | NULL    | platform     | string                              |           1 |
|    26 | NULL    | pv           | int                                 |           2 |
|    26 | NULL    | v            | int                                 |           3 |
+-------+---------+--------------+-------------------------------------+-------------+
28 rows in set (0.00 sec)
```

### 6. Hive表分区相关的元数据表（PARTITIONS、PARTITION_KEYS、PARTITION_KEY_VALS、PARTITION_PARAMS）

#### 6.1 PARTITIONS

该表存储表分区的基本信息。

##### 6.1.1 表结构
```
mysql> desc PARTITIONS;
+------------------+--------------+------+-----+---------+-------+
| Field            | Type         | Null | Key | Default | Extra |
+------------------+--------------+------+-----+---------+-------+
| PART_ID          | bigint(20)   | NO   | PRI | NULL    |       |
| CREATE_TIME      | int(11)      | NO   |     | NULL    |       |
| LAST_ACCESS_TIME | int(11)      | NO   |     | NULL    |       |
| PART_NAME        | varchar(767) | YES  | MUL | NULL    |       |
| SD_ID            | bigint(20)   | YES  | MUL | NULL    |       |
| TBL_ID           | bigint(20)   | YES  | MUL | NULL    |       |
+------------------+--------------+------+-----+---------+-------+
6 rows in set (0.00 sec)
```
##### 6.1.2 说明

元数据表字段|	说明
---|---
PART_ID|	表分区ID
CREATE_TIME|	分区创建时间
LAST_ACCESS_TIME|	最后一次访问时间
PART_NAME|	分区名
SD_ID|	分区存储ID
TBL_ID|	表ID

#### 6.2 PARTITION_KEYS

该表存储分区的字段信息。

##### 6.2.1 表结构
```
mysql> desc PARTITION_KEYS;
+--------------+---------------+------+-----+---------+-------+
| Field        | Type          | Null | Key | Default | Extra |
+--------------+---------------+------+-----+---------+-------+
| TBL_ID       | bigint(20)    | NO   | PRI | NULL    |       |
| PKEY_COMMENT | varchar(4000) | YES  |     | NULL    |       |
| PKEY_NAME    | varchar(128)  | NO   | PRI | NULL    |       |
| PKEY_TYPE    | varchar(767)  | NO   |     | NULL    |       |
| INTEGER_IDX  | int(11)       | NO   |     | NULL    |       |
+--------------+---------------+------+-----+---------+-------+
5 rows in set (0.00 sec)
```


#### 6.3 PARTITION_KEY_VALS

该表存储分区字段值。

##### 6.3.1 表结构
```
mysql> desc PARTITION_KEY_VALS;
+--------------+--------------+------+-----+---------+-------+
| Field        | Type         | Null | Key | Default | Extra |
+--------------+--------------+------+-----+---------+-------+
| PART_ID      | bigint(20)   | NO   | PRI | NULL    |       |
| PART_KEY_VAL | varchar(256) | YES  |     | NULL    |       |
| INTEGER_IDX  | int(11)      | NO   | PRI | NULL    |       |
+--------------+--------------+------+-----+---------+-------+
3 rows in set (0.00 sec)
```





