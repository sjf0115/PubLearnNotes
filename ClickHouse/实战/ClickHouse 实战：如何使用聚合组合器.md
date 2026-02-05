ClickHouse 不仅支持标准聚合函数，还提供了大量更高级的[函数](https://clickhouse.com/docs/sql-reference/aggregate-functions/reference)以满足大多数分析场景的需求。除了聚合函数之外，ClickHouse 还提供了[聚合组合器](https://clickhouse.com/docs/sql-reference/aggregate-functions/combinators)，这是对查询能力的强大扩展，能够应对海量复杂需求。

聚合组合器允许扩展与混合聚合操作，从而适配各种数据结构。这一能力使我们能够通过调整查询而非表结构，来回答即使是最复杂的问题。

在本篇博文中，我们探讨聚合组合器，以及如何用它简化查询并避免对数据结构进行修改。

## 1. 如何使用聚合组合器

要使用聚合组合器，我们需要完成两个步骤。首先，选择所需的聚合函数，例如我们选用 `sum()` 函数；其次，根据实际场景选取合适的组合器，比如我们需要 `If` 组合器。在查询中应用时，只需将组合器放在函数名之后即可：
```sql
SELECT sumIf(...)
```
更有用的特性是，我们甚至可以在一个函数中组合任意数量的组合器：
```sql
SELECT sumArrayIf(...)
```

在这里，我们将 `sum()` 聚合函数与 `Array` 和 `If` 组合器组合在一起：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4RZUuTasRav0syZLA6Mu3g6WIM726eoySONAmnuibc33iaRZnJTEnGKFdmvXtcXsIENZuWL07icjHNZ9g/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

上面这个具体示例让我们能够对满足条件的数组列内容进行求和。

接下来，让我们探索一些可以使用组合器的实际场景。

## 2. 在聚合中的增加条件

我们有时需要根据特定条件对数据进行聚合。我们就可以使用 `If` 组合器，并将条件指定为组合函数的最后一个参数，而不是使用 WHERE 子句：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4RZUuTasRav0syZLA6Mu3g6WWibq4VqhJ0nhJkbzNmYjz7a3N6Wb9EP4C9ZeyVTK4Iiay5sod7veFbdQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=5)

假设我们有一个用户付款表，结构如下（使用[示例](https://gist.github.com/gingerwizard/a24d0057367dbd9b7e4e36e26522a30a)数据填充）：
```sql
CREATE TABLE payments (
    `total_amount` Float,
    `status` ENUM('declined', 'confirmed'),
    `create_time` DateTime,
    `confirm_time` DateTime
)
ENGINE = MergeTree
ORDER BY (status, create_time)
```
假设我们仅想获得确认付款的总金额时，即 `status="confirmed"` 的金额：
```sql
SELECT sumIf(total_amount, status = 'confirmed') FROM payments

┌─sumIf(total_amount, equals(status, 'confirmed'))─┐
│                               12033.219916582108 │
└──────────────────────────────────────────────────┘
```
> 我们可以使用与 WHERE 子句相同的条件语法。

现在我们想获取确认付款的总金额，但仅统计确认时间 confirm_time 晚于创建时间 create_time 晚1分钟的情况：
```sql
SELECT sumIf(total_amount, (status = 'confirmed') AND (confirm_time > (create_time + toIntervalMinute(1)))) AS confirmed_and_checked
FROM payments

┌─confirmed_and_checked─┐
│     11195.98991394043 │
└───────────────────────┘
```
相较于标准的 WHERE 子句，使用 `If` 组合器的主要优势在于能够为不同条件计算多个聚合值。我们还可以将任何可用的聚合函数与组合器结合使用，例如 `countIf()`、`avgIf()` 或 `quantileIf()` 等。结合这些能力，我们可以在单个查询中基于多条件和多函数进行聚合：
```sql
SELECT
    countIf((status = 'confirmed') AND (confirm_time > (create_time + toIntervalMinute(1)))) AS num_confirmed_checked,
    sumIf(total_amount, (status = 'confirmed') AND (confirm_time > (create_time + toIntervalMinute(1)))) AS confirmed_checked_amount,
    countIf(status = 'declined') AS num_declined,
    sumIf(total_amount, status = 'declined') AS dec_amount,
    avgIf(total_amount, status = 'declined') AS dec_average
FROM payments

┌─num_confirmed_checked─┬─confirmed_checked_amount─┬─num_declined─┬────────dec_amount─┬───────dec_average─┐
│                    39 │        11195.98991394043 │           50 │ 10780.18000793457 │ 215.6036001586914 │
└───────────────────────┴──────────────────────────┴──────────────┴───────────────────┴───────────────────┘
```

## 3. 计算唯一值的聚合

计算唯一值的数量是一种常见需求。ClickHouse 提供了多种实现方式：既可以使用 `COUNT(DISTINCT col)`（等同于 `uniqExact`），也可以在接受估算值（速度更快）时使用 `uniq()` 函数。然而，有时我们需要基于同一列的不同聚合函数获取唯一值。这时可以使用 `Distinct` 组合器：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4RZUuTasRav0syZLA6Mu3g6WxQezib4QTBHbLY9Rf4BMfcx6QTLosWsKLZSvpic3HkZFjYuYbgsjLILw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=7)

