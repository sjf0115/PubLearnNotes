### 1. 缺少MySQL驱动包

#### 1.1 问题描述
```java
Caused by: org.datanucleus.store.rdbms.connectionpool.DatastoreDriverNotFoundException: The specified datastore driver ("com.mysql.jdbc.Driver") was not found in the CLASSPATH. Please check your CLASSPATH specification, and the name of the driver.
	at org.datanucleus.store.rdbms.connectionpool.AbstractConnectionPoolFactory.loadDriver(AbstractConnectionPoolFactory.java:58)
	at org.datanucleus.store.rdbms.connectionpool.BoneCPConnectionPoolFactory.createConnectionPool(BoneCPConnectionPoolFactory.java:54)
	at org.datanucleus.store.rdbms.ConnectionFactoryImpl.generateDataSources(ConnectionFactoryImpl.java:213)
```
#### 1.2. 解决方案

上述问题很可能是缺少mysql的jar包，下载mysql-connector-java-5.1.32.tar.gz，复制到hive的lib目录下：
```
xiaosi@yoona:~$ cp mysql-connector-java-5.1.34-bin.jar opt/hive-2.1.0/lib/
```

### 2. 元数据库mysql初始化

#### 2.1 问题描述

运行./hive脚本时，无法进入，报错：
```java
Exception in thread "main" java.lang.RuntimeException: Hive metastore database is not initialized. Please use schematool (e.g. ./schematool -initSchema -dbType ...) to create the schema. If needed, dont forget to include the option to auto-create the underlying database in your JDBC connection string (e.g. ?createDatabaseIfNotExist=true for mysql)
```
#### 2.2 解决方案

在scripts目录下运行  schematool -initSchema -dbType mysql命令进行Hive元数据库的初始化：
```
xiaosi@yoona:~/opt/hive-2.1.0/scripts$  schematool -initSchema -dbType mysql
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/home/xiaosi/opt/hive-2.1.0/lib/log4j-slf4j-impl-2.4.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/home/xiaosi/opt/hadoop-2.7.3/share/hadoop/common/lib/slf4j-log4j12-1.7.10.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Metastore connection URL:	 jdbc:mysql://localhost:3306/hive_meta?createDatabaseIfNotExist=true
Metastore Connection Driver :	 com.mysql.jdbc.Driver
Metastore connection User:	 root
Starting metastore schema initialization to 2.1.0
Initialization script hive-schema-2.1.0.mysql.sql
Initialization script completed
schemaTool completed
```

### 3. Relative path in absolute URI

#### 3.1 问题描述
```
Exception in thread "main" java.lang.IllegalArgumentException: java.net.URISyntaxException: Relative path in absolute URI: ${system:java.io.tmpdir%7D/$%7Bsystem:user.name%7D
...
Caused by: java.net.URISyntaxException: Relative path in absolute URI: ${system:java.io.tmpdir%7D/$%7Bsystem:user.name%7D
	at java.net.URI.checkPath(URI.java:1823)
	at java.net.URI.<init>(URI.java:745)
	at org.apache.hadoop.fs.Path.initialize(Path.java:202)
	... 12 more
```

#### 3.2 解决方案

产生上述问题的原因是使用了没有配置的变量，解决此问题只需在配置文件hive-site.xml中配置system:user.name和system:java.io.tmpdir两个变量，配置文件中就可以使用这两个变量：
```xml
<property>
    <name>system:user.name</name>
    <value>wy</value>
</property>
<property>
    <name>system:java.io.tmpdir</name>
    <value>/tmp/hive/</value>
</property>
```

### 4. 拒绝连接

