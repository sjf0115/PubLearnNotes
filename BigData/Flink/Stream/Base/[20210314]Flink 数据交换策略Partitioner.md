---
layout: post
author: smartsi
title: Flink 数据交换策略Partitioner
date: 2021-03-14 13:21:01
tags:
  - Flink

categories: Flink
permalink: physical-partitioning-in-apache-flink
---

- GlobalPartitioner
- ForwardPartitioner
- BroadcastPartitioner
- ShufflePartitioner
- RebalancePartitioner
- RescalePartitioner
- KeyGroupStreamPartitioner
- CustomPartitionerWrapper

物理分区操作的作用是根据指定的分区策略将数据重新分配到不同节点的 Task 实例上执行。当使用 DataStream 提供的 API 对数据处理过程中，依赖算子本身对数据的分区控制，如果用户希望自己控制数据分区，例如当数据发生数据倾斜的时候，就需要通过定义物理分区策略对数据进行重新分布处理。Flink 中已经提供了常见的分区策略，例如，随机分区(Random Partitioning)、平衡分区(Rebalancing Partitioning)、按比例分区(Rescaling Partitioning)等。

### 1. GlobalPartitioner

#### 1.1 作用

GlobalPartitioner 分区器会将上游所有元素都发送到下游的第一个算子实例上(SubTask Id = 0)，下图所示。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-1.png?raw=true)

#### 1.2 源码

我们可以看到 selectChannel 方法中始终返回 0，表示只发送给下游算子 SubTask Id = 0 的子任务上。
```java
@Internal
public class GlobalPartitioner<T> extends StreamPartitioner<T> {
    private static final long serialVersionUID = 1L;
    @Override
    public int selectChannel(SerializationDelegate<StreamRecord<T>> record) {
        // 返回0表示只发送给下游算子SubTask Id=0的子任务上
        return 0;
    }

    @Override
    public StreamPartitioner<T> copy() {
        return this;
    }

    @Override
    public SubtaskStateMapper getDownstreamSubtaskStateMapper() {
        return SubtaskStateMapper.FIRST;
    }

    @Override
    public String toString() {
        return "GLOBAL";
    }
}
```

#### 1.3 如何使用

如下所示，调用 global() 方法即可：
```java
DataStream<String> result = env.socketTextStream("localhost", 9100, "\n")
    .map(str -> str.toLowerCase()).name("LowerCaseMap").setParallelism(2)
    .global()
    .map(str -> str.toUpperCase()).name("UpperCaseMap").setParallelism(2);
```
> 完成代码请查阅:[GlobalPartitionerExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/partitioner/GlobalPartitionerExample.java)

我们可以看到 LowerCaseMap 和 UpperCaseMap 算子之间的 GLOBAL 标示，表示我们使用的 GlobalPartitioner：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-2.png?raw=true)

如下所示，LowerCaseMap 算子两个子任务分别接受到3个元素，经过处理之后均发送到 UpperCaseMap 算子的第一个子任务上：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-3.png?raw=true)

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-4.png?raw=true)

### 2. ForwardPartitioner

#### 2.1 作用

仅将元素转发到本地运行的下游算子。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-5.png?raw=true)

#### 2.2 源码

```java
@Internal
public class ForwardPartitioner<T> extends StreamPartitioner<T> {
	private static final long serialVersionUID = 1L;

	@Override
	public int selectChannel(SerializationDelegate<StreamRecord<T>> record) {
		return 0;
	}

	public StreamPartitioner<T> copy() {
		return this;
	}

	@Override
	public String toString() {
		return "FORWARD";
	}

	@Override
	public SubtaskStateMapper getDownstreamSubtaskStateMapper() {
		return SubtaskStateMapper.ROUND_ROBIN;
	}
}
```

#### 2.3 如何使用

