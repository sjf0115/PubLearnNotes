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

## 1. EXPLAIN

在查询语句的 SQL 前面加上关键字 EXPLAIN 就可以查看执行计划。例如，有如下 EXPLAIN 查询：
```sql
EXPLAIN
SELECT COUNT(*) FROM tb_order;
```

返回的执行计划如下所示：
```
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: tb_order
            Statistics: Num rows: 13066777 Data size: 11760099340 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              Statistics: Num rows: 13066777 Data size: 11760099340 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count()
                mode: hash
                outputColumnNames: _col0
                Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  sort order:
                  Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
                  value expressions: _col0 (type: bigint)
      Execution mode: vectorized
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0)
          mode: mergepartial
          outputColumnNames: _col0
          Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        ListSink
```
用 EXPLAIN 打开的执行计划包含以下两部分：
- 作业的依赖关系图，即 STAGE DEPENDENCIES。
- 每个作业的详细信息，即 STAGE PLANS。

从上面信息可以知道：
- 该查询涉及两个执行阶段：`Stage-1` 和 `Stage-0`
- `Stage-1` 是根阶段（root stage），即最先执行的阶段
- `Stage-0` 依赖于 `Stage-1`，表示 `Stage-0` 需要在 `Stage-1` 完成后才能执行

在这 `Stage-1` 是 MapReduce 作业执行阶段（包含 Map 和 Reduce），`Stage-0` 是 Fetch 阶段，负责将结果返回给客户端。

## 2. EXPLAIN EXTENDED

在 EXPLAIN 语句中添加 EXTENDED 关键词可以查看执行计划的扩展信息。EXPLAIN EXTENDED，顾名思义就是对 EXPLAIN 的扩展，打印的信息会比 EXPLAIN 更加丰富，包含如下三部分的内容：
- 抽象语法树（Abstract Syntax Tree，AST）：是 SQL 转换成 MapReduce 或其他计算引擎任务中的一个过程。在 Hive 3.0 版本中，AST 会从 EXPLAIN EXTENDED 中移除，要查看 AST，需要使用 EXPLAIN AST 命令。
- 作业的依赖关系图，即 STAGE DEPENDENCIES，其内容和 EXPLAIN 所展现的一样，在这不做重复介绍。
- 每个作业的详细信息，即 STAGE PLANS。在打印每个作业的详细信息时，EXPLAIN EXTENDED 会打印出更多的信息，除了 EXPLAIN 打印出的内容，还包括每个表的 HDFS 读取路径，每个 Hive 表的表配置信息等。

例如，有如下 EXPLAIN EXTENDED 查询：
```sql
EXPLAIN EXTENDED
SELECT COUNT(*) FROM tb_order;
```

