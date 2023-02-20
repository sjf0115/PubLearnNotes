


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


- Select Operator： 选取操作，常见的属性 ：
  - expressions：需要的字段名称及字段类型
  - outputColumnNames：输出的列名称
  - Statistics：表统计信息，包含表中数据条数，数据大小等
- Group By Operator：分组聚合操作，常见的属性：
  - aggregations：显示聚合函数信息
  - mode：聚合模式，值有 hash：随机聚合，就是hash partition；partial：局部聚合；final：最终聚合
  - keys：分组的字段，如果没有分组，则没有此字段
  - outputColumnNames：聚合之后输出列名
  - Statistics： 表统计信息，包含分组聚合之后的数据条数，数据大小等
- Reduce Output Operator：输出到reduce操作，常见属性：
  - sort order：值为空 不排序；值为 + 正序排序，值为 - 倒序排序；值为 ± 排序的列为两列，第一列为正序，第二列为倒序
- Filter Operator：过滤操作，常见的属性：
  - predicate：过滤条件，如sql语句中的where id>=1，则此处显示(id >= 1)
- Map Join Operator：join 操作，常见的属性：
  - condition map：join方式 ，如Inner Join 0 to 1 Left Outer Join0 to 2
  - keys: join 的条件字段
  - outputColumnNames： join 完成之后输出的字段
  - Statistics： join 完成之后生成的数据条数，大小等
- File Output Operator：文件输出操作，常见的属性
  - compressed：是否压缩
  - table：表的信息，包含输入输出文件格式化方式，序列化方式等
- Fetch Operator 客户端获取数据操作，常见的属性：
  - limit，值为 -1 表示不限制条数，其他值为限制的条数




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
