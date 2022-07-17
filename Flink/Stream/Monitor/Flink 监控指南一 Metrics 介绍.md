---
layout: post
author: sjf0115
title: Flink 监控指南一 Metrics 介绍
date: 2022-07-16 10:02:21
tags:
  - Flink

categories: Flink
permalink: flink-monitor-part-one-metric-base
---

## 1. 什么是 Metrics？

Flink 提供的 Metrics 可以在 Flink 内部收集一些指标，比如系统指标的 CPU、内存、线程、JVM、网络、IO、GC 以及任务运行组件 JM、TM、Slot、作业、算子等相关指标。通过这些指标让开发人员更好地理解作业或者集群的状态。由于集群运行后很难发现内部的实际状况，跑得快慢，是否有异常等，开发人员无法实时查看所有的 Task 日志，比如作业很大或者有很多作业的情况下，该如何处理？此时 Metrics 可以很好的帮助开发人员了解作业的当前状况。

## 2. Metrics 类型

Flink 一共提供了四种 Metric：Counter、Gauge、Histogram、Meter：
- Counter：计数器，是最常用的一种 Metric。写过 MapReduce 作业的开发人员应该很熟悉 Counter，其含义都是一样的，就是对一个计数器进行累加。例如，Flink 算子的接收记录总数(numRecordsIn)和发送记录总数(numRecordsOut)就属于 Counter 类型。
- Gauge：测量器，是最简单的一种 Metric，它直接反映了一个值，根据需要可以提供任何类型的值。例如 Status.JVM.Memory.Heap.Used 当前堆内存使用量就属于 Gauge 类型，每次实时的暴露一个 Gauge，Gauge 当前值就是堆内存使用量。
- Meter：计量器，用来统计吞吐量和单位时间内发生'事件'的次数。它相当于求一种速率，即事件次数除以使用的时间。例如记录每秒接收记录数（numRecordsInPerSecond）和每秒输出记录数（numRecordsOutPerSecond）就属于 Meter 类型。
- Histogram：直方图，用来统计数据的分布。例如，分位数（Quantile）、均值、标准偏差（StdDev）、最大值、最小值等，其中最重要一个是统计算子的延迟。此项指标会记录数据处理的延迟信息，对任务监控起到很重要的作用。

## 3. Metrics 作用范围

Flink 的指标体系是按树形结构划分，每个 Metric 都被分配一个标识符，并以这个标识符进行上报。标识符由3部分组成：
- 注册 Metric 时用户提供的名称
- 可选的用户定义的作用域
- 系统提供的作用域

例如，如果`A.B`是系统作用域，`C.D`是用户作用域，`E`是名称，那么 Metric 的标识符是 `A.B.C.D.E`。举例说明：以算子的指标组结构为例，其默认为：
```
<host>.taskmanager.<tm_id>.<job_name>.<operator_name>.<subtask_index>
```
算子的输入记录数指标为：
```
localhost.taskmanager.1234.wordcount.flatmap.0.numRecordsIn
```
> 你可以通过在 `conf/flink-conf.yaml` 中修改 `metrics.scope.delimiter` 参数来修改使用什么分隔符(默认为:`.`)。

## 4. Metrics 上报机制

为了保证对 Flink 集群和作业的运行状态进行监控，Flink 提供了两种 Metrics 上报的方式：内置 Reporter 主动推送和 REST API 被动拉取：
- 被动拉取 REST API：外部系统通过调用 Flink 提供的 Rest API 接口，可以返回集群、组件、作业、Task、算子的状态。Flink 的 WebUI 就是采用的 REST API 的方式获取指标。
- 主动推送 MetricReport：Flink Metrics 通过在 conf/flink-conf.yaml 中配置一个或者一些 reporters，将指标暴露给一个外部系统。这些 reporters 将在每个 job 和 task manager 启动时被实例化。

### 4.1 被动拉取 REST API

REST API 是 RESTful 接口，接受 HTTP 请求并返回 JSON 数据响应。通过解析 JSON 数据来获取集群、作业、算子等监控信息。REST API 使用 Netty 和 Netty Router 库来处理 REST 请求和转换 URL。

例如，如下是用 Postman 等 REST 工具获得的 JobManager 的通用指标：
```
GET /jobmanager/metrics

# Response
[
{"id":"taskSlotsAvailable"},
{"id":"taskSlotsTotal"},
{"id":"Status.JVM.Memory.Mapped.MemoryUsed"},
{"id":"Status.JVM.CPU.Time"},
......
{"id":"Status.JVM.Memory.Heap.Used"},
{"id":"Status.JVM.Memory.Heap.Max"},
{"id":"Status.JVM.ClassLoader.ClassesUnloaded"}
]
```

> REST 支持接口可以参考[]()

### 4.2 主动推送 MetricReport

Metric Reporter 通过一个单线程的线程池定时调用 Scheduled 接口的实现类的 report 函数完成定时上报数据，默认每 10 秒上报一次。flink-metrics 模块中通过实现 MetricReporter 接口实现了对 Datadog、Graphite、Influxdb、JMX、Prometheus、Slf4j 日志、StatsD（网络守护进程）等日志模块和监控系统的支持。以 Prometheus 为例，简单说明一下 Flink 是如何以主动推送方式上报监控指标的。

![]()

如需支持自定义 Reporter，例如 KafkaReporter，我们需要实现 MetricReporter、Scheduled接口并重写 report 方法即可。MetricRegistry 是在 flink-rumtime 模块 ClusterEntrypoint 类 initializeServices 方法中完成了对 Reporters 的注册。

## 5. Metrics 使用场景

一般会用 Metrics 来做自动化运维和性能分析。

### 5.1 自动化运维