#### 4.1 问题描述
```java
exception: java.net.ConnectException: 拒绝连接; For more details see:  http://wiki.apache.org/hadoop/ConnectionRefused
...
Caused by: java.net.ConnectException: Call From Qunar/127.0.0.1 to localhost:9000 failed on connection exception: java.net.ConnectException: 拒绝连接; For more details see:  http://wiki.apache.org/hadoop/ConnectionRefused
...
Caused by: java.net.ConnectException: 拒绝连接
	at sun.nio.ch.SocketChannelImpl.checkConnect(Native Method)
	at sun.nio.ch.SocketChannelImpl.finishConnect(SocketChannelImpl.java:717)
	at org.apache.hadoop.net.SocketIOWithTimeout.connect(SocketIOWithTimeout.java:206)
	at org.apache.hadoop.net.NetUtils.connect(NetUtils.java:531)
	at org.apache.hadoop.net.NetUtils.connect(NetUtils.java:495)
	at org.apache.hadoop.ipc.Client$Connection.setupConnection(Client.java:614)
	at org.apache.hadoop.ipc.Client$Connection.setupIOstreams(Client.java:712)
	at org.apache.hadoop.ipc.Client$Connection.access$2900(Client.java:375)
	at org.apache.hadoop.ipc.Client.getConnection(Client.java:1528)
	at org.apache.hadoop.ipc.Client.call(Client.java:1451)
	... 29 more
```
#### 4.2 解决方案

有可能是Hadoop没有启动，使用jps查看一下当前进程发现：
```
xiaosi@yoona:~/opt/hive-2.1.0$ jps
7317 Jps
```
可以看见，我们确实没有启动Hadoop。开启Hadoop的NameNode和DataNode守护进程
```
xiaosi@yoona:~/opt/hadoop-2.7.3$ ./sbin/start-dfs.sh
Starting namenodes on [localhost]
localhost: starting namenode, logging to /home/xiaosi/opt/hadoop-2.7.3/logs/hadoop-xiaosi-namenode-yoona.out
localhost: starting datanode, logging to /home/xiaosi/opt/hadoop-2.7.3/logs/hadoop-xiaosi-datanode-yoona.out
Starting secondary namenodes [0.0.0.0]
0.0.0.0: starting secondarynamenode, logging to /home/xiaosi/opt/hadoop-2.7.3/logs/hadoop-xiaosi-secondarynamenode-yoona.out
xiaosi@yoona:~/opt/hadoop-2.7.3$ jps
8055 Jps
7561 NameNode
7929 SecondaryNameNode
7724 DataNode
```
### 5. 创建Hive表失败

#### 5.1 问题描述
```java
FAILED: Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.DDLTask. MetaException(message:For direct MetaStore DB connections, we dont support retries at the client level.)
```
#### 5.2 解决方案

查看Hive日志，看到这样的错误日志：
```java
NestedThrowablesStackTrace:
Could not create "increment"/"table" value-generation container `SEQUENCE_TABLE` since autoCreate flags do not allow it.
org.datanucleus.exceptions.NucleusUserException: Could not create "increment"/"table" value-generation container `SEQUENCE_TABLE` since autoCreate flags do not allow it.
```
出现上述问题主要因为mysql的bin-log format默认为statement ，在mysql中通过 show variables like 'binlog_format'; 语句查看bin-log format的配置值
```
mysql> show variables like 'binlog_format';
+---------------+-----------+
| Variable_name | Value     |
+---------------+-----------+
| binlog_format | STATEMENT |
+---------------+-----------+
1 row in set (0.00 sec)
```
修改bin-log format的默认值，在mysql的配置文件/etc/mysql/mysql.conf.d/mysqld.cnf中添加 binlog_format="MIXED" ，重启mysql，再启动 hive即可。
```
mysql> show variables like 'binlog_format';
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| binlog_format | MIXED |
+---------------+-------+
1 row in set (0.00 sec)
```
再次执行创表语句：
```
hive> create table  if not exists employees(
    >    name string comment '姓名',
    >    salary float comment '工资',
    >    subordinates array<string> comment '下属',
    >    deductions map<string,float> comment '扣除金额',
    >    address struct<city:string,province:string> comment '家庭住址'
    > )
    > comment '员工信息表'
    > ROW FORMAT DELIMITED
    > FIELDS TERMINATED BY '\t'
    > LINES TERMINATED BY  '\n'
    > STORED AS TEXTFILE;
OK
Time taken: 0.664 seconds
```
### 6. 加载数据失败

