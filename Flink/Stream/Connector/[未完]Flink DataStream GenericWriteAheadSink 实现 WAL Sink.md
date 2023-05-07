
## 1. 原理

GenericWriteAheadSink 可以使实现一致性 Sink 更加的方便。这些算子会和 Flink 的检查点机制相结合，目的是将记录以 Exactly-Once 语义写入外部系统。然而，基于 WAL 的 Sink 在某些极端情况下可能会将同一条记录重复写出多次。因此 GenericWriteAheadSink 并不能百分之百的提供 Exactly-Once 语义保证，而只能做到 At-Least-Once 语义保证。

GenericWriteAheadSink 的原理是将接收到的所有记录都追加到由检查点分割好的预写式日志 WAL 中去。每当 Sink 算子遇到检查点屏障 Barrier，算子将会开辟一个新的 '记录章节'，并将接下来的所有记录都追加到新的 '记录章节' 中去。WAL（预写式日志）会以算子状态的形式存储和写入检查点。由于它在发生故障时可以恢复，所以不会导致数据丢失。

当 GenericWriteAheadSink 接收到检查点完成通知时，就会将 WAL 中该检查点对应的所有记录发出。根据 Sink 的具体实现，这些记录可以被写入任意一个存储或者消息系统中。当所有记录发送成功时，Sink 需要在内部提交该检查点。

检查点的提交分两步。第一步，Sink 需要将检查点已提交的信息持久化。第二步，删除 WAL 中相应的数据。检查点已提交的信息无法存储在 Flink 应用程序状态中，因为状态本身不具有持久性，并且会在故障恢复时重置状态。实际上，GenericWriteAheadSink 依赖一个名为 CheckpointCommitter 的可插拔组件来控制外部持久化系统存储和查找已提交检查点信息。

## 2. 实现

GenericWriteAheadSink 完善的内部逻辑使得我们可以相对容易的实现基于 WAL 的 Sink。继承自 GenericWriteAheadSink 的算子需要再构造方法中提供三个参数：
- 一个 CheckpointCommitter
- 一个用于序列化输入记录的 TypeSerializer
- 一个传递给 CheckpointCommitter，用于应用重启后标识提交信息的作业 ID

此外，算子还需要一个方法：
```java
protected abstract boolean sendValues(Iterable<IN> values, long checkpointId, long timestamp) throws Exception;
```
GenericWriteAheadSink 会调用 方法将已完成检查点对应的记录写入外部存储系统。该方法接收的参数为针对检查点对应全部记录的 Iterable 对象、检查点ID，以及检查点的生成时间。它会在全部记录写出成功时返回 true，如果失败则返回 false。


抽象类GenericWriteAheadSink实现了缓存数据。在收到上游的消息时，会将消息存储在state中(保存于taskowned目录下)，收到全局一致快照完成的notify后，调用sendValues(Iterable<IN> values, long checkpointId, long timestamp)方法向下游系统发送global commit的消息。



## 3. 源码分析

```java
public abstract class CustomGenericWriteAheadSink<IN> extends AbstractStreamOperator<IN>
        implements OneInputStreamOperator<IN, IN> {

}
```
GenericWriteAheadSink 实现了一个将其输入元素发送到任意状态后端的通用 Sink。该 Sink 与 Flink 的 checkpointing 机制集成，可以提供 Exactly-Once 语义保证，具体还需要取决于状态后端和 Sink/Committer 的实现。传入进来的记录会存储在 AbstractStateBackend 中，并且仅在检查点完成时提交。

### 3.1 构造器

继承 GenericWriteAheadSink 的算子需要提供三个构造器参数：
```java
GenericWriteAheadSink(CheckpointCommitter committer, TypeSerializer<IN> serializer, String jobID)
```
- CheckpointCommitter，Checkpoint 提交器
- TypeSerializer，用来序列化输入数据。
- jobID 作业ID，传给 CheckpointCommitter，当应用重启时可以识别commit信息。

### 3.2 生命周期管理

```java

```

### 3.3 状态处理

初始化状态：
```java
public void initializeState(StateInitializationContext context) throws Exception {
    super.initializeState(context);
    Preconditions.checkState(this.checkpointedState == null, "The reader state has already been initialized.");
    // 创建算子 Checkpoint 状态
    checkpointedState = context.getOperatorStateStore().getListState(
            new ListStateDescriptor<>("pending-checkpoints", new JavaSerializer<>())
    );
    // 子任务Id
    int subtaskIdx = getRuntimeContext().getIndexOfThisSubtask();
    // 是否需要从状态中恢复
    if (context.isRestored()) {
        LOG.info("Restoring state for the GenericWriteAheadSink (taskIdx={}).", subtaskIdx);
        for (PendingCheckpoint pendingCheckpoint : checkpointedState.get()) {
            this.pendingCheckpoints.add(pendingCheckpoint);
        }
    } else {
        LOG.info("No state to restore for the GenericWriteAheadSink (taskIdx={}).", subtaskIdx);
    }
}
```
生成状态快照：
```java
public void snapshotState(StateSnapshotContext context) throws Exception {
    super.snapshotState(context);
    Preconditions.checkState(this.checkpointedState != null, "The operator state has not been properly initialized.");

    saveHandleInState(context.getCheckpointId(), context.getCheckpointTimestamp());

    this.checkpointedState.clear();

    try {
        for (PendingCheckpoint pendingCheckpoint : pendingCheckpoints) {
            this.checkpointedState.add(pendingCheckpoint);
        }
    } catch (Exception e) {
        checkpointedState.clear();
        throw new Exception(xxx);
    }
}
```
### 3.4 CheckpointCommitter

CheckpointCommitter 类用于保存 Sink 算子实例已将检查点提交到状态后端的信息。

```java

```


当前的检查点机制不适合依赖于不支持回滚的后端的接收器。在处理这样的系统时，在尝试获得完全一次语义时，既不能在创建快照时提交数据（因为另一个接收器实例可能失败，导​​致对相同数据的重放），也不能在接收到检查点完成通知时（因为随后的失败将使我们不知道数据是否已提交）。

CheckpointCommitter 可用于解决第二个问题，方法是保存实例是否提交了属于某个检查点的所有数据。这些数据必须存储在一个后端，该后端在重试后是持久的（这排除了 Flink 的状态机制），并且可以从所有机器（如数据库或分布式文件）访问。

没有关于如何共享资源的规定；所有 Flink 作业可能有一个资源，或者每个作业/操作员/实例分别有一个资源。这意味着资源不能由系统本身清理，因此应保持尽可能小。











...
