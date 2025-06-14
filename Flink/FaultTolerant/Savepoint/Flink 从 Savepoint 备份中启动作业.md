保障维度	实现方式	风险点
状态一致性	保存触发时刻所有算子状态	可能包含未完全处理的"in-flight"数据
数据完整性	Source 从 Savepoint 记录的 Offset 重放数据	✅ 不丢数据
数据不重	依赖 Sink 的幂等性/事务机制	⚠️ 若 Sink 不支持事务，可能重复输出
精确一次范围	框架级 Exactly-Once (Flink内部状态)	非端到端 (需外部系统配合)

当且仅当 Sink 支持事务写入（如 Kafka 事务 Producer、JDBC 幂等写入）时，才能实现端到端 Exactly-Once


每隔30s触发一次 Checkpoint

a
b
a
Trigger Savepoint -> Checkpoint  20s
b
a
Trigger Checkpoint 30s
a
停止作业
a:4
b:2



从 Savepoint 中恢复，预期是从 a 这个元素之后重新消费
