---
layout: post
author: sjf0115
title: Hadoop 安装与启动
date: 2016-12-29 11:01:01
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-setup-and-start
---

### 1. SSH

参考博文：[Hadoop]SSH免密码登录以及失败解决方案（http://blog.csdn.net/sunnyyoona/article/details/51689041#t1）

### 2. 下载

(1) 直接从官网上下载 http://hadoop.apache.org/releases.html

(2) 使用命令行下载：
```
xiaosi@yoona:~$ wget http://mirrors.hust.edu.cn/apache/hadoop/common/hadoop-2.7.3/hadoop-2.7.3.tar.gz
--2016-06-16 08:40:07--  http://mirrors.hust.edu.cn/apache/hadoop/common/hadoop-2.7.3/hadoop-2.7.3.tar.gz
正在解析主机 mirrors.hust.edu.cn (mirrors.hust.edu.cn)... 202.114.18.160
正在连接 mirrors.hust.edu.cn (mirrors.hust.edu.cn)|202.114.18.160|:80... 已连接。
已发出 HTTP 请求，正在等待回应... 200 OK
长度： 196015975 (187M) [application/octet-stream]
正在保存至: “hadoop-2.6.4.tar.gz”
```

### 3. 解压缩Hadoop包

解压位于根目录`/`文件夹下的`hadoop-2.7.3.tar.gz`到`~/opt`文件夹下
```
xiaosi@yoona:~$ tar -zxvf hadoop-2.7.3.tar.gz -C opt/
```

### 4. 配置

配置文件都位于安装目录下的`/etc/hadoop`文件夹下：
```
xiaosi@yoona:~/opt/hadoop-2.7.3/etc/hadoop$ ls
capacity-scheduler.xml  hadoop-env.sh              httpfs-log4j.properties  log4j.properties            mapred-site.xml.template
configuration.xsl       hadoop-metrics2.properties  httpfs-signature.secret  log4j.properties          slaves
container-executor.cfg  hadoop-metrics.properties   httpfs-site.xml          mapred-env.cmd              ssl-client.xml.example
core-site.xml           hadoop-policy.xml           kms-acls.xml             mapred-env.sh               ssl-server.xml.example
core-site.xml          hdfs-site.xml               kms-env.sh               mapred-queues.xml.template  yarn-env.cmd
hadoop-env.cmd          hdfs-site.xml              kms-log4j.properties     mapred-site.xml             yarn-env.sh
hadoop-env.sh           httpfs-env.sh               kms-site.xml             mapred-site.xml            yarn-site.xml
```
Hadoop的各个组件均可利用`XML`文件进行配置。`core-site.xml`文件用于配置`Common`组件的属性，`hdfs-site.xml`文件用于配置HDFS属性，而`mapred-site.xml`文件则用于配置`MapReduce`属性。

备注：
```
Hadoop早期版本采用一个配置文件hadoop-site.xml来配置Common，HDFS和MapReduce组件。从0.20.0版本开始该文件以分为三，各对应一个组件。
```

#### 4.1 配置core-site.xml

`core-site.xml` 配置如下：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<!--
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License. See accompanying LICENSE file.
-->
<!-- Put site-specific property overrides in this file. -->
<configuration>
   <property>
      <name>hadoop.tmp.dir</name>
      <value>/home/${user.name}/tmp/hadoop</value>
      <description>Abase for other temporary directories.</description>
   </property>
   <property>
      <name>fs.defaultFS</name>
      <value>hdfs://localhost:9000</value>
   </property>

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
</configuration>
```

#### 4.2 配置hdfs-site.xml

`hdfs-site.xml`配置如下：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<!--
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License. See accompanying LICENSE file.
-->
<!-- Put site-specific property overrides in this file. -->
<configuration>
   <property>
      <name>dfs.replication</name>
      <value>1</value>
   </property>
   <property>
      <name>dfs.namenode.name.dir</name>
      <value>file:/home/xiaosi/tmp/hadoop/dfs/name</value>
   </property>
   <property>
      <name>dfs.datanode.data.dir</name>
      <value>file:/home/xiaosi/tmp/hadoop/dfs/data</value>
   </property>
   <property>
      <name>dfs.namenode.http-address</name>
      <value>localhost:50070</value>
   </property>
</configuration>
```

