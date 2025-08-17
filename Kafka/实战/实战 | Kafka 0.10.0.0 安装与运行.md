### 1. 下载
下载地址：https://www.apache.org/dyn/closer.cgi?path=/kafka/0.10.0.0/kafka_2.11-0.10.0.0.tgz

下载版本：kafka_2.11-0.10.0.0.tgz

### 2. 解压
```
xiaosi@Qunar:~/下载$ sudo tar -zxvf kafka_2.11-0.10.0.0.tgz -C /opt/
[sudo] xiaosi 的密码： 
kafka_2.11-0.10.0.0/
kafka_2.11-0.10.0.0/LICENSE
kafka_2.11-0.10.0.0/NOTICE
kafka_2.11-0.10.0.0/bin/
kafka_2.11-0.10.0.0/bin/connect-distributed.sh
kafka_2.11-0.10.0.0/bin/connect-standalone.sh
kafka_2.11-0.10.0.0/bin/kafka-acls.sh
kafka_2.11-0.10.0.0/bin/kafka-configs.sh
kafka_2.11-0.10.0.0/bin/kafka-console-consumer.sh
kafka_2.11-0.10.0.0/bin/kafka-console-producer.sh
kafka_2.11-0.10.0.0/bin/kafka-consumer-groups.sh
kafka_2.11-0.10.0.0/bin/kafka-consumer-offset-checker.sh
kafka_2.11-0.10.0.0/bin/kafka-consumer-perf-test.sh
kafka_2.11-0.10.0.0/bin/kafka-mirror-maker.sh
```
安装完成之后：
```
xiaosi@Qunar:/opt$ cd kafka_2.11-0.10.0.0/
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ ls
bin  config  libs  LICENSE  NOTICE  site-docs
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ cd config/
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0/config$ ls
connect-console-sink.properties    consumer.properties
connect-console-source.properties  log4j.properties
connect-distributed.properties     producer.properties
connect-file-sink.properties       server.properties
connect-file-source.properties     tools-log4j.properties
connect-log4j.properties           zookeeper.properties
connect-standalone.properties
```
### 3. 启动

Kafka用到了Zookeeper，所有首先启动Zookper。如果你之前没有安装Zookeeper，可以使用Kafaka的脚本启用一个单实例的Zookkeeper服务。可以在命令的结尾加个&符号，这样就可以启动后离开控制台。
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/zookeeper-server-start.sh config/zookeeper.properties 
[sudo] xiaosi 的密码： 
[2016-08-01 21:25:20,236] INFO Reading configuration from: config/zookeeper.properties (org.apache.zookeeper.server.quorum.QuorumPeerConfig)
[2016-08-01 21:25:20,238] INFO autopurge.snapRetainCount set to 3 (org.apache.zookeeper.server.DatadirCleanupManager)
[2016-08-01 21:25:20,239] INFO autopurge.purgeInterval set to 0 (org.apache.zookeeper.server.DatadirCleanupManager)
[2016-08-01 21:25:20,239] INFO Purge task is not scheduled. (org.apache.zookeeper.server.DatadirCleanupManager)
[2016-08-01 21:25:20,239] WARN Either no config or no quorum defined in config, running  in standalone mode (org.apache.zookeeper.server.quorum.QuorumPeerMain)
[2016-08-01 21:25:20,258] INFO Reading configuration from: config/zookeeper.properties (org.apache.zookeeper.server.quorum.QuorumPeerConfig)
[2016-08-01 21:25:20,259] INFO Starting server (org.apache.zookeeper.server.ZooKeeperServerMain)
[2016-08-01 21:25:20,271] INFO Server environment:zookeeper.version=3.4.6-1569965, built on 02/20/2014 09:09 GMT (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,272] INFO Server environment:host.name=localhost (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,272] INFO Server environment:java.version=1.7.0_101 (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,272] INFO Server environment:java.vendor=Oracle Corporation (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,272] INFO Server environment:java.home=/usr/lib/jvm/java-7-openjdk-amd64/jre (org.apache.zookeeper.server.ZooKeeperServer)
....
[2016-08-01 21:25:20,272] INFO Server environment:java.library.path=/usr/java/packages/lib/amd64:/usr/lib/x86_64-linux-gnu/jni:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:/usr/lib/jni:/lib:/usr/lib (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,272] INFO Server environment:java.io.tmpdir=/tmp (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,272] INFO Server environment:java.compiler=<NA> (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,272] INFO Server environment:os.name=Linux (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,272] INFO Server environment:os.arch=amd64 (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,273] INFO Server environment:os.version=4.2.0-35-generic (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,273] INFO Server environment:user.name=root (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,273] INFO Server environment:user.home=/root (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,273] INFO Server environment:user.dir=/opt/kafka_2.11-0.10.0.0 (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,282] INFO tickTime set to 3000 (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,282] INFO minSessionTimeout set to -1 (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,282] INFO maxSessionTimeout set to -1 (org.apache.zookeeper.server.ZooKeeperServer)
[2016-08-01 21:25:20,304] INFO binding to port 0.0.0.0/0.0.0.0:2181 (org.apache.zookeeper.server.NIOServerCnxnFactory)
```

或者
```
sudo ./bin/zookeeper-server-start.sh config/zookeeper.properties &
[1] 20150
```
启动Kafka服务：
```
sudo ./bin/kafka-server-start.sh config/server.properties &
[2] 20220
```
### 3. 创建Topic

创建一个叫做“test-topic”的topic，它只有一个分区，一个副本：

```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic test-topic
Created topic "test-topic".
```
可以通过list命令查看创建的topic：

```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-topics.sh --list --zookeeper localhost:2181
test-topic
```
除了手动创建主题之外，我们还可以配置brokers，当发布消息的主题不存在时，自动创建该主题（Alternatively, instead of manually creating topics you can also configure your brokers to auto-create topics when a non-existent topic is published to）


#### 4. 发送消息

Kafka 使用一个简单的命令行客户端，从文件中或者从标准输入中读取消息并发送到Kafka集群中。默认的每条命令将发送一条消息。
运行一个producer并在控制台中输一些消息发送到服务端：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-console-producer.sh --broker-list localhost:9092 --topic test-topic
hello kafka
i am xiaosi
// 等待输入
ctrl+c可以退出发送。
```
### 5. 启动consumer

