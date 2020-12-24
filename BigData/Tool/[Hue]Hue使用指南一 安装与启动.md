---
layout: post
author: sjf0115
title: Hue 安装与配置
date: 2018-05-12 19:16:01
tags:
  - Hue

categories: Hue
permalink: hue-how-to-install-and-configure
---

### 1. 下载

### 2. 安装

#### 2.1 安装依赖

本机为 CentOS 系统，所以采用如下方式安装依赖:
```
sudo yum install ant asciidoc cyrus-sasl-devel cyrus-sasl-gssapi cyrus-sasl-plain gcc gcc-c++ krb5-devel libffi-devel libxml2-devel libxslt-devel make  mysql mysql-devel openldap-devel python-devel sqlite-devel gmp-devel
```
其他方式可以参考：[Hue Installation](http://cloudera.github.io/hue/latest/admin-manual/manual.html#installation)

### 3. 配置

根据我们的需求来配置自己需要的内容。我们修改配置文件的情况，如下表所示：

Hue配置段|Hue配置项|Hue配置值|说明
---|---|---
desktop|default_hdfs_superuser| hadoop| HDFS管理用户
desktop|http_host| 10.10.4.125| Hue Web Server所在主机/IP
desktop|http_port| 8000| Hue Web Server服务端口
desktop|server_user| hadoop| 运行Hue Web Server的进程用户
desktop|server_group| hadoop| 运行Hue Web Server的进程用户组
desktop|default_user| yanjun| Hue管理员
hadoop/hdfs_clusters|	fs_defaultfs|	hdfs://hadoop6:8020|	对应core-site.xml配置项fs.defaultFS
hadoop/hdfs_clusters| hadoop_conf_dir|	/usr/local/hadoop/etc/hadoop|	Hadoop配置文件目录
hadoop/yarn_clusters|	resourcemanager_host|	hadoop6|	对应yarn-site.xml配置项yarn.resourcemanager.hostname
hadoop/yarn_clusters|	resourcemanager_port|	8032|	ResourceManager服务端口号
hadoop/yarn_clusters|	resourcemanager_api_url|	http://hadoop6:8088|	对应于yarn-site.xml配置项yarn.resourcemanager.webapp.address|
hadoop/yarn_clusters|	proxy_api_url|	http://hadoop6:8888|	对应yarn-site.xml配置项yarn.web-proxy.address|
hadoop/yarn_clusters|	history_server_api_url|	http://hadoo6:19888|	对应mapred-site.xml配置项mapreduce.jobhistory.webapp.address
beeswax|	hive_server_host|	10.10.4.125|	Hive所在节点主机名/IP
beeswax|	hive_server_port|	10000|	HiveServer2服务端口号
beeswax|	hive_conf_dir|	/usr/local/hive/conf|	Hive配置文件目录



/home/xiaosi/opt/hue-4.0.0/desktop/conf目录下修改`hue.ini`配置文件:

(1) Hive相关配置:
```
# Host where HiveServer2 is running.
# If Kerberos security is enabled, use fully-qualified domain name (FQDN).
hive_server_host=localhost

# Port where HiveServer2 Thrift server runs on.
hive_server_port=10000

# Hive configuration directory, where hive-site.xml is located
hive_conf_dir=/home/xiaosi/opt/hive-2.1.0/conf
```
(2) Hadoop相关配置:
```
# 文件系统URI 对应Hadoop的`core-site.xml`配置项`fs.defaultFS`
fs_defaultfs=hdfs://localhost:9000

# Hadoop 配置文件目录
hadoop_conf_dir=/home/xiaosi/opt/hadoop-2.7.3/etc/hadoop

# ResourceManager 服务端口号 对应Hadoop的`yarn-site.xml`配置项`yarn.resourcemanager.address`的端口
resourcemanager_port=8032

# ResourceManager host 对应Hadoop的`yarn-site.xml`配置项`yarn.resourcemanager.address`的host
resourcemanager_host=localhost

# ResourceManager API URL 对应Hadoop的`yarn-site.xml`配置项`yarn.resourcemanager.webapp.address`
resourcemanager_api_url=http://localhost:8088

# 对应yarn-site.xml配置项yarn.web-proxy.address
proxy_api_url=

# 对应mapred-site.xml配置项mapreduce.jobhistory.webapp.address
history_server_api_url=
```
(3) Desktop相关配置:
```
# Hadoop 集群管理员
default_hdfs_superuser=hdfs

# Webserver 地址与端口号
http_host=0.0.0.0
http_port=8888

# 运行Webserver的用户与用户组
server_user=hue
server_group=hue

# Hue 管理员
default_user=hue
```


问题:

(1) 问题一
```
Could not connect to localhost:10000
```
解决方案:
```
Hue使用HiveServer2连接hive，所以要开启HiveServer2服务，使用如下命令开启:
$HIVE_HOME/bin/hiveserver2
或者
$HIVE_HOME/bin/hive --service hiveserver2
```

(2) 问题二
```java
Failed to open new session: java.lang.RuntimeException: org.apache.hadoop.security.AccessControlException: Permission denied: user=root, access=EXECUTE, inode="/tmp/hive":xiaosi:supergroup:drwx------ at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.check(FSPermissionChecker.java:319) at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkTraverse(FSPermissionChecker.java:259) at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkPermission(FSPermissionChecker.java:205) at org.apache.hadoop.hdfs.server.namenode.FSPermissionChecker.checkPermission(FSPermissionChecker.java:190) at org.apache.hadoop.hdfs.server.namenode.FSDirectory.checkPermission(FSDirectory.java:1728) at org.apache.hadoop.hdfs.server.namenode.FSDirStatAndListingOp.getFileInfo(FSDirStatAndListingOp.java:108) at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.getFileInfo(FSNamesystem.java:3857) at org.apache.hadoop.hdfs.server.namenode.NameNodeRpcServer.getFileInfo(NameNodeRpcServer.java:1012) at org.apache.hadoop.hdfs.protocolPB.ClientNamenodeProtocolServerSideTranslatorPB.getFileInfo(ClientNamenodeProtocolServerSideTranslatorPB.java:843) at org.apache.hadoop.hdfs.protocol.proto.ClientNamenodeProtocolProtos$ClientNamenodeProtocol$2.callBlockingMethod(ClientNamenodeProtocolProtos.java) at org.apache.hadoop.ipc.ProtobufRpcEngine$Server$ProtoBufRpcInvoker.call(ProtobufRpcEngine.java:616) at org.apache.hadoop.ipc.RPC$Server.call(RPC.java:982) at org.apache.hadoop.ipc.Server$Handler$1.run(Server.java:2049) at org.apache.hadoop.ipc.Server$Handler$1.run(Server.java:2045) at java.security.AccessController.doPrivileged(Native Method) at javax.security.auth.Subject.doAs(Subject.java:422) at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1698) at org.apache.hadoop.ipc.Server$Handler.run(Server.java:2043)
```
解决方案:
```
Hadoop用户的管理员为xiaosi，所以root用户没有权限操作Hadoop，改用账号xiaosi登录Hue
```
