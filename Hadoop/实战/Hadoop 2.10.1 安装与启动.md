---
layout: post
author: sjf0115
title: Hadoop 2.10.1 安装与启动
date: 2023-08-22 11:01:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-2.10.1-setup-and-start
---

### 1. SSH

参考博文：[Hadoop]SSH免密码登录以及失败解决方案（http://blog.csdn.net/sunnyyoona/article/details/51689041#t1）

### 2. 下载与解压缩

可以直接从官网上下载 https://archive.apache.org/dist/hadoop/common/ 你需要的版本，在这我们使用的是 2.10.1 版本 hadoop-2.10.1.tar.gz。下载之后解压缩到 `/opt` 目录下：
```
sudo tar -zxvf hadoop-2.10.1.tar.gz -C /opt/
```

为了以后升级方便，运行如下命令创建软连接：
```
ln -s hadoop-2.10.1 hadoop
```

### 3. 配置

配置文件都位于安装目录下的`/etc/hadoop`文件夹下：
```
localhost:hadoop wy$ cd etc/hadoop/
localhost:hadoop wy$ ll
total 328
drwxr-xr-x  31 1000  1000    992 Sep 14  2020 ./
drwxr-xr-x   3 1000  1000     96 Sep 14  2020 ../
-rw-r--r--   1 1000  1000   8814 Sep 14  2020 capacity-scheduler.xml
-rw-r--r--   1 1000  1000   1335 Sep 14  2020 configuration.xsl
-rw-r--r--   1 1000  1000   1211 Sep 14  2020 container-executor.cfg
-rw-r--r--   1 1000  1000    774 Sep 14  2020 core-site.xml
-rw-r--r--   1 1000  1000   4133 Sep 14  2020 hadoop-env.cmd
-rw-r--r--   1 1000  1000   4969 Sep 14  2020 hadoop-env.sh
-rw-r--r--   1 1000  1000   2490 Sep 14  2020 hadoop-metrics.properties
-rw-r--r--   1 1000  1000   2598 Sep 14  2020 hadoop-metrics2.properties
-rw-r--r--   1 1000  1000  10206 Sep 14  2020 hadoop-policy.xml
-rw-r--r--   1 1000  1000    775 Sep 14  2020 hdfs-site.xml
-rw-r--r--   1 1000  1000   2432 Sep 14  2020 httpfs-env.sh
-rw-r--r--   1 1000  1000   1657 Sep 14  2020 httpfs-log4j.properties
-rw-r--r--   1 1000  1000     21 Sep 14  2020 httpfs-signature.secret
-rw-r--r--   1 1000  1000    620 Sep 14  2020 httpfs-site.xml
-rw-r--r--   1 1000  1000   3518 Sep 14  2020 kms-acls.xml
-rw-r--r--   1 1000  1000   3139 Sep 14  2020 kms-env.sh
-rw-r--r--   1 1000  1000   1788 Sep 14  2020 kms-log4j.properties
-rw-r--r--   1 1000  1000   5939 Sep 14  2020 kms-site.xml
-rw-r--r--   1 1000  1000  14016 Sep 14  2020 log4j.properties
-rw-r--r--   1 1000  1000   1076 Sep 14  2020 mapred-env.cmd
-rw-r--r--   1 1000  1000   1507 Sep 14  2020 mapred-env.sh
-rw-r--r--   1 1000  1000   4113 Sep 14  2020 mapred-queues.xml.template
-rw-r--r--   1 1000  1000    758 Sep 14  2020 mapred-site.xml.template
-rw-r--r--   1 1000  1000     10 Sep 14  2020 slaves
-rw-r--r--   1 1000  1000   2316 Sep 14  2020 ssl-client.xml.example
-rw-r--r--   1 1000  1000   2697 Sep 14  2020 ssl-server.xml.example
-rw-r--r--   1 1000  1000   2250 Sep 14  2020 yarn-env.cmd
-rw-r--r--   1 1000  1000   4876 Sep 14  2020 yarn-env.sh
-rw-r--r--   1 1000  1000    690 Sep 14  2020 yarn-site.xml
```
Hadoop 的各个组件均可利用 `XML` 文件进行配置。`core-site.xml` 文件用于配置 `Common` 组件的属性，`hdfs-site.xml` 文件用于配置 HDFS 属性，而 `mapred-site.xml` 文件则用于配置 `MapReduce` 属性。