#### 6.1 问题描述
```shell
hive> load data local inpath '/home/xiaosi/hive/input/result.txt' overwrite into table recent_attention;
Loading data to table test_db.recent_attention
Failed with exception Unable to move source file:/home/xiaosi/hive/input/result.txt to destination hdfs://localhost:9000/user/hive/warehouse/test_db.db/recent_attention/result.txt
FAILED: Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.MoveTask
```
查看Hive日志，看到这样的错误日志：
```
Caused by: org.apache.hadoop.ipc.RemoteException(java.io.IOException): File /home/xiaosi/hive/warehouse/recent_attention/result.txt could only be replicated to 0 nodes instead of minReplication (=1).  There are 0 datanode(s) running and no node(s) are excluded in this operation.
```
看到 0 datanodes running 我们猜想可能datanode挂掉了，jps验证一下，果然我们的datanode没有启动起来。

#### 6.2 问题解决

这个问题是由于datanode没有启动导致的，至于datanode为什么没有启动起来，去看另一篇博文：那些年踩过的Hadoop坑（http://blog.csdn.net/sunnyyoona/article/details/51659080）

### 7. Java连接Hive 驱动失败

#### 7.1 问题描述

```
java.lang.ClassNotFoundException: org.apache.hadoop.hive.jdbc.HiveDriver
	at java.net.URLClassLoader.findClass(URLClassLoader.java:381) ~[na:1.8.0_91]
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424) ~[na:1.8.0_91]
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:331) ~[na:1.8.0_91]
	at java.lang.ClassLoader.loadClass(ClassLoader.java:357) ~[na:1.8.0_91]
	at java.lang.Class.forName0(Native Method) ~[na:1.8.0_91]
	at java.lang.Class.forName(Class.java:264) ~[na:1.8.0_91]
	at com.sjf.open.hive.HiveClient.getConn(HiveClient.java:29) [classes/:na]
	at com.sjf.open.hive.HiveClient.run(HiveClient.java:53) [classes/:na]
	at com.sjf.open.hive.HiveClient.main(HiveClient.java:77) [classes/:na]
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method) ~[na:1.8.0_91]
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) ~[na:1.8.0_91]
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) ~[na:1.8.0_91]
	at java.lang.reflect.Method.invoke(Method.java:498) ~[na:1.8.0_91]
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144) [idea_rt.jar:na]
```
#### 7.2 解决方案
```java
private static String driverName = "org.apache.hadoop.hive.jdbc.HiveDriver";
```
取代
```
private static String driverName = "org.apache.hive.jdbc.HiveDriver"
```
### 8. create table问题

#### 8.1 问题描述

```sql
create table if not exists employee(
   name string comment 'employee name',
   salary float comment 'employee salary',
   subordinates array<string> comment 'names of subordinates',
   deductions map<string,float> comment 'keys are deductions values are percentages',
   address struct<street:string, city:string, state:string, zip:int> comment 'home address'
)
comment 'description of the table'
tblproperties ('creator'='yoona','date'='20160719')
location '/user/hive/warehouse/test.db/employee';
```
错误信息：
```
FAILED: ParseException line 10:0 missing EOF at 'location' near ')'
```
#### 8.2 解决方案

Location放在TBPROPERTIES之前：
```sql
create table if not exists employee(
   name string comment 'employee name',
   salary float comment 'employee salary',
   subordinates array<string> comment 'names of subordinates',
   deductions map<string,float> comment 'keys are deductions values are percentages',
   address struct<street:string, city:string, state:string, zip:int> comment 'home address'
)
comment 'description of the table'
location '/user/hive/warehouse/test.db/employee'
tblproperties ('creator'='yoona','date'='20160719');
create table命令：https://cwiki.apache.org/confluence/display/Hive/LanguageManual+DDL#LanguageManualDDL-CreateTable
```
### 9. JDBC Hive 拒绝连接

