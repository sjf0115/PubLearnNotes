https://zhuanlan.zhihu.com/p/455444829
https://cloud.tencent.com/developer/article/1583233
http://caorong.net/cao/blog/94
https://blog.51cto.com/simplelife/2401521



## 1. 语义保障

### 1.1 EXACTLY_ONCE

在 EXACTLY_ONCE 语义下，Flink 生产者将在 Kafka 事务中写入所有消息，然后在检查点完成时提交给 Kafka。

在这种模式下，FlinkKafkaProducer 会设置一个 FlinkKafkaInternalProducer 池。每个检查点都会创建一个 Kafka 事务，该事务在 notifyCheckpointComplete(long) 上提交。如果检查点完成通知延迟，FlinkKafkaProducer 可能会用完池中的 FlinkKafkaInternalProducer。在这种情况下，任何后续的 snapshotState(FunctionSnapshotContext) 请求都将失败，FlinkKafkaProducer 将继续使用前一个检查点的 FlinkKafkaInternalProducer。为了减少检查点失败的机会，有四个选项：
- 减少最大并发检查点的数量
- 使检查点更可靠（以便它们更快地完成）
- 增加检查点之间的延迟
- 增加 FlinkKafkaInternalProducers 池的大小

### 1.2 AT_LEAST_ONCE

AT_LEAST_ONCE 语义下，Flink 生产者将等待 Kafka 缓冲区中的所有未完成消息在检查点上被 Kafka 生产者确认。

### 1.3 NONE

NONE 语义表示没有任何保证。如果发生故障，消息可能会丢失和/或重复。

## 2. 数据结构

### 2.1 KafkaTransactionState

处理事务的状态，主要用来存储事务相关的信息：
```java
public static class KafkaTransactionState {
    private final transient FlinkKafkaInternalProducer<byte[], byte[]> producer;
    @Nullable final String transactionalId;
    final long producerId;
    final short epoch;
    ...
}
```
这里提供了 producer，producerId，transactionId 以及 epoch，并且重写了 toString，equals 和 hashCode方法。

### 2.2 KafkaTransactionContext

与 FlinkKafkaProducer 实例关联的上下文，本质上是一个事务Id的集合，主要用来跟踪 transactionalIds：
```java
public static class KafkaTransactionContext {
    final Set<String> transactionalIds;
    ...
}
```

### 2.3 TransactionStateSerializer

实现对 FlinkKafkaProducer.KafkaTransactionState 的序列化与反序列化：
```java
public static class TransactionStateSerializer extends TypeSerializerSingleton<FlinkKafkaProducer.KafkaTransactionState> {
...
}
```

### 2.4 ContextStateSerializer

实现对 FlinkKafkaProducer.KafkaTransactionContext 的序列化与反序列化：
```java
public static class ContextStateSerializer extends TypeSerializerSingleton<FlinkKafkaProducer.KafkaTransactionContext> {
  ...
}
```

### 2.5 NextTransactionalIdHint

NextTransactionalIdHint 存储推断下一个可以安全使用的事务 ID 所需的信息。记录了 lastParallelism 和 nextFreeTransactionalId：
```java
public static class NextTransactionalIdHint {
    public int lastParallelism = 0;
    public long nextFreeTransactionalId = 0;
    ...
}
```
同时提供了一个对应的序列化器：
```java
public static class NextTransactionalIdHintSerializer extends TypeSerializerSingleton<NextTransactionalIdHint> {
    ...
}
```

### 2.6 TransactionalIdsGenerator

```java

```



## 3. FlinkKafkaInternalProducer



## 4. Checkpoint 处理

### 4.1 initializeState

如果设置的是 EXACTLY_ONCE 或者 AT_LEAST_ONCE 语义，需要保证开启 Checkpoint，否则重置为 NONE 语义:
```java
if (semantic != FlinkKafkaProducer.Semantic.NONE && !((StreamingRuntimeContext) this.getRuntimeContext()).isCheckpointingEnabled()) {
    // LOG.warn();
    semantic = FlinkKafkaProducer.Semantic.NONE;
}
```
Kafka 事务 ID 的长度必须小于 short 的最大值，因此我们在必要时将此处截断为更合理长度的字符串：
```java
if (taskName.length() > maxTaskNameSize) {
    taskName = taskName.substring(0, maxTaskNameSize);
    //LOG.warn();
}
```


