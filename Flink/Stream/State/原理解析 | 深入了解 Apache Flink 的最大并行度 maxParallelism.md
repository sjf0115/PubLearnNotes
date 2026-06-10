在 Flink 生产实践中，`maxParallelism` 是一个极其容易被忽视但后果严重的配置项。很多开发者在首次部署作业时没有显式设置它，等到需要扩缩容或从 Savepoint 恢复时才发现：**作业无法恢复、状态全部丢失**。这篇博文将从底层原理出发，系统讲解 maxParallelism 的本质、计算方式、对状态分布的影响，以及生产级最佳实践。

> 本文基于 Flink 1.13.6 版本源码。

## 1. 并行度 Parallelism

Flink 作业被划分为多个算子（Source、Map、Reduce、Sink 等），每个算子可以并行执行，由一个或多个并行子任务（SubTask）实例完成。子任务的数量就是该算子的 **并行度（Parallelism）**。

```
算子 A（parallelism = 3）
┌───────────┐  ┌───────────┐  ┌───────────┐
│ SubTask-0 │  │ SubTask-1 │  │ SubTask-2 │
└───────────┘  └───────────┘  └───────────┘
```

并行度是一个运行时概念，可以在作业每次提交时调整。但 Flink 的 Keyed State 在扩缩容时如何重新分配？这就需要引入 KeyGroup 和 maxParallelism。

## 2. 最大并行度 maxParallelism 的本质

**maxParallelism 的本质是 KeyGroup 的数量**。KeyGroup 是 Flink 中 Keyed State 重分布的最小原子单元。每个 Key 被映射到一个 KeyGroup，每个 SubTask 负责一段连续的 KeyGroup 范围。当并行度发生变化时，Flink 只需要重新分配 KeyGroup 到新的 SubTask 上，而不需要对单个 Key 进行重分配。例如，maxParallelism = 8，即 8 个 KeyGroup：
- 当前 parallelism = 2：
	- SubTask-0: KeyGroup [0, 1, 2, 3]
	- SubTask-1: KeyGroup [4, 5, 6, 7]
- 扩容到 parallelism = 4：
	- SubTask-0: KeyGroup [0, 1]
	- SubTask-1: KeyGroup [2, 3]
	- SubTask-2: KeyGroup [4, 5]
	- SubTask-3: KeyGroup [6, 7]

这就是为什么 **parallelism ≤ maxParallelism** 必须成立——如果并行度大于 KeyGroup 数量，就会有 SubTask 分不到任何 KeyGroup，无法处理任何 Keyed State。

## 3. Key → KeyGroup → SubTask：三层映射机制

理解 maxParallelism 的关键是理解 Flink 如何将一个 Key 路由到具体的 SubTask。这个过程分为三步：

### 3.1 第一步：Key → KeyGroup

首先对 Key 的 hashCode 进行二次 MurmurHash（打散分布），然后对 `maxParallelism` 取模，得到 KeyGroup 编号：
```java
public static int assignToKeyGroup(Object key, int maxParallelism) {
    return computeKeyGroupForKeyHash(key.hashCode(), maxParallelism);
}

public static int computeKeyGroupForKeyHash(int keyHash, int maxParallelism) {
    return MathUtils.murmurHash(keyHash) % maxParallelism;
}
```
> org.apache.flink.runtime.state.KeyGroupRangeAssignment

为什么要做二次 Hash？因为用户自定义 Key 的 `hashCode()` 分布可能不均匀（如连续整数），MurmurHash 可以将其打散到 [0, maxParallelism) 范围内实现均匀分布。

### 3.2 第二步：KeyGroup → SubTask（operatorIndex）

这是一个整数除法的均匀分配算法，将 `[0, maxParallelism)` 范围内的 KeyGroup 均匀分配到 `[0, parallelism)` 个 SubTask 上：
```java
public static int computeOperatorIndexForKeyGroup(int maxParallelism, int parallelism, int keyGroupId) {
    return keyGroupId * parallelism / maxParallelism;
}
```
> org.apache.flink.runtime.state.KeyGroupRangeAssignment

