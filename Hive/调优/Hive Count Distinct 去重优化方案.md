
## 1. 问题

假设用户行为表数据分布如下：

| 类型 | 记录数 |
| :------------- | :------------- |
| 0  | 46亿 |
| 1  | 1600万 |
| 2  | 2.5亿 |
| 3  | 98万 |

假设要使用如下语句计算每种类型访问的用户数就很容易发生数据倾斜：
```sql
SELECT type, COUNT(DISTINCT uid) AS uv
FROM behavior
WHERE dt = '20230216'
GROUP BY type;
```

## 2. 解决方案

解决方案如下：

| 序号 | 方案 | 说明 |
| :------------- | :------------- | :------------- |
| 方案一 | 两阶段聚合 | 先对 GoupBy 字段(type)和 DISTINCT 字段(uid)进行 GroupBy，再使用 COUNT |
| 方案二 | 参数设置调优 | `SET hive.groupby.skewindata=true` |
| 方案三 | 两阶段聚合+随机数 | 通用两阶段聚合在 partition 字段值拼接随机数 |

### 2.1 方案一:两阶段聚合

首先在第一层对 GoupBy 字段(type)和 DISTINCT 字段(uid)进行 GroupBy，然后在第二层直接 COUNT 计算即可：
```sql
-- 第二层 COUNT
SELECT type, COUNT(uid) AS uv
FROM (
    -- 第一层 GroupBy
    SELECT type, uid
    FROM behavior
    WHERE dt = '20230216'
    GROUP BY type, uid
) AS a
GROUP BY type;
```
### 2.2 方案二:参数设置调优

```sql
`SET hive.groupby.skewindata=true`
```

### 2.3 方案三:两阶段聚合+随机数

若 uid 字段数据不均匀，则无法通过方案一和方案二进行优化，较通用的方式是在分区（partition）字段值上拼接或者增加随机数：
```sql

```
