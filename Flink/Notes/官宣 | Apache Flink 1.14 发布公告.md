> 原文：[官宣｜Apache Flink 1.14.0 发布公告](https://mp.weixin.qq.com/s/ctP9ImWHuFqAHKJv3jhIgg)

在 Apache 软件基金会近期发布的年度报告中，Apache Flink 再次跻身最活跃项目前 5 名！该项目最新发布的 1.14.0 版本同样体现了其非凡的活跃力，囊括了来自超过 200 名贡献者的 1000 余项贡献。整个社区为项目的推进付出了持之以恒的努力，我们引以为傲。

新版本在 SQL API、更多连接器支持、Checkpoint 机制、PyFlink 等多个方面带来了大量的新特性与改进。其中一个主要的改进是针对流批一体的使用体验。我们相信，在实践中，对无界的数据流的处理与对有界的批数据的处理是密不可分的，因为很多场景都需要在处理实时数据流的同时处理来自各种数据源的历史数据。例如开发新应用时的数据探索、新应用的状态初始化、用于流式应用的训练模型、升级或修复后的数据重处理等。

在 Flink 1.14 中，我们终于可以在同一个应用当中混合使用有界流和无界流：Flink 现在支持对部分运行、部分结束的应用（部分算子已处理到有界输入数据流的末端）做 Checkpoint。此外，Flink 在处理到有界数据流末端时会触发最终 Checkpoint，以确保所有计算结果顺利提交到 Sink。

批执行模式现在支持在同一应用中混合使用 DataStream API 和 SQL/Table API（此前仅支持单独使用 DataStream API 或 SQL/Table API）。

我们更新了统一的 Source 和 Sink API，并已开始围绕统一的 API 整合连接器生态。我们新增了混合 Source 可在多个存储系统间过渡。你现在可以实现诸如先从 Amazon S3 中读取旧的数据再无缝切换到 Apache Kafka 这样的处理。

此外，这一版本朝着我们将 Flink 打造得更加自调易用、无需大量流处理特定知识的目标又迈进了一步。作为向此目标迈出的第一步，我们在上个版本中引入了[被动弹性伸缩模式](https://flink.apache.org/news/2021/05/03/release-1.13.0.html#reactive-scaling)。现在，我们又新增了对网络内存的自动调整（即缓冲区去膨胀）。这一特性能在保持高吞吐、不增加 Checkpoint 大小的前提下，加速高负载时的 Checkpoint。该机制通过不断调整网络缓冲区的大小，能够以最少的缓冲数据达到最佳的吞吐效率。更多详情请参考缓冲区去膨胀章节。

新版本中有许多来自各个组件的新特性与改进，我们将在下文介绍。与此同时，我们也告别了一些在最近的版本中逐渐被取代、废弃的组件和功能。最具代表性的是，新版本中移除了旧版 SQL 查询引擎和对 Apache Mesos 的集成。

我们希望你喜欢这个新版本，同时迫切地想了解你的使用体验：这一版本解决了哪些此前尚未解决的问题，满足了哪些新场景？

## 1. 流批一体的处理体验

Flink 的一个独特之处是其对流和批处理的统一：使用同一套 API、同一个可支持多种执行范式的运行时。

正如在前文中提到的，我们相信流处理和批处理是密不可分的。下面这段话来自一份关于 [Facebook 流式数据处理的报告]( https://research.fb.com/wp-content/uploads/2016/11/realtime_data_processing_at_facebook.pdf)，很好地呼应了这一观点。

> 流处理与批处理并不是非此即彼的选择。最初，Facebook 所有数据仓库的处理都是批处理。我们在大约 5 年前开始研发 Puma 和 Swift。正如我们在 […] 章节所展示的，混合使用流处理和批处理能够为较长的处理流程节约数个小时。

利用同一引擎处理实时和历史数据还可以确保语义的一致性，使结果具有更好的可比性。这里有一篇[关于阿里巴巴使用 Apache Flink 生成统一的、一致的业务报告的文章](https://www.ververica.com/blog/apache-flinks-stream-batch-unification-powers-alibabas-11.11-in-2020)。

此前的版本已经可以实现流批一体的数据处理。新版本在这方面增加了针对更多使用场景的新特性，以及一系列使用体验的改进。

### 1.1 有界流 Checkpoint 机制

Flink 的 Checkpoint 机制原本只支持在应用 DAG 中的所有任务都处于运行状态时创建 Checkpoint。这意味着让应用同时读取有界和无界数据源在实质上是不可能的。此外，以流式（而非批式）处理有界输入数据的应用，在数据将要处理完、部分任务结束时将不再做 Checkpoint。这使得最后一部分输出数据无法被提交到要求精确一次语义的 Sink 中，造成业务延迟。

通过 [FLIP-147](https://cwiki.apache.org/confluence/display/FLINK/FLIP-147%3A+Support+Checkpoints+After+Tasks+Finished)，Flink 支持在部分任务结束后创建 Checkpoint，以及在有界流处理结束后触发最终 Checkpoint 以确保在作业结束时将所有输出结果提交到 Sink（与 stop-with-savepoint 类似）。

该特性可通过在配置中添加 execution.checkpointing.checkpoints-after-tasks-finish.enabled: true 启用。出于让用户自主选择并试用重大新特性的传统，这一特性在 Flink 1.14 中没有默认启用。我们希望在下个版本中将其作为默认模式。

背景：处理有界数据时，尽管人们通常倾向于使用批处理模式，仍有一些情况需要用到流处理模式。例如，Sink 可能只支持流模式（即 Kafka Sink），或者应用希望尽量发挥流处理固有的近时间排序特性（例如 [Kappa+ 架构](https://www.youtube.com/watch?v=4qSlsYogALo&t=666s)）。

DataStream 和 Table/SQL 混合应用的批执行模式

SQL 和 Table API 正在成为新项目的默认起点，其天然的声明式特点和丰富的内置类型与操作使应用开发变得简单快速。然而，开发人员遇到一些特定的、事件驱动的业务逻辑，SQL 的表达能力无法满足（或不适合强行用 SQL 来表达）的情况也并不罕见。

此时，自然的做法是插入一段有状态的 DataStream API 描述的逻辑，再切换回 SQL。

在 Flink 1.14 中，有界的批执行模式的 SQL/Table 应用可将其中间数据表转换成数据流，经过由 DataStream API 定义的算子处理，再转换回数据表。其内部原理是，Flink 构建了一个由优化的声明式 SQL执行和 DataStream 批执行混合而成的数据流 DAG。详见[相关文档](https://nightlies.apache.org/flink/flink-docs-release-1.14/zh/docs/dev/table/data_stream_api/)。

混合 Source

全新的[混合 Source][https://nightlies.apache.org/flink/flink-docs-release-1.14/zh/docs/connectors/datastream/hybridsource/] 能够依次地从多个数据源读取数据，在不同数据源之间无缝切换，产出一条由来自多个数据源的数据合并而成的数据流。

混合 Source 针对的是从分层存储中读取数据的场景，相当于从一条跨越所有层级的数据流读取数据。例如，将新数据灌入 Kafka，并最终迁移至 S3（出于成本与效率的考量这通常是压缩的列存格式）。混合 Source 可以像读取一条连续的逻辑数据流一样，先从 S3 读取历史数据，然后转换到 Kafka 读取最新的数据。

图片


我们相信这是向着实现日志与 Kappa 架构完整前景的令人兴奋的一步。即使事件日志的陈旧部分在物理上被迁移到了不同的存储（出于成本、压缩效率、读取速度等原因），你仍可以将其视作连续的日志处理。

Flink 1.14 加入了混合 Source 的核心功能。在后续的版本中，我们希望加入更多针对典型切换策略的工具与模式。

整合 Source 和 Sink

随着新的流批统一的 Source 和 Sink API 变得稳定，我们开始了围绕这些 API 整合所有连接器的巨大努力。与此同时，我们也会让 DataStream 和 SQL / Table API 上的连接器更好地对齐，首先是DataStream API 上的 Kafka 和文件 Source、Sink。

伴随着这一努力（预计仍将持续 1-2 个版本），Flink 用户在连接外部系统时将获得更加流畅、一致的体验。

二、运维改进


缓冲区去膨胀


缓冲区去膨胀是 Flink 中的一项新技术，可以最小化 Checkpoint 的延迟和开销。它通过自动调整网络内存的用量，在确保高吞吐的同时最小化缓冲区中的数据量。



Apache Flink 在其网络栈中缓冲了一定量的数据，以便有效利用快速网络的高带宽。Flink 应用以高吞吐运行时，会使用部分（或全部）网络缓冲内存。对齐的 Checkpoint 随着数据在毫秒级的时间内流过网络缓冲区。



当 Flink 应用出现（暂时的）反压时（例如外部系统反压或遇到数据倾斜），往往会导致网络缓冲区中存放了相对应用当前吞吐（因反压而降低）所需的带宽过多的数据。更加不利的是，缓冲的数据越多意味着 Checkpoint 机制需要做越多的工作。对齐的 Checkpoint 需要等待更多的数据得到处理，非对齐的 Checkpoint 则需要持久化更多排队中的数据。



这就轮到缓冲区去膨胀登场了。它将网络栈从持有最多 X 字节的数据改为持有需要接收端 X 毫秒计算时间处理的数据。默认值是 1000 毫秒，意味着网络栈会缓冲下游任务 1000 毫秒所能处理的数据量。通过持续的测量和调整，系统能够在不断变化的情况下保持这一特性。因此，Flink 对齐式 Checkpoint 具备了稳定的、可预测的对齐时间，反压时存放在非对齐式 Checkpoint中的数据量也极大程度减少了。



图片



缓冲区去膨胀可以作为非对齐式 Checkpoint 的补充，甚至是替代选择。关于如何启用该特性，请参考[文档](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/deployment/memory/network_mem_tuning/#the-buffer-debloating-mechanism)。



细粒度资源管理


细粒度资源管理是一项新的高级功能，用于提高大型共享集群的资源利用率。



Flink 集群执行多种多样的数据处理工作负载。不同的数据处理步骤通常需要不同的资源，如计算资源、内存等。例如，大多数映射函数都比较轻量，而较大的、保留时间较长的窗口函数往往受益于大量内存。默认情况下，Flink 以粗粒度的 Slot 管理资源，一个 Slot 代表 TaskManager 的一个资源切片。一个 Slot 可以存放流式处理流程中每个算子的一个并发子任务实例，即一个 Slot 可持有一整条处理流程的并发子任务实例。通过 Slot Sharing Group，用户可以影响子任务在 Slot 上的分布。



有了细粒度资源管理，TaskManager 上的 Slot 可以动态改变大小。转换和算子指定所需的资源配置（CPU、内存、磁盘等），由 Flink 的 ResourceManager 和 TaskManager 负责从 TaskManager 的总资源中划分出指定大小的资源切片。你可以将这看做是 Flink 中的一层最小化、轻量化的资源编排。下图展示了细粒度资源管理与目前默认的共享固定大小 Slot 资源管理方式的区别。



图片



你可能会问，Flink 已经集成了 Kubernetes、Yarn 等成熟的资源编排框架，为什么还要增加这样一个新特性？有几种情况，在 Flink 内部增加一层资源管理可以显著提高资源利用率：

当 Slot 比较小时，为每个 Slot 专门申请 TaskManager 的代价是非常高的（JVM 开销、Flink 框架开销等）。Slot Sharing 通过让不同类型的算子共享 Slot，即在轻量的算子（需要较小的 Slot）和重量的算子（需要较大的 Slot）间共享资源，在一定程度上解决了这个问题。然而，这仅在所有算子的并发度相同时有较好的效果，并非总是最优的。此外，有些算子更适合单独运行（例如机器学习中负责训练的算子需要专用的 GPU资源）。

Kubernetes 和 Yarn 往往需要花费一段时间来满足资源请求，特别是在集群负载较高时。对于一些批处理作业，等待资源的时间会降低作业的执行效率。

那么什么时候应该启用这一特性呢？默认的资源管理机制适用于大多数流处理和批处理作业。如果你的作业是长时间运行的流作业或快速的批作业，其不同处理阶段需要的资源差异明显，且你已经为不同算子设置了不同的并发度，那么你可以尝试用细粒度资源管理提高资源效率。

阿里巴巴内部基于 Flink 的平台已经应用这种机制有一段时间了，在实践中集群资源利用率有着显著的提高。

关于如何使用细粒度资源管理的更多细节，请参考[文档](https://nightlies.apache.org/flink/flink-docs-release-1.14/zh/docs/deployment/finegrained_resource/)。

三、连接器


连接器指标


此版本对连接器的指标进行了标准化（详见 [FLIP-33](https://cwiki.apache.org/confluence/display/FLINK/FLIP-33%3A+Standardize+Connector+Metrics)）。在接下来的几个版本中，社区将在围绕新的统一 API 逐步翻新所有连接器的同时，同步实现标准化指标对所有连接器的覆盖。在 Flink 1.14 中，我们覆盖了 Kafka 连接器和（部分的）文件系统连接器。



连接器在 Flink 作业中是数据的出入口。如果作业未按预期运行，连接器的指标是首先要检查的部分之一。我们相信对于 Flink 应用的生产运维而言，这将是一个很好的改进。



Pulsar 连接器


此版本新增了 [Apache Pulsar](https://pulsar.apache.org/) 连接器。Pulsar 连接器支持以流和批两种执行模式从 Pulsar 主题读取数据。在 Pulsar 事务功能（自 Pulsar 2.8.0 引入）的支持下，Pulsar 连接器可以支持精确一次的数据传递语义，即使在生产者尝试重传消息时也能确保消息仅被传递给消费者一次。



为了满足不同场景下对消息顺序和规模的需求，Pulsar Source 连接器支持四种订阅类型：[独占](https://pulsar.apache.org/docs/zh-CN/concepts-messaging/#exclusive)、[共享](https://pulsar.apache.org/docs/zh-CN/concepts-messaging/#shared%E5%85%B1%E4%BA%AB)、[灾备](https://pulsar.apache.org/docs/zh-CN/concepts-messaging/#failover%E7%81%BE%E5%A4%87)、[键共享](https://pulsar.apache.org/docs/zh-CN/concepts-messaging/#key_shared)。



该连接器目前支持 DataStream API。SQL / Table API 预计将在后续版本中提供。关于如何使用 Pulsar 连接器，请参考[文档](https://nightlies.apache.org/flink/flink-docs-release-1.14/zh/docs/connectors/datastream/pulsar/)。


四、PyFlink


基于链接的性能提升


与 Java API 将任务中的转换函数、算子链接起来以避免序列化开销类似，PyFlink 现在也会将 Python 函数链接起来。对于 PyFlink，链接不仅能消除序列化开销，还能减少 Java 和 Python 进程间的 RPC 通信。这大幅提高了 PyFlink 的整体性能。



此前版本中，SQL / Table API 已经可以将 Python 函数链接起来。在 Flink 1.14中，这一优化进一步覆盖了 Python DataStream API 中的 cPython 函数。



环回调试模式


通常情况下，Python 函数是由独立于 Flink JVM 之外的 Python 进程执行的。这一架构导致对 Python 代码的调试比较困难。



PyFlink 1.14 引入了环回模式，在本地部署模式下自动启用。该模式下，用户自定义 Python 函数将由运行客户端的 Python 进程执行，该进程是启动 PyFlink 应用的入口，负责执行用于构建数据流 DAG 的所有 DataStream API 和 Table API 代码。用户现在本地运行 PyFlink 作业时，可以通过在 IDE 中设置断点的方式方便地调试 Python 函数。



其他改进


PyFlink 还有很多其他改进，例如支持用 Yarn Application 模式执行作业、支持使用 tgz 压缩格式的 Python 归档文件等。更多详情请参考 [Python API 文档](https://nightlies.apache.org/flink/flink-docs-release-1.14/zh/docs/dev/python/overview/)。


五、告别旧版 SQL 引擎和 Mesos 支持


维护一个开源项目也意味着有时要告别一些受人喜爱的功能特性。


在两年前我们将 Blink SQL 引擎加入到 Flink 时，就已明确它终将取代原本的 SQL 引擎。Blink 速度更快，功能也更加完整。最近一年，Blink 已成为默认的 SQL 引擎。在 Flink 1.14，我们终于将旧版 SQL 引擎的所有代码移除了。这让我们得以移除许多过时的接口，避免用户在实现自定义连接器和函数时产生不知该用哪个接口的困惑。这还有助于我们今后更加快速的迭代 SQL 引擎。



此版本还移除了对 Apache Mesos 的集成，因为我们发现几乎没有用户仍对这一特性感兴趣，同时也缺少足够的贡献者愿意帮助维护这部分系统。Flink 1.14 将不再能够在不依赖于像 Marathon 这样的辅助项目的情况下运行在 Mesos 上，同时 Flink 的 ResourceManager 也不再支持根据工作负载的资源需求从 Mesos 动态申请、释放资源。


六、升级说明


我们已努力让版本升级变得尽可能顺利，但仍有一些改动需要用户在升级 Flink 版本时对应用的一些部分做出调整。有关升级过程中可能需要做出的调整及确认，请参阅[发版公告](https://nightlies.apache.org/flink/flink-docs-release-1.14/release-notes/flink-1.14/)。


> 原文连接：https://flink.apache.org/news/2021/09/29/release-1.14.0.html
