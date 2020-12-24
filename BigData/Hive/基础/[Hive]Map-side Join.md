
Hive支持 MapJoin，适合场景：至少足够小可以放入内存。在版本0.11之前，可以通过MapJoin提示调用MapJoin：
```sql
set hive.ignore.mapjoin.hint = false;
select /*+ MAPJOIN(time_dim) */ count(*)
from store_sales
join time_dim
on (ss_sold_time_sk = t_time_sk)
```
或者
```sql
set hive.auto.convert.join=true;
select count(*)
from store_sales
join time_dim
on (ss_sold_time_sk = t_time_sk)
```
在Hive 0.10.0版本中　`Hive.auto.convert.join`　的默认值为 `false`。Hive 0.11.0以后版本将默认值更改为 `true`（HIVE-3297）。请注意，在Hive 0.11.0至0.13.1版本中 `hive-default.xml.template` 错误地将默认值设置为 `false`。

### 1. MapJoin提示

上面第一个语句使用 `MAPJOIN` 提示来优化查询的执行时间。在此示例中，`tmp_entrance_order_user` 表要比 `tmp_entrance_order` 表小：
```sql
SELECT /*+ MAPJOIN(u) */ o.gid, o.orderTime, o.businessType
FROM tmp_entrance_order o
JOIN tmp_entrance_order_user u
ON u.gid = o.gid;
```
默认情况下 MapJoin 提示优化选项是关闭的，需要开启：
```
set hive.ignore.mapjoin.hint = false;
```
输出信息如下：
```
2017-04-19 03:57:07     Starting to launch local task to process map join;      maximum memory = 514850816
2017-04-19 03:57:08     Processing rows:        8       Hashtable size: 8       Memory usage:   146857552       rate:   0.285
2017-04-19 03:57:08     Dump the hashtable into file: file:/tmp/xiaosi/hive_2017-04-19_15-57-05_466_914191914066790595/-local-10002/HashTable-Stage-1/MapJoin-u-11--.hashtable
2017-04-19 03:57:08     Upload 1 File to: file:/tmp/xiaosi/hive_2017-04-19_15-57-05_466_914191914066790595/-local-10002/HashTable-Stage-1/MapJoin-u-11--.hashtable File size: 876
2017-04-19 03:57:08     End of local task; Time Taken: 0.705 sec.
Execution completed successfully
Mapred Local Task Succeeded . Convert the Join into MapJoin
Mapred Local Task Succeeded . Convert the Join into MapJoin
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there's no reduce operator
...
Hadoop job information for Stage-1: number of mappers: 1; number of reducers: 0
2017-04-19 15:57:22,648 Stage-1 map = 0%,  reduce = 0%
2017-04-19 15:57:32,923 Stage-1 map = 100%,  reduce = 0%, Cumulative CPU 3.23 sec
2017-04-19 15:57:33,948 Stage-1 map = 100%,  reduce = 0%, Cumulative CPU 3.23 sec
MapReduce Total cumulative CPU time: 3 seconds 230 msec
Ended Job = job_1472052053889_13815596
MapReduce Jobs Launched:
Job 0: Map: 1   Cumulative CPU: 3.23 sec   HDFS Read: 59677056 HDFS Write: 588 SUCCESS
Total MapReduce CPU Time Spent: 3 seconds 230 msec
OK
```

#### 2. 启用自动转换

上面第二个语句不使用 MAPJOIN 提示，而是开启自动转选项：
```
set hive.auto.convert.join=true。
```
不同Hive版本，自动转换功能默认值是不同的，在0.11版本默认是关闭的，使用时需要开启，在2.1.0版本则是默认开启的。

在此，所有查询将被视为 MAPJOIN 查询，而提示用于特定查询：
```sql
SELECT o.entrance, o.gid, o.orderTime, o.businessType
FROM tmp_entrance_order o
JOIN tmp_entrance_order_user u
ON u.gid = o.gid;
```
输出信息如下：
```
2017-04-18 10:46:02     Starting to launch local task to process map join;      maximum memory = 514850816
2017-04-18 10:46:11     Processing rows:        8       Hashtable size: 8       Memory usage:   149205136       rate:   0.29
2017-04-18 10:46:11     Dump the hashtable into file: file:/tmp/xiaosi/hive_2017-04-18_10-45-49_973_1790466181163205947/-local-10002/HashTable-Stage-3/MapJoin-mapfile11--.hashtable
2017-04-18 10:46:11     Upload 1 File to: file:/tmp/xiaosi/hive_2017-04-18_10-45-49_973_1790466181163205947/-local-10002/HashTable-Stage-3/MapJoin-mapfile11--.hashtable File size: 876
2017-04-18 10:46:11     End of local task; Time Taken: 9.905 sec.
Execution completed successfully
Mapred Local Task Succeeded . Convert the Join into MapJoin
Mapred Local Task Succeeded . Convert the Join into MapJoin
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there's no reduce operator
...
Hadoop job information for Stage-3: number of mappers: 8; number of reducers: 0
2017-04-18 10:46:27,847 Stage-3 map = 0%,  reduce = 0%
2017-04-18 10:46:35,240 Stage-3 map = 13%,  reduce = 0%, Cumulative CPU 4.42 sec
...
2017-04-18 10:46:52,036 Stage-3 map = 100%,  reduce = 0%, Cumulative CPU 51.17 sec
MapReduce Total cumulative CPU time: 51 seconds 170 msec
Ended Job = job_1472052053889_13716990
MapReduce Jobs Launched:
Job 0: Map: 8   Cumulative CPU: 51.17 sec   HDFS Read: 36197529 HDFS Write: 588 SUCCESS
Total MapReduce CPU Time Spent: 51 seconds 170 msec
OK
```

