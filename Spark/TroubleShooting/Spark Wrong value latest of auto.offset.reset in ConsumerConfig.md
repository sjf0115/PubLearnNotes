
```java
// Kafka 配置参数
Map<String, String> kafkaParams = new HashMap<>();
kafkaParams.put("bootstrap.servers", "localhost:9092");
kafkaParams.put("group.id", "word");
kafkaParams.put("auto.offset.reset", "latest");
```

```java
Exception in thread "main" kafka.common.InvalidConfigException: Wrong value latest of auto.offset.reset in ConsumerConfig; Valid values are smallest and largest
	at kafka.consumer.ConsumerConfig$.validateAutoOffsetReset(ConsumerConfig.scala:75)
	at kafka.consumer.ConsumerConfig$.validate(ConsumerConfig.scala:59)
	at kafka.consumer.ConsumerConfig.<init>(ConsumerConfig.scala:184)
	at kafka.consumer.ConsumerConfig.<init>(ConsumerConfig.scala:94)
	at org.apache.spark.streaming.kafka.KafkaCluster$SimpleConsumerConfig.<init>(KafkaCluster.scala:398)
	at org.apache.spark.streaming.kafka.KafkaCluster$SimpleConsumerConfig$.apply(KafkaCluster.scala:434)
	at org.apache.spark.streaming.kafka.KafkaCluster.config(KafkaCluster.scala:53)
	at org.apache.spark.streaming.kafka.KafkaCluster.getPartitionMetadata(KafkaCluster.scala:130)
	at org.apache.spark.streaming.kafka.KafkaCluster.getPartitions(KafkaCluster.scala:119)
	at org.apache.spark.streaming.kafka.KafkaUtils$.getFromOffsets(KafkaUtils.scala:211)
	at org.apache.spark.streaming.kafka.KafkaUtils$.createDirectStream(KafkaUtils.scala:484)
	at org.apache.spark.streaming.kafka.KafkaUtils$.createDirectStream(KafkaUtils.scala:607)
	at org.apache.spark.streaming.kafka.KafkaUtils.createDirectStream(KafkaUtils.scala)
	at com.spark.example.streaming.conncetor.kafka.KafkaDirectExample.main(KafkaDirectExample.java:40)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at org.apache.spark.deploy.SparkSubmit$.org$apache$spark$deploy$SparkSubmit$$runMain(SparkSubmit.scala:755)
	at org.apache.spark.deploy.SparkSubmit$.doRunMain$1(SparkSubmit.scala:180)
	at org.apache.spark.deploy.SparkSubmit$.submit(SparkSubmit.scala:205)
	at org.apache.spark.deploy.SparkSubmit$.main(SparkSubmit.scala:119)
	at org.apache.spark.deploy.SparkSubmit.main(SparkSubmit.scala)
```


```java
// Kafka 配置参数
Map<String, String> kafkaParams = new HashMap<>();
kafkaParams.put("bootstrap.servers", "localhost:9092");
kafkaParams.put("group.id", "word");
kafkaParams.put("auto.offset.reset", "latest");
```
