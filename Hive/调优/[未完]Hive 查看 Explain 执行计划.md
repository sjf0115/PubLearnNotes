---
layout: post
author: sjf0115
title: Hive 执行计划
date: 2018-07-21 17:16:01
tags:
  - Hive

categories: Hive
permalink: hive-optimization-how-to-use-explain
---

Hive 提供了一个 EXPLAIN 语句，不运行查询就可以返回查询的执行计划。如果我们担心查询的性能，我们可以使用它来分析查询。EXPLAIN 语句可帮助我们查看实现相同任务的不同查询语句的差异。 EXPLAIN 语法如下：
```
EXPLAIN [EXTENDED|CBO|AST|DEPENDENCY|AUTHORIZATION|LOCKS|VECTORIZATION] query
```
从上面可以知道 Hive 提供的执行计划可以查看的信息有如下几种：
- 查看 SQL 执行计划的基本信息，使用 EXPLAIN 命令；
- 查看 SQL 执行计划的扩展信息，使用 EXPLAIN EXTENDED 命令；
- 查看 Calcite 优化器生成的查询计划信息，使用 EXPLAIN CBO 命令；
- 查看 SQL 查询的抽象语法树，使用 EXPLAIN AST 命令。
- 查看 SQL 数据输入依赖的信息，使用 EXPLAIN DEPENDENCY 命令。
- 查看 SQL 操作相关权限的信息，使用 EXPLAIN AUTHORIZATION 命令。
- 查看 SQL 获取哪些锁来运行查询，使用 EXPLAIN LOCKS 命令。
- 查看 SQL 的向量化描述信息，使用 EXPLAIN VECTORIZATION 命令。

### 1. EXPLAIN

在查询语句的 SQL 前面加上关键字 EXPLAIN 就可以查看执行计划。例如，有如下 EXPLAIN 查询：
```sql
EXPLAIN
INSERT OVERWRITE TABLE dws_app_pub_user_overview_1d
SELECT uid, COUNT(wid) AS num
FROM dws_app_pub_user_behavior_1d
GROUP BY uid;
```
用 EXPLAIN 打开的执行计划包含以下两部分：
- 作业的依赖关系图，即 STAGE DEPENDENCIES。
- 每个作业的详细信息，即 STAGE PLANS。

```
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1
  Stage-2 depends on stages: Stage-0

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: dws_app_user_behavior_1d
            Statistics: Num rows: 224481 Data size: 44896344 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              expressions: uid (type: string), wid (type: string)
              outputColumnNames: uid, wid
              Statistics: Num rows: 224481 Data size: 44896344 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count(wid)
                keys: uid (type: string)
                mode: hash
                outputColumnNames: _col0, _col1
                Statistics: Num rows: 224481 Data size: 44896344 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  key expressions: _col0 (type: string)
                  sort order: +
                  Map-reduce partition columns: _col0 (type: string)
                  Statistics: Num rows: 224481 Data size: 44896344 Basic stats: COMPLETE Column stats: NONE
                  value expressions: _col1 (type: bigint)
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0)
          keys: KEY._col0 (type: string)
          mode: mergepartial
          outputColumnNames: _col0, _col1
          Statistics: Num rows: 112240 Data size: 22448071 Basic stats: COMPLETE Column stats: NONE
          Select Operator
            expressions: _col0 (type: string), UDFToInteger(_col1) (type: int)
            outputColumnNames: _col0, _col1
            Statistics: Num rows: 112240 Data size: 22448071 Basic stats: COMPLETE Column stats: NONE
            File Output Operator
              compressed: false
              Statistics: Num rows: 112240 Data size: 22448071 Basic stats: COMPLETE Column stats: NONE
              table:
                  input format: org.apache.hadoop.mapred.TextInputFormat
                  output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
                  serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
                  name: default.dws_app_pub_user_overview_1d

  Stage: Stage-0
    Move Operator
      tables:
          replace: true
          table:
              input format: org.apache.hadoop.mapred.TextInputFormat
              output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
              serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
              name: default.dws_app_pub_user_overview_1d

  Stage: Stage-2
    Stats-Aggr Operator
```

