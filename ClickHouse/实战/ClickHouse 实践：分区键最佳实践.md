本文介绍在 ClickHouse 数据库中，表设计场景下如何正确选择表分区键，以优化性能和提升数据管理效率。

## 1. 分区键

分区功能会根据指定的键将数据组织成逻辑段，即数据会按照分区键划分为多个独立的片段（part）。当您向没有分区键的表发送插入语句（插入许多行）时，所有数据将会被写入一个新的 part（即数据片段）。然而，当表使用了分区键，会执行以下操作：
- 检查插入表中包含的行的分区键值。
- 在存储中为每个不同的分区键值创建新的part（即数据片段）。
- 将行按照分区键值放入相应的分区中。

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/9513885961/p724556.png)

> 没有分区键的表

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/5497885961/p724597.png)

> 有分区键的表

## 2. 核心原则

为了最小化向 ClickHouse 的对象存储发送写入请求数量，分区键应优先选择低基数（即不同分区值的数量较小）、易于数据管理的字段（如时间），主键应覆盖常用过滤字段且顺序合理。避免高基数字段、过细分区和无关主键，以发挥 ClickHouse 的高性能和易管理优势：
- 分区是数据管理手段

分区主要用于高效的数据过期、分层存储、批量删除等，而不是首选的查询优化工具。详细信息，请参见 Choosing a Partitioning Key。

选择低基数字段作为分区键

推荐分区数控制在100~1000以内，避免高基数字段（即不同分区值的数量很大，如user_id、设备号等）作为分区键，否则会导致Part数量爆炸，影响性能，甚至出现“too many parts”错误。

常见分区方式为按时间分区

按月、按天等时间维度进行分区，如toYYYYMM(date)、toStartOfMonth(date)、toDate(date)，便于数据生命周期管理和冷热分层存储。详细信息，请参见Custom Partitioning Key。

分区键应与数据生命周期、归档、清理等管理需求紧密结合

优先考虑业务上易于批量管理的维度。详细信息，请参见Applications of partitioning。

表设计建议
优先按时间分区
对于日志、时序、监控等场景，推荐按月或按天分区。例如，log表按月份分区，每个月数据为一个分区，具有以下优势：

高效的数据管理：可以按分区批量删除、归档、移动数据。例如，线上工单最典型的ALTER TABLE DELETE删除过期数据场景，按月或者按日分区后只需DROP PARTITION删除对应的分区，无需扫描全表，极大提升效率。

便于实现数据生命周期管理（TTL）：结合TTL策略，可以自动清理过期分区，简化运维。

分区裁剪提升查询效率：查询时如果按时间过滤，ClickHouse只需扫描相关分区，跳过无关分区，显著减少I/O和加快查询速度。

避免高基数字段分区
如用户ID、订单号、设备号等。例如，某个表按照user_id作为分区键，该字段为高基数字段（每个用户唯一代表基数很高），这样会导致分区数非常多，存在以下弊端：

分区数爆炸：每个唯一的用户ID都会生成一个分区，分区数量极大，远超推荐的100~1000范围，导致元数据管理和文件系统压力巨大。

后台合并失效：ClickHouse只会在同一分区内合并parts，分区过多会导致合并操作无法进行，产生大量小part，影响查询和写入性能。

查询性能下降：分区过多会导致查询时需要扫描大量分区元数据，降低查询效率。

实例资源耗尽：过多的分区part会消耗大量内存和文件句柄，甚至导致ClickHouse启动变慢或失败。

分区键不宜过细
如按小时、分钟、秒分区，除非数据量极大且有明确需求。例如，某个表toYYYYMMDDhhmm(event_time) 以分钟为单位分区，每天就有1440个分区，一年将产生超过50万个分区，存在以下弊端：

分区数过多：分区过细会导致分区数量远超推荐的100~1000范围，极大增加元数据和文件系统的管理负担。

典型报错：DB::Exception: Too many parts (N). Merges are processing significantly slower than inserts。

后台合并失效：ClickHouse只会在同一分区内合并parts，分区过多会导致合并操作无法进行，产生大量小part，影响查询和写入性能。

查询和写入性能下降：分区过多会导致查询时需要扫描大量分区元数据，降低查询效率，同时写入时也会因part数量过多而变慢。

分区键应为原始字段或简单表达式
避免复杂函数，便于ClickHouse利用分区裁剪。

分区键与主键配合设计
主键应覆盖常用查询过滤字段，分区键则服务于数据管理。

例如，有一张日志表，典型的业务需求是经常按时间范围和服务名查询，同时需要定期清理过期数据，设计如下：

分区键：toYYYYMM(event_time)，每月一个分区，便于按月批量删除、归档、冷热分层等数据管理操作。

主键：(service_name, event_time)，常用查询如WHERE service_name = 'A' AND event_time BETWEEN ... ，能充分利用主键索引进行数据裁剪，加速查询。

表设计示例

CREATE TABLE logs
(
    event_time DateTime,
    service_name String,
    log_level String,
    message String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)         -- 按月分区，便于数据管理
ORDER BY (service_name, event_time)       -- 主键覆盖常用过滤字段
不推荐的分区键选择
分区键为user_id（高基数）：每个用户一个分区，分区数极多，merge失效，性能极差。

分区键为设备号device_id（高基数）：同上，导致“too many parts”错误，无法管理。

分区键为订单号order_id（高基数）：每个订单一个分区，极端碎片化。

分区键为name（高基数字符串）：分区数不可控，管理困难。

分区键为toHour(event_time)（过细）：每天24个分区，长期运行后分区数极大，merge 失效。

分区键为toMinute(event_time)（极细）：分区数爆炸，严重影响性能。

主键为高基数字段且顺序不合理：例如ORDER BY (user_id, event_time)，但常按 event_time 查询，导致主键索引利用率低。

主键包含过多字段：例如ORDER BY (a, b, c, d, e, f, g, h, i, j)，导致主键索引体积大，内存消耗高。

主键为低基数字段：例如ORDER BY (status)，只有几个状态值，导致主键索引裁剪能力极差。

分区键与主键完全无关，且都不覆盖常用查询条件：例如分区键为region，主键为type，但常按event_time 查询，导致分区和主键都无法加速查询。

> https://help.aliyun.com/zh/clickhouse/use-cases/best-practices-in-selecting-table-partitioning-keys-for-apsaradb-for-clickhouse?spm=a2c4g.11186623.help-menu-144466.d_3_4.49052841afzpHD&scm=20140722.H_2573931._.OR_help-T_cn~zh-V_1
