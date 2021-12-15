---
layout: post
author: sjf0115
title: Hive SORT BY vs ORDER BY vs DISTRIBUTE BY vs CLUSTER BY
date: 2021-12-15 21:56:01
tags:
  - Hive

categories: Hive
permalink: hive-sort-by-order-distribute-cluster
---

在这篇文章中，我们主要来了解一下 SORT BY，ORDER BY，DISTRIBUTE BY 和 CLUSTER BY 在 Hive 中的表现。

首先准备一下测试数据：
```sql
CREATE TABLE IF NOT EXISTS tmp_sport_user_step_1d(
  dt STRING COMMENT 'dt',
  uid STRING COMMENT 'uid',
  step INT COMMENT 'sport step'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';

INSERT INTO TABLE tmp_sport_user_step_1d (dt, uid, step) VALUES
    ('20211123', 'a1', 100),
    ('20211123', 'a2', 200),
    ('20211123', 'a3', 300),
    ('20211123', 'a4', 400),
    ('20211123', 'a5', 500),
    ('20211123', 'a6', 600),
    ('20211123', 'a7', 700),
    ('20211123', 'a8', 800),
    ('20211123', 'a9', 900),
    ('20211124', 'a1', 900),
    ('20211124', 'a2', 800),
    ('20211124', 'a3', 700),
    ('20211124', 'a4', 600),
    ('20211124', 'a5', 500),
    ('20211124', 'a6', 400),
    ('20211124', 'a7', 300),
    ('20211124', 'a8', 200),
    ('20211124', 'a9', 100);
```

### 1. Order By

在 Hive 中，ORDER BY 保证数据的全局有序，为此将所有的数据发送到一个 Reducer 中。因为只有一个 Reducer，所以当输入规模较大时，需要较长的计算时间。Hive 中的 ORDER BY 语法与 SQL 中 ORDER BY 的语法相似，按照某一项或者几项排序输出，可以指定是升序或者是降序排序：
```sql
SELECT uid, step
FROM tmp_sport_user_step_1d
ORDER BY step DESC;
```
运行结果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-1.png?raw=true)

ORDER BY 子句有一些限制：
在严格模式下，即 hive.mapred.mode = strict，ORDER BY 子句后面必须跟一个 LIMIT 子句。如果将 hive.mapred.mode 设置为 nonstrict，可以不用 LIMIT 子句。原因是为了实现所有数据的全局有序，只能使用一个 reducer 来对最终输出进行排序。如果输出中的行数太大，单个 Reducer 可能需要很长时间才能完成。如果在严格模式不指定 LIMIT 子句，会报如下错误：
```
hive> set hive.mapred.mode=strict;
hive> select * from adv_push_click order by click_time;
FAILED: SemanticException 1:47 order by-s without limit are disabled for safety reasons.
If you know what you are doing, please make sure that hive.strict.checks.large.query is set to false
and that hive.mapred.mode is not set to 'strict' to enable them.. Error encountered near token 'click_time'
```
> hive.mapred.mode 在 Hive 0.3.0 版本加入，默认值如下:
- Hive 0.x: nonstrict
- Hive 1.x: nonstrict
- Hive 2.x: strict (HIVE-12413)

请注意，列是按名称指定的，而不是按位置编号指定的。在 Hive 0.11.0 以及更高版本中，实现如下配置时，可以按位置指定列：
- 对于 Hive 0.11.0 到 2.1.x，将 hive.groupby.orderby.position.alias 设置为 true（默认值为false）。
- 对于 Hive 2.2.0 以及更高版本，hive.orderby.position.alias 默认为 true。

### 2. Sort By

如果输出中的行数太多，单个 Reducer 可能需要很长时间才能完成。Hive 增加了一个可供选择的方式，也就是 SORT BY，只会在每个 Reducer 中对数据进行排序，也就是执行一个局部排序。这可以保证每个 Reducer 的输出数据是有序的（但全局并不有序）。这样可以提高后面进行的全局排序的效率。

SORT BY 语法与 ORDER BY 语法类似，区别仅仅是，一个关键字是 ORDER，另一个关键字是 SORT。用户可以指定任意字段进行排序，并可以在字段后面加上 ASC 关键字（默认的），表示按升序排序，或加 DESC 关键字，表示按降序排序：
```sql
SET mapreduce.job.reduces = 3;
SELECT uid, step
FROM tmp_sport_user_step_1d
SORT BY step;
```
> 排序顺序将取决于列类型，如果该列是数字类型的，则排序顺序也是数字顺序；如果该列是字符串类型，那么排序顺序是字典顺序。