### 2. EXPLAIN EXTENDED

在 EXPLAIN 语句中使用 EXTENDED 可以查看执行计划的扩展信息。EXPLAIN EXTENDED，顾名思义就是对 EXPLAIN 的扩展，打印的信息会比 EXPLAIN 更加丰富，包含以下三部分的内容：
- 抽象语法树（Abstract Syntax Tree，AST）：是 SQL 转换成 MapReduce 或其他计算引擎任务中的一个过程。在 Hive 3.0 版本中，AST 会从 EXPLAIN EXTENDED 中移除，要查看 AST，需要使用 EXPLAIN AST 命令。
- 作业的依赖关系图，即 STAGE DEPENDENCIES，其内容和 EXPLAIN 所展现的一样，在这不做重复介绍。
- 每个作业的详细信息，即 STAGE PLANS。在打印每个作业的详细信息时，EXPLAIN EXTENDED 会打印出更多的信息，除了 EXPLAIN 打印出的内容，还包括每个表的 HDFS 读取路径，每个 Hive 表的表配置信息等。

例如，有如下 EXPLAIN EXTENDED 查询：
```sql
EXPLAIN EXTENDED
INSERT OVERWRITE TABLE dws_app_pub_user_overview_1d
SELECT uid, COUNT(wid) AS num
FROM dws_app_pub_user_behavior_1d
WHERE dt = '20150831'
GROUP BY uid;
```