如下所示，调用 forward() 方法即可：
```java
// ForwardPartitioner
DataStream<String> result = env.socketTextStream("localhost", 9100, "\n")
        .map(str -> str.toLowerCase()).name("LowerCaseMap").setParallelism(3)
        .forward()
        .map(str -> str.toUpperCase()).name("UpperCaseMap").setParallelism(3).disableChaining();
```
> 完成代码请查阅:[ForwardPartitionerExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/partitioner/ForwardPartitionerExample.java)

我们可以看到 LowerCaseMap 和 UpperCaseMap 算子之间的 FORWARD 标示，表示我们使用的 ForwardPartitioner：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-6.png?raw=true)

> 在代码中特意使用了 disableChaining() 方法，目的是不让 LowerCaseMap 和 UpperCaseMap 算子 Chain 一起，更好的观察两个算子之间的分区方式。

在没有指定 Partitioner 时，如果上下游算子的并行度相同，默认就会采用 ForwardPartitioner，否则会采用下面要讲解的的 RebalancePartitioner：
```java
// If no partitioner was specified and the parallelism of upstream and downstream
// operator matches use forward partitioning, use rebalance otherwise.
if (partitioner == null
        && upstreamNode.getParallelism() == downstreamNode.getParallelism()) {
    partitioner = new ForwardPartitioner<Object>();
} else if (partitioner == null) {
    partitioner = new RebalancePartitioner<Object>();
}
```
需要注意的是在使用 ForwardPartitioner 时，必须保证上下游算子的并行度一致，否则就会抛出如下异常：
```java
if (partitioner instanceof ForwardPartitioner) {
    if (upstreamNode.getParallelism() != downstreamNode.getParallelism()) {
        throw new UnsupportedOperationException(
                "Forward partitioning does not allow "
                        + "change of parallelism. Upstream operation: "
                        + upstreamNode
                        + " parallelism: "
                        + upstreamNode.getParallelism()
                        + ", downstream operation: "
                        + downstreamNode
                        + " parallelism: "
                        + downstreamNode.getParallelism()
                        + " You must use another partitioning strategy, such as broadcast, rebalance, shuffle or global.");
    }
}
```

### 3. BroadcastPartitioner

#### 3.1 作用

上游算子实例广播发送到下游所有的算子实例上：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-7.png?raw=true)

#### 3.2 源码

BroadcastPartitioner 策略是直接发送到下游的所有 Task 上，所以不需要通过下面的 selectChannel 方法选择发送的通道：
```java
@Internal
public class BroadcastPartitioner<T> extends StreamPartitioner<T> {
	private static final long serialVersionUID = 1L;

	/**
	 * Note: Broadcast mode could be handled directly for all the output channels
	 * in record writer, so it is no need to select channels via this method.
	 */
	@Override
	public int selectChannel(SerializationDelegate<StreamRecord<T>> record) {
		throw new UnsupportedOperationException("Broadcast partitioner does not support select channels.");
	}

	@Override
	public SubtaskStateMapper getUpstreamSubtaskStateMapper() {
		return SubtaskStateMapper.DISCARD_EXTRA_STATE;
	}

	@Override
	public SubtaskStateMapper getDownstreamSubtaskStateMapper() {
		return SubtaskStateMapper.ROUND_ROBIN;
	}

	@Override
	public boolean isBroadcast() {
		return true;
	}

	@Override
	public StreamPartitioner<T> copy() {
		return this;
	}

	@Override
	public String toString() {
		return "BROADCAST";
	}
}
```

#### 3.3 如何使用

如下所示，调用 broadcast() 方法即可：
```java
DataStream<String> result = env.socketTextStream("localhost", 9100, "\n")
  .map(str -> str.toLowerCase()).name("LowerCaseMap").setParallelism(2)
  .broadcast()
  .map(str -> str.toUpperCase()).name("UpperCaseMap").setParallelism(2);
```
> 完成代码请查阅:[BroadcastPartitionerExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/partitioner/BroadcastPartitionerExample.java)

我们可以看到 LowerCaseMap 和 UpperCaseMap 算子之间的 BROADCAST 标示，表示我们使用的 BroadcastPartitioner：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-8.png?raw=true)

