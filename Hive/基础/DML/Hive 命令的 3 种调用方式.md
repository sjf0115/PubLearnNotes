### 1. 多语句执行 执行 HQL 脚本
```sql
hive –f  /root/shell/hive-script.sql
```
`hive-script.sql` 类似于script一样，直接写查询命令就行。

hive-script.sql 是 hive 语句的集合：
```sql
xiaosi@yoona：～$ vim hive_script.sql
select * from search_click;
select count(*) from search_click;
```
这里可以和静音模式 `-S` 联合使用，通过第三方程序调用，第三方程序通过hive的标准输出获取结果集。
```
# 不会显示 mapreduce 的操作过程
$HIVE_HOME/bin/hive -S -f /home/my/hive-script.sql
```

### 2. 短语句执行 命令行执行 HQL
```
hive -e 'sql语句'
```
例如执行：
```sql
xiaosi@yoona:~$ hive -e 'select * from t1'
```
静音模式：（不会显示 mapreduce 的操作过程）
```sql
xiaosi@yoona:~$ hive -S -e 'select * from t1'
```
导出数据：
```sql
xiaosi@yoona:~$ hive -e 'select * from t1'  > test.txt
```

### 3. 交互模式

直接使用 hive 命令：
```sql
#hive     启动
hive>quit;     退出hive
hive> show databases;   查看数据库
hive> create database test;  创建数据库
hive> use default;    使用哪个数据库
hive>create table t1 (key string); 创建表
```
