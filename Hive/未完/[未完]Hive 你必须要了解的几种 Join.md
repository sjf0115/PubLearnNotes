
## 1. Common Join

Common Join 是 Hive 中的默认 Join 类型，也称为 Reduce Side Join。通过一个 MapReduce 作业完成一个 Join 操作。Map 端负责将 Join 操作所需表的数据，并按照关联字段(Join Key)进行分区，通过 Shuffle 将其发送到 Reduce 端，拥有相同的 Key 的数据最终会出现在同一个节点上，在 Reduce 端完成最终的 Join 操作。

![](1)

工作流程：
- 在 Map 阶段，Mapper 从表中读取数据并以 Join 列值作为 Key 输出到一个中间文件。
- 在 Shuffle 阶段，这些键值对被排序以及合并。有相同 Key 的行都会被发送到同一个 Reducer 实例上。
- 在 Reduce 阶段，Reducer 获取排序后的数据并进行 Join。

Common Join 的优点是可以适用于任何大小的表。但由于 Shuffle 操作代价比较高，因此非常耗费资源。如果一个或多个 Join Key 占据了很大比例的数据，相应的 Reducer 实例负载就会很高，需要运行很长时间。问题是大多数 Reducer 实例已经完成了 Join 操作，只有部分实例仍在运行。查询的总运行时间由运行时间最长的 Reducer 决定。显然，这是一个典型的数据倾斜问题。

如何识别 Common Join：使用 EXPLAIN 命令时，在 Reduce Operator Tree 下方看到 Join Operator。

## 2. Map Join

Common Join 的一个主要问题是 Shuffle 代价太高会导致数据倾斜问题。当其中一个 Join 表足够小可以放进内存时就可以使用 Map Join，因此它速度快但受表大小的限制。

![](2)

Map Join 的第一步是在原始 Map Reduce 任务之前创建一个 Map Reduce 本地任务。这个任务从 HDFS 读取小表的数据并将其保存到内存中的哈希表中，然后保存到哈希表文件中。接下来，当原始的 Join Map Reduce 任务开始时，会将哈希表文件上传到 Hadoop 分布式缓存中，该缓存会将这些文件发送到每个 Mapper 的本地磁盘上。因此，所有 Mapper 都可以将此持久化的哈希表文件加载回内存，然后在 Map 阶段进行 Join。

在 0.11 版之前，可以通过优化器提示调用 Map Join：
```sql
SELECT
  /*+ MAPJOIN(b) */
  count(*)
FROM a
JOIN b
ON a.uid = b.uid;
```
从 Hive 0.7.0 版本开始，可以使用 hive.auto.convert.join 配置自动转换为 Map Join，不再需要优化器提示：
```sql
SET hive.auto.convert.join=true;
SELECT
  count(*)
FROM a
JOIN b
ON a.uid = b.uid;
```
hive.auto.convert.join 的默认值在 Hive 0.7.0 版本中为 false，需要手动修改配置。在 Hive 0.11.0 版本中默认值已经更改为 true([HIVE-3297](https://issues.apache.org/jira/browse/HIVE-3297))。需要注意的是在 Hive 0.11.0 到 0.13.1 ，hive-default.xml.template 错误地将其默认值设置为 false。

在 Join 过程中，需要通过参数 `hive.mapjoin.smalltable.filesize` 来确定哪个表是小表，默认情况下为 25MB。当 Join 中涉及三个或更多表时，Hive 会生成三个或更多的 Map Join，并假设所有表都是小表。为了进一步加快 JOIN 速度，如果 n-1 表的大小小于 10MB（这是默认值），您可以将三个或更多地图侧连接合并为一个地图侧连接。为此，您需要将 hive.auto.convert.join.noconditionaltask 参数设置为 true 并指定参数 hive.auto.convert.join.noconditionaltask.size。


如何识别 Map Join：使用 EXPLAIN 命令时，在 Map Operator Tree 下方会看到 Map Join Operator。

## 3. Bucket map JOIN

Bucket Map Join 是应用在 Bucket 表上的一种特殊类型的 Map JOIN。如果要使用 Bucket Map JOIN 时，需要使用如下配置:
- set hive.auto.convert.join=true;
- set hive.optimize.bucketmapjoin=true; —— 默认为false

在 Bucket Map Join 中，所有 JOIN 表都必须是 Bucket 表，并在 Bucket 列上进行 JOIN。此外，较大表中的桶号必须是小表桶的倍数

## 4. Sort merge bucket (SMB) join

Sort Merge Bucket (SMB) Join

SMB是在具有相同排序、桶和连接的桶表上执行的连接

状态列。它从两个桶表读取数据，并执行公共连接(映射

和减少触发)在桶桌上。我们需要启用以下属性

使用SMB:
- set hive.input.format=org.apache.hadoop.hive.ql.io.BucketizedHiveInputFormat;
- set hive.auto.convert.sortmerge.join=true;
- set hive.optimize.bucketmapjoin=true;
- set hive.optimize.bucketmapjoin.sortedmerge=true;
- set hive.auto.convert.sortmerge.join.noconditionaltask=true;


## 5. Sort merge bucket map (SMBM) join

## 6. Skew join

在处理分布极不均匀的数据时，可能会发生数据倾斜。这样一来，少量的计算节点就必须处理大量的计算。以下设置通知Hive在数据倾斜时进行适当优化发生了:
- SET hive.optimize.skewjoin=true;
- SET hive.skewjoin.key=100000;

需要设置 hive.groupby。skewindata=true 可使用上述设置在GROUP BY结果中启用倾斜数据优化。一旦配置完成，Hive将首先触发一个额外的MapReduce作业，其映射输出将随机分布到reducer，以避免数据倾斜



。。。