### 4. ShufflePartitioner

#### 4.1 作用

上游算子实例随机选择一个下游算子实例进行发送：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-9.png?raw=true)

#### 4.2 源码

ShufflePartitioner 使用 java.util.Random 随机函数将数据随机输出到下游算子的一个实例。由于 Random 生成的随机数符合均匀分布，所以可以认为是输出均匀分布：
```java
@Internal
public class ShufflePartitioner<T> extends StreamPartitioner<T> {
	private static final long serialVersionUID = 1L;

	private Random random = new Random();

	@Override
	public int selectChannel(SerializationDelegate<StreamRecord<T>> record) {
		return random.nextInt(numberOfChannels);
	}

	@Override
	public SubtaskStateMapper getDownstreamSubtaskStateMapper() {
		return SubtaskStateMapper.ROUND_ROBIN;
	}

	@Override
	public StreamPartitioner<T> copy() {
		return new ShufflePartitioner<T>();
	}

	@Override
	public String toString() {
		return "SHUFFLE";
	}
}
```

#### 4.3 如何使用

如下所示，调用 shuffle() 方法即可：
```java
DataStream<String> result = env.socketTextStream("localhost", 9100, "\n")
  .map(str -> str.toLowerCase()).name("LowerCaseMap").setParallelism(2)
  .shuffle()
  .map(str -> str.toUpperCase()).name("UpperCaseMap").setParallelism(2);
```
> 完成代码请查阅:[ShufflePartitionerExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/partitioner/ShufflePartitionerExample.java)

我们可以看到 LowerCaseMap 和 UpperCaseMap 算子之间的 SHUFFLE 标示，表示我们使用的 ShufflePartitioner：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-10.png?raw=true)

### 5. RebalancePartitioner

#### 5.1 作用

RebalancePartitioner 会先利用随机数生成函数 ThreadLocalRandom.current().nextInt 随机选择一个第一个要发送的下游算子实例。然后用轮询（round-robin）的方式从该实例开始循环输出。该方式能保证下游的负载均衡，所以常用来处理有倾斜的数据流：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-11.png?raw=true)

#### 5.2 源码

在 setup 方法中初始化第一个发送的 channel id，返回 [0,numberOfChannels) 一个随机数。确定第一个要发送的下游算子实例之后，循环依次发送到下游的 Task，比如：nextChannelToSendTo 初始值为0，numberOfChannels(下游算子的实例个数，并行度)值为 2，那么第一次发送到 ID = 1 的 Task，第二次发送到 ID = 0 的 Task，第三次发送到 ID = 1 的 Task上，依次类推：
```java
@Internal
public class RebalancePartitioner<T> extends StreamPartitioner<T> {
	private static final long serialVersionUID = 1L;

	private int nextChannelToSendTo;

	@Override
	public void setup(int numberOfChannels) {
		super.setup(numberOfChannels);

		nextChannelToSendTo = ThreadLocalRandom.current().nextInt(numberOfChannels);
	}

	@Override
	public int selectChannel(SerializationDelegate<StreamRecord<T>> record) {
		nextChannelToSendTo = (nextChannelToSendTo + 1) % numberOfChannels;
		return nextChannelToSendTo;
	}

	@Override
	public SubtaskStateMapper getDownstreamSubtaskStateMapper() {
		return SubtaskStateMapper.ROUND_ROBIN;
	}

	public StreamPartitioner<T> copy() {
		return this;
	}

	@Override
	public String toString() {
		return "REBALANCE";
	}
}
```
#### 5.3 如何使用

如下所示，调用 rebalance() 方法即可：
```java
DataStream<String> result = env.socketTextStream("localhost", 9100, "\n")
    .map(str -> str.toLowerCase()).name("LowerCaseMap").setParallelism(1)
    .rebalance()
    .map(str -> str.toUpperCase()).name("UpperCaseMap").setParallelism(2);
```
> 完成代码请查阅:[RebalancePartitionerExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/partitioner/RebalancePartitionerExample.java)

