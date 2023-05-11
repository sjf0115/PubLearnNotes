Flink 应用端到端的一致性保障取决于 Sink 连接器的属性，正常情况下不做额外的操作是不能提供 Exactly-Once 语义保障的。例如 Failover 会导致作业重启，然后从最近一次成功的检查点记录的 Offset 位点开始消费，这样会导致重复消费检查点记录的 Offset 位点到已经消费到的 Offset 位点之间记录。为了提供端到端的一致性保障，应用的 Sink 连接器要么实现幂等性，要么实现事务支持。如果无法实现幂等性写入，也没有提供内置的事务支持，那只能通过在检查点完成之后再将检查点周期内的所有记录写入到外部系统(这样就就跟检查点重置的 Offset 对应)。Flink 已经帮我们实现了一个通用 WAL Sink 模板(GenericWriteAheadSink)来完成事务写入。

## 1. 原理

为了简化事务 WAL Sink 的实现，Flink DataStream API 提供了一个 GenericWriteAheadSink 模板(抽象类)，可以通过继承更加方便的实现一致性的 Sink。实现 GenericWriteAheadSink 的算子会和 Flink 的检查点机制相结合，目的是将记录以 Exactly-Once 语义写入外部系统。

需要特别注意的是，基于 WAL 的 Sink 在某些极端情况下可能会将同一条记录重复写出多次。因此 GenericWriteAheadSink 并不能百分之百的提供 Exactly-Once 语义保证，而只能做到 At-Least-Once 语义保证。有两种故障会导致同一条记录重复写出多次：
- 在运行 `sendValues` 方法时发生故障。如果外部系统不支持原子性的写入多个记录(全写或者全不写)，那么就会出现部分数据已经写入而部分数据没能写入成功。由于此时检查点还没有提交，下次恢复时重写全部记录。
- 所有记录都已经成功写入，`sendValues` 返回了 true，但是程序在调用 CheckpointCommitter 前出现故障或者 CheckpointCommitter 未能成功提交检查点。这样，在故障恢复期间，未提交的检查点所对应的全部记录都会被重新消费一次。

GenericWriteAheadSink 会收集每个检查点周期内所有需要写出的记录，并将它们存储到 Sink 任务的算子状态中。该状态会被写入到检查点并在故障时恢复。由于它在发生故障时可以恢复，所以不会导致数据丢失。

当一个任务接收到检查点完成通知时，会将此检查点周期内的所有记录写入到外部系统。根据 Sink 的具体实现，这些记录可以被写入任意一个存储或者消息系统中。当所有记录发送成功时，Sink 需要在内部提交该检查点。检查点的提交分两步。第一步，Sink 需要将检查点已提交的信息持久化。第二步，删除 WAL 中相应的数据。检查点已提交的信息无法存储在 Flink 应用程序状态中，因为状态本身不具有持久性，并且会在故障恢复时重置状态。实际上，GenericWriteAheadSink 依赖一个名为 CheckpointCommitter 的可插拔组件来控制外部持久化系统存储和查找已提交检查点信息。

## 2. 实现

