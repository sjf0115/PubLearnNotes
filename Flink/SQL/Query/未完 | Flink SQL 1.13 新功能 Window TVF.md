
社区的小伙伴应该了解，在腾讯、阿里巴巴、字节跳动等公司的内部分支已经开发了这个功能的基础版本。这次 Flink 社区也在 Flink 1.13 推出了 TVF 的相关支持和优化。下面将从 Window TVF 语法、近实时累计计算场景、 Window 性能优化、多维数据分析，来解读这个新功能。

## 1. Window TVF 语法

在 1.13 版本前，window 的实现是通过一个特殊的 SqlGroupedWindowFunction：
```sql
SELECT
  TUMBLE_START(bidtime,INTERVAL '10' MINUTE),
  TUMBLE_END(bidtime,INTERVAL '10' MINUTE),
  TUMBLE_ROWTIME(bidtime,INTERVAL '10' MINUTE),
  SUM(price)
FROM MyTable
GROUP BY TUMBLE(bidtime,INTERVAL '10' MINUTE)
```
在 1.13 版本中，我们对它进行了 Table-Valued Function 的语法标准化：
```sql
SELECT WINDOW_start,WINDOW_end,WINDOW_time,SUM(price)
FROM Table(TUMBLE(Table myTable,DESCRIPTOR(biztime),INTERVAL '10' MINUTE))
GROUP BY WINDOW_start,WINDOW_end
```
通过对比两种语法，我们可以发现：TVF 语法更加灵活，不需要必须跟在 GROUP BY 关键字后面，同时 Window TVF 基于关系代数，使得其更加标准。在只需要划分窗口场景时，可以只用 TVF，无需用 GROUP BY 做聚合，这使得 TVF 扩展性和表达能力更强，支持自定义 TVF（例如实现 TOP-N 的 TVF）。



上图中的示例就是利用 TVF 做的滚动窗口的划分，只需要把数据划分到窗口，无需聚合；如果后续需要聚合，再进行 GROP BY 即可。同时，对于熟悉批 SQL 的用户来说，这种操作是非常自然的，我们不再需要像 1.13 版本之前那样必须要用特殊的 SqlGroupedWindowFunction 将窗口划分和聚合绑定在一起。


目前 Window TVF 支持 tumble window，hop window，新增了 cumulate window；session window 预计在 1.14 版本也会支持。

## 2. Cumulate Window

Cumulate window 就是累计窗口，简单来说，以上图里面时间轴上的一个区间为窗口步长。

第一个 window 统计的是一个区间的数据；


第二个 window 统计的是第一区间和第二个区间的数据；


第三个 window 统计的是第一区间，第二个区间和第三个区间的数据。


累积计算在业务场景中非常常见，如累积 UV 场景。在 UV 大盘曲线中：我们每隔 10 分钟统计一次当天累积用户 UV。

![]()

在 1.13 版本之前，当需要做这种计算时，我们一般的 SQL 写法如下：
```sql
INSERT INTO cumulative_UV
SELECT date_str,MAX(time_str),COUNT(DISTINCT user_id) as UV
FROM (
  SELECT
    DATE_FORMAT(ts,'yyyy-MM-dd') as date_str,
    SUBSTR(DATE_FORMAT(ts,'HH:mm'),1,4) || '0' as time_str,
  user_id
  FROM user_behavior
)
GROUP BY date_str
```
先将每条记录所属的时间窗口字段拼接好，然后再对所有记录按照拼接好的时间窗口字段，通过 GROUP BY 做聚合，从而达到近似累积计算的效果。

1.13 版本前的写法有很多缺点，首先这个聚合操作是每条记录都会计算一次。其次，在追逆数据的时候，消费堆积的数据时，UV 大盘的曲线就会跳变。


在 1.13 版本支持了 TVF 写法，基于 cumulate window，我们可以修改为下面的写法，将每条数据按照 Event Time 精确地分到每个 Window 里面, 每个窗口的计算通过 watermark 触发，即使在追数据场景中也不会跳变。

```sql
INSERT INTO cumulative_UV
SELECT WINDOW_end,COUNT(DISTINCT user_id) as UV
FROM Table(
  CUMULATE(Table user_behavior,DESCRIPTOR(ts),INTERVAL '10' MINUTES,INTERVAL '1' DAY))
)
GROUP BY WINDOW_start,WINDOW_end
```
UV 大盘曲线效果如下图所示：

![]()

## 3. Window 性能优化

Flink 1.13 社区开发者们对 Window TVF 进行了一系列的性能优化，包括：
- 内存优化：通过内存预分配，缓存 window 的数据，通过 window watermark 触发计算，通过申请一些内存 buffer 避免高频的访问 state；
- 切片优化：将 window 切片，尽可能复用已计算结果，如 hop window，cumulate window。计算过的分片数据无需再次计算，只需对切片的计算结果进行复用；
- 算子优化：window 算子支持 local-global 优化；同时支持 count(distinct) 自动解热点优化；
- 迟到数据：支持将迟到数据计算到后续分片，保证数据准确性。

基于这些优化，我们通过开源 Benchmark (Nexmark) 进行性能测试。结果显示 window 的普适性能有 2x 提升，且在 count(distinct) 场景会有更好的性能提升。

![]()

## 4. 多维数据分析

语法的标准化带来了更多的灵活性和扩展性，用户可以直接在 window 窗口函数上进行多维分析。如下图所示，可以直接进行 GROUPING SETS、ROLLUP、CUBE 的分析计算。如果是在 1.13 之前的版本，我们可能需要对这些分组进行单独的 SQL 聚合，再对聚合结果做 union 操作才能达到类似的效果。而现在，类似这种多维分析的场景，可以直接在 window TVF 上支持。

![]()

支持 Window Top-N

除了多维分析，Window TVF 也支持 Top-N 语法，使得在 Window 上取 Top-N 的写法更加简单。

![]()

...
