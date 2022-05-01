---
layout: post
author: sjf0115
title: DataX 离线同步实战 MySQL Reader 与 Writer
date: 2022-04-30 22:17:17
tags:
  - DataX

categories: DataX
permalink: datax-mysql-reader-writer
---

> DataX 版本：3.0

> Github主页地址：https://github.com/alibaba/DataX

## 1. MySQL Reader

MySQL Reader 插件实现了从 MySQL 读取数据。在底层实现上，MySQL Reader 通过 JDBC 连接远程 MySQL 数据库，并执行相应的 SQL 语句将数据从 MySQL 数据库中查询出来。不同于其他关系型数据库，MySQL Reader 不支持 FetchSize。

MySQL Reader 插件支持读取表和视图。表字段可以依序指定全部列、指定部分列、调整列顺序、指定常量字段和配置 MySQL 的函数，例如 now() 等。

### 1.1 实现原理

简而言之，MySQL Reader 通过 JDBC 连接器连接到远程的 MySQL 数据库，并根据用户配置的信息生成查询 SELECT SQL 语句，然后发送到远程 MySQL 数据库，并将该 SQL 执行返回结果使用 DataX 自定义的数据类型拼装为抽象的数据集，并传递给下游 Writer 处理。

对于用户配置 Table、Column、Where 的信息，MySQL Reader 将其拼接为 SQL 语句发送到 MySQL 数据库；对于用户配置 QuerySql 信息，MySQL Reader 直接将其发送到 MySQL 数据库。

### 1.2 配置样例

```json
{
    "job": {
        "content": [
            {
                "reader": {
                    "name": "mysqlreader",
                    "parameter": {
                        "column": [],
                        "connection": [
                            {
                                "jdbcUrl": [],
                                "table": []
                            }
                        ],
                        "password": "",
                        "username": "",
                        "where": ""
                    }
                },
                "writer": {
                    "name": "hdfswriter",
                    "parameter": {
                        "column": [],
                        "compress": "",
                        "defaultFS": "",
                        "fieldDelimiter": "",
                        "fileName": "",
                        "fileType": "",
                        "path": "",
                        "writeMode": ""
                    }
                }
            }
        ],
        "setting": {
            "speed": {
                "channel": ""
            }
        }
    }
}
```

## 1.3 参数说明

- jdbcUrl：描述的是到对端数据库的JDBC连接信息，使用JSON的数组描述，并支持一个库填写多个连接地址。之所以使用JSON数组描述连接信息，是因为阿里集团内部支持多个IP探测，如果配置了多个，MysqlReader 可以依次探测ip的可连接性，直到选择一个合法的IP。如果全部连接失败，MysqlReader报错。 注意，jdbcUrl必须包含在connection配置单元中。对于阿里集团外部使用情况，JSON数组填写一个JDBC连接即可。
- username：必选字段，数据源的用户名。
- password：必选字段，数据源指定用户名的密码。
- table：必选字段，需要同步的表。可以支持多张表，使用 JSON 数组表示。当配置多张表时，用户自己需保证多张表是同一 Schema 结构。注意，table 必须包含在 connection 配置单元中。
- column：必选字段，表中需要需要同步的列名。可以同步多列，使用 JSON 数组表示。用户使用 `*` 表示同步所有列，例如 `['*']`。支持列裁剪，即列可以挑选部分列进行导出；支持列换序，即列可以不按照表 Schema 信息进行导出。支持常量配置，用户需要按照 MySQL SQL 语法格式: `["id", "`table`", "1", "'bazhen.csy'", "null", "to_char(a + 1)", "2.3" , "true"]` id 为普通列名，`table` 为包含保留字的列名，1为整形数字常量，'bazhen.csy'为字符串常量，null为空指针，to_char(a + 1)为表达式，2.3为浮点数，true为布尔值。
- splitPk：可选字段，数据分片的键。MysqlReader 进行数据抽取时，如果指定 splitPk，表示用户希望使用 splitPk 代表的字段进行数据分片，DataX 因此会启动并发任务进行数据同步，这样可以大大提供数据同步的效能。推荐 splitPk 用户使用表主键，因为表主键通常情况下比较均匀，因此切分出来的分片也不容易出现数据热点。目前splitPk仅支持整形数据切分，不支持浮点、字符串、日期等其他类型。如果用户指定其他非支持类型，MysqlReader将报错。如果splitPk不填写，包括不提供splitPk或者splitPk值为空，DataX视作使用单通道同步该表数据。
- where：可选字段，过滤条件。MysqlReader 根据指定的 column、table、where 条件拼接 SQL，并根据这个 SQL 进行数据抽取。在实际业务场景中，往往会选择当天的数据进行同步，可以将 where 条件指定为 gmt_create > $bizdate 。注意：不可以将 where 条件指定为 limit 10，limit 不是 SQL 的合法 where 子句。where条件可以有效地进行业务增量同步。如果不填写where语句，包括不提供where的key或者value，DataX均视作同步全量数据。
- querySql：可选字段，自定义查询 SQL。在有些业务场景下，where这一配置项不足以描述所筛选的条件，用户可以通过该配置型来自定义筛选SQL。当用户配置了这一项之后，DataX系统就会忽略table，column这些配置型，直接使用这个配置项的内容对数据进行筛选，例如需要进行多表join后同步数据，使用select a,b from table_a join table_b on table_a.id = table_b.id。当用户配置querySql时，MysqlReader直接忽略table、column、where条件的配置，querySql优先级大于table、column、where选项。

