大家都知道，由于 MergeTree 的实现原理导致它只能支持数据的最终一致性。这导致我们在使用 ReplacingMergeTree、SummingMergeTree 这类表引擎的时候，会出现短暂数据不一致的情况。

在某些对一致性非常敏感的场景，通常有这么几种解决方案。



一种是在写入数据后，立刻通过
```sql
OPTIMIZE TABLE PARTITION part FINAL
```
强制触发新写入分区的合并动作。

一种是通过 GROUP BY 查询 + 过滤实现，可以参考我先前的[文章](https://mp.weixin.qq.com/s/a8OfsBn9VFnj7oxp0IIVGg)。

还有一种是通过 FINAL 查询实现，即在查询语句后增加 FINAL 修饰符，这样在查询的过程中将会执行 Merge 的特殊逻辑(例如数据去重，预聚合等)。但是这种方法基本没有人使用，因为在增加 FINAL 之后，我们的查询将会变成一个单线程的执行过程，查询速度非常慢。

但是在最新的 MaterializeMySQL 中，消费同步 binlog 的表使用了 ReplacingMergeTree，而它实现数据去重的方法就是使用了 FINAL 查询，难道不怕慢吗？不知道 MaterializeMySQL ? 请参考[文章](https://mp.weixin.qq.com/s/CxvWmgjywHLFraGF9F1ROw)。

原来在 v20.5.2.7-stable 版本中，FINAL 查询进行了优化，现在已经支持多线程执行了，并且可以通过 `max_final_threads` 参数控制单个查询的线程数。https://github.com/ClickHouse/ClickHouse/pull/10463

支持了多线程的 FINAL 查询到底性能如何呢? 我们就来试试看吧。这里直接使用 Yandex 提供的测试数据集 hits_100m_obfuscated，它拥有 1亿 行数据，105个字段，DDL示意如下：
```sql
ATTACH TABLE hits_100m_obfuscated (
    `WatchID` UInt64,
    `JavaEnable` UInt8,
    `Title` String,
    `GoodEvent` Int16,
    `EventTime` DateTime,
    ...
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(EventDate)
ORDER BY (CounterID, EventDate, intHash32(UserID), EventTime)
SAMPLE BY intHash32(UserID)
```

我使用了两台 8c 16g 的虚拟机，分别安装了19.17.4.11 和 20.6.3.28 两个版本的 CH 进行对比。首先在 19.17.4.11 中执行普通的语句:
```sql
select * from hits_100m_obfuscated WHERE EventDate = '2013-07-15' limit 100

100 rows in set. Elapsed: 0.595 sec.
```
接近0.6秒返回，它的执行日志如下所示：
```
Expression
 Expression
  ParallelAggregating
   Expression × 8
    MergeTreeThread
```
可以看到这个查询有8个线程并行查询。

接下来换 FINAL 查询:
```sql
select * from hits_100m_obfuscated FINAL WHERE EventDate = '2013-07-15' limit 100

100 rows in set. Elapsed: 1.406 sec.
```
时间慢了接近3倍，然后看看 FINAL 查询的执行日志:
```
Expression
 Expression
  Aggregating
   Concat
    Expression
     SourceFromInputStream
```
先前的并行查询变成了单线程，所以速度变慢也是情理之中的事情了。

现在我们换到 20.6.3.28 版本执行同样的对比查询。首先执行普通的不带 FINAL 的查询:
```sql
select * from hits_100m_obfuscated WHERE EventDate = '2013-07-15' limit 100 settings max_threads = 8

100 rows in set. Elapsed: 0.497 sec.
```
返回时间很快，在 CH 新版本中已经实现了 EXPLAIN 查询，所以查看这条 SQL 的执行计划就很方便了：
```
explain pipeline select * from hits_100m_obfuscated  WHERE EventDate = '2013-07-15' limit 100  settings max_threads = 8

(Union)
Converting × 8
  (Expression)
  ExpressionTransform × 8
    (Limit)
    Limit 8 → 8
      (Expression)
      ExpressionTransform × 8
        (ReadFromStorage)
        MergeTreeThread × 8 0 → 1
```
很明显的，该SQL将由8个线程并行读取 part 查询。

现在换 FINAL 查询:
```sql
select * from hits_100m_obfuscated final WHERE EventDate = '2013-07-15' limit 100  settings max_final_threads = 8

100 rows in set. Elapsed: 0.825 sec.
```
查询速度没有普通的查询快，但是相比之前已经有了一些提升了，我们看看新版本 FINAL 查询的执行计划：
```
explain pipeline select * from hits_100m_obfuscated final WHERE EventDate = '2013-07-15' limit 100  settings max_final_threads = 8

(Union)
Converting × 8
  (Expression)
  ExpressionTransform × 8
    (Limit)
    Limit 8 → 8
      (Expression)
      ExpressionTransform × 8
        (Filter)
        FilterTransform × 8
          (ReadFromStorage)
          ExpressionTransform × 8
            ReplacingSorted × 8 6 → 1
              Copy × 6 1 → 8
                AddingSelector × 6
                  ExpressionTransform
                    MergeTree 0 → 1
                      ExpressionTransform
                        MergeTree 0 → 1
                          ExpressionTransform
                            MergeTree 0 → 1
                              ExpressionTransform
                                MergeTree 0 → 1
                                  ExpressionTransform
                                    MergeTree 0 → 1
                                      ExpressionTransform
                                        MergeTree 0 → 1
```
可以看到新版本 FINAL 查询的执行计划有了很大的变化。 在这条 SQL 中，从ReplacingSorted 这一步开始已经是多线程执行了。不过比较遗憾的是，目前读取 part 部分的动作还是串行的。在这里例子中可以看到，这张表有6个分区被依次加载了。

好了，现在总结一下：
- 从 v20.5.2.7-stable 版本开始，FINAL 查询执行并行执行了
- 目前读取 part 部分的动作依然是串行的
- 总的来说，目前的 FINAL 相比之前还是有了一些性能的提升

最后的最后，FINAL 查询最终的性能和很多因素相关，列字段的大小、分区的数量等等都会影响到最终的查询时间， 所以大家还是需要基于自己的业务数据多加测试。
