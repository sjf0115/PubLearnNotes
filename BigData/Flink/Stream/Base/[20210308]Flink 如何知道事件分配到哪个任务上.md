

## 1. maxParallelism

> 最大并行度

### 1.1 最大并行度的概念

maxParallelism 表示当前算子设置的最大并行度，而不是 Flink 任务的并行度。maxParallelism 为 KeyGroup 的个数。算子的最大并行度可以通过如下代码所示进行设置：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setMaxParallelism(128);
```
> 算子的并行度则需要通过算子的 setParallelism(xxx) 方法进行设置

当设置算子的并行度大于 maxParallelism 时，有些并行度就分配不到 KeyGroup，此时 Flink 任务是无法从 Checkpoint 处恢复的。

### 1.2 maxParallelism 到底是多少呢？

如果设置了，就是设定的值。当然设置了，也需要检测合法性。如下图所示，Flink 要求 maxParallelism 应该介于 1 到 Short.MAX_VALUE 之间，即：0 < maxParallelism < 32768：
```java
// UPPER_BOUND_MAX_PARALLELISM = 32768;
public StreamExecutionEnvironment setMaxParallelism(int maxParallelism) {
	Preconditions.checkArgument(maxParallelism > 0 &&
					maxParallelism <= KeyGroupRangeAssignment.UPPER_BOUND_MAX_PARALLELISM,
			"maxParallelism is out of bounds 0 < maxParallelism <= " +
					KeyGroupRangeAssignment.UPPER_BOUND_MAX_PARALLELISM + ". Found: " + maxParallelism);

	config.setMaxParallelism(maxParallelism);
	return this;
}
```
如果用户没有明确配置最大并行度，则 Flink 会自动通过 KeyGroupRangeAssignment 类的 computeDefaultMaxParallelism 方法计算得出，computeDefaultMaxParallelism 源码如下所示：
```java
public static int computeDefaultMaxParallelism(int operatorParallelism) {
    checkParallelismPreconditions(operatorParallelism);
    return Math.min(
      Math.max(
        MathUtils.roundUpToPowerOfTwo(operatorParallelism + (operatorParallelism / 2)),
        DEFAULT_LOWER_BOUND_MAX_PARALLELISM
      ),
      UPPER_BOUND_MAX_PARALLELISM
    );
}
```
根据算子并行度计算默认的最大并行度。计算规则如下：
- 将算子并行度 * 1.5 后，向上取整到 2 的 n 次幂
- 跟 DEFAULT_LOWER_BOUND_MAX_PARALLELISM（128）相比，取 MAX，保证大于最小默认并发度
- 跟 UPPER_BOUND_MAX_PARALLELISM（32768）相比，取 MIN，保证小于最大并发度

通过上述计算规则，我们可以看出 Flink 提供的默认最大并发度在 128 和 32768 之间。


### 1.3 明确定义 Flink 算子的最大并发度

Flink 的 keyed state 是由 key group 进行组织的，并分布在 Flink 算子（operator）的各个并发实例上。Key group 是用来分布和影响 Flink 应用程序可扩展性的最小原子单元，每个算子上的 key group 个数即为最大并发数（maxParallelism），可以手动配置也可以直接使用默认配置。默认值粗略地使用 operatorParallelism * 1.5 ，下限 128，上限 32768 。可以通过 setMaxParallelism(int maxParallelism) 来手动地设定作业或具体算子的最大并发。

任何进入生产的作业都应该指定最大并发数。但是，一定要仔细考虑后再决定该值的大小。因为一旦设置了最大并发度（无论是手动设置，还是默认设置），之后就无法再对该值做更新。想要改变一个作业的最大并发度，就只能将作业从全新的状态重新开始执行。目前还无法在更改最大并发度后，从上一个 checkpoint 或 savepoint 恢复。

最大并发度的取值建议设定一个足够高的值以满足应用未来的可扩展性和可用性，同时，又要选一个相对较低的值以避免影响应用程序整体的性能。这是由于一个很高的最大并发度会导致 Flink 需要维护大量的元数据（用于扩缩容），这可能会增加 Flink 应用程序的整体状态大小。

## 2. 每个 key 应该分配到哪个 subtask 上运行？



















...
