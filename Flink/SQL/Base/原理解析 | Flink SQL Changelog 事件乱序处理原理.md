本文围绕 Flink SQL 实时数据处理中的 Changelog 事件乱序问题，分析了 Flink SQL 中 Changelog 事件乱序问题的原因，并提供了解决方案以及处理 Changelog 事件乱序的建议。以帮助您更好地理解 Changelog 的概念和应用，更加高效地使用 Flink SQL 进行实时数据处理。

## 1. Flink SQL 中的 Changelog

### 1.1 Changelog 介绍

在关系数据库领域，MySQL 使用 binlog（二进制日志）记录数据库中所有修改操作，包括 INSERT、UPDATE 和 DELETE 操作。类似地，Flink SQL 中的 Changelog 主要记录数据变化，以实现增量数据处理。

在 MySQL 中，binlog 可以用于数据备份、恢复、同步和复制。通过读取和解析 binlog 中的操作记录，可以实现增量数据同步和复制。变更数据捕获（CDC）作为一种常用的数据同步技术，常被用于监控数据库中的数据变化，并将其转换为事件流进行实时处理。CDC 工具可用于将关系数据库中的数据变化实时传输到其他系统或数据仓库，以支持实时分析和报告。当前常用的 CDC工 具包括 Debezium 和 Maxwell。Flink 通过 [FLINK-15331](https://issues.apache.org/jira/browse/FLINK-15331) 支持了CDC，可以实时地集成外部系统的 CDC 数据，并实现实时数据同步和分析。

### 1.2 Changelog 事件生成和处理

binlog 和 CDC 是与 Flink 集成的外部 Changelog 数据源，Flink SQL 内部也会生成 Changelog 数据。为了区分事件是否为更新事件，我们将仅包含 INSERT 类型事件的 Changelog 称为追加流(Append-only)或非更新流，而同时包含其他类型（例如 UPDATE）事件的 Changelog 称为更新流。Flink 中的一些操作（如分组聚合和去重）可以产生更新事件，生成更新事件的操作通常会使用状态，这类操作被称为状态算子。需要注意的是，并非所有状态算子都支持处理更新流。例如，Over 窗口聚合和 Interval Join 暂不支持更新流作为输入。

### 1.3 Changelog的事件类型

[FLINK-6047](https://issues.apache.org/jira/browse/FLINK-6047) 引入了回撤机制，使用 INSERT 和 DELETE 两种事件类型（尽管数据源仅支持 INSERT 事件），实现了流 SQL 算子的增量更新算法。[FLINK-16987](https://issues.apache.org/jira/browse/FLINK-16987) 以后，Changelog 事件类型被重构为四种类型（如下），形成一个完整的 Changelog 事件类型体系，便于与 CDC 生态系统连接。
```java
/**
 * A kind of row in a Changelog.
 */
@PublicEvolving
public enum RowKind {

	/**
	 * Insertion operation.
	 */
	INSERT,

	/**
	 * Previous content of an updated row.
	 */
	UPDATE_BEFORE,

	/**
	 * New content of an updated row.
	 */
	UPDATE_AFTER,

	/**
	 * Deletion operation.
	 */
	DELETE
}
```

Flink 不使用包含 UPDATE_BEFORE 和 UPDATE_AFTER 的复合 UPDATE 事件类型的原因主要有两个方面：
- 拆分的事件无论是何种事件类型（仅RowKind不同）都具有相同的事件结构，这使得序列化更简单。如果使用复合UPDATE事件，那么事件要么是异构的，要么是 INSERT 或 DELETE 事件对齐 UPDATE 事件（例如，INSERT事件仅含有UPDATE_AFTER，DELETE事件仅含有UPDATE_BEFORE）。
- 在分布式环境下，经常涉及数据shuffle（例如Join、聚合）。即使使用复合UPDATE事件，有时仍需将其拆分为单独的DELETE和INSERT事件进行shuffle，例如下面的示例。

### 1.4 示例

下面是一个复合 UPDATE 事件必须拆分为 DELETE 和 INSERT 事件的场景示例。本文后续也将围绕此 SQL 作业示例讨论 Changelog 事件乱序问题并提供相应的解决方案。
```sql
-- CDC source tables:  s1 & s2
CREATE TEMPORARY TABLE s1 (
  id BIGINT,
  level BIGINT,
  PRIMARY KEY(id) NOT ENFORCED
)WITH (...);

CREATE TEMPORARY TABLE s2 (
  id BIGINT,
  attr VARCHAR,
  PRIMARY KEY(id) NOT ENFORCED
)WITH (...);

-- sink table: t1
CREATE TEMPORARY TABLE t1 (
  id BIGINT,
  level BIGINT,
  attr VARCHAR,
  PRIMARY KEY(id) NOT ENFORCED
)WITH (...);

-- join s1 and s2 and insert the result into t1
INSERT INTO t1
SELECT
  s1.*, s2.attr
FROM s1 JOIN s2
ON s1.level = s2.id;
```
假设源表 s1 中 id 为 1 的记录的 Changelog 在时间 t0 插入(id=1, level=10)，然后在时间 t1 将该行更新为(id=1, level=20)。这对应三个拆分事件：

| s1 | 事件类型 |
| :------------- | :------------- |
| +I（id=1，level=10） | INSERT |
| -U（id=1，level=10） | UPDATE_BEFORE |
| +U（id=1，level=20） | UPDATE_AFTER |

源表 user_detail 的主键是 user_id，但 Join 操作需要按 level_id 列进行 shuffle（见子句ON）。

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/5166786171/p694577.png)

如果 Join 算子的并发数为2，那么以上三个事件可能会被发送到两个任务中。即使使用复合 UPDATE 事件，它们也需要在 shuffle 阶段拆分，来保证数据的并行处理。

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/5166786171/p694580.png)

