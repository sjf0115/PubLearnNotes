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
SELECT s1.*, s2.attr
FROM s1
JOIN s2
ON s1.level = s2.id;
```
假设源表 s1 中 id 为 1 的记录的 Changelog 在时间 t0 插入(id=1, level=10)，然后在时间 t1 将该行更新为(id=1, level=20)。这对应三个拆分事件：

| s1 | 事件类型|
| :------------- | :------------- |
| +I（id=1，level=10） | INSERT |
| -U（id=1，level=10） | UPDATE_BEFORE |
| +U（id=1，level=20） | UPDATE_AFTER |

源表 s1 的主键是 id，但 Join 操作需要按 level 列进行 shuffle（见子句ON）。

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/5166786171/p694577.png)

如果 Join 算子的并发数为2，那么以上三个事件可能会被发送到两个任务中。即使使用复合 UPDATE 事件，它们也需要在 shuffle 阶段拆分，来保证数据的并行处理。

![](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/5166786171/p694580.png)












> [Changelog事件乱序处理原理](https://help.aliyun.com/zh/flink/realtime-flink/use-cases/processing-changelog-events-out-of-orderness-in-flink-sql?scm=20140722.S_help%40%40%E6%96%87%E6%A1%A3%40%402411139._.ID_help%40%40%E6%96%87%E6%A1%A3%40%402411139-RL_%E7%8A%B6%E6%80%81%E4%BF%9D%E7%95%99-LOC_doc%7EUND%7Eab-OR_ser-PAR1_2102029b17585524621276387de3f6-V_4-PAR3_o-RE_new10-P0_8-P1_0&spm=a2c4g.11186623.help-search.i19)
