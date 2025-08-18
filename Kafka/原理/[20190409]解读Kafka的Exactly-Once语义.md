
### 1. Exactly-Once语义为什么重要

有些用例（如财务应用程序，物联网应用程序和其他流应用程序）不能接受低于 Exactly-Once 的语义。存款或从银行账户取款时，我们不能接受有重复或丢失信息。作为最终结果，我们需要 Exactly-Once 语义。

### 2. 为什么很难实现

假设我们有一个小的 Kafka 流应用程序，输入分区比较少和输出分区也比较少。我们应用程序的目的是从输入分区接收数据，处理完数据后将其写入输出分区。这里我们需要实现 Exactly-Once 语义保证。在处理过程中有些情况，例如网络故障，系统崩溃以及其他错误会导致数据重复。

#### 2.1 问题一:重复或多次写入
参见图1a。消息 m1 正在被处理写入到 Topic B。消息 m1 成功写入到 Topic B（m1'）但我们的应用程序并未收到确认。可能因为网络延迟导致最终超时。

![]()

![]()

因为应用程序从未收到确认，所以不知道消息是否已经成功写入到 Topic，因此应用程序会重试导致重复写入。参见图1b。消息 m1' 被重复写入到 Topic B。这是一个重复写入问题，需要修复。

#### 2.2 问题二:重复读入输入记录

参见图2a。与上面场景相同，但是，在这个场景下，流应用程序在提交偏移量之前崩溃。由于未提交偏移量，当流应用程序重新启动后，重新读取消息 m1 并再次处理一次（图2b）。这再次导致在 Topic B 中重复写入消息 m1。

### 3. Kafka如何解决

Kafka 使用以下方法通过 Exactly-once 语义解决上述问题。

#### 3.1 幂等Producer

在 Producer 端的幂等性可以通过阻止消息处理多次来实现。这可以通过仅持久化消息一次来实现。在开启幂等性的情况下，每个 Kafka 消息都有两个东西：生产者ID（PID）和序列号（seq）。PID的分配对用户完全透明，永远不会公开给客户端。

![]()

```
producerProps.put("enable.idempotence", "true");
producerProps.put("transactional.id", "100");
```
在 Broker 崩溃或客户端出现故障的情况下，在重试消息发送期间，Topic 仅接受具有新的唯一序列号和生产者ID的消息。 Broker 会自动删除此生产者发送的任何重复消息，以确保幂等性。无需更改其他代码。

#### 3.2 跨分区的事务

为了确保每个消息都被完全处理一次(Exactly-Once)，可以使用事务。事务要么全部执行，要么全都不执行。它们可以确保在选择消息之后，可以将消息和消费消息的偏移量原子性地一起写入多个 Topic/Partitions。

原子事务的代码片段：
```java
producer.initTransactions();
try {
  producer.beginTxn();
   // ... read from input topic
   // ... transform
  producer.send(rec1); // topic A
  producer.send(rec2); // topic B
  producer.send(rec3); // topic C
  producer.sendOffsetsToTxn(offsetsToCommit, “group-id”);
  producer.commitTransaction();
} catch ( Exception e ) {
  producer.abortTransaction();
}
```
Kafka 0.11 版本引入了两个组件 - `Transaction Coordinator`和`Transaction Log` - 它们维护原子写入的状态。

下图详细说明了在各个分区之间启用原子事务的高级事件流：
![]()

- `initTransactions（）`向协调器注册`transactional.id`。
- 协调器突破了PID的时期，以便该PID的先前实例被视为僵尸并被隔离。 这些僵尸不会接受将来的写作。
- 当生产者即将向分区发送数据时，生产者在协调器中添加一个分区。


原文:[Interpreting Kafka's Exactly-Once Semantics](https://dzone.com/articles/interpreting-kafkas-exactly-once-semantics)
