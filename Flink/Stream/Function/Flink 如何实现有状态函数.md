
在状态管理中介绍到状态可分为 KeyedState 和 OperateState 两类，Flink 提供多种接口来定义状态函数。

## 1. KeyedState 函数

Keyed State 总是与 key 相对应，即每个 Key 对应一个 State，并且只能在 KeyedStream 上的函数和算子中使用。KeyedStream 可以通过调用 DataStream.keyBy() 来获得。每个 KeyedState 在逻辑上唯一对应一个 `<并行算子实例，key>`，由于每个 key '只属于' 一个 KeyedOperator 的一个并行实例，我们可以简单地认为成 `<operator，key>`。

KeyedState 类似分布式 KV 存储，每个函数实例负责维护状态的一部分。KeyedState 只用于处理 KeyedStream 上的函数，Flink 提供如下 KeyedState 原语：
- ValueState<T>：维护单个值的状态，通过ValueState.value()和ValueState.update(T value)分别获取、更新状态。
- ListState<T>：以链表形式维护多个值的状态，通过ListState.add(T value)、ListState.addAll(List<T> values)添加值，通过ListState.get()获取到所有值的迭代器Iterable<T>，通过ListState.update(List<T> values)更新状态。
- MapState<K, V>：以map形式维护多个值的状态，提供get(K key)、put(K key, V value)、contains(K key)、 remove(K key)方法获取更新值。
- ReducingState<T>：和ListState类似，但没有addAll()和update()方法，通过ReduceFunction计算得到一个聚合结果value，通过get()方法返回只含有value的Iterable。
- AggregatingState<I, O>：和ReducingState类似，使用AggregateFunction计算得到一个结果value，通过get()方法返回只含有value的Iterable。
所有的状态原语通过State.clear()方法清空内容。代码TemperatureAlert.java演示如何使用状态保存上一个温度，并在温度差大于指定值时发出报警。

通过 StateDescriptor 对象获取状态句柄 xxxState，描述符包含状态名称和状态数据类型(Class或者TypeInformation)。状态数据类型必须指定，因为 Flink需要创建合适的序列化器。

通常状态句柄在 RichFunction 的 open() 方法中创建，它仅是状态句柄并不包含状态自身。当函数注册StateDescriptor后，Flink会从状态后端查找是否存在相同名称和类型的状态，如果有的话将状态句柄指向状态，否则返回空。



在访问上，Keyed State 通过 RuntimeContext 来访问，这需要算子是一个 Rich Function。首先我们必须创建状态描述符 StateDescriptor，包含了状态的名字（可以创建多个状态，必须有唯一的名称，以便引用它们），状态值的类型。根据需求我们可以创建一个 ValueStateDescriptor，ListStateDescriptor，ReducingStateDescriptor 或 MapStateDescriptor，下面我们创建一个 ValueStateDescriptor：


## 2. 实现 OperateState 函数

### 2.1 ListCheckpointed 实现

```java
public interface ListCheckpointed<T extends Serializable> {
  // 返回状态快照
  List<T> snapshotState(long checkpointId, long timestamp) throws Exception;
  // 恢复状态
  void restoreState(List<T> state) throws Exception;
}
```

### 2.2 CheckpointedFunction

```java

```





https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/dev/datastream/fault-tolerance/state/#using-operator-state


## 1. CheckpointListener

CheckpointListener 接口是一个监听接口，以便当 Checkpoint 完成时通知 Function 进行一些必要的处理。CheckpointListener 接口通常仅用于与'外部世界'的事务性交互。一个例子是一旦检查点完成就提交外部事务。CheckpointListener 接口不会保证每个实现都能收到检查点已完成或中止的通知。虽然在大多数情况下都会通知，但有时候可能不会通知，例如，在检查点完成后直接发生故障/恢复时。

来自这个接口的通知都是'事后'的，即在检查点被中止或完成之后才会通知。抛出异常不会改变检查点的完成/中止。此方法抛出的异常会导致任务或作业失败以及恢复。

Checkpoint 包含合约

检查点 ID 是严格递增的。具有较高 ID 的检查点始终包含具有较低 ID 的检查点。例如，当检查点 T 被确认完成时，可以认为具有较低 ID（T-1、T-2 等）的检查点不用在处理了。在具有较高 ID 的检查点完成之后，不会再提交具有较低 ID 的检查点。但这并不一定意味着之前的所有检查点实际上都已成功完成。也有可能某些检查点超时或者没有被所有任务完全确认，可以当这些检查点没有发生一样。推荐的方法是让新检查点（较高 ID）的完成包含所有较早检查点（较低 ID）的完成。

