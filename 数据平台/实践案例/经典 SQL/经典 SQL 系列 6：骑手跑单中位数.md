## 1. 需求

假设有一张骑手跑单汇总表 dws_mt_qs_order_dd，包含 qs_id（骑手id）、order_cnt（跑单量）、snap_dt（统计日期）三个字段。需求是计算近1个月每个外卖员跑单的中位数是多少。

> 注意：如果外卖员当天没跑单，不在中位数统计范围内；

## 2. 数据准备

假设 dws_online_shop_ms 表有如下数据：

| qs_id | order_cnt | snap_dt |
| :------------- | :------------- | :------------- |
| 001 | 1000 | 20241010 |
| 001 | 300  | 20241011 |
| 001 | 600  | 20241012 |
| 002 | 100  | 20241010 |
| 002 | 500  | 20241011 |

```sql
CREATE TABLE dws_mt_qs_order_dd (
  qs_id varchar(20),
  order_cnt bigint,
  snap_dt varchar(20)
);

INSERT INTO dws_mt_qs_order_dd VALUES
  ('001',1000,'20241010'),
  ('001',300,'20241011'),
  ('001',600,'20241012'),
  ('002',100,'20241010'),
  ('002',500,'20241011');
```


结算结果应该输出如下结果：

| qs_id | order_cnt |
| :------------- | :------------- |
| 001 | 600 |
| 002 | 100 |
| 002 | 500 |

## 3. 方案

我们需要计算每个骑手在近1个月内的跑单量中位数。中位数是将一组数值按大小顺序排列后位于中间位置的值。如果数据个数为奇数，中位数就是这组数据排序后的中间那个数；如果数据个数为偶数，中位数是这组数据排序后中间两个数的平均值。



```sql
WITH dws_mt_qs_order_dd AS (
    SELECT qs_id, order_cnt, snap_dt
    FROM VALUES
      ('001',1000,'20241010'),
      ('001',300,'20241011'),
      ('001',600,'20241012'),
      ('002',100,'20241010'),
      ('002',500,'20241011') t(qs_id, order_cnt, snap_dt)
),
order_rank AS (
    -- 正序排序和倒序排序
    SELECT
        qs_id, order_cnt
        ROW_NUMBER() OVER (PARTITION BY qs_id ORDER BY order_cnt) AS asc_rank,
        ROW_NUMBER() OVER (PARTITION BY qs_id ORDER BY order_cnt DESC) AS desc_rank,
        COUNT(*) OVER(PARTITION BY qs_id) AS num
    FROM dws_mt_qs_order_dd
    WHERE MONTH(snap_dt) = '${month}'
)

SELECT qs_id, order_cnt, asc_rank
FROM order_rank
WHERE asc_rk >= num/2 AND desc_rk >= num/2;



```





...
