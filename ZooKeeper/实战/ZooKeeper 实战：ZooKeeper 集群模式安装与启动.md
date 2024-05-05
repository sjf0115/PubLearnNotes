---
layout: post
author: sjf0115
title: ZooKeeper 集群模式安装与启动
date: 2018-08-14 12:30:01
tags:
  - ZooKeeper

categories: ZooKeeper
permalink: zookeeper-setup-and-run
---

### 1. 安装

要在你的计算机上安装 ZooKeeper 框架，请访问该[链接](http://zookeeper.apache.org/releases.html)并下载最新版本的ZooKeeper。
到目前为止，最新稳定版本的 ZooKeeper是3.4.12(ZooKeeper-3.4.12.tar.gz)。

使用以下命令提取tar文件：
```
cd ~/opt/
$ tar -zxf zookeeper-3.4.12.tar.gz
```
创建软连接，便于升级：
```
$ sudo ln -s zookeeper-3.4.12/ zookeeper
```
创建数据目录：
```
$ cd zookeeper
$ mkdir data
```

### 2. 配置

修改 `conf/zoo.cfg` 配置文件：
```
tickTime = 2000
dataDir = /Users/smartsi/opt/zookeeper/data
clientPort = 2181
initLimit = 10
syncLimit = 5
server.1=101.34.82.15:2888:3888  
server.2=101.34.82.16:2888:3888
server.3=101.34.82.17:2888:3888
```
> 我们在三台机器上搭建 ZooKeeper 集群：101.34.82.15，101.43.28.1６，101.43.28.1７

说明：

参数|默认值|描述
---|---|---
initLimit | 10 | 对于从节点最初连接到主节点时的超时时间，单位为tick值的倍数。
syncLimit | 5 |对于主节点与从节点进行同步操作时的超时时间，单位为tick值的倍数。
dataDir | `/tmp/zookeeper` |用于配置内存数据库保存的模糊快照的目录。文件信息都存放在data目录下。
clientPort | 2181 |表示客户端所连接的服务器所监听的端口号，默认是2181。即zookeeper对外提供访问的端口号。

> server.A=B:C:D 其中A是一个数字，表示这是第几号服务器。B是这台服务器的IP地址。C表示这台服务器与集群中的Leader服务器交换信息的端口。D表示的是万一集群中的Leader服务器挂了，需要一个端口来重新进行选举，选出一个新的Leader，这个端口就是用来执行选举时服务器相互通信的端口。如果是伪集群的配置方式，由于B都是一样，所以不同的zookeeper实例通信端口号不能一样，所以要给他们分配不同的端口号。

### 3. 创建myid文件

分别在三台机器上我们创建的data目录下新建一个 `myid` 文件，并进行修改：
- 在 101.34.82.15 机器上输入1
- 在 101.34.82.16 机器上输入2
- 在 101.34.82.17 机器上输入3

> 需要确保每台服务器的 myid 文件中数字不同，并且和自己所在机器的 zoo.cfg 中 server.id=host:port:port 的id值一样。另外，id的范围是1～255。

### 4. 配置环境变量

分别在三台机器的上修改 `/etc/profile` 配置环境变量：
```
# ZOOKEEPER
export ZOOKEEPER_HOME=/Users/smartsi/opt/zookeeper
export PATH=${ZOOKEEPER_HOME}/bin:$PATH
```
运行命令 `source /etc/profile` 使环境变量生效。

### 5. 启动ZooKeeper

分别在三台机器的上启动ZooKeeper，进入bin目录下执行：
```
[sjf0115@ying /Users/smartsi/opt/zookeeper/bin]$ sudo zkServer.sh start
ZooKeeper JMX enabled by default
Using config: /Users/smartsi/opt/zookeeper/bin/../conf/zoo.cfg
Starting zookeeper ... STARTED
```
当对三台机器启动后，我们用 `zkServer.sh status` 命令来查看启动状态：
```
# 101.34.82.16
ZooKeeper JMX enabled by default
Using config: /Users/smartsi/opt/zookeeper/bin/../conf/zoo.cfg
Mode: leader

# 101.34.82.15
ZooKeeper JMX enabled by default
Using config: /Users/smartsi/opt/zookeeper/bin/../conf/zoo.cfg
Mode: follower

# 101.34.82.17
ZooKeeper JMX enabled by default
Using config: /Users/smartsi/opt/zookeeper/bin/../conf/zoo.cfg
Mode: follower
```

> 三台机器会选择一台做为leader，另两台为follower。

### 6. 连接到ZooKeeper

使用如下命令即可连接到其中一台ZooKeeper服务器：
```
[sjf0115@ying ~]$ zkCli.sh -server 101.34.82.17:2181
Connecting to 101.34.82.17:2181
...
Welcome to ZooKeeper!
...
WATCHER::

WatchedEvent state:SyncConnected type:None path:null
```
其他自动实现同步，客户端只需要和一台保持连接即可。

成功连接后，系统会输出ZooKeeper的相关配置信息和相关环境，并在屏幕上输出 `Welcome to ZooKeeper!` 等信息。