nextTransactionalIdHintState ？

创建事务 Id 生成器：
```java
transactionalIdsGenerator = new TransactionalIdsGenerator(
    taskName + "-" + ((StreamingRuntimeContext) getRuntimeContext()).getOperatorUniqueID(),
    getRuntimeContext().getIndexOfThisSubtask(),
    getRuntimeContext().getNumberOfParallelSubtasks(),
    kafkaProducersPoolSize,
    SAFE_SCALE_DOWN_FACTOR
);
```



### 4.2 snapshotState

为了避免重复，只有第一个子任务跟踪下一个事务 id 提示。否则，所有子任务都会写入完全相同的信息：
```java
if (getRuntimeContext().getIndexOfThisSubtask() == 0
        && semantic == FlinkKafkaProducer.Semantic.EXACTLY_ONCE) {
  ...
}
```
如果我们扩容，一些（未知）子任务必须从头开始创建新的事务 ID。在这种情况下，我们将 nextFreeTransactionalId 调整为可用于此扩展的 transactionalId 的范围：
```java
// 并行度大于lastParallelism
if (getRuntimeContext().getNumberOfParallelSubtasks()
        > nextTransactionalIdHint.lastParallelism) {
    nextFreeTransactionalId += getRuntimeContext().getNumberOfParallelSubtasks() * kafkaProducersPoolSize;
}
```
存储到 nextTransactionalIdHintState 状态中：
```java
nextTransactionalIdHintState.add(
    // 生成 NextTransactionalIdHint
    new FlinkKafkaProducer.NextTransactionalIdHint(
        getRuntimeContext().getNumberOfParallelSubtasks(),
        nextFreeTransactionalId
    )
);
```

### 4.3 notifyCheckpointComplete



### 4.4 notifyCheckpointAborted

## 5. 事务处理

### 5.1 beginTransaction

使用 beginTransaction 方法开启一个事务，返回 KafkaTransactionState 对象：
```java
protected FlinkKafkaProducer.KafkaTransactionState beginTransaction() {
...
}
```
开启事务具体取决于你所设置的语义保障，核心是创建 Producer 以及事务Id（是否有取决于语义保障），最终包装为
KafkaTransactionState 对象返回。

【1】 EXACTLY_ONCE

如果是 EXACTLY_ONCE 语义保障，首先需要每次在 beginTransaction() 中创建一个事务 Producer，然后开启事务，并最终返回一个事务状态对象：
```java
FlinkKafkaInternalProducer<byte[], byte[]> producer = createTransactionalProducer();
// 调用
producer.beginTransaction();
return new FlinkKafkaProducer.KafkaTransactionState(producer.getTransactionalId(), producer);
```
此时 KafkaTransactionState 事务状态对象中保存了 Producer 以及事务 Id。

创建事务 Producer：
```java
private FlinkKafkaInternalProducer<byte[], byte[]> createTransactionalProducer() throws FlinkKafkaException {
    // 从当前可用事务Id集合中获取一个可用的事务Id
    String transactionalId = availableTransactionalIds.poll();
    if (transactionalId == null) {
        // 抛出异常 提示增大 Kafka 生产者池大小或者降低 Checkoint 并发个数
        throw new FlinkKafkaException(xxx);
    }
    // 创建 FlinkKafkaInternalProducer 对象
    // 下面两行是简化后的核心逻辑 实际调用 initTransactionalProducer(transactionalId, true);
    producerConfig.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, transactionalId);
    FlinkKafkaInternalProducer<byte[], byte[]> producer = new FlinkKafkaInternalProducer<>(this.producerConfig);
    // 初始化事务
    producer.initTransactions();
    return producer;
}
```
核心是创建 FlinkKafkaInternalProducer 对象。通过将获取的一个可用事务 Id 放在 Properties (key 为 transactional.id )中，并作为参数传递给 FlinkKafkaInternalProducer 对象。

