---
layout: post
author: sjf0115
title: Hive 安装与配置
date: 2020-08-30 14:43:01
tags:
  - Hive

categories: Hive
permalink: hive-install-and-config
---

### 1. 下载

可以从 http://hive.apache.org/downloads.html 下载你想要的版本，在这我们使用的是2.3.7版本

> Mac 操作系统、Hive 2.3.7 版本

### 2. 解压

把下载好的文件解压到 /opt 目录下：
```
wy:opt wy$ tar -zxvf apache-hive-2.3.7-bin.tar.gz -C /opt/
```
创建软连接，便于升级：
```
ln -s apache-hive-2.3.7-bin/ hive
```

### 3. 配置

使用如下命令根据模板创建配置文件：
```shell
cp hive-default.xml.template hive-site.xml
```
有了配置文件之后我们修改默认配置，重点修改如下几个配置：
```xml
<property>
   <name>javax.jdo.option.ConnectionURL</name>
   <value>jdbc:mysql://localhost:3306/hive_meta?createDatabaseIfNotExist=true</value>
</property>
<property>
   <name>javax.jdo.option.ConnectionDriverName</name>
   <value>com.mysql.cj.jdbc.Driver</value>
</property>
<property>
   <name>javax.jdo.option.ConnectionUserName</name>
   <value>root</value>
</property>
<property>
   <name>javax.jdo.option.ConnectionPassword</name>
   <value>root</value>
</property>
<property>
   <name>hive.metastore.warehouse.dir</name>
   <value>/user/hive/warehouse</value>
</property>
```
除了修改上述配置之外，我们还需要添加如下两个配置：
```xml
<property>
    <name>system:user.name</name>
    <value>xiaosi</value>
</property>
<property>
    <name>system:java.io.tmpdir</name>
    <value>/tmp/${system:user.name}/hive/</value>
</property>
```
如果不添加，可能抛出如下异常：
```java
Exception in thread "main" java.lang.IllegalArgumentException: java.net.URISyntaxException: Relative path in absolute URI: ${system:java.io.tmpdir%7D/$%7Bsystem:user.name%7D
	at org.apache.hadoop.fs.Path.initialize(Path.java:205)
	at org.apache.hadoop.fs.Path.<init>(Path.java:171)
	at org.apache.hadoop.hive.ql.session.SessionState.createSessionDirs(SessionState.java:663)
	at org.apache.hadoop.hive.ql.session.SessionState.start(SessionState.java:586)
	at org.apache.hadoop.hive.ql.session.SessionState.beginStart(SessionState.java:553)
	at org.apache.hadoop.hive.cli.CliDriver.run(CliDriver.java:750)
	at org.apache.hadoop.hive.cli.CliDriver.main(CliDriver.java:686)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.hadoop.util.RunJar.run(RunJar.java:226)
	at org.apache.hadoop.util.RunJar.main(RunJar.java:141)
Caused by: java.net.URISyntaxException: Relative path in absolute URI: ${system:java.io.tmpdir%7D/$%7Bsystem:user.name%7D
	at java.net.URI.checkPath(URI.java:1823)
	at java.net.URI.<init>(URI.java:745)
	at org.apache.hadoop.fs.Path.initialize(Path.java:202)
	... 12 more
```

### 4. Hive元数据

> 这里我们使用 MySQL 存储 Hive 元数据

使用如下命令将 MySQL 驱动包复制到 lib 目录下：
```
cp mysql-connector-java-8.0.17.jar /opt/hive/lib/
```
> 在这我们已经提前下载好驱动包

创建存储 Hive 元数据的数据库 `hive_meta`：
```
mysql> create database hive_meta;
Query OK, 1 row affected (0.00 sec)
```

创建好数据库之后在 scripts 目录下运行如下命令进行 Hive 元数据库的初始化：
```
schematool -initSchema -dbType mysql --verbose
```
如果不进行初始化可能会遇到如下异常：
```java
Exception in thread "main" java.lang.RuntimeException: Hive metastore database is not initialized. Please use schematool (e.g. ./schematool -initSchema -dbType ...) to create the schema. If needed, dont forget to include the option to auto-create the underlying database in your JDBC connection string (e.g. ?createDatabaseIfNotExist=true for mysql)
```

### 5. 设置环境变量

在 `/etc/profile` 配置文件下添加如下配置：
```shell
# Hive
export HIVE_HOME=/opt/hive
export PATH=${HIVE_HOME}/bin:$PATH
```
修改完成之后如行如下命令使之生效：
```shell
source /etc/profile
```

### 6. 启动

由于上一步骤已经配置了环境变量，我们可以在任意目录下 `hive` 命令即可启动：
```shell
wy:~ wy$ hive
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/apache-hive-2.3.7-bin/lib/log4j-slf4j-impl-2.6.2.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/Users/wy/opt/hadoop-2.7.7/share/hadoop/common/lib/slf4j-log4j12-1.7.10.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]

Logging initialized using configuration in jar:file:/opt/apache-hive-2.3.7-bin/lib/hive-common-2.3.7.jar!/hive-log4j2.properties Async: true
Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
hive>
```
启动 Hive CLI 之后我们通过创建一个内部来测试一下：
```sql
CREATE TABLE IF NOT EXISTS tmp_hive_managed_table (
  uid STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n';
```
查询一下创建的表：
```shell
hive> show tables;
OK
tmp_hive_managed_table
Time taken: 0.123 seconds, Fetched: 1 row(s)
hive>
```
现在我们完成了 Hive 安装与配置。
