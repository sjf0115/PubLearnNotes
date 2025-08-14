本文将通过 JOIN 查询的执行计划来深入剖析 Hive 如何将 SQL 转化为 MapReduce 作业。假设我们有一个表 `user_behavior` 包含了 uid (用户ID)、pid (商品ID)、cid (商品类目ID)、behavior (行为类型)和 ts(时间戳) 5个字段：

| 字段 | 中文名称 | 说明 |
| :------------- | :------------- | :------------- |
| uid | 用户ID	| 整数类型 |
| pid | 商品ID	| 整数类型 |
| cid | 商品类目ID	| 整数类型|
| behavior | 行为类型	| 字符串，枚举类型，包括('pv', 'buy', 'cart', 'fav') |
| ts | 时间戳	| 行为发生的时间戳 |

此外还有一个表 `dim_user_behavior` 包含了 behavior_id(行为类型ID)、behavior_name(行为类型名称) 2个字段：

| 字段 | 中文名称 | 说明 |
| :------------- | :------------- | :------------- |
| behavior_id | 行为类型ID	| 字符串，枚举类型，包括('pv', 'buy', 'cart', 'fav') |
| behavior_name | 行为类型名称	| 字符串 |


我们分析的查询是计算每种行为(中文名称)的日志量：
```sql
SELECT a1.behavior, MAX(a2.behavior_name) AS behavior_name, COUNT(*) AS num
FROM user_behavior AS a1
JOIN dim_user_behavior AS a2
ON a1.behavior = a2.behavior_id
GROUP BY a1.behavior;
```
执行过程如下所示：
```sql
hive> SELECT a1.behavior, MAX(a2.behavior_name) AS behavior_name, COUNT(*) AS num
    > FROM user_behavior AS a1
    > JOIN dim_user_behavior AS a2
    > ON a1.behavior = a2.behavior_id
    > GROUP BY a1.behavior;
Query ID = smartsi_20250814222643_ee1e9070-ecfd-4d32-b0d8-28c737ed4e83
Total jobs = 1
SLF4J: Found binding in [jar:file:/opt/workspace/apache-hive-3.1.3-bin/lib/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/workspace/hadoop-3.2.1/share/hadoop/common/lib/slf4j-log4j12-1.7.25.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
2025-08-14 22:26:49	Dump the side-table for tag: 1 with group count: 4 into file: file:/tmp/xiaosi/hive/xiaosi/fc17b844-4c2e-4b7e-abf3-94b5ff07b320/hive_2025-08-14_22-26-43_281_8547285945765234786-1/-local-10005/HashTable-Stage-2/MapJoin-mapfile01--.hashtable
2025-08-14 22:26:49	End of local task; Time Taken: 0.759 sec.
Execution completed successfully
MapredLocal task succeeded
Launching Job 1 out of 1
Number of reduce tasks not specified. Estimated from input data size: 15
In order to change the average load for a reducer (in bytes):
  set hive.exec.reducers.bytes.per.reducer=<number>
In order to limit the maximum number of reducers:
  set hive.exec.reducers.max=<number>
In order to set a constant number of reducers:
  set mapreduce.job.reduces=<number>
Starting Job = job_1755179593818_0003, Tracking URL = http://192.168.5.161:8088/proxy/application_1755179593818_0003/
Kill Command = /opt/workspace/hadoop/bin/mapred job  -kill job_1755179593818_0003
Hadoop job information for Stage-2: number of mappers: 14; number of reducers: 15
2025-08-14 22:26:58,193 Stage-2 map = 0%,  reduce = 0%
2025-08-14 22:27:08,466 Stage-2 map = 43%,  reduce = 0%
2025-08-14 22:27:17,760 Stage-2 map = 86%,  reduce = 0%
2025-08-14 22:27:22,882 Stage-2 map = 93%,  reduce = 0%
2025-08-14 22:27:23,912 Stage-2 map = 100%,  reduce = 0%
2025-08-14 22:27:24,934 Stage-2 map = 100%,  reduce = 20%
2025-08-14 22:27:25,957 Stage-2 map = 100%,  reduce = 33%
2025-08-14 22:27:28,018 Stage-2 map = 100%,  reduce = 40%
2025-08-14 22:27:29,047 Stage-2 map = 100%,  reduce = 60%
2025-08-14 22:27:30,065 Stage-2 map = 100%,  reduce = 73%
2025-08-14 22:27:31,086 Stage-2 map = 100%,  reduce = 80%
2025-08-14 22:27:32,103 Stage-2 map = 100%,  reduce = 93%
2025-08-14 22:27:33,139 Stage-2 map = 100%,  reduce = 100%
Ended Job = job_1755179593818_0003
MapReduce Jobs Launched:
Stage-Stage-2: Map: 14  Reduce: 15   HDFS Read: 3672747653 HDFS Write: 1508 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
fav	收藏商品	2888258
pv	浏览商品	89716264
buy	购买商品	2015839
cart	加入购物车	5530446
Time taken: 51.973 seconds, Fetched: 4 row(s)
```
这个看似简单的聚合查询背后，Hive 执行引擎做了大量复杂的工作。让我们逐层解析执行计划输出的每个部分。

