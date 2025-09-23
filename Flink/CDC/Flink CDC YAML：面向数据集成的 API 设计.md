## 1. Flink CDC

### 1.1 Flink CDC

![](https://mmbiz.qpic.cn/mmbiz_jpg/8AsYBicEePu6TaWk6m7A2KFPyZ6QTZVOl7Wv0VkRxBAFtjJVXsFibic9bibXeSqzkUKLrQIM6yCoZYIt69icyH3UhYg/640?wx_fmt=other&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

Flink CDC 基于数据库日志中变化记录捕获技术，能够实现全量与增量数据的一体化读取，并提供了端到端的流式数据集成框架。通过与 Flink 框架结合，CDC 不仅展现出强大的数据管道处理能力，还能充分利用上下游丰富的生态系统，从而高效地完成海量数据的实时集成任务。在升级至 3.0 版本后，Flink CDC 的功能得到了进一步扩展：它不再仅仅作为数据源（Source），而是同时提供了写入下游端（Sink）的能力，使得从源头到目的地的数据集成过程变得更加流畅且可控。以 MySQL 为例，Flink CDC 提供的核心连接器均支持全量和增量数据的一体化处理，在整个同步过程中自动从全量切换到增量模式，并且确保数据传输的实时性和精确一次语义。

### 1.2 Flink CDC 用户 API

![](https://mmbiz.qpic.cn/mmbiz_jpg/8AsYBicEePu6TaWk6m7A2KFPyZ6QTZVOlx8JSyb36Uzco3Jx0BLHPGp5LOvmia2ibibMsL6dib1Pzxf1ecLw4bZPTicw/640?wx_fmt=other&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

从3.0版本开始，用户现在可以使用三种 API 来编写作业：CDC YAML API、Flink SQL API 和 Flink DataStream API。这三种 API 各有特点，适用于不同的场景，CDC YAML API 是目前最被推荐的选择。
- CDC YAML API :
  - 特别适合那些希望以更直观且易于维护的方式定义其数据处理逻辑的用户。
  - 它支持多种高级特性，如自动化的 Schema Evolution（表结构变更）、分库分表同步、行过滤、列投影转换（Transform）等。
  - 通过 YAML API 实现这些功能不仅简单直接，而且能够极大简化开发流程。
  - 对于需要频繁调整表结构或执行复杂的数据迁移任务来说，YAML API 提供了极大的便利性。
- Flink SQL API :
  - 允许用户利用类似标准 SQL 的语法进行数据查询与转换操作，非常适合熟悉 SQL 语言的专业人士。
  - 虽然在特定领域内表现优秀，但当涉及到较为复杂的业务逻辑（如表结构变更演化）时可能不够灵活。
- Flink DataStream API :
  - 基于 Java 语言的 DataStream API 为开发者提供了最大的灵活性，几乎可以实现所有类型的需求。
  - 然而，这也意味着它的学习曲线相对陡峭，特别是对于初学者而言的理解门槛较高。


1.3 传统 CDC 数据集成作业
图片
在讨论 Flink CDC 的优势之前，我们先回顾一下传统 CDC（变更数据捕获）的数据集成方案。尽管这种架构较为传统，但目前仍被众多企业所采用。这类做法是将全量数据同步和增量数据同步分开处理：全量同步基于 DataX 或 Sqoop 完成，而增量同步则使用 Debezium 或 Canal 等组件来实现。系统中会同时存在两张表——一个用于存储全量数据，另一个用于存放增量更新的信息；两表由调度系统定时进行合并，方可得到完整的结果表。
这种方法的缺点在于整个流程较长且涉及多个组件，这不仅增加了系统的复杂性，也对维护提出了更高的要求。此外，由于定时任务无法保证事务级别的数据一致性，因此难以确保每次合并后的数据都是符合数据库一致性语义的。
此外，上述链路难以满足对高时效性场景的需求。即使是极限配置下的调度策略，其更新频率也很难低于5分钟一次；若试图进一步缩短时间间隔至秒级，则很可能导致链路负荷过高，进而崩溃。
1.4 基于 Flink CDC 的数据集成作业
图片
相比之下，基于 Flink CDC 的数据集成作业可以显著简化上述流程。在已有 Flink 集群的前提下，开发人员仅需编写一个 Flink 作业即可完成全量与增量一体化的数据同步任务。整个过程中，Flink 框架能够确保精确一次（Exactly-once）的事件处理语义，即保证同步的数据记录既不会丢失也不会重复。此外，作为一款专为实时计算设计的流处理框架，Flink 具备提供端到端亚秒级延迟的能力，非常适合对时效性要求高的应用场景。
特别是随着 YAML API 的引入，现在可以通过简单的 YAML 配置文件来定义从源到目的地的数据集成过程，无需再手动寻找和配置各种连接器，使得创建端到端的数据集成解决方案变得更加便利。
1.5 Flink CDC 的优势
图片
Flink CDC 的架构优势在于其提供了一个端到端的数据流水线（Data Pipeline）。用户仅需编写一个 YAML 文件来定义整个数据流水线的处理逻辑，同时，它还配备了工具支持，使得现有的命令可以直接将 YAML 描述的数据流水线转换为 Flink 作业运行起来。这大大简化了配置和启动流程。
在过去的一年里，社区在“细粒度 Schema Evolution”（表结构变更同步）方面做了大量工作。这项功能允许更灵活地应对数据库模式变化的情况，包括但不限于容错机制、容错级别以及进化策略的支持等。这些改进使得 Flink CDC 能够更好地适应不同业务场景下的具体需求。
此外，ETL（抽取-转换-加载）过程中的“转换”(Transform)环节对于数据集成至关重要。Flink CDC 在此环节提供了强大的类 SQL 表达能力，支持对部分列进行投影、根据表达式追加计算列、按条件过滤数据行等功能，并且支持表达式嵌套及用户自定义函数（UDF）等。这样的设计极大地提升了基于 Flink CDC 的数据集成任务的效率与灵活性。值得注意的是，Flink CDC 作为早期就致力于实现全增量一体化解决方案的技术之一，不仅能够处理实时变化的数据捕获问题，同时也兼顾了历史数据的批量导入，从而为企业级应用提供了更加全面的数据同步方案。
02

YAML API

2.1 Flink CDC 发展历史
图片
Flink CDC 自 2020 年发布首个版本以来，基本保持着一到两年一个大版本，每个大版本分为四到五个小版本的稳定演进。继 2.0 版本实现增量快照算法、3.0 版本提出 YAML 端到端数据集成框架之后，Flink CDC 在 2024 年一月成功作为 Apache Flink 的子项目捐赠到 ASF 基金会。
2.2 Flink CDC 1.x：早期版本的 Flink CDC 连接器
图片
Flink CDC 1.x 系列版本最早于 2020 年发布并开源，它是基于 Flink Source API 实现的一组连接器，可以作为数据源使用，提供了捕获 MySQL 和 PostgreSQL 表中变化数据的能力。然而早期版本实现中，全量捕获转增量捕获的过程需要锁表，由于快照阶段耗时较长，这一过程会对生产业务造成巨大影响，可以认为在生产上基本不可用。（即便如此，当时也积累了一批用户）
2.3 Flink CDC 2.x：生产大规模可用的 CDC 连接器
图片
Flink CDC 2.x 系列版本实现了社区原创的“增量快照算法”，能够并行执行数据表快照，并实现全增量阶段的无锁切换，得到了阿里及其他云厂商公司在生产上大规模的验证及使用。增量快照算法的核心思路是将每张表按照主键列进行分块（Chunk）后由多个节点进行分布式读取，并通过水位线填充算法保证数据一致性，既不锁表也能提供精确一次语义。此外，此版本还增加了对 Db2、MongoDB、OceanBase 等数据库的支持。
2.4 Flink CDC 1.x & 2.x：简化 Flink ETL 作业
图片
Flink CDC 的 1.x 和 2.x 版本都只是一组支持了 CDC 的 Source 连接器，只能作为 Flink ETL 作业的一部分使用，即从事务型数据库中实时取出数据。这意味着作为一个数据源连接器，只能由用户选择已有的、基于 DataStream 或 SQL API 的 Sink 连接器搭配使用，没有提供完整的、端到端的体验。此外，由于 Flink CDC Source 连接器需要与所有其他符合标准的 Sink 连接器搭配使用，无法简单地加入自定义扩展，因此用户最期望的表结构变更同步、数据库 Binlog 写入 Kafka 等等功能，2.x 都不支持。
2.5 Flink CDC 3.x ：端到端实时数据集成框架
图片
在上述背景下，我们在社区推出了 Flink CDC 3.x 版本，提供了一个面向端到端的实时数据集成框架。它提供完整的数据集成体验，不仅提供了 Source 连接器，还提供了写入外部系统的 Sink 连接器。它能够识别源表的表结构变更，并通过特殊的事件报告给下游；能够正确处理上游动态加表、删除表等事件；此外，很重要的一点是版权归属问题。早期版本的 Flink CDC 在阿里巴巴组织下开源，可能导致社区中立性的疑虑。这些疑虑在捐赠给 Apache 基金会后得到了解决。
2.6 YAML API 设计
图片
在设计 YAML API 时，我们主要从两个方面进行了考量：一是面向的目标用户，一是 API 的设计原则。用户的需求是很简单的，MySQL 的数据要写到湖里、写到仓里。目标用户当然不需要是 Flink 的专家，这些初级用户正是 YAML API 的潜在用户。API 的设计原则是：足够简单，足够强大。这些是设计 YAML API 的时候个人的考量。
图片
最终推出的 API 也经过了很多方案的比较和选择，当时社区的设计稿讨论到了第五版，大家也对业界的数据集成框架、以及它们采用的 DSL 语言做了很多调研，最终选择基于 YAML。YAML 被广泛接受的原因之一是它的使用门槛比较低，可以理解它是若干个具有层级关系的 KV Pair 组成的文本文件，能够清晰地描述数据集成的逻辑，通过文本就能描述复杂的数据集成的 Flink 作业。
为了进一步简化体验，社区还提供了一个 CLI 命令行工具，可以让用户编写一个 YAML 文本，执行一条 shell 命令，就能生成一个 Flink CDC 作业。
2.7 Flink CDC 架构
图片
在加入 YAML API 后，Flink CDC 整体的架构如图所示。大家发现我特地标了不同的颜色，方便对三种 API 做详细的对比，包括 DataStream API，SQL API 还有 YAML API。DataStream 和 SQL API 下层都只有 CDC 的 Source，而 YAML API 下层不仅有 Source，还有 Sink ，这是最大的不同。此外，在 YAML API 下面还有一层 CDC Runtime，这其中包含一些运行时的算子逻辑。比如为了实现 Schema Evolution、要提供 Table Route 和 Transform 等特性的支持，就需要在运行时插入一些额外的流处理算子；而 DataStream API 和 SQL API 都不能提供这样的能力。
2.8 SQL 作业 vs YAML 作业
图片
从用户的角度来看，SQL 作业和 YAML 管道在处理数据变更（CDC, Change Data Capture）时存在一些关键差异。Flink SQL 在处理变更日志时，会将每次更新操作拆分为四条独立的数据记录：插入（Insert）、更新前（Update Before）、更新后（Update After）以及删除（Delete）。虽然这种机制有助于某些类型的计算优化，但同时也破坏了更新操作的原子性，使得原始更新信息难以复原。相比之下，设计一种能够完整保留更新事件（Update）的数据结构，如自定义的 DataChangeEvent，可以更好地支持从源数据库（例如 MySQL）到消息队列（如 Kafka）的数据同步过程，从而让下游业务系统更易于消费这些变更。
此外，在YAML格式定义的数据管道中引入对模式变更事件的支持（比如CreateTableEvent、AddColumnEvent 等），可以让表结构变更事件的处理更加灵活与直观。当数据源端识别到添加列的 DDL 事件时，可以通过在数据流中插入特殊事件来通知下游动态地调整目标存储（如 Paimon 表）的结构，同时保持整个分布式流程的一致性和高效性。对于拥有大量数据记录的大规模记录的表而言，特殊的标识事件效率比起手动替换数据记录高效得多。例如，如果需要将 Truncate Table 清空表事件同步到下游，使用标识事件的方式相比发送数以亿计的 Delete 事件来清空旧表——显然更加简洁且资源消耗更低。
上述优化和改进策略，不仅增强了系统的灵活性和可维护性，还提高了处理大规模数据集时的效率。
图片
在使用 Flink SQL 进行作业开发时，尤其是涉及整库同步的场景，通常需要编写大量的 DDL 语句来创建表。这种方式存在几个主要问题：首先，它难以应对表结构的变化，所有的字段名称及类型都需要在设计作业时确定。其次，当表结构发生变化时，更新（Update）操作的变更日志（Changelog）语义可能会被破坏；最后，由于每张表都需要对应一个处理节点，这会导致整个作业的拓扑变得异常庞大且复杂，给 Flink 集群及其管理器带来了较大压力，尤其是在构建 ODS 层等大规模数据集成任务中尤为明显。
相比之下，采用 YAML 配置文件定义作业的方式提供了更灵活的解决方案。这种模式下，系统能够自动检测并适应表结构的变化，并且支持表结构变更同步功能。这不仅限于基本的上下游同步，还包括了更加精细级别的 Schema 调整能力。此外，在提交分库分表的整库同步作业时，当前版本的 Source 和 Sink 组件已经可以支持单个实例读写多个表的操作，这意味着不再需要为数据库中的每一单独表格都创建独立的物理算子，从而极大地简化了作业的设计与执行流程——从视觉上来看，整个同步过程仅需通过两个关键节点就能完成，而不是像之前那样，每张表都需要独立的 Source 节点并各自读取 Binlog。这种方法有效减轻了对 Flink 集群资源的需求，同时也提高了整体系统的可维护性和扩展性。
2.9 DataStream 作业 vs YAML 作业
图片
对比一下 DataStream 作业和 YAML 作业，如果一个 Flink DataStream作业，需要用 CDC JSON Format 描述数据结构。这意味着每一条数据记录中，都需要携带对应 Schema 的信息描述。考虑到表结构变更并不常见，大部分数据记录的 Schema 都一样，重复发送给下游的 Schema 就会造成信息冗余、存储空间和 IO 带宽的浪费。而在 YAML CDC 中，数据记录中所有的结构都是经过压缩的 Binary Data，相比 DataStream 的数据记录结构更紧凑，在底层的物理存储上更加节约内存。此外，YAML 作业只在 Schema 发生变化时发送 SchemaChangeEvent 来描述变更信息，即总是使用最新的的 Schema 来描述随后的所有 DataChangeEvent，直到新的 SchemaChangeEvent 出现。这样的设计不用给每条数据记录携带一份 Schema 数据，减少了信息冗余。
图片
总结一下 DataStream API 和 YAML API 的区别。DataStream API 主要面向熟悉 Java、Scala 的开发者，且需要对分布式系统有一定理解，才能写出正确且高效的 Flink 作业（包括 Flink 的 DataStream API，持久化 State Backend、Checkpoint 模型等)。此外，为了将 Jar 作业提交到 Flink 上正确执行，还需要了解 Maven 及依赖管理相关的知识。最后，Java 作业其实是比较难以复用的；一个描述 MySQL 写入 Paimon 的 Jar 作业，想要迁移写入 Kafka，很多部分可能都需要从头重写。
而 YAML API 就可以比较轻易地应对这些问题。它面向普通用户，不要求高深的前置知识，即可构建强大的整库同步、表结构同步作业。此外，YAML 语法很简单，业界也比较通用，想要复用已有作业就更简单了，因为它只不过是一段文本，只需要对 Source、Sink 的部分属性稍加修改，就能实现写入目标的迁移。
2.10 YAML 核心特性：Schema Evolution
图片
下面介绍 YAML 的核心特性，第一个是上下游同步的表结构变更（Schema Evolution)。核心原理是在 YAML Pipeline 中传递的事件类型是 Event，既包括描述数据记录变更的 DataChangeEvent，也包括描述表结构变更的 SchemaChangeEvent。在遇到表结构变更事件时，将 Pipeline 里现存的数据全部落盘，然后根据 SchemaChangeEvent 进行表结构的演化，成功后即可继续处理上游数据。
图片
目前，上游 MySQL 数据库中可能发生很多 DDL 变化，例如新增表、新增列，修改列类型、重命名列、删表删列等，但在实际业务中，不同类型的结构变更可能有不同的处理需求。
例如上游某一列被删除了，下游可能希望保留；部分上游支持的表结构变更，下游可能无法实现。又或者是用户不希望下游表的结构发生改变，不用动业务代码。这样的诉求可以通过 Schema Change Behavior 选项和细粒度配置实现。
目前社区推荐使用 LENIENT 和 TRY_EVOLVE 两种模式。LENIENT 是最宽容的模式，能够保证 Schema 的向前兼容性，下游业务方的业务代码不用动。TRY_EVOLVE 会尽量将上游表的变更应用到下游，但相比 EVOLVE 模式略微宽容些，会做一定程度的容错。
其他两种模式就比较简单了。EXCEPTION 模式碰到 SchemaChange 就直接抛异常，IGNORE 模式则是忽略所有表结构变更，保证下游 Schema 始终不变。
03

