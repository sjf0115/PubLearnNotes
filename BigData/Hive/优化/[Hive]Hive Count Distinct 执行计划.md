
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
算一下一共多少人下了订单：
```sql
SELECT COUNT(DISTINCT PersonId)
FROM tmp_order_test;
OK
3
```

```sql
EXPLAIN extended
SELECT COUNT(DISTINCT PersonId)
FROM tmp_order_test;
```

```
STAGE DEPENDENCIES: //stage依赖
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

STAGE PLANS: // stage计划
  Stage: Stage-1
    Map Reduce
      Map Operator Tree: // Map阶段
          TableScan // 表扫描
            alias: tmp_order_test // 表名称
            Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
            Select Operator // 选择列
              expressions: personid (type: string)
              outputColumnNames: personid
              Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
              Group By Operator // Map端Group By
                aggregations: count(DISTINCT personid) // 聚合
                keys: personid (type: string)
                mode: hash
                outputColumnNames: _col0, _col1
                Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
                Reduce Output Operator // 输出到Reduce
                  key expressions: _col0 (type: string)
                  sort order: +
                  Statistics: Num rows: 1 Data size: 51 Basic stats: COMPLETE Column stats: NONE
      Reduce Operator Tree: // Reduce阶段
        Group By Operator // Reduce端Group By
          aggregations: count(DISTINCT KEY._col0:0._col0) // 聚合
          mode: mergepartial
          outputColumnNames: _col0
          Statistics: Num rows: 1 Data size: 16 Basic stats: COMPLETE Column stats: NONE
          File Output Operator // 输出到文件
            compressed: false
            Statistics: Num rows: 1 Data size: 16 Basic stats: COMPLETE Column stats: NONE
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
