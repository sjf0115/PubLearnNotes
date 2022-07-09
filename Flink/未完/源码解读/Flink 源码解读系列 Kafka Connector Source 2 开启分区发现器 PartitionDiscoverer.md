
## 1. 创建分区发现器

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

## 2. 开启分区发现器

通过如下代码开启分区发现器：
```java
public void open() throws Exception {
    closed = false;
    initializeConnections();
}
```
将状态变量 closed 设置为 false，表示分区发现器已开启。开启分区发现器比较简单，分区发现器本质上是一个 Kafka 消费者，开启分区发现器只需要创建一个 Kafka 消费者 kafkaConsumer 即可：
```java
@Override
protected void initializeConnections() {
    this.kafkaConsumer = new KafkaConsumer<>(kafkaProperties);
}
```
> 开启分区发现器的过程其实是根据传递进来的配置文件创建 Kafka 消费者 KafkaConsumer 的过程。

## 3. 分区发现

### 3.1 获取 Topic 的分区

#### 3.1.1 固定 Topic 列表模式

如果是固定 Topic 列表模式，直接获取指定 Topic 的所有分区：
```java
// 固定 Topic 列表模式
if (topicsDescriptor.isFixedTopics()) {
    // 获取指定 Topic 的所有 Partition
    newDiscoveredPartitions = getAllPartitionsForTopics(topicsDescriptor.getFixedTopics());
}
````
下面具体看看 getAllPartitionsForTopics 函数如何获取指定 Topic 的所有的分区。首先循环遍历所有 Topic，通过调用 Kafka 消费者 API 中的 partitionsFor 来获取对应 Topic 下所有的 Partition 信息。每一个 Partition 封装为一个 KafkaTopicPartition 对象，然后放在列表中返回：
```java
// 获取指定 Topic 的所有 Partition
final List<KafkaTopicPartition> partitions = new LinkedList<>();
for (String topic : topics) {
    // 获取对应 Topic 的 Partition 信息
    final List<PartitionInfo> kafkaPartitions = kafkaConsumer.partitionsFor(topic);
    if (kafkaPartitions == null) {
        // 抛出 Could not fetch partitions 异常
    }
    for (PartitionInfo partitionInfo : kafkaPartitions) {
        // Partition 信息封装为 KafkaTopicPartition 存储在 partitions 列表中
        partitions.add(new KafkaTopicPartition(partitionInfo.topic(), partitionInfo.partition()));
    }
}
```

#### 3.1.2 Topic 正则表达式模式

如果订阅 Topic 的模式为正则表达式模式，不能像固定 Topic 模式一样可以直接获取到所有需要的 Topic。首先通过 getAllTopics 函数获取 Kafka 中所有的 Topic，然后迭代遍历每一个 Topic 判断是否满足给定的正则表达式，最终只保留满足要求的 Topic。有了 Topic 之后，跟上述模式一样，都需要通过 getAllPartitionsForTopics 获取指定 Topic 的 Partition：
```java
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
```
获取所有 Topic 是通过 getAllTopics 函数获取的，如下所示内部是通过调用 Kafka 消费者 API 中的 listTopics 函数获取全部的 Topic：
```java
protected List<String> getAllTopics() throws AbstractPartitionDiscoverer.WakeupException {
    try {
        return new ArrayList<>(kafkaConsumer.listTopics().keySet());
    } catch (org.apache.kafka.common.errors.WakeupException e) {
        throw new AbstractPartitionDiscoverer.WakeupException();
    }
}
```
### 3.2 校验是否满足要求

如果指定 Topic 下没有可用分区，直接抛出检索不到分区异常。如果指定 Topic 下有可用分区，需要迭代遍历每一个分区并校验是不是符合要求，即新发现的分区&分配给当前 SubTask：
```java
if (newDiscoveredPartitions == null || newDiscoveredPartitions.isEmpty()) {
    // 抛出 Unable to retrieve any partitions 异常
} else {
    Iterator<KafkaTopicPartition> iter = newDiscoveredPartitions.iterator();
    KafkaTopicPartition nextPartition;
    while (iter.hasNext()) {
        nextPartition = iter.next();
        // 只保留符合要求分区，即新发现的分区&分配给当前 SubTask
        if (!setAndCheckDiscoveredPartition(nextPartition)) {
            iter.remove();
        }
    }
}
```
如上我们可以看到是通过 setAndCheckDiscoveredPartition 函数校验是不是符合要求的。那是如何校验的呢？首先判断指定的分区是不是已经 在 discoveredPartitions 发现分区列表中出现了。如果不在列表中说明是新发现的分区，首先需要添加到 discoveredPartitions 发现分区列表中，最重要的是判断该分区是不是分配给当前 SubTask。只有分配给当前 SubTask 的新分区才是我们的目标：
```java
public boolean setAndCheckDiscoveredPartition(KafkaTopicPartition partition) {
    // 判断是否在已经发现的分区列表中
    if (isUndiscoveredPartition(partition)) {
        // 如果是新发现的分区 Partition 则添加到发现分区列表中
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
## 4. 中断分区发现器

通过如下代码中断分区发现器：
```java
public void wakeup() {
    wakeup = true;
    wakeupConnections();
}
```
中断分区发现器非常简单，分区发现器本质上是一个 Kafka 消费者，中断分区发现器只需要中断 Kafka 消费者 kafkaConsumer 即可：
```java
protected void wakeupConnections() {
    if (this.kafkaConsumer != null) {
        this.kafkaConsumer.wakeup();
    }
}
```

## 5. 关闭分区发现器

通过如下代码关闭分区发现器：
```java
public void close() throws Exception {
    closed = true;
    closeConnections();
}
```
关闭分区发现器跟中断一样，需要关闭 Kafka 消费者 kafkaConsumer 即可：
```java
protected void closeConnections() throws Exception {
    if (this.kafkaConsumer != null) {
        this.kafkaConsumer.close();
        this.kafkaConsumer = null;
    }
}
```

....
