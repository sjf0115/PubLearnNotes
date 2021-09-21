---
layout: post
author: smartsi
title: Kafka Connect 如何构建实时数据管道
date: 2021-09-21 15:58:00
tags:
  - Kafka

categories: Kafka
permalink: how-to-build-a-pipeline-with-kafka-connect
---

[Kafka Connect](http://smartsi.club/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines.html) 旨在通过将数据移入和移出 Kafka 进行标准化，以更轻松地构建大规模的实时数据管道。我们可以使用 Kafka Connector 读取或写入外部系统、管理数据流以及扩展系统，所有这些都无需开发新代码。Kafka Connect 管理与其他系统连接时的所有常见问题（Schema 管理、容错、并行性、延迟、投递语义等），每个 Connector 只关注如何在目标系统和 Kafka 之间复制数据。

> 如果有对 Kafka Connect 不了解的，可以参考[Kafka Connect 构建大规模低延迟的数据管道](http://smartsi.club/announcing-kafka-connect-building-large-scale-low-latency-data-pipelines.html)

### 1. 执行模式

Kafka Connect 是与 Apache Kafka 一起发布的，所以没有必要单独安装，对于生产使用，特别是计划使用 Connect 移动大量数据或运行多个 Connector 时，应该在单独的服务器上运行 Connect。在这种情况下，所有的机器上安装 Apache Kafka，并在部分服务器上启动 broker，然后在其他服务器上启动 Connect。Kafka Connect 目前支持两种执行模式：Standalone 模式和分布式模式。

#### 1.1 Standalone 模式

在 Standalone 模式下，所有的工作都在单个进程中完成。这种模式更容易配置以及入门，但不能充分利用 Kafka Connect 的某些重要功能，例如，容错。我们可以使用如下命令启动 Standalone 进程：
```
bin/connect-standalone.sh config/connect-standalone.properties connector1.properties [connector2.properties ...]
```
第一个参数 config/connect-standalone.properties 是 worker 的配置。这其中包括 Kafka 连接参数、序列化格式以及提交 Offset 的频率等配置：
```xml
bootstrap.servers=localhost:9092
key.converter.schemas.enable=true
value.converter.schemas.enable=true
offset.storage.file.filename=/tmp/connect.offsets
offset.flush.interval.ms=10000
```
上述提供的默认配置适用于使用 config/server.properties 提供的默认配置运行的本地集群。如果使用不同配置或者在生产部署，那就需要对默认配置做调整。但无论怎样，所有 Worker（独立的和分布式的）都需要一些配置：
- bootstrap.servers：该参数列出了将要与 Connect 协同工作的 broker 服务器，Connector 将会向这些 broker 写入数据或者从它们那里读取数据。你不需要指定集群的所有 broker，但是建议至少指定3个。
- key.converter 和 value.converter：分别指定了消息键和消息值所使用的的转换器，用于在 Kafka Connect 格式和写入 Kafka 的序列化格式之间进行转换。这控制了写入 Kafka 或从 Kafka 读取的消息中键和值的格式。由于这与 Connector 没有任何关系，因此任何 Connector 可以与任何序列化格式一起使用。默认使用 Kafka 提供的 JSONConverter。有些转换器还包含了特定的配置参数。例如，通过将 key.converter.schemas.enable 设置成 true 或者 false 来指定 JSON 消息是否包含 schema。
- offset.storage.file.filename：用于存储 Offset 数据的文件。

这些配置参数可以让 Kafka Connect 的生产者和消费者访问配置、Offset 和状态 Topic。配置 Kafka Source 任务使用的生产者和 Kafka Sink 任务使用的消费者，可以使用相同的参数，但需要分别加上 'producer.' 和 'consumer.' 前缀。bootstrap.servers 是唯一不需要添加前缀的 Kafka 客户端参数。

#### 1.2 分布式模式

分布式模式可以自动平衡工作负载，并可以动态扩展（或缩减）以及提供容错。分布式模式的执行与 Standalone 模式非常相似：
```
bin/connect-distributed.sh config/connect-distributed.properties
```
不同之处在于启动的脚本以及配置参数。在分布式模式下，使用 connect-distributed.sh 来代替 connect-standalone.sh。第一个 worker 配置参数使用的是 config/connect-distributed.properties 配置文件：
```
bootstrap.servers=localhost:9092
group.id=connect-cluster
key.converter.schemas.enable=true
value.converter.schemas.enable=true
offset.storage.topic=connect-offsets
offset.storage.replication.factor=1
#offset.storage.partitions=25
config.storage.topic=connect-configs
config.storage.replication.factor=1
status.storage.topic=connect-status
status.storage.replication.factor=1
#status.storage.partitions=5
offset.flush.interval.ms=10000
```
Kafka Connect 将 Offset、配置以及任务状态存储在 Kafka Topic 中。建议手动创建 Offset、配置和状态的 Topic，以达到所需的分区数和复制因子。如果在启动 Kafka Connect 时尚未创建 Topic，将使用默认分区数和复制因子来自动创建 Topic，这可能不适合我们的应用。在启动集群之前配置如下参数至关重要：
- group.id：Connect 集群的唯一名称，默认为 connect-cluster。具有相同 group id 的 worker 属于同一个 Connect 集群。需要注意的是这不能与消费者组 ID 冲突。
- config.storage.topic：用于存储 Connector 和任务配置的 Topic，默认为 connect-configs。需要注意的是这是一个只有一个分区、高度复制、压缩的 Topic。我们可能需要手动创建 Topic 以确保配置的正确，因为自动创建的 Topic 可能有多个分区或自动配置为删除而不是压缩。
- offset.storage.topic：用于存储 Offset 的 Topic，默认为 connect-offsets。这个 Topic 可以有多个分区。
- status.storage.topic：用于存储状态的 Topic，默认为 connect-status。这个 Topic 可以有多个分区。

### 2. 配置 Connector

Connector 配置是简单的键值对。对于 Standalone 模式，配置参数在配置文件中定义并通过命令行传递给 Connect 进程。但在分布式模式下，需要使用 REST API 来提交 Connector 配置，来请求创建或者修改 Connector。如下是文件 Source Connector 的示例：
```
name=local-file-source
connector.class=FileStreamSource
tasks.max=1
file=test.txt
```
大多数配置都依赖于具体的 Connector，因此无法在此处进行概述。但是，有一些常见的配置参数：
- name：Connector 的唯一名称。使用相同名称注册会失败。
- connector.class：Connector 对应的的 Java 类。
- tasks.max：应为此 Connector 创建的最大任务数。如果 Connector 无法达到这种并行度级别，可能会创建比配置要少的任务。

connector.class 配置支持多种格式：Connector 类的全名或别名。对于文件 Source Connector，我们可以全名 org.apache.kafka.connect.file.FileStreamSinkConnector，也可以使用简写的 FileStreamSink 或 FileStreamSinkConnector。Sink Connector 还需要一些其他的参数来控制输入。每个 Sink Connector 都必须设置如下参数：
- topic：Connector 的输入 Topic，以逗号分隔的列表
- topic.regex：Connector 输入 Topic 的 Java 正则表达式

### 3. 运行 Connect

启动 Connect 进程与启动 broker 进程差不多，在调用脚本时传入一个配置文件即可，如下使用分布式执行模式来启动 Connect：
```
bin/connect-distributed.sh config/connect-distributed.properties &
```
我们一般通过 Connect 的 REST API 来配置和监控 rest.host.name 和 rest.port。你可以为 REST API 指定特定的端口：
```
rest.port=9083
```
> 默认端口号为 8083，在这里我们为了防止端口号冲突，特意修改为 9083。

启动 Worker 集群之后，可以通过 REST API 来验证它们是否正常运行：
```
localhost:script wy$ curl http://localhost:9083/
{"version":"2.4.0","commit":"77a89fcf8d7fa018","kafka_cluster_id":"jNjfTPnOTHOYxyaafsGU6A"}
```
这个 REST API 会返回当前 Connect 的版本号。我们运行的是 Kafka 2.4.0 版本。我们还可以检查已经安装好的 Connector 插件：
```
localhost:script wy$ curl http://localhost:9083/connector-plugins
[{"class":"org.apache.kafka.connect.file.FileStreamSinkConnector","type":"sink","version":"2.4.0"},{"class":"org.apache.kafka.connect.file.FileStreamSourceConnector","type":"source","version":"2.4.0"},{"class":"org.apache.kafka.connect.mirror.MirrorCheckpointConnector","type":"source","version":"1"},{"class":"org.apache.kafka.connect.mirror.MirrorHeartbeatConnector","type":"source","version":"1"},{"class":"org.apache.kafka.connect.mirror.MirrorSourceConnector","type":"source","version":"1"}]
```

### 4. Connector 示例

在这里，我们使用 Kafka 自带的文件连接器(FileStreamSource、FileStreamSink)来演示如何将一个文件发送到 Kafka Topic 上，再从 Kafka Topic 导出到文件中。

如下所示创建一个文件 Source Connector。在这里，直接让它读取我们创建的 a.txt 文件，即把 a.txt 文件发送到 Topic 上：
```
echo '{"name":"file-source-connector", "config":{"connector.class":"FileStreamSource","file":"a.txt","topic":"file-connector-topic"}}' | curl -X POST -d @- http://localhost:9083/connectors --header "content-Type:application/json"
```
上述命令使用 Kafka Connect REST API 'POST /connectors' 创建一个新的 Connector，请求是一个 JSON 对象，其中包含一个字符串名称字段 name 以及一个带有 Connector 配置参数的对象配置字段 config。我们通过 echo 命令把 JSON 内容发送给 REST API。从 JSON 中我们可以知道：
- Connector 名称： file-source-connector
- Connector 类： FileStreamSource
- 要加载的文件： a.txt
- 把文件加载到 Kaffa 的 topic：file-connector-topic

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/how-to-build-a-pipeline-with-kafka-connect-1.png?raw=true)

a.txt 文件内容如下：
```
1
2
3
4
5
6
7
8
```

创建完 Connector 之后，我们通过如下命令查看目前已经创建的 Connector：
```
curl -X GET http://localhost:9083/connectors
```
![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/how-to-build-a-pipeline-with-kafka-connect-2.png?raw=true)

> 可以通过该命令删除对应的 Connector：curl -X DELETE http://localhost:9083/connectors/<name>

下面通过 Kafka 的控制台消费者来验证指定的文件是否已经加载到 Topic 中：
```
bin/kafka-console-consumer.sh --topic file-connector-topic --from-beginning --bootstrap-server localhost:9092
```
如果一切正常，可以看到如下输出：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/how-to-build-a-pipeline-with-kafka-connect-3.png?raw=true)