Kafka也有一个命令行consumer可以读取消息并输出到标准输出：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-console-consumer.sh --zookeeper localhost:2181 --topic test-topic --from-beginning
[sudo] xiaosi 的密码： 
hello kafka
i am xiaosi
```
你在一个终端中运行consumer命令行，另一个终端中运行producer命令行，就可以在一个终端输入消息，将会在另一个终端中输出消息（读取）。
这两个命令都有自己的可选参数，可以在运行的时候不加任何参数可以看到帮助信息。



### 6. 搭建多broker集群

到目前为止，我们已经启动了一个broker，启动一个没啥意思，对于Kafka来说，一个broker只是意味着集群个数为一，相对于启动多个broker来说，没有什么大的改变。我们只是为了感受一下Kafka的集群，所以才在本地机器上扩展为三个broker。

#### 6.1 配置

现在为每个broker创建配置文件：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo cp config/server.properties config/server1.properties 
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo cp config/server.properties config/server2.properties 
```
修改配置文件：
```
config/server-1.properties:
    broker.id=1
    listeners=PLAINTEXT://:9093
    log.dirs=/home/xiaosi/logs/kafka/kafka-logs-1
config/server-2.properties:
    broker.id=2
    listeners=PLAINTEXT://:9094
    log.dirs=/home/xiaosi/logs/kafka/kafka-logs-2
```
broker.id在集群中唯一的标注一个节点，因为在同一个机器上，所以必须制定不同的端口和日志文件，避免数据被覆盖。（We have to override the port and log directory only because we are running these all on the same machine and we want to keep the brokers from all trying to register on the same port or overwrite each others data）

#### 6.2 启动Broker

