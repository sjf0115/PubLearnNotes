## 1. 前言

Apache Paimon 作为数据湖对各种场景有着完整的功能支持，看完这篇文章，你可以了解到 Paimon 有哪几种表模式。对应哪些场景。

## 2. 概览

![](https://mmbiz.qpic.cn/sz_mmbiz_png/Tu25q5CsmvZay54XEGlPxFlNuLIiajmLPhCicLTJKczsmbsbaXSfFr0UbAbWMNtHcqfw3X9e5s4Shiakn3OOxMkdw/640?wx_fmt=png&from=appmsg&wxfrom=13&tp=wxpic#imgIndex=0)

上图描述了大致所有表模式的配置及能力，在下文中，会逐个简单介绍下。以上的所有表模式在最新版本中已得到生产验证。

## 3. 主键表

主键表是 Paimon 作为流式数据湖的核心，它可以接收上游来自数据库 CDC 或者 Flink Streaming 产生的 Changelog，里面包含 INSERT、UPDATE、DELTE 的数据。

主键表支持分区，它和 Hive 分区的概念完全相同，分区字段与主键字段的关系请见后面的具体说明。

主键表强制绑定 Bucket (桶) 概念，数据根据主键会被分配不同的 Bucket 中，在同一时间，同一个主键只会落到同一个 Bucket 中，每个 bucket 里面都包含一个单独的 LSM Tree 及其变更日志文件。Bucket 是最小的读写存储单元，因此 Bucket 的数量限制了最大的处理并行度。不过，这个数字不应该太大，因为这会导致大量小文件和低读取性能。一般情况下，建议每个bucket中的数据大小约为 200MB-1GB。

Paimon 采用 LSM Tree 作为文件存储的数据结构。LSM Tree 将文件组织为几个排序的 Sort Runs。Sort Runs 由一个或多个数据文件组成，数据文件中的记录按其主键进行排序。在 Sort Run 中，数据文件的主键范围从不重叠。

### 3.1 Compaction

主键表的 Compaction 默认在 Flink Sink 中自动完成，你不用关心它的具体过程，它会在 LSM 中生成一个 写放大 与 读放大 的基本平衡。你需要关心的有两点：
- 后台运行的 Compaction 会不会阻塞写？
- 想要多作业同时写入一张表怎么办？

对于第一点，你可以开启全异步 Compaction：
```sql
num-sorted-run.stop-trigger = 2147483647
sort-spill-threshold = 10
-- 此参数针对 changelog-producer=lookup的表
changelog-producer.lookup-wait = false
```

全异步 Compaction 打开后，Compaction 永远不会阻塞 Write 的正常写入。

Paimon 支持多作业同时写入，但是并不支持多作业同时 Compaction，所以你可以给写入作业配置 write-only 为 true，避免写入作业进行后台 compaction，然后启动单独的 Dedicated Compaction Job。

### 3.2 固定桶主键表

```sql
CREATE TABLE MyTable (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
    'bucket' = '5' -- default 1
)
```

此模式定义固定的 Bucket 个数，上面有说过，Bucket 个数会影响并发度，影响性能，所以你需要根据表的数据量来合理定义出一个 bucket 个数，而且可能会有调整的场景：
- 我们一般推荐直接重建表方便
- 也可以保留已经写入的数据，详见文档 Rescale Bucket

固定 Bucket 的模式下并不支持跨分区更新，所以此模式需要你的主键包含所有的分区字段，在分区内更新：
```sql
CREATE TABLE MyTable (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    dt STRING,
    PRIMARY KEY (dt, user_id) NOT ENFORCED
) P. dt WITH (
    'bucket' = '5' -- default 1
)
```
以下三种类型的字段可以定义为主键表的分区字段：
- 创建时间（推荐）：创建时间通常是不可变的，因此您可以放心地将其视为分区字段，并将其添加到主键中。
- 事件时间：事件时间是表中的一个字段。对于 CDC 数据，比如 MySQL CDC 同步的表，或者 Paimon 生成的 changelog，都是完整的 CDC 数据，包括 UPDATE_BEFORE 记录，即使声明了包含主键的分区字段，也可以达到唯一的效果（需要 'changelog-producer' = 'input'）。
- CDC op_ts：不能定义为分区字段，因为不能知道以前的记录时间戳，需要使用跨分区更新的功能。

执行 Flink 写入的拓扑图如下：

![](https://mmbiz.qpic.cn/sz_mmbiz_png/Tu25q5CsmvZay54XEGlPxFlNuLIiajmLPwtfCNv5yV8RRY85ibqrFNWjIvssUC1bwRw4zxlaErpkmCZGIVp7FsFg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

如图所示，Writer 前会有根据 bucket 的 shuffler。

### 3.3 动态桶主键表

配置 'bucket' = '-1'，数据如果是已经存在主键，将会落入旧的存储桶中，新的主键将落入新的存储桶。存储桶和主键的分布取决于数据到达的顺序。Paimon 会维护一个索引，以确定哪个主键对应于哪个桶。Paimon 会自动扩展 bucket 的数量。有两个参数你需要关心：
- 'dynamic-bucket.target-row-num'：控制一个桶的目标数据量。
- 'dynamic-bucket.initial-buckets'：控制桶的初始化个数。

请注意，动态桶由于需要维护索引，它并不支持多个作业同时写入，请 UNION ALL 多路到单个 Flink Sink。

#### 3.3.1 普通动态桶

```sql
CREATE TABLE MyTable (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    dt STRING,
    PRIMARY KEY (dt, user_id) NOT ENFORCED
) P. dt WITH (
    'bucket' = '-1'
)
```
当您的更新不跨分区（没有分区，或者主键包含所有分区字段）时，动态桶模式使用 HASH 索引来维护从主键到桶的映射，这比固定桶模式需要更多的内存，一个分区中的1亿个条目会多占用 1GB 的内存 (整个作业，将会被分摊到多个 TaskManager 中)，这内存消耗并不高，而且不再活动的分区不会占用内存。对于更新率较低的表，建议使用此模式以显著提高易用性。


执行拓扑如下：

![](https://mmbiz.qpic.cn/sz_mmbiz_png/Tu25q5CsmvZay54XEGlPxFlNuLIiajmLPaDPT5OqJZpBGZicBfqTZBbpwoFJR4OibKyIDngC4EBMqdG3RRjtZicFeg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

可以看到，多出来一个节点用于桶的分配。

#### 3.3.2 跨分区更新动态桶

```sql
CREATE TABLE MyTable (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    dt STRING,
    PRIMARY KEY (user_id) NOT ENFORCED
)  P. dt WITH (
    'bucket' = '-1'
)
```
当您需要跨分区更新（主键不包含所有分区字段）时，此模式直接维护主键到分区和 Bucket 的映射，使用本地磁盘，并在启动流写入作业时初始化索引。

Paimon 会利用诸多手段来加速初始化索引的过程，往往初始化过程非常快速。Paimon 也会默认使用 Flink Managed Memory 来当做 RocksDB 的 Block Cache，它是后续检索性能的关键。

当然，随着分区的增多，主键个数可能会越来越多，如果您的更新不依赖于太旧的数据，您可以考虑配置索引 TTL 以减少初始化时间和提升索引性能：'cross-partition-upsert.index-ttl'，但请注意，如果评估不准确，它可能导致你的表产生重复数据。

执行拓扑如下：

![](https://mmbiz.qpic.cn/sz_mmbiz_png/Tu25q5CsmvZay54XEGlPxFlNuLIiajmLP4RQn7ic9ahVMuW0QVVJshWRn94sq1KfPP9N4Y6ljsCNvmxW3v4JJt0g/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=3)

可以看到，在 assigner 前，会有 INDEX_BOOTSTRAP 节点来初始化索引，Paimon 为了正确性考虑，你没有办法跳过初始化阶段，但请放心，在大部分场景这个初始化速度非常快。

## 4. Append 表

如果表没有定义主键，则它是 Append 表，你只能插入 INSERT 的数据。Append 表的 Compaction 只是用来合并小文件。目前 Append 表有两种模式：Scalable 表 与 Queue 表。整体上我们推荐使用 Scalable 表，它更简单易懂。

### 4.1 Append Scalable 表

```sql
CREATE TABLE MyTable (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    dt STRING
) WITH (
    'bucket' = '-1'
)
```
当你定义 bucket 为 -1，且没有主键时，你可以认为它就是一张增强的 Hive 表，它将没有桶的概念 (虽然这种模式把数据放到 bucket-0 目录中，但是所有的读写并没有并发限制，桶被忽略了)，它就是一个普通的数仓表，支持批写批读，支持流写流读，只是它的流读会有一部分乱序 (并不是完全的输入顺序)。

它有如下应用场景：
- 简单替换 Hive 表，在 Hive 表的基础上拥有湖存储的 ACID 特性。
- 你可以流写流读它，它有着非常高的吞吐，非常好的易用性。
- 你也可以使用对它进行批的排序，结合 z-order 等手段，它可以提供非常快速的点查范围查询。

如果你想在传统 TPC-DS 中测试 Paimon 表，请使用此模式。


执行拓扑：

![](https://mmbiz.qpic.cn/sz_mmbiz_png/Tu25q5CsmvZay54XEGlPxFlNuLIiajmLPGt7IRtxhh3HBaGM1PoyM0MynX6mar6sNoIpbPVOyA3cSic5TrqaRu8A/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=4)

图的上面部分是 Source 数据写入表，可以看到，中间并没有 Shuffler 了，它可以有着非常高的吞吐。

图的下面部分是 Compaction 拓扑，它会监控文件，进行必要性的小文件合并，它是完全非阻塞，纯异步的模式，并不会阻塞正常数据的写。如果你希望关闭它，请配置 'write-only'。
我们的建议是：在一个流写任务中保持 Compaction 拓扑的打开 (或者启动 Dedicated Compaction 作业)，其它写作业统统 write-only，这是非常方便的玩法，Compaction 拓扑不但会合并小文件，还会清理过期 Snapshots 等等。

### 4.2 Append Queue 表

```
CREATE TABLE MyTable (
    user_id BIGINT,
    item_id BIGINT,
    behavior STRING,
    dt STRING
) WITH (
    'bucket' = '10',
    'bucket-key' = 'user_id'
)
```
在这种模式下，你可以将 Append 表视为一个由 bucket 分隔的队列。同一存储桶中的每条记录都是严格排序的，流式读取会将记录准确地按写入顺序传输到下游。你需要还可以定义 bucket 个数和 bucket-key，以实现更大的并行性 (默认 bucket 为 1)。

目前 Queue 表只能通过设置 bucket-key 的方式，Flink Kafka 默认模式 (Fixed, each Flink task ends up in at most one Kafka partition) 暂时没被支持，但是这在 Roadmap 上。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/Tu25q5CsmvZay54XEGlPxFlNuLIiajmLP2Ya9BXPcBrdgzKtpeo7ibeITDKPw9QKDY6QmYTkHzDuLX5ap6gXgztA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=5)

整张表就像 Kafka 的 Queue 一样在工作，它与 Kafka 的优劣如下：
- 延时分钟级，而 Kafka 可以是秒级，但是 Paimon 的成本要低得多。
- 数据沉淀下来，可被计算引擎 AD-HOC 查询。
- 流读可以进行 Projection & Filter Pushdown，这可以大大降低成本。

另外，此模式的 Compaction 只会进行 bucket 内的小文件合并，所以会造成更多的小文件，你可以配置 'compaction.max.file-num' (默认 50) 更小的此参数来更多的合并小文件。

另外，并不仅仅是顺序，Paimon 的此模式还可以让你定义 Watermark，并且支持最新的 Watermark 对齐的策略。
