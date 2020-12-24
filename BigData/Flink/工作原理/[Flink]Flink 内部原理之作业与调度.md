---
layout: post
author: sjf0115
title: Flink 内部原理之作业与调度
date: 2018-01-29 17:31:01
tags:
  - Flink
  - Flink 内部原理

categories: Flink
permalink: flink-internals-job-scheduling
---


### 1. 调度

`Flink`中的执行资源是通过任务槽定义。每个`TaskManager`都有一个或多个任务槽，每个任务槽可以运行一个并行任务的流水线(pipeline)。流水线由多个连续的任务组成，例如 `MapFunction` 的第n个并行实例和 `ReduceFunction` 的第n个并行实例。请注意，`Flink`经常同时执行连续的任务：对于流式处理程序时刻发生，但是对于批处理程序来说却是经常发生。

下图证明了这一点。考虑一个带有数据源，一个`MapFunction` 和 一个`ReduceFunction` 的程序。数据源和 `MapFunction` 以并行度`4`运行， `ReduceFunction`以并行度`3`运行。流水线由 `Source-Map-Reduce` 序列组成。在具有2个`TaskManager`（每个有3个插槽）的集群上，程序将按照下面的描述执行:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink_internals_job_scheduling-1.png?raw=true)

在内部，`Flink`通过[SlotSharingGroup](https://github.com/apache/flink/blob/master//flink-runtime/src/main/java/org/apache/flink/runtime/jobmanager/scheduler/SlotSharingGroup.java)和 [CoLocationGroup]()定义哪些任务可以共享一个槽（允许），哪些任务必须严格放置在同一个槽中。

### 2. JobManager 数据结构

在作业执行期间，`JobManager` 追踪分布式任务，决定何时调度下一个任务（或任务集合），并对完成的任务或执行失败的任务进行相应的处理。

`JobManager` 接收 [JobGraph](https://github.com/apache/flink/tree/master/flink-runtime/src/main/java/org/apache/flink/runtime/jobgraph)，`JobGraph`表示由算子（[JobVertex](https://github.com/apache/flink/blob/master//flink-runtime/src/main/java/org/apache/flink/runtime/jobgraph/JobVertex.java)）和中间结果（[IntermediateDataSet](https://github.com/apache/flink/blob/master//flink-runtime/src/main/java/org/apache/flink/runtime/jobgraph/IntermediateDataSet.java)）组成的数据流。每个算子都具有属性，如并行度和执行的代码等。另外，`JobGraph`还有一组附加的库，运行算子代码必需使用这些库。


`JobManager` 将 `JobGraph` 转换成 [ExecutionGraph](https://github.com/apache/flink/tree/master/flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph)。 `ExecutionGraph` 是 `JobGraph` 的并行版本：对于每个 `JobVertex`，对于每个并行子任务它都包含一个  [ExecutionVertex](https://github.com/apache/flink/blob/master//flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/ExecutionVertex.java)。例如并行度为100的算子会有一个 `JobVertex` 以及 100个 `ExecutionVertices`。 `ExecutionVertex`跟踪特定子任务的执行状态。`JobVertex` 中所有的 `ExecutionVertices` 都保存在一个 `ExecutionJobVertex` 中，该 [ExecutionJobVertex](https://github.com/apache/flink/blob/master//flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/ExecutionJobVertex.java) 跟踪整个算子的状态。除了顶点之外， `ExecutionGraph` 还包含 [IntermediateResult](https://github.com/apache/flink/blob/master//flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/IntermediateResult.java) 和 [IntermediateResultPartition](https://github.com/apache/flink/blob/master//flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/IntermediateResultPartition.java)。前者跟踪 `IntermediateDataSet` 的状态，后者追踪每个分区的状态。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink_internals_job_scheduling-2.png?raw=true)

每个 `ExecutionGraph` 都有一个与之相关的作业状态。作业状态表示作业执行的当前状态。

`Flink` 作业首先处于 `ctreated` 状态，然后切换到 `running` 状态，一旦所有工作完成后切换到 `finished` 状态。在出现故障的情况下，作业首先切换到 `failing` 状态，取消所有正在运行任务的地方。如果所有作业顶点已达到最终状态，并且作业不可重新启动，那么作业转换 `failed` 状态。如果作业可以重新启动，那么它将进入 `restarting` 状态。一旦作业重新启动完成后，将进入 `ctreated` 状态。

在用户取消作业的情况下，将进入 `cancelling` 状态。这也需要取消所有正在运行的任务。一旦所有正在运行的任务都达到最终状态，作业将转换到 `cancelled` 状态。

不同于表示全局终端状态以及触发清理工作的 `finished`， `canceled` 和 `failed` 状态，`suspended` 状态只是本地终端。本地终端的意思是作业的执行已在相应的 `JobManager` 上终止，但 `Flink` 集群的另一个 `JobManager` 可从持久性 `HA` 存储中检索作业并重新启动作业。因此，进入 `suspended` 状态的作业将不会完全清理。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink_internals_job_scheduling-3.png?raw=true)

在 `ExecutionGraph` 的执行过程中，每个并行任务都经历了从 `ctreated` 到 `finished` 或 `failed` 的多个阶段。下图说明了它们之间的状态和可能的转换。任务可以执行多次（例如在故障恢复过程中）。出于这个原因， `ExecutionVertex` 执行跟踪信息保存在 [Execution](https://github.com/apache/flink/blob/master//flink-runtime/src/main/java/org/apache/flink/runtime/executiongraph/Execution.java) 中。 每个 `ExecutionVertex` 都有一个当前的`Execution`，以及之前的`Executions`。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/flink_internals_job_scheduling-4.png?raw=true)


备注:
```
Flink版本:1.4
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/internals/job_scheduling.html
