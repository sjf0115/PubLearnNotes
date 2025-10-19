在流处理系统中，实现端到端的精确一次（Exactly-Once）语义是一个经典且复杂的挑战。当数据从源端流出，经过复杂的处理逻辑，最终写入外部存储系统时，如何在故障恢复的场景下保证数据既不丢失也不重复，是每个流处理框架必须解决的问题。

Apache Flink 通过其创新的检查点机制和状态管理，提供了强大的精确一次保证。而 GenericWriteAheadSink 则是实现这一目标的关键组件之一。本文将深入 Flink 1.13.6 源码探讨其设计原理是如何保证数据的可靠性。

GenericWriteAheadSink 实现了一个将其输入元素发送到任意状态后端的通用 Sink。该 Sink 与 Flink 的 CheckPoint 机制集成，可以提供 Exactly-Once 语义保证，具体还需要取决于状态后端和 Sink/Committer 的实现。传入进来的记录会存储在 AbstractStateBackend 中，并且仅在检查点完成时提交。

## 1. GenericWriteAheadSink 架构

GenericWriteAheadSink 是一个抽象类，继承自 `AbstractStreamOperator` 抽象类并实现了 `OneInputStreamOperator` 接口：
```java
public abstract class GenericWriteAheadSink<IN> extends AbstractStreamOperator<IN> implements OneInputStreamOperator<IN, IN> {
    public GenericWriteAheadSink(CheckpointCommitter committer, TypeSerializer<IN> serializer, String jobID) throws Exception {
        ...
    }

    @Override
    public void open() throws Exception {
        ...
    }

    public void close() throws Exception {
        ...
    }

    @Override
    public void initializeState(StateInitializationContext context) throws Exception {
        ...
    }

    @Override
    public void snapshotState(StateSnapshotContext context) throws Exception {
        ...
    }

    @Override
    public void notifyCheckpointComplete(long checkpointId) throws Exception {
        ...
    }

    protected abstract boolean sendValues(Iterable<IN> values, long checkpointId, long timestamp) throws Exception;

    @Override
    public void processElement(StreamRecord<IN> element) throws Exception {
        ...
    }
}
```

## 2. 核心工作机制详解

### 2.1 生命周期管理

### 2.1.1 构造器

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

> 写入外部系统成功时提交 CheckpointCommitter 标记 Checkpoint 对应数据通过 sendValues 提交外部系统成功

#### 2.1.2 open