## 1. 执行计划获取

执行如下语句获取执行计划：
```sql
EXPLAIN
SELECT a1.behavior, MAX(a2.behavior_name) AS behavior_name, COUNT(*) AS num
FROM user_behavior AS a1
JOIN dim_user_behavior AS a2
ON a1.behavior = a2.behavior_id
GROUP BY a1.behavior;
```

在默认参数配置下输出如下执行计划信息：
```sql
STAGE DEPENDENCIES:
  Stage-5 is a root stage
  Stage-2 depends on stages: Stage-5
  Stage-0 depends on stages: Stage-2

STAGE PLANS:
  Stage: Stage-5
    Map Reduce Local Work
      Alias -> Map Local Tables:
        $hdt$_1:a2
          Fetch Operator
            limit: -1
      Alias -> Map Local Operator Tree:
        $hdt$_1:a2
          TableScan
            alias: a2
            Statistics: Num rows: 4 Data size: 67 Basic stats: COMPLETE Column stats: NONE
            Filter Operator
              predicate: behavior_id is not null (type: boolean)
              Statistics: Num rows: 4 Data size: 67 Basic stats: COMPLETE Column stats: NONE
              Select Operator
                expressions: behavior_id (type: string), behavior_name (type: string)
                outputColumnNames: _col0, _col1
                Statistics: Num rows: 4 Data size: 67 Basic stats: COMPLETE Column stats: NONE
                HashTable Sink Operator
                  keys:
                    0 _col0 (type: string)
                    1 _col0 (type: string)

  Stage: Stage-2
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: a1
            Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
            Filter Operator
              predicate: behavior is not null (type: boolean)
              Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
              Select Operator
                expressions: behavior (type: string)
                outputColumnNames: _col0
                Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
                Map Join Operator
                  condition map:
                       Inner Join 0 to 1
                  keys:
                    0 _col0 (type: string)
                    1 _col0 (type: string)
                  outputColumnNames: _col0, _col2
                  Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
                  Group By Operator
                    aggregations: max(_col2), count()
                    keys: _col0 (type: string)
                    mode: hash
                    outputColumnNames: _col0, _col1, _col2
                    Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
                    Reduce Output Operator
                      key expressions: _col0 (type: string)
                      sort order: +
                      Map-reduce partition columns: _col0 (type: string)
                      Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
                      value expressions: _col1 (type: string), _col2 (type: bigint)
      Execution mode: vectorized
      Local Work:
        Map Reduce Local Work
      Reduce Operator Tree:
        Group By Operator
          aggregations: max(VALUE._col0), count(VALUE._col1)
          keys: KEY._col0 (type: string)
          mode: mergepartial
          outputColumnNames: _col0, _col1, _col2
          Statistics: Num rows: 2 Data size: 36 Basic stats: COMPLETE Column stats: NONE
          File Output Operator
            compressed: false
            Statistics: Num rows: 2 Data size: 36 Basic stats: COMPLETE Column stats: NONE
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

## 2. Stage 依赖关系解析

```sql
STAGE DEPENDENCIES:
  Stage-5 is a root stage
  Stage-2 depends on stages: Stage-5
  Stage-0 depends on stages: Stage-2
