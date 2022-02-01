
```sql
SELECT
  -- 所有订单量
  COUNT(1) AS all_order_pv,
  -- 有效订单量   orderFlag=1 表示有效订单
  COUNT(CASE orderFlag WHEN '1' THEN 1 ELSE NULL END) AS valid_order_pv,
  -- 所有下单用户
  COUNT(DISTINCT uid) AS all_order_uv,
  -- 有效下单用户
  COUNT(DISTINCT CASE orderFlag WHEN '1' THEN uid ELSE NULL END) AS valid_order_uv,
  -- 所有下单票数
  SUM(num) AS all_order_num,
  -- 有效下单票数
  SUM(CASE orderFlag WHEN '1' THEN num ELSE NULL END) AS valid_order_num
from order
where dt = '20180521';
```
