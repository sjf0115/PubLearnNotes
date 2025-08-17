### 1. 安装

要在你的计算机上安装 ZooKeeper 框架，请访问该[链接](http://zookeeper.apache.org/releases.html)并下载最新版本的ZooKeeper。到目前为止，最新稳定版本的 ZooKeeper 是 3.8.4。

使用以下命令提取tar文件：
```
$ tar -zxf apache-zookeeper-3.8.4-bin.tar.gz -C /opt/workspace/
```
创建软连接，便于升级：
```
$ sudo ln -s apache-zookeeper-3.8.4-bin zookeeper
```
创建数据目录：
```
$ cd zookeeper
$ mkdir data
```

### 2. 配置

如果我们手上只有一台机器，那么我们可以作为单机模式进行部署，资源明显有点浪费。如果我们按照集群模式部署的话，那么就需要借助硬件上的虚拟化技术，把一台物理机转换成几台虚拟机，不过这样的操作成本太高。幸运的是，和其他所有分布式系统一样，ZooKeeper 也允许我们在一台机器上完成一个伪集群的搭建。

伪集群就是说集群所有的机器都在一台机器上，但是还是以集群的特性对外提供服务。这种模式和集群模式非常类似，只是把 zoo.cfg 做一些修改:
```bash
tickTime=2000
dataDir=/opt/workspace/zookeeper/data
clientPort=2181
initLimit=10
syncLimit=5
admin.serverPort=2081
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
在 zoo.cfg 配置中，每一行的机器配置都是同一个IP地址，但是后面的端口号配置已经不一样了。因为在同一台机器上启动多个进程，就必须绑定不同的端口。

说明：

| 参数|默认值|描述|
| :------------- | :------------- | :------------- |
|initLimit | 10 | 对于从节点最初连接到主节点时的超时时间，单位为tick值的倍数。|
|syncLimit | 5 |对于主节点与从节点进行同步操作时的超时时间，单位为tick值的倍数。|
|dataDir | `/tmp/zookeeper` |用于配置内存数据库保存的模糊快照的目录。文件信息都存放在data目录下。|
|clientPort | 2181 |表示客户端所连接的服务器监听的端口号，默认是2181。即zookeeper对外提供访问的端口号。|

`server.A=B:C:D` 其中A是一个数字，表示这是第几号服务器。B是这台服务器的IP地址。C表示这台服务器与集群中的Leader服务器交换信息的端口。D表示的是万一集群中的Leader服务器挂了，需要一个端口来重新进行选举，选出一个新的Leader，这个端口就是用来执行选举时服务器相互通信的端口。如果是伪集群的配置方式，由于B都是一样，所以不同的zookeeper实例通信端口号不能一样，所以要给他们分配不同的端口号。

第一台机器的配置如下：
```bash
tickTime=2000
dataDir=/opt/workspace/zookeeper/data/zk1
clientPort=2181
initLimit=10
syncLimit=5
admin.serverPort=2081
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
> conf/zoo1.cfg

第二台机器的配置如下：
```bash
tickTime=2000
dataDir=/opt/workspace/zookeeper/data/zk2
clientPort=2182
initLimit=10
syncLimit=5
admin.serverPort=2082
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
> conf/zoo2.cfg

第三台机器的配置如下：
```bash
tickTime=2000
dataDir=/opt/workspace/zookeeper/data/zk3
clientPort=2183
initLimit=10
syncLimit=5
admin.serverPort=2083
server.1=127.0.0.1:2888:3888
server.2=127.0.0.1:2889:3889
server.3=127.0.0.1:2890:3890
```
> conf/zoo3.cfg

需要注意的时，配置中需要添加 `admin.serverPort` 参数，否与会遇到 [Zookeeper 3.8.4 Problem starting AdminServer on address 0.0.0.0, port 8080](https://smartsi.blog.csdn.net/article/details/150474014) 问题。

### 3. 创建myid文件

需要对应 data 目录下新建 `myid` 文件，并进行修改：
- 在第一台机器对应的文件中输入1
- 在第一台机器对应的文件中输入2
- 在第一台机器对应的文件中输入3

```bash
echo "1" > /opt/workspace/zookeeper/data/zk1/myid
echo "2" > /opt/workspace/zookeeper/data/zk2/myid
echo "3" > /opt/workspace/zookeeper/data/zk3/myid
```

需要确保每台服务器的 myid 文件中数字不同，并且和自己所在机器的 zoo.cfg 中 server.id=host:port:port 的id值一样。另外，id的范围是1～255。

### 4. 配置环境变量

修改 `/etc/profile` 配置环境变量：
```bash
# ZOOKEEPER
export ZOOKEEPER_HOME=/opt/workspace/zookeeper
export PATH=${ZOOKEEPER_HOME}/bin:$PATH
```
运行命令 `source /etc/profile` 使环境变量生效。

### 5. 创建启动和停止脚本

在 bin 创建 `start-zk-cluster.sh` 启动脚本：
```bash
#!/bin/bash

ZK_HOME="/opt/workspace/zookeeper"

echo "启动 Zookeeper 第一个实例"
$ZK_HOME/bin/zkServer.sh start $ZK_HOME/conf/zoo1.cfg
sleep 2

echo "启动 Zookeeper 第二个实例"
$ZK_HOME/bin/zkServer.sh start $ZK_HOME/conf/zoo2.cfg
sleep 2

echo "启动 Zookeeper 第三个实例"
$ZK_HOME/bin/zkServer.sh start $ZK_HOME/conf/zoo3.cfg
sleep 2

echo "ZooKeeper集群启动结束"

echo "----------------------------------------------"
echo "查看 Zookeeper 第一个实例状态"
$ZK_HOME/bin/zkServer.sh status $ZK_HOME/conf/zoo1.cfg
sleep 2

echo "查看 Zookeeper 第二个实例状态"
$ZK_HOME/bin/zkServer.sh status $ZK_HOME/conf/zoo2.cfg
sleep 2

echo "查看 Zookeeper 第三个实例状态"
$ZK_HOME/bin/zkServer.sh status $ZK_HOME/conf/zoo3.cfg
sleep 2
```

在 bin 创建 `stop-zk-cluster.sh` 停止脚本：
```bash
#!/bin/bash

ZK_HOME="/opt/workspace/zookeeper"

echo "停止 Zookeeper 第一个实例"
$ZK_HOME/bin/zkServer.sh stop $ZK_HOME/conf/zoo1.cfg
sleep 2

echo "停止 Zookeeper 第二个实例"
$ZK_HOME/bin/zkServer.sh stop $ZK_HOME/conf/zoo2.cfg
sleep 2

echo "停止 Zookeeper 第三个实例"
$ZK_HOME/bin/zkServer.sh stop $ZK_HOME/conf/zoo3.cfg
sleep 2

echo "ZooKeeper集群停止结束"
```

### 6. 启动 ZooKeeper 集群

在 bin 目录下执行如下命令启动 Zookeeper：
```bash
. start-zk-cluster.sh
```
启动过程中会输出如下信息：
```bash
192:bin smartsi$ . start-zk-cluster.sh
启动 Zookeeper 第一个实例
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo1.cfg
Starting zookeeper ... STARTED
启动 Zookeeper 第二个实例
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo2.cfg
Starting zookeeper ... STARTED
启动 Zookeeper 第三个实例
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo3.cfg
Starting zookeeper ... STARTED
ZooKeeper集群启动结束
----------------------------------------------
查看 Zookeeper 第一个实例状态
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo1.cfg
Client port found: 2181. Client address: localhost. Client SSL: false.
Mode: follower
查看 Zookeeper 第二个实例状态
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo2.cfg
Client port found: 2182. Client address: localhost. Client SSL: false.
Mode: leader
查看 Zookeeper 第三个实例状态
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo3.cfg
Client port found: 2183. Client address: localhost. Client SSL: false.
Mode: follower
```

> 三台服务器会选择一台做为leader，另两台为follower。

### 7. 服务器验证

启动完成后，可以使用如下命令来检查服务器启动是否正常：
```bash
192:bin smartsi$ echo srvr | nc 127.0.0.1 2181
Zookeeper version: 3.8.4-9316c2a7a97e1666d8f4593f34dd6fc36ecc436c, built on 2024-02-12 22:16 UTC
Latency min/avg/max: 0/0.0/0
Received: 3
Sent: 2
Connections: 1
Outstanding: 0
Zxid: 0x0
Mode: follower
Node count: 5
192:bin smartsi$
192:bin smartsi$
192:bin smartsi$ echo srvr | nc 127.0.0.1 2182
Zookeeper version: 3.8.4-9316c2a7a97e1666d8f4593f34dd6fc36ecc436c, built on 2024-02-12 22:16 UTC
Latency min/avg/max: 0/0.0/0
Received: 2
Sent: 1
Connections: 1
Outstanding: 0
Zxid: 0x300000000
Mode: leader
Node count: 5
Proposal sizes last/min/max: -1/-1/-1
192:bin smartsi$ echo srvr | nc 127.0.0.1 2183
Zookeeper version: 3.8.4-9316c2a7a97e1666d8f4593f34dd6fc36ecc436c, built on 2024-02-12 22:16 UTC
Latency min/avg/max: 0/0.0/0
Received: 2
Sent: 1
Connections: 1
Outstanding: 0
Zxid: 0x300000000
Mode: follower
Node count: 5
```
使用 srvr 命令进行服务器启动的验证，如果出现和上面类似的输出信息，就说明服务器已经正常启动了。

### 8. 连接到 ZooKeeper

使用如下命令即可连接到其中一台 ZooKeeper 服务器：
```bash
192:bin smartsi$ zkCli.sh -server 127.0.0.1:2181
Connecting to 127.0.0.1:2181
...
Welcome to ZooKeeper!
...

WATCHER::

WatchedEvent state:SyncConnected type:None path:null
[zk: 127.0.0.1:2181(CONNECTED) 0]
```
其他自动实现同步，客户端只需要和一台保持连接即可。成功连接后，系统会输出 ZooKeeper 的相关配置信息和相关环境，并在屏幕上输出 `Welcome to ZooKeeper!` 等信息。

### 9. 停止 Zookeeper 集群

在 bin 目录下执行如下命令启动 Zookeeper：
```bash
. stop-zk-cluster.sh
```
启动过程中会输出如下信息：
```bash
192:bin smartsi$ . stop-zk-cluster.sh
停止 Zookeeper 第一个实例
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo1.cfg
Stopping zookeeper ... STOPPED
停止 Zookeeper 第二个实例
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo2.cfg
Stopping zookeeper ... STOPPED
停止 Zookeeper 第三个实例
ZooKeeper JMX enabled by default
Using config: /opt/workspace/zookeeper/conf/zoo3.cfg
Stopping zookeeper ... STOPPED
ZooKeeper集群停止结束
```