#### 9.1 问题描述
```java
15:00:50.815 [main] INFO  org.apache.hive.jdbc.Utils - Supplied authorities: localhost:10000
15:00:50.832 [main] INFO  org.apache.hive.jdbc.Utils - Resolved authority: localhost:10000
15:00:51.010 [main] DEBUG o.a.thrift.transport.TSaslTransport - opening transport org.apache.thrift.transport.TSaslClientTransport@3ffc5af1
15:00:51.019 [main] WARN  org.apache.hive.jdbc.HiveConnection - Failed to connect to localhost:10000
15:00:51.027 [main] ERROR com.sjf.open.hive.HiveClient - Connection error!
java.sql.SQLException: Could not open client transport with JDBC Uri: jdbc:hive2://localhost:10000/default: java.net.ConnectException: 拒绝连接
	at org.apache.hive.jdbc.HiveConnection.openTransport(HiveConnection.java:219) ~[hive-jdbc-2.1.0.jar:2.1.0]
	at org.apache.hive.jdbc.HiveConnection.<init>(HiveConnection.java:157) ~[hive-jdbc-2.1.0.jar:2.1.0]
	at org.apache.hive.jdbc.HiveDriver.connect(HiveDriver.java:107) ~[hive-jdbc-2.1.0.jar:2.1.0]
	at java.sql.DriverManager.getConnection(DriverManager.java:664) ~[na:1.8.0_91]
	at java.sql.DriverManager.getConnection(DriverManager.java:247) ~[na:1.8.0_91]
	at com.sjf.open.hive.HiveClient.getConn(HiveClient.java:29) [classes/:na]
	at com.sjf.open.hive.HiveClient.run(HiveClient.java:52) [classes/:na]
	at com.sjf.open.hive.HiveClient.main(HiveClient.java:76) [classes/:na]
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method) ~[na:1.8.0_91]
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) ~[na:1.8.0_91]
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) ~[na:1.8.0_91]
	at java.lang.reflect.Method.invoke(Method.java:498) ~[na:1.8.0_91]
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144) [idea_rt.jar:na]
Caused by: org.apache.thrift.transport.TTransportException: java.net.ConnectException: 拒绝连接
	at org.apache.thrift.transport.TSocket.open(TSocket.java:226) ~[libthrift-0.9.3.jar:0.9.3]
	at org.apache.thrift.transport.TSaslTransport.open(TSaslTransport.java:266) ~[libthrift-0.9.3.jar:0.9.3]
	at org.apache.thrift.transport.TSaslClientTransport.open(TSaslClientTransport.java:37) ~[libthrift-0.9.3.jar:0.9.3]
	at org.apache.hive.jdbc.HiveConnection.openTransport(HiveConnection.java:195) ~[hive-jdbc-2.1.0.jar:2.1.0]
	... 12 common frames omitted
Caused by: java.net.ConnectException: 拒绝连接
	at java.net.PlainSocketImpl.socketConnect(Native Method) ~[na:1.8.0_91]
	at java.net.AbstractPlainSocketImpl.doConnect(AbstractPlainSocketImpl.java:350) ~[na:1.8.0_91]
	at java.net.AbstractPlainSocketImpl.connectToAddress(AbstractPlainSocketImpl.java:206) ~[na:1.8.0_91]
	at java.net.AbstractPlainSocketImpl.connect(AbstractPlainSocketImpl.java:188) ~[na:1.8.0_91]
	at java.net.SocksSocketImpl.connect(SocksSocketImpl.java:392) ~[na:1.8.0_91]
	at java.net.Socket.connect(Socket.java:589) ~[na:1.8.0_91]
	at org.apache.thrift.transport.TSocket.open(TSocket.java:221) ~[libthrift-0.9.3.jar:0.9.3]
	... 15 common frames omitted
```
#### 9.2 解决方案

