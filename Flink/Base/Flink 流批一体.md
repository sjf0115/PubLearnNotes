

## 1. DataStream API 支持批执行模式

> Flink 1.12

Flink 的核心 API 最初是针对特定的场景设计的，尽管 Table API / SQL 针对流处理和批处理已经实现了统一的 API，但当用户使用较底层的 API 时，仍然需要在批处理（DataSet API）和流处理（DataStream API）这两种不同的 API 之间进行选择。鉴于批处理是流处理的一种特例，将这两种 API 合并成统一的 API，有一些非常明显的好处，比如：
- 可复用性：作业可以在流和批这两种执行模式之间自由地切换，而无需重写任何代码。因此，用户可以复用同一个作业，来处理实时数据和历史数据。
- 维护简单：统一的 API 意味着流和批可以共用同一组 connector，维护同一套代码，并能够轻松地实现流批混合执行，例如 backfilling 之类的场景。

考虑到这些优点，社区已朝着流批统一的 DataStream API 迈出了第一步：支持高效的批处理（FLIP-134）。从长远来看，这意味着 DataSet API 将被弃用（FLIP-131），其功能将被包含在 DataStream API 和 Table API / SQL 中。

> https://mp.weixin.qq.com/s/6YaLA-_UL_L4V27BT4jrKQ


https://mp.weixin.qq.com/s/qcS4FQdSHaZaU52ELEBqBw
https://mp.weixin.qq.com/s/AnBU9ntRVwbsWQoiDkzZHg
https://mp.weixin.qq.com/s/_DalioFjqqWCncmoU03uNA
https://mp.weixin.qq.com/s/CujqeteeJt82wjVhhvPE8g
