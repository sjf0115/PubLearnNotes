---
layout: post
author: sjf0115
title: ZooKeeper可视化监控ZKUI
date: 2019-09-02 19:04:15
tags:
  - ZooKeeper

categories: ZooKeeper
permalink: zkui-zookeeper-ui-dashboard
---

### 1. 简介

ZKUI 提供了一个图形化管理界面，可以针对 ZooKeepr 的节点值进行 CRUD 操作，同时也提供了安全认证。

### 2. 要求

由于 ZKUI 是基于 Java 开发的，所以需要安装 JDK。要求使用 Java 7 以上版本。

### 3. 安装

因为 ZKUI 需要手工进行编译、构建打包，所以还需要下载安装 Maven。从[代码库](https://github.com/DeemOpen/zkui)下载源码进行编译:
```
# 克隆代码
smartsi:software smartsi$ git clone git@github.com:DeemOpen/zkui.git
smartsi:software cd zkui/
# 编译、构建、打包
smartsi:zkui smartsi$ mvn clean install
```
编译成功后会生成如下文件:
```
smartsi:zkui smartsi$ ll
total 96
drwxr-xr-x  15 smartsi  staff    480  9  2 14:33 ./
drwxr-xr-x   3 smartsi  staff     96  9  2 11:44 ../
drwxr-xr-x  13 smartsi  staff    416  9  2 11:45 .git/
-rw-r--r--   1 smartsi  staff     25  9  2 11:45 .gitignore
-rw-r--r--   1 smartsi  staff  11358  9  2 11:45 LICENSE-2.0.txt
-rw-r--r--   1 smartsi  staff    416  9  2 11:45 Makefile
-rw-r--r--   1 smartsi  staff   6216  9  2 11:45 README.md
-rw-r--r--   1 smartsi  staff   2357  9  2 11:45 config.cfg
drwxr-xr-x   5 smartsi  staff    160  9  2 11:45 docker/
drwxr-xr-x   8 smartsi  staff    256  9  2 11:45 images/
-rw-r--r--   1 smartsi  staff   1746  9  2 11:45 nbactions.xml
-rw-r--r--   1 smartsi  staff   5294  9  2 11:45 pom.xml
-rw-r--r--   1 smartsi  staff     43  9  2 11:45 run.sh
drwxr-xr-x   4 smartsi  staff    128  9  2 11:45 src/
drwxr-xr-x  10 smartsi  staff    320  9  2 11:46 target/
```
将 `zkui` 下的 `config.cfg` 和 `target` 下的 `zkui-2.0-SNAPSHOT-jar-with-dependencies.jar` 复制到我们的工作目录下 `~/opt/zkui`:
```
smartsi:opt cp ../software/zkui/target/zkui-2.0-SNAPSHOT-jar-with-dependencies.jar zkui/
smartsi:opt cp ../software/zkui/config.cfg zkui/
```
#### 4. 配置

修改 `config.cfg` 配置:
```
# 指定端口
serverPort=9090
# ZooKeeper 实例
zkServer=localhost:2181,localhost:2181
# 生产环境设置为 prod、开发环境设置为 dev。设置为 dev 每次会清除历史记录
env=prod
# MySQL 数据库配置
jdbcClass=com.mysql.jdbc.Driver
jdbcUrl=jdbc:mysql://localhost:3306/zkui
jdbcUser=root
jdbcPwd=zxcvbnm1
# 设置登录用户及其权限
userSet = {"users": [{ "username":"admin" , "password":"admin","role": "ADMIN" },{ "username":"test" , "password":"123","role": "USER" }]}
```
上面配置了需要连接的 ZooKeeper 集群的IP地址和端口。多个 zk 实例以逗号进行分割。例如：`server1:2181, server2:2181`。第一台服务器应始终是领导者。ZKUI 默认的用户名与密码是 `admin/manager` ，上面配置中我们修改为 `admin/admin`，同时修改用户 `appconfig` 的账号密码为 `test/123`。在这我们使用 MySQL 存储历史记录，必须注释掉 h2 数据库配置。

### 5. 运行

现在使用如下命令启动 ZKUI:
```
nohup java -jar zkui-2.0-SNAPSHOT-jar-with-dependencies.jar ＆
```
现在我们可以通过Web界面(http://localhost:9090)访问 ZKUI:
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zkui-zookeeper-ui-dashboard-1.jpg?raw=true)

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/ZooKeeper/zkui-zookeeper-ui-dashboard-2.jpg?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

参考: [zkui - Zookeeper UI Dashboard](https://github.com/DeemOpen/zkui)
