---
layout: post
author: sjf0115
title: Kafka 安装与启动
date: 2019-09-01 12:30:01
tags:
  - Kafka

categories: Kafka
permalink: kafka-setup-and-run
---

### 1. 下载代码

[下载](https://dlcdn.apache.org/kafka/3.9.1/kafka_2.12-3.9.1.tgz) 3.9.1 版本并解压缩:
```
tar -zxvf kafka_2.12-3.9.1.tgz -C /opt/workspace
```
创建软连接便于升级:
```
ln -s kafka_2.12-3.9.1/ kafka
```
配置环境变量:
```
# Kafka
export KAFKA_HOME=/opt/workspace/kafka
export PATH=${KAFKA_HOME}/bin:$PATH
```

### 2. 安装ZooKeeper

Kafka 依赖 [ZooKeeper](https://zookeeper.apache.org/)，如果你还没有 ZooKeeper 服务器，你需要先启动一个 ZooKeeper 服务器。可以先参考[ZooKeeper 安装与启动](https://smartsi.blog.csdn.net/article/details/124680579)来安装 ZooKeeper。ZooKeeper 配置如下:
```
tickTime=2000
initLimit=10
syncLimit=5
dataDir=/opt/zookeeper/data
clientPort=2181
server.1=localhost:2888:3888
```

你也可以通过与 kafka 打包在一起的便捷脚本来快速简单地创建一个单节点 ZooKeeper 实例:
```
> bin/zookeeper-server-start.sh config/zookeeper.properties
[2013-04-22 15:01:37,495] INFO Reading configuration from: config/zookeeper.properties (org.apache.zookeeper.server.quorum.QuorumPeerConfig)
...
```

### 3. 配置 Kafka

第一个 broker 配置 `server-9092.properties` 如下:
```
broker.id=0
listeners=PLAINTEXT://127.0.0.1:9092
log.dirs=../logs/broker/9092
zookeeper.connect=localhost:2181/kafka-2.3.0
zookeeper.connection.timeout.ms=6000
```
> 运行起来至少要配置四项。上面的前四项。

第二个 broker 配置 `server-9093.properties` 如下:
```
broker.id=1
listeners=PLAINTEXT://127.0.0.1:9093
log.dirs=../logs/broker/9093
zookeeper.connect=localhost:2181/kafka-2.3.0
zookeeper.connection.timeout.ms=6000
```
第三个 broker 配置 `server-9094.properties` 如下:
```
broker.id=2
listeners=PLAINTEXT://127.0.0.1:9094
log.dirs=../logs/broker/9094
zookeeper.connect=localhost:2181/kafka-2.3.0
zookeeper.connection.timeout.ms=6000
```
> 我们必须重写端口和日志目录，因为我们在同一台机器上运行这些，我们不希望所有都在同一个端口注册，或者覆盖彼此的数据。所以用端口号9092、9093、9094分别代表三个 broker。

下面具体解释一下我们的配置项:

(1) Broker相关:
```
broker.id=0
```
broker 的 Id。每一个 broker 在集群中的唯一标示，要求是正数。每个 broker 都不相同。

(2) Socket服务设置:
```
listeners=PLAINTEXT://127.0.0.1:9092
```
Socket服务器监听的地址，如果没有设置，则监听 `java.net.InetAddress.getCanonicalHostName()` 返回的地址。

(3) ZooKeeper相关:
```
zookeeper.connect=localhost:2181/kafka-2.3.0
zookeeper.connection.timeout.ms=6000
```
`zookeeper.connect` 是一个逗号分隔的 `host:port` 键值对，每个对应一个 zk 服务器。例如 `127.0.0.1:3000,127.0.0.1:3001,127.0.0.1:3002`。你还可以将可选的客户端命名空间 Chroot 字符串追加到 URL 上以指定所有 kafka 的 Znode 的根目录。另外这个 `kafka-2.3.0` 这个节点需要你提前建立。让 Kafka 把他需要的数据结构都建立在这个节点下，否则会建立在根节点 `/` 节点下。

(3) 日志相关:
```
log.dirs=../logs/broker/9092
```
Kafka存储Log的目录。

### 4. 启动 Kafka 服务器

有两种方式可以启动 Kafka 服务器:
```
# 第一种方式（推荐）
bin/kafka-server-start.sh -daemon config/server.properties
# 第二种方式
nohup bin/kafka-server-start.sh config/server.properties &
```

我们以第一种方式启动 Kafka 服务器:
```
bin/kafka-server-start.sh -daemon config/server-9092.properties
bin/kafka-server-start.sh -daemon config/server-9093.properties
bin/kafka-server-start.sh -daemon config/server-9094.properties
```
查看进程和端口:
```
smartsi:kafka smartsi$ jps
8914 DataNode
42802 Jps
9252 NodeManager
41253 Kafka
41541 Kafka
42790 Kafka
41670 ZooKeeperMain
16731
9164 ResourceManager
1997
```

我们现在看一下 Kafka 在 ZooKeeper 上创建的节点:
```
[zk: 127.0.0.1:2181(CONNECTED) 23] ls /kafka-2.3.0
[cluster, controller_epoch, controller, brokers, admin, isr_change_notification, consumers, log_dir_event_notification, latest_producer_id_block, config]
```
看一下我们在ZooKeeper上注册的两个 broker:
```
[zk: 127.0.0.1:2181(CONNECTED) 3] ls /kafka-2.3.0/brokers/ids
[0, 1, 2]
[zk: 127.0.0.1:2181(CONNECTED) 4] get /kafka-2.3.0/brokers/ids/0
{"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://127.0.0.1:9092"],"jmx_port":-1,"host":"127.0.0.1","timestamp":"1567390121522","port":9092,"version":4}
cZxid = 0x92
ctime = Mon Sep 02 10:08:41 CST 2019
mZxid = 0x92
mtime = Mon Sep 02 10:08:41 CST 2019
pZxid = 0x92
cversion = 0
dataVersion = 1
aclVersion = 0
ephemeralOwner = 0x100009088560012
dataLength = 188
numChildren = 0
[zk: 127.0.0.1:2181(CONNECTED) 5] get /kafka-2.3.0/brokers/ids/1
{"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://127.0.0.1:9093"],"jmx_port":-1,"host":"127.0.0.1","timestamp":"1567390128813","port":9093,"version":4}
cZxid = 0xa7
ctime = Mon Sep 02 10:08:48 CST 2019
mZxid = 0xa7
mtime = Mon Sep 02 10:08:48 CST 2019
pZxid = 0xa7
cversion = 0
dataVersion = 1
aclVersion = 0
ephemeralOwner = 0x100009088560014
dataLength = 188
numChildren = 0
[zk: 127.0.0.1:2181(CONNECTED) 6] get /kafka-2.3.0/brokers/ids/2
{"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://127.0.0.1:9094"],"jmx_port":-1,"host":"127.0.0.1","timestamp":"1567390749151","port":9094,"version":4}
cZxid = 0xbd
ctime = Mon Sep 02 10:19:09 CST 2019
mZxid = 0xbd
mtime = Mon Sep 02 10:19:09 CST 2019
pZxid = 0xbd
cversion = 0
dataVersion = 1
aclVersion = 0
ephemeralOwner = 0x100009088560018
dataLength = 188
numChildren = 0
```

### 5. 测试Kafka

#### 5.1 创建Topic

让我们创建一个名为 `test` 的 Topic，它有一个分区和一个副本：
```
bin/kafka-topics.sh --create --zookeeper localhost:2181/kafka-2.3.0 --replication-factor 1 --partitions 1 --topic test
```
现在我们可以运行 `list` 命令来查看这个 Topic:
```
smartsi:kafka smartsi$ bin/kafka-topics.sh --list --zookeeper localhost:2181/kafka-2.3.0
test
```
或者，你也可将代理配置为：在发布的topic不存在时，自动创建topic，而不是手动创建。

#### 5.2 启动生产者

Kafka 自带一个命令行客户端，它从文件或标准输入中获取输入，并将其作为消息发送到 Kafka 集群。默认情况下，每行将作为单独的消息发送。

运行 Producer (生产者)，然后在控制台输入一些消息以发送到服务器:
```
smartsi:kafka smartsi$ bin/kafka-console-producer.sh --broker-list localhost:9092 --topic test
>this is my first message
>this is my second message
```
#### 5.3 启动消费者

Kafka 还有一个命令行 Consumer（消费者），将消息转储到标准输出:
```
smartsi:kafka smartsi$ bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test --from-beginning
this is my first message
this is my second message
```
如果你将上述命令在不同的终端中运行，那么现在就可以将消息输入到生产者终端中，并将它们在消费终端中显示出来。

原文:[Quickstart](http://kafka.apache.org/quickstart)