当我们为聚合函数添加 Distinct 组合器之后会自动忽略重复值：
```sql
SELECT
    countDistinct(toHour(create_time)) AS hours,
    avgDistinct(toHour(create_time)) AS avg_hour,
    avg(toHour(create_time)) AS avg_hour_all
FROM payments

┌─hours─┬─avg_hour─┬─avg_hour_all─┐
│     2 │     13.5 │        13.74 │
└───────┴──────────┴──────────────┘
```
在这里，avg_hour 将基于仅两个唯一值计算，而 avg_hour_all 则基于表中的全部 100 条记录计算。

### 3.1 组合使用 Distinct 与 If

由于组合器可以相互结合，我们可以将前两种组合器结合为 avgDistinctIf 函数，以处理更复杂的逻辑：
```sql
SELECT avgDistinctIf(toHour(create_time), total_amount > 400) AS avg_hour
FROM payments

┌─avg_hour─┐
│       13 │
└──────────┘
```
这将针对 total_amount 值大于 400 的记录，基于不重复的 hour 值计算平均值。

## 4. 在聚合前将数据分组

与最小/最大值分析不同，我们可能希望在聚合之前先将数据分成组，再分别计算各组的指标。这可以通过 `Resample` 组合器实现。该组合器接收一个计算列、范围（开始/结束）和您希望使用的分割数据的步长。然后返回每个组的聚合结果：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4RZUuTasRav0syZLA6Mu3g6WyMNGWoZf1GL8icNicp3iaubZhCuGZhjAC8fjxzyk15NJCBSPaYGPylDoQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=9)

假设我们想根据 `total_amount` 从0（最小值）到 500（最大值）以 100 的步长对 payments 表数据进行分组。然后，我们想知道每个分组中有多少条目以各分组的平均值：
```sql
SELECT
    countResample(0, 500, 100)(toInt16(total_amount)) AS group_entries,
    avgResample(0, 500, 100)(total_amount, toInt16(total_amount)) AS group_totals
FROM payments
FORMAT Vertical

Query id: 8f7f30aa-8efc-4b92-be63-b5fd8e195933

Row 1:
──────
group_entries: [21,20,24,31,4]
group_totals:  [50.21238123802912,157.32600135803222,246.1433334350586,356.2583834740423,415.2425003051758]
```
在这里，`countResample()` 函数计算每个分组中的条目数，`avgResample()` 函数计算每个分组 `total_amount` 的平均值。`Resample` 组合器基于组合函数最后一个参数列进行分组。
请注意，`countResample()` 函数只有一个参数（因为 `count()` 函数根本不需要参数），`avgResample()` 有两个参数（第一个是 `avg()` 函数要计算平均值的列）。最后，由于 `Resample` 组合器需要，我们必须使用 `toInt16` 将 `total_amount` 转换为整数。

为了以表格布局呈现 `Resample()` 组合器的输出，我们可以使用 `arrayZip()` 和 `arrayJoin()` 函数：
```sql
SELECT
    round(tp.2, 2) AS avg_total,
    tp.1 AS entries
FROM
(
    SELECT arrayJoin(arrayZip(countResample(0, 500, 100)(toInt16(total_amount)), avgResample(0, 500, 100)(total_amount, toInt16(total_amount)))) AS tp
    FROM payments
)

Query id: 5364269a-1f13-44c3-8933-988f406ea5fc

┌─avg_total─┬─entries─┐
│     50.21 │      21 │
│    157.33 │      20 │
│    246.14 │      24 │
│    356.26 │      31 │
│    415.24 │       4 │
└───────────┴─────────┘

5 rows in set. Elapsed: 0.009 sec.
```
在这里，我们将两个数组的相应值组合成元组，并使用 `arrayJoin()` 函数将结果数组展开成表格。

## 5. 控制空结果的聚合值

