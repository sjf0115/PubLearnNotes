### 1. javax.jdo.option.ConnectionURL 与 javax.jdo.ConnectionDriver

Alongside javax.jdo.option.ConnectionURL and javax.jdo.ConnectionDriver they are intended to connect to Hive's metastore. Are you planning on using MySQL or another database as metastore? You only need to set these if you're not using Hive's standard metastore (Derby).

An example of how to set up hive-site.xml when using MySQL:
```
 <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:mysql://localhost:3306/<databasename></value>
 </property>
 <property>
    <name>jaavax.jdo.ConnectionDriver</name>
    <value>com.mysql.jdbc.Driver</value>
 </property>
 <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value> <your database user> </value>
 </property>
 <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value> <your database user password> </value>
 </property>
```
If you're indeed planning on running another database as metastore don't forget to create a database and run the scripts in $HIVE_HOME/scripts/metastore/upgrade/.

The easiest to do this latter in my opinion is to first create your database in the MySQL shell then exit the shell and use this command from your shell: mysql -u <username> -p -h <host> <databasename> < <sql script>

By the way, I think it's better to create a Hadoop specific database user instead of using your root user.

### 2. 在提示符里面显示当前所在的数据库（Hive 0.8版本以及之后的版本才支持此功能）
```
<property>
    <name>hive.cli.print.current.db</name>
    <value>true</value>
    <description>Whether to include the current database in the Hive prompt.</description>
</property>
``
```
hive (default)> use test_db;
OK
Time taken: 0.033 seconds
hive (test_db)> 
```

### 3. 如果表中数据以及分区个数都非常大，执行这样一个包含所有分区的查询会触发一个巨大的MapReduce任务。将Hive设置为"strict(严格)"模式，这样如果对分区表进行查询而where子句没有加分区过滤的话，将会禁止提交这个任务。
```
<property>
    <name>hive.mapred.mode</name>
    <value>strict</value>
    <description>Deprecated; use hive.strict.checks.* settings instead.</description>
</property>
```
