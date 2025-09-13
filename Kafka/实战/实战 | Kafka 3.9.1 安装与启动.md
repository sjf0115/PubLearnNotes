### 1. 下载代码

[下载](https://dlcdn.apache.org/kafka/3.9.1/kafka_2.12-3.9.1.tgz) 3.9.1 版本并解压缩:
```
tar -zxvf kafka_2.12-3.9.1.tgz -C /opt/workspace/
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

### 2. 安装 ZooKeeper

Kafka 依赖 [ZooKeeper](https://zookeeper.apache.org/)，如果你还没有 ZooKeeper 服务器，你需要先启动一个 ZooKeeper 服务器。可以先参考[实战 | ZooKeeper 3.8.4 伪分布式模式安装与启动](https://smartsi.blog.csdn.net/article/details/150474174)来安装 ZooKeeper。

### 3. 配置 Kafka

根据提供的默认配置复制生成三个节点的配置文件：
```bash
192:config smartsi$ cp server.properties server-9092.properties
192:config smartsi$ cp server.properties server-9093.properties
192:config smartsi$ cp server.properties server-9094.properties
```

第一个 broker 配置 `server-9092.properties` 修改如下:
```
broker.id=0
listeners=PLAINTEXT://127.0.0.1:9092
advertised.listeners=PLAINTEXT://127.0.0.1:9092
# 持久化数据目录
log.dirs=/opt/workspace/kafka/logs/9092
zookeeper.connect=localhost:2181/kafka-3.9.1
```
> 运行起来至少要配置四项。上面的前四项。

第二个 broker 配置 `server-9093.properties` 修改如下:
```
broker.id=1
listeners=PLAINTEXT://127.0.0.1:9093
advertised.listeners=PLAINTEXT://127.0.0.1:9093
log.dirs=/opt/workspace/kafka/logs/9093
zookeeper.connect=localhost:2181/kafka-3.9.1
```
第三个 broker 配置 `server-9094.properties` 修改如下:
```
broker.id=2
listeners=PLAINTEXT://127.0.0.1:9094
advertised.listeners=PLAINTEXT://127.0.0.1:9094
log.dirs=/opt/workspace/kafka/logs/9094
zookeeper.connect=localhost:2181/kafka-3.9.1
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
zookeeper.connect=localhost:2181/kafka-3.9.1
```
`zookeeper.connect` 是一个逗号分隔的 `host:port` 键值对，每个对应一个 zk 服务器。例如 `127.0.0.1:3000,127.0.0.1:3001,127.0.0.1:3002`。你还可以将可选的客户端命名空间 Chroot 字符串追加到 URL 上以指定所有 kafka 的 Znode 的根目录。另外这个 `kafka-3.9.1` 这个节点需要你提前建立。让 Kafka 把他需要的数据结构都建立在这个节点下，否则会建立在根节点 `/` 节点下。

(4) 日志相关:
```
log.dirs=/opt/workspace/kafka/logs/9092
```
Kafka 存储 Log 的目录。


### 4. 创建启动和停止脚本

有两种方式可以启动 Kafka 服务器:
```bash
# 第一种方式（推荐）
bin/kafka-server-start.sh -daemon config/server.properties
# 第二种方式
nohup bin/kafka-server-start.sh config/server.properties &
```

我们以第一种方式启动 Kafka 服务器。为了方便，在 bin 创建 `start-kafka-cluster.sh` 启动脚本：
```bash
#!/bin/bash

KAFKA_HOME="/opt/workspace/kafka"

echo "启动 Kafka 第一个实例"
$KAFKA_HOME/bin/kafka-server-start.sh -daemon $KAFKA_HOME/config/server-9092.properties
sleep 2

echo "启动 Kafka 第二个实例"
$KAFKA_HOME/bin/kafka-server-start.sh -daemon $KAFKA_HOME/config/server-9093.properties
sleep 2

echo "启动 Kafka 第三个实例"
$KAFKA_HOME/bin/kafka-server-start.sh -daemon $KAFKA_HOME/config/server-9094.properties
sleep 2

echo "Kafka 集群启动结束"
```
在 bin 创建 `stop-kafka-cluster.sh` 启动脚本：
```bash
#!/bin/bash

KAFKA_HOME="/opt/workspace/kafka"

echo "停止 Kafka"
$KAFKA_HOME/bin/kafka-server-stop.sh
```

### 5. 启动 Kafka 服务器

运行 `start-kafka-cluster.sh` 启动脚本即可创建 Kafka 服务器：
```
smarsi:bin smartsi$ . start-kafka-cluster.sh
启动 Kafka 第一个实例
启动 Kafka 第二个实例
启动 Kafka 第三个实例
Kafka 集群启动结束
```
查看进程和端口:
```
smarsi:bin smartsi$ jps
14496 Kafka
14119 Kafka
13742 Kafka
16751 Jps
...
```

我们现在看一下 Kafka 在 ZooKeeper 上创建的节点:
```
[zk: 127.0.0.1:2181(CONNECTED) 0] ls /kafka-3.9.1
[admin, brokers, cluster, config, consumers, controller, controller_epoch, feature, isr_change_notification, latest_producer_id_block, log_dir_event_notification]
```
看一下我们在 ZooKeeper 上注册的三个 broker:
```
[zk: 127.0.0.1:2181(CONNECTED) 1] ls /kafka-3.9.1/brokers/ids
[0, 1, 2]
[zk: 127.0.0.1:2181(CONNECTED) 2] get /kafka-3.9.1/brokers/ids/0
{"listener_security_protocol_map":{"PLAINTEXT":"PLAINTEXT"},"endpoints":["PLAINTEXT://127.0.0.1:9092"],"jmx_port":-1,"features":{},"host":"127.0.0.1","timestamp":"1757774749541","port":9092,"version":5}
```

### 6. 测试 Kafka

#### 6.1 创建Topic

首先创建一个名为 `hello-world` 的 Topic，它有一个分区和一个副本：
```
smarsi:bin smartsi$ kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic hello-world
Created topic hello-world.
```
运行 `list` 命令来查看这个 Topic:
```
smarsi:bin smartsi$ kafka-topics.sh --list --bootstrap-server localhost:9092
__consumer_offsets
hello-world
...
```
可以看到我们创建的名为 `hello-world` 的 Topic 已经创建成功。

#### 6.2 启动生产者

Kafka 自带一个命令行客户端，它从文件或标准输入中获取输入，并将其作为消息发送到 Kafka 集群。默认情况下，每行将作为单独的消息发送。运行 Producer (生产者)，然后在控制台输入一些消息以发送到服务器:
```
smarsi:bin smartsi$ kafka-console-producer.sh --bootstrap-server localhost:9092 --topic hello-world
>hello
>world
```
#### 6.3 启动消费者

Kafka 还有一个命令行 Consumer（消费者），将消息转储到标准输出:
```
smarsi:bin smartsi$ kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic hello-world --from-beginning
hello
world
```
如果你将上述命令在不同的终端中运行，那么现在就可以将消息输入到生产者终端中，并将它们在消费终端中显示出来。

参考:[Quickstart](http://kafka.apache.org/quickstart)
