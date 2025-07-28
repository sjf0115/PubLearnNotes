根据导入的地方不一样，主要介绍下面几种方式:
- 从本地文件系统中导入数据到Hive表
- 从HDFS上导入数据到Hive表
- 从别的表中查询出相应的数据并导入到Hive表中

### 1. 本地文件系统导入 Hive 表中

#### 1.1 导入普通 Hive 表

##### 1.1.1 创建 Hive 普通表

```sql
CREATE TABLE IF NOT EXISTS order_uid_total(
  uid string,
  bucket_type string,
  file_name string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE;
```

##### 1.1.2 导入数据

```sql
load data local inpath '/home/xiaosi/adv/order_uid_total.txt' into table order_uid_total;
```

##### 1.1.3 查看数据

```sql
hive (test)> select * from order_uid_total where bucket_type = 'put' limit 10;
OK
868	put	uids.3_1
865	put	uids.3_1
DC8	put	uids.3_1
861	put	uids.3_1
867	put	uids.3_1
861	put	uids.3_1
868	put	uids.3_1
867	put	uids.3_1
867	put	uids.3_1
A00	put	uids.3_1
```

#### 1.2 导入 Hive 分区表

##### 1.2.1 创建分区表

```sql
CREATE TABLE IF NOT EXISTS order_uid_total_partition(
  uid string
)
PARTITIONED BY(bucket_type string, file_name string)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE;
```
##### 1.2.2 静态导入数据

```sql
load data local inpath '/home/xiaosi/adv/order_uid_total_partition.txt' into table order_uid_total_partition partition(bucket_type='put',file_name='uids_3_1');
```
##### 1.2.3 动态导入数据

如果表中有多个分区，按上面插入语句会要写很多的SQL，而且查询语句要对应上不同的分区，这样就插入语句用起来就会很繁琐。为了解决这个问题，Hive 中提供了动态分区插入的功能，它能根据分区字段的内容自动创建分区，并在每个分区插入相应的内容:
```sql
insert overwrite table order_uid_total_partition
partition (bucket_type, file_name)
select uid, bucket_type, file_name from order_uid_total;
```
如果直接运行上面代码，会报如下错误：
```
FAILED: SemanticException [Error 10096]: Dynamic partition strict mode requires at least one static partition column. To turn this off set hive.exec.dynamic.partition.mode=nonstrict
```
从上面错误提示中，我们知道我们需要设置分区动态导入模式：
```sql
set hive.exec.dynamic.partition.mode=nonstrict;
```
默认值为`strict`，设置完毕之后，再次导入数据即可。

> 备注
在SELECT子句的最后两个字段，必须对应前面partition (bucket_type, file_name)中指定的分区字段，包括顺序。

### 2. HDFS 上导入数据到 Hive 表

从本地文件系统中将数据导入到 Hive 表的过程中，其实是先将数据临时复制到 HDFS 的一个目录下，然后再将数据从那个临时目录下移动到对应的 Hive 表的数据目录里面。因此，我们可以直接从 HDFS 上的一个目录移动到相应 Hive 表的数据目录下，假设 HDFS 上有下面这个文件 `data/order_uid_total.txt`，具体的操作如下:
```sql
load data inpath 'data/order_uid_total.txt' overwrite into table order_uid_total;
```
相对比于从本地文件导入 Hive 表中，唯一的区别就是少了一个 local 关键词。local 表示文件位于本地文件系统上，如果没有 local 关键词，表示文件位于 HDFS 上。

### 3. 从别的表中查询出相应的数据导入到 Hive 表中

#### 3.1 普通 Hive 表

创建普通 Hive 表：
```sql
CREATE TABLE IF NOT EXISTS order_uid_total(
  uid string,
  bucket_type string,
  file_name string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE;
```
查询数据导入 Hive 表中
```sql
insert overwrite table order_uid_total
select uid, bucket_type, file_name from order_uid_total_partition;
```

#### 3.2 分区 Hive 表

创建分区 Hive 表:
```sql
CREATE TABLE IF NOT EXISTS order_uid_total_partition(
  uid string
)
PARTITIONED BY(bucket_type string, file_name string)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE;
```
查询数据导入Hive表中
```sql
insert overwrite table order_uid_total_partition
partition (bucket_type, file_name)
select uid, bucket_type, file_name from order_uid_total;
```