【2】 NONE & AT_LEAST_ONCE

NONE & AT_LEAST_ONCE 语义下需要创建的是非事务性 Produce。同时如果没有必要，不需要在每个 beginTransaction() 上创建新的 Producer：
```java
// 获取当前事务状态
final FlinkKafkaProducer.KafkaTransactionState currentTransaction = currentTransaction();
if (currentTransaction != null && currentTransaction.producer != null) {
    return new FlinkKafkaProducer.KafkaTransactionState(currentTransaction.producer);
}
// 下面几行是简化后的核心逻辑 删除了注册 Metirc 的逻辑
// 相比事务 Producer 需要移除事务ID
producerConfig.remove(ProducerConfig.TRANSACTIONAL_ID_CONFIG);
FlinkKafkaInternalProducer<byte[], byte[]> producer = new FlinkKafkaInternalProducer<>(this.producerConfig);
return new FlinkKafkaProducer.KafkaTransactionState(producer);
```
此时 KafkaTransactionState 事务状态对象中只保存了 Producer。

### 5.2 preCommit

根据设置的处理语义的不同处理逻辑也不一样，预提交阶段只适用于 EXACTLY_ONCE 和 AT_LEAST_ONCE 语义：
```java
protected void preCommit(FlinkKafkaProducer.KafkaTransactionState transaction) throws FlinkKafkaException {
    switch (semantic) {
        case EXACTLY_ONCE:
        case AT_LEAST_ONCE:
            flush(transaction);
            break;
        case NONE:
            break;
        default:
            throw new UnsupportedOperationException("Not implemented semantic");
    }
    checkErroneous();
}
```
逻辑比较简单，直接调用 flush 函数将数据刷写到 Kafka 集群的磁盘上：
```java
private void flush(FlinkKafkaProducer.KafkaTransactionState transaction) throws FlinkKafkaException {
    if (transaction.producer != null) {
        transaction.producer.flush();
    }
    long pendingRecordsCount = pendingRecords.get();
    if (pendingRecordsCount != 0) {
        // 待提交的记录数必须大于0
        throw new IllegalStateException(xxx);
    }
    // if the flushed requests has errors, we should propagate it also and fail the checkpoint
    checkErroneous();
}
```
### 5.3 commit
commit 阶段会调用 Producer 的 commitTransaction() 方法来提交事务，然后回收该 Producer：
```java
protected void commit(FlinkKafkaProducer.KafkaTransactionState transaction) {
    if (transaction.isTransactional()) {
        try {
            transaction.producer.commitTransaction();
        } finally {
   // 回收
            recycleTransactionalProducer(transaction.producer);
        }
    }
}

private void recycleTransactionalProducer(FlinkKafkaInternalProducer<byte[], byte[]> producer) {
// 回收事务Id
    availableTransactionalIds.add(producer.getTransactionalId());
    // 刷写 Producer
    producer.flush();
    // 关闭 Producer
    producer.close(Duration.ofSeconds(0));
}
```

### 5.4 recoverAndCommit

```java
protected void recoverAndCommit(FlinkKafkaProducer.KafkaTransactionState transaction) {
    if (transaction.isTransactional()) {
        FlinkKafkaInternalProducer<byte[], byte[]> producer = null;
        try {
            // 重新初始化 Producer
            producer = initTransactionalProducer(transaction.transactionalId, false);
            // 恢复 Producer 的事务
            producer.resumeTransaction(transaction.producerId, transaction.epoch);
            // 提交事务
            producer.commitTransaction();
        } catch (InvalidTxnStateException | ProducerFencedException ex) {
            // 可能是因为之前已经提交过该事务
            LOG.warn(xxx);
        } finally {
            if (producer != null) {
                producer.close(0, TimeUnit.SECONDS);
            }
        }
    }
}
```

