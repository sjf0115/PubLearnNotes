Flink 1.13 发布了！Flink 1.13 包括了超过 200 名贡献者所提交的 1000 多项修复和优化。

这一版本中，Flink 的一个主要目标取得了重要进展，即让流处理应用的使用像普通应用一样简单和自然。Flink 1.13 新引入的被动扩缩容使得流作业的扩缩容和其它应用一样简单，用户仅需要修改并发度即可。

这个版本还包括一系列重要改动使用户可以更好理解流作业的性能。当流作业的性能不及预期的时候，这些改动可以使用户可以更好的分析原因。这些改动包括用于识别瓶颈节点的负载和反压可视化、分析算子热点代码的 CPU 火焰图和分析 State Backend 状态的 State 访问性能指标。

除了这些特性外，Flink 社区还添加了大量的其它优化，本文后续会讨论其中的一些。我们希望用户可以享受新的版本和特性带来的便利，在本文最后，我们还会介绍升级 Flink 版本需要注意的一些变化。

我们鼓励用户下载试用新版 Flink 并且通过[邮件列表](https://flink.apache.org/community.html#mailing-lists) 和 [JIRA](https://issues.apache.org/jira/projects/FLINK/summary) 来反馈遇到的问题。

## 1. 重要特性

### 1.1 被动扩缩容

Flink 项目的一个初始目标，就是希望流处理应用可以像普通应用一样简单和自然，被动扩缩容是 Flink 针对这一目标上的最新进展。

当考虑资源管理和部分的时候，Flink 有两种可能的模式。用户可以将 Flink 应用部署到 k8s、yarn 等资源管理系统之上，并且由 Flink 主动的来管理资源并按需分配和释放资源。这一模式对于经常改变资源需求的作业和应用非常有用，比如批作业和实时 SQL 查询。在这种模式下，Flink 所启动的 Worker 数量是由应用设置的并发度决定的。在 Flink 中我们将这一模式叫做主动扩缩容。

对于长时间运行的流处理应用，一种更适合的模型是用户只需要将作业像其它的长期运行的服务一样启动起来，而不需要考虑是部署在 k8s、yarn 还是其它的资源管理平台上，并且不需要考虑需要申请的资源的数量。相反，它的规模是由所分配的 worker 数量来决定的。当 worker 数量发生变化时，Flink 自动的改动应用的并发度。在 Flink 中我们将这一模式叫做被动扩缩容。

Flink 的 Application [部署模式](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/concepts/flink-architecture/#flink-application-execution) 开启了使 Flink 作业更接近普通应用（即启动 Flink 作业不需要执行两个独立的步骤来启动集群和提交应用）的努力，而被动扩缩容完成了这一目标：用户不再需要使用额外的工具（如脚本、K8s 算子）来让 worker 的数量与应用并发度设置保持一致。

用户现在可以将自动扩缩容的工具应用到 Flink 应用之上，就像普通的应用程序一样，只要用户了解扩缩容的代价：**有状态的流应用在扩缩容的时候需要将状态重新分发**。

如果想要尝试被动扩缩容，用户可以增加 `scheduler-mode: reactive` 这一配置项，然后启动一个应用集群（[Standalone](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/deployment/resource-providers/standalone/overview/#application-mode) 或者 [K8s](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/deployment/resource-providers/standalone/kubernetes/#deploy-application-cluster)）。更多细节见被动扩缩容的[文档](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/deployment/elastic_scaling/#reactive-mode)。


### 1.2 分析应用的性能

对所有应用程序来说，能够简单的分析和理解应用的性能是非常关键的功能。这一功能对 Flink 更加重要，因为 Flink 应用一般是数据密集的（即需要处理大量的数据）并且需要在（近）实时的延迟内给出结果。

当 Flink 应用处理的速度跟不上数据输入的速度时，或者当一个应用占用的资源超过预期，下文介绍的这些工具可以帮你分析原因。

#### 1.2.1 瓶颈检测与反压监控

Flink 性能分析首先要解决的问题经常是：哪个算子是瓶颈？为了回答这一问题，Flink 引入了描述作业繁忙（即在处理数据）与反压（由于下游算子不能及时处理结果而无法继续输出）程度的指标。应用中可能的瓶颈是那些繁忙并且上游被反压的算子。

Flink 1.13 优化了反压检测的逻辑（使用基于任务 Mailbox 计时，而不在再于堆栈采样），并且重新实现了作业图的 UI 展示：Flink 现在在 UI 上通过颜色和数值来展示繁忙和反压的程度。

![](https://mmbiz.qpic.cn/mmbiz_png/8AsYBicEePu6JhSC2pgGR5ib29CuZS6kjDFtrabjyUQ1Lic5aCVTicVMyO6GZVSuictBkoZdPp4E5CFWJVf6fn9eIuA/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

#### 1.2.2 Web UI 中的 CPU 火焰图

Flink 关于性能另一个经常需要回答的问题：瓶颈算子中的哪部分计算逻辑消耗巨大？针对这一问题，一个有效的可视化工具是火焰图。它可以帮助回答以下问题：
- 哪个方法现在在占用 CPU？
- 不同方法占用 CPU 的比例如何？
- 一个方法被调用的栈是什么样子的？

火焰图是通过重复采样线程的堆栈来构建的。在火焰图中，每个方法调用被表示为一个矩形，矩形的长度与这个方法出现在采样中的次数成正比。火焰图在 UI 上的一个例子如下图所示。

![](https://mmbiz.qpic.cn/mmbiz_png/8AsYBicEePu6JhSC2pgGR5ib29CuZS6kjD7lviagjUBVVh0sIR88MJn0tOczcZAEmicmuqPJiclA0GMsszbwRWQHOmQ/640?wx_fmt=png&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

火焰图的[文档](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/ops/debugging/flame_graphs)包括启用这一功能的更多细节和指令。

#### 1.2.3 State 访问延迟指标

另一个可能的性能瓶颈是 state backend，尤其是当作业的 state 超过内存容量而必须使用 RocksDB state backend 时。这里并不是想说 RocksDB 性能不够好（我们非常喜欢 RocksDB！），但是它需要满足一些条件才能达到最好的性能。例如，用户可能很容易遇到非故意的在云上由于[使用了错误的磁盘资源类型而不能满足 RockDB 的 IO 性能需求](https://www.ververica.com/blog/the-impact-of-disks-on-rocksdb-state-backend-in-flink-a-case-study)的问题。

基于 CPU 火焰图，新的 State Backend 的延迟指标可以帮助用户更好的判断性能不符合预期是否是由 State Backend 导致的。例如，如果用户发现 RocksDB 的单次访问需要几毫秒的时间，那么就需要查看内存和 I/O 的配置。这些指标可以通过设置 `state.backend.rocksdb.latency-track-enabled` 这一选项来启用。这些指标是通过采样的方式来监控性能的，所以它们对 RocksDB State Backend 的性能影响是微不足道的。

### 1.3 通过 Savepoint 来切换 State Backend

用户现在可以在从一个 Savepoint 重启时切换一个 Flink 应用的 State Backend。这使得 Flink 应用不再被限制只能使用应用首次运行时选择的 State Backend。基于这一功能，用户现在可以首先使用一个 HashMap State Backend（纯内存的 State Backend），如果后续状态变得过大的话，就切换到 RocksDB State Backend 中。

在实现层，Flink 现在统一了所有 State Backend 的 Savepoint 格式来实现这一功能。


### 1.4 K8s 部署时使用用户指定的 Pod 模式

原生 kubernetes 部署（Flink 主动要求 K8s 来启动 Pod）中，现在可以使用自定义的 Pod 模板。使用这些模板，用户可以使用一种更符合 K8s 的方式来设置 JM 和 TM 的 Pod，这种方式比 Flink K8s 集成内置的配置项更加灵活。

### 1.5 生产可用的 Unaligned Checkpoint

Unaligned Checkpoint 目前已达到了生产可用的状态，我们鼓励用户在存在反压的情况下试用这一功能。具体来说，Flink 1.13 中引入的这些功能使 Unaligned Checkpoint 更容易使用：
- 用户现在使用 Unaligned Checkpoint 时也可以扩缩容应用。如果用户需要因为性能原因不能使用 Savepoint而必须使用 Retained checkpoint 时，这一功能会非常方便。
- 对于没有反压的应用，启用 Unaligned Checkpoint 现在代价更小。Unaligned Checkpoint 现在可以通过超时来自动触发，即一个应用默认会使用 Aligned Checkpoint（不存储传输中的数据），而只在对齐超过一定时间范围时自动切换到 Unaligned Checkpoint（存储传输中的数据）。

关于如何启用 Unaligned Checkpoint 可以参考相关[文档](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/ops/state/checkpoints/#unaligned-checkpoints)。

### 1.6 机器学习迁移到单独的仓库

为了加速 Flink 机器学习的进展（流批统一的机器学习），现在 Flink 机器学习开启了新的 flink-ml 仓库。我们采用类似于 Stateful Function 项目的管理方式，通过使用一个单独的仓库从而简化代码合并的流程并且可以进行单独的版本发布，从而提高开发的效率。

用户可以关注 Flink 在机器学习方面的进展，比如与 Alink（Flink 常用机器学习算法套件）的互操作以及 Flink 与 Tensorflow 的集成。

## 2. SQL / Table API 进展

与之前的版本类似，SQL 和 Table API 仍然在所有开发中占用很大的比例。

### 2.1 通过 Table-valued 函数来定义时间窗口

在流式 SQL 查询中，一个最经常使用的是定义时间窗口。Flink 1.13 中引入了一种新的定义窗口的方式：通过 Table-valued 函数。这一方式不仅有更强的表达能力（允许用户定义新的窗口类型），并且与 SQL 标准更加一致。Flink 1.13 在新的语法中支持 TUMBLE 和 HOP 窗口，在后续版本中也会支持 SESSION 窗口。我们通过以下两个例子来展示这一方法的表达能力。

例 1：一个新引入的 CUMULATE 窗口函数，它可以支持按特定步长扩展的窗口，直到达到最大窗口大小：
```sql
SELECT window_time, window_start, window_end, SUM(price) AS total_price
FROM TABLE(CUMULATE(TABLE Bid, DESCRIPTOR(bidtime), INTERVAL '2' MINUTES, INTERVAL '10' MINUTES))
GROUP BY window_start, window_end, window_time;
```

例 2：用户在 table-valued 窗口函数中可以访问窗口的起始和终止时间，从而使用户可以实现新的功能。例如，除了常规的基于窗口的聚合和 Join 之外，用户现在也可以实现基于窗口的 Top-K 聚合：
```sql
SELECT window_time, ...
  FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY window_start, window_end ORDER BY total_price DESC) AS rank
    FROM t
) WHERE rank <= 100;
```

### 2.2 提高 DataStream API 与 Table API / SQL 的互操作能力

这一版本极大的简化了 DataStream API 与 Table API 混合的程序。

Table API 是一种非常方便的应用开发接口，因为这经支持表达式的程序编写并提供了大量的内置函数。但是有时候用户也需要切换回 DataStream，例如当用户存在表达能力、灵活性或者 State 访问的需求时。

Flink 新引入的  `StreamTableEnvironment.toDataStream()/.fromDataStream()` 可以将一个 DataStream API 声明的 Source 或者 Sink 当作 Table 的 Source 或者 Sink 来使用。主要的优化包括：
- DataStream 与 Table API 类型系统的自动转换。
- Event Time 配置的无缝集成，Watermark 行为的高度一致性。
- Row 类型（即 Table API 中数据的表示）有了极大的增强，包括 `toString()` / `hashCode()` 和 `equals()` 方法的优化，按名称访问字段值的支持与稀疏表示的支持。

```sql
Table table = tableEnv.fromDataStream(
  dataStream,
  Schema.newBuilder()
    .columnByMetadata("rowtime", "TIMESTAMP(3)")
    .watermark("rowtime", "SOURCE_WATERMARK()")
    .build());

DataStream<Row> dataStream = tableEnv.toDataStream(table)
  .keyBy(r -> r.getField("user"))
  .window(...);
```

### 2.3 SQL Client: 初始化脚本和语句集合 （Statement Sets）

SQL Client 是一种直接运行和部署 SQL 流或批作业的简便方式，用户不需要编写代码就可以从命令行调用 SQL，或者作为 CI / CD 流程的一部分。

这个版本极大的提高了 SQL Client 的功能。现在基于所有通过 Java 编程（即通过编程的方式调用 TableEnvironment 来发起查询）可以支持的语法，现在 SQL Client 和 SQL 脚本都可以支持。这意味着 SQL 用户不再需要添加胶水代码来部署他们的SQL作业。

#### 2.3.1 配置简化和代码共享

Flink 后续将不再支持通过 Yaml 的方式来配置 SQL Client（注：目前还在支持，但是已经被标记为废弃）。作为替代，SQL Client 现在支持使用一个初始化脚本在主 SQL 脚本执行前来配置环境。这些初始化脚本通常可以在不同团队/部署之间共享。它可以用来加载常用的 catalog，应用通用的配置或者定义标准的视图。
```sql
./sql-client.sh -i init1.sql init2.sql -f sqljob.sql
```

#### 2.3.2 更多的配置项

通过增加配置项，优化 SET / RESET 命令，用户可以更方便的在 SQL Client 和 SQL 脚本内部来控制执行的流程。

#### 2.3.3 通过语句集合来支持多查询

多查询允许用户在一个 Flink 作业中执行多个 SQL 查询（或者语句）。这对于长期运行的流式 SQL 查询非常有用。语句集可以用来将一组查询合并为一组同时执行。以下是一个可以通过 SQL Client 来执行的 SQL 脚本的例子。它初始化和配置了执行多查询的环境。这一脚本包括了所有的查询和所有的环境初始化和配置的工作，从而使它可以作为一个自包含的部署组件。
```sql
-- set up a catalog
CREATE CATALOG hive_catalog WITH ('type' = 'hive');
USE CATALOG hive_catalog;

-- or use temporary objects
CREATE TEMPORARY TABLE clicks (
  user_id BIGINT,
  page_id BIGINT,
  viewtime TIMESTAMP
) WITH (
  'connector' = 'kafka',
  'topic' = 'clicks',
  'properties.bootstrap.servers' = '...',
  'format' = 'avro'
);

-- set the execution mode for jobs
SET execution.runtime-mode=streaming;

-- set the sync/async mode for INSERT INTOs
SET table.dml-sync=false;

-- set the job's parallelism
SET parallism.default=10;

-- set the job name
SET pipeline.name = my_flink_job;

-- restore state from the specific savepoint path
SET execution.savepoint.path=/tmp/flink-savepoints/savepoint-bb0dab;

BEGIN STATEMENT SET;

INSERT INTO pageview_pv_sink
SELECT page_id, count(1) FROM clicks GROUP BY page_id;

INSERT INTO pageview_uv_sink
SELECT page_id, count(distinct user_id) FROM clicks GROUP BY page_id;

END;
```

### 2.4 Hive 查询语法兼容性

用户现在在 Flink 上也可以使用 Hive SQL 语法。除了 Hive DDL 方言之外，Flink现在也支持常用的 Hive DML 和 DQL 方言。



为了使用 Hive SQL 方言，需要设置 table.sql-dialect 为 hive 并且加载 HiveModule。后者非常重要，因为必须要加载 Hive 的内置函数后才能正确实现对 Hive 语法和语义的兼容性。例子如下：



CREATE CATALOG myhive WITH ('type' = 'hive'); -- setup HiveCatalog
USE CATALOG myhive;
LOAD MODULE hive; -- setup HiveModule
USE MODULES hive,core;
SET table.sql-dialect = hive; -- enable Hive dialect
SELECT key, value FROM src CLUSTER BY key; -- run some Hive queries


需要注意的是， Hive 方言中不再支持 Flink 语法的 DML 和 DQL 语句。如果要使用 Flink 语法，需要切换回 default 的方言配置。



### 2.5 优化的 SQL 时间函数


在数据处理中时间处理是一个重要的任务。但是与此同时，处理不同的时区、日期和时间是一个日益复杂[16] 的任务。



在 Flink 1.13 中，我们投入了大量的精力来简化时间函数的使用。我们调整了时间相关函数的返回类型使其更加精确，例如 PROCTIME()，CURRENT_TIMESTAMP() 和 NOW()。



其次，用户现在还可以基于一个 TIMESTAMP_LTZ 类型的列来定义 Event Time 属性，从而可以优雅的在窗口处理中支持夏令时。



用户可以参考 Release Note 来查看该部分的完整变更。




## 3. PyFlink 核心优化


这个版本对 PyFlink 的改进主要是使基于 Python 的 DataStream API 与 Table API 与 Java/scala 版本的对应功能更加一致。


### 3.1 Python DataStream API 中的有状态算子


在 Flink 1.13 中，Python 程序员可以享受到 Flink 状态处理 API 的所有能力。在 Flink 1.12 版本重构过的 Python DataStream API 现在已经拥有完整的状态访问能力，从而使用户可以将数据的信息记录到 state 中并且在后续访问。



带状态的处理能力是许多依赖跨记录状态共享（例如 Window Operator）的复杂数据处理场景的基础。



以下例子展示了一个自定义的计算窗口的实现：



class CountWindowAverage(FlatMapFunction):
    def __init__(self, window_size):
        self.window_size = window_size

    def open(self, runtime_context: RuntimeContext):
        descriptor = ValueStateDescriptor("average", Types.TUPLE([Types.LONG(), Types.LONG()]))
        self.sum = runtime_context.get_state(descriptor)

    def flat_map(self, value):
        current_sum = self.sum.value()
        if current_sum is None:
            current_sum = (0, 0)
        # update the count
        current_sum = (current_sum[0] + 1, current_sum[1] + value[1])
        # if the count reaches window_size, emit the average and clear the state
        if current_sum[0] >= self.window_size:
            self.sum.clear()
            yield value[0], current_sum[1] // current_sum[0]
        else:
            self.sum.update(current_sum)

ds = ...  # type: DataStream
ds.key_by(lambda row: row[0]) \
  .flat_map(CountWindowAverage(5))


### 3.2 PyFlink DataStream API 中的用户自定义窗口


Flink 1.13 中 PyFlink DataStream 接口增加了对用户自定义窗口的支持，现在用户可以使用标准窗口之外的窗口定义。



由于窗口是处理无限数据流的核心机制 （通过将流切分为多个有限的『桶』），这一功能极大的提高的 API 的表达能力。



### 3.3 PyFlink Table API 中基于行的操作


Python Table API 现在支持基于行的操作，例如用户对行数据的自定义函数。这一功能使得用户可以使用非内置的数据处理函数。



一个使用 map() 操作的 Python Table API 示例如下：



@udf(result_type=DataTypes.ROW(
  [DataTypes.FIELD("c1", DataTypes.BIGINT()),
   DataTypes.FIELD("c2", DataTypes.STRING())]))
def increment_column(r: Row) -> Row:
  return Row(r[0] + 1, r[1])

table = ...  # type: Table
mapped_result = table.map(increment_column)


除了 map()，这一 API 还支持 flat_map()，aggregate()，flat_aggregate() 和其它基于行的操作。这使 Python Table API 的功能与 Java Table API 的功能更加接近。



### 3.3 PyFlink DataStream API 支持 Batch 执行模式


对于有限流，PyFlink DataStream API 现在已经支持 Flink 1.12 DataStream API 中引入的 Batch 执行模式。



通过复用数据有限性来跳过 State backend 和 Checkpoint 的处理，Batch 执行模式可以简化运维，并且提高有限流处理的性能。




## 4. 其它优化

### 4.1 基于 Hugo 的 Flink 文档

Flink 文档从 JekyII 迁移到了 Hugo。如果您发现有问题，请务必通知我们，我们非常期待用户对新的界面的感受。

### 4.2 Web UI 支持历史异常

Flink Web UI 现在可以展示导致作业失败的 n 次历史异常，从而提升在一个异常导致多个后续异常的场景下的调试体验。用户可以在异常历史中找到根异常。


### 4.3 优化失败 Checkpoint 的异常和失败原因的汇报

Flink 现在提供了失败或被取消的 Checkpoint 的统计，从而使用户可以更简单的判断 Checkpoint 失败的原因，而不需要去查看日志。

Flink 之前的版本只有在 Checkpoint 成功的时候才会汇报指标（例如持久化数据的大小、触发时间等）。

### 4.4 提供『恰好一次』一致性的 JDBC Sink

从 1.13 开始，通过使用事务提交数据，JDBC Sink 可以对支持 XA 事务的数据库提供『恰好一次』的一致性支持。这一特性要求目标数据库必须有（或链接到）一个 XA 事务处理器。

这一 Sink 现在只能在 DataStream API 中使用。用户可以通过 JdbcSink.exactlyOnceSink(…) 来创建这一 Sink（或者通过显式初始化一个 JdbcXaSinkFunction）。

### 4.5 PyFlink Table API 在 Group 窗口上支持用户自定义的聚合函数

PyFlink Table API 现在对 Group 窗口同时支持基于 Python 的用户自定义聚合函数（User-defined Aggregate Functions, UDAFs）以及 Pandas UDAFs。这些函数对许多数据分析或机器学习训练的程序非常重要。

在 Flink 1.13 之前，这些函数仅能在无限的 Group-by 聚合场景下使用。Flink 1.13 优化了这一限制。

### 4.6 Batch 执行模式下 Sort-merge Shuffle 优化

Flink 1.13 优化了针对批处理程序的 Sort-merge Blocking Shuffle 的性能和内存占用情况。这一 Shuffle 模式是在 Flink 1.12 的 FLIP-148[17] 中引入的。

这一优化避免了大规模作业下不断出现 OutOfMemoryError: Direct Memory 的问题，并且通过 I/O 调度和 broadcast 优化提高了性能（尤其是在机械硬盘上）。

### 4.7 HBase 连接器支持异步维表查询和查询缓存

HBase Lookup Table Source 现在可以支持异步查询模式和查询缓存。这极大的提高了使用这一 Source 的 Table / SQL 维表 Join 的性能，并且在一些典型情况下可以减少对 HBase 的 I/O 请求数量。

在之前的版本中，HBase Lookup Source 仅支持同步通信，从而导致作业吞吐以及资源利用率降低。

升级 Flink 1.13 需要注意的改动：
- FLINK-21709[18] – 老的 Table & SQL API 计划器已经被标记为废弃，并且将在 Flink 1.14 中被删除。Blink 计划器在若干版本之前已经被设置为默认计划器，并且将成为未来版本中的唯一计划器。这意味着 BatchTableEnvironment 和 DataSet API 互操作后续也将不再支持。用户需要切换到统一的 TableEnvironment 来编写流或者批的作业。
- FLINK-22352[19] – Flink 社区决定废弃对 Apache mesos 的支持，未来有可能会进一步删除这部分功能。用户最好能够切换到其它的资源管理系统上。
- FLINK-21935[20] – state.backend.async 这一配置已经被禁用了，因为现在 Flink 总是会异步的来保存快照（即之前的配置默认值），并且现在没有实现可以支持同步的快照保存操作。
- FLINK-17012[21] – Task 的 RUNNING 状态被细分为两步：INITIALIZING 和 RUNNING。Task 的 INITIALIZING 阶段包括加载 state 和在启用 unaligned checkpoint 时恢复 In-flight 数据的过程。通过显式区分这两种状态，监控系统可以更好的区分任务是否已经在实际工作。
- FLINK-21698[22] – NUMERIC 和 TIMESTAMP 类型之间的直接转换存在问题，现在已经被禁用，例如 CAST(numeric AS TIMESTAMP(3))。用户应该使用 TO_TIMESTAMP(FROM_UNIXTIME(numeric)) 来代替。
- FLINK-22133[23] – 新的 Source 接口有一个小的不兼容的修改，即 SplitEnumerator.snapshotState() 方法现在多接受一个 checkpoint id 参数来表示正在进行的 snapshot 操作所属的 checkpoint 的 id。
- FLINK-19463[24] – 由于老的 Statebackend 接口承载了过多的语义并且容易引起困惑，这一接口被标记为废弃。这是一个纯 API 层的改动，而并不会影响应用运行时。对于如何升级现有作业，请参考作业迁移指引[25]。

## 5. 其它资源

二进制和代码可以从 Flink 官网的下载页面[26] 获得，最新的 PyFlink 发布可以从 PyPI[27] 获得。

如果想要升级到 Flink 1.13，请参考发布说明[28]。这一版本与之前 1.x 的版本在标记为@Public 的接口上是兼容的。

用户也可以查看新版本修改列表[29] 与更新后的文档[30] 来获得修改和新功能的详细列表。

原文链接：https://flink.apache.org/news/2021/05/03/release-1.13.0.html

参考链接：

[1] https://flink.apache.org/downloads.html
[2] https://flink.apache.org/community.html#mailing-lists
[3] https://issues.apache.org/jira/projects/FLINK/summary
[4] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/concepts/flink-architecture/#flink-application-execution
[5] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/deployment/resource-providers/standalone/overview/#application-mode
[6] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/deployment/resource-providers/standalone/kubernetes/#deploy-application-cluster
[7] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/deployment/elastic_scaling/#reactive-mode
[8] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/ops/debugging/flame_graphs
[9] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/ops/state/state_backends/#the-embeddedrocksdbstatebackend
[10] https://www.ververica.com/blog/the-impact-of-disks-on-rocksdb-state-backend-in-flink-a-case-study
[11] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/deployment/resource-providers/native_kubernetes/
[12] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/ops/state/checkpoints/#unaligned-checkpoints
[13] https://github.com/apache/flink-ml
[14] https://github.com/alibaba/Alink
[15] https://github.com/alibaba/flink-ai-extended
[16] https://xkcd.com/1883/
[17] https://cwiki.apache.org/confluence/display/FLINK/FLIP-148%3A+Introduce+Sort-Merge+Based+Blocking+Shuffle+to+Flink
[18] https://issues.apache.org/jira/browse/FLINK-21709
[19] https://issues.apache.org/jira/browse/FLINK-22352
[20] https://issues.apache.org/jira/browse/FLINK-21935
[21] https://issues.apache.org/jira/browse/FLINK-17012
[22] https://issues.apache.org/jira/browse/FLINK-21698
[23] https://issues.apache.org/jira/browse/FLINK-22133
[24] https://issues.apache.org/jira/browse/FLINK-19463
[25] https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/ops/state/state_backends/#migrating-from-legacy-backends
[26] https://flink.apache.org/downloads.html
[27] https://pypi.org/project/apache-flink/
[28] https://ci.apache.org/projects/flink/flink-docs-release-1.13/release-notes/flink-1.13
[29] https://issues.apache.org/jira/secure/ReleaseNote.jspa?projectId=12315522&version=12349287
[30] https://ci.apache.org/projects/flink/flink-docs-release-1.13/
