## 1. 简介

窗口 TopN 是一种特殊的 TopN，会为每个窗口以及分区键返回 N 个最小或者最大的值。窗口 TopN 是基于窗口表值函数 TVF 实现的，因此窗口 TopN 可以和窗口表值函数、窗口关联等操作一起使用。由于窗口 TopN 是基于窗口的操作，因此在窗口结束时，会自动把窗口状态数据清除。

之前介绍过[流式 TopN](https://smartsi.blog.csdn.net/article/details/151902584)，为什么还需要窗口 TopN 呢？流式 TopN 每次计算得到的结果都是中间结果，结果数据流是 Retract 流，从而出现回撤数据。而窗口 TopN 则是在窗口结束时输出最终结果，产出的结果数据流是 Append-only 流（即不会产生回撤记录），只会在到达窗口末尾时产生总共 Top N 条记录。

> 需要注意的是窗口 TopN 不支持分组窗口聚合函数。

## 2. 语法

窗口 TopN 可以用与常规 TopN 相同的语法定义，有关更多信息，请参阅 [TopN](https://smartsi.blog.csdn.net/article/details/151902584) 文档。此外，窗口 Top-N 要求 PARTITION BY 子句要包含窗口 TVF 或窗口聚合关系的 window_start 和 window_end 列。否则，优化器将无法转换查询。

窗口 TopN 语句的语法如下:
```sql
SELECT [column_list]
FROM (
   SELECT
      [column_list],
      ROW_NUMBER() OVER (
  PARTITION BY window_start, window_end [, col_key1...]
  ORDER BY col1 [asc|desc][, col2 [asc|desc]...]
      ) AS rownum
   FROM table_name -- 窗口表值函数
)
WHERE rownum <= N [AND conditions]
```
参数说明：
- `ROW_NUMBER()`：根据分区内的行顺序，为每一行分配一个惟一的行号，行号计算从1开始。目前，Over 窗口函数中只支持 ROW_NUMBER。未来还会支持 RANK()和 DENSE_RANK()。
- `PARTITION BY col1[, col2..]`：分区列，每个分区都有一个 TopN 结果。
  - 需要注意的是，分区列中必须包含 window_start 和 window_end 两列。
  - 这两个字段源于[窗口表值函数](https://smartsi.blog.csdn.net/article/details/127162902)中的窗口开始时间和窗口结束时间字段。只有指定了这两个字段，Flink 引擎才会将上述 SQ 翻译为窗口 TopN 来执行。
- `ORDER BY col1 [asc|desc][, col2 [asc|desc]...]`：指定排序的列和每列的排序方向，不同列上排序方向可以不同。
- `WHERE rownum <= N`：需要 rownum <= N 才能让 Flink 识别该查询是 TopN 查询。N 表示将保留最小或最大的 N 条记录。
- `[AND conditions]`：在 where 子句中可以自由添加其他条件，但其他条件只能使用 AND 连接与 `rownum <= N` 进行组合。

目前，窗口 TopN 只支持与窗口 TVF 的滚动窗口、滑动窗口以及累积窗口配合使用。目前还不支持带会话窗口的窗口 TVF，在不久的将来会支。

## 3. 示例

假设有一张商品上架表，包含商品ID、商品类目、商品下单金额以及商品上架时间：

| product_id | category | price | timestamp | 备注 |
| :------------- | :------------- | :------------- | :------------- | :------------- |
| 1001 | 图书 | 40  | 1665360300000 | 2022-10-10 08:05:00 |
| 2001 | 生鲜 | 80  | 1665360360000 | 2022-10-10 08:06:00 |
| 1002 | 图书 | 30  | 1665360420000 | 2022-10-10 08:07:00 |
| 2002 | 生鲜 | 80  | 1665360480000 | 2022-10-10 08:08:00 |
| 2003 | 生鲜 | 150 | 1665360540000 | 2022-10-10 08:09:00 |
| 1003 | 图书 | 100 | 1665360470000 | 2022-10-10 08:05:50 |
| 2004 | 生鲜 | 70  | 1665360660000 | 2022-10-10 08:11:00 |
| 2005 | 生鲜 | 20  | 1665360720000 | 2022-10-10 08:12:00 |
| 1004 | 图书 | 10  | 1665360780000 | 2022-10-10 08:13:00 |
| 2006 | 生鲜 | 120 | 1665360840000 | 2022-10-10 08:14:00 |
| 1005 | 图书 | 20  | 1665360900000 | 2022-10-10 08:15:00 |
| 1006 | 图书 | 60  | 1665360896000 | 2022-10-10 08:14:56 |
| 1007 | 图书 | 90  | 1665361080000 | 2022-10-10 08:18:00 |

需求是计算每 10 分钟内下单量最高的前 2 个商品类目并输出下单总金额和下单次数：
```sql
SELECT window_start, window_end, category, price, cnt, row_num
FROM (
  SELECT
    window_start, window_end, category, price, cnt,
    ROW_NUMBER() OVER (PARTITION BY window_start, window_end ORDER BY price DESC) AS row_num
  FROM (
    SELECT
      window_start, window_end, category,
      SUM(price) AS price, COUNT(*) AS cnt
    FROM TABLE(
      TUMBLE(TABLE shop_sales, DESCRIPTOR(ts_ltz), INTERVAL '5' MINUTES)
    )
    GROUP BY window_start, window_end, category
  )
) WHERE row_num <= 3
```
实际效果如下所示：

| op |  window_start |  window_end | category | price |  cnt |  row_num |
| :------------- | :------------- | :------------- | :------------- | :------------- | :------------- | :------------- |
| +I | 2022-10-10 00:05:00.000 | 2022-10-10 00:10:00.000 | 生鲜 | 310 | 3 | 1 |
| +I | 2022-10-10 00:05:00.000 | 2022-10-10 00:10:00.000 | 图书 | 170 | 3 | 2 |
| +I | 2022-10-10 00:10:00.000 | 2022-10-10 00:15:00.000 | 生鲜 | 210 | 3 | 1 |
| +I | 2022-10-10 00:10:00.000 | 2022-10-10 00:15:00.000 | 图书 | 70  | 2 | 2 |
| +I | 2022-10-10 00:15:00.000 | 2022-10-10 00:20:00.000 | 图书 | 110 | 2 | 1 |


> 从上面可以看出 Window TopN 结果是 Append 流，不会出现回撤数据，因为 Window TopN 实现是在窗口结束时输出最终结果，不会产生中间结果
