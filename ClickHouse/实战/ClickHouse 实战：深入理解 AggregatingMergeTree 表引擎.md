# ClickHouse 实战：深入理解 AggregatingMergeTree 表引擎

在数据仓库和 OLAP 系统中，"预聚合"是一种经典的以空间换时间的优化策略。ClickHouse 的 `AggregatingMergeTree` 正是这一思想的工程实现——它将聚合计算从查询阶段前移到数据合并阶段，通过在后台自动合并数据分片（Part）时执行聚合运算，将明细数据压缩为高度聚合的中间状态。

本文作为 MergeTree 家族系列的第四篇，将深入剖析 `AggregatingMergeTree` 的工作原理、使用方法和生产实践。

## 1. 概述

### 1.1 核心定位

`AggregatingMergeTree` 是 `SummingMergeTree` 的"升级版"。如果说 `SummingMergeTree` 只能做 SUM 一种聚合操作，那么 `AggregatingMergeTree` 则支持**任意聚合函数**：

| 引擎 | 支持的聚合操作 | 聚合列类型 | 典型场景 |
|---|---|---|---|
| [SummingMergeTree](https://smartsi.blog.csdn.net/article/details/157103654) | 仅 SUM | 普通数值类型 | 求和统计 |
| **AggregatingMergeTree** | SUM/COUNT/AVG/MIN/MAX/UNIQ 等任意函数 | AggregateFunction 类型 | 多维分析、UV 计算 |

### 1.2 工作原理

```
数据写入阶段：                    后台合并阶段：
┌────────────┐                 ┌────────────────┐
│ Part 1     │                 │                │
│ k=A, v=S1  │──── 合并 ────→  │ Merged Part    │
│ k=A, v=S2  │                 │ k=A, v=merge() │
│ k=B, v=S3  │                 │ k=B, v=S3      │
└────────────┘                 └────────────────┘
┌────────────┐
│ Part 2     │
│ k=A, v=S4  │──── 合并 ────→ 与 Part 1 的合并结果再次合并
└────────────┘
```

核心流程：
1. **写入**：数据以明细形式写入，每行保存的是聚合函数的**中间状态**（二进制）
2. **合并**：后台线程合并同一 Part 内排序键相同的行，调用聚合函数的 **merge** 方法合并状态
3. **查询**：使用 `*Merge` 函数从中间状态计算出最终结果

### 1.3 与其他引擎的对比

| 对比维度 | MergeTree | SummingMergeTree | AggregatingMergeTree |
|---|---|---|---|
| 合并行为 | 保留所有行 | 合并同 Key 行，SUM 数值列 | 合并同 Key 行，执行任意聚合函数 |
| 聚合列类型 | 普通类型 | 普通数值类型 | AggregateFunction |
| 聚合时机 | 不聚合 | Part 合并时 | Part 合并时 |
| 查询方式 | 直接查询 | 直接查询或 GROUP BY | 必须使用 *Merge 函数 |




## 2. 从 SummingMergeTree 说起

在 [SummingMergeTree](https://smartsi.blog.csdn.net/article/details/157103654) 中，我们已经实现了一种预聚合能力——当 Part 合并时，相同排序键的行会被合并，数值列被 SUM 求和。例如：
```sql
CREATE TABLE visit_sum (
    city    String,
    day     Date,
    pv      UInt64,
    uv      UInt64   -- 注意：这里存的是"去重后的用户数"
)
ENGINE = SummingMergeTree()
ORDER BY (city, day);
```

当我们写入数据时：
```sql
INSERT INTO visit_sum VALUES ('beijing', '2024-01-15', 100, 50);
INSERT INTO visit_sum VALUES ('beijing', '2024-01-15', 200, 80);
```

合并后：

```sql
SELECT * FROM visit_sum FINAL;
-- city='beijing', day='2024-01-15', pv=300, uv=130  ← ❌ UV 被简单求和了！
```

**问题出现了**：UV（独立访客数）不能简单求和！同一个用户在两次访问中可能都出现了，直接 `50 + 80 = 130` 是错误的，正确值应该 ≤ 130。

| 指标 | SUM 求和是否正确 | 原因 |
|---|---|---|
| PV（页面浏览量） | ✅ 正确 | 每次访问独立计数 |
| UV（独立访客） | ❌ 错误 | 同一用户多次访问被重复计数 |
| 平均停留时长 | ❌ 错误 | 平均值不能直接相加再求和 |
| P99 延迟 | ❌ 错误 | 分位数不能简单相加 |

**本质矛盾**：SummingMergeTree 只会做 SUM 一种聚合运算，但真实业务中，我们经常需要 COUNT、AVG、UNIQ（去重计数）、分位数等**多种聚合函数**。

这就是 `AggregatingMergeTree` 要解决的问题——它让 Part 合并时可以执行 **任意聚合函数**，而不仅仅是 SUM。

## 3. 关键设计：AggregateFunction 数据类型

### 3.1 问题的本质

要让 Part 合并时能执行"任意聚合函数"，首先需要解决一个核心问题：**如何在磁盘上存储聚合的中间状态？**

以 SUM 为例：两行数据 `pv=100` 和 `pv=200`，合并时直接 `100+200=300`，这是简单的数值运算。

但如果是 UNIQ（去重计数）呢？假设第一批有 50 个用户，第二批有 80 个用户，它们可能有交集。要做到正确的去重，我们需要保存的 **不是结果数字**，而是 **能够后续合并的中间状态**。

### 3.2 AggregateFunction 是什么

ClickHouse 为此设计了一种全新的数据类型——`AggregateFunction`。它存储的不是最终结果，而是 **聚合函数的中间计算状态**：

```sql
-- 语法：AggregateFunction(聚合函数名, 输入参数类型)
AggregateFunction(sum, UInt64)          -- 存储 sum 的中间状态（一个累加器）
AggregateFunction(count)                -- 存储 count 的中间状态（一个计数器）
AggregateFunction(uniq, String)         -- 存储 uniq 的中间状态（HyperLogLog 草图）
AggregateFunction(avg, Float64)         -- 存储 avg 的中间状态（sum + count 两个值）
AggregateFunction(quantile(0.99), Float64) -- 存储分位数的中间状态（t-digest）
AggregateFunction(argMax, String, DateTime) -- 存储 argMax 的中间状态
```

**关键认知**：AggregateFunction 列的值不是普通数据，而是一种 **二进制序列化的状态对象**。这正是它能被"合并"的原因——两个中间状态可以通过 merge 操作合并为一个新的中间状态。

### 3.3 三种操作后缀：State、Merge、MergeState

为了操作这种特殊的二进制状态，ClickHouse 为每个聚合函数派生了三种后缀变体：
```
原始数据 ──*State──→ 中间状态 ──*Merge──→ 最终结果
                       │
                       └──*MergeState──→ 新的中间状态（用于二次聚合）
```

| 后缀 | 作用 | 输入 | 输出 | 使用场景 |
|---|---|---|---|---|
| `*State` | 将原始值转化为中间状态 | 原始数据 | `AggregateFunction(...)` | INSERT 写入时 |
| `*Merge` | 将中间状态转化为最终结果 | `AggregateFunction(...)` | 具体数值 | SELECT 查询时 |
| `*MergeState` | 将多个中间状态合并为一个 | `AggregateFunction(...)` | `AggregateFunction(...)` | 物化视图嵌套聚合时 |

**具体示例**：

```sql
-- sumState：将数值 100 转化为 sum 的中间状态
sumState(toUInt64(100))   -- 返回类型: AggregateFunction(sum, UInt64)

-- sumMerge：从中间状态计算出最终的求和结果
sumMerge(state_column)    -- 返回类型: UInt64

-- sumMergeState：将两个 sum 的中间状态合并为一个
sumMergeState(state_column) -- 返回类型: AggregateFunction(sum, UInt64)
```

### 3.4 SimpleAggregateFunction：轻量替代方案

对于某些"简单"的聚合函数（结果可以直接存储，无需复杂二进制状态），ClickHouse 提供了更轻量的 `SimpleAggregateFunction`：

```sql
-- 语法：SimpleAggregateFunction(聚合函数名, 存储类型)
SimpleAggregateFunction(sum, Int64)      -- 直接存累加后的数值
SimpleAggregateFunction(max, UInt32)     -- 直接存最大值
SimpleAggregateFunction(anyLast, String) -- 直接存最后写入的值
SimpleAggregateFunction(argMax, String, DateTime)
```

**与 AggregateFunction 的区别**：

| 维度 | AggregateFunction | SimpleAggregateFunction |
|---|---|---|
| 存储格式 | 二进制序列化状态 | 原始数据类型（可读） |
| 支持的函数 | 所有聚合函数 | 仅 sum/count/min/max/any/anyLast/argMin/argMax |
| 写入方式 | 必须用 `*State` | 可以直接写值 |
| 查询方式 | 必须用 `*Merge` | 直接查询或用 `max()`/`min()` 等 |
| 性能开销 | 有序列化/反序列化 | 无序列化开销 |

**选择原则**：
- 能用 `SimpleAggregateFunction` 的场景（sum/max/min/anyLast），就用它——更简单、更快
- 需要 uniq/avg/quantile 等复杂聚合时，必须用 `AggregateFunction`

### 3.5 AggregatingMergeTree 的建表语法

理解了 AggregateFunction 类型后，建表就很简单了：

```sql
CREATE TABLE [IF NOT EXISTS] [db.]table_name [ON CLUSTER cluster] (
    name1 [type1] [DEFAULT|MATERIALIZED|ALIAS expr1],
    name2 [type2] [DEFAULT|MATERIALIZED|ALIAS expr2],
    ...
) ENGINE = AggregatingMergeTree()
[PARTITION BY expr]
[ORDER BY expr]
[PRIMARY KEY expr]
[SAMPLE BY expr]
[TTL expr]
[SETTINGS name=value, ...]
```

与普通 MergeTree 唯一的不同就是 `ENGINE = AggregatingMergeTree()`，**引擎本身没有任何额外参数**。聚合的逻辑完全由列定义中的 `AggregateFunction` / `SimpleAggregateFunction` 类型来决定。

## 4. 使用方式一：直接建表

### 4.1 基本示例

```sql
-- 创建 AggregatingMergeTree 表
CREATE TABLE agg_demo (
    user_id     String,
    city        String,
    pv          AggregateFunction(sum, UInt64),
    uv_flag     AggregateFunction(uniq, String),
    max_score   SimpleAggregateFunction(max, Float64),
    event_time  DateTime
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (city, user_id)
PRIMARY KEY city;
```

### 4.2 写入数据（必须使用 INSERT SELECT + State）

```sql
-- ✅ 正确方式：使用 INSERT ... SELECT + *State 函数
INSERT INTO agg_demo
SELECT
    'user_001',
    'beijing',
    sumState(toUInt64(1)),        -- pv 加 1
    uniqState('user_001'),        -- uv 记录
    95.5,                         -- SimpleAggregateFunction 直接写值
    '2024-01-15 10:00:00';

INSERT INTO agg_demo
SELECT
    'user_001',
    'beijing',
    sumState(toUInt64(3)),        -- pv 再加 3
    uniqState('user_002'),        -- 另一个 user
    88.0,
    '2024-01-15 11:00:00';

-- ❌ 错误方式：直接 INSERT VALUES 无法构造 AggregateFunction 状态
-- INSERT INTO agg_demo VALUES ('user_001', 'beijing', 1, 'flag', 95.5, now());
-- 这会报错，因为 AggregateFunction 列不能直接接受普通值
```

### 4.3 查询数据（必须使用 `*Merge` 函数）

```sql
-- ✅ 正确方式：使用 *Merge 函数 + GROUP BY
SELECT
    city,
    user_id,
    sumMerge(pv)        AS total_pv,
    uniqMerge(uv_flag)  AS unique_users,
    max(max_score)       AS highest_score  -- SimpleAggregateFunction 直接查
FROM agg_demo
GROUP BY city, user_id;

-- 结果（合并后）：
-- ┌─city────┬─user_id──┬─total_pv─┬─unique_users─┬─highest_score─┐
-- │ beijing │ user_001 │        4 │            2 │          95.5 │
-- └─────────┴──────────┴──────────┴──────────────┴───────────────┘
```

### 4.4 手动触发合并查看效果

```sql
-- 查看合并前的数据（明细形式，每行独立存在）
SELECT city, user_id, sumMerge(pv) AS pv FROM agg_demo GROUP BY city, user_id;

-- 强制合并所有 Part
OPTIMIZE TABLE agg_demo FINAL;

-- 再次查看（合并后，同 Key 的行已经聚合）
SELECT city, user_id, sumMerge(pv) AS pv FROM agg_demo GROUP BY city, user_id;
```

## 5. 使用方式二：聚合物化视图（推荐）

### 5.1 为什么推荐物化视图方式？

直接使用 `AggregatingMergeTree` 建表存在明显不便：
- 写入必须使用 `INSERT SELECT + *State` 语法
- 无法直接 `INSERT VALUES`
- 应用层需要感知聚合函数类型

**物化视图方案** 将复杂性封装在视图层，对应用透明：

```
写入端（应用）          底表（MergeTree）         聚合物化视图
                        存储全量明细               自动预聚合
┌──────────┐     INSERT     ┌────────────┐   trigger    ┌───────────────┐
│  App     │──────────────→ │ base_table │──────────→  │  agg_view     │
│          │                │ (MergeTree)│              │(AggMergeTree) │
└──────────┘                └────────────┘              └───────────────┘
                                                              │
                                                    SELECT + *Merge
                                                              │
                                                              ▼
                                                         查询结果
```

### 5.2 完整示例：网站访问统计

**Step 1：创建底表（存储全量明细）**

```sql
CREATE TABLE visit_detail (
    user_id     String,
    session_id  String,
    page_url    String,
    city        String,
    device      String,
    duration    UInt32,        -- 页面停留时长（秒）
    is_bounce   UInt8,         -- 是否跳出
    visit_time  DateTime
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(visit_time)
ORDER BY (city, visit_time, user_id);
```

**Step 2：创建聚合物化视图**

```sql
CREATE MATERIALIZED VIEW visit_daily_agg
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (city, day, page_url)
PRIMARY KEY (city, day)
AS SELECT
    city,
    toDate(visit_time)                          AS day,
    page_url,
    sumState(duration)                          AS total_duration,
    countState()                                AS visit_count,
    uniqState(user_id)                          AS unique_visitors,
    uniqState(session_id)                       AS unique_sessions,
    avgState(toFloat64(duration))               AS avg_duration,
    SimpleAggregateFunction(max, UInt32)(duration)  -- 注意：物化视图中直接写
        AS max_duration,
    sumState(is_bounce)                         AS bounce_count
FROM visit_detail
GROUP BY city, day, page_url;
```

> **注意**：在物化视图的 SELECT 中，`SimpleAggregateFunction` 列不能使用 `*State` 函数包裹，应直接使用聚合函数或值。

**Step 3：写入明细数据（面向底表）**

```sql
INSERT INTO visit_detail VALUES
('user_001', 'sess_01', '/home',    'beijing',  'mobile', 30,  0, '2024-01-15 10:00:00'),
('user_001', 'sess_01', '/product', 'beijing',  'mobile', 120, 0, '2024-01-15 10:01:00'),
('user_002', 'sess_02', '/home',    'beijing',  'pc',     5,   1, '2024-01-15 10:05:00'),
('user_003', 'sess_03', '/home',    'shanghai', 'pc',     45,  0, '2024-01-15 11:00:00'),
('user_001', 'sess_04', '/home',    'beijing',  'mobile', 60,  0, '2024-01-15 14:00:00');
```

**Step 4：查询预聚合结果（面向物化视图）**

```sql
SELECT
    city,
    day,
    page_url,
    sumMerge(total_duration)  AS total_dur,
    countMerge(visit_count)   AS visits,
    uniqMerge(unique_visitors) AS uv,
    uniqMerge(unique_sessions) AS sessions,
    avgMerge(avg_duration)    AS avg_dur,
    max(max_duration)         AS max_dur
FROM visit_daily_agg
GROUP BY city, day, page_url
ORDER BY city, day, page_url;

-- 预期结果：
-- ┌─city────┬────day────┬─page_url─┬─total_dur─┬─visits─┬─uv─┬─sessions─┬─avg_dur─┬─max_dur─┐
-- │ beijing │ 2024-01-15│ /home    │        95 │      3 │  2 │        3 │    31.7 │      60 │
-- │ beijing │ 2024-01-15│ /product │       120 │      1 │  1 │        1 │   120.0 │     120 │
-- │ shanghai│ 2024-01-15│ /home    │        45 │      1 │  1 │        1 │    45.0 │      45 │
-- └─────────┴───────────┴──────────┴───────────┴────────┴────┴──────────┴─────────┴─────────┘
```

### 5.3 多层聚合（汇总报表）

```sql
-- 基于日聚合数据，进一步汇总为城市级指标
SELECT
    city,
    day,
    sumMerge(total_duration)    AS city_total_dur,
    countMerge(visit_count)     AS city_visits,
    uniqMerge(unique_visitors)  AS city_uv,
    city_total_dur / city_visits AS avg_dur_per_visit,
    city_uv / city_visits       AS visits_per_user
FROM visit_daily_agg
GROUP BY city, day;
```

## 6. 常用聚合函数与 AggregatingMergeTree 的适配

### 6.1 函数速查表

| 聚合函数 | State 写入 | Merge 查询 | 含义 |
|---|---|---|---|
| `sum` | `sumState(val)` | `sumMerge(col)` | 求和 |
| `count` | `countState()` | `countMerge(col)` | 计数 |
| `avg` | `avgState(val)` | `avgMerge(col)` | 平均值 |
| `min` | `minState(val)` | `minMerge(col)` | 最小值 |
| `max` | `maxState(val)` | `maxMerge(col)` | 最大值 |
| `uniq` | `uniqState(val)` | `uniqMerge(col)` | 近似去重计数（HLL） |
| `uniqExact` | `uniqExactState(val)` | `uniqExactMerge(col)` | 精确去重计数 |
| `uniqCombined` | `uniqCombinedState(val)` | `uniqCombinedMerge(col)` | 高精度近似去重 |
| `argMax` | `argMaxState(val, key)` | `argMaxMerge(col)` | 取 key 最大时的 val |
| `argMin` | `argMinState(val, key)` | `argMinMerge(col)` | 取 key 最小时的 val |
| `quantile(0.95)` | `quantileState(0.95)(val)` | `quantileMerge(0.95)(col)` | 分位数 |
| `anyLast` | `anyLastState(val)` | `anyLastMerge(col)` | 最后一个值 |

### 6.2 argMax 的经典用法

获取每个用户最后一次登录的 IP 地址：

```sql
CREATE TABLE user_latest_info (
    user_id  String,
    last_ip  AggregateFunction(argMax, String, DateTime),
    last_device  SimpleAggregateFunction(argMax, String, DateTime)
)
ENGINE = AggregatingMergeTree()
ORDER BY user_id;

-- 写入（每次登录记录 IP 和时间）
INSERT INTO user_latest_info
SELECT 'user_001', argMaxState('192.168.1.1', toDateTime('2024-01-15 10:00:00')),
       argMax('192.168.1.1', toDateTime('2024-01-15 10:00:00'));

INSERT INTO user_latest_info
SELECT 'user_001', argMaxState('10.0.0.1', toDateTime('2024-01-16 09:00:00')),
       argMax('10.0.0.1', toDateTime('2024-01-16 09:00:00'));

-- 查询（自动取时间最大的那条记录的 IP）
SELECT user_id, argMaxMerge(last_ip) AS latest_ip
FROM user_latest_info
GROUP BY user_id;

-- 结果：user_001 → 10.0.0.1（因为 2024-01-16 > 2024-01-15）
```

### 6.3 分位数统计

```sql
-- P50、P95、P99 延迟统计
CREATE TABLE latency_agg (
    service_name String,
    endpoint     String,
    day          Date,
    p50  AggregateFunction(quantile(0.5), Float64),
    p95  AggregateFunction(quantile(0.95), Float64),
    p99  AggregateFunction(quantile(0.99), Float64)
)
ENGINE = AggregatingMergeTree()
ORDER BY (service_name, endpoint, day);
```

## 7. 注意事项与最佳实践

### 7.1 聚合时机

> **关键认知**：`AggregatingMergeTree` 只在 **Part 合并时**才执行聚合，而非写入时。

这意味着：
- 写入后的数据在合并前仍然是明细行
- 不同 Part 中的相同 Key 可能暂时未被聚合
- 查询时**必须**使用 `*Merge` 函数 + `GROUP BY`，以保证正确性

```sql
-- ❌ 错误：直接查询可能看到未聚合的多行
SELECT user_id, sumMerge(pv) FROM agg_table;

-- ✅ 正确：始终使用 GROUP BY
SELECT user_id, sumMerge(pv) FROM agg_table GROUP BY user_id;

-- 如果需要强制查看完全聚合的结果
SELECT user_id, sumMerge(pv) FROM agg_table FINAL GROUP BY user_id;
```

### 7.2 FINAL 关键字的性能代价

```sql
-- FINAL 会在查询时强制合并所有 Part（代价高）
SELECT * FROM agg_table FINAL;

-- 生产环境推荐：不加 FINAL，用 GROUP BY 保证正确性
SELECT key, sumMerge(val) FROM agg_table GROUP BY key;
```

### 7.3 ORDER BY 与 PRIMARY KEY 分离

```sql
-- 推荐：PRIMARY KEY 只保留最常用的过滤维度
CREATE TABLE daily_metrics (
    date        Date,
    service     String,
    metric_name String,
    host        String,
    region      String,
    value_sum   AggregateFunction(sum, Float64),
    value_count AggregateFunction(count),
    value_avg   AggregateFunction(avg, Float64)
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, service, metric_name, host, region)  -- 全维度作为排序键
PRIMARY KEY (date, service, metric_name);              -- 主键只保留高频过滤列
```

> PRIMARY KEY 必须是 ORDER BY 的前缀。

### 7.4 分区策略

```sql
-- 推荐按天/月分区，配合 ORDER BY 中的时间维度
PARTITION BY toYYYYMM(day)   -- 月级分区（适合数据量大）
PARTITION BY toYYYYMMDD(day) -- 天级分区（适合数据量适中，方便 TTL 淘汰）
```

### 7.5 不要混合使用 AggregateFunction 和普通聚合

```sql
-- ❌ 错误：在同一个查询中混用 Merge 和普通聚合
SELECT key, sumMerge(agg_val) + sum(normal_val)  -- 类型不兼容

-- ✅ 正确：分别处理
SELECT key,
    sumMerge(agg_val)   AS agg_sum,
    sum(normal_val)      AS normal_sum
FROM table GROUP BY key;
```

## 8. 生产环境典型场景

### 8.1 用户行为分析平台

```
原始日志 → Kafka → ClickHouse 底表（MergeTree）
                        │
                        ▼
              聚合物化视图（AggregatingMergeTree）
                        │
                ┌───────┴────────┐
                ▼                ▼
        实时仪表盘          离线报表
    (UV/PV/转化率)      (留存/路径分析)
```

### 8.2 监控指标预聚合

```sql
-- 分钟级原始数据 → 小时级聚合 → 天级聚合
-- 实现分层降维，大幅减少查询扫描量

-- Level 1: 原始数据（秒级）
CREATE TABLE metrics_raw (...)
ENGINE = MergeTree() ORDER BY (service, timestamp);

-- Level 2: 小时聚合
CREATE MATERIALIZED VIEW metrics_hourly
ENGINE = AggregatingMergeTree()
ORDER BY (service, hour)
AS SELECT service, toStartOfHour(timestamp) AS hour,
   avgState(cpu_usage) AS cpu_avg,
   maxState(cpu_usage) AS cpu_max,
   quantileState(0.99)(cpu_usage) AS cpu_p99
FROM metrics_raw
GROUP BY service, hour;

-- Level 3: 天聚合（基于小时数据进一步合并）
CREATE MATERIALIZED VIEW metrics_daily
ENGINE = AggregatingMergeTree()
ORDER BY (service, day)
AS SELECT service, toStartOfDay(hour) AS day,
   avgMergeState(cpu_avg) AS cpu_avg,
   maxMergeState(cpu_max) AS cpu_max,
   quantileMergeState(0.99)(cpu_p99) AS cpu_p99
FROM metrics_hourly
GROUP BY service, day;
```

### 8.3 A/B 测试指标计算

```sql
CREATE MATERIALIZED VIEW ab_test_metrics
ENGINE = AggregatingMergeTree()
ORDER BY (experiment_id, variant, day)
AS SELECT
    experiment_id,
    variant,
    toDate(event_time) AS day,
    countState()                    AS impressions,
    uniqState(user_id)              AS unique_users,
    sumState(toUInt64(is_click))   AS clicks,
    sumState(revenue)               AS total_revenue,
    uniqState(order_id)             AS unique_orders
FROM user_events
WHERE experiment_id != ''
GROUP BY experiment_id, variant, day;

-- 查询实验结果
SELECT
    variant,
    uniqMerge(unique_users) AS users,
    sumMerge(clicks) / uniqMerge(unique_users) AS ctr,
    sumMerge(total_revenue) / uniqMerge(unique_users) AS arpu
FROM ab_test_metrics
WHERE experiment_id = 'exp_2024_01'
GROUP BY variant;
```

## 9. SummingMergeTree vs AggregatingMergeTree：如何选择？

| 决策维度 | 选择 SummingMergeTree | 选择 AggregatingMergeTree |
|---|---|---|
| 聚合需求 | 只需 SUM | 需要 UV/AVG/分位数/argMax 等 |
| 实现复杂度 | 低（普通数值列） | 中（需要理解 AggregateFunction） |
| 写入方式 | 直接 INSERT VALUES | INSERT SELECT + *State |
| 查询方式 | 直接查询列值 | 必须 *Merge + GROUP BY |
| 存储效率 | 较高（原始数值） | 略低（二进制状态） |
| 物化视图 | 可选 | 几乎必须 |

**决策公式**：
- 如果 `GROUP BY 条件固定 + 只需 SUM` → `SummingMergeTree`（更简单）
- 如果 `需要 UV、分位数、argMax 等复杂聚合` → `AggregatingMergeTree`

## 总结

| 要点 | 内容 |
|---|---|
| **核心机制** | Part 合并时执行聚合，将多行合并为一行（保留聚合中间状态） |
| **数据类型** | `AggregateFunction`（二进制状态）和 `SimpleAggregateFunction`（原始值） |
| **写入** | 使用 `*State` 函数生成中间状态 |
| **查询** | 使用 `*Merge` 函数 + `GROUP BY` 计算最终结果 |
| **最佳搭配** | 作为聚合物化视图的引擎，底表用 MergeTree |
| **关键约束** | ORDER BY 决定聚合粒度；聚合只在同 Part 内发生 |
| **生产建议** | PRIMARY KEY 与 ORDER BY 分离；始终使用 GROUP BY 查询 |

> 参考：[AggregatingMergeTree 表引擎](https://clickhouse.com/docs/zh/engines/table-engines/mergetree-family/aggregatingmergetree)