之前已经启动了zookeeper和一个broker，现在我们只需要启动另外两个broker：
```
sudo ./bin/kafka-server-start.sh config/server1.properties &
sudo ./bin/kafka-server-start.sh config/server2.properties &
```
看一下server2的输出结果：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-server-start.sh config/server2.properties
[sudo] xiaosi 的密码： 
[2016-08-02 12:30:45,660] INFO KafkaConfig values: 
	request.timeout.ms = 30000
	log.roll.hours = 168
	inter.broker.protocol.version = 0.10.0-IV1
	log.preallocate = false
	security.inter.broker.protocol = PLAINTEXT
	controller.socket.timeout.ms = 30000
	broker.id.generation.enable = true
	ssl.keymanager.algorithm = SunX509
	ssl.key.password = null
	log.cleaner.enable = true
	ssl.provider = null
	num.recovery.threads.per.data.dir = 1
	background.threads = 10
	unclean.leader.election.enable = true
	sasl.kerberos.kinit.cmd = /usr/bin/kinit
	replica.lag.time.max.ms = 10000
	ssl.endpoint.identification.algorithm = null
	sasl.mechanism.inter.broker.protocol = GSSAPI
	auto.create.topics.enable = true
	log.message.timestamp.difference.max.ms = 9223372036854775807
	zookeeper.sync.time.ms = 2000
	ssl.client.auth = none
	ssl.keystore.password = null
	offsets.topic.compression.codec = 0
	log.cleaner.io.buffer.load.factor = 0.9
	log.retention.hours = 168
	log.dirs = /home/xiaosi/logs/kafka/kafka-logs-2
	ssl.protocol = TLS
	log.index.size.max.bytes = 10485760
	sasl.kerberos.min.time.before.relogin = 60000
	broker.rack = null
	log.retention.minutes = null
	connections.max.idle.ms = 600000
	ssl.trustmanager.algorithm = PKIX
	offsets.retention.minutes = 1440
	max.connections.per.ip = 2147483647
	replica.fetch.wait.max.ms = 500
	log.message.timestamp.type = CreateTime
	metrics.num.samples = 2
	port = 9092
	offsets.retention.check.interval.ms = 600000
	log.cleaner.dedupe.buffer.size = 134217728
	log.segment.bytes = 1073741824
	group.min.session.timeout.ms = 6000
	producer.purgatory.purge.interval.requests = 1000
	min.insync.replicas = 1
	ssl.truststore.password = null
	socket.receive.buffer.bytes = 102400
	log.flush.scheduler.interval.ms = 9223372036854775807
	num.io.threads = 8
	leader.imbalance.per.broker.percentage = 10
	zookeeper.connect = localhost:2181
	queued.max.requests = 500
	offsets.topic.replication.factor = 3
	replica.socket.timeout.ms = 30000
	offsets.topic.segment.bytes = 104857600
	replica.high.watermark.checkpoint.interval.ms = 5000
	broker.id = 2
	ssl.keystore.location = null
	listeners = PLAINTEXT://:9094
	log.flush.interval.messages = 9223372036854775807
	principal.builder.class = class org.apache.kafka.common.security.auth.DefaultPrincipalBuilder
	log.retention.ms = null
	offsets.commit.required.acks = -1
	sasl.kerberos.principal.to.local.rules = [DEFAULT]
	group.max.session.timeout.ms = 300000
	num.replica.fetchers = 1
	advertised.listeners = null
	replica.socket.receive.buffer.bytes = 65536
	delete.topic.enable = false
	log.index.interval.bytes = 4096
	metric.reporters = []
	compression.type = producer
	log.cleanup.policy = delete
	log.message.format.version = 0.10.0-IV1
	controlled.shutdown.max.retries = 3
	log.cleaner.threads = 1
	quota.window.size.seconds = 1
	zookeeper.connection.timeout.ms = 6000
	offsets.load.buffer.size = 5242880
	zookeeper.session.timeout.ms = 6000
	ssl.cipher.suites = null
	authorizer.class.name = 
	sasl.kerberos.ticket.renew.jitter = 0.05
	sasl.enabled.mechanisms = [GSSAPI]
	sasl.kerberos.service.name = null
	controlled.shutdown.enable = true
	offsets.topic.num.partitions = 50
	quota.window.num = 11
	message.max.bytes = 1000012
	log.cleaner.backoff.ms = 15000
	log.roll.jitter.hours = 0
	log.retention.check.interval.ms = 300000
	replica.fetch.max.bytes = 1048576
	log.cleaner.delete.retention.ms = 86400000
	fetch.purgatory.purge.interval.requests = 1000
	log.cleaner.min.cleanable.ratio = 0.5
	offsets.commit.timeout.ms = 5000
	zookeeper.set.acl = false
	log.retention.bytes = -1
	offset.metadata.max.bytes = 4096
	leader.imbalance.check.interval.seconds = 300
	quota.consumer.default = 9223372036854775807
	log.roll.jitter.ms = null
	reserved.broker.max.id = 1000
	replica.fetch.backoff.ms = 1000
	advertised.host.name = null
	quota.producer.default = 9223372036854775807
	log.cleaner.io.buffer.size = 524288
	controlled.shutdown.retry.backoff.ms = 5000
	log.dir = /tmp/kafka-logs
	log.flush.offset.checkpoint.interval.ms = 60000
	log.segment.delete.delay.ms = 60000
	num.partitions = 1
	num.network.threads = 3
	socket.request.max.bytes = 104857600
	sasl.kerberos.ticket.renew.window.factor = 0.8
	log.roll.ms = null
	ssl.enabled.protocols = [TLSv1.2, TLSv1.1, TLSv1]
	socket.send.buffer.bytes = 102400
	log.flush.interval.ms = null
	ssl.truststore.location = null
	log.cleaner.io.max.bytes.per.second = 1.7976931348623157E308
	default.replication.factor = 1
	metrics.sample.window.ms = 30000
	auto.leader.rebalance.enable = true
	host.name = 
	ssl.truststore.type = JKS
	advertised.port = null
	max.connections.per.ip.overrides = 
	replica.fetch.min.bytes = 1
	ssl.keystore.type = JKS
 (kafka.server.KafkaConfig)
