### 1. 简介

Apache Kafka是分布式`发布-订阅`消息系统。它最初由LinkedIn公司开发，之后成为Apache项目的一部分。Kafka是一种快速、可扩展的、设计内在就是分布式的，分区的和可复制的提交日志服务。

Apache Kafka与传统消息系统相比，有以下不同：
- 它被设计为一个分布式系统，易于向外扩展；
- 它同时为发布和订阅提供高吞吐量；
- 它支持多订阅者，当失败时能自动平衡消费者；
- 它将消息持久化到磁盘，因此可用于批量消费，例如ETL，以及实时应用程序。

本文我将重点介绍Apache Kafka的架构、特性和特点，帮助我们理解Kafka为何比传统消息服务更好。

我将比较Kafak和传统消息服务RabbitMQ、Apache ActiveMQ的特点，讨论一些Kafka优于传统消息服务的场景。在最后一节，我们将探讨一个进行中的示例应用，展示Kafka作为消息服务器的用途。这个示例应用的完整源代码在GitHub。关于它的详细讨论在本文的最后一节。

### 2. 架构

首先，我介绍一下Kafka的基本概念。它的架构包括以下组件：

- 话题（Topic）是特定类型的消息流。消息是字节的有效负载（Payload），话题是消息的分类名或种子（Feed）名。
- 生产者（Producer）是能够发布消息到Topic的任何对象。
- 已发布的消息保存在一组服务器中，它们被称为代理（Broker）或Kafka集群。
- 消费者(Consumer)可以订阅一个或多个Topic，并从Broker中拉数据，从而消费这些已发布的消息。

