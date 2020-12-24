### 1. 多语句执行 执行HQL脚本
```
hive –f  /root/shell/hive-script.sql
```
hive-script.sql类似于script一样，直接写查询命令就行。

hive-script.sql是hive 语句的集合：
```
xiaosi@yoona：～$ vim hive_script.sql
select * from search_click;
select count(*) from search_click;
```
这里可以和静音模式-S联合使用，通过第三方程序调用，第三方程序通过hive的标准输出获取结果集。
```
# 不会显示mapreduct的操作过程
$HIVE_HOME/bin/hive -S -f /home/my/hive-script.sql
```
### 2. 短语句执行 命令行执行HQL
```
hive -e  'sql语句'
```
例如执行：
```
xiaosi@yoona:~$ hive -e 'select * from t1'
```
静音模式：（不会显示mapreduce的操作过程）
```
xiaosi@yoona:~$ hive -S -e 'select * from t1'
```
导出数据：
```
xiaosi@yoona:~$ hive -e 'select * from t1'  > test.txt
```

### 3. 交互模式

直接使用hive命令：
```
#hive     启动
hive>quit;     退出hive
hive> show databases;   查看数据库
hive> create database test;  创建数据库
hive> use default;    使用哪个数据库
hive>create table t1 (key string); 创建表
```
