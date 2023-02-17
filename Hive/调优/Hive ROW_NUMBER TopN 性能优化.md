## 1. 背景

假设我们要查看每个频道下第一次出现的用户，常用解决方案会使用 `row_number`：
```sql
SELECT cid, cname, uid, server_tm
FROM (
    SELECT
        cid, cname, uid, server_tm,
        ROW_NUMBER() OVER(PARTITION BY cid ORDER BY server_tm) AS rk
    FROM behavior
    WHERE dt = '20230216'
) AS a
WHERE rk = 1;
```

`row_number` 会按照频道ID `cid` 进行分组，并在每个分组内根据时间进行排序。如果某一个或者某几个频道有大量的用户访问，那么就会极易发生数据倾斜。那么怎么才能避免数据倾斜快速实现 TopN 呢？

## 2. 优化

当发生数据倾斜时，可以通用以下几种方式解决：

| 序号 | 方案 | 说明 |
| -------- | -------- | -------- |
| 方案一  | SQL写法的两阶段聚合 | 增加随机列或拼接随机数，将其作为分区（Partition）中一参数 |
| 方案二  | UDAF写法的两阶段聚合 | 最小堆的队列优先的通过UDAF的方式进行调优 |

### 2.1 SQL 写法的两阶段聚合

为使 Map 阶段中 Partition 各分组数据尽可能均匀，增加随机列，将其作为 Partition 中一参数。可以理解为将频道分为 N 个分组，先在 N 个分组中取 TopN，然后在全局取 TopN：
```sql
SELECT cid, cname, uid, server_tm
FROM (
    -- 每个频道的 Top1
    SELECT
        cid, cname, uid, server_tm,
        ROW_NUMBER() OVER(PARTITION BY cid ORDER BY server_tm) AS rk
    FROM (
        -- 每个频道在不同分组中的 Top1
        SELECT
            cid, cname, uid, server_tm,
            ROW_NUMBER() OVER(PARTITION BY cid, random ORDER BY server_tm) AS rk
        FROM (
            -- 添加随机数 分组
            SELECT
                cid, cname, uid, server_tm,
                CEIL(110 * RAND()) % 15 AS random
            FROM behavior
            WHERE dt = '20230216'
        ) AS a
    ) AS b
    WHERE rk = 1
) AS c
WHERE rk = 1;
```

### 2.2 UDAF 写法的两阶段聚合

SQL 的方式会有较多代码，且可能不利于维护，可以利用最小堆的队列优先的通过 UDAF 的方式进行调优，即在 iterate 阶段仅取 TopN，merge 阶段则均仅对 N 个元素融合，过程如下：
- iterate：将前K个元素进行push，K之后的元素通过不断与最小顶比较交换堆中元素。
- merge：将两堆merge后，原地返回前K个元素。
- terminate：数组形式返回堆。
- SQL中将数组拆为各行。