[2016-08-02 12:30:45,735] INFO starting (kafka.server.KafkaServer)
[2016-08-02 12:30:45,741] INFO Connecting to zookeeper on localhost:2181 (kafka.server.KafkaServer)
[2016-08-02 12:30:45,755] INFO Starting ZkClient event thread. (org.I0Itec.zkclient.ZkEventThread)
[2016-08-02 12:30:45,760] INFO Client environment:zookeeper.version=3.4.6-1569965, built on 02/20/2014 09:09 GMT (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,760] INFO Client environment:host.name=localhost (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,760] INFO Client environment:java.version=1.7.0_101 (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,760] INFO Client environment:java.vendor=Oracle Corporation (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,760] INFO Client environment:java.home=/usr/lib/jvm/java-7-openjdk-amd64/jre (org.apache.zookeeper.ZooKeeper)
...
[2016-08-02 12:30:45,761] INFO Client environment:java.io.tmpdir=/tmp (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,761] INFO Client environment:java.compiler=<NA> (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,761] INFO Client environment:os.name=Linux (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,761] INFO Client environment:os.arch=amd64 (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,761] INFO Client environment:os.version=4.2.0-35-generic (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,761] INFO Client environment:user.name=root (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,761] INFO Client environment:user.home=/root (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,761] INFO Client environment:user.dir=/opt/kafka_2.11-0.10.0.0 (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,762] INFO Initiating client connection, connectString=localhost:2181 sessionTimeout=6000 watcher=org.I0Itec.zkclient.ZkClient@28c19a75 (org.apache.zookeeper.ZooKeeper)
[2016-08-02 12:30:45,778] INFO Waiting for keeper state SyncConnected (org.I0Itec.zkclient.ZkClient)
[2016-08-02 12:30:45,780] INFO Opening socket connection to server localhost/127.0.0.1:2181. Will not attempt to authenticate using SASL (unknown error) (org.apache.zookeeper.ClientCnxn)
[2016-08-02 12:30:45,784] INFO Socket connection established to localhost/127.0.0.1:2181, initiating session (org.apache.zookeeper.ClientCnxn)
[2016-08-02 12:30:45,795] INFO Session establishment complete on server localhost/127.0.0.1:2181, sessionid = 0x1564983388f0005, negotiated timeout = 6000 (org.apache.zookeeper.ClientCnxn)
[2016-08-02 12:30:45,797] INFO zookeeper state changed (SyncConnected) (org.I0Itec.zkclient.ZkClient)
[2016-08-02 12:30:45,836] INFO Loading logs. (kafka.log.LogManager)
[2016-08-02 12:30:45,885] INFO Completed load of log my-replicated-topic-0 with log end offset 2 (kafka.log.Log)
[2016-08-02 12:30:45,890] INFO Logs loading complete. (kafka.log.LogManager)
[2016-08-02 12:30:45,926] INFO Starting log cleanup with a period of 300000 ms. (kafka.log.LogManager)
[2016-08-02 12:30:45,927] INFO Starting log flusher with a default period of 9223372036854775807 ms. (kafka.log.LogManager)
[2016-08-02 12:30:45,971] INFO Awaiting socket connections on 0.0.0.0:9094. (kafka.network.Acceptor)
[2016-08-02 12:30:45,973] INFO [Socket Server on Broker 2], Started 1 acceptor threads (kafka.network.SocketServer)
[2016-08-02 12:30:45,989] INFO [ExpirationReaper-2], Starting  (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)
[2016-08-02 12:30:45,990] INFO [ExpirationReaper-2], Starting  (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)
[2016-08-02 12:30:46,153] INFO [ExpirationReaper-2], Starting  (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)
[2016-08-02 12:30:46,154] INFO [ExpirationReaper-2], Starting  (kafka.server.DelayedOperationPurgatory$ExpiredOperationReaper)
[2016-08-02 12:30:46,174] INFO [GroupCoordinator 2]: Starting up. (kafka.coordinator.GroupCoordinator)
[2016-08-02 12:30:46,174] INFO [GroupCoordinator 2]: Startup complete. (kafka.coordinator.GroupCoordinator)
[2016-08-02 12:30:46,177] INFO [Group Metadata Manager on Broker 2]: Removed 0 expired offsets in 6 milliseconds. (kafka.coordinator.GroupMetadataManager)
[2016-08-02 12:30:46,190] INFO [ThrottledRequestReaper-Produce], Starting  (kafka.server.ClientQuotaManager$ThrottledRequestReaper)
[2016-08-02 12:30:46,191] INFO [ThrottledRequestReaper-Fetch], Starting  (kafka.server.ClientQuotaManager$ThrottledRequestReaper)
[2016-08-02 12:30:46,196] INFO Will not load MX4J, mx4j-tools.jar is not in the classpath (kafka.utils.Mx4jLoader$)
[2016-08-02 12:30:46,217] INFO Creating /brokers/ids/2 (is it secure? false) (kafka.utils.ZKCheckedEphemeral)
[2016-08-02 12:30:46,233] INFO Result of znode creation is: OK (kafka.utils.ZKCheckedEphemeral)
[2016-08-02 12:30:46,234] INFO Registered broker 2 at path /brokers/ids/2 with addresses: PLAINTEXT -> EndPoint(localhost,9094,PLAINTEXT) (kafka.utils.ZkUtils)
[2016-08-02 12:30:46,247] INFO Kafka version : 0.10.0.0 (org.apache.kafka.common.utils.AppInfoParser)
[2016-08-02 12:30:46,247] INFO Kafka commitId : b8642491e78c5a13 (org.apache.kafka.common.utils.AppInfoParser)
[2016-08-02 12:30:46,248] INFO [Kafka Server 2], started (kafka.server.KafkaServer)
```
#### 6.3 创建Topic

创建一个拥有三个副本的Topic：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 3 --partitions 1 --topic my-replicated-topic
[sudo] xiaosi 的密码： 
Created topic "my-replicated-topic".
```
#### 6.4 查看broker状态