以上输出的是 a.txt 文件的内容，这些内容被一行一行的转成 JSON 记录，并被 Connector 发送到 file-connector-topic Topic 上。默认情况下，JSON 转换器会在每一条记录上附带上 schema 信息。payload 列对应了文件里的一行内容。

文件已经发送到 Kafka Topic 上了，现在使用文件 Sink Connector 再把 Topic 里的内容导出到 a-backup.txt 文件中。导出的文件应该与原始文件 a.txt 的内容完全一样，JSON转换器会把每个 JSON 记录转成单行文本：
```
echo '{"name":"file-sink-connector", "config":{"connector.class":"FileStreamSink","file":"a-backup.txt","topics":"file-connector-topic"}}' | curl -X POST -d @- http://localhost:9083/connectors --header "content-Type:application/json"
```
上述命令还是使用 Kafka Connect REST API 'POST /connectors' 创建一个新的 Connector，请求同样是一个 JSON 对象，其中有几个配置参数发生了变化，connector.class 使用 FileStreamSink，而不是 FileStreamSource；file 参数指向目标文件，而不是原始文件；我们使用 topics，而不是 topic 来指定读取的 Topic。如果一切正常，我们会得到一个名为 a-backup.txt 的文件。

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/how-to-build-a-pipeline-with-kafka-connect-4.png?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

参考：
- [KAFKA CONNECT](https://kafka.apache.org/documentation/#connect)