聚合函数对于结果集为空的情况会表现出不同的行为。例如，`count()` 将返回 0，而 `avg()` 将产生 nan 值。我们可以使用 `OrDefault()` 和 `OrNull()` 组合器来控制此行为。两者都会更改在数据集为空时使用聚合函数的返回值：
- `OrDefault()` 将返回函数的默认值而不是 nan，
- `OrNull()` 将返回 NULL（同时会将返回类型改为 Nullable）。

考虑以下示例：
```sql
SELECT
    count(),
    countOrNull(),
    avg(total_amount),
    avgOrDefault(total_amount),
    sumOrNull(total_amount)
FROM payments
WHERE total_amount > 1000

Query id: b737d73c-63de-443c-bf5f-b4fa97c54e31

┌─count()─┬─countOrNull()─┬─avg(total_amount)─┬─avgOrDefault(total_amount)─┬─sumOrNull(total_amount)─┐
│       0 │          ᴺᵁᴸᴸ │               nan │                          0 │                    ᴺᵁᴸᴸ │
└─────────┴───────────────┴───────────────────┴────────────────────────────┴─────────────────────────┘

1 row in set. Elapsed: 0.007 sec.
```
正如我们在第一列中看到的，没有返回任何行。请注意，`countOrNull()` 将返回 NULL 而不是 0，`avgOrDefault()` 会返回 0 而不是 nan。

### 5.1 与其他组合器一起使用

与所有其他组合器一样，`OrNull()` 和 `OrDefault()` 可以与不同的组合器一起使用以进行更高级的逻辑：
```sql
SELECT
    sumIfOrNull(total_amount, status = 'declined') AS declined,
    countIfDistinctOrNull(total_amount, status = 'confirmed') AS confirmed_distinct
FROM payments
WHERE total_amount > 420

Query id: f10d73bb-0e77-4213-b479-2161f30ec83e

┌─declined─┬─confirmed_distinct─┐
│     ᴺᵁᴸᴸ │                  1 │
└──────────┴────────────────────┘

1 row in set. Elapsed: 0.008 sec.
```
我们使用了 `sumIfOrNull()` 组合函数来仅计算被拒绝的付款，并在空集时返回 NULL。`countIfDistinctOrNull()` 函数计算不同的 total_amount 值，但仅适用于满足指定条件的行。

## 6. 聚合数组

ClickHouse 的 Array 类型深受用户青睐，因为它为表结构带来了很多灵活性。为了有效地操作 Array 列，ClickHouse 提供了一组数组函数。为了简化对 Array 类型的聚合，ClickHouse 提供了 `Array()` 组合器。这些将给定的聚合函数应用于数组列中的所有值，而不是数组本身：