也可以直接使用 `assignKeyToParallelOperator` 完成第一步和第二步的处理逻辑，直接为指定的 Key 分配 SubTask：
```java
public static int assignKeyToParallelOperator(Object key, int maxParallelism, int parallelism) {
    return computeOperatorIndexForKeyGroup(maxParallelism, parallelism, assignToKeyGroup(key, maxParallelism));
}
```

### 3.3 第三步：计算每个 SubTask 负责的 KeyGroup 范围

每个 SubTask 负责的是一段 **连续的** KeyGroup 范围：
```java
public static KeyGroupRange computeKeyGroupRangeForOperatorIndex(int maxParallelism, int parallelism, int operatorIndex) {
    int start = ((operatorIndex * maxParallelism + parallelism - 1) / parallelism);
    int end = ((operatorIndex + 1) * maxParallelism - 1) / parallelism;
    return new KeyGroupRange(start, end);
}
```
> org.apache.flink.runtime.state.KeyGroupRangeAssignment

这种连续性是高效 State 重分布的基础——扩缩容时只需要在相邻 SubTask 之间转移边界 KeyGroup，而不需要全局 Shuffle。

### 3.4 完整映射示例

假设 `maxParallelism = 8`，`parallelism = 3`：

| KeyGroup | computeOperatorIndexForKeyGroup | SubTask |
|---|---|---|
| 0 | 0 * 3 / 8 = 0 | SubTask-0 |
| 1 | 1 * 3 / 8 = 0 | SubTask-0 |
| 2 | 2 * 3 / 8 = 0 | SubTask-0 |
| 3 | 3 * 3 / 8 = 1 | SubTask-1 |
| 4 | 4 * 3 / 8 = 1 | SubTask-1 |
| 5 | 5 * 3 / 8 = 1 | SubTask-1 |
| 6 | 6 * 3 / 8 = 2 | SubTask-2 |
| 7 | 7 * 3 / 8 = 2 | SubTask-2 |

结果：SubTask-0 负责 [0,2]，SubTask-1 负责 [3,5]，SubTask-2 负责 [6,7]。

如果扩容到 `parallelism = 4`：

| KeyGroup | computeOperatorIndexForKeyGroup | SubTask |
|---|---|---|
| 0 | 0 * 4 / 8 = 0 | SubTask-0 |
| 1 | 1 * 4 / 8 = 0 | SubTask-0 |
| 2 | 2 * 4 / 8 = 1 | SubTask-1 |
| 3 | 3 * 4 / 8 = 1 | SubTask-1 |
| 4 | 4 * 4 / 8 = 2 | SubTask-2 |
| 5 | 5 * 4 / 8 = 2 | SubTask-2 |
| 6 | 6 * 4 / 8 = 3 | SubTask-3 |
| 7 | 7 * 4 / 8 = 3 | SubTask-3 |

可以看到，原来 SubTask-0 的 KeyGroup [0,1,2] 中，[0,1] 留在新的 SubTask-0，[2] 转移给新的 SubTask-1。这就是 KeyGroup 机制实现平滑扩缩容的核心。

## 4. 默认 maxParallelism 的计算规则