`open()` 方法在处理任何元素之前调用，主要包含算子的一些初始化逻辑，例如开启 CheckpointCommitter 设置算子ID以及获取 CheckpointStorage 等：
```java
public void open() throws Exception {
    super.open();
    this.committer.setOperatorId(this.id);
    this.committer.open();
    this.checkpointStorage = this.getContainingTask().getCheckpointStorage();
    this.cleanRestoredHandles();
}
```
此外该方法中最重要的是调用 `cleanRestoredHandles()` 方法来遍历从状态中恢复的所有待提交的检查点。通过 CheckpointCommitter 的 `isCheckpointCommitted` 方法来检查哪些已经提交到外部存储系统了，如果已经提交了则将它们从 pendingCheckpoints 列表中删除并清除状态句柄：
```java
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

#### 2.1.3 close

使用 close 方法关闭 GenericWriteAheadSink，核心关闭 CheckpointCommitter：
```java
public void close() throws Exception {
    this.committer.close();
}
```

### 2.2 数据接收与缓存

`processElement()` 方法用来处理到达的元素记录 StreamRecord，并将其写入到 Checkpoint 状态流中。当第一个元素到达时，会调用 `checkpointStorage.createTaskOwnedStateStream()` 创建一个新的任务管理的状态流，然后后续的元素都会序列化并写入这个流：
```java
@Override
public void processElement(StreamRecord<IN> element) throws Exception {
    IN value = element.getValue();
    if (out == null) {
        out = checkpointStorage.createTaskOwnedStateStream();
    }
    serializer.serialize(value, new DataOutputViewStreamWrapper(out));
}
```
从上面代码中可以看到通过 CheckpointStorageWorkerView(`checkpointStorage.createTaskOwnedStateStream()`) 创建一个流来持久化 Checkpoint 状态数据，需要注意的是数据只跟任务有关系，与 Checkpoint 的生命周期没有关系。当创建持久数据的 Checkpoint 被删除后而无法立即删除数据时，建议使用此方法，例如预写日志。对于这些情况，只有在数据写入到目标系统后才能删除状态，这有时可能需要比一个 Checkpoint 更长的时间(如果目标系统暂时无法跟上)。作业管理器不拥有这种状态的生命周期，这也意味着这些数据的清理完全交由任务来责任。

### 2.3 快照管理

#### 2.3.1 initializeState

当第一次初始化函数或者因为故障重启需要从之前 Checkpoint 中恢复状态数据时会调用 `initializeState(StateInitializationContext)` 方法：
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
通过该方法访问 OperatorStateStore 获取一个算子状态 ListState 来存储待提交的检查点 PendingCheckpoint(包含了检查点ID，当前子任务ID，检查点生成时间以及状态句柄)。然后通过 `isRestored()` 方法来判断状态是否是从上一次成功的 Checkpoint 中恢复(如果是返回 true），将从状态中恢复的待提交检查点 PendingCheckpoint 保存在 pendingCheckpoints 集合中。如果是第一次初始化则不会从 Checkpoint 中进行恢复。

#### 2.3.2 snapshotState

每当触发 Checkpoint 生成状态快照时就会调用 `snapshotState(StateSnapshotContext)` 方法：
```java
public void snapshotState(StateSnapshotContext context) throws Exception {
    super.snapshotState(context);
    Preconditions.checkState(this.checkpointedState != null, "The operator state has not been properly initialized.");
    // 关闭当前状态流并获取一个状态句柄封装在 PendingCheckpoint
    saveHandleInState(context.getCheckpointId(), context.getCheckpointTimestamp());
    // 清空上一次快照的状态
    this.checkpointedState.clear();
    try {
        // 生成新快照的状态
        for (PendingCheckpoint pendingCheckpoint : pendingCheckpoints) {
            this.checkpointedState.add(pendingCheckpoint);
        }
    } catch (Exception e) {
        checkpointedState.clear();
        throw new Exception("Could not add panding checkpoints to operator state backend of operator " + getOperatorName() + '.', e);
    }
}
```
上面我们知道每当一个记录到达时都会调用 `processElement()` 方法来处理，并写入 CheckPoint 状态流中。再触发 Checkpoint 快照时关闭当前状态流并获取一个状态句柄。另外根据当前检查点ID、Checkpoint 时间戳、当前子任务 ID 来封装成 PendingCheckpoint，并存入待提交 CheckPoint 集合中等待写入算子状态中:
```java
private void saveHandleInState(final long checkpointId, final long timestamp) throws Exception {
    if (out != null) {
        int subtaskIdx = getRuntimeContext().getIndexOfThisSubtask();
        // 将当前的状态流关闭并获取一个状态句柄
        StreamStateHandle handle = out.closeAndGetHandle();
        // 待提交的 Checkpoint
        // 创建一个 PendingCheckpoint 对象，将其添加到待处理的检查点集合中
        PendingCheckpoint pendingCheckpoint = new PendingCheckpoint(checkpointId, subtaskIdx, timestamp, handle);
        // 我们已经为该 ID 存储了一个可能部分写入的检查点，所以我们会丢弃这个“备用版本”，并使用已存储的检查点。
        if (pendingCheckpoints.contains(pendingCheckpoint)) {
            handle.discardState();
        } else {
            pendingCheckpoints.add(pendingCheckpoint);
        }
        out = null;
    }
}
```
将待提交的检查点的数据保存到状态后端并最终持久化存储:
```java
// 生成新快照的状态
for (PendingCheckpoint pendingCheckpoint : pendingCheckpoints) {
    this.checkpointedState.add(pendingCheckpoint);
}
```

### 2.3.3 notifyCheckpointComplete

当 Checkpoint 完成时会调用 `notifyCheckpointComplete()` 方法来周知该 Checkpoint 已完成，核心完成输出每个待提交检查点缓冲的数据并进行提交：
```java
public void notifyCheckpointComplete(long checkpointId) throws Exception {
    super.notifyCheckpointComplete(checkpointId);
    synchronized (pendingCheckpoints) {
        Iterator<PendingCheckpoint> pendingCheckpointIt = pendingCheckpoints.iterator();
        // 处理每个 PendingCheckpoint
        while (pendingCheckpointIt.hasNext()) {
            PendingCheckpoint pendingCheckpoint = pendingCheckpointIt.next();
            long pastCheckpointId = pendingCheckpoint.checkpointId;
            int subtaskId = pendingCheckpoint.subtaskId;
            long timestamp = pendingCheckpoint.timestamp;
            StreamStateHandle streamHandle = pendingCheckpoint.stateHandle;
            // 处理小于当前 checkpointId 的 Checkpoint
            if (pastCheckpointId <= checkpointId) {
                try {
                    // 通过 CheckpointCommitter 判断是否已提交
                    if (!committer.isCheckpointCommitted(subtaskId, pastCheckpointId)) {
                        ...
                    } else {
                        ...
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
核心提交处理逻辑：
```java
// Checkpoint 对应的数据是否已成功提交到外部系统 通过 CheckpointCommitter 来判断
if (!committer.isCheckpointCommitted(subtaskId, pastCheckpointId)) {
    // 未提交到外部系统
    try (FSDataInputStream in = streamHandle.openInputStream()) {
        // 从状态流句柄中重新读取序列化数据
        ReusingMutableToRegularIteratorWrapper<IN> ins = new ReusingMutableToRegularIteratorWrapper<>(
                new InputViewIterator<>(new DataInputViewStreamWrapper(in), serializer),
                serializer
        );
        // 交由 sendValues 发送
        boolean success = sendValues(ins, pastCheckpointId, timestamp);
        // 发送成功 通过 CheckpointCommitter 标记已成功提交到外部系统
        if (success) {
            committer.commitCheckpoint(subtaskId, pastCheckpointId);  // 标记为已提交
            streamHandle.discardState(); // 清理状态数据
            pendingCheckpointIt.remove(); // 从待处理列表移除
        }
        // 如果失败，保持现状等待下次重试
    }
} else {
    // 已提交到外部系统
    streamHandle.discardState();  // 清理状态数据
    pendingCheckpointIt.remove(); // 从待处理列表移除
}
```
> 通过 sendValues 成功输出到外部系统则通过 CheckpointCommitter 标记该 Checkpoint 已提交

假设有以下场景：
- Checkpoint 序列: 100, 101, 102, 103
- 当前完成 Checkpoint: checkpointId = 102
- pendingCheckpoints: [100, 101, 102]  // 按checkpointId排序

那么执行过程：
- Checkpoint 100: 已提交？ → 否 → 读取数据 → 发送成功 → 提交并清理
- Checkpoint 101: 已提交？ → 否 → 读取数据 → 发送成功 → 提交并清理
- Checkpoint 102: 已提交？ → 否 → 读取数据 → 发送成功 → 提交并清理
- 结果: pendingCheckpoints = []（全部清理）

### 2.4 内部数据结构 PendingCheckpoint

PendingCheckpoint 是对待提交的一个 Checkpoint 的封装，包含了 Checkpoint Id(checkpointId)、子任务Id(subtaskId)、Checkpoint 时间戳(timestamp)以及状态句柄(stateHandle)。重写了 equals、hashCode、toString 方法，此外还实现了 Comparable 接口重写了 compareTo 方法用于比较 PendingCheckpoint 的大小，确保能按照 CheckpointId 和 SubtaskId 顺序提交 Checkpoint：
```java
private static final class PendingCheckpoint implements Comparable<PendingCheckpoint>, Serializable {

    private static final long serialVersionUID = -3571036395734603443L;

    private final long checkpointId;
    private final int subtaskId;
    private final long timestamp;
    private final StreamStateHandle stateHandle;

    PendingCheckpoint(long checkpointId, int subtaskId, long timestamp, StreamStateHandle handle) {
        this.checkpointId = checkpointId;
        this.subtaskId = subtaskId;
        this.timestamp = timestamp;
        this.stateHandle = handle;
    }

    @Override
    public int compareTo(PendingCheckpoint o) {
        int res = Long.compare(this.checkpointId, o.checkpointId);
        return res != 0 ? res : this.subtaskId - o.subtaskId;
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof GenericWriteAheadSink.PendingCheckpoint)) {
            return false;
        }
        PendingCheckpoint other = (PendingCheckpoint) o;
        return this.checkpointId == other.checkpointId
                && this.subtaskId == other.subtaskId
                && this.timestamp == other.timestamp;
    }

    @Override
    public int hashCode() {
        int hash = 17;
        hash = 31 * hash + (int) (checkpointId ^ (checkpointId >>> 32));
        hash = 31 * hash + subtaskId;
        hash = 31 * hash + (int) (timestamp ^ (timestamp >>> 32));
        return hash;
    }

    @Override
    public String toString() {
        return "Pending Checkpoint: id=" + checkpointId + "/" + subtaskId + "@" + timestamp;
    }
}
```
