---
layout: post
author: sjf0115
title: Kafka 监控工具之 Kafka Eagle
date: 2022-05-09 21:00:01
tags:
  - Kafka

categories: Kafka
permalink: use-kafka-eagle-to-manage-kafka
---

> 2.1.0 版本

## 1. 安装

下载 kafka-eagle-bin-xxx.tar.gz，需要解压缩两次:
```
tar -zxvf kafka-eagle-bin-2.1.0.tar.gz -C /opt/
cd /opt/kafka-eagle-bin-2.1.0
tar -zxvf efak-web-2.1.0-bin.tar.gz -C /opt/
```
为了便于后续版本升级，创建如下软连接：
```
ln -s efak-web-2.1.0/ efak
```
然后，配置 `/etc/profile` 配置文件
```
# Kafa Eagle
export KE_HOME=/opt/efak
export PATH=${KE_HOME}/bin:$PATH
```
最后，我们使用 `. /etc/profile` 使配置立即生效。需要注意的是名称必须为 KE_HOME，否则在启动的时候报如下错误：
```
localhost:bin wy$ ke.sh start
[2022-05-09 22:31:02] INFO: Starting  EFAK( Eagle For Apache Kafka ) environment check ...
[2022-05-09 22:31:02] Error: The KE_HOME environment variable is not defined correctly.
[2022-05-09 22:31:02] Error: This environment variable is needed to run this program.
```

## 2. 配置

根据自身 Kafka 集群的实际情况配置 EFAK，例如 zookeeper 地址、Kafka 集群的版本类型（zk 为低版本，kafka 为高版本）、Kafka 集群开启安全认证等。

修改 conf 下的 system-config.properties 配置文件：
```
######################################
# 设置Kafka多集群，这里只需要设置 Zookeeper,
# 系统会自动识别 Kafka Broker
######################################
efak.zk.cluster.alias=cluster1
cluster1.zk.list=localhost:2181,localhost:2182,localhost:2183

######################################
# zookeeper 是否开启 ACL
######################################
cluster1.zk.acl.enable=false
cluster1.zk.acl.schema=digest
cluster1.zk.acl.username=test
cluster1.zk.acl.password=test123

######################################
# broker size online list
######################################
cluster1.efak.broker.size=20

######################################
# Zookeeper 线程池最大连接数
######################################
kafka.zk.limit.size=16

######################################
# EFAK 的页面访问端口
######################################
efak.webui.port=8048

######################################
# EFAK 是否开启分布式模式
######################################
efak.distributed.enable=false
efak.cluster.mode.status=master
efak.worknode.master.host=localhost
efak.worknode.port=8085

######################################
# kafka jmx acl and ssl authenticate
######################################
cluster1.efak.jmx.acl=false
cluster1.efak.jmx.user=keadmin
cluster1.efak.jmx.password=keadmin123
cluster1.efak.jmx.ssl=false
cluster1.efak.jmx.truststore.location=/data/ssl/certificates/kafka.truststore
cluster1.efak.jmx.truststore.password=ke123456

######################################
# 存储消费信息的类型
# 在 0.9 版本之前，消费信息会默认存储在 Zookeeper中，存储类型设置 zookeeper
# 在 0.10 版本之后，消费者信息默认存储在 Kafka 中，所以存储类型设置为 kafka
######################################
cluster1.efak.offset.storage=kafka

######################################
# kafka JMX
######################################
cluster1.efak.jmx.uri=service:jmx:rmi:///jndi/rmi://%s/jmxrmi

######################################
# 开启性能监控，数据默认保留15天
######################################
efak.metrics.charts=true
efak.metrics.retain=15

######################################
# KSQL 查询 Topic 数据默认是最新的5000条
######################################
efak.sql.topic.records.max=5000
efak.sql.topic.preview.records.max=10

######################################
# 删除Kafka Topic时需要输入删除密钥，由管理员执行
######################################
efak.topic.token=keadmin

######################################
# 开启 Kafka ACL 特性
######################################
cluster1.efak.sasl.enable=false
cluster1.efak.sasl.protocol=SASL_PLAINTEXT
cluster1.efak.sasl.mechanism=SCRAM-SHA-256
cluster1.efak.sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username="kafka" password="kafka-eagle";
cluster1.efak.sasl.client.id=
cluster1.efak.blacklist.topics=
cluster1.efak.sasl.cgroup.enable=false
cluster1.efak.sasl.cgroup.topics=

######################################
# 使用 Sqlite 存储 EFAK 元数据信息的数据库
######################################
#efak.driver=org.sqlite.JDBC
#efak.url=jdbc:sqlite:/hadoop/kafka-eagle/db/ke.db
#efak.username=root
#efak.password=www.kafka-eagle.org

######################################
# 使用 MySQL 存储 EFAK 元数据信息的数据库
######################################
efak.driver=com.mysql.cj.jdbc.Driver
efak.url=jdbc:mysql://127.0.0.1:3306/efak?useUnicode=true&characterEncoding=UTF-8&zeroDateTimeBehavior=convertToNull
efak.username=root
efak.password=root
```

## 3. 启动 EFAK 服务器

> Standalone 模式，非分布式模式

在 $KE_HOME/bin 目录中，有一个 ke.sh 脚本文件。执行启动命令如下：
```
cd ${KE_HOME}/bin
chmod +x ke.sh
ke.sh start
```

当看到如下界面时，表示我们的 EFAK 服务器已经启动成功了：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/use-kafka-eagle-to-manage-kafka-1.png?raw=true)

上图中已经给出了 Web 的地址 http://127.0.0.1:8048/ 以及账号(admin)与密码(123456)。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/use-kafka-eagle-to-manage-kafka-2.png?raw=true)

登录成功之后的界面如下：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/use-kafka-eagle-to-manage-kafka-3.png?raw=true)

之后，当 EFAK 服务器重新启动或停止时，执行以下命令：
```
ke.sh restart
ke.sh stop
```







原文:[Kafka Eagle Install](https://docs.kafka-eagle.org/2.env-and-install/2.installing)
