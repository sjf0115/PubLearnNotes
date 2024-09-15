## 1. 什么是 Flume

Apache Flume 是一个分布式、可靠和高可用的系统，可以从大量不同的数据源有效地收集、聚合和移动日志数据，从而集中式的存储数据。Flume 被设计成为一个灵活的分布式系统，可以很容易扩展，而且是高度的可定制化。

## 2. 使用场景

Flume 使用最多的场景是日志收集，也可以通过定制 Source 来传输其他不同类型的数据。Flume 最终会将数据落地到实时计算平台（例如Flink、Spark Streaming 和 Storm）、离线计算平台上（例如 Hive 和 Presto），也可仅落地到数据存储系统中（例如 HDFS、OSS、Kafka 和 Elasticsearch），为后续分析数据和清洗数据做准备。

## 3. Flume 架构

Flume 部署的最简单元是 Flume Agent，是一个 Flume 的实例，本质上是一个 JVM 进程。Flume Agent 用来控制 Event 数据流从生产者传输到消费者。

![](img-flume-getting-started-guide-1.png)

每个 Flume Agent 有三个组件：Source、Channel 和 Sink。其中，Source 和 Channel 可以是一对多的关系，Channel 和 Sink 也可以是一对多的关系。Source 负责获取事件到 Flume Agent，而 Sink 负责从 Agent 移走事件并转发它们到拓扑结构中的下一个 Agent 或者 HDFS 等存储系统。Channel 是一个存储 Source 已经接收到的数据的缓冲区，直到 Sink 已经将数据成功写入到下一阶段或者最终的存储系统。

### 3.1 Event

事件 Event 是数据流通过 Flume Agent 的最小单位。一条条日志又或者一个个的二进制文件被 Flume 采集之后它就叫 Event。Event 由一个可选的 Header 字典和一个装载数据的字节数组组成。示例如下：

| Header (Map)     | Body (byte[])     |
| :------------- | :------------- |
| Item One       | Item Two       |

### 3.2 Source

Source 是数据源收集器，负责从外部数据源收集数据，并批量发送到一个或多个 Channel 中。Source 可以处理各种类型、各种格式的的日志数据。

常见 Source 如下所示：

| Source     | 说明  |
| :------------- | :------------- |
| NetCat TCP Source | 监听指定TCP端口获取数据 |
| Taildir Source | 监控目录下的多个文件，记录偏移量，并且不会丢失数据，较为常用 |
| Avro Source | 通过监听Avro端口获取Avro Client发送的事件。Avro是Hadoop提供的一种协议，用于数据序列化。 |
| Exec Source | 通过监听命令行输出获取数据，例如 tail -f /var/log/messages。 |


### 3.3 Channel

Channel 是 Source 和 Sink 之间的缓冲队列。用来存储 Source 已经接收到，但是尚未写出到另一个 Agent 或者存储系统的数据。Channel 的行为像队列，Source 写入到它们，Sink 从它们中读取。

常见 Channel 如下所示：

| Channel     | 说明  |
| :------------- | :------------- |
| Memory Channel | 缓存到内存中，性能高，较为常用。|
| File Channel | 缓存到文件中，会记录Checkpoint和DATA文件，可靠性高，但性能较差。|
| JDBC Channel | 缓存到关系型数据库中。|
| Kafka Channel | 通过Kafka来缓存数据。|

Event 数据会缓存在 Channel 中用来在失败的时候恢复出来。Flume 支持保存在本地文件系统中的 `File Channel`，也支持保存在内存中的 `Memory Channel`，`Memory Channel` 显然速度会更快，缺点是万一 Agent 挂掉 `Memory Channel` 中缓存的数据也就丢失了。

### 3.4 Sink

Sink 负责从 Channel 移走事件 Event 并将以事务的形式 Commit 到拓扑结构中的下一个 Agent 或者 HDFS 等外部存储系统中。一旦事务 Commit 成功，Event 会从 Channel 中移除。

常见 Sink 如下所示：

| Sink     | 说明  |
| :------------- | :------------- |
| Logger Sink | 用于测试。|
| Avro Sink | 转换成Avro Event，主要用于连接多个Flume Agent。|
| HDFS Sink | 写入HDFS，较为常用。|
| Hive Sink | 写入Hive表或分区，使用Hive事务写Events。|
| Kafka Sink | 写入Kafka。|

## 4. 数据流

一个 Flume Agent 可以连接一个或者多个其他的 Agent。一个 Agent 也可以从一个或者多个 Agent 接收数据。通过相互连接的多个 Flume Agent，一个数据流被建立。

![](img-flume-getting-started-guide-2.png)

> 官方这个图的 Agent 4 的 Sink 画错了，不应该是 Avro Sink ，应该是 HDFS Sink。

这个 Flume Agent 链条可以用于将数据从一个位置移动到另一个位置，特别是从生产数据的应用程序到 HDFS、HBase 等。一般的 Flume Agent 从应用程序服务器接收数据，然后将数据写入到 HDFS 或者 HBase(无论是直接或者通过其他 Flume Agent)，通过简单增加更多的 Flume Agent 就能够扩展服务器数量并将大量数据写入到存储系统。