```

从上面信息可以知道：
- 该查询涉及三个执行阶段：`Stage-0`、`Stage-2` 以及 `Stage-5`
- `Stage-5` 是根阶段（root stage），即最先执行的阶段
- `Stage-2` 依赖于 `Stage-5`，表示 `Stage-2` 需要在 `Stage-5` 完成后才能执行
- `Stage-0` 依赖于 `Stage-2`，表示 `Stage-0` 需要在 `Stage-2` 完成后才能执行

## 3. Stage 执行计划解读

在这 `Stage-1` 是 MapReduce 作业执行阶段（包含 Map 和 Reduce），`Stage-0` 是 Fetch 阶段，负责将结果返回给客户端。由于 `Stage-0` 比较简单，在这着重解读一下 `Stage-1` MapReduce 作业执行阶段。这也是整个执行计划最复杂的部分，完整展示了 Hive 如何将 GROUP BY 转换为 MapReduce 作业。

> Execution mode: vectorized
这表示Hive启用了向量化执行模式，这是Hive 0.13引入的优化特性，可以一次处理一批记录而非单条记录，显著提高CPU利用率。

### 3.1 Stage-5: Map Reduce Local Work 执行阶段

标识这是一个本地工作阶段，不需要启动完整的MapReduce作业。

```sql
Stage: Stage-5
  Map Reduce Local Work
    Alias -> Map Local Tables:
      $hdt$_1:a2
        Fetch Operator
          limit: -1
    Alias -> Map Local Operator Tree:
      $hdt$_1:a2
        TableScan
          alias: a2
          Statistics: Num rows: 4 Data size: 67 Basic stats: COMPLETE Column stats: NONE
          Filter Operator
            predicate: behavior_id is not null (type: boolean)
            Statistics: Num rows: 4 Data size: 67 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              expressions: behavior_id (type: string), behavior_name (type: string)
              outputColumnNames: _col0, _col1
              Statistics: Num rows: 4 Data size: 67 Basic stats: COMPLETE Column stats: NONE
              HashTable Sink Operator
                keys:
                  0 _col0 (type: string)
                  1 _col0 (type: string)
```

### 3.2 Stage-2: MapReduce 执行阶段

```sql
Stage: Stage-2
  Map Reduce
    Map Operator Tree:
        TableScan
          alias: a1
          Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
          Filter Operator
            predicate: behavior is not null (type: boolean)
            Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              expressions: behavior (type: string)
              outputColumnNames: _col0
              Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
              Map Join Operator
                condition map:
                     Inner Join 0 to 1
                keys:
                  0 _col0 (type: string)
                  1 _col0 (type: string)
                outputColumnNames: _col0, _col2
                Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
                Group By Operator
                  aggregations: max(_col2), count()
                  keys: _col0 (type: string)
                  mode: hash
                  outputColumnNames: _col0, _col1, _col2
                  Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
                  Reduce Output Operator
                    key expressions: _col0 (type: string)
                    sort order: +
                    Map-reduce partition columns: _col0 (type: string)
                    Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
                    value expressions: _col1 (type: string), _col2 (type: bigint)
    Execution mode: vectorized
    Local Work:
      Map Reduce Local Work
    Reduce Operator Tree:
      Group By Operator
        aggregations: max(VALUE._col0), count(VALUE._col1)
        keys: KEY._col0 (type: string)
        mode: mergepartial
        outputColumnNames: _col0, _col1, _col2
        Statistics: Num rows: 2 Data size: 36 Basic stats: COMPLETE Column stats: NONE
        File Output Operator
          compressed: false
          Statistics: Num rows: 2 Data size: 36 Basic stats: COMPLETE Column stats: NONE
          table:
              input format: org.apache.hadoop.mapred.SequenceFileInputFormat
              output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
              serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
```

#### 3.2.1 Map 阶段：Map Operator Tree

Map Operator Tree 描述了在 Map 阶段执行的操作序列：
```sql
Map Operator Tree:
    TableScan
      alias: a1
      Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
      Filter Operator
        predicate: behavior is not null (type: boolean)
        Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
        Select Operator
          expressions: behavior (type: string)
          outputColumnNames: _col0
          Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
          Map Join Operator
            condition map:
                 Inner Join 0 to 1
            keys:
              0 _col0 (type: string)
              1 _col0 (type: string)
            outputColumnNames: _col0, _col2
            Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
            Group By Operator
              aggregations: max(_col2), count()
              keys: _col0 (type: string)
              mode: hash
              outputColumnNames: _col0, _col1, _col2
              Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
              Reduce Output Operator
                key expressions: _col0 (type: string)
                sort order: +
                Map-reduce partition columns: _col0 (type: string)
                Statistics: Num rows: 4 Data size: 73 Basic stats: COMPLETE Column stats: NONE
                value expressions: _col1 (type: string), _col2 (type: bigint)
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

