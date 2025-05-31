
思路: 连接上 Kafka 根据输入的 Topic 模式来获取 Topic 下的分区
- 连接上 Kafka: 不同版本可能不一样，具体实现类实现
- 根据输入的 Topic 模式来获取 Topic 下的分区：通用能力，放在抽象类中实现


本质：分区发现器本质上是对 KafkaConsumer 的一层封装，通过 KafkaConsumer 的 API 实现分区发现。

## 1. 分区发现器框架


| 层级 | 组件 | 职责 | 变化频率 |
| -------- | -------- | -------- | -------- |
| 抽象层 | AbstractPartitionDiscoverer | 定义通用行为约束: 生命周期管理与分区发现行为约束 | 低频变化 |
| 实现层 | KafkaPartitionDiscoverer | 提供Kafka特定版本实现: 生命周期管理与分区发现的版本适配实现 | 高频变化(随Kafka演进) |

![undefined](https://intranetproxy.alipay.com/skylark/lark/0/2025/png/158678/1748482689823-28d8691d-38c1-4528-8850-99d2f1c1bf1a.png)

### 1.1 抽象层

AbstractPartitionDiscoverer 抽象层定义了生命周期管理与分区发现通用行为约束：
- open: 开启分区发现器建立连接，具体交由实现层 initializeConnections 实现
- close: 关闭分区发现器关闭已建立的连接，具体交由实现层 closeConnections 实现
- wakeup: 中断分区发现器中断已建立的连接，具体交由实现层 wakeupConnections 实现
- discoverPartitions: 分区发现，具体交由实现层 getAllPartitionsForTopics、getAllTopics 实现


```java
public abstract class AbstractPartitionDiscoverer {

// 定义通用行为约束
public AbstractPartitionDiscoverer(KafkaTopicsDescriptor topicsDescriptor,
            int indexOfThisSubtask, int numParallelSubtasks) {
        // 构造器
    }

public void open() throws Exception {
        // 开启分区发现器: 建立连接
    }

public void close() throws Exception {
        // 关闭分区发现器: 关闭已建立的连接
    }

public void wakeup() {
        // 中断分区发现器: 中断已建立的连接
    }

public List<KafkaTopicPartition> discoverPartitions() throws WakeupException, ClosedException {
// 分区发现的核心逻辑入口
}

// -------------------------------------------------
// 具体实现类实现

// 建立连接
protected abstract void initializeConnections() throws Exception;

    // 关闭已建立的连接
    protected abstract void closeConnections() throws Exception;

// 中断已建立的连接
    protected abstract void wakeupConnections();

    // 获取指定 Topic 列表的所有分区
    protected abstract List<KafkaTopicPartition> getAllPartitionsForTopics(List<String> topics) throws WakeupException;

    // 获取所有 Topic 列表
    protected abstract List<String> getAllTopics() throws WakeupException;
}
```

### 1.2 实现层

KafkaPartitionDiscoverer 实现层提供 Kafka 特定版本专属实现:
- initializeConnections: 建立连接
- closeConnections: 关闭已建立的连接
- wakeupConnections: 中断已建立的连接
- getAllPartitionsForTopics: 获取指定 Topic 列表的所有分区
- getAllTopics: 获取所有 Topic 列表

```java
public class KafkaPartitionDiscoverer extends AbstractPartitionDiscoverer {
    @Override
    protected void initializeConnections() throws Exception {
        // 建立连接
    }

    @Override
    protected void closeConnections() throws Exception {
// 关闭已建立的连接
    }

    @Override
    protected void wakeupConnections() {
// 中断已建立的连接
    }

    @Override
    protected List<KafkaTopicPartition> getAllPartitionsForTopics(List<String> topics) throws WakeupException {
// 获取指定 Topic 列表的所有分区
        return null;
    }

    @Override
    protected List<String> getAllTopics() throws WakeupException {
// 获取所有 Topic 列表
        return null;
    }
}
```

## 2. 创建分区发现器

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

## 3. 开启分区发现器

通过如下代码开启分区发现器：
```java
public void open() throws Exception {
    closed = false;
    initializeConnections();
}
```

开启分区发现器会将状态变量 closed 设置为 false，表示分区发现器已开启。分区发现器本质上是一个 Kafka 消费者，开启分区发现器比较简单，只需要创建一个 Kafka 消费者 kafkaConsumer 即可：
```java
@Override
protected void initializeConnections() {
    this.kafkaConsumer = new KafkaConsumer<>(kafkaProperties);
}
```
> KafkaPartitionDiscoverer
> 开启分区发现器的过程其实是根据传递进来的配置文件创建 Kafka 消费者 KafkaConsumer 的过程。

## 4. 中断分区发现器

通过如下代码中断分区发现器：
```java
public void wakeup() {
    wakeup = true;
    wakeupConnections();
}
```
中断分区发现器会将状态变量 wakeup 设置为 true，表示分区发现器已中断。中断分区发现器本质上是要中断 Kafka 消费者 kafkaConsumer：
```java
protected void wakeupConnections() {
    if (this.kafkaConsumer != null) {
        this.kafkaConsumer.wakeup();
    }
}
```
> KafkaPartitionDiscoverer

## 5. 关闭分区发现器

通过如下代码关闭分区发现器：
```java
public void close() throws Exception {
    closed = true;
    closeConnections();
}
```
关闭分区发现器会将状态变量 closed 设置为 true，表示分区发现器已关闭。关闭分区发现器本质上是要关闭 Kafka 消费者 kafkaConsumer：
```java
protected void closeConnections() throws Exception {
    if (this.kafkaConsumer != null) {
        this.kafkaConsumer.close();
        this.kafkaConsumer = null;
    }
}
```
> KafkaPartitionDiscoverer

## 6. 分区发现

这块是分区发现的核心逻辑。

### 6.1 获取 Topic 的分区

可以通过 Topic 描述符 topicsDescriptor 来判断 Flink 订阅 Kafka Topic 的模式： 固定 Topic 列表模式和 Topic 正则表达式模式。不同模式下获取 Topic 的方式会有一些区别。

#### 6.1.1 固定 Topic 列表模式

如果是固定 Topic 列表模式，可以通过 Topic 描述符的 getFixedTopics 方法获取指定的 Topic，再根据 Topic 获取所有分区：
```java
// 固定 Topic 列表模式
if (topicsDescriptor.isFixedTopics()) {
    // 获取指定 Topic 的所有 Partition
    newDiscoveredPartitions = getAllPartitionsForTopics(topicsDescriptor.getFixedTopics());
}
````
通过上面代码可以知道通过 getAllPartitionsForTopics 函数获取指定 Topic 的所有的分区。那具体如何获取的呢？首先循环遍历所有 Topic，通过调用 Kafka 消费者 API 中的 partitionsFor 来获取对应 Topic 下所有的 Partition 信息。将每一个 Partition 封装为一个 KafkaTopicPartition 对象，然后放在列表中返回：
```java
protected List<KafkaTopicPartition> getAllPartitionsForTopics(List<String> topics)
            throws WakeupException, RuntimeException {
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
}
```
> KafkaPartitionDiscoverer

#### 6.1.2 Topic 正则表达式模式

如果订阅 Topic 的模式为正则表达式模式，不会像固定 Topic 模式一样可以直接获取到所有需要的 Topic。那具体如何获取需要的 Topic 呢？首先通过 getAllTopics 方法获取 Kafka 中所有的 Topic，然后迭代遍历每一个 Topic 判断是否满足给定的正则表达式，最终只保留满足要求的 Topic。有了 Topic 之后，跟上述模式一样，都需要通过 getAllPartitionsForTopics 获取指定 Topic 的 Partition：
```java
// Topic 正则表达式模式
// 获取所有 Topic
List<String> matchedTopics = getAllTopics();
// 保留匹配的 Topic
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
获取所有 Topic 是通过 getAllTopics 方法获取的，如下所示内部是通过调用 Kafka 消费者 API 中的 listTopics 方法获取全部的 Topic：
```java
protected List<String> getAllTopics() throws AbstractPartitionDiscoverer.WakeupException {
    try {
        return new ArrayList<>(kafkaConsumer.listTopics().keySet());
    } catch (org.apache.kafka.common.errors.WakeupException e) {
        throw new AbstractPartitionDiscoverer.WakeupException();
    }
}
```
### 6.2 校验是否满足要求

如果指定的 Topic 下没有可用分区，直接抛出检索不到分区异常。如果指定的 Topic 下有可用分区，需要迭代遍历每一个分区并校验是不是符合要求：分配给当前 SubTask 的分区并且是新发现的分区：
```java
if (newDiscoveredPartitions == null || newDiscoveredPartitions.isEmpty()) {
    // 抛出 Unable to retrieve any partitions 异常
} else {
    Iterator<KafkaTopicPartition> iter = newDiscoveredPartitions.iterator();
    KafkaTopicPartition nextPartition;
    while (iter.hasNext()) {
        nextPartition = iter.next();
        // 只保留符合要求的分区，即新发现的分区&分配给当前 SubTask
        if (!setAndCheckDiscoveredPartition(nextPartition)) {
            iter.remove();
        }
    }
}
```
如上我们可以看到是通过 setAndCheckDiscoveredPartition 方法校验是不是符合要求的。那是如何校验的呢？首先判断指定的分区是不是已经在 discoveredPartitions 已发现分区集合中。如果不在集合中说明是一个新发现的分区，用完之后也需要添加到 discoveredPartitions 已发现分区集合中，确保下次校验的准确性。此外最重要的是判断该分区是不是分配给当前 SubTask。只有分配给当前 SubTask 的新分区才是我们的目标：
```java
public boolean setAndCheckDiscoveredPartition(KafkaTopicPartition partition) {
    // 判断是否在已发现分区集合中
    if (isUndiscoveredPartition(partition)) {
        // 如果是新发现的分区则添加到发现分区集合中
        discoveredPartitions.add(partition);
        // 判断分区是否分配到该 SubTask
        return KafkaTopicPartitionAssigner.assign(partition, numParallelSubtasks) == indexOfThisSubtask;
    }
    return false;
}

// 判断是否在已经发现的分区集合中
private boolean isUndiscoveredPartition(KafkaTopicPartition partition) {
    return !discoveredPartitions.contains(partition);
}
```

### 6.3 分区分配器

Flink Kafka 分区分配器 KafkaTopicPartitionAssigner 的作用是将 Kafka Topic 的分区均匀且确定性地分配给 Flink 的并行子任务（Subtask），通过 assign() 方法实现该目标：
```java
public class KafkaTopicPartitionAssigner {
    public static int assign(KafkaTopicPartition partition, int numParallelSubtasks) {
        int startIndex = ((partition.getTopic().hashCode() * 31) & 0x7FFFFFFF) % numParallelSubtasks;
        return (startIndex + partition.getPartition()) % numParallelSubtasks;
    }
}
```

#### 6.3.1 起始索引计算
```java
int startIndex = ((partition.getTopic().hashCode() * 31) & 0x7FFFFFFF) % numParallelSubtasks;
```
- **Topic 哈希计算**：
  对 Topic 名称计算哈希值（`hashCode()`），并乘以 `31`（类似 Java String 哈希的优化策略），目的是让不同 Topic 的起始索引分布更均匀。
- **非负化处理**：
  `& 0x7FFFFFFF` 确保结果为非负数（屏蔽符号位）。
- **取模映射**：
  将结果对并行度 `numParallelSubtasks` 取模，得到起始索引 `startIndex`。
  **作用**：相同 Topic 的所有分区分配从同一起始点开始，不同 Topic 的起始点可能不同。

---

#### 6.3.2 轮询分配逻辑
```java
return (startIndex + partition.getPartition()) % numParallelSubtasks;
```
- **分区号叠加**：
  将 Kafka 分区的 ID（`partition.getPartition()`）作为偏移量，叠加到 `startIndex`。
- **环形分配**：
  通过取模操作实现环形分配，确保分区按顺时针方向依次分配给 Subtask。
  **示例**：
  - 若 `startIndex = 2`，`numParallelSubtasks = 4`：
    分区 0 → Subtask 2，分区 1 → Subtask 3，分区 2 → Subtask 0，分区 3 → Subtask 1。
