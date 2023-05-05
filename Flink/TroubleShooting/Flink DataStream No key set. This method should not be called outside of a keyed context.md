## 1. 问题

在使用 CheckpointedFunction 实现操作 KeyedState 的有状态函数时，抛出如下异常：
```java
java.io.IOException: Could not perform checkpoint 1 for operator Flat Map -> Sink: Print to Std. Out (2/2)#0.
	at org.apache.flink.streaming.runtime.tasks.StreamTask.triggerCheckpointOnBarrier(StreamTask.java:1048) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.checkpointing.CheckpointBarrierHandler.notifyCheckpoint(CheckpointBarrierHandler.java:135) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.checkpointing.SingleCheckpointBarrierHandler.triggerCheckpoint(SingleCheckpointBarrierHandler.java:250) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.checkpointing.SingleCheckpointBarrierHandler.access$100(SingleCheckpointBarrierHandler.java:61) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.checkpointing.SingleCheckpointBarrierHandler$ControllerImpl.triggerGlobalCheckpoint(SingleCheckpointBarrierHandler.java:431) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.checkpointing.AbstractAlignedBarrierHandlerState.barrierReceived(AbstractAlignedBarrierHandlerState.java:61) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.checkpointing.SingleCheckpointBarrierHandler.processBarrier(SingleCheckpointBarrierHandler.java:227) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.checkpointing.CheckpointedInputGate.handleEvent(CheckpointedInputGate.java:180) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.checkpointing.CheckpointedInputGate.pollNext(CheckpointedInputGate.java:158) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.AbstractStreamTaskNetworkInput.emitNext(AbstractStreamTaskNetworkInput.java:110) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.io.StreamOneInputProcessor.processInput(StreamOneInputProcessor.java:66) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.processInput(StreamTask.java:423) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.mailbox.MailboxProcessor.runMailboxLoop(MailboxProcessor.java:204) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runMailboxLoop(StreamTask.java:684) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeInvoke(StreamTask.java:639) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.invoke(StreamTask.java:623) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:779) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at java.lang.Thread.run(Thread.java:748) ~[?:1.8.0_161]
Caused by: org.apache.flink.runtime.checkpoint.CheckpointException: Could not complete snapshot 1 for operator Flat Map -> Sink: Print to Std. Out (2/2)#0. Failure reason: Checkpoint was declined.
	at org.apache.flink.streaming.api.operators.StreamOperatorStateHandler.snapshotState(StreamOperatorStateHandler.java:264) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.StreamOperatorStateHandler.snapshotState(StreamOperatorStateHandler.java:169) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.AbstractStreamOperator.snapshotState(AbstractStreamOperator.java:371) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.checkpointStreamOperator(SubtaskCheckpointCoordinatorImpl.java:706) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.buildOperatorSnapshotFutures(SubtaskCheckpointCoordinatorImpl.java:627) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.takeSnapshotSync(SubtaskCheckpointCoordinatorImpl.java:590) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.checkpointState(SubtaskCheckpointCoordinatorImpl.java:312) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.lambda$performCheckpoint$8(StreamTask.java:1092) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$1.runThrowing(StreamTaskActionExecutor.java:50) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.performCheckpoint(StreamTask.java:1076) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.triggerCheckpointOnBarrier(StreamTask.java:1032) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	... 19 more
Caused by: java.lang.NullPointerException: No key set. This method should not be called outside of a keyed context.
	at org.apache.flink.util.Preconditions.checkNotNull(Preconditions.java:76) ~[flink-core-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.heap.StateTable.checkKeyNamespacePreconditions(StateTable.java:270) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.heap.StateTable.remove(StateTable.java:276) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.heap.StateTable.remove(StateTable.java:177) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.heap.AbstractHeapState.clear(AbstractHeapState.java:81) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.runtime.state.heap.HeapValueState.update(HeapValueState.java:85) ~[flink-runtime_2.11-1.13.5.jar:1.13.5]
	at com.flink.example.stream.function.stateful.CheckpointedFunctionKSExample$TemperatureAlertFlatMapFunction.snapshotState(CheckpointedFunctionKSExample.java:101) ~[classes/:?]
	at org.apache.flink.streaming.util.functions.StreamingFunctionUtils.trySnapshotFunctionState(StreamingFunctionUtils.java:118) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.util.functions.StreamingFunctionUtils.snapshotFunctionState(StreamingFunctionUtils.java:99) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.AbstractUdfStreamOperator.snapshotState(AbstractUdfStreamOperator.java:89) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.StreamOperatorStateHandler.snapshotState(StreamOperatorStateHandler.java:218) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.StreamOperatorStateHandler.snapshotState(StreamOperatorStateHandler.java:169) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.api.operators.AbstractStreamOperator.snapshotState(AbstractStreamOperator.java:371) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.checkpointStreamOperator(SubtaskCheckpointCoordinatorImpl.java:706) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.buildOperatorSnapshotFutures(SubtaskCheckpointCoordinatorImpl.java:627) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.takeSnapshotSync(SubtaskCheckpointCoordinatorImpl.java:590) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.SubtaskCheckpointCoordinatorImpl.checkpointState(SubtaskCheckpointCoordinatorImpl.java:312) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.lambda$performCheckpoint$8(StreamTask.java:1092) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$1.runThrowing(StreamTaskActionExecutor.java:50) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.performCheckpoint(StreamTask.java:1076) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	at org.apache.flink.streaming.runtime.tasks.StreamTask.triggerCheckpointOnBarrier(StreamTask.java:1032) ~[flink-streaming-java_2.11-1.13.5.jar:1.13.5]
	... 19 more
```

## 2. 解决方案

通过异常分析，抛出异常的位置如下所示：
```java
@Override
public void snapshotState(FunctionSnapshotContext context) throws Exception {
    // 获取最新的温度之后更新保存上一次温度的状态
    lastTemperatureState.update(lastTemperature); // 抛出异常信息的位置
    LOG.info("sensor snapshotState, temperature: {}", lastTemperature);
}
```
snapshotState 主要是给 OperatorState 使用的，异常原因是 KeyedState 访问时需要设置 currentKey，但是 currentKey 是当前正在处理的 record 的 Key，与 snapshotState 的执行语义不一样，执行 snapshotState 方法的时候，是可以没有当前 record 的。


Salva Alcántara 在 snapshotState 方法中对 keyed state 进行了 clear 处理。job 启动后，没有一条数据进入 input streams 时，触发 checkpoint 会报 NPE。Yun Tang 对该问题进行了回复，讲述了 keyed state 和 operator state 的区别，并根据 Salva Alcántara 的业务逻辑推荐他使用 operator state。