### 5.5 abort
abort 阶段调用 Producer 的 abortTransaction() 方法来终止事务，然后回收该 Producer：
```java
protected void abort(FlinkKafkaProducer.KafkaTransactionState transaction) {
    if (transaction.isTransactional()) {
  // 终止事务
        transaction.producer.abortTransaction();
        // 回收
        recycleTransactionalProducer(transaction.producer);
    }
}
```

### 5.6 recoverAndAbort

```java
protected void recoverAndAbort(FlinkKafkaProducer.KafkaTransactionState transaction) {
    if (transaction.isTransactional()) {
        FlinkKafkaInternalProducer<byte[], byte[]> producer = null;
        try {
            producer = initTransactionalProducer(transaction.transactionalId, false);
            producer.initTransactions();
        } finally {
            if (producer != null) {
                producer.close(0, TimeUnit.SECONDS);
            }
        }
    }
}
```

## 6. 数据处理

invoke 的核心作用就是将数据流中的数据对象转换为 Kafka 可以直接识别的 ProducerRecord：

```java
public void invoke(FlinkKafkaProducer.KafkaTransactionState transaction, IN next, Context context) throws FlinkKafkaException {
  ...
}
```
根据指定的 SerializationSchema 不同，处理逻辑也有不同。如果指定的是 KeyedSerializationSchema：
```java
byte[] serializedKey = keyedSchema.serializeKey(next);
byte[] serializedValue = keyedSchema.serializeValue(next);
String targetTopic = keyedSchema.getTargetTopic(next);
if (targetTopic == null) {
    targetTopic = defaultTopicId;
}

Long timestamp = null;
if (this.writeTimestampToKafka) {
    timestamp = context.timestamp();
}

int[] partitions = topicPartitionsMap.get(targetTopic);
if (null == partitions) {
    partitions = getPartitionsByTopic(targetTopic, transaction.producer);
    topicPartitionsMap.put(targetTopic, partitions);
}
// 组装 ProducerRecord
if (flinkKafkaPartitioner != null) {
    // 如果指定了 Partitioner
    record = new ProducerRecord<>(
        targetTopic,
        flinkKafkaPartitioner.partition(
            next, serializedKey, serializedValue,
            targetTopic, partitions
        ),
        timestamp, serializedKey, serializedValue
    );
} else {
    record = new ProducerRecord<>(targetTopic, null, timestamp, serializedKey, serializedValue);
}
```
如果指定的是 KafkaSerializationSchema：
```java
if (kafkaSchema instanceof KafkaContextAware) {
    // 如果实现了 KafkaContextAware
    @SuppressWarnings("unchecked")
    KafkaContextAware<IN> contextAwareSchema = (KafkaContextAware<IN>) kafkaSchema;
    // 目标 Topic
    String targetTopic = contextAwareSchema.getTargetTopic(next);
    if (targetTopic == null) {
        // 如果没有指定目标 Topic 则使用默认 Topic
        targetTopic = defaultTopicId;
    }
    // 目标 Topic 的分区
    int[] partitions = topicPartitionsMap.get(targetTopic);
    if (null == partitions) {
        partitions = getPartitionsByTopic(targetTopic, transaction.producer);
        topicPartitionsMap.put(targetTopic, partitions);
    }
    contextAwareSchema.setPartitions(partitions);
}
// 序列化为 ProducerRecord
record = kafkaSchema.serialize(next, context.timestamp());
```
在 KafkaSerializationSchema 情况下，需要注意的是是否实现了 KafkaContextAware 接口。


## 7. 初始化

(1) FlinkKafkaProducer 提供了如下几种构造器：
- SerializationSchema
- KeyedSerializationSchema
- KafkaSerializationSchema

如下是提供基于 SerializationSchema 的构造器：
```java
public FlinkKafkaProducer(String brokerList, String topicId, SerializationSchema<IN> serializationSchema);

public FlinkKafkaProducer(String topicId, SerializationSchema<IN> serializationSchema, Properties producerConfig);

public FlinkKafkaProducer(String topicId, SerializationSchema<IN> serializationSchema,
            Properties producerConfig, Optional<FlinkKafkaPartitioner<IN>> customPartitioner);

public FlinkKafkaProducer(String topicId, SerializationSchema<IN> serializationSchema,
            Properties producerConfig, @Nullable FlinkKafkaPartitioner<IN> customPartitioner,
            FlinkKafkaProducer.Semantic semantic, int kafkaProducersPoolSize);
```