我们可以看到 LowerCaseMap 和 UpperCaseMap 算子之间的 REBALANCE 标示，表示我们使用的 RebalancePartitioner：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-12.png?raw=true)

### 6. RescalePartitioner

#### 6.1 作用

基于上下游算子的并行度，将元素循环的分配到下游算子的某几个实例上。如果想使上游算子的每个并行实例均匀分散到下游算子的某几个实例来达到负载均衡，但又不希望使用 rebalance 这种方式达到整体的负载均衡，那么 Rescale 这种方式很有用。这种方式仅需要本地数据传输，不需要通过网络传输数据，具体取决于我们的配置，例如，TaskManager的 Slot 数。

上游算子实例具体发送到哪几个下游算子实例，取决于上游算子和下游算子两者的并行度。例如，如果上游算子并行度为 2，而下游算子并行度为 4，那么其中一个上游算子实例将元素发送到其中两个下游算子实例，而另一个上游算子实例则发送到另外两个下游算子实例。相反，如果下游算子并行度为 2，而上游算子并行度为 4，那么两个上游算子实例将发送到其中一个下游算子实例，而其他两个上游算子则发送到另一个下游算子实例：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-13.png?raw=true)

RebalancePartitioner 和 RescalePartitioner 有什么不同呢？我们还是以上游算子并行度为 2，而下游算子并行度为 4 为例，当使用 RebalancePartitioner时，上游每个实例会轮询发给下游的 4 个实例。但是当使用 RescalePartitioner 时，上游每个实例只需轮询发给下游 2 个实例。因为 Channel 个数变少了，Subpartition 的 Buffer 填充速度能变快，能提高网络效率。当上游的数据比较均匀时，且上下游的并发数成比例时，可以使用 RescalePartitioner 替换 RebalancePartitioner。

#### 6.2 源码

初始化 channel 为 -1，循环依次发送到下游的 SubTask：
```java
@Internal
public class RescalePartitioner<T> extends StreamPartitioner<T> {
	private static final long serialVersionUID = 1L;

	private int nextChannelToSendTo = -1;

	@Override
	public int selectChannel(SerializationDelegate<StreamRecord<T>> record) {
		if (++nextChannelToSendTo >= numberOfChannels) {
			nextChannelToSendTo = 0;
		}
		return nextChannelToSendTo;
	}

	@Override
	public SubtaskStateMapper getDownstreamSubtaskStateMapper() {
		return SubtaskStateMapper.ROUND_ROBIN;
	}

	public StreamPartitioner<T> copy() {
		return this;
	}

	@Override
	public String toString() {
		return "RESCALE";
	}
}
```

#### 6.3 如何使用

如下所示，调用 rescale() 方法即可：
```java
DataStream<String> result = env.socketTextStream("localhost", 9100, "\n")
  .map(str -> str.toLowerCase()).name("LowerCaseMap").setParallelism(1)
  .rescale()
  .map(str -> str.toUpperCase()).name("UpperCaseMap").setParallelism(2);
```
> 完成代码请查阅:[RescalePartitionerExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/partitioner/RescalePartitionerExample.java)

我们可以看到 LowerCaseMap 和 UpperCaseMap 算子之间的 RESCALE 标示，表示我们使用的 RescalePartitioner：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-14.png?raw=true)

### 7. KeyGroupStreamPartitioner

#### 7.1 作用

使用 keyBy 函数指定分组 key 发送到相对应的下游实例上：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-15.png?raw=true)

#### 7.2 源码

