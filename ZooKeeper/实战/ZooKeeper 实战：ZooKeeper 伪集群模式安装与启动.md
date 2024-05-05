---
layout: post
author: sjf0115
title: ZooKeeper 伪集群模式安装与启动
date: 2019-09-28 13:16:01
tags:
  - ZooKeeper

categories: ZooKeeper
permalink: zookeeper-standalone-setup-and-run
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

如果我们手上只有一台机器，那么我们可以作为单机模式进行部署，资源明显有点浪费。如果我们按照集群模式部署的话，那么就需要借助硬件上的虚拟化技术，把一台物理机转换成几台虚拟机，不过这样的操作成本太高。幸运的是，和其他所有分布式系统一样，ZooKeeper 也允许我们在一台机器上完成一个伪集群的搭建。

伪集群就是说集群所有的机器都在一台机器上，但是还是以集群的特性对外提供服务。这种模式和集群模式非常类似，只是把 zoo.cfg 做一些修改:
```
tickTime = 2000
dataDir = /opt/zookeeper/data
clientPort = 2181
initLimit = 10
syncLimit = 5
server.1=127.0.0.1:2888:3888  
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
在 zoo.cfg 配置中，每一行的机器配置都是同一个IP地址，但是后面的端口号配置已经不一样了。因为在同一台机器上启动多个进程，就必须绑定不同的端口。

说明：

参数|默认值|描述
---|---
initLimit | 10 | 对于从节点最初连接到主节点时的超时时间，单位为tick值的倍数。
syncLimit | 5 |对于主节点与从节点进行同步操作时的超时时间，单位为tick值的倍数。
dataDir | `/tmp/zookeeper` |用于配置内存数据库保存的模糊快照的目录。文件信息都存放在data目录下。
clientPort | 2181 |表示客户端所连接的服务器监听的端口号，默认是2181。即zookeeper对外提供访问的端口号。

`server.A=B:C:D` 其中A是一个数字，表示这是第几号服务器。B是这台服务器的IP地址。C表示这台服务器与集群中的Leader服务器交换信息的端口。D表示的是万一集群中的Leader服务器挂了，需要一个端口来重新进行选举，选出一个新的Leader，这个端口就是用来执行选举时服务器相互通信的端口。如果是伪集群的配置方式，由于B都是一样，所以不同的zookeeper实例通信端口号不能一样，所以要给他们分配不同的端口号。

第一台机器的配置如下：
```
tickTime = 2000
dataDir = /opt/zookeeper/zk1/data
clientPort = 2181
initLimit = 10
syncLimit = 5
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
第二台机器的配置如下：
```
tickTime = 2000
dataDir = /opt/zookeeper/zk2/data
clientPort = 2182
initLimit = 10
syncLimit = 5
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
第三台机器的配置如下：
```
tickTime = 2000
dataDir = /opt/zookeeper/zk3/data
clientPort = 2183
initLimit = 10
syncLimit = 5
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```

### 3. 创建myid文件

分别在对应 data 目录下新建 `myid` 文件，并进行修改：
- 在第一台机器对应的文件中输入1
- 在第一台机器对应的文件中输入2
- 在第一台机器对应的文件中输入3

需要确保每台服务器的 myid 文件中数字不同，并且和自己所在机器的 zoo.cfg 中 server.id=host:port:port 的id值一样。另外，id的范围是1～255。

### 4. 配置环境变量

修改 `/etc/profile` 配置环境变量：
```
# ZOOKEEPER
export ZOOKEEPER_HOME=/opt/zookeeper
export PATH=${ZOOKEEPER_HOME}/bin:$PATH
```
运行命令 `source /etc/profile` 使环境变量生效。

### 5. 启动ZooKeeper

分别启动三台 ZooKeeper 服务器，在根目录下执行如下命令：
```
bin/zkServer.sh start /opt/zookeeper/conf/zoo1.cfg
bin/zkServer.sh start /opt/zookeeper/conf/zoo2.cfg
bin/zkServer.sh start /opt/zookeeper/conf/zoo3.cfg
```
启动过程中会输出如下信息：
```
smartsi:zookeeper smartsi$ bin/zkServer.sh start conf/zoo1.cfg
ZooKeeper JMX enabled by default
Using config: conf/zoo1.cfg
Starting zookeeper ... STARTED
```
当对三台服务器启动后，我们用 `zkServer.sh status` 命令来查看启动状态：
```
smartsi:zookeeper smartsi$ zkServer.sh status /opt/zookeeper/conf/zoo3.cfg
ZooKeeper JMX enabled by default
Using config: conf/zoo3.cfg
Mode: follower
smartsi:zookeeper smartsi$ zkServer.sh status /opt/zookeeper/conf/zoo1.cfg
ZooKeeper JMX enabled by default
Using config: conf/zoo1.cfg
Mode: follower
smartsi:zookeeper smartsi$ zkServer.sh status /opt/zookeeper/conf/zoo2.cfg
ZooKeeper JMX enabled by default
Using config: conf/zoo2.cfg
Mode: leader
```

> 三台服务器会选择一台做为leader，另两台为follower。

### 6. 服务器验证

启动完成后，可以使用如下命令来检查服务器启动是否正常：
```
smartsi:zookeeper smartsi$ telnet 127.0.0.1 2181
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
stat
Zookeeper version: 3.4.12-e5259e437540f349646870ea94dc2658c4e44b3b, built on 03/27/2018 03:55 GMT
Clients:
 /127.0.0.1:51068[0](queued=0,recved=1,sent=0)

Latency min/avg/max: 0/0/0
Received: 465
Sent: 2
Connections: 1
Outstanding: 0
Zxid: 0x0
Mode: follower
Node count: 4
Connection closed by foreign host.
```
上面就是通过 telnet 方式，使用 stat 命令进行服务器启动的验证，如果出现和上面类似的输出信息，就说明服务器已经正常启动了。

集群模式和单机模式下输出的服务器验证信息基本一致，只有Mode属性不一样，在集群模式中，Mode 显示的是follower，或者 leader。在单机模式中，Mode 显示的是 standalone。

### 7. 连接到ZooKeeper

使用如下命令即可连接到其中一台ZooKeeper服务器：
```
smartsi:bin smartsi$ zkCli.sh -server 127.0.0.1:2181
Connecting to 127.0.0.1:2181
Welcome to ZooKeeper!
JLine support is enabled

WATCHER::

WatchedEvent state:SyncConnected type:None path:null
[zk: 127.0.0.1:2181(CONNECTED) 0]
```
其他自动实现同步，客户端只需要和一台保持连接即可。

成功连接后，系统会输出 ZooKeeper 的相关配置信息和相关环境，并在屏幕上输出 `Welcome to ZooKeeper!` 等信息。
