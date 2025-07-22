## 1. 需求

给你一个用户行为日志表 tb_user_log(uid, in_time, out_time)。用户等级标准：
- 忠实用户：近7天活跃过且非新晋用户
- 新晋用户：近7天新增，即首次活跃在近7天
- 沉睡用户：近7天未活跃但近30天内活跃过
- 流失用户：近30天未活跃但更早前活跃过

请你统计各活跃度分层的用户占比。

## 2. 数据准备

假设 tb_user_log 表有如下数据：

| uid | in_time | out_time |
| :------------- | :------------- | :------------- |


## 3. 思路

- 计算每个用户最早活跃日期 (first_dt) 和最晚活跃日期 (last_dt)
- 确定当前日期 (cur_dt) 为数据中的最大日期，并计算总用户数 (total_user_cnt)
- 计算每个用户 first_dt 和 last_dt 距离 cur_dt 的天数差
- 使用 CASE WHEN 根据天数差进行用户分级
- 按用户等级分组，计算各等级用户数，然后计算占比。

## 4. 实现

```sql
-- 步骤1: 计算用户首次和最近活跃日期
WITH user AS (
  SELECT
    uid,
    TO_DATE(MIN(in_time)) AS first_active_date,  -- 首次活跃
    TO_DATE(MAX(out_time)) AS last_active_date    -- 最近活跃
    DATE_SUB(TO_DATE('${date}'), 6) AS date_7, -- 用于计算最近7天是否活跃
    DATE_SUB(TO_DATE('${date}'), 29) AS date_30, -- 用于计算最近30天是否活跃
  FROM tb_user_log
  GROUP BY uid
),
-- 步骤2: 标记用户分层
user_layer AS (
  SELECT
    uid, first_active_date, last_active_date,
    CASE
      -- 优先判断新晋用户（首次活跃在7天内）
      WHEN first_active_date >= date_7 THEN '新晋用户'
      -- 再判断忠实用户（最近活跃在7天内）
      WHEN last_active_date >= date_7 THEN '忠实用户'
      -- 沉睡用户（最近活跃在8-30天）
      WHEN last_active_date >= date_30 THEN '沉睡用户'
      -- 其余为流失用户
      ELSE '流失用户'
    END AS layer
  FROM user
),
-- 步骤3: 统计各分层用户量
user_layer_uv AS (
  SELECT layer, COUNT(*) AS layer_uv
  FROM user_layer
  GROUP BY layer
),
-- 步骤4: 统计各分层占比
SELECT layer, layer_uv, uv, ROUND(layer_uv/uv, 3) AS ratio
FROM (
  SELECT layer, layer_uv, SUM(uv) OVER (PARTITION BY layer) AS uv
  FROM user_layer_uv
) AS a1;
```

https://mp.weixin.qq.com/s/azxPgNjjV0ka5uy9Fu9HaQ
