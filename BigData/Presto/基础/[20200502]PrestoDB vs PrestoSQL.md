
Presto 社区分家后搞了2个项目，分别为 PrestoDB 和 PrestoSQL，同时他们都成立了自己的基金会。而去年国庆时候，abei写了篇文章《PrestoDB VS PrestoSQL发展比较》比对了2个分支的进展。而现在已经分家17个月了，那我们简单梳理下这2个分支的主要核心功能：

PrestoDB：

Connector：ElasticSearch 及 Druid
Master 和Worker 通信协议支持二进制
Orc 及 Parquet读写性能优化
Hive写数据支持指定压缩格式
task通信协议可以指定 thrift
spi pushdown
MapReduce-style shuffle，支持部分 etl 任务及大查询
fix bug 及 improve performace
PrestoSQL：

Connector：ElasticSearch和MemSQL
spi pushdown
S3优化读取
join 延时物化
大量的 fix bug 及 improve performance
从以上功能实现可以看到，PrestoDB更符合我对Presto未来的定位：

支持大集群
提高并发能力
减少指定场景的查询耗时，比如ORC
下推能力存储计算分离，比如agg扔到存储层去做（2个分支都有）
除了以上功能外，PrestoDB还有其他优点：

核心功能会有技术文章输出
issue里技术实现和细节比较全
基金会里包含Facebook、阿里巴巴、twitter及Uber，有场景支持和实践，目前twitter员工很活跃
老的PrestoDB版本升级简单
PrestoDB代码质量比PrestoSQL要好，PrestoSQL有些地方代码改的有些混乱
wiki和文章排版很舒服，PrestoSQL Blog也没有任何技术输出
PrestoDB缺点：

主要是Facebook员工维护，Facebook的文化迫使他们员工没有办法花时间在社区上
社区活跃度不如PrestoSQL
Release Notes 上的改动没有对应的issue链接
19年我经常在slack上与PrestoSQL社区的人打交道，别人问我选择版本时候，我都是建议选择PrestoSQL，但是目前我有了不同的想法，如果说只是使用Presto，2个分支其实都无所谓，如果说公司体量较大，会有不少二次开发，我认为PrestoDB做的事情和提供的能力更符合国内很多公司的需求，比如让Presto即要支持ad-hoc，又要支持etl（听说目前Facebook就在这么搞），以及很多实时需求等等。



原文：
- [Presto Software Foundation Launches to Advance Presto Open Source Community](http://www.prweb.com/releases/presto_software_foundation_launches_to_advance_presto_open_source_community/prweb16070792.htm)
- [PrestoSQL 项目更名为 Trino，彻底和 PrestoDB 分家](https://www.iteblog.com/archives/9918.html)
- [PrestoDB和PrestoSQL比较及选择](https://mp.weixin.qq.com/s/oy-MD9ZZdsXfK3eYwJMfuA)
- [PrestoDB VS PrestoSQL发展比较](https://mp.weixin.qq.com/s/KK1VRWMurf_8xAwcBsdeZw)