这种属性对于完成增加 Offset、Watermark 以及其他在 Checkpoint 完成时传达进度指示器的情况非常有用。较新的检查点将比前一个检查点具有更高的 Offset（更多进度），因此它会自动包含前一个检查点。

```java
public interface CheckpointListener {
    void notifyCheckpointComplete(long checkpointId) throws Exception;
    default void notifyCheckpointAborted(long checkpointId) throws Exception {}
}
```

### 1.1 notifyCheckpointComplete

通知监听器指定 checkpointId 的检查点已完成并已提交。请注意，检查点通常可能会重叠，因此我们不能假设 notifyCheckpointComplete() 调用始终针对最新的检查点(实现此接口的函数/算子)。有可能是针对较早触发的检查点。如果此方法抛出异常不会撤销已完成的检查点。抛出异常只会导致任务/作业失败并触发恢复。

### 1.2 notifyCheckpointAborted

一旦检查点被中止，此方法将作为通知被调用。检查点被中止并不意味着前一个检查点和中止的检查点之间产生的数据会被丢弃。我们可以认为这个检查点从来没有被触发过，下一个成功的检查点会覆盖更长的时间跨度。这种方法很少需要我们实现。'尽力而为'的保证以及此方法不会导致丢弃任何数据意味着它主要用于辅助资源的早期清理。一个例子是在检查点失败时主动清除本地每个检查点的状态缓存。

## 2. CheckpointedFunction

这是有状态转换函数的核心接口，这意味着维护状态的函数可以跨多个流记录进行处理。虽然存在更轻量级的接口，但该接口在管理 Keyed State 和 Operator State 能提供最大的灵活性。


OperatorStateStore 和 KeyedStateStore提供了对数据结构的访问，Flink应该在其中存储状态，以便透明地管理和检查它，例如org.apache.flink.api.common.state.ValueState或org.apache.flink.api.common.state.ListState。
注意:KeyedStateStore只能在转换支持键控状态时使用，也就是说，当它应用在键控流上时(在keyBy(…)之后)。


```java
public interface CheckpointedFunction {
    void snapshotState(FunctionSnapshotContext context) throws Exception;
    void initializeState(FunctionInitializationContext context) throws Exception;
}
```

### 2.1 initializeState

在分布式执行期间，当创建转换函数的并行实例时，将会调用 `initializeState(FunctionInitializationContext)` 方法。该方法提供了访问 FunctionInitializationContext 的能力，而 FunctionInitializationContext 又提供了访问 OperatorStateStore 和 KeyedStateStore 的能力：
```java
public interface FunctionInitializationContext extends ManagedInitializationContext {
}

public interface ManagedInitializationContext {
    boolean isRestored();
    OperatorStateStore getOperatorStateStore();
    KeyedStateStore getKeyedStateStore();
}
```
通过 `isRestored()` 可以判断状态是否是从上一次执行的快照中恢复，如果是返回 true。需要注意的是对于无状态任务，该方法总是返回 false。通过 `getOperatorStateStore()` 方法获取允许注册算子状态 OpeartorState 的 OperatorStateStore。通过 `getKeyedStateStore()` 方法获取允许注册键值状态 KeyedState 的 KeyedStateStore。

OperatorStateStore 和 KeyedStateStore 则又提供了访问状态 State 存储数据结构的能力，例如 `org.apache.flink.api.common.state.ValueState` 或者 `org.apache.flink.api.common.state.ListState`：
```java
public void initializeState(FunctionInitializationContext context) throws Exception {
    // 获取 ListState
    ListStateDescriptor<String> descriptor = new ListStateDescriptor<>(
        "buffered-elements", TypeInformation.of(new TypeHint<String>() {})
    );
    statePerPartition = context.getOperatorStateStore().getListState(descriptor);
    // 判断是否是从快照中恢复
    if (context.isRestored()) {
        // 恢复时执行逻辑
        for (String element : statePerPartition.get()) {
            bufferedElements.add(element);
        }
    } else {
        // 首次运行时执行逻辑
    }
}
```

### 2.2 snapshotState

每当触发 Checkpoint 生成转换函数的状态快照时就会调用 `snapshotState(FunctionSnapshotContext)` 方法。该方法提供了访问 FunctionSnapshotContext 的能力，而 FunctionSnapshotContext 又提供了访问检查点元数据的能力：
```java
public interface FunctionSnapshotContext extends ManagedSnapshotContext {}

public interface ManagedSnapshotContext {
    long getCheckpointId();
    long getCheckpointTimestamp();
}
```
通过 `getCheckpointId()` 方法获取生成快照时的检查点 ID，检查点 ID 保证了检查点之间的严格单调递增。对于完成的两个检查点 A 和 B, `ID_B > ID_A` 表示检查点 B 包含检查点 A，即检查点 B 包含的状态晚于检查点 A。通过 `getCheckpointTimestamp()` 方法返回主节点触发检查点生成快照时的时间戳。