Transform + AI

3.1 YAML 核心特性：Transform 设计
图片
Transform 数据加工过程是 ETL 当中 T 的部分。其中主要的需求包括从表中现存的列里投影出部分列、根据特定表达式的值筛选出特定的数据行、根据已有列计算出新列并加入其中。
例如，一个较为复杂的场景可能是这样的：上游存在一个 age 字段，希望追加一个布尔变量 flag，判断 age 是否大于 18，并且只保留 age 和 flag 字段到下游，删除其余数据列。此外，计算列可能涉及到用户定义函数逻辑，甚至调用外部 Web 服务。此外，用户可能还希望根据条件表达式对数据行进行过滤。在合并分库分表写入 Paimon 等数据湖下游时，可能需要手动指定主键列（Primary Key）和分区列（Partition Key）。此外，在结合 AI 场景下是否能支持大模型的调用，这都是 Transform 需要解决的问题。
3.2 YAML 核心特性：Transform 实现
图片
CDC YAML 为 Transform 选择的语法是类 SQL 的表达式。可以看到 Projection 和 Filter 字段完全是 SQL 表达，对于指定的 app_db.orders表，Projection 里写出的是下游希望读到的字段。其中支持使用 UDF 函数和计算列，Filter 可以简单类比成 SQL 里的 WHERE 字段后面跟的条件，例如 ID 列不为空、price 列的值 >= 100 等组合的表达式。实现上，YAML 的类 SQL 语法首先被转换为标准的 SQL 语句，并使用 Calcite 进行解析，最终用 Janino 模版引擎动态编译成单个可复用的表达式后进行求值。实现上还需要考虑 Schema Evolution 导致的缓存失效等问题。
图片
目前 Transform 实现的整体拓扑图如上所示。其中 PreTransform 和 PostTransform 都是可选的节点，在用户没有编写任何 Transform 规则时不存在，默认行为是将 Source 下发的数据记录原封不动的发给下游的 Schema Operator 和 Data Sink 节点。
3.3 YAML 核心特性：AI model 集成
图片
YAML Pipeline 与 AI Model 的深度集成如图所示。左侧是 Flink CDC 从 MySQL 产生的 Binlog 日志中捕获到最新的实时业务数据，并且同步到下游的 StarRocks OLAP 系统或 ElasticSearch 系统构建搜索场景。
既然 Transform 已经支持调用任意的 UDF 函数，那能否与 AI 模型集成呢？答案是可以的。在知识库或广告营销、金融这类时效性要求比较强的业务场景中，AI 模型的集成是具备实际需求的，例如 RAG、广告的实时投放、金融行业的实时风控等。
3.4 YAML 核心特性：AI model 设计
图片
YAML 集成 AI Model 能力的 API 设计如图所示。用户可以在 Pipeline 级别定义 AI Model，目前内置了 Embedding 和 Chat 两类模型。想要调用模型只需要指定 Model 类型、提供一些必要的参数（例如 Host 和 Key 等)即可，生命的模型可以直接在 Transform 表达式中调用。
这个例子的场景是从 testdb.articles 表中提取最新发布的文章内容，根据文章的标题及内容生成向量，灌入 ElasticSearch 中，配合整体的 RAG 设计，ElasticSearch 里的向量就代表今天最新的文章的信息，可以用于下游模型的答案生成，实时更新。这是 Flink 实时数据的计算引擎、Flink CDC 实时数据集成框架给 AI 带来的切实收益，通过处理实时数据来帮助模型生成更准确的答案。
AI Model API 的设计上能够兼容多种模型，且各个模型的参数可以通过 YAML 自定义配置。同时支持开源和闭源模型，例如 ChatGPT 和阿里的通义千问模型。此外，模型的复用也非常简单，只需复制粘贴模型定义配置项即可。
3.5 YAML 核心特性：AI model 实现
图片
AI Model 集成在社区分配的 JIRA Ticket 为 FLINK-36525，并且已经合入社区 master 分支，欢迎大家自行编译体验（笔者注：春节前发布的 Flink CDC 3.3.0 版本已经支持该特性)。
04

