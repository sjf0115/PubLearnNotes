---
layout: post
author: sjf0115
title: Hadoop无法访问50070端口
date: 2019-06-16 17:36:01
tags:
  - Hadoop
  - TroubleShooting

categories: Hadoop
permalink: trouble-shooting-cannot-access-port-50070-in-hadoop
---

最近在搭建 Hadoop（3.1.2）环境时遇到了一件比较奇葩的问题。Hadoop 配置文件正常，各个守护进程正常启动，但是启动后无法在浏览器中访问 50070 端口，但是又可以访问 8088 端口:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/trouble-shooting-cannot-access-port-50070-in-hadoop-1.png?raw=true)

参考网上的各中解决方案，有的方案没有解决我的问题，最终发现如下方案可以解决我的问题。有可能是 NameNode 初始化默认端口失效，于是决定手动修改配置文件设置默认端口:
```
<property>
  <name>dfs.http.address</name>
  <value>localhost:50070</value>
</property>
```
然后重新格式化 NameNode，启动 Hadoop。最终访问正常:
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hadoop/trouble-shooting-cannot-access-port-50070-in-hadoop-2.png?raw=true)

重新格式化 NameNode 之前需要清空 dfs 下的 name 和 data 文件夹以解决 DataNode 无法启动的问题。具体配置路径在 hdfs-site.xml 中配置:
```
<property>
   <name>dfs.namenode.name.dir</name>
   <value>file:/Users/xxx/tmp/hadoop/dfs/name</value>
</property>
<property>
   <name>dfs.datanode.data.dir</name>
   <value>file:/Users/xxx/tmp/hadoop/dfs/data</value>
</property>
```