(1) 检查hive server2是否启动：
```
xiaosi@Qunar:/opt/apache-hive-2.0.0-bin/bin$ sudo netstat -anp | grep 10000
```
如果没有启动hive server2，首先启动服务：
```
xiaosi@Qunar:/opt/apache-hive-2.0.0-bin/conf$ hive --service hiveserver2 >/dev/null 2>/dev/null &
[1] 11978
```
(2) 检查配置：
```xml
<property>
    <name>hive.server2.thrift.port</name>
    <value>10000</value>
    <description>Port number of HiveServer2 Thrift interface when hive.server2.transport.mode is 'binary'.</description>
</property>
```

### 10. User root is not allowed to impersonate anonymous

#### 10.1 问题描述

```java
Failed to open new session: java.lang.RuntimeException: org.apache.hadoop.ipc.RemoteException(org.apache.hadoop.security.authorize.AuthorizationException): User:xiaosiis not allowed to impersonate anonymous
```
#### 10.2 解决方案

修改 Hadoop 配置文件 `etc/hadoop/core-site.xml` 加入如下配置项：
```xml
<property>
    <name>hadoop.proxyuser.root.hosts</name>
    <value>*</value>
</property>
<property>
    <name>hadoop.proxyuser.root.groups</name>
    <value>*</value>
</property>
```
`hadoop.proxyuser.XXX.hosts` 与 `hadoop.proxyuser.XXX.groups` 中 XXX 为异常信息中 `User:*` 中的用户名部分，修改为自己的用户名称：
```xml
<property>
    <name>hadoop.proxyuser.xiaosi.hosts</name>
    <value>*</value>
    <description>The superuser can connect only from host1 and host2 to impersonate a user</description>
</property>
<property>
    <name>hadoop.proxyuser.xiaosi.groups</name>
    <value>*</value>
    <description>Allow the superuser oozie to impersonate any members of the group group1 and group2</description>
</property>
```


### 12. Failed to recognize predicate 'date'. Failed rule: 'identifier' in column specification

#### 12.1 问题描述

在Hive1.2.2版本运行如下HQL时：
```sql
select dt as date, comMap['searchType'] as search_type, comMap['clickType'] as click_type
from search_click
where dt = '20170614';
```
会抛出如下异常：
```java
Failed to recognize predicate 'date'. Failed rule: 'identifier' in column specification
```
#### 12.2 问题分析

在Hive1.2.0版本开始增加了如下配置选项，默认值为`true`：
```
hive.support.sql11.reserved.keywords
```

该选项的目的是：是否启用对SQL2011保留关键字的支持。 启用后，将支持部分SQL2011保留关键字。

#### 12.3　解决方案

从上面可以知道是因为启用了对保留关键字的支持导致的，上面语句中`date`是保留关键字．所以解决方案如下：
- 弃用保留关键字`date`
```sql
select dt, comMap['searchType'] as search_type, comMap['clickType'] as click_type
from search_click
where dt = '20170614';
```
- 弃用对保留关键字的支持

```shell
sudo -uwirelessdev hive -e "
   set hive.support.sql11.reserved.keywords = false ;
   select dt, comMap['searchType'] as search_type, comMap['clickType'] as click_type
   from search_click
   where dt = '20170614';
" > a.txt
```
或者在`conf`下的`hive-site.xml`配置文件中修改配置选项：

```xml
<property>
    <name>hive.support.sql11.reserved.keywords</name>
    <value>false</value>
</property>
```


### 14. The MySQL server is running with the --read-only