![img](http://img.blog.csdn.net/20170805235401901)

生产者可以选择自己喜欢的序列化方法对消息内容编码。为了提高效率，生产者可以在一个发布请求中发送一组消息。下面的代码演示了如何创建生产者并发送消息。

生产者示例代码：
```java
producer = new Producer(…);
message = new Message(“test message str”.getBytes());
set = new MessageSet(message);
producer.send(“topic1”, set);
```
为了订阅话题，消费者首先为话题创建一个或多个消息流。发布到该话题的消息将被均衡地分发到这些流。每个消息流为不断产生的消息提供了迭代接口。然后消费者迭代流中的每一条消息，处理消息的有效负载。与传统迭代器不同，消息流迭代器永不停止。如果当前没有消息，迭代器将阻塞，直到有新的消息发布到该话题。Kafka同时支持`点到点分发模型`（Point-to-point delivery model），即`多个消费者共同消费队列中某个消息的单个副本`，以及`发布-订阅模型`（Publish-subscribe model），即`多个消费者接收自己的消息副本`。下面的代码演示了消费者如何使用消息。

消费者示例代码：
```java
streams[] = Consumer.createMessageStreams(“topic1”, 1)
for (message : streams[0]) {
bytes = message.payload();
// do something with the bytes
}
```
Kafka的整体架构如下图所示。因为Kafka内在就是分布式的，一个Kafka集群通常包括多个Broker。为了均衡负载，将Topic分成多个分区，每个Broker存储一或多个分区。多个生产者和消费者能够同时生产和获取消息。

  ![img](http://img.blog.csdn.net/20170806000230635?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)


### 3. Kafka存储

Kafka的存储布局非常简单。Topic的每个分区对应一个逻辑日志。物理上，一个日志为相同大小的一组分段文件。每次生产者发布消息到一个分区，Broker就将消息追加到最后一个段文件中。当发布的消息数量达到设定值或者经过一定的时间后，段文件真正写入磁盘中。写入完成后，消息公开给消费者。

与传统的消息系统不同，Kafka系统中存储的消息没有明确的消息Id。

消息通过日志中的`逻辑偏移量`来公开。这样就避免了维护配套密集寻址，用于映射消息ID到实际消息地址的随机存取索引结构的开销。消息ID是增量的，但不连续。要计算下一消息的ID，可以在其逻辑偏移的基础上加上当前消息的长度。

消费者始终从特定分区顺序地获取消息，如果消费者知道特定消息的偏移量，也就说明消费者已经消费了之前的所有消息。消费者向Broker发出异步拉请求，准备字节缓冲区用于消费。每个异步拉请求都包含要消费的消息偏移量。Kafka利用sendfile API高效地从代理的日志段文件中分发字节给消费者。

![img](http://img.blog.csdn.net/20170806000718291)

### 4. Kafka代理

与其它消息系统不同，Kafka代理是无状态的。这意味着消费者必须维护已消费的状态信息。这些信息由消费者自己维护，代理完全不管。这种设计非常微妙，它本身包含了创新。

- 从代理删除消息变得很棘手，因为代理并不知道消费者是否已经使用了该消息。Kafka创新性地解决了这个问题，它将一个简单的基于时间的SLA应用于保留策略。当消息在代理中超过一定时间后，将会被自动删除。
- 这种创新设计有很大的好处，消费者可以故意倒回到老的偏移量再次消费数据。这违反了队列的常见约定，但被证明是许多消费者的基本特征。

### 5. ZooKeeper与Kafka

考虑一下有多个服务器的分布式系统，每台服务器都负责保存数据，在数据上执行操作。这样的潜在例子包括分布式搜索引擎、分布式构建系统或者已知的系统如Apache Hadoop。所有这些分布式系统的一个常见问题是，你如何在任一时间点确定哪些服务器活着并且在工作中。最重要的是，当面对这些分布式计算的难题，例如网络失败、带宽限制、可变延迟连接、安全问题以及任何网络环境，甚至跨多个数据中心时可能发生的错误时，你如何可靠地做这些事。这些正是Apache ZooKeeper所关注的问题，它是一个快速、高可用、容错、分布式的协调服务。你可以使用ZooKeeper构建可靠的、分布式的数据结构，用于群组成员、领导人选举、协同工作流和配置服务，以及广义的分布式数据结构如锁、队列、屏障（Barrier）和锁存器（Latch）。许多知名且成功的项目依赖于ZooKeeper，其中包括HBase、Hadoop 2.0、Solr Cloud、Neo4J、Apache Blur（Incubating）和Accumulo。

ZooKeeper是一个分布式的、分层级的文件系统，能促进客户端间的松耦合，并提供最终一致的，类似于传统文件系统中文件和目录的Znode视图。它提供了基本的操作，例如创建、删除和检查Znode是否存在。它提供了事件驱动模型，客户端能观察特定Znode的变化，例如现有Znode增加了一个新的子节点。ZooKeeper运行多个ZooKeeper服务器，称为Ensemble，以获得高可用性。每个服务器都持有分布式文件系统的内存复本，为客户端的读取请求提供服务。

![img](http://img.blog.csdn.net/20170806000938430)

上图4展示了典型的ZooKeeper ensemble，一台服务器作为Leader，其它作为Follower。当Ensemble启动时，先选出Leader，然后所有Follower复制Leader的状态。所有写请求都通过Leader路由，变更会广播给所有Follower。变更广播被称为原子广播。

Kafka中ZooKeeper的用途：正如ZooKeeper用于分布式系统的协调和促进，Kafka使用ZooKeeper也是基于相同的原因。ZooKeeper用于管理、协调Kafka代理。每个Kafka代理都通过ZooKeeper协调其它Kafka代理。当Kafka系统中新增了代理或者某个代理故障失效时，ZooKeeper服务将通知生产者和消费者。生产者和消费者据此开始与其它代理协调工作。Kafka整体系统架构如图5所示。

![img](http://img.blog.csdn.net/20170806001019419)

### 6. Apache Kafka对比其它消息服务

让我们了解一下使用Apache Kafka的两个项目，以对比其它消息服务。这两个项目分别是LinkedIn和我的项目：

#### 6.1 LinkedIn的研究

LinkedIn团队做了个实验研究，对比Kafka与Apache ActiveMQ V5.4和RabbitMQ V2.4的性能。他们使用ActiveMQ默认的消息持久化库Kahadb。LinkedIn在两台Linux机器上运行他们的实验，每台机器的配置为8核2GHz、16GB内存，6个磁盘使用RAID10。两台机器通过1GB网络连接。一台机器作为代理，另一台作为生产者或者消费者。

#### 6.2 生产者测试

LinkedIn团队在所有系统中配置代理，异步将消息刷入其持久化库。对每个系统，运行一个生产者，总共发布1000万条消息，每条消息200字节。Kafka生产者以1和50批量方式发送消息。ActiveMQ和RabbitMQ似乎没有简单的办法来批量发送消息，LinkedIn假定它的批量值为1。结果如下面的图6所示：

![img](http://img.blog.csdn.net/20170806001131042)

Kafka性能要好很多的主要原因包括：

- Kafka不等待代理的确认，以代理能处理的最快速度发送消息。
- Kafka有更高效的存储格式。平均而言，Kafka每条消息有9字节的开销，而ActiveMQ有144字节。其原因是JMS所需的沉重消息头，以及维护各种索引结构的开销。LinkedIn注意到ActiveMQ一个最忙的线程大部分时间都在存取B-Tree以维护消息元数据和状态。

#### 6,3 消费者测试

为了做消费者测试，LinkedIn使用一个消费者获取总共1000万条消息。LinkedIn让所有系统每次拉请求都预获取大约相同数量的数据，最多1000条消息或者200KB。对ActiveMQ和RabbitMQ，LinkedIn设置消费者确认模型为自动。结果如图7所示。

![img](http://img.blog.csdn.net/20170806001242193)

Kafka性能要好很多的主要原因包括：

- Kafka有更高效的存储格式；在Kafka中，从代理传输到消费者的字节更少。
- ActiveMQ和RabbitMQ两个容器中的代理必须维护每个消息的传输状态。LinkedIn团队注意到其中一个ActiveMQ线程在测试过程中，一直在将KahaDB页写入磁盘。与此相反，Kafka代理没有磁盘写入动作。最后，Kafka通过使用sendfile API降低了传输开销。
目前，我正在工作的一个项目提供实时服务，从消息中快速并准确地提取场外交易市场（OTC）定价内容。这是一个非常重要的项目，处理近25种资产类别的财务信息，包括债券、贷款和ABS（资产担保证券）。项目的原始信息来源涵盖了欧洲、北美、加拿大和拉丁美洲的主要金融市场领域。下面是这个项目的一些统计，说明了解决方案中包括高效的分布式消息服务是多么重要：

- 每天处理的消息数量超过1,300,000；
- 每天解析的OTC价格数量超过12,000,000；
- 支持超过25种资产类别；
- 每天解析的独立票据超过70,000。

消息包含PDF、Word文档、Excel及其它格式。OTC定价也可能要从附件中提取。

由于传统消息服务器的性能限制，当处理大附件时，消息队列变得非常大，我们的项目面临严重的问题，JMSqueue一天需要启动2-3次。重启JMS队列可能丢失队列中的全部消息。项目需要一个框架，不论解析器（消费者）的行为如何，都能够保住消息。Kafka的特性非常适用于我们项目的需求。

当前项目具备的特性：

- 使用Fetchmail获取远程邮件消息，然后由Procmail过滤并处理，例如单独分发基于附件的消息。
- 每条消息从单独的文件获取，该文件被处理（读取和删除）为一条消息插入到消息服务器中。
- 消息内容从消息服务队列中获取，用于解析和提取信息。

### 7. 示例应用

这个示例应用是基于我在项目中使用的原始应用修改后的版本。我已经删除日志的使用和多线程特性，使示例应用的构件尽量简单。示例应用的目的是展示如何使用Kafka生产者和消费者的API。应用包括一个生产者示例（简单的生产者代码，演示Kafka生产者API用法并发布特定话题的消息），消费者示例（简单的消费者代码，用于演示Kafka消费者API的用法）以及消息内容生成API（在特定路径下生成消息内容到文件的API）。下图展示了各组件以及它们与系统中其它组件间的关系。

![img](http://img.blog.csdn.net/20170806001428338)

示例应用的结构与Kafka源代码中的例子程序相似。应用的源代码包含Java源程序文件夹‘src’和'config'文件夹，后者包括几个配置文件和一些Shell脚本，用于执行示例应用。要运行示例应用，请参照ReadMe.md文件或GitHub网站Wiki页面的说明。

程序构建可以使用Apache Maven，定制也很容易。如果有人想修改或定制示例应用的代码，有几个Kafka构建脚本已经过修改，可用于重新构建示例应用代码。关于如何定制示例应用的详细描述已经放在项目GitHub的Wiki页面。

现在，让我们看看示例应用的核心构件。

Kafka生产者代码示例:
```java
/**
 * Instantiates a new Kafka producer.
 *
 * @param topic the topic
 * @param directoryPath the directory path
 */
public KafkaMailProducer(String topic, String directoryPath) {
       props.put("serializer.class", "kafka.serializer.StringEncoder");
       props.put("metadata.broker.list", "localhost:9092");
       producer = new kafka.javaapi.producer.Producer<Integer, String>(new ProducerConfig(props));
       this.topic = topic;
       this.directoryPath = directoryPath;
}

public void run() {
      Path dir = Paths.get(directoryPath);
      try {
           new WatchDir(dir).start();
           new ReadDir(dir).start();
      } catch (IOException e) {
           e.printStackTrace();
      }
}
```
上面的代码片断展示了Kafka生产者API的基本用法，例如设置生产者的属性，包括发布哪个话题的消息，可以使用哪个序列化类以及代理的相关信息。这个类的基本功能是从邮件目录读取邮件消息文件，然后作为消息发布到Kafka代理。目录通过java.nio.WatchService类监视，一旦新的邮件消息Dump到该目录，就会被立即读取并作为消息发布到Kafka代理。

Kafka消费者代码示例:
```java
public KafkaMailConsumer(String topic) {
       consumer =
Kafka.consumer.Consumer.createJavaConsumerConnector(createConsumerConfig());
       this.topic = topic;
}

/**
 * Creates the consumer config.
 *
 * @return the consumer config
 */
private static ConsumerConfig createConsumerConfig() {
      Properties props = new Properties();
      props.put("zookeeper.connect", KafkaMailProperties.zkConnect);
      props.put("group.id", KafkaMailProperties.groupId);
      props.put("zookeeper.session.timeout.ms", "400");
      props.put("zookeeper.sync.time.ms", "200");
      props.put("auto.commit.interval.ms", "1000");
      return new ConsumerConfig(props);
}

public void run() {
      Map<String, Integer> topicCountMap = new HashMap<String, Integer>();
      topicCountMap.put(topic, new Integer(1));
      Map<String, List<KafkaStream<byte[], byte[]>>> consumerMap = consumer.createMessageStreams(topicCountMap);
      KafkaStream<byte[], byte[]> stream = consumerMap.get(topic).get(0);
      ConsumerIterator<byte[], byte[]> it = stream.iterator();
      while (it.hasNext())
      System.out.println(new String(it.next().message()));
}
```
上面的代码演示了基本的消费者API。正如我们前面提到的，消费者需要设置消费的消息流。在Run方法中，我们进行了设置，并在控制台打印收到的消息。在我的项目中，我们将其输入到解析系统以提取OTC定价。

在当前的质量保证系统中，我们使用Kafka作为消息服务器用于概念验证（Proof of Concept，POC）项目，它的整体性能优于JMS消息服务。其中一个我们感到非常兴奋的特性是消息的再消费（re-consumption），这让我们的解析系统可以按照业务需求重新解析某些消息。基于Kafka这些很好的效果，我们正计划使用它，而不是用Nagios系统，去做日志聚合与分析。

### 8. 总结

Kafka是一种处理大量数据的新型系统。Kafka基于拉的消费模型让消费者以自己的速度处理消息。如果处理消息时出现了异常，消费者始终可以选择再消费该消息。
