https://mp.weixin.qq.com/s/6zUCeFGw4_AAcQzw4ugWoQ
https://www.jianshu.com/p/c9d6e9fe900a
- [Faster checkpointing through unaligned checkpoints](https://www.youtube.com/watch?v=-ABPHMhrecQ)
https://blog.csdn.net/nazeniwaresakini/article/details/107954076

## 1. Barrier

Flink 分布式快照的核心元素就是 Barrier。Flink 通过在 Source 中定时向数据流注入 Barrier 这种特殊元素，也会作为数据流中的一个元素在流动。Barrier 会严格按顺序流动，永远不会超过其前面的记录。Barrier 将数据流中的记录分隔为进入当前 Checkpoint 的记录集和进入下一个 Checkpoint 的记录集（Barrier 将数据流划分为多个有限序列，对应多个 Checkpoint 周期）。每个 Barrier 都携带它前面的 Checkpoint 的ID。Barrier 不会中断水流的流动，因此非常轻。来自不同 Checkpoint 的多个 Barrier 可以同时存在于流中，这意味着各种 Checkpoint 可能同时发生。

![]()

然后 Barrier 流向下游。当中间算子从其所有输入流中接收到 Checkpoint n 的 Barrier 时，将向其所有输出流输出 Checkpoint n 的 Barrier。一旦一个 Sink 算子从它所有输入流中接收到 Barrier n，就会向 Checkpoint 协调器确认 Checkpoint n。当所有的 Sink 都确认了一个 Checkpoint 后，就认为它完成了。

一旦 Checkpoint n 完成，作业将不再向 Source 请求 Sn 之前的记录，因为此时这些记录(以及它们的后代记录)将穿过整个数据流拓扑。

https://nightlies.apache.org/flink/flink-docs-release-1.16/docs/concepts/stateful-stream-processing/#unaligned-checkpointing

一旦算子从一个输入流中接收到 Barrier n（不是指 Barrier n 到达输入缓冲区），它就不能进一步处理来自该流的任何记录，直到从其他输入流中也接收到 Barrier n。否则会将属于 Checkpoint n 和 Checkpoint n+1 的记录混合在一起。

一旦最后一个输入流接收到 Barrier n，算子输出所有挂起的输出记录，然后本身输出 Checkpoint n 的 Barrier。对状态进行快照，并从所有输入流恢复处理记录，在处理来自输入数据流的记录之前先处理来自输入缓冲区的记录。

最后，算子将状态异步写入状态后端。