在 `snapshotState` 方法中，一般需要确保检查点数据结构（在 initialization 方法中获取）是最新的，以便生成快照。此外，函数可以作为一个 hook 与外部系统交互实现刷新/提交/同步。如下所示，通过 FunctionSnapshotContext 上下文获取检查点元数据信息，并将最新数据存储在状态中生成快照：
```java
public void snapshotState(FunctionSnapshotContext context) throws Exception {
    long checkpointId = context.getCheckpointId();
    long checkpointTimestamp = context.getCheckpointTimestamp();
    int subTask = getRuntimeContext().getIndexOfThisSubtask();
    statePerPartition.clear();
    for (String element : bufferedElements) {
        LOG.info("snapshotState subTask: {}, checkpointId: {}, checkpointTimestamp: {}, element: {}",
                subTask, checkpointId, checkpointTimestamp, element);
        statePerPartition.add(element);
    }
}
```

### 2.3 简写

transformation 函数可以在不实现完整 CheckpointedFunction 接口的情况下与 State 进行交互。这也是实现 CheckpointedFunction 接口的快捷方式。

#### 2.3.1 Operator 状态

通过直接实现 ListCheckpointed 接口，可以以更简单的方式检查属于函数对象本身的某些状态。

#### 2.3.2 Keyed 状态

可以通过 RuntimeContext 方法访问 keyed 状态：
```java
public class CountPerKeyFunction<T> extends RichMapFunction<T, T> {
    private ValueState<Long> count;

    public void open(Configuration cfg) throws Exception {
    count = getRuntimeContext().getState(new ValueStateDescriptor<>("myCount", Long.class));
    }

    public T map(T value) throws Exception {
    Long current = count.value();
    count.update(current == null ? 1L : current + 1);

    return value;
    }
}
```