算子的最大并行度 maxParallelism 可以通过如下代码所示进行设置：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setMaxParallelism(128);
```
> 算子的并行度则需要通过算子的 setParallelism(xxx) 方法进行设置

如果用户没有显式设置 maxParallelism，Flink 会根据算子的并行度自动计算：
```java
public static int computeDefaultMaxParallelism(int operatorParallelism) {
    checkParallelismPreconditions(operatorParallelism);
    return Math.min(
        Math.max(
            MathUtils.roundUpToPowerOfTwo(operatorParallelism + (operatorParallelism / 2)),
            DEFAULT_LOWER_BOUND_MAX_PARALLELISM  // 128
        ),
        UPPER_BOUND_MAX_PARALLELISM  // 32768
    );
}
```
> org.apache.flink.runtime.state.KeyGroupRangeAssignment

计算逻辑分三步：
- 取 `operatorParallelism * 1.5`（向下取整），然后向上取整到 2 的幂次
- 与下界 `DEFAULT_LOWER_BOUND_MAX_PARALLELISM` 128 相比，取 MAX，保证大于最小默认并发度
- 与上界 `UPPER_BOUND_MAX_PARALLELISM`（32768）相比，取 MIN，保证小于最大并发度

> 通过上述计算规则，我们可以看出 Flink 提供的默认最大并发度在 128 和 32768 之间。

以下是几个典型并行度对应的默认 maxParallelism：

| 算子并行度 | parallelism * 1.5 | roundUpToPowerOfTwo | 最终 maxParallelism |
|---|---|---|---|
| 1 | 1 | 2 | 128（下界） |
| 4 | 6 | 8 | 128（下界） |
| 64 | 96 | 128 | 128（下界） |
| 100 | 150 | 256 | 256 |
| 200 | 300 | 512 | 512 |
| 500 | 750 | 1024 | 1024 |
| 1000 | 1500 | 2048 | 2048 |
| 10000 | 15000 | 16384 | 16384 |
| 30000 | 45000 | 65536 | 32768（上界） |

> 为什么默认值要取 2 的幂次？因为 `MurmurHash(keyHash) % maxParallelism` 在 maxParallelism 为 2 的幂次时，分布均匀性最好（等价于位运算取低位），避免了某些 KeyGroup 比其他的多接收 Key 的偏斜问题。

## 5. maxParallelism 的合法范围

maxParallelism 的合法范围在 **0 < maxParallelism ≤ 32768** 区间：
```java
// KeyGroupRangeAssignment.java
public static final int UPPER_BOUND_MAX_PARALLELISM = 32768; // 2^15

// StreamExecutionEnvironment.java
public StreamExecutionEnvironment setMaxParallelism(int maxParallelism) {
    Preconditions.checkArgument(
        maxParallelism > 0 && maxParallelism <= KeyGroupRangeAssignment.UPPER_BOUND_MAX_PARALLELISM,
        "maxParallelism is out of bounds 0 < maxParallelism <= " +
            KeyGroupRangeAssignment.UPPER_BOUND_MAX_PARALLELISM);
    config.setMaxParallelism(maxParallelism);
    return this;
}
```
上界为什么是 32768（2^15）？在 `computeKeyGroupRangeForOperatorIndex` 方法中的整数算术在 `maxParallelism > Short.MAX_VALUE + 1` 时可能溢出，因此限制在 32768。

## 6. 为什么 maxParallelism 一旦设定就不能修改

任何进入生产的作业都应该指定最大并发数。但是，一定要仔细考虑后再决定该值的大小。因为一旦设置了最大并发度（无论是手动设置，还是默认设置），之后就无法再对该值做更新。想要改变一个作业的最大并发度，就只能将作业从全新的状态重新开始执行。目前还无法在更改最大并发度后，从上一个 checkpoint 或 savepoint 恢复。这也是 maxParallelism 最关键的约束。理解原因需要回到 Key → KeyGroup 的映射公式：
```java
keyGroupId = MurmurHash(key.hashCode()) % maxParallelism
```

如果修改了 maxParallelism（比如从 128 改为 256），同一个 Key 的 KeyGroup 编号就会改变：
```
Key = "A"
  MurmurHash(hashCode) = 743412968

  maxParallelism = 128: keyGroupId = 1098257485 % 128 = 104
  maxParallelism = 256: keyGroupId = 1098257485 % 256 = 232
