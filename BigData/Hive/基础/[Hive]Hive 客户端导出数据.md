根据导出的地方不一样，将这些方式分为三种:
- 导出到本地文件系统中
- 导出到HDFS中
- 导出到Hive的另一个表中

### 1. 导出到本地文件系统中
```sql
INSERT OVERWRITE LOCAL DIRECTORY '/home/xiaosi/data/client_behavior'
SELECT * FROM client_behavior WHERE dt = '2017-08-16' LIMIT 2000;
```
这条HQL的执行需要启用Mapreduce作业，运行完这条语句之后，将会在本地文件系统`/home/xiaosi/data/client_behavior`目录下生成文件名称为`000000_2`的文件，这是由Reduce产生的结果，我们可以看看这个文件的内容：
```sql
ll /home/xiaosi/data/client_behavior
total 536
-rw-r--r-- 1 wirelessdev wirelessdev 546233 Aug 17 19:46 000000_2
```
在Hive0.11.0版本之前，当用户将Hive查询结果输出到文件中时，用户不能指定列的分割符，默认为\x01:
```
cat /home/xiaosi/data/client_behavior/000000_2 |awk -F"\x01" '{print $1}' | less
2017-08-16
2017-08-16
2017-08-16
2017-08-16
2017-08-16
2017-08-16
2017-08-16
...
```
在Hive0.11.0版本之后，引入了新特性，用户可以指定列和行的分隔符:
```sql
INSERT OVERWRITE LOCAL DIRECTORY '/home/xiaosi/data/client_behavior'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
SELECT * FROM client_behavior WHERE dt = '2017-08-16' LIMIT 2000;
```
查看数据:
```
cat /home/xiaosi/data/client_behavior/000000_2 | awk -F"\t" '{print $1}' | less
2017-08-16
2017-08-16
2017-08-16
2017-08-16
2017-08-16
...
```

### 2. 导出到HDFS中

导出到HDFS中，与导出到本地文件系统中思路一致，只是少了一个`LOCAL`关键字：
```
INSERT OVERWRITE DIRECTORY 'tmp/data_group/test/client_behavior'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
SELECT * FROM client_behavior WHERE dt = '2017-08-16' LIMIT 2000;
```
上面代码将会导出查询数据到HDFS的`tmp/data_group/test/client_behavior`目录下。


### 3. 导出到Hive的另一个表中

导出到Hive中的另一个表中，也是Hive的数据导入方式：
```
INSERT INTO TABLE client_behavior_copy
SELECT * FROM client_behavior WHERE dt = '2017-08-16' LIMIT 2000;
```
**备注**
```
如果想要导入数据到另一个表中，则这个表必须已经创建成功
```
