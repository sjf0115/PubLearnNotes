
## 1. 数据准备

假设我们有一个表 user_behavior 包含了 uid (用户ID)、pid (商品ID)、cid (商品类目ID)、behavior (行为类型)和 ts(时间戳) 5个字段：

| 字段 | 中文名称 | 说明 |
| :------------- | :------------- | :------------- |
| uid | 用户ID	| 整数类型 |
| pid | 商品ID	| 整数类型 |
| cid | 商品类目ID	| 整数类型|
| behavior | 行为类型	| 字符串，枚举类型，包括('pv', 'buy', 'cart', 'fav') |
| ts | 时间戳	| 行为发生的时间戳 |

现在需要计算每种行为的日志量：
```sql
SELECT behavior, COUNT(*) AS num
FROM user_behavior
GROUP BY behavior;
```

## 2. 计算过程

```sql
hive> SELECT behavior, COUNT(*) AS num
    > FROM user_behavior
    > GROUP BY behavior;
Query ID = smartsi_20250810230649_98a7c01e-299e-47b8-85de-643d2781eee6
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks not specified. Estimated from input data size: 15
In order to change the average load for a reducer (in bytes):
  set hive.exec.reducers.bytes.per.reducer=<number>
In order to limit the maximum number of reducers:
  set hive.exec.reducers.max=<number>
In order to set a constant number of reducers:
  set mapreduce.job.reduces=<number>
Starting Job = job_1754826210574_0002, Tracking URL = http://192.168.5.132:8088/proxy/application_1754826210574_0002/
Kill Command = /opt/workspace/hadoop/bin/mapred job  -kill job_1754826210574_0002
Hadoop job information for Stage-1: number of mappers: 14; number of reducers: 15
2025-08-10 23:06:57,605 Stage-1 map = 0%,  reduce = 0%
2025-08-10 23:07:07,746 Stage-1 map = 7%,  reduce = 0%
2025-08-10 23:07:08,865 Stage-1 map = 43%,  reduce = 0%
2025-08-10 23:07:14,470 Stage-1 map = 50%,  reduce = 0%
2025-08-10 23:07:15,577 Stage-1 map = 64%,  reduce = 0%
2025-08-10 23:07:16,673 Stage-1 map = 86%,  reduce = 0%
2025-08-10 23:07:21,019 Stage-1 map = 93%,  reduce = 0%
2025-08-10 23:07:22,092 Stage-1 map = 100%,  reduce = 0%
2025-08-10 23:07:24,297 Stage-1 map = 100%,  reduce = 33%
2025-08-10 23:07:26,495 Stage-1 map = 100%,  reduce = 40%
2025-08-10 23:07:28,631 Stage-1 map = 100%,  reduce = 73%
2025-08-10 23:07:30,746 Stage-1 map = 100%,  reduce = 80%
2025-08-10 23:07:31,782 Stage-1 map = 100%,  reduce = 100%
Ended Job = job_1754826210574_0002
MapReduce Jobs Launched:
Stage-Stage-1: Map: 14  Reduce: 15   HDFS Read: 3672652512 HDFS Write: 1402 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
fav	2888258
pv	89716264
buy	2015839
cart	5530446
Time taken: 44.382 seconds, Fetched: 4 row(s)
```


执行流程详解
Map阶段:

读取user_behavior表数据

提取behavior列

在Map端进行部分聚合(combiner)，计算每个Map任务处理的data中各个behavior的出现次数

按照behavior的值对输出进行分区，确保相同behavior的记录会发送到同一个Reducer

Shuffle阶段:

将Map端的输出按照behavior的值进行排序和分区

将数据发送到对应的Reducer

Reduce阶段:

接收来自不同Map任务的相同behavior的数据

合并部分聚合结果，计算最终的count值

将结果写入SequenceFile

Fetch阶段:

从Reduce阶段输出的文件中读取结果

返回给客户端

## 3. 执行计划

```sql
EXPLAIN
SELECT behavior, COUNT(*) AS num
FROM user_behavior
GROUP BY behavior;
```