## 2. Changelog 事件乱序问题

### 2.1 乱序原因

假设示例中表 s2 已有两行数据进入 Join 算子（`+I（id=10，attr=a1`)，`+I（id=20，attr=b1）`），Join 运算符从表 s1 新接收到三个 Changelog 事件。在分布式环境中，实际的 Join 在两个任务上并行处理，下游算子（示例中为 Sink 任务）接收的事件序列可能情况如下所示。

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/5166786171/p801579.png)

| 情况1 | 情况2 | 情况3 |
| :------------- | :------------- | :------------- |
| +I (id=1，level=10，attr='a1')<br>-U (id=1，level=10，attr='a1')<br>+U (id=1，level=20，attr='b1')   | +U (id=1，level=20，attr='b1')<br>+I (id=1，level=10，attr='a1')<br>-U (id=1，level=10，attr='a1') | +I (id=1，level=10，attr='a1')<br>+U (id=1，level=20，attr='b1')<br>-U (id=1，level=10，attr='a1')<br> |

情况 1 的事件序列与顺序处理中的事件序列相同。情况 2 和情况 3 显示了 Changelog 事件在 Flink SQL 中到达下游算子时的乱序情况。乱序情况可能会导致不正确的结果。在示例中，结果表声明的主键是 id，外部存储进行 upsert 更新时，在情况 2 和 3 中，如果没有其他措施，将从外部存储不正确地删除 id=1 的行，而期望的结果是`(id=1, level=20, attr='b1')`。

### 2.2 使用 SinkUpsertMaterializer 解决

在示例中，Join 操作生成更新流，其中输出包含 INSERT 事件（`+I`）和 UPDATE 事件（`-U`和`+U`），如果不正确处理，乱序可能会导致正确性问题。

#### 2.2.1 唯一键与upsert键

`唯一键`是指 SQL 操作后满足唯一约束的列或列组合。在本示例中`(s1.id)`、`(s1.id, s1.level)`和`(s1.id, s2.id)`这三组都是唯一键。

Flink SQL 的 Changelog 参考了 binlog 机制，但实现方式更加简洁。Flink 不再像 binlog 一样记录每个更新的时间戳，而是通过 planner 中的全局分析来确定主键接收到的更新历史记录的排序。如果某个键维护了唯一键的排序，则对应的键称为 upsert 键。对于存在 upsert 键的情况，下游算子可以正确地按照更新历史记录的顺序接收 upsert 键的值。如果 shuffle 操作破坏了唯一键的排序，upsert 键将为空，此时下游算子需要使用一些算法（例如计数算法）来实现最终的一致性。

