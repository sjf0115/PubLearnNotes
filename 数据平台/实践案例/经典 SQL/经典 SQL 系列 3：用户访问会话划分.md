在用户行为分析中，**会话（Session）** 是一个非常重要的概念。它能够帮我们回答“用户每次来用了多久”“平均每次操作几次”“哪个会话转化最高”等问题。划分会话的规则通常是：如果用户两次行为间隔超过一定阈值（比如30分钟），就认为开启了一个新会话。

这类问题也是 Hive SQL 面试中的高频考点，因为它综合考察了窗口函数、时间计算和条件分组能力。今天我们就用一道典型题目，彻底讲清楚它的解决套路。

---

## 1. 问题描述

我们有一张用户行为日志表 `user_behavior`，结构如下：

| 字段名      | 类型     | 说明                     |
|-------------|----------|--------------------------|
| user_id     | string   | 用户ID                   |
| event_time  | string   | 行为时间，格式 `yyyy-MM-dd HH:mm:ss` |

**规则**：按用户分组，按时间排序，如果相邻两次操作间隔 **超过30分钟**，则开启一个新会话。一条记录也算一个会话。

**需求**：输出每个用户的以下指标：
- `session_count`：会话总数
- `avg_session_duration_minutes`：平均会话时长（分钟）
- `avg_event_count_per_session`：平均每个会话的操作次数

这三个指标能够直观地评估用户的粘性和活跃质量。

---

## 2. 核心思路：给每个事件贴上“会话ID”

解决这类“根据间隔分组”的问题，有一个通用公式：  
**标记新分组起点 → 累积求和生成分组ID → 分组聚合**

具体步骤如下：

### 2.1 计算相邻时间差

用 `LAG()` 窗口函数获取每个用户当前事件的上一个事件时间，然后计算差值（秒）。

### 2.2 标记新会话起点

如果时间差大于 1800 秒（30分钟），或者这是用户的第一条记录（上一条时间为 NULL），则标记为 1，否则为 0。

### 2.3 用累积和生成会话ID

对标记列使用 `SUM() OVER (PARTITION BY user_id ORDER BY event_time)`，这样每碰到一个起点，会话ID就会递增，连续的记录共享同一个ID。

### 2.4 按会话ID聚合，再按用户汇总

先得到每个会话的起止时间和事件数，然后按用户计算总数、平均时长和平均事件数。

---

## 3. 完整 Hive SQL 实现

我们分步实现，每个 CTE 对应一步逻辑，清晰易懂。

```sql
WITH t1 AS (
  -- 第一步：计算与上一次操作的时间差（秒）
  SELECT
    user_id,
    event_time,
    unix_timestamp(event_time) AS ts,
    LAG(unix_timestamp(event_time)) OVER (
      PARTITION BY user_id ORDER BY event_time
    ) AS prev_ts
  FROM user_behavior
),
-- 第二步：标记新会话起点，并累积求和生成会话ID
t2 AS (
  SELECT
    user_id, event_time, ts,
    CASE
      WHEN prev_ts IS NULL OR (ts - prev_ts) > 1800 THEN 1
      ELSE 0
    END AS is_new_session
  FROM t1
),
t3 AS (
  SELECT
    user_id, event_time, ts,
    SUM(is_new_session) OVER (
      PARTITION BY user_id ORDER BY event_time
    ) AS session_id
  FROM t2
),
-- 第三步：按会话ID计算每个会话的指标
t4 AS (
  SELECT
    user_id,
    session_id,
    MIN(ts) AS session_start,
    MAX(ts) AS session_end,
    COUNT(1) AS event_count
  FROM t3
  GROUP BY user_id, session_id
),
-- 第四步：按用户计算最终指标
t5 AS (
  SELECT
    user_id,
    COUNT(1) AS session_count,
    AVG(session_end - session_start) / 60 AS avg_session_duration_minutes,
    AVG(event_count) AS avg_event_count_per_session
  FROM t4
  GROUP BY user_id
)
SELECT * FROM t5;
```

### 关键函数与技巧说明

- **`unix_timestamp(event_time)`**：将格式化时间转为秒级时间戳，便于做减法。
- **`LAG(ts) OVER (PARTITION BY user_id ORDER BY event_time)`**：获取当前行往前一行的值，没有则为 NULL。
- **`SUM(is_new_session) OVER (... ORDER BY event_time)`**：累加求和，实现连续分组号的分配。这是解决一切“连续/间隔分组”问题的核心手段。
- **会话时长 = `session_end - session_start`**，单位秒，除以60得到分钟数。
- **平均时长和平均事件数** 直接使用 `AVG` 聚合即可。

---

## 4. 测试验证

我们用具体数据跑一遍，确保逻辑正确。

### 输入示例

