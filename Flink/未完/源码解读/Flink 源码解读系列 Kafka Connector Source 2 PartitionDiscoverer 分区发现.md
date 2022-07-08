
在 open 方法中初始化创建 partitionDiscoverer 分区发现器：
```java
// 分区发现器
this.partitionDiscoverer = createPartitionDiscoverer(
        topicsDescriptor,
        getRuntimeContext().getIndexOfThisSubtask(),
        getRuntimeContext().getNumberOfParallelSubtasks()
);
this.partitionDiscoverer.open();
```

```java
protected AbstractPartitionDiscoverer createPartitionDiscoverer(
        KafkaTopicsDescriptor topicsDescriptor, int indexOfThisSubtask, int numParallelSubtasks) {
    return new KafkaPartitionDiscoverer(topicsDescriptor, indexOfThisSubtask, numParallelSubtasks, properties);
}
```

###

- topicsDescriptor：Topic 描述符
- indexOfThisSubtask：SubTask Id
- numParallelSubtasks：SubTask 的个数
- kafkaProperties：Kafka 配置文件

```java
public KafkaPartitionDiscoverer(KafkaTopicsDescriptor topicsDescriptor,
        int indexOfThisSubtask,
        int numParallelSubtasks,
        Properties kafkaProperties) {
    super(topicsDescriptor, indexOfThisSubtask, numParallelSubtasks);
    this.kafkaProperties = checkNotNull(kafkaProperties);
}

public AbstractPartitionDiscoverer(KafkaTopicsDescriptor topicsDescriptor, int indexOfThisSubtask, int numParallelSubtasks) {
    this.topicsDescriptor = checkNotNull(topicsDescriptor);
    this.indexOfThisSubtask = indexOfThisSubtask;
    this.numParallelSubtasks = numParallelSubtasks;
    this.discoveredPartitions = new HashSet<>();
}
```

### open

开启分区发现：
```java
// AbstractPartitionDiscoverer
public void open() throws Exception {
    closed = false;
    initializeConnections();
}
```
将变量 closed 设置为 false，最重要的是初始化连接，在这是初始化 Kafka 连接，由派生类 KafkaPartitionDiscoverer 实现：
```java
@Override
protected void initializeConnections() {
    this.kafkaConsumer = new KafkaConsumer<>(kafkaProperties);
}
```
初始化 Kafka 连接的过程其实是根据传递进来的配置文件创建 Kafka 消费者 KafkaConsumer 的过程。

### discoverPartitions

```java
public List<KafkaTopicPartition> discoverPartitions() throws WakeupException, ClosedException {
    if (!closed && !wakeup) {
        try {
            List<KafkaTopicPartition> newDiscoveredPartitions = null;
            // 判断 Topic 订阅模式
            if (topicsDescriptor.isFixedTopics()) {
                // 指定 Topic 列表模式
                // 获取指定 Topic 的所有 Partition
                newDiscoveredPartitions = getAllPartitionsForTopics(topicsDescriptor.getFixedTopics());
            } else {
                // Topic 正则表达式模式
                // 获取所有 Topic
                List<String> matchedTopics = getAllTopics();
                // 保留符合正则要求的分区
                Iterator<String> iter = matchedTopics.iterator();
                while (iter.hasNext()) {
                    if (!topicsDescriptor.isMatchingTopic(iter.next())) {
                        iter.remove();
                    }
                }
                // 符合要求的 Topic 列表
                if (matchedTopics.size() != 0) {
                    // 获取符合要求的 Topic 的所有 Partition
                    newDiscoveredPartitions = getAllPartitionsForTopics(matchedTopics);
                }
            }
            if (newDiscoveredPartitions == null || newDiscoveredPartitions.isEmpty()) {
                // 抛出 Unable to retrieve any partitions 异常
            } else {
                Iterator<KafkaTopicPartition> iter = newDiscoveredPartitions.iterator();
                KafkaTopicPartition nextPartition;
                while (iter.hasNext()) {
                    nextPartition = iter.next();
                    // 不符合要求删除 不是新发现的分区或者不是分配给该 SubTask
                    if (!setAndCheckDiscoveredPartition(nextPartition)) {
                        iter.remove();
                    }
                }
            }
            return newDiscoveredPartitions;
        } catch (WakeupException e) {
            wakeup = false;
            throw e;
        }
    } else if (!closed && wakeup) {
        wakeup = false;
        throw new WakeupException();
    } else {
        throw new ClosedException();
    }
}

// 判断分区是否符合要求
public boolean setAndCheckDiscoveredPartition(KafkaTopicPartition partition) {
    // 判断是否在已经发现的分区列表中
    if (isUndiscoveredPartition(partition)) {
        // 如果是新发现的分区 Partition 则添加到已发现分区列表中
        discoveredPartitions.add(partition);
        // 判断分区是否分配到该 SubTask
        return KafkaTopicPartitionAssigner.assign(partition, numParallelSubtasks) == indexOfThisSubtask;
    }
    return false;
}
// 判断是否在已经发现的分区列表中
private boolean isUndiscoveredPartition(KafkaTopicPartition partition) {
    return !discoveredPartitions.contains(partition);
}
```




....
