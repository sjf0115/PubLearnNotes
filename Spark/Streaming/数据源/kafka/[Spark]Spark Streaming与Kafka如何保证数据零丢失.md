---
layout: post
author: 加米谷大数据
title: Spark Streaming与Kafka如何保证数据零丢失
date: 2018-04-01 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-kafka-integration-achieve-zero-data-loss
---

Spark Streaming 是一种构建在 Spark 上的实时计算框架，它扩展了 Spark 处理大规模流式数据的能力。Spark Streaming 的优势在于：
- 能运行在1000+的结点上，并达到秒级延迟。
- 使用基于内存的 Spark 作为执行引擎，具有高效和容错的特性。
- 能集成 Spark 的批处理和交互查询。
- 为实现复杂的算法提供和批处理类似的简单接口。

为此，Spark Streaming受到众多企业的追捧，并将其大量用于生产项目；然而，在使用过程中存在一些辣手的问题。本文将介绍使用Spark Streaming进行实时处理的一个关于保证数据零丢失的经验。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-kafka-integration-achieve-zero-data-loss-1.jpg?raw=true)

在Spark Streaming的生产实践中，要做到数据零丢失，你需要满足以下几个先决条件：
- 输入的数据源是可靠的；
- 数据接收器是可靠的；
- 元数据持久化;
- 启用了WAL特性（Write ahead log）；
- Exactly-Once。

下面将简单地介绍这些先决条件。

### 1. 输入的数据源是可靠的

Spark Streaming实时处理数据零丢失，需要类似Kafka的数据源：
- 支持在一定时间范围内重新消费；
- 支持高可用消费；
- 支持消费确认机制；

具有这些特征的数据源，可以使得消费程序准确控制消费位置，做到完全掌控消费情况的程度，为数据零丢失打下基础。

### 2. 数据接收器是可靠的

Spark Streaming可以对已经接收的数据进行确认。输入的数据首先被接收器（Receivers）所接收，然后存储到Spark内部。数据一旦存储到Spark中，接收器可以对它进行确认。这种机制保证了在接收器突然挂掉的情况下也不会丢失数据：因为数据虽然被接收，但是没有被持久化的情况下是不会发送确认消息的。所以在接收器恢复的时候，数据可以被原端重新发送。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-kafka-integration-achieve-zero-data-loss-2.jpg?raw=true)

### 3. 元数据持久化

可靠的数据源和接收器可以让实时计算程序从接收器挂掉的情况下恢复。但是更棘手的问题是，如果Driver挂掉如何恢复？使用Checkpoint应用程序元数据的方法可以解决这一问题。为此，Driver可以将应用程序的重要元数据（包含：配置信息、计算代码、未处理的batch数据）持久化到可靠的存储中，比如HDFS、S3；然后Driver可以利用这些持久化的数据进行恢复。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-kafka-integration-achieve-zero-data-loss-3.jpg?raw=true)

由于有了元数据的Checkpoint，所以Driver可以利用他们重构应用程序，而且可以计算出Driver挂掉的时候应用程序执行到什么位置。

通过持久化元数据，并能重构应用程序，貌似解决了数据丢失的问题，然而在以下场景任然可能导致数据丢失：

1）两个Exectuor已经从接收器中接收到输入数据，并将它缓存到Exectuor的内存中；

2）接收器通知输入源数据已经接收；

3）Exectuor根据应用程序的代码开始处理已经缓存的数据；

4）这时候Driver突然挂掉了；

5）从设计的角度看，一旦Driver挂掉之后，它维护的Exectuor也将全部被kill；

6）既然所有的Exectuor被kill了，所以缓存到它们内存中的数据也将被丢失。结果，这些已经通知数据源但是还没有处理的缓存数据就丢失了；

7）缓存的时候不可能恢复，因为它们是缓存在Exectuor的内存中，所以数据被丢失了。

这对于很多关键型的应用程序来说还是无法容忍。这时，Spark团队再次引入了WAL解决以上这些问题。

### 4. WAL（Write ahead log）

启用了WAL机制，所以已经接收的数据被接收器写入到容错存储中，比如HDFS或者S3。由于采用了WAl机制，Driver可以从失败的点重新读取数据，即使Exectuor中内存的数据已经丢失了。在这个简单的方法下，Spark Streaming提供了一种即使是Driver挂掉也可以避免数据丢失的机制。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-kafka-integration-achieve-zero-data-loss-4.jpg?raw=true)

虽然WAL可以确保数据不丢失,它并不能对所有的数据源保证exactly-once语义。以下场景任然比较糟糕：

1）接收器接收到输入数据，并把它存储到WAL中；

2）接收器在更新Zookeeper中Kafka的偏移量之前突然挂掉了；

3）Spark Streaming假设输入数据已成功收到（因为它已经写入到WAL中），然而Kafka认为数据被没有被消费，因为相应的偏移量并没有在Zookeeper中更新；

4）过了一会，接收器从失败中恢复；

5）那些被保存到WAL中但未被处理的数据被重新读取；

6）一旦从WAL中读取所有的数据之后，接收器开始从Kafka中消费数据。因为接收器是采用Kafka的High-Level Consumer API实现的，它开始从Zookeeper当前记录的偏移量开始读取数据，但是因为接收器挂掉的时候偏移量并没有更新到Zookeeper中，所有有一些数据被处理了2次。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-kafka-integration-achieve-zero-data-loss-5.jpg?raw=true)

除了上面描述的场景，WAL还有其他两个不可忽略的缺点:

1）WAL减少了接收器的吞吐量，因为接受到的数据必须保存到可靠的分布式文件系统中。

2）对于一些输入源来说，它会重复相同的数据。比如当从Kafka中读取数据，你需要在Kafka的brokers中保存一份数据，而且你还得在Spark Streaming中保存一份。

### 5. Exactly-Once

为了解决由WAL引入的性能损失，并且保证 exactly-once 语义，新版的Spark中引入了名为Kafka direct API。这个想法对于这个特性是非常明智的。Spark driver只需要简单地计算下一个batch需要处理Kafka中偏移量的范围，然后命令Spark Exectuor直接从Kafka相应Topic的分区中消费数据。换句话说，这种方法把Kafka当作成一个文件系统，然后像读文件一样来消费Topic中的数据。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-kafka-integration-achieve-zero-data-loss-6.jpg?raw=true)

在这个简单但强大的设计中:

1）不再需要Kafka接收器，Exectuor直接采用Simple Consumer API从Kafka中消费数据。

2）不再需要WAL机制，我们仍然可以从失败恢复之后从Kafka中重新消费数据；

3）Exactly-Once语义得以保存，我们不再从WAL中读取重复的数据。


原文：　[Spark Streaming And Kafka：可靠实时计算](https://www.toutiao.com/a6513864038332498435/?tt_from=weixin&utm_campaign=client_share&timestamp=1523321861&app=news_article&utm_source=weixin&iid=26380623414&utm_medium=toutiao_android&wxshare_count=1)