在默认参数配置下输出如下执行计划信息：
```sql
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: user_behavior
            Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              expressions: behavior (type: string)
              outputColumnNames: behavior
              Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
              Group By Operator
                aggregations: count()
                keys: behavior (type: string)
                mode: hash
                outputColumnNames: _col0, _col1
                Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator
                  key expressions: _col0 (type: string)
                  sort order: +
                  Map-reduce partition columns: _col0 (type: string)
                  Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
                  value expressions: _col1 (type: bigint)
      Execution mode: vectorized
      Reduce Operator Tree:
        Group By Operator
          aggregations: count(VALUE._col0)
          keys: KEY._col0 (type: string)
          mode: mergepartial
          outputColumnNames: _col0, _col1
          Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
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

Hive执行计划输出主要分为三大部分：
- `STAGE DEPENDENCIES`：`Stage` 依赖关系
- `STAGE PLANS`：详细的 `Stage` 执行计划
- 执行统计信息（如果有实际执行）

### 3.1 Stage 依赖关系

```sql
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1
```
从上面信息可以知道：
- 该查询涉及两个执行阶段：`Stage-1` 和 `Stage-0`
- `Stage-1` 是根阶段（root stage），即最先执行的阶段
- `Stage-0` 依赖于 `Stage-1`，表示 `Stage-0` 需要在 `Stage-1` 完成后才能执行

### 3.2 Stage 执行计划

在这 `Stage-1` 是 MapReduce 作业执行阶段（包含Map和Reduce），`Stage-0` 是 Fetch 阶段，负责将结果返回给客户端。由于 `Stage-0` 比较简单，在这着重解读一下 `Stage-1` MapReduce 作业执行阶段。这也是整个执行计划最复杂的部分，完整展示了 Hive 如何将 GROUP BY 转换为 MapReduce 作业。

> Execution mode: vectorized
这表示Hive启用了向量化执行模式，这是Hive 0.13引入的优化特性，可以一次处理一批记录而非单条记录，显著提高CPU利用率。

#### 3.2.1 Map 阶段：Map Operator Tree

Map Operator Tree 描述了在 Map 阶段执行的操作序列：

```sql
Map Operator Tree:
    TableScan
      alias: user_behavior
      Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
      Select Operator
        expressions: behavior (type: string)
        outputColumnNames: behavior
        Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
        Group By Operator
          aggregations: count()
          keys: behavior (type: string)
          mode: hash
          outputColumnNames: _col0, _col1
          Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
          Reduce Output Operator
            key expressions: _col0 (type: string)
            sort order: +
            Map-reduce partition columns: _col0 (type: string)
            Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
            value expressions: _col1 (type: bigint)
```
第一个是 TableScan Operator，用于扫描 user_behavior 表数据，关键属性：
- alias: user_behavior：表别名
- Statistics：统计信息（注意这里的 Num rows 为 1 是估计值，实际数据量 36.7GB）

第二个是 Select Operator，用于选择需要的列（投影操作），关键属性：
- expressions: behavior，在上述查询中只选择 behavior 列
- outputColumnNames: 输出列名为 behavior
- Statistics：统计信息（注意这里的 Num rows 为 1 是估计值，实际数据量 36.7GB）

第三个是 Group By Operator，用于在 Map 端执行部分聚合（Map 端 Combiner），关键属性：
- aggregations: `count()` 表示执行 COUNT 聚合
- keys: 表示按照 behavior 分组
- mode: `hash` 表示使用哈希表实现聚合
- outputColumnNames: Map 段输出临时列名 `_col0` 和 `_col1`（behavior对应 `_col0`，count 对应`_col1`）
- Statistics：统计信息（注意这里的 Num rows 为 1 是估计值，实际数据量 36.7GB）

> 为了减少 Reducer 端处理的数据量，`hive.map.aggr`默认设置为`true`，所以先会在 Mapper 端进行一次 Group By，结果根据 key 聚合。Reducer 端 `Group By Operator` 的 mode 为 `mergepartial`。如果设置 `hive.map.aggr=false`，Reducer 端 `Group By Operator` 的 mode 为 `complete`。

```
set hive.map.aggr=true;
```


第四个是 Reduce Output Operator，用于准备发送到 Reduce 端的数据，关键属性：
- key expressions: `_col0` 表示以 `_col0`（即behavior）作为 Reduce 的 key 进行 Shuffle
- sort order: `+` 表示按 key 升序排序
- value expressions: `_col1` 表示发送 `_col1`（即count值）到 Reduce


#### 3.2.2 Reduce 阶段：Reduce Operator Tree

Reduce端操作树描述了Reduce阶段执行的操作：

```sql
Reduce Operator Tree:
  Group By Operator
    aggregations: count(VALUE._col0)
    keys: KEY._col0 (type: string)
    mode: mergepartial
    outputColumnNames: _col0, _col1
    Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
    File Output Operator
      compressed: false
      Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
      table:
          input format: org.apache.hadoop.mapred.SequenceFileInputFormat
          output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
          serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
```

第一个是 Group By Operator，用于合并 Map 端的部分聚合结果，关键属性：
- mode: `mergepartial` 表示合并部分聚合结果
- aggregations: `count(VALUE._col0)` 表示合并 Map 端传递过来的 count 值
- keys: `KEY._col0` 表示仍按 behavior 分组
- outputColumnNames: Reduce 端输出临时列名 `_col0` 和 `_col1`（behavior对应 `_col0`，num 对应`_col1`）

第二个是 File Output Operator，用于将最终结果写入文件系统，关键配置：
- compressed: `false` 表示输出未压缩
- input format: `org.apache.hadoop.mapred.SequenceFileInputFormat` 表示输入格式为 SequenceFileInputFormat
- output format: `org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat` 表示输出格式为 HiveSequenceFileOutputFormat
- serde: `org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe` 表示使用 `LazySimpleSerDe` 序列化

...