```
STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: dws_app_pub_user_behavior_1d
            Statistics: Num rows: 5724 Data size: 1450359 Basic stats: COMPLETE Column stats: NONE
            GatherStats: false
            Select Operator
              expressions: uid (type: string), wid (type: string)
              outputColumnNames: uid, wid
              Statistics: Num rows: 5724 Data size: 1450359 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count(wid)
                keys: uid (type: string)
                mode: hash
                outputColumnNames: _col0, _col1
                Statistics: Num rows: 5724 Data size: 1450359 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  key expressions: _col0 (type: string)
                  null sort order: a
                  sort order: +
                  Map-reduce partition columns: _col0 (type: string)
                  Statistics: Num rows: 5724 Data size: 1450359 Basic stats: COMPLETE Column stats: NONE
                  tag: -1
                  value expressions: _col1 (type: bigint)
                  auto parallelism: false
      Path -> Alias:
        hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_behavior_1d/dt=20150831 [dws_app_pub_user_behavior_1d]
      Path -> Partition:
        hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_behavior_1d/dt=20150831
          Partition
            base file name: dt=20150831
            input format: org.apache.hadoop.mapred.TextInputFormat
            output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
            partition values:
              dt 20150831
            properties:
              COLUMN_STATS_ACCURATE {"BASIC_STATS":"true"}
              bucket_count -1
              column.name.delimiter ,
              columns uid,wid,time,content
              columns.comments '用户uid','微博Id','创建微博时间','微博内容'
              columns.types string:string:string:string
              field.delim
              file.inputformat org.apache.hadoop.mapred.TextInputFormat
              file.outputformat org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
              line.delim

              location hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_behavior_1d/dt=20150831
              name default.dws_app_pub_user_behavior_1d
              numFiles 1
              numRows 5724
              partition_columns dt
              partition_columns.types string
              rawDataSize 1450359
              serialization.ddl struct dws_app_pub_user_behavior_1d { string uid, string wid, string time, string content}
              serialization.format
              serialization.lib org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
              totalSize 1456083
              transient_lastDdlTime 1634466629
            serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

              input format: org.apache.hadoop.mapred.TextInputFormat
              output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
              properties:
                bucket_count -1
                column.name.delimiter ,
                columns uid,wid,time,content
                columns.comments '用户uid','微博Id','创建微博时间','微博内容'
                columns.types string:string:string:string
                field.delim
                file.inputformat org.apache.hadoop.mapred.TextInputFormat
                file.outputformat org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
                line.delim

                location hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_behavior_1d
                name default.dws_app_pub_user_behavior_1d
                partition_columns dt
                partition_columns.types string
                serialization.ddl struct dws_app_pub_user_behavior_1d { string uid, string wid, string time, string content}
                serialization.format
                serialization.lib org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
                transient_lastDdlTime 1634259002
              serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
              name: default.dws_app_pub_user_behavior_1d
            name: default.dws_app_pub_user_behavior_1d
      Truncated Path -> Alias:
        /dws_app_pub_user_behavior_1d/dt=20150831 [dws_app_pub_user_behavior_1d]
      Needs Tagging: false
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0)
          keys: KEY._col0 (type: string)
          mode: mergepartial
          outputColumnNames: _col0, _col1
          Statistics: Num rows: 2862 Data size: 725179 Basic stats: COMPLETE Column stats: NONE
          Select Operator
            expressions: _col0 (type: string), UDFToInteger(_col1) (type: int)
            outputColumnNames: _col0, _col1
            Statistics: Num rows: 2862 Data size: 725179 Basic stats: COMPLETE Column stats: NONE
            File Output Operator
              compressed: false
              GlobalTableId: 1
              directory: hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_overview_1d/.hive-staging_hive_2021-10-17_22-06-50_442_3292392681241833748-1/-ext-10000
              NumFilesPerFileSink: 1
              Statistics: Num rows: 2862 Data size: 725179 Basic stats: COMPLETE Column stats: NONE
              Stats Publishing Key Prefix: hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_overview_1d/.hive-staging_hive_2021-10-17_22-06-50_442_3292392681241833748-1/-ext-10000/
              table:
                  input format: org.apache.hadoop.mapred.TextInputFormat
                  output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
                  properties:
                    COLUMN_STATS_ACCURATE {"BASIC_STATS":"true"}
                    bucket_count -1
                    column.name.delimiter ,
                    columns uid,num
                    columns.comments '用户uid','发微博次数'
                    columns.types string:int
                    field.delim
                    file.inputformat org.apache.hadoop.mapred.TextInputFormat
                    file.outputformat org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
                    line.delim

                    location hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_overview_1d
                    name default.dws_app_pub_user_overview_1d
                    numFiles 0
                    numRows 0
                    rawDataSize 0
                    serialization.ddl struct dws_app_pub_user_overview_1d { string uid, i32 num}
                    serialization.format
                    serialization.lib org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
                    totalSize 0
                    transient_lastDdlTime 1634378599
                  serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
                  name: default.dws_app_pub_user_overview_1d
              TotalFiles: 1
              GatherStats: true
              MultiFileSpray: false

  Stage: Stage-0
    Move Operator
      tables:
          replace: true
          source: hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_overview_1d/.hive-staging_hive_2021-10-17_22-06-50_442_3292392681241833748-1/-ext-10000
          table:
              input format: org.apache.hadoop.mapred.TextInputFormat
              output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
              properties:
                COLUMN_STATS_ACCURATE {"BASIC_STATS":"true"}
                bucket_count -1
                column.name.delimiter ,
                columns uid,num
                columns.comments '用户uid','发微博次数'
                columns.types string:int
                field.delim
                file.inputformat org.apache.hadoop.mapred.TextInputFormat
                file.outputformat org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
                line.delim

                location hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_overview_1d
                name default.dws_app_pub_user_overview_1d
                numFiles 0
                numRows 0
                rawDataSize 0
                serialization.ddl struct dws_app_pub_user_overview_1d { string uid, i32 num}
                serialization.format
                serialization.lib org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
                totalSize 0
                transient_lastDdlTime 1634378599
              serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
              name: default.dws_app_pub_user_overview_1d

  Stage: Stage-2
    Stats-Aggr Operator
      Stats Aggregation Key Prefix: hdfs://localhost:9000/user/hive/warehouse/dws_app_pub_user_overview_1d/.hive-staging_hive_2021-10-17_22-06-50_442_3292392681241833748-1/-ext-10000/
```

### 3. EXPLAIN CBO

