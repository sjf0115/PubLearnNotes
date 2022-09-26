Flink 应用要想在大规模场景下可靠地运行，必须要满足如下两个条件：
- 应用程序需要能够可靠地创建 Checkpoint。
- 在应用故障恢复后，需要有足够的资源追赶输入流。

第一部分讨论如何在大规模场景下获得良好性能的 Checkpoint。后一部分解释了一些关于要规划使用多少资源的最佳实践。

## 1. 监控 State 和 Checkpoint

监控 Checkpoint 最简单的方法是通过查看 Web UI 的 Checkpoint 部分。[Flink 监控检查点 Checkpoint](https://smartsi.blog.csdn.net/article/details/127038971) 博文中你可以获取如何查看 Checkpoint 指标。


- 算子收到第一个 Checkpoint Barrier 的时间：从触发 Checkpoint 到算子收到第一个 Checkpoint Barrier 的时间一直非常高时，这意味着 Checkpoint Barrier 需要很长时间才能从 Source 到算子。这通常表明系统处于反压下运行。
- Checkpoint 对齐时间(Alignment Duration)：接收到第一个 Checkpoint Barrier 到最后一个之间的时间。在非对齐 Checkpoint 下，Exactly-Once 和 At-Least-Once 语义 Checkpoint 的 Subtasks 处理来自上游 Subtasks 的所有数据，不会有任何阻塞。对于对齐 Checkpoint，已经收到 Checkpoint Barrier 的 Channel 会被阻塞，直到所有剩余 Channel 都赶上并接收到 Checkpoint Barrier。

理想情况下，这两个值都应该很低。如果比较高，则意味着由于存在反压（没有足够的资源来处理传入的记录）导致 Checkpoint Barriers 在作业中的移动速度比较慢，这也可以处理记录的端到端延迟在增加来观察到。需要注意的是，在出现瞬间反压、数据倾斜或者网络问题时，这些指标也会抖动。


## 2. Checkpoint 调优

应用程序可以配置定期触发 Checkpoints。 当 checkpoint 完成时间超过 checkpoint 间隔时，在正在进行的 checkpoint 完成之前，不会触发下一个 checkpoint。默认情况下，一旦正在进行的 checkpoint 完成，将立即触发下一个 checkpoint。

当 checkpoints 完成的时间经常超过 checkpoints 基本间隔时(例如，因为状态比计划的更大，或者访问 checkpoints 所在的存储系统暂时变慢)， 系统不断地进行 checkpoints（一旦完成，新的 checkpoints 就会立即启动）。这可能意味着过多的资源被不断地束缚在 checkpointing 中，并且 checkpoint 算子进行得缓慢。 此行为对使用 checkpointed 状态的流式应用程序的影响较小，但仍可能对整体应用程序性能产生影响。

为了防止这种情况，应用程序可以定义 checkpoints 之间的最小等待时间：
```
StreamExecutionEnvironment.getCheckpointConfig().setMinPauseBetweenCheckpoints(milliseconds)
```
此持续时间是指从最近一个 checkpoint 结束到下一个 checkpoint 开始之间必须经过的最小时间间隔。下图说明了这如何影响 checkpointing。




https://mp.weixin.qq.com/s/0QRrOC7MaPHs_otAqK85ig
https://mp.weixin.qq.com/s/YhCJUamiGvGKbwVGWoXbGA
https://nightlies.apache.org/flink/flink-docs-master/zh/docs/ops/state/large_state_tuning/