> Hadoop 早期版本采用一个配置文件hadoop-site.xml来配置Common，HDFS和MapReduce组件。从0.20.0版本开始该文件以分为三，各对应一个组件。

#### 3.1 配置 core-site.xml

`core-site.xml` 配置如下：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
   <property>
      <name>fs.defaultFS</name>
      <value>hdfs://localhost:9000</value>
   </property>
   <property>
      <name>hadoop.tmp.dir</name>
      <value>/Users/wy/tmp/hadoop</value>
   </property>
</configuration>
```

#### 3.2 配置 hdfs-site.xml

添加以下内容至 `hdfs-site.xml` 文件。`dfs.replication` 通常为3, 由于我们只有一台主机和一个伪分布式模式的 DataNode，将此值修改为1：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
   <property>
      <name>dfs.replication</name>
      <value>1</value>
   </property>
</configuration>
```

#### 3.3 配置 mapred-site.xml

将 `mapred-site.xml.template` 重命名为 `mapred-site.xml`，并向 `mapred-site.xml` 文件添加以下内容。设置数据处理框架为 yarn：
```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
     <name>mapreduce.framework.name</name>
     <value>yarn</value>
  </property>
  <property>
        <name>mapreduce.application.classpath</name>
        <value>$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
```
> 本地模式下是`value`值是`local`，`yarn`模式下`value`值是`yarn`。

#### 3.4 配置 yarn-site.xml

如果在 mapred-site.xml 中设置数据处理框架为 yarn，同时也需要配置 yarn-site.xml 文件。具体配置如下所示：
```xml
<configuration>
   <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
</configuration>
```
运行`Hadoop`的时候可能会找不到`jdk`，需要我们修改`hadoop.env.sh`脚本文件，唯一需要修改的环境变量就是`JAVE_HOME`，其他选项都是可选的：
```
export JAVA_HOME=/home/xiaosi/opt/jdk-1.8.0
```

### 4. 运行

#### 4.1 初始化HDFS系统

在配置完成后，运行`hadoop`前，需要初始化 `HDFS` 系统，通过创建存储目录和初始化元数据来格式化和创建新的文件系统。在`bin/`目录下执行如下命令：
```
hdfs namenode -format
```
#### 4.2 启动 HDFS

通过 sbin 目录下的如下命令来启动 HDFS：
```
. start-dfs.sh
```
启动之后通过`jps`命令查看 `namenode` 和 `datanode` 是否已经启动起来：
```
localhost:hadoop wy$ jps
6352 SecondaryNameNode
6152 NameNode
6237 DataNode
6478 Jps
```
从启动日志我们可以知道，日志信息存储在 hadoop 安装目录下的 `logs/` 文件夹下，如果启动过程中有任何问题，可以通过查看日志来确认问题原因。

#### 4.3 检查是否运行成功

打开浏览器，输入：http://localhost:50070/

### 5. 启动yarn

启动`yarn`：
```
localhost:sbin wy$ . start-yarn.sh
starting yarn daemons
which: illegal option -- b
usage: which [-as] program ...
starting resourcemanager, logging to /opt/hadoop-2.10.1/logs/yarn-wy-resourcemanager-localhost.out
localhost: starting nodemanager, logging to /opt/hadoop-2.10.1/logs/yarn-wy-nodemanager-localhost.out
```
关闭 yarn 可以通过 `stop-yarn.sh` 来实现。
