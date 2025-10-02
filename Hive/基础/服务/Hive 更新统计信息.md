## 1. 查看统计信息

使用 DESC FORMATTED 命令查看表的详细统计信息：
```sql
hive> DESC FORMATTED tb_order;
OK
# col_name            	data_type           	comment
id                  	string              	??id
user_id             	string              	??id
product_id          	string              	??id
province_id         	string              	??id
create_time         	string              	????
product_num         	int                 	????
total_amount        	decimal(16,2)       	????

# Partition Information
# col_name            	data_type           	comment
dt                  	string

# Detailed Table Information
Database:           	default
OwnerType:          	USER
Owner:              	smartsi
CreateTime:         	Thu Oct 02 07:01:03 CST 2025
LastAccessTime:     	UNKNOWN
Retention:          	0
Location:           	hdfs://localhost:9000/user/hive/warehouse/tb_order
Table Type:         	MANAGED_TABLE
Table Parameters:
	bucketing_version   	2
	numFiles            	1
	numPartitions       	1
	numRows             	0
	rawDataSize         	0
	totalSize           	1176009934
	transient_lastDdlTime	1759359663

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
	line.delim          	\n
	serialization.format	,
Time taken: 0.083 seconds, Fetched: 43 row(s)
```
重点关注以下字段：
```
numFiles            	1
numPartitions       	1
numRows             	0
rawDataSize         	0
totalSize           	1176009934
transient_lastDdlTime	1759359663
```


## 2. 手动更新统计信息

可以使用 `ANALYZE TABLE xxx COMPUTE STATISTICS` 命令手动执行更新统计信息：
```
hive> ANALYZE TABLE tb_order COMPUTE STATISTICS;
Query ID = smartsi_20251002170453_6b8daac6-7545-4b06-9b89-59246d8581fb
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there's no reduce operator
Starting Job = job_1759320196617_0008, Tracking URL = http://smarsi:8088/proxy/application_1759320196617_0008/
Kill Command = /opt/workspace/hadoop/bin/mapred job  -kill job_1759320196617_0008
Hadoop job information for Stage-0: number of mappers: 5; number of reducers: 0
2025-10-02 17:04:59,241 Stage-0 map = 0%,  reduce = 0%
2025-10-02 17:05:06,018 Stage-0 map = 20%,  reduce = 0%
2025-10-02 17:05:07,097 Stage-0 map = 100%,  reduce = 0%
Ended Job = job_1759320196617_0008
MapReduce Jobs Launched:
Stage-Stage-0: Map: 5   HDFS Read: 1176062879 HDFS Write: 489 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
Time taken: 15.191 seconds
```

## 3. 验证

```
hive> DESC FORMATTED tb_order;
OK
# col_name            	data_type           	comment
id                  	string              	??id
user_id             	string              	??id
product_id          	string              	??id
province_id         	string              	??id
create_time         	string              	????
product_num         	int                 	????
total_amount        	decimal(16,2)       	????

# Partition Information
# col_name            	data_type           	comment
dt                  	string

# Detailed Table Information
Database:           	default
OwnerType:          	USER
Owner:              	smartsi
CreateTime:         	Thu Oct 02 07:01:03 CST 2025
LastAccessTime:     	UNKNOWN
Retention:          	0
Location:           	hdfs://localhost:9000/user/hive/warehouse/tb_order
Table Type:         	MANAGED_TABLE
Table Parameters:
	COLUMN_STATS_ACCURATE	{\"BASIC_STATS\":\"true\"}
	bucketing_version   	2
	numFiles            	1
	numPartitions       	1
	numRows             	20000000
	rawDataSize         	1136009934
	totalSize           	1176009934
	transient_lastDdlTime	1759359663

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
	line.delim          	\n
	serialization.format	,
Time taken: 0.174 seconds, Fetched: 44 row(s)
```
发现 numRows 和 rawDataSize 已经更新了。