在 EXPLAIN 语句中使用 CBO 可以查看 Calcite 优化器生成的查询计划信息。可以选择包含有关使用 Calcite 默认成本模型和用于连接重新排序的成本模型的查询计划成本的信息。从 Hive 4.0.0 版本开始提供支持，具体查阅 [HIVE-17503](https://issues.apache.org/jira/browse/HIVE-17503) 和 [HIVE-21184](https://issues.apache.org/jira/browse/HIVE-21184)。

```sql
EXPLAIN CBO
SELECT uid, COUNT(wid) AS num
FROM dws_app_pub_user_behavior_1d
WHERE dt = '20150831'
GROUP BY uid;
```

### 4. EXPLAIN AST

在 EXPLAIN 语句中使用 AST 可以查看 SQL 查询的抽象语法树。AST 在 Hive 2.1.0 版本中从 EXPLAIN EXTENDED 中删除，主要是因为对于非常大的查询，转储 AST 会导致 OOM 错误，具体查阅[HIVE-13533](https://issues.apache.org/jira/browse/HIVE-13533)。在 HIVE 4.0.0 版本开始提供 AST 的单独命令，对于 Hive 开发人员和高级用户来说，查看 AST 来诊断问题会很有用，具体查阅 [HIVE-15932](https://issues.apache.org/jira/browse/HIVE-15932)。

```sql
EXPLAIN AST
FROM src INSERT OVERWRITE TABLE dest_g1
SELECT src.key, sum(substr(src.value,4))
GROUP BY src.key;
```

### 5. EXPLAIN DEPENDENCY

在 EXPLAIN 语句中使用 DEPENDENCY 可以查看 SQL 数据输入依赖的信息。输出是一个 Json 格式的数据，里面包含以下两个部分的内容：
- input_tables：SQL 数据输入依赖的表。tablename 格式为 '库名@表名'，tabletype 可以是 MANAGED_TABLE（内部表） 或者 EXTERNAL_TABLE（外部表）。
- input_partitions：SQL 数据输入依赖的表分区。partitionName 格式为：'库名@表名@分区列=分区列的值'。如果依赖的所有表都是非分区表，则显示为空。

例如，有如下 EXPLAIN DEPENDENCY 查看 SQL 查询分区表：
```sql
EXPLAIN DEPENDENCY
SELECT uid, COUNT(wid) AS num
FROM dws_app_pub_user_behavior_1d
WHERE dt = '20150831'
GROUP BY uid;
```
输出结果如下：
```json
{
  "input_tables": [
    {
      "tablename": "default@dws_app_pub_user_behavior_1d",
      "tabletype": "MANAGED_TABLE"
    }
  ],
  "input_partitions": [
    {
      "partitionName": "default@dws_app_pub_user_behavior_1d@dt=20150831"
    }
  ]
}
```
查看 SQL 查询非分区表：
```sql
EXPLAIN DEPENDENCY
SELECT uid, num
FROM dws_app_pub_user_overview_1d;
```
输出结果如下，输入分区为空：
```json
{
  "input_tables": [
    {
      "tablename": "default@dws_app_pub_user_overview_1d",
      "tabletype": "MANAGED_TABLE"
    }
  ],
  "input_partitions": [
  ]
}
```
查看 SQL 通过视图访问表：
```sql
CREATE VIEW V1 AS SELECT uid, num
FROM dws_app_pub_user_overview_1d;

EXPLAIN DEPENDENCY SELECT * FROM V1;
```
输出结果如下，依赖项也会显示父表：
```json
{
  "input_tables": [
    {
      "tablename": "default@v1",
      "tabletype": "VIRTUAL_VIEW"
    },
    {
      "tablename": "default@dws_app_pub_user_overview_1d",
      "tabletype": "MANAGED_TABLE",
      "tableParents": "[default@v1]"
    }
  ],
  "input_partitions": [
  ]
}
```

### 6. EXPLAIN AUTHORIZATION

在 EXPLAIN 语句中使用 AUTHORIZATION 可以查看 SQL 操作相关权限的信息：当前 SQL 访问的数据输入(INPUTS)、数据输出(OUTPUTS)、当前 Hive 的访问用户(CURRENT_USER)以及操作类型(OPERATION)。AUTHORIZATION 从 HIVE 0.14.0 版本开始提供支持，具体查阅[HIVE-5961](https://issues.apache.org/jira/browse/HIVE-5961)。

例如，有如下 EXPLAIN AUTHORIZATION 查询，读取一个分区表，然后输出到另一个表中：
```sql
EXPLAIN AUTHORIZATION
INSERT OVERWRITE TABLE dws_app_pub_user_overview_1d
SELECT uid, COUNT(wid) AS num
FROM dws_app_pub_user_behavior_1d
WHERE dt = '20150831'
GROUP BY uid;
```
输出结果如下：
```
INPUTS:
  default@dws_app_pub_user_behavior_1d
  default@dws_app_pub_user_behavior_1d@dt=20150831
OUTPUTS:
  default@dws_app_pub_user_overview_1d
CURRENT_USER:
  wy
OPERATION:
  QUERY
```
从上面的信息可知，数据输入(INPUTS)是 defalut 数据库下 dws_app_pub_user_behavior_1d 表的 dt=20150831 分区，数据输出(OUTPUTS)是 defalut 数据库 dws_app_pub_user_overview_1d 表，当前的操作用户是 wy，操作类型是查询(QUERY)。

如下只是从非分区表中读取数据：
```sql
EXPLAIN AUTHORIZATION
SELECT uid, num
FROM dws_app_pub_user_overview_1d;
```
输出结果如下，数据输出(OUTPUTS)是一个 HDFS 路径：
```
INPUTS:
  default@dws_app_pub_user_overview_1d
OUTPUTS:
  hdfs://localhost:9000/tmp/hive/wy/81eb4d8c-aa55-4db2-9a46-55d2d21a3f53/hive_2021-10-17_22-56-40_118_5202108417763437647-1/-mr-10001
CURRENT_USER:
  wy
OPERATION:
  QUERY
```
如果 EXPLAIN 后添加上 FORMATTED 关键字，输出结果以 JSON 格式返回：
```sql
EXPLAIN FORMATTED AUTHORIZATION
INSERT OVERWRITE TABLE dws_app_pub_user_overview_1d
SELECT uid, COUNT(wid) AS num
FROM dws_app_pub_user_behavior_1d
WHERE dt = '20150831'
GROUP BY uid;
```
输出结果如下：
```json
{
  "INPUTS": [
    "default@dws_app_pub_user_behavior_1d",
    "default@dws_app_pub_user_behavior_1d@dt=20150831"
  ],
  "OUTPUTS": [
    "default@dws_app_pub_user_overview_1d"
  ],
  "CURRENT_USER": "wy",
  "OPERATION": "QUERY"
}
```

### 7. EXPLAIN LOCKS

在 EXPLAIN 语句中使用 LOCKS 可以查看 SQL 获取哪些锁来运行指定的查询。LOCKS 从 Hive 3.2.0 版本开始提供支持，具体查阅 [HIVE-17683](HIVE-17683)。

```sql
EXPLAIN LOCKS
UPDATE target SET b = 1 WHERE p IN (SELECT t.q1 FROM source t WHERE t.a1=5)
```
输出结果如下：
```
LOCK INFORMATION:
default.source -> SHARED_READ
default.target.p=1/q=2 -> SHARED_READ
default.target.p=1/q=3 -> SHARED_READ
default.target.p=2/q=2 -> SHARED_READ
default.target.p=2/q=2 -> SHARED_WRITE
default.target.p=1/q=3 -> SHARED_WRITE
default.target.p=1/q=2 -> SHARED_WRITE
```
> 如果 EXPLAIN 语句后添加上 FORMATTED 关键字，输出结果也会以 JSON 格式返回。

### 8. EXPLAIN VECTORIZATION

VECTORIZATION 从 Hive 2.3.0 版本开始提供支持，具体查阅[HIVE-11394](https://issues.apache.org/jira/browse/HIVE-11394)。


https://mp.weixin.qq.com/s/VOuUpwtOJGZltGqba28y3A


- [LanguageManual Explain](https://cwiki.apache.org/confluence/display/Hive/LanguageManual+Explain)