Community

4.1 Flink CDC 社区动态
图片
上图是 Flink CDC 社区在 2023 年和 2024 年的数据对比（截止到十月制作 PPT 之时)。社区贡献者从 101 位增加到 140 几位，增长 40% 多。主分支上的代码 commit 数量随着最近一年在 Scheme Evolution、YAML、AI Model 的集成等功能的实现，Commits 数量大幅增加 50%。社区的 Stars 现在大概有 5000+。
4.2 Flink CDC 社区规划
图片
社区规划方面主要分为两部分。第一部分，我们希望解锁更多新的场景，例如 AI Model 的深度集成（笔者注：春节前发布的 Flink CDC 3.3.0 版本已经支持该特性)，支持 Batch Pipeline、流批一体等；对接更多的上下游，例如支持 Apache Iceberg，之后会由货拉拉和天翼云的老师一起推动。此外还有支持更多 Schema Change 类型，例如 MySQL 的 Schema 类型总共大概有三十几种，目前应该只支持十几种，许多罕见的类型也希望能够完整支持，保证在线上极端的 Schema 变更的 Case 都能覆盖到。
另一部分是关于稳定性的打磨，包括数据限流，细粒度的异常工程。这里的稳定性指的不是 Flink 框架不稳定或者 CDC 框架不稳定，主要是因为 Pipeline 作业和上下游息息相关，上游 DB 负载高， CPU 高或者下游的 Kafka 写的时候压力太大都会导致 Pipeline 不稳定，但是它的根因并不一定在框架，但框架提供的容错支持能够极大地改善用户体验。围绕这部分的工作包括数据限流、兼容更多的 Flink 版本，依赖库版本升级等等。
4.3 欢迎加入开源社区
图片
Flink CDC 作为 Apache Flink 最活跃的官方子项目，有独立的文档网站。关于项目的任何讨论，都可以在 Flink 的开发者邮件列表中发出，也可以在 Github 上提交代码 PR，中文用户也可以加入Flink CDC 社区用户钉钉群，钉钉群号：80655011780。右图是参与代码提交的贡献者，GitHub 默认截图只能截 Top100，目前社区已经有超过 150 名代码贡献者。欢迎大家加入！

独立的文档网站: https://nightlies.apache.org/flink/flink-cdc-docs-stable

在 Flink 社区邮件列表讨论: dev@flink.apache.org / user@flink.apache.org

在 Apache JIRA 管理需求和缺陷: https://issues.apache.org/jira

在 GitHub 上提交代码PR : https://github.com/apache/flink-cdc
