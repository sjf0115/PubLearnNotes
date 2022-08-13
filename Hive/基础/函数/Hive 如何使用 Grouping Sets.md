---
layout: post
author: sjf0115
title: Hive 如何使用 Grouping Sets
date: 2018-07-05 19:16:01
tags:
  - Hive

categories: Hive
permalink: hive-base-grouping-sets
---

> Hive 版本：2.3.4

这篇文章描述了 SELECT 语句 GROUP BY 子句的增强聚合功能 GROUPING SETS。GROUPING SETS 子句是 SELECT 语句的 GROUP BY 子句的扩展。通过 GROUPING SETS 子句，你可采用多种方式对结果分组，而不必使用多个 SELECT 语句来实现这一目的。这就意味着，能够减少响应时间并提高性能。

> 在Hive 0.10.0版本中添加了 Grouping sets，CUBE 和 ROLLUP 运算符以及 GROUPING__ID 函数。参见[HIVE-2397](https://issues.apache.org/jira/browse/HIVE-2397)，[HIVE-3433](https://issues.apache.org/jira/browse/HIVE-3433)，[HIVE-3471](https://issues.apache.org/jira/browse/HIVE-3471)和 [HIVE-3613](https://issues.apache.org/jira/browse/HIVE-3613)。另外在Hive 0.11.0版本进行的优化 [HIVE-3552](https://issues.apache.org/jira/browse/HIVE-3552)。

### 1. GROUPING SETS

GROUP BY 中的 GROUPING SETS 子句允许我们在同一记录集中指定多个 GROUP BY 选项。所有 GROUPING SET 子句都可以逻辑表示为 UNION 连接的几个 GROUP BY 查询。为了帮助我们快速了解 GROUPING SETS 子句的思想，我们看一下如下几个示例。

示例 1：
```sql
SELECT dt, os, SUM(num)
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt, os)
)
```
等价于:
```sql
SELECT dt, os, SUM(num)
FROM a
GROUP BY dt, os
```

示例 2：
```sql
SELECT dt, os, SUM(num)
FROM a GROUP BY dt, os
GROUPING SETS (
  (dt, os), (dt)
)
```
等价于:
```sql
SELECT dt, os, SUM(num)
FROM a
GROUP BY dt, os
UNION
SELECT dt, null, SUM(num)
FROM a
GROUP BY dt
```

示例 3：
```sql
SELECT dt, os, SUM(num)
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt), (os)
)
```
等价于:
```sql
SELECT dt, null, SUM(num)
FROM a
GROUP BY dt
UNION
SELECT null, os, SUM(num)
FROM a
GROUP BY os
```

示例 4：
```sql
SELECT dt, os, SUM(num)
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt, os), (dt), (os), ()
)
```
等价于:
```sql
SELECT dt, os, SUM(num)
FROM a
GROUP BY dt, os
UNION
SELECT dt, null, SUM(num)
FROM a
GROUP BY dt
UNION
SELECT null, os, SUM(num)
FROM a
GROUP BY os
UNION
SELECT null, null, SUM(num)
FROM a
```
> GROUPING SETS 子句中的空白 `()` 计算整体聚合。

### 2. Grouping__ID

GROUPING SETS　会对 GROUP BY 子句中的列进行多维组合，结果整体展现，对于没有参与 GROUP BY 的那一列使用 `NULL` 充当占位符。如果列本身值中也有为 `NULL` 的，那么就无法区分是占位符 NULL 还是数据中真正的 `NULL`。`GROUPING__ID` 函数就是为了解决这个问题而引入的。

此函数返回一个位向量，与每列是否参与计算相对应，用二进制位中的每一位来标示对应列是否参与 GROUP BY。Hive 2.3.0 版本之前，如果某一列参与了 GROUP BY 计算，对应位就被置为 `1`，否则置为 `0`。在这一版本中 GROUPING__ID 与位向量之间的关系比较别扭，GROUPING__ID 实际为位向量先反转之后再转为十进制的值。这一点，在 Hive 2.3.0 版本得到解决，如果某一列参与了 GROUP BY 计算，对应位就被置为 `0`，否则置为 `1`。GROUPING__ID 为位向量转为十进制的值。所以在使用 GROUPING__ID 时注意一下 Hive 版本。

> GROUPING__ID 的值与 GROUP BY 表达式中列的取值和顺序有关，所以如果重新排列，GROUPING__ID 对应的含义也会变化。

具体看一个例子，假设 a 表中的数据如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-base-grouping-sets-1.png?raw=true)

使用如下语句计算日期(dt)和操作系统(os)两个字段的不同组合的结果：
```sql
SELECT
  GROUPING__ID, dt, os, SUM(num) AS num
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt, os), (dt), (os), ()
);
```
如果 Hive 版本小于 2.3.0，输出结果如下：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-base-grouping-sets-2.png?raw=true)

如果 Hive 版本大于 2.3.0，输出结果如下：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-base-grouping-sets-3.png?raw=true)