返回的执行计划如下所示：
```
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: tb_order
            Statistics: Num rows: 13066777 Data size: 11760099340 Basic stats: COMPLETE Column stats: NONE
            GatherStats: false
            Select Operator
              Statistics: Num rows: 13066777 Data size: 11760099340 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count()
                mode: hash
                outputColumnNames: _col0
                Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  null sort order:
                  sort order:
                  Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
                  tag: -1
                  value expressions: _col0 (type: bigint)
                  auto parallelism: false
      Execution mode: vectorized
      Path -> Alias:
        hdfs://localhost:9000/user/hive/warehouse/tb_order/dt=2020-06-14 [tb_order]
      Path -> Partition:
        hdfs://localhost:9000/user/hive/warehouse/tb_order/dt=2020-06-14
          Partition
            base file name: dt=2020-06-14
            input format: org.apache.hadoop.mapred.TextInputFormat
            output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
            partition values:
              dt 2020-06-14
            properties:
              bucket_count -1
              column.name.delimiter ,
              columns id,user_id,product_id,province_id,create_time,product_num,total_amount
              columns.comments '??id','??id','??id','??id','????','????','????'
              columns.types string:string:string:string:string:int:decimal(16,2)
              field.delim ,
              file.inputformat org.apache.hadoop.mapred.TextInputFormat
              file.outputformat org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
              line.delim

              location hdfs://localhost:9000/user/hive/warehouse/tb_order/dt=2020-06-14
              name default.tb_order
              numFiles 1
              numRows 0
              partition_columns dt
              partition_columns.types string
              rawDataSize 0
              serialization.ddl struct tb_order { string id, string user_id, string product_id, string province_id, string create_time, i32 product_num, decimal(16,2) total_amount}
              serialization.format ,
              serialization.lib org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
              totalSize 1176009934
              transient_lastDdlTime 1759359690
            serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

              input format: org.apache.hadoop.mapred.TextInputFormat
              output format: org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
              properties:
                bucket_count -1
                bucketing_version 2
                column.name.delimiter ,
                columns id,user_id,product_id,province_id,create_time,product_num,total_amount
                columns.comments '??id','??id','??id','??id','????','????','????'
                columns.types string:string:string:string:string:int:decimal(16,2)
                field.delim ,
                file.inputformat org.apache.hadoop.mapred.TextInputFormat
                file.outputformat org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat
                line.delim

                location hdfs://localhost:9000/user/hive/warehouse/tb_order
                name default.tb_order
                partition_columns dt
                partition_columns.types string
                serialization.ddl struct tb_order { string id, string user_id, string product_id, string province_id, string create_time, i32 product_num, decimal(16,2) total_amount}
                serialization.format ,
                serialization.lib org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
                transient_lastDdlTime 1759359663
              serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
              name: default.tb_order
            name: default.tb_order
      Truncated Path -> Alias:
        /tb_order/dt=2020-06-14 [tb_order]
      Needs Tagging: false
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0)
          mode: mergepartial
          outputColumnNames: _col0
          Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            GlobalTableId: 0
            directory: hdfs://localhost:9000/tmp/hive/smartsi/cb81f1ed-947f-4cf2-9e0c-d77a861ca2f5/hive_2025-10-02_09-32-44_348_8718163619082941927-1/-mr-10001/.hive-staging_hive_2025-10-02_09-32-44_348_8718163619082941927-1/-ext-10002
            NumFilesPerFileSink: 1
            Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
            Stats Publishing Key Prefix: hdfs://localhost:9000/tmp/hive/smartsi/cb81f1ed-947f-4cf2-9e0c-d77a861ca2f5/hive_2025-10-02_09-32-44_348_8718163619082941927-1/-mr-10001/.hive-staging_hive_2025-10-02_09-32-44_348_8718163619082941927-1/-ext-10002/
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                properties:
                  columns _col0
                  columns.types bigint
                  escape.delim \
                  hive.serialization.extend.additional.nesting.levels true
                  serialization.escape.crlf true
                  serialization.format 1
                  serialization.lib org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
                serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
            TotalFiles: 1
            GatherStats: false
            MultiFileSpray: false

  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        ListSink
```
> Hive 3.1.3 版本

对比 EXPLAIN 语句返回的执行计划，可以看出每个 Stage 的详细信息中还包括每个表的 HDFS 读取路径，每个 Hive 表的表配置信息等。

## 3. EXPLAIN CBO