```

这意味着该 Key 对应的 State 在 Checkpoint/Savepoint 中保存在 KeyGroup-104 里，但恢复后系统去 KeyGroup-232 中找——自然找不到。**整个 Keyed State 的映射关系被打乱，无法正确恢复**。因此 Flink 在从 Checkpoint/Savepoint 恢复时，会校验 maxParallelism 是否与保存时一致，不一致则直接拒绝恢复。

> 最大并发度的取值建议设定一个足够高的值以满足应用未来的可扩展性和可用性，同时，又要选一个相对较低的值以避免影响应用程序整体的性能。这是由于一个很高的最大并发度会导致 Flink 需要维护大量的元数据（用于扩缩容），这可能会增加 Flink 应用程序的整体状态大小。

# 7. maxParallelism 与扩缩容

maxParallelism 决定了作业能够扩容的上限：`parallelism ≤ maxParallelism`。如果 `maxParallelism = 128`，那么作业最多只能扩到 128 个并行度。超过 128 时，部分 SubTask 分配不到 KeyGroup，无法工作。但这不意味着 maxParallelism 设得越大越好。过大的 maxParallelism 会带来以下代价：
- State 元数据开销
	- 每个 KeyGroup 在 Checkpoint 中都有独立的元数据条目。maxParallelism = 32768 意味着即使只有 10 个并行度，Checkpoint 中也要维护 32768 个 KeyGroup 的元数据信息，增加 Checkpoint 大小和恢复时间。
- RocksDB 的 Column Family 切分
	- 使用 RocksDB StateBackend 时，State 按 KeyGroup 粒度进行组织。过多的 KeyGroup 会导致 RocksDB 内部的数据结构（如 SST 文件的索引）更加碎片化。
- 扩缩容时的 State 迁移粒度
	- KeyGroup 越多，每个 KeyGroup 中的 Key 数量越少。扩缩容时虽然迁移的 KeyGroup 数量增多，但每个 KeyGroup 更小，总体迁移量不变。但过于细粒度的切分会增加恢复时打开和合并 State 文件的开销。

## 8. 生产级最佳实践

### 8.1 显式设置 maxParallelism

**任何进入生产的 Flink 作业都必须显式设置 maxParallelism**。原因：
- 如果依赖默认值，后续修改并行度可能导致默认 maxParallelism 发生变化，进而无法从 Savepoint 恢复
- 例如：初始 parallelism = 100 → 默认 maxParallelism = 256；后来改为 parallelism = 200 → 默认 maxParallelism = 512。此时无法从旧的 Savepoint 恢复

```java
// 推荐：在 Environment 级别统一设置
env.setMaxParallelism(512);

// 或者对特定算子设置
stream.keyBy(...)
    .process(new MyProcessFunction())
    .setMaxParallelism(512);
```

### 8.2 选择合适的值

| 考量维度 | 建议 |
|---|---|
| 预期最大扩容规模 | maxParallelism ≥ 未来可能的最大并行度 |
| 状态/元数据开销 | 不需要设太大，够用即可 |
| 均匀分布 | 建议取 2 的幂次（128、256、512、1024） |
| 通用推荐 | 对于大多数作业，**128 或 256** 是合理的起点 |

### 8.3 设置级别

maxParallelism 可以在三个级别设置，优先级从高到低：
```java
// 1. 算子级别（最高优先级）
operator.setMaxParallelism(256);

// 2. Environment 级别
env.setMaxParallelism(256);

// 3. Flink 配置文件（flink-conf.yaml）
// pipeline.max-parallelism: 256
```
建议在 Environment 级别统一设置，除非某个算子有特殊需求。

## 9. 总结

| 维度 | 要点 |
|---|---|
| 本质 | maxParallelism = KeyGroup 数量 = State 重分布的最小粒度 |
| 合法范围 | (0, 32768] |
| 默认计算 | roundUpToPowerOfTwo(parallelism * 1.5)，下界 128，上界 32768 |
| 不可变性 | 一旦设定（或使用默认值），后续无法修改，否则无法从 Savepoint 恢复 |
| 与并行度关系 | parallelism ≤ maxParallelism 必须成立 |
| 推荐值 | 128 或 256（对大多数作业），取 2 的幂次保证均匀分布 |
| 核心建议 | **生产作业必须显式设置 maxParallelism** |

一句话总结：**maxParallelism 决定了作业 State 的"分桶方式"，一旦确定就刻入了 Savepoint 的 DNA 中，永远无法修改。请在作业第一次上线前就想清楚这个值。**
