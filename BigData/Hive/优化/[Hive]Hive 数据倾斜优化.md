
### 1. 参数调优

(1) hive.groupby.skewindata

如果 `hive.groupby.skewindata` 设置为 `true` 时，生成的查询计划会有两个 mapreduce 作业。第一个 mapreduce 作业中，Map 的输出结果集合会随机分布到 Reduce 中，每个 Reduce 做部分聚合操作，并输出结果，这样处理的结果是相同的 Group By Key 有可能被分发到不同的 Reduce 中，从而达到负载均衡的目的。

第二个 mapreduce 作业再根据预处理的数据结果按照 Group By Key 分布到 Reduce 中（这个过程可以保证相同的 Group By Key 被分布到同一个 Reduce 中），最后完成最终的聚合操作。

(2) hive.map.aggr=true

如果 `hive.map.aggr` 设置为 `true`，会在 Map 端进行部分聚合，相当于Combiner。

### 2. SQL语句优化

#### 2.1 大表关联小表



MapJoin简单说就是在Map阶段将小表读入内存，顺序扫描大表完成Join。

上图是Hive MapJoin的原理图，出自Facebook工程师Liyin Tang的一篇介绍Join优化的slice，从图中可以看出MapJoin分为两个阶段：

通过MapReduce Local Task，将小表读入内存，生成HashTableFiles上传至Distributed Cache中，这里会对HashTableFiles进行压缩。

MapReduce Job在Map阶段，每个Mapper从Distributed Cache读取HashTableFiles到内存中，顺序扫描大表，在Map阶段直接进行Join，将数据传递给下一个MapReduce任务。

可以使用Map Join让小的维度表（1000条以下的记录条数）先进内存。在map端完成reduce。

### 3.





原文：　https://www.cnblogs.com/skyl/p/4855099.html