在 EXPLAIN 语句中使用 CBO 可以查看 Calcite 优化器生成的查询计划信息。可以选择包含有关使用 Calcite 默认成本模型和用于连接重新排序的成本模型的查询计划成本的信息。从 Hive 4.0.0 版本开始提供支持，具体查阅 [HIVE-17503](https://issues.apache.org/jira/browse/HIVE-17503) 和 [HIVE-21184](https://issues.apache.org/jira/browse/HIVE-21184)。

```sql
EXPLAIN CBO
SELECT COUNT(*) FROM tb_order;
```

## 4. EXPLAIN AST

在 EXPLAIN 语句中使用 AST 可以查看 SQL 查询的抽象语法树。AST 在 Hive 2.1.0 版本中从 EXPLAIN EXTENDED 中删除，主要是因为对于非常大的查询，转储 AST 会导致 OOM 错误，具体查阅[HIVE-13533](https://issues.apache.org/jira/browse/HIVE-13533)。在 HIVE 4.0.0 版本开始提供 AST 的单独命令，对于 Hive 开发人员和高级用户来说，查看 AST 来诊断问题会很有用，具体查阅 [HIVE-15932](https://issues.apache.org/jira/browse/HIVE-15932)。

```sql
EXPLAIN AST
SELECT COUNT(*) FROM tb_order;
```

## 5. EXPLAIN DEPENDENCY

在 EXPLAIN 语句中使用 DEPENDENCY 可以查看 SQL 数据输入依赖的信息。输出是一个 Json 格式的数据，里面包含以下两个部分的内容：
- input_tables：SQL 数据输入依赖的表。tablename 格式为 '库名@表名'，tabletype 可以是 MANAGED_TABLE（内部表） 或者 EXTERNAL_TABLE（外部表）。
- input_partitions：SQL 数据输入依赖的表分区。partitionName 格式为：'库名@表名@分区列=分区列的值'。如果依赖的所有表都是非分区表，则显示为空。

例如，有如下 EXPLAIN DEPENDENCY 查看 SQL 查询分区表：
```sql
EXPLAIN DEPENDENCY
SELECT COUNT(*) FROM tb_order;
```
输出结果如下：
```json
{
  "input_tables": [
    {
      "tablename": "default@tb_order",
      "tabletype": "MANAGED_TABLE"
    }
  ],
  "input_partitions": [
    {
      "partitionName": "default@tb_order@dt=2020-06-14"
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

## 6. EXPLAIN AUTHORIZATION

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

## 7. EXPLAIN LOCKS

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

## 8. EXPLAIN VECTORIZATION

VECTORIZATION 从 Hive 2.3.0 版本开始提供支持，用来显示 Map 和 Reduce 作业没有向量化的原因，具体查阅[HIVE-11394](https://issues.apache.org/jira/browse/HIVE-11394)。

```sql
EXPLAIN VECTORIZATION
SELECT COUNT(*) FROM tb_order;
```
返回的执行计划如下所示：
```
PLAN VECTORIZATION:
  enabled: true
  enabledConditionsMet: [hive.vectorized.execution.enabled IS true]

STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: tb_order
            Statistics: Num rows: 13066777 Data size: 11760099340 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              Statistics: Num rows: 13066777 Data size: 11760099340 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count()
                mode: hash
                outputColumnNames: _col0
                Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  sort order:
                  Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
                  value expressions: _col0 (type: bigint)
      Execution mode: vectorized
      Map Vectorization:
          enabled: true
          enabledConditionsMet: hive.vectorized.use.vector.serde.deserialize IS true
          inputFormatFeatureSupport: [DECIMAL_64]
          featureSupportInUse: [DECIMAL_64]
          inputFileFormats: org.apache.hadoop.mapred.TextInputFormat
          allNative: false
          usesVectorUDFAdaptor: false
          vectorized: true
      Reduce Vectorization:
          enabled: false
          enableConditionsMet: hive.vectorized.execution.reduce.enabled IS true
          enableConditionsNotMet: hive.execution.engine mr IN [tez, spark] IS false
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0)
          mode: mergepartial
          outputColumnNames: _col0
          Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        ListSink
```

在这个查询计划的如下几个部分中解释了向量化（vectorization）：
- PLAN VECTORIZATION 部分显示查询的向量化状态的高级视图。enabled 标志为 true 表示启用了向量化，而 enabledConditionsMet 标志表示启用向量化的原因是 `hive.vectorized.execution.enabled` 属性设置为 true。
- STAGE PLANS 部分中输出显示了每个查询执行任务的向量化状态。例如，一个查询可能有多个map和reduce任务，而且可能只有这些任务的一个子集是向量化的。在上面的示例中，Stage-1 子部分显示只有一个 Map 任务和一个 Reduce 任务。Map 任务的 Execution Mode 子部分显示任务是否向量化。在本例中，显示 vectorized，这意味着向量化器能够成功地验证和向量化此 Map 任务的所有操作符。

- Map Vectorization 子节显示map任务向量化的更多细节。具体来说，将显示影响map端向量化的配置，以及是否启用这些配置。如果配置是启用的，它们会在enabledConditionsMet中列出。如果配置没有启用,它们将在enabledConditionsNotMet中列出。在这个例子中，它显示查询执行的map端是启用的，因为hive.vectorized.use.vectorized.input.format属性被设置为true。这一子节还包含关于在查询执行的map端中使用的输入文件格式和适配器设置的详细信息。

- Reduce Vectorization子节显示查询执行的reduce端没有向量化，因为hive.vectorized.execute.reduce.enabled属性被设置为false。本小节还显示了执行引擎没有设置为Tez或Spark，这是reduce端向量化所需的。在这个特定的示例中，要启用reduce端向量化，应该将执行引擎设置为Spark，并将hive.vectorized.execution.reduce.enabled属性设置为true。

```
PLAN VECTORIZATION:
  enabled: false
  enabledConditionsNotMet: [hive.vectorized.execution.enabled IS false]

STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: tb_order
            Statistics: Num rows: 13066777 Data size: 11760099340 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              Statistics: Num rows: 13066777 Data size: 11760099340 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count()
                mode: hash
                outputColumnNames: _col0
                Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  sort order:
                  Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
                  value expressions: _col0 (type: bigint)
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0)
          mode: mergepartial
          outputColumnNames: _col0
          Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        ListSink
```


- [LanguageManual Explain](https://cwiki.apache.org/confluence/display/Hive/LanguageManual+Explain)