#### 4.3 配置 mapred-site.xml

`mapred-site.xml`配置如下：
```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<!--
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License. See accompanying LICENSE file.
-->
<!-- Put site-specific property overrides in this file. -->
<configuration>
   <property>
      <name>mapred.job.tracker</name>
      <value>localhost:9001</value>
   </property>
</configuration>
```

运行`Hadoop`的时候可能会找不到`jdk`，需要我们修改`hadoop.env.sh`脚本文件，唯一需要修改的环境变量就是`JAVE_HOME`，其他选项都是可选的：
```
export JAVA_HOME=/home/xiaosi/opt/jdk-1.8.0
```

### 5. 运行

#### 5.1 初始化HDFS系统

在配置完成后，运行`hadoop`前，要初始化`HDFS`系统，在`bin/`目录下执行如下命令：
```
xiaosi@yoona:~/opt/hadoop-2.7.3$ ./bin/hdfs namenode -format
```
#### 5.2 启动

开启`NameNode`和`DataNode`守护进程：
```
xiaosi@yoona:~/opt/hadoop-2.7.3$ ./sbin/start-dfs.sh
Starting namenodes on [localhost]
localhost: starting namenode, logging to /home/xiaosi/opt/hadoop-2.7.3/logs/hadoop-xiaosi-namenode-yoona.out
localhost: starting datanode, logging to /home/xiaosi/opt/hadoop-2.7.3/logs/hadoop-xiaosi-datanode-yoona.out
Starting secondary namenodes [0.0.0.0]
0.0.0.0: starting secondarynamenode, logging to /home/xiaosi/opt/hadoop-2.7.3/logs/hadoop-xiaosi-secondarynamenode-yoona.out
```
通过`jps`命令查看`namenode`和`datanode`是否已经启动起来：
```
xiaosi@yoona:~/opt/hadoop-2.7.3$ jps
13400 SecondaryNameNode
13035 NameNode
13197 DataNode
13535 Jps
```
从启动日志我们可以知道，日志信息存储在`hadoop-2.7.3/logs/`目录下，如果启动过程中有任何问题，可以通过查看日志来确认问题原因。

### 6. Yarn模式安装

#### 6.1 配置

修改`yarn-site.xml`，添加如下配置：
```xml
<configuration>
   <property>
      <name>yarn.nodemanager.aux-services</name>
      <value>mapreduce.shuffle</value>
   </property>
   <property>
      <name>yarn.nodemanager.aux-services.mapreduce.shuffle.class</name>
      <value>org.apache.hadoop.mapred.ShuffleHandler</value>
   </property>
</configuration>
```
修改`mapred-site.xml`，做如下修改：
```xml
<property>
   <name>mapreduce.framework.name</name>
   <value>yarn</value>
</property>
```

本地模式下是`value`值是`local`，`yarn`模式下`value`值是`yarn`。

#### 6.2 启动yarn

启动`yarn`：
```
xiaosi@yoona:~/opt/hadoop-2.7.3$ sbin/start-yarn.sh
starting yarn daemons
starting resourcemanager, logging to /home/xiaosi/opt/hadoop-2.7.3/logs/yarn-xiaosi-resourcemanager-yoona.out
localhost: starting nodemanager, logging to /home/xiaosi/opt/hadoop-2.7.3/logs/yarn-xiaosi-nodemanager-yoona.out
```
关闭yarn:
```
xiaosi@yoona:~/opt/hadoop-2.7.3$ sbin/stop-yarn.sh
stopping yarn daemons
stopping resourcemanager
localhost: stopping nodemanager
```
#### 6.3 检查是否运行成功

打开浏览器，输入：http://localhost:8088/cluster
