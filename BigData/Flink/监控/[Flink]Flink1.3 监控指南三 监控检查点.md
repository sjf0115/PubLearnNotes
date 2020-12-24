### 1. 概述

Flink的Web界面提供了一个选项卡来监视作业的检查点。即使作业结束后，这些统计数据也可使用。有四个不同的选项卡用来展示检查点相关信息:概览，历史记录，摘要和配置。以下部分将依次介绍所有这些内容。

### 2. 概览选项卡

![](http://img.blog.csdn.net/20171119113630725?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

概览选项卡列出了以下统计信息:

(1) 检查点个数(Checkpoint Counts):  

- 触发(Triggered)：自作业开始以来触发的检查点总数。
- 进行中：正在进行的检查点个数。
- 已完成：自作业开始以来成功完成的检查点总数。
- 失败：自作业开始以来失败的检查点总数。
- 已恢复：自作业开始以来恢复的算子总数。这也会告诉你自从提交以来作业重新启动了多少次。请注意，使用保存点进行的初始提交也算作一次还原，如果JobManager在操作期间发生故障，则会重置计数。

(2) 最近完成的检查点(Latest Completed Checkpoint)：最近成功完成的检查点。点击`更多详细信息`可以获得子任务级别d的详细统计信息。

(3) 最近失败检查点(Latest Failed Checkpoint)：最新失败检查点。点击`更多详细信息`可以获得子任务级别的详细统计信息。

(4) 最近的保存点(Latest Savepoint)：最新触发的保存点及其外部路径。点击`更多详细信息`可以获得子任务级别的详细统计信息。

(5) 最近恢复(Latest Restore)：有两种类型的恢复操作。
- 从检查点恢复：我们从定期检查点恢复(a regular periodic checkpoint)。
- 从保存点恢复：我们从保存点恢复。

备注:
```
这些统计信息在JobManager发生故障时失效，如果JobManager故障结束，这些统计信息将会重置。
```

### 3. 历史记录选项卡

检查点历史记录保存最近触发的检查点的统计信息，包括当前正在进行的检查点。

![](http://img.blog.csdn.net/20171119115823082?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

属性|说明
---|---
ID|触发的检查点的ID。每个检查点的ID都从1开始递增
Status|检查点的当前状态(`Progress`, `Completed` , 或则 `Failed`)。如果触发的检查点是保存点，将会看到一个保存符号
Trigger Time|在JobManager中触发检查点的时间
Latest Acknowledgement|在JobManager中收到的任何子任务最近确认时间(如果还没有收到确认，则为n/a)
End to End Duration|从触发时间到最近确认时间的持续时间(或者如果还没有收到确认，则为n/a)。完成检查点的结束持续时间由确认检查点的最后一个子任务确定。这个时间通常大于单个子任务实际需要检查状态的时间
State Size|所有已确认的子任务的状态大小
Buffered During Alignment|The number of bytes buffered during alignment over all acknowledged subtasks. This is only > 0 if a stream alignment takes place during checkpointing. If the checkpointing mode is AT_LEAST_ONCE this will always be zero as at least once mode does not require stream alignment.

#### 3.1 历史记录大小配置

你可以通过以下配置属性配置历史记录中最近检查点的数量。默认值是10。
```
# Number of recent checkpoints that are remembered
jobmanager.web.checkpoints.history: 15
```

### 4. 摘要选项卡

摘要在端到端持续时间(End to End Duration)，状态大小(State Size)和对齐缓冲字节数(Bytes Buffered During Alignment)上对所有已完成检查点进行简单的最小/平均/最大统计量(有关这些含义的详细信息，请参阅[历史记录](https://ci.apache.org/projects/flink/flink-docs-release-1.3/monitoring/checkpoint_monitoring.html#history))。

![](http://img.blog.csdn.net/20171119115810769?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

### 5. 配置选项卡

### 6. 检查点详细信息






原文:https://ci.apache.org/projects/flink/flink-docs-release-1.3/monitoring/checkpoint_monitoring.html
