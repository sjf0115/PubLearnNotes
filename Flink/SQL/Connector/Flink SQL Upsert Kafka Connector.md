> Flink 版本：1.13.5

Upsert Kafka Connector 可以以 upsert 的方式从 Kafka Topic 读取数据或者将数据写入 Kafka Topic。

作为 Source，upsert-kafka Connector 可以产生变更日志流(Changelog)，其中每条数据记录代表一个更新或删除事件。更准确地说，数据记录中的值被解释为相同键最后一个值的 `UPDATE`(如果有相同键的话，如果相应的键还不存在，更新将被视为一个 `INSERT`）。如果用表来类比的话，变更日志流中的数据记录被解释为 `UPSERT` 又名 `INSERT/UPDATE`，因为具有相同键的已有行都将会被覆盖。此外，NULL 值以特殊方式解释：具有空值的记录表示一个 `DELETE`。

作为 Sink，upsert-kafka Connector 可以消费变更日志流。将 `INSERT/UPDATE_AFTER` 数据以普通的 Kafka 消息值写入 Kafka，将 `DELETE` 数据以具有 NULL 值的 Kafka 消息写入 Kafka(表示对应 key 的消息被删除)。Flink 会根据主键列的值对数据进行分区，从而保证主键上消息的有序性，因此同一键上的更新/删除消息会落入同一个分区。

## 1. 依赖

为了使用 Upsert Kafka Connector，使用 Maven 构建自动化工具需要添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-connector-kafka_2.11</artifactId>
  <version>1.13.6</version>
</dependency>
```
如果在 SQL Client 中使用如下添加 [flink-sql-connector-kafka_2.11-1.13.6](https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka_2.11/1.13.6/flink-sql-connector-kafka_2.11-1.13.6.jar) JAR 包。




原文: [Upsert Kafka SQL Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/upsert-kafka/)
