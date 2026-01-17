在传统的关系型数据库和许多 OLAP 系统中，主键（Primary Key）是一个基本且核心的概念，它通常用于唯一标识表中的记录、确保数据完整性，并作为查询优化的重要依据。然而，当进入 ClickHouse 的世界，你会发现这里的主键有着截然不同的哲学和实现方式。作为一款为极致性能而生的列式数据库，ClickHouse 重新定义了"主键"在分析型场景下的意义和作用。

## 1. 传统 OLTP 数据库中的主键：约束与索引的双重角色

### 1.1 传统主键的核心特性

这里以 Postgres 作为示例，但这些通用概念同样适用于其他 OLTP 数据库。Postgres 的主键按照定义对每一行都是唯一的。借助 B-Tree 结构，可以高效地通过此键查找单行记录。虽然 ClickHouse 也可以针对单行值查找进行优化，但分析型工作负载通常需要在大量行上读取少量列。筛选条件更常见的需求是识别要执行聚合操作的行子集。

![](https://clickhouse.com/docs/zh/assets/images/postgres-b-tree-3b0b52f896ea0d780545383763658dcf.png)

在大多数数据库系统中（包括传统OLAP），主键通常具备以下特性：

```sql
-- 典型的传统OLTP主键定义
CREATE TABLE traditional_oltp_table (
    id BIGINT PRIMARY KEY,          -- 唯一标识符
    user_id INT NOT NULL,
    event_time DATETIME,
    value DECIMAL(10,2),
    UNIQUE INDEX idx_user_time (user_id, event_time)  -- 辅助索引
);
```

**关键特征：**
- **唯一性保证**：严格防止重复记录
- **非空约束**：主键列不允许 NULL 值
- **聚集索引**：在许多系统中，主键决定物理存储顺序
- **外键关联**：作为关系连接的基础

### 1.2 实现机制与代价

```sql
-- 数据插入时的约束检查
INSERT INTO traditional_olap_table VALUES
(1, 1001, '2024-01-01 10:00:00', 150.00),
(1, 1001, '2024-01-01 10:00:00', 150.00); -- 这里会失败！主键冲突

-- 查询优化器重度依赖主键
SELECT * FROM traditional_olap_table WHERE id = 123; -- 极快的点查询
```

**性能影响：**
- 插入时的唯一性检查带来开销
- 主键索引占用额外存储空间
- 更新操作可能引起索引重组

## 2. ClickHouse 主键：为分析而生的稀疏索引

### 2.1 ClickHouse 主键的本质

对于广泛使用的 ClickHouse 来说，内存和磁盘效率至关重要。数据以名为 part 的数据块形式写入 ClickHouse 表，并在后台根据一定规则对这些 part 进行合并。在 ClickHouse 中，每个 part 都有自己的主索引。当 part 被合并时，合并后 part 的主索引也会一并合并。与 Postgres 不同，这些索引并不是为每一行构建的。相反，一个 part 的主索引只为一组行维护一个索引项---这种技术称为稀疏索引（sparse indexing）。

之所以可以使用稀疏索引，是因为 ClickHouse 会根据指定的键，对某个 part 中的行在磁盘上的存储顺序进行排序。稀疏主索引并不像基于 B-Tree 索引那样直接定位单行记录，而是通过对索引项进行二分查找，快速定位可能与查询匹配的成组行。随后，这些被定位到的潜在匹配行集合会并行地流入 ClickHouse 引擎，以找到真正匹配的记录。这种索引设计使得主索引可以非常小（可完全常驻主内存），同时仍能显著加速查询执行时间，尤其是数据分析场景中常见的范围查询。


ClickHouse 的主键更像是一个"排序键+稀疏索引"的组合，而非传统意义上的约束机制：

```sql
-- ClickHouse的主键定义
CREATE TABLE clickhouse_table (
    event_date Date,
    user_id UInt64,
    event_time DateTime,
    value Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id, event_time)  -- 这就是"主键"！
PRIMARY KEY (event_date, user_id);          -- 可选的额外定义

-- 注意：以下插入不会失败，即使数据看似"重复"
INSERT INTO clickhouse_table VALUES
('2024-01-01', 1001, '2024-01-01 10:00:00', 150.00),
('2024-01-01', 1001, '2024-01-01 10:00:00', 150.00); -- 成功插入！
```

### 2.2 ClickHouse 主键的关键特性

**1. 不保证唯一性**
```sql
-- ClickHouse 不会阻止重复数据
SELECT count()
FROM clickhouse_table
WHERE event_date = '2024-01-01'
  AND user_id = 1001
  AND event_time = '2024-01-01 10:00:00';
-- 可能返回2，虽然看似是相同的"主键"
```

**2. 决定数据物理排序**
```sql
-- 数据在磁盘上按ORDER BY排序存储
-- 这对于范围查询极为重要
SELECT * FROM clickhouse_table
WHERE event_date = '2024-01-01'
  AND user_id BETWEEN 1000 AND 2000
ORDER BY user_id, event_time; -- 可以利用已排序的数据
```

**3. 稀疏索引机制**
```sql
-- ClickHouse为每8192行（index_granularity）创建一个索引标记
-- 这意味着索引非常紧凑，但可能需要在数据块内扫描
CREATE TABLE sparse_index_demo (
    timestamp DateTime,
    metric String,
    value Float64
) ENGINE = MergeTree()
ORDER BY (toStartOfHour(timestamp), metric)
SETTINGS index_granularity = 8192;
```

## 3. 核心差异对比

### 3.1 设计哲学差异

| 特性 | 传统OLTP主键 | ClickHouse主键 |
|------|-------------|----------------|
| **唯一性** | 强制保证，插入时检查 | 不保证，允许重复 |
| **空值处理** | 禁止NULL值 | 允许NULL值 |
| **主要目的** | 数据完整性，关系建立 | 查询优化，数据排序 |
| **索引类型** | 通常为稠密索引 | 稀疏索引 |
| **存储开销** | 索引与数据分离，占用额外空间 | 索引极小，通常<1%的数据大小 |
| **更新代价** | 索引维护成本高 | 更适合批量追加，更新成本高 |

### 3.2 性能影响差异

```sql
-- 传统OLAP：主键用于快速点查询
-- 查询单个ID，毫秒级响应
SELECT * FROM orders WHERE order_id = 123456;

-- ClickHouse：主键用于高效范围扫描
-- 查询某个时间段的用户行为，亚秒级响应
SELECT
    user_id,
    count() as events,
    sum(value) as total_value
FROM user_events
WHERE event_date >= '2024-01-01'
  AND event_date <= '2024-01-31'
  AND user_id IN (1001, 1002, 1003)
GROUP BY user_id;
```

## 4. ClickHouse主键最佳实践

### 4.1 主键设计原则

```sql
-- 良好实践：将高基数列放在主键末尾
CREATE TABLE good_practice (
    event_date Date,
    tenant_id UInt32,      -- 中低基数
    metric_type String,    -- 中等基数
    device_id UInt64,      -- 高基数，放最后
    value Float64
) ENGINE = MergeTree()
ORDER BY (event_date, tenant_id, metric_type, device_id)
PARTITION BY toYYYYMM(event_date);

-- 不良实践：高基数列在前会导致索引效率低下
CREATE TABLE bad_practice (
    user_id UInt64,        -- 高基数在前，错误！
    event_date Date,
    event_type String
) ENGINE = MergeTree()
ORDER BY (user_id, event_date); -- 每个用户的数据分散存储
```

### 4.2 主键与分区键的协同

```sql
-- 分区键和主键的合理搭配
CREATE TABLE optimized_table (
    event_time DateTime,
    region_id UInt16,
    user_id UInt64,
    payload String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)           -- 按月份分区
ORDER BY (region_id, toStartOfDay(event_time), user_id)
PRIMARY KEY (region_id, toStartOfDay(event_time));

-- 查询可以利用分区剪枝和主键索引
SELECT count(DISTINCT user_id)
FROM optimized_table
WHERE event_time >= '2024-01-01'
  AND event_time < '2024-02-01'
  AND region_id = 10;  -- 可以快速定位分区和主键范围
```

## 5. 高级模式与技巧

### 5.1 去重表引擎

```sql
-- 如果需要传统主键的唯一性，可以使用ReplacingMergeTree
CREATE TABLE unique_events (
    event_id UUID,
    user_id UInt64,
    event_time DateTime,
    status String
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_id);  -- event_id作为排序键，保证最终一致性去重

-- 注意：去重是异步进行的！
SELECT * FROM unique_events
WHERE event_id = '12345678-1234-1234-1234-123456789abc'
FINAL;  -- 使用FINAL确保获取最终去重后的数据
```

### 5.2 复合主键策略

```sql
-- 针对不同查询模式优化
CREATE TABLE multi_pattern_table (
    date Date,
    hour DateTime,
    tenant_id UInt32,
    event_type Enum8('click'=1, 'view'=2, 'purchase'=3),
    user_id UInt64,
    amount Decimal(10,2)
) ENGINE = MergeTree()
ORDER BY (date, tenant_id, event_type, user_id)
-- 支持多种高效查询模式：
-- 1. 按日期和租户查询
-- 2. 按日期、租户和事件类型查询
-- 3. 按具体用户查询（user_id在末尾，但数据局部性好）

-- 创建物化视图支持其他查询模式
CREATE MATERIALIZED VIEW user_event_view
ENGINE = MergeTree()
ORDER BY (user_id, date)
AS SELECT * FROM multi_pattern_table;
```

## 结论与建议

ClickHouse的主键设计颠覆了传统数据库的认知，这种设计是其实现极致分析性能的关键之一。理解这种差异对于有效使用ClickHouse至关重要：

1. **思维转变**：从"约束工具"转变为"查询优化工具"
2. **设计原则**：基于实际查询模式设计主键，而非数据完整性
3. **接受非唯一性**：在应用层处理去重，或使用特定表引擎
4. **利用稀疏索引**：设计主键时考虑索引粒度的影响
5. **分区与主键协同**：结合分区策略实现多层数据剪枝

在实践中，成功的ClickHouse主键设计往往需要：
- 深入分析查询模式
- 理解数据分布特征
- 权衡存储效率与查询性能
- 接受最终一致性的哲学

记住，在ClickHouse的世界里，没有"一刀切"的主键设计。最好的主键永远是最匹配你具体查询需求的那个设计。
