在设计和实现 Flink 的流计算算子时，我们一般会把“面向状态编程”作为第一准则。因为在流计算中，为了保证状态（State）的一致性，需要将状态数据存储在状态后端（StateBackend），由框架来做分布式快照。而目前主要使用的 RocksDB, Niagara 状态后端都会在每次 read 和 write 操作时发生序列化和反序列化操作，甚至是磁盘的 I/O 操作。因此状态的相关操作通常都会成为整个任务的性能瓶颈，状态的数据结构设计以及对状态的每一次访问都需要特别注意。

MiniBatch 的核心思想是在聚合操作符内部的缓冲区中缓存一小批数据。在访问状态状态时，每个键只需要一次操作来访问状态。这可以显著减少状态开销并获得更好的吞吐量。然而，这可能会增加一些延迟，因为它缓冲了一批记录，而不是立即处理它们。这是吞吐量和延迟之间的权衡。

## 1. 原理

MiniBatch 的一个典型应用场景就是 Group Aggregate。例如简单的求和例子：
```sql
SELECT key, SUM(value) FROM T GROUP BY key
```
如下图所示，当未开启 MiniBatch 时，Aggregate 的处理模式是每来一条数据，查询一次状态，进行聚合计算，然后写入一次状态。当有 N 条数据时，需要操作 2*N 次状态。

![]()

当开启 MiniBatch 时，对于缓存下来的 N 条数据一起触发，同 key 的数据只会读写状态一次。例如上图缓存的 4 条 A 的记录，只会对状态读写各一次。所以当数据的 key 的重复率越大，攒批的大小越大，那么对状态的访问会越少，得到的吞吐量越高。

## 2. 适用场景

微批处理通过增加延迟换取高吞吐，如果您有超低延迟的要求，不建议开启微批处理。通常对于聚合的场景，微批处理可以显著的提升系统性能，建议开启。

## 3. 使用

MiniBatch 默认关闭，开启方式如下：
```java
// 开启 MiniBatch
Configuration configuration = tEnv.getConfig().getConfiguration();
configuration.setString("table.exec.mini-batch.enabled", "true");
configuration.setString("table.exec.mini-batch.allow-latency", "1 s");
configuration.setString("table.exec.mini-batch.size", "5000");
```



## 总结

关键机制：
- 缓冲累积：在内存中暂存多条记录
- 批量触发：满足以下任一条件触发计算
  - 时间阈值(`table.exec.mini-batch.allow-latency`)
  - 数据量阈值(`table.exec.mini-batch.size`)
- 批量状态访问：单次处理多条记录，减少状态访问次数
- 增量计算优化：对聚合操作采用局部聚合+全局聚合
