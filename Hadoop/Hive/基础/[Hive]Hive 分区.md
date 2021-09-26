---
layout: post
author: sjf0115
title: Hive 分区
date: 2018-07-01 19:16:01
tags:
  - Hive

categories: Hive
permalink: hive-base-how-to-use-partitions
---

```
set hive.exec.dynamic.partition=true;
set hive.exec.dynamic.partition.mode=nonstrict;
set hive.exec.max.dynamic.partitions.pernode=1000;
set hive.enforce.bucketing = true;
```
### 1. 静态分区

#### 1.1 分区操作
(1) 创建分区
下面例子中以日期为分区：
```sql
ALTER TABLE people ADD IF NOT EXISTS PARTITION(dt='20180701') LOCATION 'day=20180701';
```
(2) 查看分区
```sql
SHOW PARTITIONS people;
```
(3) 删除分区
```sql
ALTER TABLE people DROP PARTITION (dt='20180701');
```
(4) 修改分区:
```sql
ALTER TABLE people PARTITION (dt='20180701') SET LOCATION "new location";
ALTER TABLE people PARTITION (dt='20180701') RENAME TO PARTITION (dt='20180702');
```
(5) 添加多个分区
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS people (
  line string
)
PARTITIONED BY(
  dt string,
  type string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
LOCATION '/user/xiaosi/tmp/people';

ALTER TABLE people add partition(dt='20180701',type='old') location 'day=20180701/type=old';
ALTER TABLE people add partition(dt='20180701',type='new') location 'day=20180701/type=new';
```
(6) 查看分区数据路径:
```
describe formatted people partition (dt=20180101);
```

### 2. 动态分区

#### 2.1 配置参数

在使用动态分区之前,我们要进行一些参数的配置.

hive.exec.dynamic.partition

默认值：false

是否开启动态分区功能，默认false关闭。

使用动态分区时候，该参数必须设置成true;

hive.exec.dynamic.partition.mode

默认值：strict

动态分区的模式，默认strict，表示必须指定至少一个分区为静态分区，nonstrict模式表示允许所有的分区字段都可以使用动态分区。

一般需要设置为nonstrict

hive.exec.max.dynamic.partitions.pernode

默认值：100

在每个执行MR的节点上，最大可以创建多少个动态分区。

该参数需要根据实际的数据来设定。

比如：源数据中包含了一年的数据，即day字段有365个值，那么该参数就需要设置成大于365，如果使用默认值100，则会报错。

hive.exec.max.dynamic.partitions

默认值：1000

在所有执行MR的节点上，最大一共可以创建多少个动态分区。

同上参数解释。

hive.exec.max.created.files

默认值：100000

整个MR Job中，最大可以创建多少个HDFS文件。

一般默认值足够了，除非你的数据量非常大，需要创建的文件数大于100000，可根据实际情况加以调整。

hive.error.on.empty.partition
默认值：false

当有空分区生成时，是否抛出异常。

#### 动态分区插入

前面所说的语法中还是有一个问题，即：如果需要创建非常多的分区，那么用户就需要写非常多的SQL！不过幸运的是，Hive提供了一个动态分区功能，其可以基于查询参数推断出需要创建的分区名称。相比之下，到目前为止我们所看到的都是静态分区。请看如下对前面例子修改后的句子：
```sql
INSERT OVERWRITE TABLE people_partition
PARTITION (country, state)
SELECT '20180628', id, name, country_name, state_name
FROM people
WHERE ...
```
Hive根据SELECT语句中最后2列来确定分区字段country和state的值。这就是为什么在表people中我们使用了不同的命名，就是为了强调源表字段值和输出分区值之间的关系是根据位置而不是根据命名来匹配的。

假设表people中共有100个国家和州的话，执行完上面查询后，表people_partition就将会有100个分区！

用户也可以混合使用动态和静态分区。如下这个例子中指定了country字段的值为静态的US，而分区字段state是动态值：
```sql
INSERT OVERWRITE TABLE people_partition
PARTITION (country = 'US', state)
SELECT '20180628', id, name, country_name, state_name
FROM people p
WHERE p.state_name = 'US';
```
静态分区键必须出现在动态分区键之前。

动态分区功能默认情况下没有开启。开启后，默认是以'严格'模式执行的，在这种模式下要求至少有一列分区字段是静态的。这有助于阻止因设计错误导致查询产生大量的分区。例如，用户可能错误地使用时间戳作为分区字段，然后导致每秒都对应一个分区！而用户也许是期望按照天或者按照小时进行划分的。还有一些其他相关属性值用于限制资源利用。表5-1描述了这些属性。

因此，作为例子演示，前面我们使用的第一个使用动态分区的例子看上去应该是像下面这个样子的，这里我们不过在使用前设置了一些期望的属性：
```sql
set hive.exec.dynamic.partition=true;
set hive.exec.dynamic.partition.mode=nonstrict;
set hive.exec.max.dynamic.partitions.pernode=1000;

INSERT OVERWRITE TABLE people_partition
PARTITION (country, state)
SELECT '20180628', id, name, country_name, state_name
FROM people
WHERE ...
```
