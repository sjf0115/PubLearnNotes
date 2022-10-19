## 1. 简介

实时计算的源数据在部分场景中存在重复数据，去重成为了用户经常反馈的需求。实时计算有保留第一条（Deduplicate Keep FirstRow）和保留最后一条（Deduplicate Keep LastRow）2种去重方案。

## 2. 语法

由于 SQL 上没有直接支持去重的语法，还要灵活地保留第一条或保留最后一条。因此我们使用了 SQL 的 ROW_NUMBER OVER WINDOW 功能来实现去重语法。去重本质上是一种特殊的 TopN：
```sql
SELECT *
FROM (
   SELECT *,
    ROW_NUMBER() OVER (PARTITION BY col1[, col2..]
     ORDER BY timeAttributeCol [asc|desc]) AS rownum
   FROM table_name)
WHERE rownum = 1
```
参数说明：
ROW_NUMBER()	计算行号的OVER窗口函数。行号从1开始计算。
PARTITION BY col1[, col2..]	可选。指定分区的列，即去重的KEYS。
ORDER BY timeAttributeCol [asc|desc])	指定排序的列，必须是一个时间属性的字段（即Proctime或Rowtime）。可以指定顺序（Keep FirstRow）或者倒序 （Keep LastRow）。
rownum	仅支持rownum=1或rownum<=1。


如上语法所示，去重需要两层查询：
- 使用 ROW_NUMBER() 窗口函数来对数据根据时间属性列进行排序并标上排名。
  - 当排序字段是 Proctime 列时，Flink 就会按照系统时间去重，其每次运行的结果是不确定的。
  - 当排序字段是 Rowtime 列时，Flink 就会按照业务时间去重，其每次运行的结果是确定的。
- 对排名进行过滤，只取第一条，达到了去重的目的。
  - 排序方向可以是按照时间列的顺序，也可以是倒序：
    - Deduplicate Keep FirstRow：顺序并取第一条行数据。
    - Deduplicate Keep LastRow：倒序并取第一条行数据。

## 3. Deduplicate Keep FirstRow

保留首行的去重策略：保留KEY下第一条出现的数据，之后出现该KEY下的数据会被丢弃掉。因为STATE中只存储了KEY数据，所以性能较优，示例如下:
```sql
SELECT *
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY b ORDER BY proctime) as rowNum
  FROM T
)
WHERE rowNum = 1
```
以上示例是将 T 表按照 b 字段进行去重，并按照系统时间保留第一条数据。proctime 在这里是源表 T 中的一个具有 Processing Time 属性的字段。如果您按照系统时间去重，也可以将 proctime 字段简化 proctime() 函数调用，可以省略 proctime 字段的声明。

## 4. Deduplicate Keep LastRow

保留末行的去重策略：保留KEY下最后一条出现的数据。保留末行的去重策略性能略优于LAST_VALUE函数，示例如下：
```sql
SELECT *
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY b, d ORDER BY rowtime DESC) as rowNum
  FROM T
)
WHERE rowNum = 1
```
以上示例是将T表按照b和d字段进行去重，并按照业务时间保留最后一条数据。rowtime在这里是源表T中的一个具有Event Time属性的字段。








参考：
- https://mp.weixin.qq.com/s/_EL29V1jr0lPHCyTEuZOiw
- https://mp.weixin.qq.com/s/VL6egD76B4J7IcpHShTq7Q



...
