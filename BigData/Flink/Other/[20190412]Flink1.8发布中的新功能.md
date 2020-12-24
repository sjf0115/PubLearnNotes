
Flink 1.8.0 版本与 1.xy 版本使用 @Public 注解注释的API兼容。该版本现已发布，我们鼓励大家下载该[版本](https://flink.apache.org/downloads.html)并查看最新的[文档](https://ci.apache.org/projects/flink/flink-docs-release-1.8/)。

借助 Flink 1.8.0 我们更加接近实现快速数据处理以及以无缝方式为 Flink 社区构建数据密集型应用程序。我们通过清理和重构 Flink 来实现这一目标，以便将来进行更有效的功能开发。这包括删除 Flink 底层分布式系统架构（FLIP-6）遗留运行时组件，以及Table API上的重构，为将来添加Blink增强功能做好准备（[FLINK-11439](https://issues.apache.org/jira/browse/FLINK-11439)）。

此版本包含了一些重要的新功能和 Bug 修复。其中最有趣的内容如下所示。有关更多详细信息，请参阅完整的[更改日志](https://issues.apache.org/jira/secure/ReleaseNote.jspa?projectId=12315522&version=12344274)和发行说明。

### 1. 新功能和改进

#### 1.1 最终版Schema Evolution Story

此版本完成了社区驱动的工作，为Flink管理的用户状态提供模式演变故事。 这是一项跨越2个版本的工作，从1.7.0开始，引入了对Avro状态模式演进的支持以及改进的序列化兼容性抽象。

#### 1.2 基于TTL持续清除旧状态

> [FLINK-7811](https://issues.apache.org/jira/browse/FLINK-7811)

我们在 Flink 1.6（[FLINK-9510](https://issues.apache.org/jira/browse/FLINK-9510)）中为 Keyed State 引入了TTL（生存时间）。此功能可以清除状态，并使 Keyed State 条目在一定时间后无法访问。除此之外，在编写保存点/检查点时，现在也会清除状态。

Flink 1.8 引入了对 RocksDB 状态后端（[FLINK-10471](https://issues.apache.org/jira/browse/FLINK-10471)）和堆状态后端（[FLINK-10473](https://issues.apache.org/jira/browse/FLINK-10473)）中旧条目的持续清理。这意味着旧条目会不断被清理（根据TTL设置）。

#### 1.3 使用用户定义的函数和聚合进行SQL模式检测

MATCH_RECOGNIZE子句的支持已由多个功能扩展。 添加用户定义的函数允许在模式检测期间使用自定义逻辑（FLINK-10597），而添加聚合允许更复杂的CEP定义，例如以下（FLINK-7599）。

#### 1.4 兼容RFC的CSV格式

> [FLINK-9964](https://issues.apache.org/jira/browse/FLINK-9964)

现在可以以兼容RFC-4180标准的CSV表格式读取和写入SQL表。该格式对于一般 DataStream API 用户同样适用。

#### 1.5 新的可以直接访问ConsumerRecord的KafkaDeserializationSchema

> [FLINK-8354](https://issues.apache.org/jira/browse/FLINK-8354)

对于 Flink KafkaConsumers，我们引入了一个新的 KafkaDeserializationSchema，可以直接访问 Kafka ConsumerRecord。现在，可以允许访问 Kafka 为记录提供的所有数据，包括标题。这些归入到 KeyedSerializationSchema 功能中，虽然该功能已弃用但目前仍可用。

#### 1.6 FlinkKinesisConsumer中的每个分片水印选项

> [FLINK-5697](https://issues.apache.org/jira/browse/FLINK-5697)

The Kinesis Consumer can now emit periodic watermarks that are derived from per-shard watermarks, for correct event time processing with subtasks that consume multiple Kinesis shards.

#### 1.7 为DynamoDB Streams捕获表变更的新消费者

> [FLINK-4582](https://issues.apache.org/jira/browse/FLINK-4582)

FlinkDynamoDBStreamsConsumer 是 Kinesis 消费者的变体，支持从 DynamoDB 表中检索类似CDC的流。

#### 1.8 支持用于子任务协调的全局聚合

> [FLINK-10887](https://issues.apache.org/jira/browse/FLINK-10887)

GlobalAggregateManager 设计跟踪全局数据源 Watermark 的解决方案，允许在并行子任务之间共享信息。这个功能将集成到用于 Watermark 同步的流式连接器中，也可以配合用户自定义聚合器用于其他目的。

### 2. 重要变化

#### 2.1 Flink捆绑Hadoop库的变化

> [FLINK-11266](https://issues.apache.org/jira/browse/FLINK-11266)

包含 Hadoop 的便捷二进制文件不再发布。如果部署依赖于 flink-dist 中的 flink-shaded-hadoop2，则必须从下载页面的可选组件部分手动下载预打包的 Hadoop jar 并将其复制到 `/lib` 目录下。或者，可以通过打包 flink-dist 并激活 include-hadoop maven 配置文件来构建包含 hadoop 的 Flink 包。由于 Hadoop 默认不再包含在 flink-dist 中，因此在打包 flink-dist 时指定 `-DwithoutHadoop` 不再影响构建。

#### 2.2 FlinkKafkaConsumer根据Topic规范过滤已恢复的分区

> [FLINK-10342](https://issues.apache.org/jira/browse/FLINK-10342)

从Flink 1.8.0开始，FlinkKafkaConsumer现在总是过滤掉已恢复的分区，这些分区不再与要在还原的执行中预订的指定主题相关联。在以前版本的FlinkKafkaConsumer中不存在此行为。如果您希望保留以前的行为，请使用FlinkKafkaConsumer上的disableFilterRestoredPartitionsWithSubscribedTopics（）配置方法。

考虑这个例子：如果你有一个KFS卡消费者从主题A消费，你做了一个保存点，然后改变你的Kafka消费者，而不是从主题B消费，然后从保存点重新启动你的工作。在此更改之前，您的使用者现在将同时使用主题A和B，因为它存储在消费者从主题A消耗的状态中。通过更改，您的使用者将仅在恢复后使用主题B，因为它现在过滤主题使用配置的主题存储在状态中。

#### 2.3 Table API的Maven模块中的更改

> [FLINK-11064](https://issues.apache.org/jira/browse/FLINK-11064)

之前具有 `flink-table` 依赖关系的用户需要将其依赖关系更新为依赖 `flink-table-planner`以及正确的 `flink-table-api- *` ，是选择 `flink-table-api-java-bridge` 还是 `flink-table-api-scala-bridge` 具体取决于使用的 Java 还是 Scala。

### 3. 已知问题

#### 3.1 丢弃的检查点可能导致任务失败

> [FLINK-11662](https://issues.apache.org/jira/browse/FLINK-11662)

存在可能导致错误检查点故障的竞争条件。通常发生在当一个作业从保存点或检查点重新启动需要很长时间的数据源。如果你发现随机的检查点失败似乎没有很好的解释，你可能是受到了影响。有关详细信息，请参阅Jira问题以及问题的解决方法。


原文:[What's new in Flink 1.8.0?](https://www.ververica.com/blog/whats-new-in-flink-1.8)