在示例中，表 s1 中的行根据列 level 进行 shuffle。Join 生成多个具有相同 `s1.id` 的行，因此 Join 输出的 upsert 键为空（即 Join 后唯一键上不存在排序）。此时，Flink 需存储所有输入记录，然后检查比较所有列以区分更新和插入。

此外，结果表的主键为列 id。Join 输出的 upsert 键与结果表的主键不匹配，需要进行一些处理将 Join 输出的行进行正确转换为结果表所需的行。

#### 2.2.2 SinkUpsertMaterializer

根据唯一键与 upsert 键的内容，当 Join 输出的是更新流且其 upsert 键与结果表主键不匹配时，需要一个中间步骤来消除乱序带来的影响，以及基于结果表的主键产生新的主键对应的 Changelog 事件。Flink 在 Join 算子和下游算子之间引入了 SinkUpsertMaterializer 算子（[FLINK-20374](https://issues.apache.org/jira/browse/FLINK-20374?page=com.atlassian.jira.plugin.system.issuetabpanels%3Aall-tabpanel)）。

结合乱序原因中的 Changelog 事件，可以看到 Changelog 事件乱序遵循着一些规则。例如，对于一个特定的 upsert 键（或 upsert 键为空则表示所有列），事件 `ADD（+I、+U）` 总是在事件 `RETRACT（-D、-U）` 之前发生；即使涉及到数据 shuffle，相同 upsert 键的一对匹配的 Changelog 事件也总是被相同的任务处理。这些规则也说明了为什么示例仅存在乱序原因中三个 Changelog 事件的组合。

SinkUpsertMaterializer 就是基于上述规则实现的，其工作原理如下图所示。SinkUpsertMaterializer 在其状态中维护了一个 RowData 列表。当 SinkUpsertMaterializer 被触发，在处理输入行时，它根据推断的 upsert 键或整行（如果 upsert 键为空）检查状态列表中是否存在相同的行。在 ADD 的情况下添加或更新状态中的行，在 RETRACT 的情况下从状态中删除行。最后，它根据结果表的主键生成 Changelog 事件，更多详细信息请参见 [SinkUpsertMaterializer 源代码](https://github.com/apache/flink/blob/release-1.17/flink-table/flink-table-runtime/src/main/java/org/apache/flink/table/runtime/operators/sink/SinkUpsertMaterializer.java)。

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/7341918571/CAEQQxiBgMCL2pX0_RgiIDViN2ZjY2Q3NjkyMjQ5ZWI4NjllNDc1NGI3ZmEzNDc53789734_20240518215802.438.svg)

通过 SinkUpsertMaterializer，将示例中 Join 算子输出的 Changelog 事件处理并转换为结果表主键对应的 Changelog 事件，结果如下图所示。根据 SinkUpsertMaterializer 的工作原理，在情况2中，处理 `-U(id=1，level=10，attr='a1')` 时，会将最后一行从状态中移除，并向下游发送倒数第二行；在情况3中，当处理 `+U (id=1,level=20,attr='b1')` 时，SinkUpsertMaterializer 会将其原样发出，而当处理 `-U(id=1,level=10,attr='a1')` 时，将从状态中删除行而不发出任何事件。最终，通过 SinkUpsertMaterializer 算子情况2和3也会得到期望结果 `(id=1,level=20,attr='b1')`。

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/5166786171/p694613.png)

## 3. 常见场景

触发 SinkUpsertMaterializer 算子的常见场景如下所示。

- 结果表定义主键，而写入该结果表的数据丢失了唯一性。通常包括但不限于以下操作：
	- 源表缺少主键，而结果表却设置了主键。
	- 向结果表插入数据时，忽略了主键列的选择，或错误地使用了源表的非主键数据填充结果表的主键。
	- 源表的主键数据在转换或经过分组聚合后出现精度损失。例如，将BIGINT类型降为INT类型。
	- 对源表的主键列或经过分组聚合之后的唯一键进行了运算，如数据拼接或将多个主键合并为单一字段。

		```sql
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

		-- 将分组聚合后的key进行拼接当作主键写入结果表，但实际上已经丢失了唯一性约束
		INSERT INTO performance_report
		SELECT
		  CONCAT('id:', student_id, ',name:', student_name) AS student_info,
		  avg_score
		FROM v;
		```