```
21:41:45,521 INFO   [] - word: a1
21:41:45,522 INFO   [] - buffer subTask: 1, element: a1, size: 1
21:41:46,768 INFO   [] - word: a2
21:41:46,768 INFO   [] - buffer subTask: 0, element: a2, size: 1
21:41:51,342 INFO   [] - Triggering checkpoint 1 (type=CHECKPOINT) @ 1681652511327 for job 6366a2b06387c6c734db67e1124c3395.
21:41:51,349 INFO   [] - snapshotState subTask: 0, checkpointId: 1, checkpointTimestamp: 1681652511327, element: a2
21:41:51,349 INFO   [] - snapshotState subTask: 1, checkpointId: 1, checkpointTimestamp: 1681652511327, element: a1
21:41:51,376 INFO   [] - Completed checkpoint 1 for job 6366a2b06387c6c734db67e1124c3395 (412 bytes in 46 ms).
21:41:51,749 INFO   [] - word: a3
21:41:51,750 INFO   [] - buffer subTask: 1, element: a3, size: 2
21:41:53,087 INFO   [] - word: a4
21:41:53,087 INFO   [] - buffer subTask: 0, element: a4, size: 2
21:41:54,437 INFO   [] - word: a5
21:41:54,437 INFO   [] - buffer subTask: 1, element: a5, size: 3
21:42:05,305 INFO   [] - word: a6
21:42:05,306 INFO   [] - buffer subTask: 0, element: a6, size: 3
21:42:06,970 INFO   [] - word: a7
21:42:06,970 INFO   [] - buffer subTask: 1, element: a7, size: 4
21:42:21,325 INFO   [] - Triggering checkpoint 2 (type=CHECKPOINT) @ 1681652541324 for job 6366a2b06387c6c734db67e1124c3395.
21:42:21,327 INFO   [] - snapshotState subTask: 0, checkpointId: 2, checkpointTimestamp: 1681652541324, element: a2
21:42:21,327 INFO   [] - snapshotState subTask: 1, checkpointId: 2, checkpointTimestamp: 1681652541324, element: a1
21:42:21,327 INFO   [] - snapshotState subTask: 0, checkpointId: 2, checkpointTimestamp: 1681652541324, element: a4
21:42:21,327 INFO   [] - snapshotState subTask: 1, checkpointId: 2, checkpointTimestamp: 1681652541324, element: a3
21:42:21,327 INFO   [] - snapshotState subTask: 0, checkpointId: 2, checkpointTimestamp: 1681652541324, element: a6
21:42:21,327 INFO   [] - snapshotState subTask: 1, checkpointId: 2, checkpointTimestamp: 1681652541324, element: a5
21:42:21,328 INFO   [] - snapshotState subTask: 1, checkpointId: 2, checkpointTimestamp: 1681652541324, element: a7
21:42:21,332 INFO   [] - Completed checkpoint 2 for job 6366a2b06387c6c734db67e1124c3395 (427 bytes in 6 ms).
21:42:46,798 INFO   [] - word: a8
21:42:46,799 INFO   [] - buffer subTask: 0, element: a8, size: 4
21:42:51,327 INFO   [] - Triggering checkpoint 3 (type=CHECKPOINT) @ 1681652571326 for job 6366a2b06387c6c734db67e1124c3395.
21:42:51,328 INFO   [] - snapshotState subTask: 0, checkpointId: 3, checkpointTimestamp: 1681652571326, element: a2
21:42:51,329 INFO   [] - snapshotState subTask: 1, checkpointId: 3, checkpointTimestamp: 1681652571326, element: a1
21:42:51,329 INFO   [] - snapshotState subTask: 0, checkpointId: 3, checkpointTimestamp: 1681652571326, element: a4
21:42:51,329 INFO   [] - snapshotState subTask: 1, checkpointId: 3, checkpointTimestamp: 1681652571326, element: a3
21:42:51,329 INFO   [] - snapshotState subTask: 0, checkpointId: 3, checkpointTimestamp: 1681652571326, element: a6
21:42:51,329 INFO   [] - snapshotState subTask: 1, checkpointId: 3, checkpointTimestamp: 1681652571326, element: a5
21:42:51,329 INFO   [] - snapshotState subTask: 0, checkpointId: 3, checkpointTimestamp: 1681652571326, element: a8
21:42:51,329 INFO   [] - snapshotState subTask: 1, checkpointId: 3, checkpointTimestamp: 1681652571326, element: a7
21:42:51,331 INFO   [] - Completed checkpoint 3 for job 6366a2b06387c6c734db67e1124c3395 (430 bytes in 5 ms).
21:42:57,645 INFO   [] - word: a9
21:42:57,645 INFO   [] - buffer subTask: 1, element: a9, size: 5
21:42:57,645 INFO   [] - buffer sink subTask: 1, element: a1
21:42:57,646 INFO   [] - buffer sink subTask: 1, element: a3
21:42:57,646 INFO   [] - buffer sink subTask: 1, element: a5
21:42:57,646 INFO   [] - buffer sink subTask: 1, element: a7
21:42:57,646 INFO   [] - buffer sink subTask: 1, element: a9
21:43:10,425 INFO   [] - word: a10
21:43:10,425 INFO   [] - buffer subTask: 0, element: a10, size: 5
21:43:10,426 INFO   [] - buffer sink subTask: 0, element: a2
21:43:10,426 INFO   [] - buffer sink subTask: 0, element: a4
21:43:10,426 INFO   [] - buffer sink subTask: 0, element: a6
21:43:10,426 INFO   [] - buffer sink subTask: 0, element: a8
21:43:10,426 INFO   [] - buffer sink subTask: 0, element: a10
21:43:18,810 INFO   [] - word: a11
21:43:18,810 INFO   [] - buffer subTask: 1, element: a11, size: 1
21:43:21,327 INFO   [] - Triggering checkpoint 4 (type=CHECKPOINT) @ 1681652601326 for job 6366a2b06387c6c734db67e1124c3395.
21:43:21,329 INFO   [] - snapshotState subTask: 1, checkpointId: 4, checkpointTimestamp: 1681652601326, element: a11
21:43:21,331 INFO   [] - Completed checkpoint 4 for job 6366a2b06387c6c734db67e1124c3395 (410 bytes in 4 ms).
21:43:30,850 INFO   [] - word: a12
21:43:30,850 INFO   [] - buffer subTask: 0, element: a12, size: 1
21:43:51,328 INFO   [] - Triggering checkpoint 5 (type=CHECKPOINT) @ 1681652631326 for job 6366a2b06387c6c734db67e1124c3395.
21:43:51,329 INFO   [] - snapshotState subTask: 1, checkpointId: 5, checkpointTimestamp: 1681652631326, element: a11
21:43:51,329 INFO   [] - snapshotState subTask: 0, checkpointId: 5, checkpointTimestamp: 1681652631326, element: a12
```

> 完整请查阅[]()


> [CheckpointedFunction](https://ci.apache.org/projects/flink/flink-docs-master/api/java/org/apache/flink/streaming/api/checkpoint/CheckpointedFunction.html)