我们已经搭建起了一个含有三个broker的集群，但是如何在集群中查看一个具体的broker在具体做什么呢？运行下面命令即可：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-topics.sh --describe --zookeeper localhost:2181 --topic my-replicated-topic
Topic:my-replicated-topic	PartitionCount:1	ReplicationFactor:3	Configs:
	Topic: my-replicated-topic	Partition: 0	Leader: 1	Replicas: 1,2,0	Isr: 1,2,0
```
第一行是对所有分区的一个描述，然后每个分区都会对应一行（The first line gives a summary of all the partitions, each additional line gives information about one partition），因为我们只有一个分区所以下面就只加了一行。

leader：负责处理消息的读和写，leader是从所有节点中随机选择的（Each node will be the leader for a randomly selected portion of the partitions）

replicas：列出了所有的副本节点，不管节点是否在服务中（ list of nodes that replicate the log for this partition regardless of whether they are the leader or even if they are currently alive）

isr：是正在服务中的节点（This is the subset of the replicas list that is currently alive and caught-up to the leader）



从我们的例子中可以看出，节点1是作为leader运行。

我们还可以看一下我们之前创建的那个主题：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-topics.sh --describe --zookeeper localhost:2181 --topic test-topic
Topic:test-topic	PartitionCount:1	ReplicationFactor:1	Configs:
	Topic: test-topic	Partition: 0	Leader: 0	Replicas: 0	Isr: 0
```
不出意外，这个Topic没有副本（副本因子为1，表示只有它自己）

#### 6.5 发送消息到新Topic

发送消息：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-console-producer.sh --broker-list localhost:9092 --topic my-replicated-topic
hello kafka
hello ...
^C 
```
消费消息：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-console-consumer.sh --zookeeper localhost:2181 --from-beginning --topic my-replicated-topic
hello kafka
hello ...
```

#### 6.6 测试容错能力

杀掉server2之后，再看broker的状态：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-topics.sh --describe --zookeeper localhost:2181 --topic my-replicated-topic
Topic:my-replicated-topic	PartitionCount:1	ReplicationFactor:3	Configs:
	Topic: my-replicated-topic	Partition: 0	Leader: 0	Replicas: 2,0,1	Isr: 0,1
```	
我们可以看到server2已经被杀掉，server0取代server2成为新的leader。虽然最初负责续写消息的leader down掉了，但之前的消息还是可以消费的：
```
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-console-producer.sh --broker-list localhost:9092 --topic my-replicated-topic
[sudo] xiaosi 的密码： 
hello
^Cxiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ 
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ 
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ 
xiaosi@Qunar:/opt/kafka_2.11-0.10.0.0$ sudo ./bin/kafka-console-consumer.sh --zookeeper localhost:2181 --from-beginning --topic my-replicated-topic
hello kafka
hello ...
hello
```