

> 原文：[非确定性更新（NDU）问题探索和规避](https://cloud.tencent.com/developer/article/2175582)

## 1. 问题背景

**非确定性函数**（Non-Deterministic Functions）一直是影响流处理系统状态匹配的梦魇。例如用户在定义源表时，某个虚拟列字段调用了 RAND()、NOW()、UUID() 等函数；那么每次作业崩溃后重新运行，即使输入的数据流完全一致，输出结果也未必相同。此外，如果用户使用维表 JOIN，而外部维表随时在更新时，每次 JOIN 的结果也可能不同。

对于纯 Append 流（只会输出新数据，不会更新现有结果）而言，这可能并不是太大的问题；对于 Upsert 流（如果有同主键的记录就更新，没有就新插入一条），也可以认为新数据是对旧数据的替代，因此用户也**可接受**。然而对于有回撤操作的 Retract 流，由于涉及 Flink 内部的状态匹配，因此前后不数据不一致会造成**严重后果**。

> 对上述概念不熟悉的读者，可以参考 Flink [动态表](https://nightlies.apache.org/flink/flink-docs-release-1.15/zh/docs/dev/table/concepts/dynamic_tables/) 官方文档。

## 2. 案例讲解

除了上述提到的非确定函数、维表 JOIN 以外，还有一个因素会造成该问题。例如我们有如下的 MySQL CDC 数据源表，其中 op_type 是虚拟列，表示从 Debezium 的元数据里读取本条记录的类型：
```sql
CREATE TABLE my_cdc_source (
	`id` BIGINT,
	`op_type` string METADATA FROM 'meta.op_type',
	`username` STRING,
	`first_name` STRING,
	`last_name` STRING,
	PRIMARY KEY (`id`) NOT ENFORCED
) WITH (
	'connector' = 'mysql-cdc',
	'hostname' = 'localhost',
	'port' = '3306',
	'database-name' = 'CDC',
	'table-name' = 'my_table'
);
```
如果上游的 my_table 表写入一条记录
```sql
(1, 'kylemeow', 'Kyle', 'Meow')
```
那么 Flink CDC Source 会向下游输出一条插入记录（`+I`）：
```sql
+I(1, 'INSERT', 'kylemeow', 'Kyle', 'Meow')
```
随后，因为用户修改了 username，上游表发生了变更，此时 Flink 会输出一条撤回记录（`-U`）和一条更新记录（`+U`）：
```sql
-U(1, 'UPDATE', 'kylemeow', 'Kyle', 'Meow')
+U(1, 'UPDATE', 'kylehelloo', 'Kyle', 'Meow')
```
可以发现，如果忽略 op_type 字段，那么第一条 `+I` 和第二条 `-U` 记录是对偶的（只是符号不同，内容一致），这也体现了 Flink 的回撤理念：撤回之前的状态，并用新的数据来代替。

但如果我们加上了 op_type 字段，它的值并不取决于原始数据，而是根据记录类型而有不同的取值，此时**非确定性**就出现了，**对偶性被破坏**。

> 有的读者可能会问：在我的环境下，并没有看到 `-U` 数据的下发，这是因为场景比较简单（例如 Sink 的主键、JOIN Key、Source 的主键均相同，且 Sink 支持 Upsert 模式），Flink 自动做了优化，体现在运行图中自动生成了 `DropUpdateBefore` 算子。除此之外，Flink 还是会正常下发 `-U` 数据的。

那么问题就来了，如果我们的 **JOIN Key 和 Source 的主键不同**，并行度大于 1，那么 Flink 会自动在 Sink 前插入一个名为 `SinkUpsertMaterializer` 的算子。它严格按照回撤流的匹配原则（`-U` 对 `+I`）来处理数据。对于上述 `-U` 数据，它会发现找不到任何与之匹配的记录，因此会打印一行报错，表示无法匹配：
```java
The state is cleared because of state ttl. This will result in incorrect result.
```
但实际上报错原因并不是状态因 TTL 而失效，而是我们引入的**元数据字段变化导致**的，类似于社区 Bug 单 [FLINK-28242](https://issues.apache.org/jira/browse/FLINK-28242)。前文提到，引用了 `NOW()` 等函数时，也有类似问题，可参见 [FLINK-27639](https://issues.apache.org/jira/browse/FLINK-27639).

该问题不仅仅会导致状态膨胀（历史 `+I` 记录无法被清理），也会造成数据丢失（`-U` 记录被当做乱序数据直接扔掉），对线上作业的稳定性和准确性都造成严重影响。

## 3. NDU 问题应对
非确定性导致状态无法匹配的问题，往往非常隐蔽。用户只会发现作业因为 OOM 出问题了，或者下游记录对不上，但是对于问题原因，时常需要花费很多时间来发掘。更可怕的是，即使用户发现了根因，也不一定了解如何应对。

因此，在 Flink 的 1.16 版本中，社区特意对**非确定性更新**（Non-Deterministic Update，下文简称 NDU）问题做了系统性梳理（见 [FLINK-27849](https://issues.apache.org/jira/browse/FLINK-27849)），并提供了初步的应对方案。

### 3.1 函数调用引起的 NDU 问题
对于上述提到的随机函数调用、变化的 CDC 元数据字段引起的 NDU 问题，**在作业生成物理计划期间做检测**。如果开启强制模式（`table.optimizer.non-deterministic-update.strategy` 参数设为 `TRY_RESOLVE`），则会直接报错并提示用户如何修改（例如去掉上述调用和字段）。

通过阅读源码，该功能的核心检测逻辑位于 `StreamNonDeterministicUpdatePlanVisitor`，其中 visit 方法里列举了多种 NDU 问题的判断逻辑。例如如果发现 Sink 是 Append-Only 的，那么可以认为不存在该问题，直接跳过；否则还会判断 Sink 是否有主键，如果有主键的话 Upsert Key 是否设置等等，来决定是需要处理 NDU 问题。如果最终发现风险（例如 JOIN 后的 SELECT 条件里有 NOW() 等非确定函数），会有类似如下的报错：
```java
can not satisfy the determinism requirement for correctly processing update message

There exists non deterministic function: '%s' in condition: '%s' which may cause wrong result
```
特别地，如果发现上述提到的动态 metadata 字段会导致问题，则会直接报错，例如
```java
The metadata column(s): 'op_type' in cdc source may cause wrong result or error on downstream operators, please consider removing these columns ...
```
这样用户可以提前发现并处理该问题，例如在 SELECT 条件中去掉非确定的时间函数，改用源数据里的时间戳字段；或者将输出改为 Append 流，在下游做归并处理等等。

### 3.2 维表 JOIN 引起的 NDU 问题
如果是因为外部维表 JOIN 导致的 NDU 问题，则引入物化能力（`Materialization`），重写物理计划，并加上缓存状态能力，以纠正该问题。例如遇到 `+I`、`+U` 等插入更新的记录，Flink 仍然会访问外部维表；但是对于 `-U`、`-D` 等撤回删除类记录，Flink 会从自己之前的状态中直接做匹配输出，不再查询外部维表，避免了维表数据变更造成的不确定性。

> 该操作会带来较重的额外状态存储开销，因此也需要用户手动开启 `TRY_RESOLVE` 模式。详见 此 [Pull Request](https://github.com/apache/flink/pull/20282/files#diff-9d01040e73a599dbbf49818da20f4e7d35f4243ad36f881e56344e78a18b0e5e)。目前只实现了同步查询模式，暂不支持异步 Lookup Join。

## 4. 总结

Flink 社区在 1.16 版本中，对 NDU 问题做了初步的检测和修复尝试（为了保证兼容性，需要手动开启），目前已经可以识别和处理多数的问题场景，更多案例详见官方文档 [流上的确定性](https://smartsi.blog.csdn.net/article/details/153280242)。

不过，我们也应当意识到，由于流计算系统的特殊性，该问题并不能被彻底解决。无论是去掉相关函数调用，还是增加物化能力，本质上都是一种妥协，也伴随着大小不一的代价。

我们建议用户主动开启该功能选项，毕竟问题发现的越早，修复的代价就越小。
