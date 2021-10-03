---
layout: post
author: sjf0115
title: Flink 1.9 发布中的新功能与改进
date: 2019-08-22 20:08:12
tags:
  - Flink

categories: Flink
permalink: apache-flink-release-1.9.0
---

2021年8月22日，Apache Flink 社区宣布 Apache Flink 1.9.0 正式发布。这也是阿里内部版本 Blink 合并入 Flink 后的首次版本发布。Apache Flink 项目的目标是开发一个流处理系统，以统一和支持多种形式的实时和离线数据处理应用程序以及事件驱动的应用程序。在 1.9 版本中，社区在这方面取得了巨大的进步，将 Flink 的流处理和批处理能力集成在了一个统一的 Runtime 之上。

此次版本更新带来的重大功能包括批处理作业的批式恢复以及用于 Table API 和 SQL 查询的基于 Blink 的新查询引擎（预览版）。我们还很高兴地宣布推出可用的 State Processor API，这是社区最迫切的功能之一，该 API 可以让用户能够使用 Flink DataSet 作业读取和写入 Savepoint。最后，Flink 1.9 还包括一个重新设计的 WebUI、新的 Python Table API（预览版）以及与 Apache Hive 生态系统的集成（预览版）。

这篇博文主要介绍 Apache Flink 1.9 版本主要的新功能、改进、需要注意的重要变化以及未来的发展计划。有关更多详细信息，请查看完整的[版本变更日志](https://issues.apache.org/jira/secure/ReleaseNote.jspa?projectId=12315522&version=12344601)。

现在可以通过 Flink 项目的[下载页面](https://flink.apache.org/downloads.html)以及更新的[文档](https://nightlies.apache.org/flink/flink-docs-release-1.9/)获得此版本的二进制分发和源工件。Flink 1.9 与之前的 1.x 版本的 API 兼容，用于使用 @Public 注释注释的 API。

## 1. 新功能和改进

### 1.1 细粒度批作业恢复

批作业（DataSet、Table API 和 SQL）从失败的 Task 恢复的时间被显著减少。在 Flink 1.9 之前，批处理作业中某个 Task 失败会将所有 Task 取消并重新启动整个作业来恢复，即作业从头开始，所有进度都会废弃。在 1.9 版本中，Flink 可以配置为只恢复在同一故障区中的那些任务。故障区是指通过 Pipelined 数据交换方式连接的一组 Task。因此，作业中 batch-shuffle 的连接定义了故障区的边界。有关更多详细信息，请参见 [FLIP-1](https://cwiki.apache.org/confluence/display/FLINK/FLIP-1+%3A+Fine+Grained+Recovery+from+Task+Failures)。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/apache-flink-release-1.9.0-1.png?raw=true)

要使用这种新的故障策略，我们需要在 flink-conf.yaml 文件中进行如下配置：
```
jobmanager.execution.failover-strategy: region
```
> 注意：Flink 1.9 发布包中默认就已经包含了该配置项，如果是从之前版本升级上来，复用之前的配置，则需要手动加上该配置。

除此之外，还需要在 ExecutionConfig 中将批处理作业的 ExecutionMode 设置成 BATCH，这样批作业才能有多个故障区。'Region' 故障策略也能同时提升 'embarrassingly parallel' 类型的流作业恢复速度，即不包含像 keyBy、rebalance 等 shuffle 的作业。当这种作业在恢复时，只有受影响的 Pipeline（故障区）的 Task 需要重启。对于其他类型的流作业，故障恢复行为与之前的版本一样。

### 1.2 State Processor API

在 Flink 1.9 之前，从外部访问作业的状态仅局限于 Queryable State 的实验性功能。此版本中引入了一种新的强大类库，使用批处理 DataSet 来读取、写入、和修改状态快照。实践中，这意味着：
- Flink 作业状态可以通过从外部系统读取数据，例如，外部数据库，并将其转换为 Savepoint 来引导。
- 可以通过 Flink 批处理 API（DataSet、Table、SQL）来查询 Savepoint 中的状态。例如，分析相关的状态模式或者检查状态差异以支持应用程序审核或故障排查。
- Savepoint 中的状态 schema 可以离线迁移了，而之前只能在访问状态时在线迁移。
- Savepoint 中的无效数据可以被识别出来并纠正。

新的 State Processor API 覆盖了所有类型的快照：Savepoint，全量 Checkpoint 以及增量 Checkpoint。有关更多详细信息，请参见 [FLIP-43](https://cwiki.apache.org/confluence/display/FLINK/FLIP-43%3A+State+Processor+API)。

### 1.3 Stop-with-Savepoint

[带 Savepoit 取消作业](https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/ops/state/savepoints/)是停止/重启、新分支以及升级 Flink 作业的一种常见操作。然而，现有的实现并不能为 Exactly-Once Sink 输出到外部存储系统的数据做持久化。为了在停止作业时改进端到端语义，Flink 1.9 引入了一种新的 SUSPEND 模式，可以带 Savepoint 停止作业，保证了输出数据的一致性。我们可以使用 Flink 的 CLI 客户端暂停作业，如下所示：
```
bin/flink stop -p [:targetDirectory] :jobId
```
最终作业的状态会在成功时设置成 FINISHED 状态，方便用户区别操作是否失败。[FLIP-34](https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=103090212) 中提供了更多详细信息。

### 1.4 Flink WebUI 重构

在讨论了 Flink WebUI 现代化内部实现，决定使用 Angular 最新的稳定版来重建（从 Angular 1.x 升级到 7.x）。重新设计的版本是 1.9.0 中的默认版本，但是有一个链接可以切换到旧的 WebUI。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/apache-flink-release-1.9.0-2.png?raw=true)

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/apache-flink-release-1.9.0-3.png?raw=true)

### 1.5 新 Blink SQL 查询处理器的预览

在 Blink 捐赠给 Apache Flink 之后，社区就致力于为 Table API 和 SQL 集成 Blink 的查询优化器和 Runtime。第一步，我们将 flink-table 单模块重构成了多个小模块（[FLIP-32](https://cwiki.apache.org/confluence/display/FLINK/FLIP-32%3A+Restructure+flink-table+for+future+contributions)）。这对于 Java 和 Scala API 模块、优化器、以及 Runtime 模块来说，有了一个更清晰的分层以及定义明确的接口。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/apache-flink-release-1.9.0-4.png?raw=true)

接下来，我们扩展 Blink 的 planner 来实现新的优化器接口，这样现在有两个可插拔的查询处理器来执行 Table API 和 SQL 语句：1.9 之前的 Flink 处理器以及新的基于 Blink 的查询处理器。基于 Blink 的查询处理器提供更好的 SQL 覆盖率（1.9 完整支持 TPC-H，TPC-DS 的支持计划在下一个版本实现）并通过更广泛的查询优化（基于成本的执行计划选择和更多的优化规则）、改进的代码生成机制、和调优过的算子实现来提升批处理查询的性能。基于 Blink 的查询处理器还提供了更强大的流运行器，包括一些新功能（例如，维表 Join、TopN、去重）、聚合场景的数据倾斜问题优化以及更有用的内置函数。

> 注意：查询处理器的语义和支持的操作集大部分是一致的，但并不完全一致。

但是，Blink 查询处理器的集成还没有完全完成。因此，在 Flink 1.9 版本中，1.9 之前的 Flink 处理器仍然是默认处理器，并推荐用于生产中。我们可以在创建 TableEnvironment 时通过 EnvironmentSettings 配置来启用 Blink 处理器。被选择的处理器必须要在正在执行的 Java 进程的类路径中。对于集群设置，两个查询处理器都会自动加载默认配置。在 IDE 运行查询时，我们需要在项目中显式添加 planner 依赖项。

### 1.6 Table API 和 SQL 的其他改进

除了围绕 Blink planner 的令人兴奋的进展外，社区还对一些接口进行了一整套的改进，包括：
- 为 Java 用户去除 Table API / SQL 的 Scala 依赖 （[FLIP-32](https://cwiki.apache.org/confluence/display/FLINK/FLIP-32%3A+Restructure+flink-table+for+future+contributions)）：作为 flink-table 模块重构和拆分工作的一部分，为 Java 和 Scala 创建了两个单独的 API 模块。对于 Scala 用户，没有什么真正改变，不过 Java 用户现在在使用 Table API 和 SQL 时，可以不用再引入 Scala 依赖了。
- Table API / SQL 的类型系统重构（[FLIP-37](https://cwiki.apache.org/confluence/display/FLINK/FLIP-37%3A+Rework+of+the+Table+API+Type+System)）：社区实现了一个[新的数据类型系统](https://nightlies.apache.org/flink/flink-docs-release-1.9/dev/table/types.html#data-types)，将 Table API 从 Flink TypeInformation 中分离出来，并提高其对 SQL 标准的遵从性。不过还在进行中，预计将在下一版本完工。在 Flink 1.9 中，UDF 还没有移植到新的类型系统上。
- Table API 的多行多列转换（[FLIP-29](https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=97552739)）：Table API 扩展了一组支持多行和多列输入和输出的转换功能。这些转换能够极大简化处理逻辑的实现，如果使用关系运算符来实现就会相对麻烦。
- 崭新的统一的 Catalog API([FLIP-30](https://cwiki.apache.org/confluence/display/FLINK/FLIP-30%3A+Unified+Catalog+APIs))：我们重新设计了 Catalog API 以存储元数据并统一处理内部和外部 Catalog。这项工作虽然主要是为了 Hive 集成而发起的，但同时也全面提升了 Flink 在管理 Catalog 元数据的整体便利性。除了改进 Catalog 接口外，我们还扩展了它们的功能。以前 Table API 或 SQL 查询的表都是临时的。在 Flink 1.9 中，使用 SQL DDL 语句注册的表的元数据可以保存在 Catalog 中。这意味着您可以将一个由 Kafka 主题支持的表添加到 Metastore Catalog，然后当我们的 Catalog 连接到 Metastore 时可以查询该表。
- SQL API 中的 DDL 支持 （[FLINK-10232](https://issues.apache.org/jira/browse/FLINK-10232)）：到目前为止，Flink SQL 仅支持 DML 语句（例如，SELECT、INSERT）。外部表（表源和接收器）必须通过 Java/Scala 代码或配置文件进行注册。 对于 1.9，我们添加了对 SQL DDL 语句的支持以注册和删除表和视图（CREATE TABLE、DROP TABLE）。不过目前还没有增加流特定的语法扩展来定义时间戳抽取和 watermark 生成策略等。流式的需求也将会在下一版本中完整支持。

### 1.7 Hive 集成预览

Apache Hive 在 Hadoop 生态系统中被广泛用于存储和查询大量结构化数据。除了作为查询处理器之外，Hive 还提供了一个名为 Metastore 的 Catalog 来管理和组织大型数据集。查询处理器的一个常见集成点是与 Hive 的 Metastore 集成，以便能够利用 Hive 管理的数据。

最近，社区开始为 Flink Table API 和 SQL 实现一个连接到 Hive Metastore 的外部 Catalog。在 Flink 1.9 中，用户将能够查询和处理存储在 Hive 中的所有数据。如前所述，我们还可以在 Metastore 中持久化 Flink 表的元数据。此外，Hive 集成包括支持在 Flink Table API 或 SQL 查询中使用 Hive 的 UDF。[FLINK-10556](https://issues.apache.org/jira/browse/FLINK-10556) 中提供了更多详细信息。

虽然以前 Table API 或 SQL 查询的表一直是临时的，但新的 Catalog 连接器允许在 Metastore 中持久保存使用 SQL DDL 语句创建的表。这意味着我们可以直接连接到 Metastore 并注册一个表。从现在开始，只要我们的 Catalog 连接到 Metastore，我们就可以查询该表。

> Flink 1.9 中的 Hive 支持是实验性的。我们计划在下一个版本中稳定这些功能。

### 1.8 新 Python Table API 预览

此版本还引入了 Python Table API ([FLIP-38](https://cwiki.apache.org/confluence/display/FLINK/FLIP-38%3A+Python+Table+API)) 的第一个版本。这标志着我们开始为 Flink 提供全面的 Python 支持。该功能围绕着 Table API 设计了很薄的一层 Python API 包装器，基本上将 Python Table API 方法的调用都转换为 Java Table API 调用。在 Flink 1.9 版本中，Python Table API 尚不支持 UDF，只是标准的关系操作。在 Python 中支持 UDF 的功能已规划在未来版本的路线图中。

如果想尝试新的 Python API，则需要手动安装PyFlink。然后，可以看一看文档中的演练并尝试自己探索。社区目前正在准备 一个 pyflink 的 Python 包，该包将可以通过 pip 进行安装。

## 2. 重要变化

- Table API 和 SQL 现在是 Flink 发行版默认配置的一部分。以前，必须通过将相应的 JAR 文件从 ./opt 移动到 ./lib 来启用 Table API 和 SQL。
- 为 [FLIP-39](https://docs.google.com/document/d/1StObo1DLp8iiy0rbukx8kwAJb0BwDZrQrMWub3DzsEo/edit) 做准备，机器学习库 (flink-ml) 已被删除，。
- 为了支持 [FLIP-38](https://cwiki.apache.org/confluence/display/FLINK/FLIP-38%3A+Python+Table+API)，旧的 DataSet 和 DataStream Python API 已被删除。
- Flink 可以在 Java 9 上编译和运行。需要注意的是与外部系统（连接器、文件系统、报告器）交互的某些组件可能无法工作，因为相应的项目可能已不支持 Java 9。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/ImageBucket/blob/main/Other/smartsi.jpg?raw=true)

原文:[Apache Flink 1.9.0 Release Announcement](https://flink.apache.org/news/2019/08/22/release-1.9.0.html)