如下是提供基于 KeyedSerializationSchema 的构造器：
```java
public FlinkKafkaProducer(String defaultTopicId, KeyedSerializationSchema<IN> serializationSchema,
            Properties producerConfig, Optional<FlinkKafkaPartitioner<IN>> customPartitioner,
            FlinkKafkaProducer.Semantic semantic, int kafkaProducersPoolSize);

public FlinkKafkaProducer(String defaultTopicId, KeyedSerializationSchema<IN> serializationSchema,
        Properties producerConfig, Optional<FlinkKafkaPartitioner<IN>> customPartitioner);

public FlinkKafkaProducer(String topicId, KeyedSerializationSchema<IN> serializationSchema,
        Properties producerConfig, FlinkKafkaProducer.Semantic semantic);

public FlinkKafkaProducer(String topicId, KeyedSerializationSchema<IN> serializationSchema,
        Properties producerConfig);

public FlinkKafkaProducer(String brokerList, String topicId, KeyedSerializationSchema<IN> serializationSchema);
```
如下是提供基于 KafkaSerializationSchema 的构造器：
```java
private FlinkKafkaProducer(String defaultTopic, KeyedSerializationSchema<IN> keyedSchema, FlinkKafkaPartitioner<IN> customPartitioner,
            KafkaSerializationSchema<IN> kafkaSchema, Properties producerConfig, FlinkKafkaProducer.Semantic semantic,
            int kafkaProducersPoolSize);

public FlinkKafkaProducer(String defaultTopic, KafkaSerializationSchema<IN> serializationSchema,
            Properties producerConfig, FlinkKafkaProducer.Semantic semantic, int kafkaProducersPoolSize);

public FlinkKafkaProducer(String defaultTopic, KafkaSerializationSchema<IN> serializationSchema,
          Properties producerConfig, FlinkKafkaProducer.Semantic semantic);
```

(2) 序列化

序列化需要指定 KeyedSerializationSchema 或者 KafkaSerializationSchema。两个只能指定其中一个，从 Flink 1.9 版本开始推荐使用 KafkaSerializationSchema。如果指定 KafkaSerializationSchema：
```java
this.keyedSchema = null;
this.kafkaSchema = kafkaSchema;
this.flinkKafkaPartitioner = null;
ClosureCleaner.clean(this.kafkaSchema, ExecutionConfig.ClosureCleanerLevel.RECURSIVE, true);

if (customPartitioner != null) {
    // 自定义 Partitioner 只能用于 KeyedSerializationSchema 或者 SerializationSchema
    throw new IllegalArgumentException(xxx);
}
```
如果指定的是 KeyedSerializationSchema：
```java
this.kafkaSchema = null;
this.keyedSchema = keyedSchema;
this.flinkKafkaPartitioner = customPartitioner;
ClosureCleaner.clean(this.flinkKafkaPartitioner, ExecutionConfig.ClosureCleanerLevel.RECURSIVE, true);
ClosureCleaner.clean(this.keyedSchema, ExecutionConfig.ClosureCleanerLevel.RECURSIVE, true);
```
不建议用户指定 Key 和 Value 的序列化类，使用默认的 ByteArraySerializer 即可：
```java
if (!producerConfig.containsKey(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG)) {
    this.producerConfig.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, ByteArraySerializer.class.getName());
}

if (!producerConfig.containsKey(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG)) {
    this.producerConfig.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, ByteArraySerializer.class.getName());
}
```

(3) 事务超时时间

如果没有设置 Producer 的事务超时时间则默认为1小时：
```java
if (!producerConfig.containsKey(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG)) {
    // 默认1小时
    long timeout = DEFAULT_KAFKA_TRANSACTION_TIMEOUT.toMilliseconds();
    this.producerConfig.put(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, (int) timeout);
}
```
