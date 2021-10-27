本文介绍了用于窗口函数和分析函数的Hive QL增强功能。所有窗口和分析函数操作都按照SQL标准。当前版本支持以下窗口函数和分析函数。

### 1 窗口函数

窗口函数 | 描述
---|---
LAG() | LAG()窗口函数返回分区中当前行之前行（可以指定第几行）的值。 如果没有行，则返回null。
LEAD() | LEAD()窗口函数返回分区中当前行后面行（可以指定第几行）的值。 如果没有行，则返回null。
FIRST_VALUE | FIRST_VALUE窗口函数返回相对于窗口中第一行的指定列的值。
LAST_VALUE | LAST_VALUE窗口函数返回相对于窗口中最后一行的指定列的值。

### 2 OVER子句

OVER子句可以与标准聚合函数使用(COUNT，SUM，MIN，MAX，AVG)。

OVER可以与一个或多个任何原始数据类型的分区列的PARTITION BY语句使用。

OVER可以与一个或多个任何原始类型的分区列（排序列）的PARTITION BY(ORDER BY)使用。

带有窗口规范的OVER子句。窗口可以在WINDOW子句中单独定义。 窗口规范支持如下格式：
```
(ROWS | RANGE) BETWEEN (UNBOUNDED | [num]) PRECEDING AND ([num] PRECEDING | CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN CURRENT ROW AND (CURRENT ROW | (UNBOUNDED | [num]) FOLLOWING)
(ROWS | RANGE) BETWEEN [num] FOLLOWING AND (UNBOUNDED | [num]) FOLLOWING
```
当缺少WINDOW子句并指定使用ORDER BY时，窗口规范默认为RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW，即从第一行到当前行。


当缺少ORDER BY和WINDOW子句时，窗口规范默认为ROW BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING，即第一行到最后一行。

**备注**

PRECEDING ： 表示当前行之前的行

UNBOUNDED PRECEDING ： 表示当前行之前无边界行，即第一行

num PRECEDING ： 表示当前行之前第num行

CURRENT ROW ： 表示当前行

FOLLOWING ： 表示当前行后面的行

UNBOUNDED FOLLOWING ： 表示当前行后面无边界行，即最后一行

num FOLLOWING : 表示当前行后面第num行


### 3 分析函数

分析函数 | 描述
---|---
RANK | 返回数据项在分区中的排名。排名值序列可能会有间隔
DENSE_RANK | 返回数据项在分区中的排名。排名值序列是连续的，不会有间隔
PERCENT_RANK | 计算当前行的百分比排名
ROW_NUMBER | 确定分区中当前行的序号
CUME_DIST | 计算分区中当前行的相对排名
NTILE() | 将每个分区的行尽可能均匀地划分为指定数量的分组

### 4 Distinct （Hive 2.1.0以后版本支持）

Distinct 支持包括SUM，COUNT和AVG的聚合函数，在每个分区不同值上进行聚合（aggregate over the distinct values within each partition）。当前实现具有以下局限性：由于性能原因，在分区子句中不能支持ORDER BY或窗口规范。支持的语法如下：
```
COUNT(DISTINCT a) OVER (PARTITION BY c)
```
在 Hive 2.2.0 后 Distinct可以支持 ORDER BY 和 窗口规范 (see HIVE-13453)。例如：
```
COUNT(DISTINCT a)
OVER (PARTITION BY c ORDER BY d ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING)
```
### 5. OVER子句中支持聚合函数（Hive 2.1.0及以后版本支持）

添加了对在OVER子句中使用聚合函数的支持。 例如，目前我们可以在OVER子句中使用SUM聚合函数，如下所示：
```
SELECT rank() OVER (ORDER BY sum(b))
FROM T
GROUP BY a;
```





```sql
INSERT INTO tmp_over_test_1d VALUES
    ('1001985', '铁流', 1570412317329),
    ('1001985', '铁流', 1570412317330),
    ('1001985', '红军不怕远征难-铁流', 1570412317331),
    ('1001985', '红军不怕远征难-铁流', 1570412317332),
    ('1001986', '', 1570412317330),
    ('1001986', '好梦已花开', 1570412317331),
    ('1001986', '', 1570412317332)
;

SELECT
    item_id,
    FIRST_VALUE(IF(item_name = '', NULL, item_name), TRUE) OVER(PARTITION BY item_id ORDER BY event_ts DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS item_name,
    event_ts
FROM tmp_over_test_1d;

item_id	item_name	event_ts
1001985	红军不怕远征难-铁流	1570412317332
1001985	红军不怕远征难-铁流	1570412317331
1001985	红军不怕远征难-铁流	1570412317330
1001985	红军不怕远征难-铁流	1570412317329
1001986	好梦已花开	1570412317332
1001986	好梦已花开	1570412317331
1001986	好梦已花开	1570412317330
```

All you need to do is to slide over a window between preceedings and current row and find most recent not null value. LAST_VALUE windowable function has an argument to ignore null values as boolean. LAST_VALUE(<field>,<ignore_nulls> as boolean);
