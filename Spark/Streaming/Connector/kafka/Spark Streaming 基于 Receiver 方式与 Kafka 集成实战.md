


./spark-submit --class com.spark.example.streaming.conncetor.kafka.KafkaReceiverExample --master local[2] --name KafkaReceiverExample /Users/wy/study/code/data-example/spark-example-2.2/target/spark-example-2.2-1.0.jar



在 Kafka 参数中，您必须指定 metadata.broker.list 或者 bootstrap.servers。默认情况下，会从每个 Kafka 分区的最新偏移量开始消费。 如果你在 Kafka 参数中将配置 auto.offset.reset 设置为 'smallest'，那么它将从最小的偏移量开始消费。

您还可以使用 KafkaUtils.createDirectStream 的其他变体从任意偏移量开始消费。 此外，如果您想访问每个批次中消耗的 Kafka 偏移量，您可以执行以下操作。



https://spark.apache.org/docs/2.2.0/streaming-kafka-0-8-integration.html
