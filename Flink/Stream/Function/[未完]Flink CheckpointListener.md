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
