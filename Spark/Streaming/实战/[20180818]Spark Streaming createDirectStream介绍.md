官网上对这个新接口的介绍很多，大致就是不与zookeeper交互，直接去kafka中读取数据，自己维护offset，于是速度比KafkaUtils.createStream要快上很多。但有利就有弊：无法进行offset的监控。

项目中需要尝试使用这个接口，同时还要进行offset的监控，于是只能按照官网所说的，自己将offset写入zookeeper。

```scala
def createDirectStream[K, V, KD <: Decoder[K], VD <: Decoder[V]](
  jssc: JavaStreamingContext,
  keyClass: Class[K],
  valueClass: Class[V],
  keyDecoderClass: Class[KD],
  valueDecoderClass: Class[VD],
  kafkaParams: JMap[String, String],
  topics: JSet[String]
)
```
这个方法只有3个参数，使用起来最为方便，但是每次启动的时候默认从 `Latest offset` 开始读取，或者设置参数 `auto.offset.reset="smallest"` 后将会从 `Earliest offset` 开始读取。

显然这2种读取位置都不适合生产环境。

```scala
def createDirectStream[
  K: ClassTag,
  V: ClassTag,
  KD <: Decoder[K]: ClassTag,
  VD <: Decoder[V]: ClassTag,
  R: ClassTag] (
    ssc: StreamingContext,
    kafkaParams: Map[String, String],
    fromOffsets: Map[TopicAndPartition, Long],
    messageHandler: MessageAndMetadata[K, V] => R
)
```
这个方法可以在启动的时候可以设置offset，但参数设置起来复杂很多，首先是 `fromOffsets: Map[TopicAndPartition, Long]` 的设置，参考下方代码：
```
val topic2Partitions = ZkUtils.getPartitionsForTopics(zkClient, Config.kafkaConfig.topic)
var fromOffsets: Map[TopicAndPartition, Long] = Map()

topic2Partitions.foreach(topic2Partitions => {
  val topic:String = topic2Partitions._1
  val partitions:Seq[Int] = topic2Partitions._2
  val topicDirs = new ZKGroupTopicDirs(Config.kafkaConfig.kafkaGroupId, topic)

  partitions.foreach(partition => {
    val zkPath = s"${topicDirs.consumerOffsetDir}/$partition"
    ZkUtils.makeSurePersistentPathExists(zkClient, zkPath)
    val untilOffset = zkClient.readData[String](zkPath)

    val tp = TopicAndPartition(topic, partition)
    val offset = try {
      if (untilOffset == null || untilOffset.trim == "")
        getMaxOffset(tp)
      else
        untilOffset.toLong
    } catch {
      case e: Exception => getMaxOffset(tp)
    }
    fromOffsets += (tp -> offset)
    logger.info(s"Offset init: set offset of $topic/$partition as $offset")

  })
})
```
其中getMaxOffset方法是用来获取最大的offset。当第一次启动spark任务或者zookeeper上的数据被删除或设置出错时，将选取最大的offset开始消费。代码如下：
```
private def getMaxOffset(tp:TopicAndPartition):Long = {
  val request = OffsetRequest(immutable.Map(tp -> PartitionOffsetRequestInfo(OffsetRequest.LatestTime, 1)))

  ZkUtils.getLeaderForPartition(zkClient, tp.topic, tp.partition) match {
    case Some(brokerId) => {
      ZkUtils.readDataMaybeNull(zkClient, ZkUtils.BrokerIdsPath + "/" + brokerId)._1 match {
        case Some(brokerInfoString) => {
          Json.parseFull(brokerInfoString) match {
            case Some(m) =>
              val brokerInfo = m.asInstanceOf[Map[String, Any]]
              val host = brokerInfo.get("host").get.asInstanceOf[String]
              val port = brokerInfo.get("port").get.asInstanceOf[Int]
              new SimpleConsumer(host, port, 10000, 100000, "getMaxOffset")
                .getOffsetsBefore(request)
                .partitionErrorAndOffsets(tp)
                .offsets
                .head
            case None =>
              throw new BrokerNotAvailableException("Broker id %d does not exist".format(brokerId))
          }
        }
        case None =>
          throw new BrokerNotAvailableException("Broker id %d does not exist".format(brokerId))
      }
    }
    case None =>
      throw new Exception("No broker for partition %s - %s".format(tp.topic, tp.partition))
  }
}
```
然后是参数messageHandler的设置，为了后续处理中能获取到topic，这里形成(topic, message)的tuple：
```
val messageHandler = (mmd: MessageAndMetadata[String, String]) => (mmd.topic, mmd.message())
```
接着将从获取rdd的offset并写入到zookeeper中：
```
var offsetRanges = Array[OffsetRange]()
messages.transform { rdd =>
  offsetRanges = rdd.asInstanceOf[HasOffsetRanges].offsetRanges
  rdd
}.foreachRDD(rdd => {
  rdd.foreachPartition(HBasePuter.batchSave)
  offsetRanges.foreach(o => {
    val topicDirs = new ZKGroupTopicDirs(Config.kafkaConfig.kafkaGroupId, o.topic)
    val zkPath = s"${topicDirs.consumerOffsetDir}/${o.partition}"
    ZkUtils.updatePersistentPath(zkClient, zkPath, o.untilOffset.toString)
    logger.info(s"Offset update: set offset of ${o.topic}/${o.partition} as ${o.untilOffset.toString}")
  })
})
```
最后附上batchSave的示例：
```
def batchSave(iter:Iterator[(String,String)]):Unit = {
  iter.foreach(item => {
    val topic = item._1
    val message = item._2
    ...
  })
}
```

原文：http://blog.selfup.cn/1665.html