如上所示，我们设置了三个 Reducer，根据运动步数 step 进行 SORT BY（如果只有 1 个 Reducer，作用与 ORDER BY 一样实现全局排序）。运行结果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-2.png?raw=true)

从上面输出中可以看到整体输出是无序的，无法判断单个 Reducer 内是否有序，为此我们将数据输出到文件中：
```sql
SET mapreduce.job.reduces = 3;
INSERT OVERWRITE DIRECTORY '/user/hadoop/temp/study/tmp_sport_user_step_1d_sort_by'
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
SELECT uid, step
FROM tmp_sport_user_step_1d
SORT BY step;
```
因为我们设置了三个 Reducer，因此会有三个文件输出：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-3.png?raw=true)

从上面可以看到每个 Reducer 的输出是有序的，但是全局并没有序。

### 3. Distribute By

Distribute By 可以控制 Map 端如何分发数据给 Reduce 端，类似于 MapReduce 中分区 partationer 对数据进行分区。Hive 会根据 Distribute By 后面的列，将数据分发给对应的 Reducer。默认情况下，MapReduce 计算框架会依据 Map 输入的键计算相应的哈希值，然后按照得到的哈希值将键-值对均匀分发到多个 Reducer 中去。如下所示，我们设置了三个 Reducer，根据日期 dt 进行 DISTRIBUTE BY：
```sql
SET mapreduce.job.reduces = 3;
SELECT dt, uid, step
FROM tmp_sport_user_step_1d
DISTRIBUTE BY dt;
```
运行结果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-4.png?raw=true)

从上面输出中我们无法判断相同日期的数据是否分发到同一个 Reducer 内，为此我们将数据输出到文件中：
```sql
SET mapreduce.job.reduces = 3;
INSERT OVERWRITE DIRECTORY '/user/hadoop/temp/study/tmp_sport_user_step_1d_distribute_by'
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
SELECT dt, uid, step
FROM tmp_sport_user_step_1d
DISTRIBUTE BY dt;
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-5.png?raw=true)

从上面可以看到相同日期的数据分发到同一个 Reducer 内。那我们如何实现相同日期内的数据按照运动步数 step 降序排序呢？如下所示根据日期 dt 进行 DISTRIBUTE BY，运动步数 step 进行 SORT BY：
```sql
SET mapreduce.job.reduces = 3;
SELECT dt, uid, step
FROM tmp_sport_user_step_1d
DISTRIBUTE BY dt SORT BY step DESC;
```
运行结果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-6.png?raw=true)

我们还是将数据输出到文件中，来查看数据是如何分布的：
```sql
SET mapreduce.job.reduces = 3;
INSERT OVERWRITE DIRECTORY '/user/hadoop/temp/study/tmp_sport_user_step_1d_distribute_by_sort_by'
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
SELECT dt, uid, step
FROM tmp_sport_user_step_1d
DISTRIBUTE BY dt SORT BY step DESC;
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-7.png?raw=true)

从上面可以看到相同日期的数据分发到同一个 Reducer 内，并按照运动步数 step 降序排序。

### 4. Cluster By

在前面的例子中，dt 列被用在了 DISTRIBUTE BY 语句中，而 step 列位于 SORT BY 语句中。如果这 2 个语句中涉及到的列完全相同，而且采用的是升序排序方式（也就是默认的排序方式），那么在这种情况下，CLUSTER BY 就等价于前面的 2 个语句，相当于是前面 2 个句子的一个简写方式。如下所示，我们只对 step 字段使用 CLUSTER BY 语句：
```sql
SET mapreduce.job.reduces = 3;
SELECT dt, uid, step
FROM tmp_sport_user_step_1d
CLUSTER BY step;
```
运行结果如下所示：

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-8.png?raw=true)

我们还是将数据输出到文件中，来查看数据是如何分布的：
```sql
SET mapreduce.job.reduces = 3;
INSERT OVERWRITE DIRECTORY '/user/hadoop/temp/study/tmp_sport_user_step_1d_cluster_by'
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
SELECT dt, uid, step
FROM tmp_sport_user_step_1d
CLUSTER BY step;
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Hive/hive-sort-by-order-distribute-cluster-9.png?raw=true)

从上面可以看到相同运动步数 step 的数据分发到同一个 Reducer 内，并按照其升序排序。

> 使用 DISTRIBUTE BY ... SORT BY 语句或其简化版的 CLUSTER BY 语句会剥夺 SORT BY 的并行性，然而这样可以实现输出文件的数据是全局排序的。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- https://cwiki.apache.org/confluence/display/Hive/LanguageManual+SortBy#LanguageManualSortBy-SyntaxofOrderBy
- 《Hive 编程指南》