下面设置 `set hive.auto.convert.join=false` ，然后再运行上述语句，输出信息如下：
```
Hadoop job information for Stage-1: number of mappers: 9; number of reducers: 1
2017-04-18 11:31:35,957 Stage-1 map = 0%,  reduce = 0%
2017-04-18 11:31:43,284 Stage-1 map = 11%,  reduce = 0%, Cumulative CPU 1.49 sec
...
2017-04-18 11:31:55,873 Stage-1 map = 100%,  reduce = 100%, Cumulative CPU 66.52 sec
MapReduce Total cumulative CPU time: 1 minutes 6 seconds 520 msec
Ended Job = job_1472052053889_13719609
MapReduce Jobs Launched:
Job 0: Map: 9  Reduce: 1   Cumulative CPU: 66.52 sec   HDFS Read: 36198090 HDFS Write: 588 SUCCESS
Total MapReduce CPU Time Spent: 1 minutes 6 seconds 520 msec
OK
```

### 3. MAPJOIN运行过程

将较小的表加载到内存中的哈希映射中，与更大表的键进行匹配。运行过程如下：

(1) Local work:
- 通过标准表扫描（包括过滤器和投影）从本地机器上的数据源读取记录
- 在内存中构建哈希表(hashtable)
- 将哈希表写入本地磁盘
- 将哈希表上传到HDFS
- 将哈希表添加到分布式缓存中

(2) Map task
- 从本地磁盘（分布式缓存）读取哈希表到内存
- 根据记录的键与哈希表进行匹配
- 组合匹配并输出

(3) No reduce task

### 4. MAPJOIN局限性

Hive 0.11之前的MAPJOIN实现有以下局限性：
- mapjoin操作符一次只能处理一个键; 也就是说，它可以执行多表连接，但只有在所有表在join时使用同一个键上（意思是说同一个表在不同join子句中使用同一一个key）。 （典型的星型模式连接不属于此类别。）
- Hints are cumbersome for users to apply correctly and auto conversion doesn't have enough logic to consistently predict if a MAPJOIN will fit into memory or not.
- 一个MAPJOIN链不会合并到一个只有Map的作业中，除非这个查询被写成一个mapjoin的级联序列（table，subquery（mapjoin（table，subquery ....））。自动转换不会产生一个只有Map的作业。
- 必须为每次运行查询生成mapjoin操作符的哈希表，其中包括将所有数据下载到Hive客户端计算机上以及上传生成的哈希表文件。

### 5. 星型模式连接

Hive 0.11中的优化器增强侧重于在星型模式配置中JOIN的处理效率。

### Optimize Chains of Map Joins

执行如下查询将生成两个单独的只有map的作业：
```
select /*+ MAPJOIN(time_dim, date_dim) */ count(*) from
store_sales
join time_dim on (ss_sold_time_sk = t_time_sk)
join date_dim on (ss_sold_date_sk = d_date_sk)
where t_hour = 8 and d_year = 2002
```

### Optimize Auto Join Conversion

自动转换启用时，就没有必要在查询中提供Map JOIN注释（`/*+ MAPJOIN(xxx) */`）。 可以通过两个配置参数来启用自动转换选项：
```
set hive.auto.convert.join.noconditionaltask = true;
set hive.auto.convert.join.noconditionaltask.size = 10000000;
```
`hive.auto.convert.join.noconditionaltask` 的默认值为true，表示启用自动转换。 （原来默认是false - 见HIVE-3784 - 但在Hive 0.11.0发布之前，被改为true，见HIVE-4146）


```sql
select count(*) from
store_sales
join time_dim on (ss_sold_time_sk = t_time_sk)
join date_dim on (ss_sold_date_sk = d_date_sk)
where t_hour = 8 and d_year = 2002
```

如果time_dim表和date_dim表大小满足配置规定大小，则各自的连接将转换为MapJoin。 如果表的大小总和满足配置规定大小，那么两个MapJoin会合并为一个MapJoin。 这样优化减少了MapReduce作业的数量，并显着提高了查询的执行速度。该示例也可以轻松地扩展到多路连接（ multi-way joins），并且能按我们预期运行。
