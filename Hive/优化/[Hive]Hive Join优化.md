

### 1. 对Hive优化器的改进

> 此处描述的Join优化已添加到Hive 0.11.0版中。

本文描述了对 Hive 查询执行计划的优化，以提高 Join 的效率同时降低用户对 `hints` 的需求。Hive 能够自动识别各种Case并对其进行优化。Hive 0.11对优化器进行了优化：
(1) 其中一方能够放入内存的 Join。新的优化方案：
- 能够放入内存的一方加载到内存作为哈希表
- 只需要扫描大表
- 事实表占用内存较小

(2) 星型 Join

(3) 许多情况下不再需要`hints`。

(4) 优化器会自动使用 MAPJOIN。

### 2. Star Schema Example

A simple schema for decision support systems or data warehouses is the star schema, where events are collected in large fact tables, while smaller supporting tables (dimensions) are used to describe the data.

The TPC DS is an example of such a schema. It models a typical retail warehouse where the events are sales and typical dimensions are date of sale, time of sale, or demographic of the purchasing party. Typical queries aggregate and filter fact tables along properties in the dimension tables.

```sql
Select count(*) cnt
From store_sales ss
     join household_demographics hd on (ss.ss_hdemo_sk = hd.hd_demo_sk)
     join time_dim t on (ss.ss_sold_time_sk = t.t_time_sk)
     join store s on (s.s_store_sk = ss.ss_store_sk)
Where
     t.t_hour = 8
     t.t_minute >= 30
     hd.hd_dep_count = 2
order by cnt;
```
### 3. 先前支持的MAPJOIN

Hive 支持 MAPJOIN，它非常适合这种情况 - 足够小能够加载到内存中。在版本0.11之前，可以通过优化器 `hints`　调用MAPJOIN：
```sql
select /*+ MAPJOIN(time_dim) */ count(*)
from store_sales
join time_dim
on (ss_sold_time_sk = t_time_sk)
```
或通过 Join 自动转换：
```sql
set hive.auto.convert.join=true;
select count(*)
from store_sales
join time_dim
on (ss_sold_time_sk = t_time_sk)
```
Hive 0.10.0 版本之前 `hive.auto.convert.join` 的默认值为 false。Hive 0.11.0 版本将默认值更改为 true（HIVE-3297）。

> hive-default.xml.template 在Hive 0.11.0 到 0.13.1 版本中错误地将默认值设置为false。

MAPJOINs 通过将较小的表加载到内存中以哈希映射存储进行处理，并与大表的键进行匹配。先前实现如下分工：

(1) Local work:
- 通过标准表扫描（包括过滤器和投影）从本地机器上的数据源上读取记录
- 在内存中构建哈希表(hashtable)
- 将哈希表写入本地磁盘
- 将哈希表上传到 HDFS
- 将哈希表添加到分布式缓存中

(2) Map task
- 从本地磁盘（分布式缓存）读取哈希表加载到内存
- 根据记录的 key 与哈希表进行匹配
- 组合匹配的结果并输出

(3) No reduce task

#### 3.1 先前实现的局限性

Hive 0.11之前的 MAPJOIN 实现有以下局限性：
- mapjoin操作符一次只能处理一个 key；也就是说，它可以执行多表连接，但前提是所有表都在同一个 key 上进行连接。（典型的星型模式连接不属于此类别。）
- 对于用户正确使用 `hints` 是比较麻烦的，并且自动转换没有足够的逻辑来预测 MAPJOIN 是否能够装入内存。
- 一个 MAPJOIN 链不会合并到一个只有 Map 的作业，除非写成一个 级联的 mapjoin（table，subquery（mapjoin（table，subquery ....））。自动转换不会产生一个只有 Map 的作业。(unless the query is written as a cascading sequence of mapjoin)
- mapjoin 操作符都会为每次查询生成哈希表，其中包括将所有数据下载到Hive客户端机器上以及上传生成的哈希表文件。

### 4. 增强星型Join

#### 4.1 Optimize Chains of Map Joins
##### 4.1.1 Current and Future Optimizations
#### 4.2 Optimize Auto Join Conversion
Current Optimization
Auto Conversion to SMB Map Join
SMB Join across Tables with Different Keys
Generate Hash Tables on the Task Side
Pros and Cons of Client-Side Hash Tables
Task-Side Generation of Hash Tables
Further Options for Optimization









































原文:https://cwiki.apache.org/confluence/display/Hive/LanguageManual+JoinOptimization#LanguageManualJoinOptimization-ImprovementstotheHiveOptimizer
