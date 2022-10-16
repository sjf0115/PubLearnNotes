## 1. 原理

通常开启 LocalGlobal 优化来解决常见数据热点(倾斜)问题。LocalGlobal 优化会将原先的聚合拆分成 Local 和 Global 两个阶段的聚合，类似 MapReduce 模型中的 Combine+Reduce 处理模式。第一阶段在上游节点本地攒一批数据进行聚合，即实现 LocalAgg 聚合，并输出这次微批的增量值 Accumulator。第二阶段再将收到的 Accumulator 合并 Merge，得到最终的结果 GlobalAgg 聚合。

LocalGlobal 两阶段聚合本质上能够靠 LocalAgg 的聚合筛除部分倾斜数据，从而降低 GlobalAgg 的热点，提升性能。例如，考虑下面的SQL:
```sql
SELECT color, sum(id)
FROM T
GROUP BY color
```

数据流中的记录可能是倾斜的，因此聚合算子的某些实例必须处理比其他实例多得多的记录，这就导致了热点。本地聚合可以将具有相同 Key 的一定数量的输入累积到单个累加器中。这样全局聚合接收到是数据量减少了的累加器，而不是有大量数据的原始输入。这可以显著减少网络的 Shuffle 和状态访问的成本。每次本地聚合累积的输入数量是基于 MiniBatch 间隔。这意味着 LocalGlobal 两阶段聚合必须开启 MiniBatch 优化。

## 2. 适用场景

LocalGlobal 适用于提升如 SUM、COUNT、MAX、MIN 和 AVG 等普通聚合的性能，以及解决这些场景下的数据热点问题。
> 开启 LocalGlobal 需要 UDAF 实现 Merge 方法。

## 3. 使用

需要在 MiniBatch 开启的前提下才能生效：
```java
// 开启 MiniBatch
Configuration configuration = tEnv.getConfig().getConfiguration();
configuration.setString("table.exec.mini-batch.enabled", "true");
configuration.setString("table.exec.mini-batch.allow-latency", "1 s");
configuration.setString("table.exec.mini-batch.size", "5");
```
开启 LocalGlobal 两阶段聚合优化只需要配置如下参数：
```java
// 开启两阶段聚合
configuration.setString("table.optimizer.agg-phase-strategy", "TWO_PHASE");
```
判断 LocalGlobal 两阶段聚合优化是否生效，可以通过 Web UI 观察最终生成的拓扑图的节点名字中是否包含 GlobalGroupAggregate 或 LocalGroupAggregate：

![](2)

## 4. 示例

[LocalGlobalAggExample](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/tuning/skew/LocalGlobalAggExample.java)
