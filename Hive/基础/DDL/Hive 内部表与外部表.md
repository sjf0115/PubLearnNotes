---
layout: post
author: sjf0115
title: Hive 内部表与外部表
date: 2017-12-08 19:16:01
tags:
  - Hive

categories: Hive
permalink: hive-managed-table-external-table
---

托管表(内部表)和外部表是`Hive`中的两种不同类型的表，在这篇文章中，我们将讨论`Hive`中表的类型以及它们之间的差异以及如何创建这些表以及何时将这些表用于特定的数据集。

### 1. 内部表

托管表(`Managed TABLE`)也称为内部表(`Internal TABLE`)。这是Hive中的默认表。当我们在 Hive 中创建一个表，没有指定为外部表时，默认情况下我们创建的是一个内部表。如果我们创建一个内部表，那么表将在 `HDFS` 中的特定位置创建。默认情况下，表数据将在 `HDFS` 的 `/usr/hive/warehouse` 目录中创建。如果我们删除了一个内部表，那么这个表的表数据和元数据都将从 `HDFS` 中删除。

#### 1.1 创建表

我们可以用下面的语句在 Hive 里面创建一个内部表：
```sql
CREATE  TABLE IF NOT EXISTS tb_station_coordinate(
  station string,
  lon string,
  lat string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';
```
我们已经成功创建了表并使用如下命令检查表的详细信息：
```
hive> describe formatted tb_station_coordinate;
OK
# col_name            	data_type           	comment             

station             	string              	                    
lon                 	string              	                    
lat                 	string              	                    

# Detailed Table Information	 	 
Database:           	default             	 
Owner:              	xiaosi              	 
CreateTime:         	Tue Dec 12 17:42:09 CST 2017	 
LastAccessTime:     	UNKNOWN             	 
Retention:          	0                   	 
Location:           	hdfs://localhost:9000/user/hive/warehouse/tb_station_coordinate	 
Table Type:         	MANAGED_TABLE       	 
Table Parameters:	 	 
	COLUMN_STATS_ACCURATE	{\"BASIC_STATS\":\"true\"}
	numFiles            	0                   
	numRows             	0                   
	rawDataSize         	0                   
	totalSize           	0                   
	transient_lastDdlTime	1513071729          

# Storage Information	 	 
SerDe Library:      	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	 
InputFormat:        	org.apache.hadoop.mapred.TextInputFormat	 
OutputFormat:       	org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat	 
Compressed:         	No                  	 
Num Buckets:        	-1                  	 
Bucket Columns:     	[]                  	 
Sort Columns:       	[]                  	 
Storage Desc Params:	 	 
	field.delim         	,                   
	serialization.format	,                   
Time taken: 0.16 seconds, Fetched: 33 row(s)
```
从上面我们可以看到表的类型`Table Type`为`MANAGED_TABLE`，即我们创建了一个托管表(内部表)。

#### 1.2 导入数据

我们使用如下命令将一个样本数据集导入到表中：
```
hive> load data local inpath '/home/xiaosi/station_coordinate.txt' overwrite into table tb_station_coordinate;
Loading data to table default.tb_station_coordinate
OK
Time taken: 2.418 seconds
```
如果我们在`HDFS`的目录`/user/hive/warehouse/tb_station_coordinate`查看，我们可以得到表中的内容：
```
xiaosi@yoona:~$ hadoop fs -ls  /user/hive/warehouse/tb_station_coordinate
Found 1 items
-rwxr-xr-x   1 xiaosi supergroup        374 2017-12-12 17:50 /user/hive/warehouse/tb_station_coordinate/station_coordinate.txt
xiaosi@yoona:~$
xiaosi@yoona:~$
xiaosi@yoona:~$ hadoop fs -text  /user/hive/warehouse/tb_station_coordinate/station_coordinate.txt
桂林北站,110.302159,25.329024
杭州东站,120.213116,30.290998
山海关站,119.767555,40.000793
武昌站,114.317576,30.528401
北京南站,116.378875,39.865052
...
```