- 结果表的确立依赖于主键的设定，然而在数据输入过程中，其原有的顺序性却遭到破坏。
	- 例如本文的示例，双流Join时若一方数据未通过主键与另一方关联，而结果表的主键列又是基于另一方的主键列生成的，这便可能导致数据顺序的混乱。
- 明确配置了 `table.exec.sink.upsert-materialize` 参数为'force'，配置详情请参见下方的参数设置。

## 4. 使用建议

正如前面所提到的，SinkUpsertMaterializer 在其状态中维护了一个 RowData 列表。这可能会导致状态过大并增加状态访问I/O的开销，最终影响作业的吞吐量。因此，应尽量避免使用它。

### 4.1 参数设置

SinkUpsertMaterializer 可以通过 `table.exec.sink.upsert-materialize` 进行配置：
- `auto`（默认值）：Flink 会从正确性的角度推断出乱序是否存在，如果必要的话，则会添加 SinkUpsertMaterializer。
- `none`：不使用。
- `force`：强制使用。即便结果表的 DDL 未指定主键，优化器也会插入 SinkUpsertMaterializer 状态节点，以确保数据的物理化处理。

需要注意的是，设置为 auto 并不一定意味着实际数据是乱序的。例如，使用 grouping sets 语法结合 coalesce 转换 null 值时，SQL planner 可能无法确定由 grouping sets与 coalesce 组合生成的 upsert 键是否与结果表的主键匹配。出于正确性的考虑，Flink 将添加 SinkUpsertMaterializer。如果一个作业可以在不使用 SinkUpsertMaterializer 的情况下生成正确的输出，建议设置为 none。

### 4.2 避免使用SinkUpsertMaterializer

为了避免使用 SinkUpsertMaterializer 您可以：
- 确保在进行去重、分组聚合等操作时，所使用的分区键要与结果表的主键相同。
- 如果单并发可以处理对应的数据量，改成单并发可以避免处理过程中产生额外的乱序（原始输入的乱序除外），此时在作业参数中设置 `table.exec.sink.upsert-materialize` 为 none 显式关闭生成 SinkUpsertMaterializer 节点。


若必须使用 SinkUpsertMaterializer，需注意以下事项：
- 避免在写入结果表时添加由非确定性函数（如CURRENT_TIMESTAMP、NOW）生成的列，可能会导致Sink输入在没有upsert键时，SinkUpsertMaterializer的状态异常膨胀。
- 如果已出现 SinkUpsertMaterializer 算子存在大状态的情况并影响了性能，请考虑增加作业并发度。

### 4.3 使用注意事项

SinkUpsertMaterializer 虽然解决了 Changelog 事件乱序问题，但可能引起持续状态增加的问题。主要原因有：
- 状态有效期过长（未设置或设置过长的状态TTL）。但如果 TTL 设置过短，可能会导致 [FLINK-29225](https://issues.apache.org/jira/browse/FLINK-29225) 中描述的问题，即本应删除的脏数据仍保留在状态中。当消息的 DELETE 事件与其 ADD 事件之间的时间间隔超过配置的 TTL 时会出现这种情况，此时，Flink 会在日志中产生一条如下警告信息。
```java
int index = findremoveFirst(values, row);     
if (index == -1) {          
    LOG.info(STATE_CLEARED_WARN_MSG);          
    return;     
}
```
- 您可以根据业务需要设置合理的 TTL，具体操作请参见运行参数配置。
- 当 SinkUpsertMaterializer 输入的更新流无法推导出 upsert 键，并且更新流中存在非确定性列时，将无法正确删除历史数据，这会导致状态持续增加。


> [Changelog事件乱序处理原理](https://help.aliyun.com/zh/flink/realtime-flink/use-cases/processing-changelog-events-out-of-orderness-in-flink-sql?scm=20140722.S_help%40%40%E6%96%87%E6%A1%A3%40%402411139._.ID_help%40%40%E6%96%87%E6%A1%A3%40%402411139-RL_%E7%8A%B6%E6%80%81%E4%BF%9D%E7%95%99-LOC_doc%7EUND%7Eab-OR_ser-PAR1_2102029b17585524621276387de3f6-V_4-PAR3_o-RE_new10-P0_8-P1_0&spm=a2c4g.11186623.help-search.i19)
