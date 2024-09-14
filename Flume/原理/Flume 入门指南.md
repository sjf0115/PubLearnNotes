## 1. 什么是 Flume

Apache Flume 是一个分布式、可靠和高可用的系统，可以从大量不同的数据源有效地收集、聚合和移动日志数据，从而集中式的存储数据。Flume 被设计成为一个灵活的分布式系统，可以很容易扩展，而且是高度的可定制化。

## 2. 使用场景

Flume 使用最多的场景是日志收集，也可以通过定制 Source 来传输其他不同类型的数据。Flume 最终会将数据落地到实时计算平台（例如Flink、Spark Streaming 和 Storm）、离线计算平台上（例如 Hive 和 Presto），也可仅落地到数据存储系统中（例如 HDFS、OSS、Kafka 和 Elasticsearch），为后续分析数据和清洗数据做准备。


## 3. Flume 架构

Flume 部署的最简单元是 Flume Agent，本质上是一个 JVM 进程。一个 Flume Agent 可以连接一个或者多个其他的 Agent。一个 Agent 也可以从一个或者多个 Agent 接收数据。通过相互连接的多个 Flume Agent，一个流作业被建立。这个 Flume Agent 链条可以用于将数据从一个位置移动到另一个位置，特别是从生产数据的应用程序到 HDFS、HBase 等。

一般的 Flume Agent 从应用程序服务器接收数据，然后将数据写入到 HDFS 或者 HBase(无论是直接或者通过其他 Flume Agent)，通过简单增加更多的 Flume Agent 就能够扩展服务器数量并将大量数据写入到存储系统。

每个 Flume Agent 有三个组件：Source、Channel 和 Sink。Source 负责获取事件到 Flume Agent，而 Sink 负责从 Agent 移走事件并转发它们到拓扑结构中的下一个 Agent 或者 HDFS 等存储系统。Channel 是一个存储 Source 已经接收到的数据的缓冲区，直到 Sink 已经将数据成功写入到下一阶段或者最终的存储系统。

### 2.1 Source

Source 负责接收数据到 Flume Agent。Source 可以处理各种类型、各种格式的的日志数据。

### 2.2 Channel

Channel 是一个存储 Source 已经接收到的数据的缓冲区，直到 Sink 已经将数据成功写入到下一阶段或者最终的存储系统

### 2.3 Sink

Sink 负责从 Agent 移走事件并转发它们到拓扑结构中的下一个 Agent 或者 HDFS 等存储系统
