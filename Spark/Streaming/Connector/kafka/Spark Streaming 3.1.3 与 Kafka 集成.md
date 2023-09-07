
### ２.1 引入

对于使用 SBT/Maven 项目定义的 Scala/Java 应用程序，请引入如下依赖：
```xml
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-streaming-kafka-0-10_2.12</artifactId>
    <version>3.1.3</version>
</dependency>
```
不要手动添加 `org.apache.kafka` (例如 kafka-clients ) 的依赖项。`spark-streaming-kafka-0-10` 依赖具有传递依赖关系，并且不同版本可能难兼容。

























> 原文:[Spark Streaming + Kafka Integration Guide (Kafka broker version 0.10.0 or higher)](https://spark.apache.org/docs/3.1.3/streaming-kafka-0-10-integration.html)