具体输出到下游算子哪个实例上，取决于 KeyGroupRangeAssignment.assignKeyToParallelOperator 方法：
```java
@Internal
public class KeyGroupStreamPartitioner<T, K> extends StreamPartitioner<T> implements ConfigurableStreamPartitioner {
	private static final long serialVersionUID = 1L;

	private final KeySelector<T, K> keySelector;

	private int maxParallelism;

	public KeyGroupStreamPartitioner(KeySelector<T, K> keySelector, int maxParallelism) {
		Preconditions.checkArgument(maxParallelism > 0, "Number of key-groups must be > 0!");
		this.keySelector = Preconditions.checkNotNull(keySelector);
		this.maxParallelism = maxParallelism;
	}

	public int getMaxParallelism() {
		return maxParallelism;
	}

	@Override
	public int selectChannel(SerializationDelegate<StreamRecord<T>> record) {
		K key;
		try {
			key = keySelector.getKey(record.getInstance().getValue());
		} catch (Exception e) {
			throw new RuntimeException("Could not extract key from " + record.getInstance().getValue(), e);
		}
		return KeyGroupRangeAssignment.assignKeyToParallelOperator(key, maxParallelism, numberOfChannels);
	}

	@Override
	public SubtaskStateMapper getDownstreamSubtaskStateMapper() {
		return SubtaskStateMapper.RANGE;
	}

	@Override
	public StreamPartitioner<T> copy() {
		return this;
	}

	@Override
	public String toString() {
		return "HASH";
	}

	@Override
	public void configure(int maxParallelism) {
		KeyGroupRangeAssignment.checkParallelismPreconditions(maxParallelism);
		this.maxParallelism = maxParallelism;
	}

	@Override
	public boolean equals(Object o) {
		if (this == o) {
			return true;
		}
		if (o == null || getClass() != o.getClass()) {
			return false;
		}
		if (!super.equals(o)) {
			return false;
		}
		final KeyGroupStreamPartitioner<?, ?> that = (KeyGroupStreamPartitioner<?, ?>) o;
		return maxParallelism == that.maxParallelism &&
			keySelector.equals(that.keySelector);
	}

	@Override
	public int hashCode() {
		return Objects.hash(super.hashCode(), keySelector, maxParallelism);
	}
}
```
我们具体看看如何根据输入的 Key 判断输出到哪个算子实例上：
```java
public static int assignKeyToParallelOperator(Object key, int maxParallelism, int parallelism) {
	Preconditions.checkNotNull(key, "Assigned key must not be null!");
	return computeOperatorIndexForKeyGroup(maxParallelism, parallelism, assignToKeyGroup(key, maxParallelism));
}

public static int assignToKeyGroup(Object key, int maxParallelism) {
	Preconditions.checkNotNull(key, "Assigned key must not be null!");
	return computeKeyGroupForKeyHash(key.hashCode(), maxParallelism);
}

public static int computeKeyGroupForKeyHash(int keyHash, int maxParallelism) {
	return MathUtils.murmurHash(keyHash) % maxParallelism;
}

public static int computeOperatorIndexForKeyGroup(int maxParallelism, int parallelism, int keyGroupId) {
	return keyGroupId * parallelism / maxParallelism;
}
```
通过上面代码，我们知道需要在 key 上进行两重哈希得到 key 对应的哈希值，第一重是 Java 自带的 hashCode()，第二重则是 MurmurHash。然后将哈希值对 最大并行度 取模，在乘以算子并行度，并除以最大并行度，得到最终的算子实例Id：
```java
SubTaskId = (MathUtils.murmurHash(key.hashCode()) % maxParallelism) * parallelism / maxParallelism
```

#### 7.3 如何使用

如下所示，调用 keyBy 方法指定分区 Key 即可：
```java
DataStream<String> result = env.socketTextStream("localhost", 9100, "\n")
  .map(str -> str.toLowerCase()).name("LowerCaseMap").setParallelism(2)
  .keyBy(str -> str)
  .map(str -> str.toUpperCase()).name("UpperCaseMap").setParallelism(2);
```
> 完成代码请查阅:[KeyGroupStreamPartitionerExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/partitioner/KeyGroupStreamPartitionerExample.java)

我们可以看到 LowerCaseMap 和 UpperCaseMap 算子之间的 HASH 标示，表示我们使用的 KeyGroupStreamPartitioner：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/physical-partitioning-in-apache-flink-16.png?raw=true)

### 8. CustomPartitionerWrapper