| user_id | event_time          |
|---------|---------------------|
| u01     | 2026-05-26 10:00:00 |
| u01     | 2026-05-26 10:10:00 |
| u01     | 2026-05-26 10:50:00 |
| u01     | 2026-05-26 11:00:00 |
| u01     | 2026-05-26 14:00:00 |
| u02     | 2026-05-26 09:00:00 |
| u02     | 2026-05-26 09:05:00 |

### 中间步骤推演（以 u01 为例）

| event_time          | prev_ts   | ts       | diff(s) | is_new | session_id |
|---------------------|-----------|----------|---------|--------|------------|
| 2026-05-26 10:00:00 | NULL      | 10:00:00 | -       | 1      | 1          |
| 2026-05-26 10:10:00 | 10:00:00  | 10:10:00 | 600     | 0      | 1          |
| 2026-05-26 10:50:00 | 10:10:00  | 10:50:00 | 2400    | 1      | 2          |
| 2026-05-26 11:00:00 | 10:50:00  | 11:00:00 | 600     | 0      | 2          |
| 2026-05-26 14:00:00 | 11:00:00  | 14:00:00 | 10800   | 1      | 3          |

从推演可以看出：
- 前两个事件间隔600秒（<1800），属于会话1。
- 第三个事件与前一个间隔2400秒（>1800），开启会话2，第四个事件又间隔600秒，属于会话2。
- 第五个事件间隔10800秒，开启会话3。

### 最终输出

| user_id | session_count | avg_session_duration_minutes | avg_event_count_per_session |
|---------|---------------|------------------------------|-----------------------------|
| u01     | 3             | 6.666...                     | 1.666...                    |
| u02     | 1             | 5.0                          | 2.0                         |

**解释**：
- u01 三个会话：会话1 10:00~10:10 (2事件,10分钟)；会话2 10:50~11:00 (2事件,10分钟)；会话3 14:00~14:00 (1事件,0分钟)。平均时长 (10+10+0)/3 ≈ 6.67分钟；平均事件数 (2+2+1)/3 ≈ 1.67。
- u02 只有一个会话：09:00~09:05 (2事件,5分钟)，平均时长5分钟，平均事件数2。

结果完全符合预期，SQL正确。

---

## 5. 进阶考点与优化

面试官可能会在此基础上深入提问，我们一一拆解：

### 1. 如何处理只有一条记录的用户？
我们的逻辑已经完美覆盖：`prev_ts IS NULL` 会使 `is_new_session = 1`，该记录单独成为一个会话，时长为0分钟，事件数为1。对应的平均时长和平均事件数也是正确值（0和1）。

### 2. 如果要求输出每个用户最长会话的详情（起止时间、事件数）？
在 `t4` 后面加一层 `ROW_NUMBER()` 排序取第一即可：

```sql
ranked_sessions AS (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY (session_end - session_start) DESC) AS rn
  FROM t4
)
SELECT user_id, session_id, session_start, session_end, event_count
FROM ranked_sessions
WHERE rn = 1;
```

### 3. 数据量极大时，如何优化性能？
- **减少时间戳转换**：如果原始表已有时间戳字段（如 `bigint`），直接用，避免 `unix_timestamp` 函数转换。
- **合理分区**：`PARTITION BY user_id` 本身容易造成数据倾斜（少数大用户）。可考虑加盐（随机前缀）后分两阶段聚合，但会话划分场景要求严格有序，加盐较为复杂。通常可先过滤掉无效数据，或对超大用户单独处理。
- **中间表持久化**：若是例行 ETL，可将 `t3` 的结果（事件带会话ID）保存下来，后续各种会话分析都可复用，避免重复计算窗口函数。

### 4. 如果会话边界是“跨天”而不是固定30分钟，怎么改？
只需修改 `CASE` 中的判断条件。例如使用 `datediff` 判断日期是否变化：
```sql
CASE WHEN prev_ts IS NULL OR datediff(to_date(event_time), to_date(prev_event_time)) >= 1 THEN 1 ELSE 0 END
```

---

## 六、总结

在 Hive SQL 中处理“根据间隔划分连续区间”的需求，万能公式就是：

1. **计算与前一行的差值** → `LAG()`  
2. **定义新分组起点的条件** → `CASE WHEN`  
3. **累积求和生成分组ID** → `SUM() OVER (ORDER BY ...)`  
4. **分组聚合得到结果**

这套组合拳不仅适用于会话划分，还适用于考勤间断识别、连续签到天数、断点续传片段切分等众多场景。

掌握它，你就能在面试中从容应对一大类窗口函数难题，也在日常工作中轻松搞定复杂的用户行为分析需求。希望这篇实战指南能帮你加深理解，写 SQL 时思路更清晰！

---