### 1.4 类型转换

目前 MysqlReader 支持大部分 Mysql 类型，但也存在部分个别类型没有支持的情况，请注意检查你的类型。

下面列出MysqlReader针对Mysql类型转换列表:

请注意:

除上述罗列字段类型外，其他类型均不支持。
tinyint(1) DataX视作为整形。
year DataX视作为字符串类型
bit DataX属于未定义行为。


## 2. MySQL Writer

MySQL Writer 插件实现了写入数据到 MySQL 目的表的功能。在底层实现上，MySQL Writer 通过 JDBC 连接远程 MySQL 数据库，并执行相应的 `insert into` 或者 `replace into` SQL 语句将数据写入 MySQL，内部会分批次提交入库，需要数据库本身采用 innodb 引擎。

### 2.1 实现原理

MySQL Writer 通过 DataX 框架获取 Reader 生成的协议数据，根据你配置的写入模式 writeMode 生成，目前可支持 insert、update 以及 replace 三种方式：

### 2.2 配置样例

> 这里使用一份从内存产生到 Mysql 导入的数据。
```json
{
    "job": {
        "setting": {
            "speed": {
                "channel": 1
            }
        },
        "content": [
            {
                 "reader": {
                    "name": "streamreader",
                    "parameter": {
                        "column" : [
                            {
                                "value": "DataX",
                                "type": "string"
                            },
                            {
                                "value": 19880808,
                                "type": "long"
                            },
                            {
                                "value": "1988-08-08 08:08:08",
                                "type": "date"
                            },
                            {
                                "value": true,
                                "type": "bool"
                            },
                            {
                                "value": "test",
                                "type": "bytes"
                            }
                        ],
                        "sliceRecordCount": 1000
                    }
                },
                "writer": {
                    "name": "mysqlwriter",
                    "parameter": {
                        "writeMode": "insert",
                        "username": "root",
                        "password": "root",
                        "column": [
                            "id",
                            "name"
                        ],
                        "session": [
                        	"set session sql_mode='ANSI'"
                        ],
                        "preSql": [
                            "delete from test"
                        ],
                        "connection": [
                            {
                                "jdbcUrl": "jdbc:mysql://127.0.0.1:3306/datax?useUnicode=true&characterEncoding=gbk",
                                "table": [
                                    "test"
                                ]
                            }
                        ]
                    }
                }
            }
        ]
    }
}
```

### 2.3 参数说明

- jdbcUrl：目的数据库的 JDBC 连接信息。作业运行时，DataX 会在你提供的 jdbcUrl 后面追加如下属性：yearIsDateType=false&zeroDateTimeBehavior=convertToNull&rewriteBatchedStatements=true。在一个数据库上只能配置一个 jdbcUrl 值。这与 MysqlReader 支持多个备库探测不同，因为此处不支持同一个数据库存在多个主库的情况(双主导入数据情况)；jdbcUrl按照 MySQL 官方规范，并可以填写连接附加控制信息，比如想指定连接编码为 gbk ，则在 jdbcUrl 后面追加属性 useUnicode=true&characterEncoding=gbk。
- username：目的数据库的用户名
- password：目的数据库的密码
- table：目的表的表名称。支持写入一个或者多个表。当配置为多张表时，必须确保所有表 Schema 保持一致。table 和 jdbcUrl 必须包含在 connection 配置单元中。
- column：目的表需要写入数据的字段。字段之间用英文逗号分隔，例如: `"column": ["id","name","age"]`。如果要依次写入全部列，使用 `*` 表示, 例如: `"column": ["*"]`。
- session：DataX 在获取 MySQL 连接时，执行 session 指定的 SQL 语句，修改当前 connection session 属性。
- preSql：写入数据到目的表前，会先执行这里的标准语句。如果 Sql 中有你需要操作到的表名称，请使用 `@table` 表示，这样在实际执行 Sql 语句时，会对变量按照实际表名称进行替换。比如你的任务是要写入到目的端的100个同构分表(表名称为:datax_00,datax01, ... datax_98,datax_99)，并且你希望导入数据前，先对表中数据进行删除操作，那么你可以这样配置："preSql":["delete from 表名"]，效果是：在执行到每个表写入数据前，会先执行对应的 delete from 对应表名称。
- postSql：写入数据到目的表后，会执行这里的标准语句。（原理同 preSql ）
- writeMode：控制写入数据到目标表采用 insert into 或者 replace into 或者 ON DUPLICATE KEY UPDATE 语句
  - insert
  - replace
  - update
- batchSize：一次性批量提交的记录数大小，该值可以极大减少DataX与Mysql的网络交互次数，并提升整体吞吐量。但是该值设置过大可能会造成DataX运行进程OOM情况。

### 2.4 类型转换

类似 MysqlReader ，目前 MysqlWriter 支持大部分 Mysql 类型，但也存在部分个别类型没有支持的情况，请注意检查你的类型。

下面列出 MysqlWriter 针对 Mysql 类型转换列表:














...
