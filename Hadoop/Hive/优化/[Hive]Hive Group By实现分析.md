
### 1. 数据准备

订单数据如下（购买者Id，订单Id，订单编号）：
```sql
hive> SELECT PersonId, OrderId, OrderNo FROM orders;
OK
3       1       77895
3       2       44678
1       3       22456
1       4       24562
65      5       34764
```
算一下每个人下了多少订单：
```sql
SELECT PersonId, count(1)
FROM tmp_order_test
GROUP BY PersonId;
OK
1       2
3       2
65      1
```

### 2. 计算过程


### 3. 执行计划

```
set hive.map.aggr=true;
```

```
// Stage依赖关系
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

// Stage 计划
STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree: // Map阶段
          TableScan // 表扫描
            alias: tmp_order_test // 表名
            Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
            Select Operator // 选择列
              expressions: personid (type: string)
              outputColumnNames: _col0
              Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
              Group By Operator // Map端Group By
                aggregations: count(1) // 聚合
                keys: _col0 (type: string)
                mode: hash
                outputColumnNames: _col0, _col1
                Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator // 输出到Reduce
                  key expressions: _col0 (type: string)
                  sort order: +
                  Map-reduce partition columns: _col0 (type: string)
                  Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
                  value expressions: _col1 (type: bigint)
      Reduce Operator Tree: // Reduce阶段
        Group By Operator // Reduce端Group By
          aggregations: count(VALUE._col0) // 聚合
          keys: KEY._col0 (type: string)
          mode: mergepartial
          outputColumnNames: _col0, _col1
          Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
          File Output Operator // 输出到文件
            compressed: false
            Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
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
为了减少 Reducer 端处理的数据量，`hive.map.aggr`默认设置为`true`，所以先会在 Mapper 端进行一次 Group By，结果根据 key 聚合。Reducer 端 `Group By Operator` 的 mode 为 `mergepartial`。如果设置 `hive.map.aggr=false`，Reducer 端 `Group By Operator` 的 mode 为 `complete`。

```
Map Operator Tree: // Map阶段
    TableScan // 扫描表
      alias: tmp_order_test // 表名
      Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
      Select Operator // 选择字段
        expressions: personid (type: string)
        outputColumnNames: _col0
        Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
        Reduce Output Operator // 输出到Reduce
          key expressions: _col0 (type: string)
          sort order: +
          Map-reduce partition columns: _col0 (type: string)
          Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
```










....