自动化运维具体怎么做呢？
- 收集监控数据：首先要有监控数据作为决策依据，可以利用 Metric Reporter 收集 Metrics 到存储/分析系统 (例如 TSDB)，或者直接通过 RESTful API 获取。
- 定制监控规则：关注关键指标，Failover、Checkpoint,、业务 Delay 信息。定制规则用途最广的是可以用来报警，省去很多人工的工作，并且可以定制 failover 多少次时需要人为介入。
- 自动报警：当出现问题时，有钉钉报警、邮件报警、短信报警、电话报警等通知工具。
- 运维大盘：自动化运维的优势是可以通过大盘、报表的形式清晰的查看数据，通过大盘时刻了解作业总体信息，通过报表分析优化。

### 5.2 性能分析

性能分析一般遵循如下的流程：
首先从发现问题开始，如果有 Metrics 系统，再配上监控报警，就可以很快定位问题。然后对问题进行剖析，大盘看问题会比较方便，通过具体的 System Metrics 分析，缩小范围，验证假设，找到瓶颈，进而分析原因，从业务逻辑、JVM、 操作系统、State、数据分布等多维度进行分析；如果还不能找到问题原因，就只能借助 profiling 工具了。

“任务慢，怎么办？”可以称之为无法解答的终极问题之一。我们以这个例子为例，具体说明如何进行剖析并发现问题的。这种问题是系统框架问题，比如看医生时告诉医生身体不舒服，然后就让医生下结论。而通常医生需要通过一系列的检查来缩小范围，确定问题。同理，任务慢的问题也需要经过多轮剖析才能得到明确的答案。

#### 5.2.1 发现问题

比如下图 failover 指标，线上有一个不是 0，其它都是 0，此时就发现问题了：

![]()

再比如下图 Input 指标正常都在四、五百万，突然跌成 0，这里也存在问题：

![]()

业务延时问题如下图，比如处理到的数据跟当前时间比对，发现处理的数据是一小时前的数据，平时都是处理一秒之前的数据，这也是有问题的：

![]()

#### 5.2.2 缩小范围定位瓶颈

当出现一个地方比较慢，但是不知道哪里慢时，如下图红色部分，OUTQ 并发值已经达到 100% 了，其它都还比较正常，甚至优秀。到这里生产者消费者模型出现了问题，生产者 INQ 是满的，消费者 OUT_Q 也是满的，从图中看出节点 4 已经很慢了，节点 1 产生的数据节点 4 处理不过来，而节点 5 的性能都很正常，说明节点 1 和节点 4 之间的队列已经堵了，这样我们就可以重点查看节点 1 和节点 4，缩小了问题范围。

![]()

500 个 InBps 都具有 256 个 PARALLEL ，这么多个点不可能一一去看，因此需要在聚合时把 index 是第几个并发做一个标签。聚合按着标签进行划分，看哪一个并发是 100%。在图中可以划分出最高的两个线，即线 324 和线 115，这样就又进一步的缩小了范围。

![]()

利用 Metrics 缩小范围的方式如下图所示，就是用 Checkpoint Alignment 进行对齐，进而缩小范围，但这种方法用的较少。

![]()

#### 5.2.3 多维度分析

分析任务有时候为什么特别慢呢？当定位到某一个 Task 处理特别慢时，需要对慢的因素做出分析。分析任务慢的因素是有优先级的，可以从上向下查，由业务方面向底层系统。因为大部分问题都出现在业务维度上，比如查看业务维度的影响可以有以下几个方面，并发度是否合理、数据波峰波谷、数据倾斜；其次依次从 Garbage Collection、Checkpoint Alignment、State Backend 性能角度进行分析；最后从系统性能角度进行分析，比如 CPU、内存、Swap、Disk IO、吞吐量、容量、Network IO、带宽等。

## 6. 如何使用 Metrics

### 6.1 System Metrics

System Metrics，将整个集群的状态已经涵盖得非常详细。具体包括以下方面：
Master 级别和 Work 级别的 JVM 参数，如 load 和 time；其 Memory 划分也很详细，包括 heap 的使用情况、non-heap 的使用情况、direct 的使用情况，以及 mapped 的使用情况；Threads 可以看到具体有多少线程；还有非常实用的 Garbage Collection。
Network 使用比较广泛，当需要解决一些性能问题的时候，Network 非常实用。Flink 不只是网络传输，还是一个有向无环图的结构，可以看到它的每个上下游都是一种简单的生产者消费者模型。Flink 通过网络相当于标准的生产者和消费者中间通过有限长度的队列模型。如果想要评估定位性能，中间队列会迅速缩小问题的范围，能够很快的找到问题瓶颈。

### 6.2 User-defined Metrics

除了系统的 Metrics 之外，Flink 支持自定义 Metrics ，即 User-defined Metrics。上文说的都是系统框架方面，对于自己的业务逻辑也可以用 Metrics 来暴露一些指标，以便进行监控。

User-defined Metrics 现在提及的都是 datastream 的 API，table、sql 可能需要 context 协助，但如果写 UDF，它们其实是大同小异的。

Datastream 的 API 是继承 RichFunction ，继承 RichFunction 才可以有 Metrics 的接口。然后通过 RichFunction 会带来一个 getRuntimeContext().getMetricGroup().addGroup(…) 的方法，这里就是 User-defined Metrics 的入口。通过这种方式，可以自定义 user-defined Metric Group。如果想定义具体的 Metrics，同样需要用getRuntimeContext().getMetricGroup().counter/gauge/meter/histogram(…) 方法，它会有相应的构造函数，可以定义到自己的 Metrics 类型中。


参考：
- [Apache Flink 进阶（八）：详解 Metrics 原理与实战](https://mp.weixin.qq.com/s/Lo5a-R9n_uw-bx7CbwL_cQ)
- []()