第四个是 Reduce Output Operator，用于准备发送到 Reduce 端的数据，关键属性：
- key expressions: `_col0` 表示以 `_col0`（即behavior）作为 Reduce 的 key 进行 Shuffle
- sort order: `+` 表示按 key 升序排序
- value expressions: `_col1` 表示发送 `_col1`（即count值）到 Reduce

#### 3.2.2 Reduce 阶段：Reduce Operator Tree

Reduce Operator Tree 描述了 Reduce 阶段执行的操作：
```sql
Reduce Operator Tree:
  Group By Operator
    aggregations: max(VALUE._col0), count(VALUE._col1)
    keys: KEY._col0 (type: string)
    mode: mergepartial
    outputColumnNames: _col0, _col1, _col2
    Statistics: Num rows: 2 Data size: 36 Basic stats: COMPLETE Column stats: NONE
    File Output Operator
      compressed: false
      Statistics: Num rows: 2 Data size: 36 Basic stats: COMPLETE Column stats: NONE
      table:
          input format: org.apache.hadoop.mapred.SequenceFileInputFormat
          output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
          serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
```

第一个是 Group By Operator，用于合并 Map 端的部分聚合结果，关键属性：
- mode: `mergepartial` 表示合并部分聚合结果
  - `hive.map.aggr=true`，默认会在 Map 阶段进行一次 Group By
- aggregations:
  - `max(VALUE._col0)` 表示合并 Map 端传递过来的 `VALUE._col0` 值计算最大值
  - `count(VALUE._col1)` 表示合并 Map 端传递过来的 `VALUE._col1` 值计算个数
- keys: `KEY._col0` 表示仍按 behavior 分组
- outputColumnNames: Reduce 端输出临时列名 `_col0`、`_col1`、`_col2`（behavior对应 `_col0`，behavior_name 对应 `_col1`，num 对应`_col2`）

第二个是 File Output Operator，用于将最终结果写入文件系统，关键配置：
- compressed: `false` 表示输出未压缩
- input format: `org.apache.hadoop.mapred.SequenceFileInputFormat` 表示输入格式为 SequenceFileInputFormat
- output format: `org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat` 表示输出格式为 HiveSequenceFileOutputFormat
- serde: `org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe` 表示使用 `LazySimpleSerDe` 序列化


### 3.3 Stage-0: Fetch 阶段

Fetch 阶段将 Reduce 阶段计算的结果返回给客户端：
```sql
Stage: Stage-0
  Fetch Operator
    limit: -1
    Processor Tree:
      ListSink
```
关键属性：
- `limit: -1` 表示没有限制返回行数
- `ListSink` 表示结果将收集到列表中返回

### 3.4 注意

你可能有疑惑的是为什么在 Map 阶段多了一个 Group By Operator，为了减少 Reducer 端处理的数据量，默认会在 Map 阶段进行一次 Group By，结果根据 key 聚合。Reducer 端 `Group By Operator` 的 mode 为 `mergepartial`。这种行为是通过 `hive.map.aggr` 参数控制。如果设置 `hive.map.aggr=false`，再看一下执行计划的变化：
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
              Reduce Output Operator
                key expressions: behavior (type: string)
                sort order: +
                Map-reduce partition columns: behavior (type: string)
                Statistics: Num rows: 1 Data size: 36723474432 Basic stats: COMPLETE Column stats: NONE
      Execution mode: vectorized
      Reduce Operator Tree:
        Group By Operator
          aggregations: count()
          keys: KEY._col0 (type: string)
          mode: complete
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
可以看到 Map 阶段的 Group By Operator 没有了，Reduce 端 `Group By Operator` 的 mode 变为 `complete`。

## 4. 执行流程详解

通过执行计划，我们可以还原出完整的执行流程：
- Map阶段:
  - 读取 user_behavior 表数据
  - 提取 behavior 列
  - 在 Map 端进行部分聚合(combiner)，计算每个 Map 任务处理的数据中每个 behavior 的出现次数
- Shuffle 阶段:
  - 将 Map 端的输出按照 behavior 的值进行排序和分区
  - 相同 behavior 的记录会被发送到同一个 Reducer
    - 输出格式：<behavior, count>
- Reduce 阶段:
  - 接收来自不同 Map 任务的相同 behavior 的数据
  - 合并部分聚合结果，计算最终的 count 值
  - 将结果写入 SequenceFile
- Fetch 阶段:
  - 从 Reduce 阶段输出的文件中读取结果
  - 返回给客户端
