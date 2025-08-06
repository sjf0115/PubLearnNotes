## 1. 需求

假设有一张店铺 GMV 汇总表 dws_online_shop_ms, 包含 shopid（店铺id）、gmv（成交总额）两个字段。需求是计算超过所有店铺 GMV 中位数的店铺及 GMV。

## 2. 数据准备

假设 dws_online_shop_ms 表有如下数据：

| shopid| gmv |
| :------------- | :------------- |
| 001 | 10 |
| 002 | 50 |
| 003 | 40 |
| 004 | 30 |



## 3. 方案


-- 输入
shopid  gmv

-- 输出
shopid  gmv
002     50
003     40