>
`/home/xiaosi/station_coordinate.txt`是本地文件系统路径。从上面的输出我们可以看到数据是从本地的这个路径复制到`HDFS`上的`/user/hive/warehouse/tb_station_coordinate/`目录下。
为什么会自动复制到`HDFS`这个目录下呢？这个是由`Hive`的配置文件设置的。在`Hive`的`${HIVE_HOME}/conf/hive-site.xml`配置文件中指定，`hive.metastore.warehouse.dir`属性指向的就是`Hive`表数据存放的路径(在这配置的是`/user/hive/warehouse/`)。`Hive`每创建一个表都会在`hive.metastore.warehouse.dir`指向的目录下以表名创建一个文件夹，所有属于这个表的数据都存放在这个文件夹里面`/user/hive/warehouse/tb_station_coordinate`。

#### 1.3 删除表

现在让我们使用如下命令删除上面创建的表:
```
hive> drop table tb_station_coordinate;
Moved: 'hdfs://localhost:9000/user/hive/warehouse/tb_station_coordinate' to trash at: hdfs://localhost:9000/user/xiaosi/.Trash/Current
OK
Time taken: 1.327 seconds
```
从上面的输出我们可以得知，原来属于`tb_station_coordinate`表的数据被移到`hdfs://localhost:9000/user/xiaosi/.Trash/Current`文件夹中(如果你的Hadoop没有采用回收站机制，那么删除操作将会把属于该表的所有数据全部删除)(回收站机制请参阅:[Hadoop Trash回收站使用指南](https://smartsi.blog.csdn.net/article/details/78869778)）。

如果我们在`HDFS`的目录`/user/hive/warehouse/tb_station_coordinate`查看：
```
xiaosi@yoona:~$ hadoop fs -ls  /user/hive/warehouse/tb_station_coordinate
ls: `/user/hive/warehouse/tb_station_coordinate': No such file or directory
```
你可以看到输出为`No such file or directory`，因为表及其内容都从HDFS从删除了。

### 2. 外部表

当数据在Hive之外使用时，创建外部表(`EXTERNAL TABLE`)来在外部使用。无论何时我们想要删除表的元数据，并且想保留表中的数据，我们使用外部表。外部表只删除表的`schema`。

#### 2.1 外部普通表

我们使用如下命令创建一个外部表：
```
CREATE EXTERNAL TABLE IF NOT EXISTS tb_station_coordinate(
  station string,
  lon string,
  lat string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',';
```
我们现在已经成功创建了外部表。我们使用如下命令检查关于表的细节：
```
hive> describe formatted tb_station_coordinate;
OK
# col_name            	data_type           	comment             

station             	string              	                    
lon                 	string              	                    
lat                 	string              	                    

# Detailed Table Information	 	 
Database:           	default             	 
Owner:              	xiaosi              	 
CreateTime:         	Tue Dec 12 18:16:13 CST 2017	 
LastAccessTime:     	UNKNOWN             	 
Retention:          	0                   	 
Location:           	hdfs://localhost:9000/user/hive/warehouse/tb_station_coordinate	 
Table Type:         	EXTERNAL_TABLE      	 
Table Parameters:	 	 
	COLUMN_STATS_ACCURATE	{\"BASIC_STATS\":\"true\"}
	EXTERNAL            	TRUE                
	numFiles            	0                   
	numRows             	0                   
	rawDataSize         	0                   
	totalSize           	0                   
	transient_lastDdlTime	1513073773          

# Storage Information	 	 
SerDe Library:      	org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe	 
InputFormat:        	org.apache.hadoop.mapred.TextInputFormat	 
OutputFormat:       	org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat	 
Compressed:         	No                  	 
Num Buckets:        	-1                  	 
Bucket Columns:     	[]                  	 
Sort Columns:       	[]                  	 
Storage Desc Params:	 	 
	field.delim         	,                   
	serialization.format	,                   
Time taken: 0.132 seconds, Fetched: 34 row(s)

```
从上面我们可以看到表的类型`Table Type`为`EXTERNAL_TABLE`，即我们创建了一个外部表。

#### 2.2 导入数据

我们使用如下命令将一个样本数据集导入到表中：
```
hive> load data local inpath '/home/xiaosi/station_coordinate.txt' overwrite into table tb_station_coordinate;
Loading data to table default.tb_station_coordinate
OK
Time taken: 2.418 seconds
```

如果我们在`HDFS`的目录`/user/hive/warehouse/tb_station_coordinate`查看，我们可以得到表中的内容：
```
xiaosi@yoona:~$ hadoop fs -ls  /user/hive/warehouse/tb_station_coordinate
Found 1 items
-rwxr-xr-x   1 xiaosi supergroup        374 2017-12-12 18:19 /user/hive/warehouse/tb_station_coordinate/station_coordinate.txt
xiaosi@yoona:~$
xiaosi@yoona:~$
xiaosi@yoona:~$ hadoop fs -text  /user/hive/warehouse/tb_station_coordinate/station_coordinate.txt
桂林北站,110.302159,25.329024
杭州东站,120.213116,30.290998
山海关站,119.767555,40.000793
武昌站,114.317576,30.528401
...
```

#### 2.3 删除表

现在让我们使用如下命令删除上面创建的表:
```
hive> drop table tb_station_coordinate;
OK
Time taken: 0.174 seconds
hive>
```
我们的Hadoop已经开启了回收站机制，但是删除操作并没有将数据进行删除，不像删除内部表一样，输出`Moved: 'hdfs://localhost:9000/user/hive/warehouse/tb_station_coordinate' to trash at: hdfs://localhost:9000/user/xiaosi/.Trash/Current`(回收站机制请参阅:[Hadoop Trash回收站使用指南](http://smartying.club/2017/12/07/Hadoop/Hadoop%20Trash%E5%9B%9E%E6%94%B6%E7%AB%99%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/))。为了验证我们真的没有删除数据，我们在HDFS目录下查看数据:
```
xiaosi@yoona:~$ hadoop fs -ls  /user/hive/warehouse/tb_station_coordinate
Found 1 items
-rwxr-xr-x   1 xiaosi supergroup        374 2017-12-12 18:19 /user/hive/warehouse/tb_station_coordinate/station_coordinate.txt
xiaosi@yoona:~$
xiaosi@yoona:~$ hadoop fs -text  /user/hive/warehouse/tb_station_coordinate/station_coordinate.txt
桂林北站,110.302159,25.329024
杭州东站,120.213116,30.290998
山海关站,119.767555,40.000793
武昌站,114.317576,30.528401
北京南站,116.378875,39.865052
...
```
你可以看到表中的数据仍然在HDFS中。所以我们得知如果我们创建一个外部表，在删除表之后，只有与表相关的元数据被删除，而不会删除表的内容。

#### 2.4 创建表指定外部目录

只有当你的数据在`/user/hive/warehouse`目录中时，上述方法才能有效。但是，如果你的数据在另一个位置，如果你删除该表，数据也将被删除。所以在这种情况下，你需要在创建表时设置数据的外部位置，如下所示：
```
CREATE EXTERNAL TABLE IF NOT EXISTS tb_station_coordinate(
  station string,
  lon string,
  lat string
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION '/user/xiaosi/test/coordinate/';
```

>备注:
你也可以通过在创建表时设置数据存储位置来创建一个内部表。但是，如果删除表，数据将被删除。

> 如果你想要创建外部表，需要在创建表的时候加上 EXTERNAL 关键字，同时指定外部表存放数据的路径(例如2.4所示)，也可以不指定外部表的存放路径(例如2.3所示)，这样Hive将在HDFS上的/user/hive/warehouse/目录下以外部表的表名创建一个文件夹，并将属于这个表的数据存放在这里。


### 3. 使用场景

#### 3.1 内部表

- 数据是临时的
- 希望使用`Hive`来管理表和数据的生命周期
- 删除后不想要数据

#### 3.2 外部表

- 这些数据也在`Hive`之外使用。
- `Hive`不管理数据和权限设置以及目录等，需要你有另一个程序或过程来做这些事情
- 不是基于现有表(AS SELECT)来创建的表
- 可以创建表并使用相同的模式并指向数据的位置




参考:https://acadgild.com/blog/managed-and-external-tables-in-hive/

https://www.linkedin.com/pulse/internal-external-tables-hadoop-hive-big-data-island-amandeep-modgil
