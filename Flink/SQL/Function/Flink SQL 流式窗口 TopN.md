https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/sql/queries/window-topn/
https://mp.weixin.qq.com/s/gd2XIlLx-LjZr0pUJnxSRQ

## 1. 简介

窗口 TopN 是一种特殊的 TopN，会为每个窗口以及分区键返回 N 个最小或者最大的值。

与常规 TopN 不同的是，窗口 TopN 不会产生中间结果（即不会产生回撤记录），只会在到达窗口末尾时产生总共 Top N 条记录。更重要的是，窗口 TopN 会清除所有不再需要的中间状态。因此，如果用户不需要每条记录的更新结果，那么窗口 TopN 查询具有更好的性能。通常，窗口 TopN 与窗口 TVF 一起直接使用。此外，窗口 TopN 还可以与基于窗口 TVF 的其他操作一起使用，例如窗口聚合、窗口 TopN 和窗口 JOIN。

## 2. 语法

窗口 TopN 可以用与常规 TopN 相同的语法定义，有关更多信息，请参阅 TopN 文档。此外，窗口 Top-N 要求 PARTITION BY 子句要包含窗口 TVF 或窗口聚合关系的 window_start 和 window_end 列。否则，优化器将无法转换查询。

窗口 TopN 语句的语法如下:
```sql
SELECT [column_list]
FROM (
   SELECT [column_list],
     ROW_NUMBER() OVER (PARTITION BY window_start, window_end [, col_key1...]
       ORDER BY col1 [asc|desc][, col2 [asc|desc]...]) AS rownum
   FROM table_name) -- relation applied windowing TVF
WHERE rownum <= N [AND conditions]
```
参数说明：
- `ROW_NUMBER()`：根据分区内的行顺序，为每一行分配一个惟一的行号，行号计算从1开始。目前，Over 窗口函数中只支持 ROW_NUMBER。未来还会支持 RANK()和 DENSE_RANK()。
- `PARTITION BY col1[, col2..]`：分区列，每个分区都有一个 TopN 结果。需要注意的是，分区列中必须包含 window_start 和 window_end 两列。
- `ORDER BY col1 [asc|desc][, col2 [asc|desc]...]`：指定排序的列和每列的排序方向，不同列上排序方向可以不同。
- `WHERE rownum <= N`：需要 rownum <= N 才能让 Flink 识别该查询是 TopN 查询。N 表示将保留最小或最大的 N 条记录。
- `[AND conditions]`：在 where 子句中可以自由添加其他条件，但其他条件只能使用 AND 连接与 `rownum <= N` 进行组合。

目前，Flink 只支持窗口 TopN 与窗口 TVF 的滚动窗口、滑动窗口以及累积窗口配合使用。目前还不支持带会话窗口的窗口 TVF，在不久的将来会支。

## 3. 示例

### 3.1

下面的例子展示了如何计算 10 分钟的滚动窗口中下单量最高的前 2 个商品类目：
```sql
INSERT INTO shop_category_order_top
SELECT
  window_start, window_end, category,
  price, cnt, row_num
FROM (
  SELECT
    window_start, window_end, category,
    price, cnt,
    ROW_NUMBER() OVER (PARTITION BY window_start, window_end ORDER BY price DESC) AS row_num
  FROM (
    SELECT
      window_start, window_end, category,
      SUM(price) AS price, COUNT(*) AS cnt
    FROM TABLE(
      TUMBLE(TABLE shop_sales, DESCRIPTOR(ts_ltz), INTERVAL '10' MINUTES)
    )
    GROUP BY window_start, window_end, category
  )
) WHERE row_num <= 2
```

```
3001,服装,80,1665360060000 // 2022-10-10 08:01:00
3002,服装,90,1665360120000 // 2022-10-10 08:02:00
1001,图书,40,1665360300000 // 2022-10-10 08:05:00
2001,生鲜,40,1665360360000 // 2022-10-10 08:06:00
1002,图书,20,1665360420000 // 2022-10-10 08:07:00
2002,生鲜,30,1665360480000 // 2022-10-10 08:08:00
4001,数码,50,1665360540000 // 2022-10-10 08:09:00
1003,图书,80,1665360600000 // 2022-10-10 08:10:00
2004,生鲜,20,1665360660000 // 2022-10-10 08:11:00
5005,玩具,20,1665360720000 // 2022-10-10 08:12:00
1004,图书,10,1665360780000 // 2022-10-10 08:13:00
2006,生鲜,20,1665360840000 // 2022-10-10 08:14:00
4003,数码,70,1665360900000 // 2022-10-10 08:15:00
3003,服装,70,1665360960000 // 2022-10-10 08:16:00
1005,图书,60,1665361020000 // 2022-10-10 08:17:00
1006,图书,40,1665361080000 // 2022-10-10 08:18:00
2007,生鲜,40,1665361260000 // 2022-10-10 08:21:00
```
实际效果如下所示：
```
+I[2022-10-10T08:00, 2022-10-10T08:10, 服装, 170, 2, 1]
+I[2022-10-10T08:00, 2022-10-10T08:10, 生鲜, 70, 2, 2]
+I[2022-10-10T08:10, 2022-10-10T08:20, 图书, 190, 4, 1]
+I[2022-10-10T08:10, 2022-10-10T08:20, 数码, 70, 1, 2]
```




参考：
- https://mp.weixin.qq.com/s/gd2XIlLx-LjZr0pUJnxSRQ