![](https://clickhouse.com/uploads/6_1320d1a6ee.png)

假设我们有以下表格（用[示例数据](https://gist.github.com/gingerwizard/d08ccadbc9e5cf7ef1d392c47da6ebc9)填充）：
```sql
CREATE TABLE article_reads (
    `time` DateTime,
    `article_id` UInt32,
    `sections` Array(UInt16),
    `times` Array(UInt16),
    `user_id` UInt32
)
ENGINE = MergeTree
ORDER BY (article_id, time)

┌────────────────time─┬─article_id─┬─sections─────────────────────┬─times────────────────────────────────┬─user_id─┐
│ 2023-01-18 23:44:17 │         10 │ [16,18,7,21,23,22,11,19,9,8] │ [82,96,294,253,292,66,44,256,222,86] │     424 │
│ 2023-01-20 22:53:00 │         10 │ [21,8]                       │ [30,176]                             │     271 │
│ 2023-01-21 03:05:19 │         10 │ [24,11,23,9]                 │ [178,177,172,105]                    │     536 │
...
```
这个表用于存储文章各个章节的阅读数据。当用户阅读文章时，我们将已读章节保存到 sections 数组列中，并将对应的阅读时间保存到 times 列中。让我们使用 `uniqArray()` 函数计算每篇文章阅读的去重章节数，再使用 `avgArray()` 得到每个章节的平均时间：
```sql
SELECT
    article_id,
    uniqArray(sections) sections_read,
    round(avgArray(times)) time_per_section
FROM article_reads
GROUP BY article_id

┌─article_id─┬─sections_read─┬─time_per_section─┐
│         14 │            22 │              175 │
│         18 │            25 │              159 │
...
│         17 │            25 │              170 │
└────────────┴───────────────┴──────────────────┘
```
我们可以使用 `minArray()` 和 `maxArray()` 函数计算所有文章中最小和最大阅读时间：
```sql
SELECT
    minArray(times),
    maxArray(times)
FROM article_reads

┌─minArray(times)─┬─maxArray(times)─┐
│              30 │             300 │
└─────────────────┴─────────────────┘
```
我们还可以使用 `groupUniqArray()` 函数与 `Array()` 组合器获取每篇文章的阅读章节列表：
```sql
SELECT
    article_id,
    groupUniqArrayArray(sections)
FROM article_reads
GROUP BY article_id

┌─article_id─┬─groupUniqArrayArray(sections)───────────────────────────────────────┐
│         14 │ [16,13,24,8,10,3,9,19,23,14,7,25,2,1,21,18,12,17,22,4,6,5]          │
...
│         17 │ [16,11,13,8,24,10,3,9,23,19,14,7,25,20,2,1,15,21,6,5,12,22,4,17,18] │
└────────────┴─────────────────────────────────────────────────────────────────────┘
```
另一个常用函数是 `any()`，它能在聚合时返回任意列值，同样可以与 `Array` 组合器结合使用：
```sql
SELECT
    article_id,
    anyArray(sections)
FROM article_reads
GROUP BY article_id

┌─article_id─┬─anyArray(sections)─┐
│         14 │                 19 │
│         18 │                  6 │
│         19 │                 25 │
│         15 │                 15 │
│         20 │                  1 │
│         16 │                 23 │
│         12 │                 16 │
│         11 │                  2 │
│         10 │                 16 │
│         13 │                  9 │
│         17 │                 20 │
└────────────┴────────────────────┘
```

### 6.1 使用 Array 与其他组合器

Array 组合器可以与任何其他组合器一起使用：
```sql
SELECT
    article_id,
    sumArrayIfOrNull(times, length(sections) > 8)
FROM article_reads
GROUP BY article_id

┌─article_id─┬─sumArrayOrNullIf(times, greater(length(sections), 8))─┐
│         14 │                                                  4779 │
│         18 │                                                  3001 │
│         19 │                                                  NULL │
...
│         17 │                                                 14424 │
└────────────┴───────────────────────────────────────────────────────┘
```
我们使用 `sumArrayIfOrNull()` 函数来计算阅读了超过八个章节的文章的总时间。请注意，对于阅读不超过八个章节的文章返回 NULL，因为我们还使用了 `OrNull()` 组合器。

如果我们将 `array` 函数与组合器一起使用，我们甚至可以处理更高级的情况：
```sql
SELECT
    article_id,
    countArray(arrayFilter(x -> (x > 120), times)) AS sections_engaged
FROM article_reads
GROUP BY article_id

┌─article_id─┬─sections_engaged─┐
│         14 │               26 │
│         18 │               44 │
...
│         17 │               98 │
└────────────┴──────────────────┘
```
在这里，我们首先使用 `arrayFilter` 函数过滤 times 数组，以删除所有小于等于 120 秒的值。然后，我们使用 `countArray` 来计算每篇文章的过滤时间。


### 6.2 聚合映射

ClickHouse 中另一种强大的类型是 Map。与数组一样，我们可以使用 `Map()` 组合器将聚合应用于此类型。假设我们有一个包含 Map 列类型的如下表：
```sql
CREATE TABLE page_loads (
    `time` DateTime,
    `url` String,
    `params` Map(String, UInt32)
)
ENGINE = MergeTree
ORDER BY (url, time)

┌────────────────time─┬─url─┬─params───────────────────────────────┐
│ 2023-01-25 17:44:26 │ /   │ {'load_speed':100,'scroll_depth':59} │
│ 2023-01-25 17:44:37 │ /   │ {'load_speed':400,'scroll_depth':12} │
└─────────────────────┴─────┴──────────────────────────────────────┘
```
我们可以使用 `sum()` 和 `avg()` 函数配合 `Map()` 组合器，以获得总加载时间和平均滚动深度：
```sql
SELECT
    sumMap(params)['load_speed'] AS total_load_time,
    avgMap(params)['scroll_depth'] AS average_scroll
FROM page_loads

┌─total_load_time─┬─average_scroll─┐
│             500 │           35.5 │
└─────────────────┴────────────────┘
```
`Map()` 组合器还可以与其他组合器一起使用：
```sql
SELECT sumMapIf(params, url = '/404')['scroll_depth'] AS average_scroll FROM page_loads
```

## 7. 聚合相应数组值

处理数组列的另一方法是聚合两个数组中的对应值，从而生成一个新的数组。这种方法适用于向量化数据（如向量或矩阵），可通过 `ForEach()` 组合器实现：

![](https://clickhouse.com/uploads/7_b048be4d47.png)

假设我们有如下表：
```sql
SELECT * FROM vectors

┌─title──┬─coordinates─┐
│ first  │ [1,2,3]     │
│ second │ [2,2,2]     │
│ third  │ [0,2,1]     │
└────────┴─────────────┘
```
为了计算 coordinates 数组的平均值，我们可以使用 `avgForEach()` 组合函数：
```sql
SELECT avgForEach(coordinates) FROM vectors

┌─avgForEach(coordinates)─┐
│ [1,2,2]                 │
└─────────────────────────┘
```
这就要求 ClickHouse 计算 coordinates 数组所有的第一个元素的平均值，并将其放入结果数组的第一个元素中，然后对第二和第三个元素重复相同操作。

当然，还支持与其他组合器一起使用：
```sql
SELECT avgForEachIf(coordinates, title != 'second') FROM vectors

┌─avgForEachIf(coordinates, notEquals(title, 'second'))─┐
│ [0.5,2,2]                                             │
└───────────────────────────────────────────────────────┘
```

## 8. 使用聚合状态

ClickHouse 允许操作聚合的中间状态，而不仅仅是最终结果值。举例来说，假设我们需要统计唯一值(去重)，但又不想保存原始数据本身（因为这会占用更多的存储空间）。在这种情况下，我们可以对 `uniq()` 函数使用 `State()` 组合器来保存中间聚合状态，然后通过 `Merge()` 组合器来计算实际的结果值：
```sql
SELECT uniqMerge(u)
FROM
(
    SELECT uniqState(number) AS u FROM numbers(5)
    UNION ALL
    SELECT uniqState(number + 1) AS u FROM numbers(5)
)

┌─uniqMerge(u)─┐
│            6 │
└──────────────┘
```
这里，第一个嵌套子查询将返回数字 1至5 的唯一计数状态。第二个嵌套子查询则对数字 2至6 返回相同的状态。父查询随后使用 `uniqMerge()` 函数合并子查询的状态，最终统计出我们看到的所有不重复数字的总数量。：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4RZUuTasRav0syZLA6Mu3g6WfPLUXux6kDShLGyroSNh40cg4JJdmCDDet0dxwj7REiaCHq5auUZANw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=16)

最终结果为6，因为两个集合的并集覆盖了 1 到 6 的所有数字:

![](https://clickhouse.com/uploads/1_d266654aa7.png)

为什么我们要这样做？原因很简单：聚合状态占用的空间远小于原始数据。当我们希望将这种状态存储在磁盘上时，这一点尤为重要。例如，`uniqState()` 数据占用的空间比一百万个整数要少15倍：
```sql
SELECT
    table,
    formatReadableSize(total_bytes) AS size
FROM system.tables
WHERE table LIKE 'numbers%'

┌─table─────────┬─size───────┐
│ numbers       │ 3.82 MiB   │ <- we saved 1 million ints here
│ numbers_state │ 245.62 KiB │ <- we save uniqState for 1m ints here
└───────────────┴────────────┘
```

ClickHouse 提供了一种名为 `AggregatingMergeTree` 的表引擎，专门用于存储聚合计算的中间状态，并能根据主键自动完成数据合并。接下来，我们将创建一张表，用于存储之前示例中的每日支付聚合数据:
```sql
CREATE TABLE payments_totals (
    `date` Date,
    `total_amount` AggregateFunction(sum, Float)
)
ENGINE = AggregatingMergeTree
ORDER BY date
```
我们使用了 `AggregateFunction` 类型，这样就能让 ClickHouse 知道我们要存储的是聚合后的总状态，而不是单个数值。在插入数据时，需要使用 `sumState` 函数来插入这个聚合状态:
```sql
INSERT INTO payments_totals SELECT
    date(create_time) AS date,
    sumState(total_amount)
FROM payments
WHERE status = 'confirmed'
GROUP BY date
```
最后，我们需要使用 `sumMerge()` 函数来获取最终的结果值：
```
┌─sumMerge(total_amount)─┐
│     12033.219916582108 │
└────────────────────────┘
```
请注意，ClickHouse 提供了一种简单易用的方式，可以基于物化视图来使用聚合表引擎。此外，ClickHouse 还提供了 `SimpleState` 组合器，作为适用于某些聚合函数（如 'sum' 或 'min'）的优化版本。

## 9. 总结

聚合函数组合器（Aggregation function combinators）为ClickHouse中任何数据结构的分析查询提供了几乎无限的可能性。我们可以为聚合添加条件，对数组元素应用函数，或获取中间状态来存储聚合形式的数据但仍可进行查询。

> 原文：[Using Aggregate Combinators in ClickHouse](https://clickhouse.com/blog/aggregate-functions-combinators-in-clickhouse-for-arrays-maps-and-states)
