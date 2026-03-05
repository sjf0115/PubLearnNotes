今天我们来剖析一道经典题目：**给定一张店铺GMV汇总表，找出所有GMV超过整体中位数的店铺**。这道题看似简单，但涉及窗口函数、分位数计算、边界条件处理等多个知识点，能很好地反映对 SQL 的掌握程度。

## 1. 问题描述

假设有一张店铺 GMV 汇总表 `dws_online_shop_ms`，包含两个字段：
- `shopid`：店铺ID（主键）
- `gmv`：成交总额（数值类型）

**需求**：查询所有 `gmv` 大于所有店铺 GMV 中位数的店铺以及对应的 GMV。

示例数据如下：

| shopid | gmv |
|--------|-----|
| 001    | 10  |
| 002    | 50  |
| 003    | 40  |
| 004    | 30  |

## 2. 理解中位数

中位数（Median）是统计学中的常用概念，它将数据集一分为二，一半的数据小于等于中位数，另一半大于等于中位数。计算方式取决于数据个数的奇偶性：
- 奇数个数据：中位数 = 排序后中间位置的值
- 偶数个数据：中位数 = 中间两个值的平均值

先来手动计算中位数。将 GMV 排序：10, 30, 40, 50。共有4个数（偶数），中位数则取中间两个数的平均值：(30 + 40) / 2 = 35。因此，GMV大于35的店铺为002（50）和003（40）。预期结果：

| shopid | gmv |
|--------|-----|
| 002    | 50  |
| 003    | 40  |

---

## 3. 实现方案

接下来，我们将用三种方法在 Hive 中实现这一需求。

### 3.1 方案一：利用 Hive 内置百分位数函数（最简单）

Hive 提供了两个强大的百分位数函数：
- `percentile(col, p)`：适用于整数列，返回精确的第 p 百分位数（p介于0~1）。
- `percentile_approx(col, p, B)`：适用于浮点列，返回近似第 p 百分位数，参数 B 控制近似精度（默认10000）。

对于中位数，p=0.5。因为 GMV 可能是整数或浮点，我们可以用 `percentile_approx`。

#### 3.1.1 思路

1. 计算所有GMV的中位数。
2. 筛选出GMV大于该中位数的店铺。

#### 3.1.2 SQL实现
```sql
WITH median AS (
    SELECT percentile_approx(gmv, 0.5) AS median_gmv
    FROM dws_online_shop_ms
)
SELECT shopid, gmv
FROM dws_online_shop_ms
WHERE gmv > (SELECT median_gmv FROM median);
```

#### 3.1.3 优点
- 代码简洁，易于理解。
- 对于大数据量，`percentile_approx` 采用近似算法，性能较好。

#### 3.1.4 缺点
- 依赖Hive内置函数，如果面试官希望考察纯SQL逻辑，可能不是首选。
- 近似算法在精度要求极高时需谨慎。

---

### 方案二：窗口函数+精确计算（经典面试答案）

如果不借助内置百分位数函数，我们可以用窗口函数和聚合函数手工计算中位数。核心思路：先对GMV排序，然后根据总行数的奇偶性确定中位数位置，最后取对应行的值（或平均值）。

### 步骤分解
1. 使用 `ROW_NUMBER()` 对GMV升序排序，并获取总行数。
2. 确定中位数位置：
   - 若总行数为奇数，中位数为第 `(cnt+1)/2` 行的值。
   - 若总行数为偶数，中位数为第 `cnt/2` 行和第 `cnt/2+1` 行的平均值。
3. 用条件聚合或过滤得到中位数。
4. 筛选大于中位数的记录。

### SQL实现（Hive兼容）
```sql
WITH sorted AS (
    SELECT
        shopid,
        gmv,
        ROW_NUMBER() OVER (ORDER BY gmv) AS rn,
        COUNT(*) OVER () AS total_cnt
    FROM dws_online_shop_ms
),
median_pos AS (
    SELECT
        -- 偶数时取两个位置，奇数时两个位置相同
        FLOOR((total_cnt + 1) / 2.0) AS pos1,
        CEIL((total_cnt + 1) / 2.0) AS pos2
    FROM sorted
    LIMIT 1
),
median_value AS (
    SELECT AVG(gmv) AS median_gmv
    FROM sorted
    WHERE rn IN (SELECT pos1 FROM median_pos UNION ALL SELECT pos2 FROM median_pos)
)
SELECT shopid, gmv
FROM dws_online_shop_ms
WHERE gmv > (SELECT median_gmv FROM median_value);
```

```sql
--step2:利用向下和向上取整函数FLOOR()、CEIL()，找到中位数位置后对值做平均：求中位数值
SELECT  AVG(order_gmv) AS median_gmv
FROM
(--step1:对order_gmv列从小到大进行排列，并计算Y用户数
 SELECT  user_id
        ,order_gmv
        ,ROW_NUMBER() OVER (ORDER BY  order_gmv) AS rn
        ,COUNT(1) OVER()                         AS total_cnt
 FROM usr_order
)t
WHERE rn IN (FLOOR(total_cnt / 2) + 1, CEIL(total_cnt / 2) + 1); 
```


### 注意点
- Hive中 `FLOOR` 和 `CEIL` 函数可用，注意除法保留小数。
- 偶数时两个位置可能相同（如果总行数为奇数，`pos1` 和 `pos2` 相等），用 `IN` 后 `AVG` 自动处理为单值。
- 该写法完全基于标准SQL，移植性好。

### 性能分析
- 需要一次全表扫描和一次排序（窗口函数），比内置函数开销大，但逻辑清晰。


## 三种方法对比

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 内置百分位数函数 | 简洁、高效、易读 | 依赖Hive特有函数，近似算法可能不精确 | 大数据量，对精度要求不极端 |
| 窗口函数+聚合 | 精确、标准SQL、可移植 | 代码稍长，需两次扫描 | 中小数据量，要求精确结果 |
| 自连接 | 理论可解 | 性能极差，无法扩展 | 仅用于学习原理 |

---

## 总结

回到原题，根据示例数据，我们得到的结果是002和003。实际应用中，应根据数据规模、精度要求和开发规范选择合适的方法。

- 如果追求代码简洁且数据量极大，优先使用 `percentile_approx`。
- 如果需要精确中位数且数据量适中，推荐窗口函数法。
- 面试中，如果能完整写出窗口函数解法，并对比内置函数的优劣，通常就能拿到高分。

最后，无论使用哪种方法，都要牢记：**中位数的定义需与业务方确认**（偶数时取平均还是任取一个？），避免因理解偏差导致数据错误。

希望这篇博文能帮助你彻底掌握Hive中中位数的计算技巧。如果你有更好的解法或疑问，欢迎在评论区留言讨论！


https://mp.weixin.qq.com/s/xaW0g7RYfBr_Fr4c6I1t0w
