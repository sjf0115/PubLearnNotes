

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
首先创建 `ListState<PendingCheckpoint>` 的状态对象 `checkpointedState` 来保存 `PendingCheckpoint`。如果是因为故障重启从之前的 Checkpoint 中恢复状态数，则需要从 `checkpointedState` 中恢复 pendingCheckpoints。

每当触发 Checkpoint 生成转换函数的状态快照时就会调用 `snapshotState(StateSnapshotContext)` 方法：
```java
public void snapshotState(StateSnapshotContext context) throws Exception {
    super.snapshotState(context);
    Preconditions.checkState(this.checkpointedState != null, "The operator state has not been properly initialized.");

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

当 Checkpoint 完成时会调用 `notifyCheckpointComplete()` 方法：
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
                    // 是否已提交
                    if (!committer.isCheckpointCommitted(subtaskId, pastCheckpointId)) {
                        // 未提交
                        try (FSDataInputStream in = streamHandle.openInputStream()) {
                            // 判断是否发送成功
                            ReusingMutableToRegularIteratorWrapper<IN> ins = new ReusingMutableToRegularIteratorWrapper<>(
                                    new InputViewIterator<>(new DataInputViewStreamWrapper(in), serializer),
                                    serializer
                            );
                            boolean success = sendValues(ins, pastCheckpointId, timestamp);
                            // 发送成功
                            if (success) {
                                committer.commitCheckpoint(subtaskId, pastCheckpointId);
                                streamHandle.discardState();
                                pendingCheckpointIt.remove();
                            }
                        }
                    } else {
                        // 已提交
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