从上面的输出结果中可以看出虽然都是 NULL，有可能表示的是本身值是 NULL，或者可能表示没有参数 GROUP BY 计算而置为 NULL。虽然从字面上没有办法看出其表示的含义，但是我们可以通过 GROUPING__ID 进行判断。以 Hive 大于 2.3.0 输出为例，蓝色的第一行中 dt 和 os 都是 NULL，但是通过 GROUPING__ID 等于 2（二进制位为 10）判断出 os 参与了 GROUP BY 计算，即 os 的 NULL 是本身值为 NULL，而 dt 的 NULL 是没有参与计算而置为 NULL。

如果希望没有参与 GROUP BY 计算的列不显示 `NULL` 而是显示一个有实际意义的值，例如 `全部`，这样不至于混淆两种含义的 NULL，从而便于理解。如果对于列本身值没有为 `NULL` 的情况，可以使用如下简单方式来实现：
```sql
SELECT
  (CASE WHEN dt IS NULL THEN '全部' ELSE dt END) AS dt,
  (CASE WHEN os IS NULL THEN '全部' ELSE os END) AS os,
  SUM(num) AS num
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt, os), (dt), (os), ()
);
```
如果对于列本身值就有为 `NULL` 的情况，无法使用上述方式来实现，需要使用下面方式实现：
```sql
-- Hive 版本 >= 2.3.0
SELECT
  GROUPING__ID,
  (CASE WHEN (CAST (GROUPING__ID AS INT) & 2) == 0 THEN dt ELSE '全部' END) AS dt,
  (CASE WHEN (CAST (GROUPING__ID AS INT) & 1) == 0 THEN os ELSE '全部' END) AS os,
  SUM(num) AS num
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt, os), (dt), (os), ()
);

-- Hive 版本 < 2.3.0
SELECT
  GROUPING__ID,
  (CASE WHEN (CAST (GROUPING__ID AS INT) & 1) == 0 THEN dt ELSE '全部' END) AS dt,
  (CASE WHEN (CAST (GROUPING__ID AS INT) & 2) == 0 THEN os ELSE '全部' END) AS os,
  SUM(num) AS num
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt, os), (dt), (os), ()
);
```
Hive 版本 >= 2.3.0 输出效果如下：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-base-grouping-sets-4.png?raw=true)

### 3. Grouping

除了 GROUPING__ID 之外，也可以通过 Grouping 函数指明 GROUP BY 子句中的列是否参与 GROUP BY 计算。如果 grouping 值为 0 表示该列参与了 GROUP BY 计算，而值为 1 表示没有参与计算：
```sql
SELECT
  GROUPING__ID,
  grouping(dt) AS grouping_dt, grouping(os) AS grouping_os,
  dt, os,
  SUM(num)
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt, os), (dt), (os), ()
);
```

输出结果如下：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-base-grouping-sets-5.png?raw=true)

> 2.3.4 版本

默认情况，GROUP BY 子句中没有参与计算的列，会被填充为 NULL。我们也可以通过 grouping 输出更有实际意义的值。这种方式要比使用 GROUPING__ID 方式更为简单，如下所示：
```sql
SELECT
  GROUPING__ID,
  grouping(dt) AS grouping_dt, grouping(os) AS grouping_os,
  IF(grouping(dt) == 0, dt, '全部') AS dt,
  IF(grouping(os) == 0, os, '全部') AS os,
  SUM(num) AS num
FROM a
GROUP BY dt, os
GROUPING SETS (
  (dt, os), (dt), (os), ()
);
```

效果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-base-grouping-sets-6.png?raw=true)

> 2.3.4 版本

### 4. CUBE 与 ROLLUP

通用语法是 `WITH CUBE/ROLLUP`。只能 GROUP BY 一起使用。

#### 4.1 CUBE

CUBE 简称数据魔方，可以实现 Hive 多个任意维度的查询。CUBE 创建集合中所有可能组合。例如：
```sql
GROUP BY a, b
WITH CUBE
```
等价于
```sql
GROUP BY a, b
GROUPING SETS（
  (a, b), (a), (b), ()
)  
```

#### 4.2 ROLLUP

ROLLUP 子句与 GROUP BY 一起使用用来计算维度上层次结构级别的聚合。ROLLUP 可以实现从右到左递减多级的统计。

具有 ROLLUP 的 `GROUP BY a，b，c` 假定层次结构为 `a` 向下钻取到(drilling down) `b`，向下钻取到 `c`。例如：
```sql
GROUP BY a，b，c
WITH ROLLUP
```
等价于:
```sql
GROUP BY a，b，c
GROUPING SETS (
  (a，b，c), (a，b), (a), ()
)
```

参考：
- https://stackoverflow.com/questions/29577887/grouping-in-hive
- https://cwiki.apache.org/confluence/display/Hive/Enhanced+Aggregation%2C+Cube%2C+Grouping+and+Rollup
