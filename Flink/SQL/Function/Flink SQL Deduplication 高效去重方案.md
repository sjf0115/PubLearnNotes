## 1. 简介

Deduplication 其实就是去重，删除在一组指定列上重复的行，只保留第一行或者最后一行。在某些情况下，上游 ETL 作业并不能保证端到端的 Exactly-Once 语义。在故障恢复时，可能会导致 Sink 中出现重复的记录。然而，重复记录会影响下游分析作业的正确性，例如 SUM, COUNT，因此在进一步分析之前需要删除重复数据。

## 2. 语法

由于 SQL 上没有直接支持去重的语法，还要灵活地保留第一行或者保留最后一行。因此我们使用了 SQL 的 ROW_NUMBER OVER WINDOW 功能来实现去重语法：
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
- `ROW_NUMBER()`：根据分区内的行顺序，为每一行分配一个惟一的行号，行号计算从1开始。
- `PARTITION BY col1[, col2..]`：分区列，即去重 KEYS。
- `ORDER BY timeAttributeCol [asc|desc])`：指定排序列，必须是一个时间属性的字段（即 Proctime 或 Rowtime）。可以指定顺序（Keep FirstRow）或者倒序 （Keep LastRow）。
- `WHERE rownum = 1`：仅支持rownum=1或rownum<=1。

从上面语法可以看出，Deduplication 去重本质上是一种特殊的 TopN。但是这里有一点不一样的地方是排序字段必须是时间属性列，不能是其他非时间属性的普通列。在 rownum = 1 时，如果排序字段是普通列 planner 会翻译成 TopN 算子；如果是时间属性列 planner 会翻译成 Deduplication，这两者最终的执行算子是不一样的，Deduplication 相比 TopN 算子专门做了对应的优化，性能会有很大提升。此外，如果排序字段是 Proctime 列，Flink 就会按照系统时间去重，其每次运行的结果是不确定的；如果排序字段是 Rowtime 列，Flink 就会按照业务时间去重，其每次运行的结果是确定的。

Deduplication 去重对排名进行过滤，只取第一条（rownum = 1），从而达到了去重的目的。根据排序字段的方向不同，有保留第一行（Deduplicate Keep FirstRow）和保留最后一行（Deduplicate Keep LastRow）2种去重策略。如果排序字段方向是 `ASC`（正序方向），即对应只保留第一行（Deduplicate Keep FirstRow）策略；如果排序字段方向是 `DESC`（倒序方向），即对应保留最后一行（Deduplicate Keep LastRow）策略。

## 3. 去重策略

### 3.1 保留第一行

保留首行的去重策略就是保留 KEY 下第一条出现的数据，之后该 KEY 下出现的数据会被丢弃。因为状态中只存储了 KEY 数据，所以性能较优，示例如下:
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

```
2> +I[图书, 1002, 40, 2022-10-10T00:05:00Z, 1]
2> -U[图书, 1002, 40, 2022-10-10T00:05:00Z, 1]
2> +U[图书, 1001, 60, 2022-10-10T00:04:59Z, 1]
1> +I[生鲜, 2001, 40, 2022-10-10T00:06:00Z, 1]
```


### 3.2 保留最后一行

保留末行的去重策略就是保留 KEY 下最后一条出现的数据。示例如下：
```sql
SELECT *
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY b, d ORDER BY rowtime DESC) as rowNum
  FROM T
)
WHERE rowNum = 1
```
以上示例是将 T 表按照b和d字段进行去重，并按照业务时间保留最后一条数据。rowtime在这里是源表T中的一个具有Event Time属性的字段。

```
2> +I[图书, 1002, 40, 2022-10-10T00:05:00Z, 1]
1> +I[生鲜, 2001, 40, 2022-10-10T00:06:00Z, 1]
2> -U[图书, 1002, 40, 2022-10-10T00:05:00Z, 1]
2> +U[图书, 1003, 20, 2022-10-10T00:07:00Z, 1]
1> -U[生鲜, 2001, 40, 2022-10-10T00:06:00Z, 1]
1> +U[生鲜, 2002, 30, 2022-10-10T00:08:00Z, 1]
2> -U[图书, 1003, 20, 2022-10-10T00:07:00Z, 1]
2> +U[图书, 1003, 80, 2022-10-10T00:10:00Z, 1]
1> -U[生鲜, 2002, 30, 2022-10-10T00:08:00Z, 1]
1> +U[生鲜, 2003, 20, 2022-10-10T00:11:00Z, 1]
```






参考：
- https://mp.weixin.qq.com/s/_EL29V1jr0lPHCyTEuZOiw
- https://mp.weixin.qq.com/s/VL6egD76B4J7IcpHShTq7Q



...
