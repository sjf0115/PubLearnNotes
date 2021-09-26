

Single Message Transformations (SMT) 用来处理流经 Connect 的消息。Source Connector 生成的消息在写入 Kafka 之前应用 SMT 对消息进行转换，也可以在 Kafka 消息发送到 Sink Connector 之前应用 SMT 对其进行转换。

> 如果内置的 SMT 不满足我们的需求，我们可以自定义 SMT。详细信息，请参阅[自定义转换]()。

下面我们详细介绍常用的 SMT。

### 1. Cast






















参考：
- [Kafka Connect Transformations](https://docs.confluent.io/platform/current/connect/transforms/overview.html)
