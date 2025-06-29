作为一种特定领域语言，SQL 的设计初衷是隐藏底层数据处理的复杂性，让用户通过声明式语言来进行数据操作。而 Flink SQL 由于其架构的特殊性，在实现层面通常需引入状态后端配合 checkpoint 来保证计算结果的最终一致性。目前 Flink SQL 生成状态算子的策略由优化器根据配置项 + SQL 语句来推导，想要在处理有状态的大规模数据和性能调优方面游刃有余的话，用户还是需要对 SQL 状态算子生成机制和管理策略有一定了解。

## 1. 运行原理：状态算子的产生

### 1.1 基于优化器推导产生的状态算子

| 状态算子 | 状态清理机制 |
| :------------- | :------------- |
| ChangelogNormalize | 生命周期 TTL |
| SinkUpsertMaterlizer | |
| LookupJoin（*）|

#### 1.1.1 ChangelogNormalize

ChangelogNormalize 作为一个状态算子，旨在对涉及主键语义的数据变更日志进行标准化处理[1](https://developer.aliyun.com/article/765311) 。通过这一算子，可以有效地整合和优化数据变更记录，确保数据的一致性和准确性。该状态算子会在以下两种场景出现 [2](https://issues.apache.org/jira/browse/FLINK-29849)：
- 使用了带有主键的 upsert 源表
  - upsert 源表特指在保持主键顺序一致性的前提下，仅产生基于主键的 UPDATE（包括 INSERT 和 UPDATE_AFTER）及 DELETE 操作的变更数据表。例如，upsert-kafka 便是支持这类操作的典型连接器之一。此外，用户也可以通过重写自定义源表连接器中的 getChangelogMode 方法，实现 upsert 功能。
  ```java
  @Override
  public ChangelogMode getChangelogMode() {
      return ChangelogMode.upsert();
  }
  ```
- 用户显式设置 'table.exec.source.cdc-events-duplicate' = 'true'
  - 解析：
    - 在使用 at-least-once 语义进行CDC事件处理时，可能会产生重复的变更日志。在需要 exactly-once 语义时，用户需要开启此配置项来对变更日志进行去重。
  - 举例：
    - 当出现该算子时，上游数据将按照 FlinkSQL 源表 DDL 中定义的主键做一次 hash shuffle 操作后使用 ValueState 来存储当前主键下最新的整行记录，以更新状态向下游发送变更。故处理第二条 -U(2, 'Jerry', 77) 的时候 state 已经是 empty 了, 说明截止目前 +I/+UA 和 -D/-UB 已经两两抵销, 当前这条 retract 消息就是重复的, 可以丢弃。

#### 1.1.2 SinkUpsertMaterializer

SinkUpsertMaterializer 是一种状态算子，专门用于处理具有主键定义的结果表，并确保数据的物化操作 符合upsert语义。在数据流更新过程中，如果无法保证upsert的特定要求，即按照主键进行更新时保持数据的唯一性和有序性，优化器会自动引入此算子。它通过维护基于结果表主键的状态信息，来确保这些约束得到满足。

具体来说，upsert语义包含两个方面：唯一性和有序性。唯一性指的是在传统数据库中，主键必须唯一，不能有重复的值。而有序性则意味着对于任何一次主键的更新，相关的变更日志必须遵循特定的顺序，即UPDATE_BEFORE操作必须在UPDATE_AFTER操作之前进行。

为了实现这一功能，当SinkUpsertMaterializer被触发时，系统会首先根据FlinkSQL结果表DDL中定义的主键，对上游数据执行hash shuffle操作。然后，使用ValueState来存储每个主键下的所有不可合并数据。这里的“合并”指的是，对于特定的数据项，增加（+I或+U）和删除（-D和-U）操作可以相互抵消，从而保持数据的一致性。更多关于这一主题的深入讨论和解释，可以参考相关文档[3]。



常见的三种场景：

① 结果表定义主键，而写入该结果表的数据丢失了唯一性

解析：这些操作通常包括但不限于

源表缺少主键，而结果表却设置了主键。

在向结果表插入数据时，忽略了主键列的选择，或者错误地使用了源表的非主键数据填充结果表的主键。

源表的主键数据在转换或经过分组聚合后出现精度损失，例如将BIGINT类型降为INT类型。

对源表的主键列或经过分组聚合之后的唯一键进行了运算，如数据拼接或将多个主键合并为单一字段。

举例：

CREATE TABLE students (
  student_id BIGINT NOT NULL,
  student_name STRING NOT NULL,
  course_id BIGINT NOT NULL,
  score DOUBLE NOT NULL,
  PRIMARY KEY(student_id) NOT ENFORCED
) WITH (...);

CREATE TABLE performance_report (
  student_info STRING NOT NULL PRIMARY KEY NOT ENFORCED,
  avg_score DOUBLE NOT NULL
) WITH (...);

CREATE TEMPORARY VIEW v AS
SELECT student_id, student_name, AVG(score) AS avg_score
FROM students
GROUP BY student_id, student_name;

-- 将分组聚合后的 key 进行拼接当作主键写入结果表，但实际上已经丢失了唯一性约束
INSERT INTO performance_report
SELECT
  CONCAT('id:', student_id, ',name:', student_name) AS student_info,
  avg_score
FROM v;
② 结果表的确立依赖于主键的设定，然而在数据输入过程中，其原有的顺序性却遭到破坏。

解析：这些操作通常包括但不限于

双流 Join 时若一方数据未通过主键与另一方关联，而结果表的主键列又是基于另一方的主键列生成的，这便可能导致数据顺序的混乱。

举例：假设我们有两个源数据表 s1 和 s2，以及一个目标数据表 t1。s1 表包含 id 和 level 字段，而 s2 表包含 id 和 attr 字段。目标是将这两个源表通过 level 字段关联起来，并插入到目标表 t1 中。

-- CDC source tables:  s1 & s2
s1: id BIGINT, level BIGINT, PRIMARY KEY(id)
s2: id BIGINT, attr VARCHAR, PRIMARY KEY(id)

-- sink table: t1
t1: id BIGINT, level BIGINT, attr VARCHAR, PRIMARY KEY(id)

-- join s1 and s2 and insert the result into t1
INSERT INTO t1
SELECT
  s1.*, s2.attr
FROM s1 JOIN s2
  ON s1.level = s2.id
s1表中ID=1的数据发生一次数据插入和一次数据更新，经过Flink SQL 共记录三次事件：

初始插入：用户ID为1，level设定为10。

更新前后：用户ID为1的level首先被标记为更新（-U），随即更新为20（+U）。

+I(id=1, level=10)
-U(id=1, level=10)
+U(id=1, level=20)
s2 表收到了如下一条对于s2表，接收到了一条新的插入事件：插入一条新的用户数据记录，其ID为20，attr 为'b1'。

数据

+I(id=20, attr='b1')
在进行数据合并（join）操作前，系统会先根据关联字段进行哈希洗牌，以准备数据。以s1表为例，若使用level字段作为关联依据，在分布式并发环境下，对于同一记录的变更（如-U(id=1, level=10)和+U(id=1, level=20)）可能会被分配到不同的子任务（subtask）中。在数据流经Sink操作时，上游join操作的子任务顺序是无法预测的。如果+U(id=1, level=20)这个变更先于-U(id=1, level=10)被处理，那么最终记录id=1可能会被错误地删除。这个例子说明了在处理过程中无法确保事件的顺序性，从而导致结果的不准确性。



图片


③ 用户明确配置了 table.exec.sink.upsert-materialize 参数为 'FORCE'

解释：该配置项用于强制启用 sink 节点的数据物化功能。即便结果表的 DDL 未指定主键，优化器也会插入一个 SinkUpsertMaterializer 状态节点，以确保数据的物理化处理。

（3）LookupJoin
在处理LookupJoin操作时，若用户主动配置了系统优化选项'table.optimizer.non-deterministic-update.strategy'为'TRY_RESOLVE'，且优化器识别到潜在的非确定性更新问题[4]，则系统会尝试采取特殊措施以解决这一问题。具体而言，若通过引入一个状态算子能够消除非确定性，优化器便会自动创建一个带状态的LookupJoin算子。

这种带状态的LookupJoin算子主要适用于以下情况：结果表被定义了主键，而这些主键完全或部分来自于维度表（维表），同时维表中的数据可能会发生变化（例如通过变更数据捕获，即CDC Lookup Source机制）。此外，用于Join操作的字段在维表中并非主键。在这种情况下，带状态的LookupJoin算子能够有效地处理数据的动态变化，确保查询结果的准确性和一致性。

5.1.2 基于 SQL 操作产生的状态算子
基于 SQL 操作产生的状态算子，按状态清理机制可以分为 TTL 过期和依赖 watermark 推进两类。具体说来，Flink SQL 里有部分状态算子的生命周期不是由 TTL 来控制的，比如 Window 相关的状态计算，如 WindowAggregate、WindowDeduplicate、WindowJoin、WindowTopN 等。它们的状态清理主要依赖于 watermark 的推进，当 watermark 超过窗口结束时间时，内置的定时器就会触发状态清理。

状态算子	如何产生	状态清理机制
Deduplicate	使用 row_number 语句，order by 的字段必须为 time attribute (event time 或 processing time )，且只取第一条	TTL
RegularJoin	使用 join 语句，等值条件里不包含 time attribute 字段
GroupAggregate	使用 group by 语句进行分组聚合，如 sum/count/min/max/first_value/last_value，或使用 distinct 关键字
GlobalGroupAggregate	分组聚合开启 local-global 优化
IncrementalGroupAggregate	当存在两层分组聚合操作并开启两阶段优化时，内层聚合对应的状态算子GlobalGroupAggregate 和外层聚合对应的 LocalGroupAggregate 被合并成一个 IncrementalGroupAggregate
Rank	使用 row_number 语句，order by 的字段必须为非 time attribute 字段
GlobalRank	使用 row_number 语句，order by 的字段必须为非 time attribute 字段，并开启 local-global 优化
IntervalJoin	使用 join 语句，等值条件里包含时间属性（time attribute）字段，可以是事件时间（event time）也可以是处理时间（processing time），例如L.time between R.time + X and R.time + Y   -- 或  R.time between L.time - Y and L.time - X	watermark
TemporalJoin	使用基于事件时间（event time）的 inner 或 left join 语句
WindowDeduplicate	基于 Window TVF 的去重操作
WindowAggregate	基于 Window TVF 聚合
GlobalWindowAggregate	基于 Window TVF 聚合+开启两阶段优化
WindowJoin	基于 Window TVF 的关联
WindowRank	基于 Window TVF 的排序
GroupWindowAggregate	基于 legacy 语法的 Window 聚合

5.2 问题诊断方法
同上节中的诊断方法：Flink⼤状态作业调优实践指南：Datastream 作业篇


5.3 调优方法
5.3.1 主动避免生成不必要的状态算子
基于 SQL 操作的状态计算一般很难避免，这里主要针对优化器自动推导的算子进行讨论。

（1）ChangelogNormalize
在使用 upsert source 进行数据处理时，我们需注意其ChangelogNormalize 这种状态节点的生成。通常情况下，除了事件时间的时态关联（event time temporal join）之外，其他 upsert source 应用场景都会产生该状态节点。因此，在选择 upsert-kafka 或类似的 upsert 连接器时，应首先评估具体的使用场景。对于非事件时间关联的场景，我们应特别关注状态算子的状态指标（state metrics）。由于状态节点是基于 KeyedState 的，当源表的主键数量庞大时，状态节点的规模也会相应增加。如果物理表的主键更新频繁，状态节点也将频繁地被访问和修改。从实践角度而言，像数据同步类的场景，最好避免使用 upsert-kafka 作为源表连接器，同时在数据同步工具上也最好选择能够保证 exactly-once 语义的。

（2）SinkUpsertMaterializer
在table.exec.sink.upsert-materialize配置项中，AUTO作为其预设选项，表明系统会自动判断数据的一致性，尤其是在变更日志（changelog）出现无序的情况下。该机制确保了通过引入 SinkUpsertMaterializer 算子来维持数据处理的准确性。然而，这并不意味着每当该算子被激活，数据就一定存在无序问题。例如，在先前的讨论中，我们提到了将多个分组键（group by key）合并的操作，这种情况下，优化器无法准确推导出upsert键，因此出于安全考虑，会默认添加 SinkUpsertMaterializer。然而，对于用户而言，如果他们对数据的分布有充分的了解，即便不使用这个状态算子，也能够确保输出结果的正确性，从而在数据正确性和性能上都得到保证。

为了从实际操作层面了解 SinkUpsertMaterializer 的使用情况，用户可以通过检查作业的最后一个节点来确认其是否被激活。在作业的运行拓扑图中，该算子通常会与 sink 算子一起显示，形成一个操作链。通过这种方式，用户可以直观地监控和评估SinkUpsertMaterializer在数据处理过程中的实际应用情况，从而做出更加合理的优化决策。


图片



图片


在检测到生成了特定算子且数据计算无误的情况下，可以通过调整配置项 'table.exec.sink.upsert-materialize' 为 'NONE'，以避免自动添加 SinkUpsertMaterializer。为了提升用户体验并协助用户更便捷地识别此类问题，阿里云实时计算Flink版在VVR-8.0.x版本中引入了SQL 执行计划智能分析功能。我们建议用户密切关注计划正确性建议，以便在遇到相关问题时能够得到及时的提示，如下面的图示所示。


图片


5.3.2 减少状态访问频次：开启 mini-batch
在对延时要求不高（比如分钟级别的更新）的场景下，开启 mini-batch 攒批优化将会减少 state 的访问和更新频率，提升吞吐 [5] 高性能 FlinkSQL 优化技巧。

阿里云实时计算Flink版可以应用 mini-batch 的状态算子列举如下：

状态算子	社区是否支持	备注
ChangelogNormalize	Y
Deduplicate	Y	可配置 table.exec.deduplicate.mini-batch.compact-changes-enabled制定是否在基于 event time 去重时压缩 changelog
GroupAggregateGlobalGroupAggregateIncrementalGroupAggregate	Y
RegularJoin	1.19 及以上支持	需额外配置 table.exec.stream.join.mini-batch-enabled 开启 mini-batch join 优化。适用于对于更新流 + outer join 场景
5.3.3 减少状态大小：设置合理生命周期
在优化计算系统时，关键在于精简状态数据以提高性能。通过减少不必要的状态信息，我们可以显著提升状态访问的速度。TTL（Time-to-Live）策略在此过程中扮演着重要角色，它通过设定数据的存活时间来控制状态数据的规模。

具体来说，当数据首次进入系统并被处理后，它会存储在状态内存中。当下一次相同主键的数据到来时，系统会使用之前存储的状态数据进行计算，并更新其访问时间。这一过程是实时计算的核心，因为它依赖于数据的持续流动。

然而，如果数据在设定的TTL时间窗口内未被再次访问，它将被系统视为过期，并从状态存储中清除。这样，通过合理设定TTL值，我们不仅可以维持计算的精确性，还能及时清理陈旧数据，有效减少状态内存的占用，进而降低系统内存负担，提升计算效率和系统稳定性。

请注意，TTL开关在不同状态下并不保证相互兼容。当尝试在已启用TTL的作业上尝试关闭TTL配置，或者反过来操作时，将会导致兼容性失败并引发StateMigrationException异常，这一问题与社区版本的行为一致。

（1）如何设置合理的 TTL

在对SQL作业进行状态管理时，我们可以通过设置table.exec.state.ttl参数来控制作业状态的生命周期。该参数代表状态信息的存活时间，单位为小时。默认情况下，其值为0，表示状态信息不会自动过期，即一直保持有效。

在阿里云实时计算的Flink版本中，为了更好地进行作业状态的维护和管理，系统默认将此参数设置为36小时。这意味着，如果在作业配置中未对该参数进行修改，那么作业状态信息将在36小时后自动过期并清除。这一设置有助于保持系统资源的有效利用，避免过时状态信息的堆积。

若要查看或修改此参数，可以在作业运维界面中找到“作业探查”选项，点击进入后选择“Job Manager - 配置”标签页。在这里，你可以看到当前作业的table.exec.state.ttl参数值，也可以在作业启动前，通过参数配置界面对其进行调整，以满足不同的运维需求和策略。



图片


在对Flink SQL作业进行TTL（Time-To-Live）配置时，应避免设置过短或过长，以免影响数据处理的准确性和资源的有效利用。过短的TTL可能导致数据未能及时处理，从而产生不符合预期的计算结果，如在聚合或连接操作后出现错误。例如，我们曾处理过用户反馈的聚合或连接结果异常问题，原因是部分数据晚到，而相关状态已过期。相反，过长的TTL会无端消耗资源，降低作业的稳定性。

为确保数据处理的合理性和资源的有效性，建议根据数据特性和业务需求进行恰当的TTL设置。例如，如果计算周期以自然天为单位，并且数据跨天漂移不会超过1小时，那么将TTL设定为25小时即可满足需求。数据开发人员应深入了解业务场景和计算逻辑，以实现最佳的平衡。

此外，针对双流连接场景，Flink SQL自VVR-8.0.1版本起，支持通过JOIN_STATE_TTL提示为左流和右流分别设置不同的生命周期。这一改进允许为各自数据流定制生命周期，有效减少不必要的状态存储开销，从而优化作业性能。开发者可以根据左右流数据的实际生命周期需求，灵活配置，以达到节省资源和提高作业效率的目的。

SELECT /*+ JOIN_STATE_TTL('left_table' = '..', 'right_table' = '..') *
FROM left_table [LEFT | RIGHT | INNER] JOIN right_table ON ...
以下是用户在使用了 JOIN_STATE_TTL hint 前后的 state 大小对比：

（2）优化前的作业状态：
双流join操作，左流数据量大，约为右流的20至50倍。

右流需长期保存数据，原定为18天。

为提升性能，实际将右流的保存周期缩短至10天，导致数据正确性受损。

join操作的状态大小约为5.8TB。

单作业所需资源高达700计算单元（CU）。

（3）优化后的改进：
通过合理设置JOIN_STATE_TTL提示，左流可缩短至12小时，右流保持18天的保存周期，无需牺牲数据完整性。

join操作的状态大小大幅减少至约590GB，仅为原来的十分之一。

资源消耗显著降低，从700 CU降至200-300CU，节省了50%至70%的资源。

通过这一改动，用户不仅能够保持数据的完整性，还能大幅提升作业效率和资源利用率。这样的优化对于处理大规模数据流具有重要意义，能够显著提升数据处理能力和降低运行成本。


图片

图片

5.3.4 减少状态大小：命中更优的执行计划
在生成执行计划时，优化器会结合输入 SQL 和配置选择相应的 state 实现。

（1）利用主键优化双流连接
当连接键（join key）包含主键时，系统采用ValueState<RowData>进行数据存储，这样可以为每个连接键仅保留一条最新记录，实现存储空间的最大化节省。

如果连接操作使用了非主键字段，即使已定义主键，系统会使用MapState<RowData, RowData>进行存储，以便为每个连接键保存来自源表的、基于主键的最新记录。

在未定义主键的情况下，系统将使用MapState<RowData, Integer>存储数据，记录每个连接键对应的整行数据及其出现次数。

因此，建议在DDL中声明主键，并在双流连接时优先使用主键，以优化存储效率。

（2）优化append_only流去重操作

使用row_number函数替代first_value或last_value函数进行去重，可以更有效地保留首次或最新出现的记录，对应着两个场景，row_number函数生成的Deduplicated算子仅保留出现过的key，或保留key及其最后一次出现的记录。

（3）提升聚合查询性能

在进行多维度统计，如计算全网UV、手机客户端UV、PC端UV等时，推荐使用AGG WITH FILTER语法替代传统的CASE WHEN语法。这样做的好处是，SQL优化器能够识别Filter参数，使得在同一个字段上根据不同条件计算COUNT DISTINCT时能够共享状态信息，减少状态的读写次数。根据性能测试结果，采用AGG WITH FILTER语法相比CASE WHEN可以提升性能达一倍。

5.3.5 减少状态大小：调整多流 join 顺序缓解 state 放大

Flink 在处理数据流时，采用了二进制哈希连接（binary hash join）的方式。在示例中，A 与 B 的连接结果会导致数据存储的冗余，这种冗余程度与连接操作的频率成正比。随着加入连接的流数量增加，状态（state）的冗余问题会变得更加严重。



图片


为了优化这一问题，我们可以策略性地调整连接的顺序。具体来说，可以先将数据量较小的流进行连接，而将数据量大的流放在最后进行。这样的顺序调整有助于减轻状态冗余带来的放大效应，从而提高数据处理的效率和性能。

5.3.6 尽可能减少读盘
参考“Flink⼤状态作业调优实践指南：Datastream 作业篇” 中的调优方法

参考文献
[1] 深入分析 Flink SQL 工作机制：

https://developer.aliyun.com/article/765311

[2] 在使用 EvenTimeTemporalJoin 时不会产生 ChangelogNormalize，详见 FLINK-29849：

https://issues.apache.org/jira/browse/FLINK-29849

[3] Flink SQL Secrets: Mastering the Art of Changelog Event Out-of-Orderness：

https://www.ververica.com/blog/flink-sql-secrets-mastering-the-art-of-changelog-event-out-of-orderness

[4] 如何消除流查询的不确定性影响：

https://nightlies.apache.org/flink/flink-docs-release-1.18/zh/docs/dev/table/concepts/determinism/#33-如何消除流查询的不确定性影响

[5] 高性能 FlinkSQL 优化技巧：

https://help.aliyun.com/zh/flink/user-guide/optimize-flink-sql?spm=a2c4g.11186623.0.0.2790ff53sQpyuy
