


### 1. 执行计划解读

用 EXPLAIN 打开的执行计划包含以下两部分：
- 作业的依赖关系图，即 STAGE DEPENDENCIES。
- 每个作业的详细信息，即 STAGE PLANS。

一个 MR 的执行计划分为两个部分：
- Map Operator Tree：MAP端的执行计划
- Reduce Operator Tree：Reduce端的执行计划
- Processor Tree

Operator|描述
---|---
TableScanOperator| 从表中读取数据
ReduceOutputOperator| Map阶段结束，将结果数据输出到Reducer
Fetch Operator | 
JoinOperator| Join操作
SelectOperator| Reduce阶段输出select中的列
FileSinkOperator| 将结果数据输出到输出文件
FilterOperator| 过滤输入数据
GroupByOperator|*
MapJoinOperator|*
LimitOperator|*
UnionOperator|*


```sql
EXPLAIN
SELECT uid, wid, time, content
FROM dws_app_pub_user_behavior_1d
WHERE dt = '20150831' AND time LIKE '%2015-08-31 15%';
```

```
STAGE DEPENDENCIES:
  Stage-0 is a root stage

STAGE PLANS:
  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        TableScan
          alias: dws_app_pub_user_behavior_1d
          Statistics: Num rows: 5724 Data size: 1450359 Basic stats: COMPLETE Column stats: NONE
          Filter Operator
            predicate: (time like '%2015-08-31 15%') (type: boolean)
            Statistics: Num rows: 2862 Data size: 725179 Basic stats: COMPLETE Column stats: NONE
            Select Operator
              expressions: uid (type: string), wid (type: string), time (type: string), content (type: string)
              outputColumnNames: _col0, _col1, _col2, _col3
              Statistics: Num rows: 2862 Data size: 725179 Basic stats: COMPLETE Column stats: NONE
              ListSink
```