GenericWriteAheadSink 完善的内部逻辑使得我们可以相对容易的实现基于 WAL 的 Sink。继承自 GenericWriteAheadSink 的算子需要在构造方法中提供三个参数：
- 一个 CheckpointCommitter
- 一个用于序列化输入记录的 TypeSerializer
- 一个传递给 CheckpointCommitter，用于应用重启后标识提交信息的作业 ID
```java
private static class StdOutWALSink extends GenericWriteAheadSink<Tuple2<String, Long>> {
    // 构造函数
    public StdOutWALSink() throws Exception {
        super(
                // CheckpointCommitter
                new FileCheckpointCommitter(System.getProperty("java.io.tmpdir")),
                // 用于序列化输入记录的 TypeSerializer
                Types.<Tuple2<String, Long>>TUPLE(Types.STRING, Types.LONG).createSerializer(new ExecutionConfig()),
                // 自定义作业 ID
                UUID.randomUUID().toString()
        );
    }
}
```
从上面可以看到内部使用一个名为 FileCheckpointCommitter 的 CheckpointCommitter，将 Sink 算子实例提交的检查点信息保存到文件中，具体实现可以查阅[Flink 源码解读系列 CheckpointCommitter](https://smartsi.blog.csdn.net/article/details/130550211)。

此外，最重要的是需要实现 `sendValues` 方法：
```java
@Override
protected boolean sendValues(Iterable<Tuple2<String, Long>> words, long checkpointId, long timestamp) throws Exception {
    // 输出到外部系统 在这为 StdOut 标准输出
    // 每次 Checkpoint 完成之后通过 notifyCheckpointComplete 调用该方法
    int subtask = getRuntimeContext().getIndexOfThisSubtask();
    for (Tuple2<String, Long> word : words) {
        System.out.println("StdOut> " + word);
        LOG.info("checkpointId {} (subTask = {}) send word: {}", checkpointId, subtask, word);
    }
    return true;
}
```
GenericWriteAheadSink 会调用 `sendValues` 方法将已完成检查点 `checkpointId` 对应的全部记录写入外部存储系统。该方法第一个参数是检查点 `checkpointId` 对应全部记录的 Iterable 对象 `words`、检查点ID `checkpointId` 以及检查点的生成时间 `timestamp`。在这我们简单实现了一个写标准输出的 WAL Sink，输出该检查点对应的全部记录。在全部记录写出成功时返回 true，如果失败则返回 false。

> 你可以简单理解 GenericWriteAheadSink 实现了一个缓存，在收到上游的记录时，先将消息存储在状态中，再收到 Checkpoint 完成通知后，调用 `sendValues` 方法向外部系统输出缓冲的全部记录。GenericWriteAheadSink 相当于缓存了一个 Checkpoint 间隔的记录。

需要注意的是，GenericWriteAheadSink 没有实现 SinkFunction 接口。因此我们无法使用 `DataStream.addSink()` 方法添加一个继承自 GenericWriteAheadSink 的 Sink，而是要使用 `DataStream.transform()` 方法：
```java
// WAL Sink 输出 需要等 Checkpoint 完成再输出
result.transform(
    "StdOutWriteAheadSink",
    Types.TUPLE(Types.STRING, Types.LONG),
    new StdOutWALSink()
);
```

## 3. 源码分析

GenericWriteAheadSink 是一个抽象类：
```java
public abstract class GenericWriteAheadSink<IN> extends AbstractStreamOperator<IN>
        implements OneInputStreamOperator<IN, IN> {
}
```
GenericWriteAheadSink 实现了一个将其输入元素发送到任意状态后端的通用 Sink。该 Sink 与 Flink 的 checkpointing 机制集成，可以提供 Exactly-Once 语义保证，具体还需要取决于状态后端和 Sink/Committer 的实现。传入进来的记录会存储在 AbstractStateBackend 中，并且仅在检查点完成时提交。

### 3.1 构造器 GenericWriteAheadSink

继承自 GenericWriteAheadSink 的算子需要在构造方法中提供三个参数：
- 一个 CheckpointCommitter
- 一个用于序列化输入记录的 TypeSerializer
- 一个传递给 CheckpointCommitter，用于应用重启后标识提交信息的作业 ID
```java
public GenericWriteAheadSink(CheckpointCommitter committer, TypeSerializer<IN> serializer, String jobID) throws Exception {
    this.committer = Preconditions.checkNotNull(committer);
    this.serializer = Preconditions.checkNotNull(serializer);
    this.id = UUID.randomUUID().toString();
    this.committer.setJobId(jobID);
    this.committer.createResource();
}
```
此外，还在构造函数中调用 CheckpointCommitter 的 `createResource` 方法来创建资源(可以是分布式存储，也可以是数据库)，后续用来存储提交的检查点信息。

### 3.2 初始化状态 initializeState

当第一次初始化函数或者因为故障重启需要从之前 Checkpoint 中恢复状态数据时会调用 `initializeState()` 方法：
```java
private transient ListState<PendingCheckpoint> checkpointedState;
private final Set<PendingCheckpoint> pendingCheckpoints = new TreeSet<>();

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
    }
}
```
通过该方法访问 OperatorStateStore 获取一个 ListState 来存储待提交的检查点 PendingCheckpoint(包含了检查点ID，当前子任务ID，检查点生成时间以及状态句柄)。然后通过 `isRestored()` 方法来判断状态是否是从上一次成功的 Checkpoint 中恢复(如果是返回 true），将从状态中恢复的待提交检查点 PendingCheckpoint 保存在 pendingCheckpoints 集合中。如果是第一次初始化函数则不会从 Checkpoint 中进行恢复。

### 3.3 打开 open

`open()` 方法在处理任何元素之前调用，主要包含算子的一些初始化逻辑，例如为 FileCheckpointCommitter 设置算子ID以及获取 CheckpointStorage 等：
```java
public void open() throws Exception {
    super.open();
    committer.setOperatorId(id);
    committer.open();
    checkpointStorage = getContainingTask().getCheckpointStorage();
    cleanRestoredHandles();
}

private void cleanRestoredHandles() throws Exception {
    synchronized (pendingCheckpoints) {
        Iterator<PendingCheckpoint> pendingCheckpointIt = pendingCheckpoints.iterator();
        while (pendingCheckpointIt.hasNext()) {
            PendingCheckpoint pendingCheckpoint = pendingCheckpointIt.next();
            if (committer.isCheckpointCommitted(pendingCheckpoint.subtaskId, pendingCheckpoint.checkpointId)) {
                pendingCheckpoint.stateHandle.discardState();
                pendingCheckpointIt.remove();
            }
        }
    }
}
```
此外该方法中最重要的是调用 `cleanRestoredHandles()` 方法来遍历从状态中恢复的所有待提交的检查点。通过 FileCheckpointCommitter 的 `isCheckpointCommitted` 方法来检查哪些已经提交到外部存储系统了，如果已经提交了则将它们从 pendingCheckpoints 列表中删除并清除状态句柄。

### 3.4 元素处理 processElement

```java
public void processElement(StreamRecord<IN> element) throws Exception {
    IN value = element.getValue();
    if (out == null) {
        out = checkpointStorage.createTaskOwnedStateStream();
    }
    serializer.serialize(value, new DataOutputViewStreamWrapper(out));
}
```

### 3.5 生成状态快照 snapshotState

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
### 3.6 检查点完成通知 CheckpointCommitter

CheckpointCommitter 类用于保存 Sink 算子实例已将检查点提交到状态后端的信息。

```
public void notifyCheckpointComplete(long checkpointId) throws Exception {
    super.notifyCheckpointComplete(checkpointId);
    synchronized (pendingCheckpoints) {
        Iterator<PendingCheckpoint> pendingCheckpointIt = pendingCheckpoints.iterator();
        while (pendingCheckpointIt.hasNext()) {
            PendingCheckpoint pendingCheckpoint = pendingCheckpointIt.next();
            long pastCheckpointId = pendingCheckpoint.checkpointId;
            int subtaskId = pendingCheckpoint.subtaskId;
            long timestamp = pendingCheckpoint.timestamp;
            StreamStateHandle streamHandle = pendingCheckpoint.stateHandle;

            if (pastCheckpointId <= checkpointId) {
                try {
                  if (!committer.isCheckpointCommitted(subtaskId, pastCheckpointId)) {
                    try (FSDataInputStream in = streamHandle.openInputStream()) {
                      //  判断是否发送成功
                      boolean success =
                          sendValues(
                              new ReusingMutableToRegularIteratorWrapper<>(
                                  new InputViewIterator<>(new DataInputViewStreamWrapper(in), serializer),
                                  serializer
                              ),
                              pastCheckpointId,
                              timestamp
                          );
                      // 发送成功
                      if (success) {
                          committer.commitCheckpoint(subtaskId, pastCheckpointId);
                          streamHandle.discardState();
                          pendingCheckpointIt.remove();
                      }
                    }
                  } else {
                      streamHandle.discardState();
                      pendingCheckpointIt.remove();
                  }
                } catch (Exception e) {
                    LOG.error("Could not commit checkpoint.", e);
                    break;
                }
            }
        }
    }
}
```


当前的检查点机制不适合依赖于不支持回滚的后端的接收器。在处理这样的系统时，在尝试获得完全一次语义时，既不能在创建快照时提交数据（因为另一个接收器实例可能失败，导​​致对相同数据的重放），也不能在接收到检查点完成通知时（因为随后的失败将使我们不知道数据是否已提交）。

### 3.7 关闭 close

```java
public void close() throws Exception {
    committer.close();
}
```









...
