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

与最小/最大值分析不同，我们可能希望在聚合之前先将数据分成组，再分别计算各组的指标。这可以通过 `Resample` 组合器实现。该组合器接收一个列、范围（开始/结束）和您希望使用的分割数据的步长。然后返回每个组的聚合结果：

![](https://mmbiz.qpic.cn/mmbiz_png/ECfQdkxm4RZUuTasRav0syZLA6Mu3g6WyMNGWoZf1GL8icNicp3iaubZhCuGZhjAC8fjxzyk15NJCBSPaYGPylDoQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=9)

假设我们想根据total_amount从0（最小值）到500（最大值）以100的步长拆分我们的payments表数据。然后，我们想知道每个组中有多少条目以各组的平均总和：


> 原文：[Using Aggregate Combinators in ClickHouse](https://clickhouse.com/blog/aggregate-functions-combinators-in-clickhouse-for-arrays-maps-and-states)