```java
Caused by: java.sql.SQLException: The MySQL server is running with the --read-only option so it cannot execute this statement
        at com.mysql.jdbc.SQLError.createSQLException(SQLError.java:1074)
        at com.mysql.jdbc.MysqlIO.checkErrorPacket(MysqlIO.java:4074)
        at com.mysql.jdbc.MysqlIO.checkErrorPacket(MysqlIO.java:4006)
        at com.mysql.jdbc.MysqlIO.sendCommand(MysqlIO.java:2468)
        at com.mysql.jdbc.MysqlIO.sqlQueryDirect(MysqlIO.java:2629)
				...
        at org.datanucleus.api.jdo.JDOTransaction.commit(JDOTransaction.java:107)
        ... 45 more
```
https://blog.csdn.net/lwei_998/article/details/50445830
https://www.cnblogs.com/gomysql/p/3671896.html


### 15. Loading class com.mysql.jdbc.Driver

创建表的时候出现如下警告：
```
Loading class 'com.mysql.jdbc.Driver'. This is deprecated. The new driver class is `com.mysql.cj.jdbc.Driver'. The driver is automatically registered via the SPI and manual loading of the driver class is generally unnecessary.
```
修改 Hive 配置文件，将 `com.mysql.jdbc.Driver` 修改为 `com.mysql.cj.jdbc.Driver`：
```xml
<property>
   <name>javax.jdo.option.ConnectionDriverName</name>
   <value>com.mysql.cj.jdbc.Driver</value>
</property>
```

### 16. Invalid signature file digest for Manifest main attributes

```
Error: A JNI error has occurred, please check your installation and try again
Exception in thread "main" java.lang.SecurityException: Invalid signature file digest for Manifest main attributes
        at sun.security.util.SignatureFileVerifier.processImpl(SignatureFileVerifier.java:330)
        at sun.security.util.SignatureFileVerifier.process(SignatureFileVerifier.java:263)
        at java.util.jar.JarVerifier.processEntry(JarVerifier.java:318)
        at java.util.jar.JarVerifier.update(JarVerifier.java:230)
        at java.util.jar.JarFile.initializeVerifier(JarFile.java:383)
        at java.util.jar.JarFile.getInputStream(JarFile.java:450)
        at sun.misc.URLClassPath$JarLoader$2.getInputStream(URLClassPath.java:977)
        at sun.misc.Resource.cachedInputStream(Resource.java:77)
        at sun.misc.Resource.getByteBuffer(Resource.java:160)
        at java.net.URLClassLoader.defineClass(URLClassLoader.java:454)
        at java.net.URLClassLoader.access$100(URLClassLoader.java:73)
        at java.net.URLClassLoader$1.run(URLClassLoader.java:368)
        at java.net.URLClassLoader$1.run(URLClassLoader.java:362)
        at java.security.AccessController.doPrivileged(Native Method)
        at java.net.URLClassLoader.findClass(URLClassLoader.java:361)
        at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
        at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:338)
        at java.lang.ClassLoader.loadClass(ClassLoader.java:357)
        at sun.launcher.LauncherHelper.checkAndLoadMain(LauncherHelper.java:495)
```
这是因为在使用Maven打包的时候导致某些包的重复引用，以至于打包之后的META-INF的目录下多出了一些*.SF,*.DSA,*.RSA文件所致，我们可以在pom文件里面加入以下配置：
```xml
<build>
  <plugins>
  <plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-shade-plugin</artifactId>
    <version>2.2</version>
    <configuration>
      <filters>
        <filter>
          <artifact>*:*</artifact>
          <excludes>
            <exclude>META-INF/*.SF</exclude>
            <exclude>META-INF/*.DSA</exclude>
            <exclude>META-INF/*.RSA</exclude>
          </excludes>
        </filter>
      </filters>
    </configuration>
  </plugin>
  </plugins>
</build>
```
### 17. /bin/java: No such file or directory

在执行 Hive 报错，查看运行日志发现报如下错误：
```
/bin/bash: /bin/java: No such file or directory
```
根本问题是找不到 Java 路径，解决方案是修改 hadoop-env.sh 中 JAVA_HOME：
```
#export JAVA_HOME=${JAVA_HOME}
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk1.8.0_161.jdk/Contents/Home
```





欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)
