Kafka 在 0.8 和 0.10 之间引入了一种新的消费者 API，因此 Spark Streaming 与 Kafka 集成也有两种依赖包可以选择：
- spark-streaming-kafka-0-8
- spark-streaming-kafka-0-10

需要根据 Kafka 版本以及所需的功能选择正确的依赖包。需要注意的是 与 0.8 的集成（spark-streaming-kafka-0-8）可以兼容 Kafka 0.8 版本之后的版本，但是与 0.10 的集成（spark-streaming-kafka-0-10）与 Kafka 0.10 版本之前的版本不兼容。

## 1. spark-streaming-kafka-0-8

spark-streaming-kafka-0-8 兼容 Kafka 0.8.2.1 及以后的版本。从 Spark 2.3.0 开始，对 Kafka 0.8 支持已被标记为过时。

## 2. spark-streaming-kafka-0-10

spark-streaming-kafka-0-10 兼容 Kafka 0.10.0 及以后的版本。从 Spark 2.3.0 开始，该依赖包下的 API 变为稳定版本。

## 3. 对比

| 特性 | spark-streaming-kafka-0-8 | spark-streaming-kafka-0-10 |
| :------------- | :------------- |
| Kafka Broker 版本 | 0.8.2.1 或者更高版本 | 0.10.0 或者更高版本 |
| Receiver DStream | 支持 | 不支持 |
| Direct DStream | 支持 | 支持 |
| SSL / TLS 支持 | 不支持 | 支持 |
| Offset Commit API | 不支持 | 支持 |
| 动态 Topic 订阅 | 不支持 | 支持 |

## 4. 建议

如果 Kafka 版本大于等于 0.10.0，且 Spark 版本大于等于 2.3.0，应使用 spark-streaming-kafka-0-10。

| Spark 版本  | Kafka 版本 | Maven 依赖 |
| :------------- | :------------- | :------------- |
| 2.0.0  | 0.8.2.1 或者更高版本 | spark-streaming-kafka-0-8_2.10|
| 2.2.0  | 0.8.2.1 或者更高版本 | spark-streaming-kafka-0-8_2.10 |
| 2.3.0  | 0.8.2.1 - 0.9.0.1 | spark-streaming-kafka-0-10_2.11 |
| 2.3.0  | 0.10.0 或者更高版本 | spark-streaming-kafka-0-10_2.11 |
| 2.4.0  | 0.10.0 或者更高版本 | spark-streaming-kafka-0-10_2.11 |
| 3.0.0  | 0.10.0 或者更高版本 | spark-streaming-kafka-0-10_2.12 |

参考：
- https://spark.apache.org/docs/2.2.0/streaming-kafka-integration.html
- https://spark.apache.org/docs/2.3.0/streaming-kafka-integration.html
