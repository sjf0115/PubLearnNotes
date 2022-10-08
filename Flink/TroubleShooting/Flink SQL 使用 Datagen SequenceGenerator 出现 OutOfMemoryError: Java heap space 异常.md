> Flink 1.13.5

## 1. 现象

在使用 Datagen Connector 的序列化生成器 SequenceGenerator 生成模拟数据抛出 OutOfMemoryError 异常，具体 DDL 如下所示：
```sql
CREATE TABLE session_behavior (
  session_id STRING COMMENT '会话Id',
  uid BIGINT COMMENT '用户Id'
) WITH (
  'connector' = 'datagen',
  'rows-per-second' = '10',
  'fields.session_id.kind' = 'sequence',
  'fields.session_id.start' = '10000001',
  'fields.session_id.end' = '90000000',
  'fields.uid.kind' = 'random',
  'fields.uid.min' = '10001',
  'fields.uid.max' = '99999'
)
```
程序启动之后抛出如下异常：
```java
Caused by: java.lang.OutOfMemoryError: Java heap space
	at java.util.ArrayDeque.doubleCapacity(ArrayDeque.java:162)
	at java.util.ArrayDeque.addLast(ArrayDeque.java:252)
	at java.util.ArrayDeque.add(ArrayDeque.java:423)
	at org.apache.flink.streaming.api.functions.source.datagen.SequenceGenerator.open(SequenceGenerator.java:92)
	at org.apache.flink.table.factories.datagen.types.RowDataGenerator.open(RowDataGenerator.java:48)
	at org.apache.flink.streaming.api.functions.source.datagen.DataGeneratorSource.initializeState(DataGeneratorSource.java:95)
	at org.apache.flink.streaming.util.functions.StreamingFunctionUtils.tryRestoreFunction(StreamingFunctionUtils.java:189)
	at org.apache.flink.streaming.util.functions.StreamingFunctionUtils.restoreFunctionState(StreamingFunctionUtils.java:171)
	at org.apache.flink.streaming.api.operators.AbstractUdfStreamOperator.initializeState(AbstractUdfStreamOperator.java:96)
	at org.apache.flink.streaming.api.operators.StreamOperatorStateHandler.initializeOperatorState(StreamOperatorStateHandler.java:118)
	at org.apache.flink.streaming.api.operators.AbstractStreamOperator.initializeState(AbstractStreamOperator.java:290)
	at org.apache.flink.streaming.runtime.tasks.OperatorChain.initializeStateAndOpenOperators(OperatorChain.java:441)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restoreGates(StreamTask.java:585)
	at org.apache.flink.streaming.runtime.tasks.StreamTask$$Lambda$264/947042656.call(Unknown Source)
	at org.apache.flink.streaming.runtime.tasks.StreamTaskActionExecutor$SynchronizedStreamTaskActionExecutor.call(StreamTaskActionExecutor.java:100)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.executeRestore(StreamTask.java:565)
	at org.apache.flink.streaming.runtime.tasks.StreamTask$$Lambda$231/152736321.run(Unknown Source)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.runWithCleanUpOnFail(StreamTask.java:650)
	at org.apache.flink.streaming.runtime.tasks.StreamTask.restore(StreamTask.java:540)
	at org.apache.flink.runtime.taskmanager.Task.doRun(Task.java:759)
	at org.apache.flink.runtime.taskmanager.Task.run(Task.java:566)
	at java.lang.Thread.run(Thread.java:748)
```
## 2. 解决方案

从上面日志中可以看出是在序列化生成器 SequenceGenerator 初始化时抛出异常，具体与双端队列 ArrayDeque 相关。下面我们一起看一下在初始化方法 open 中具体做了什么：
```java
public void open(String name, FunctionInitializationContext context, RuntimeContext runtimeContext) throws Exception {
    ...
		// 创建双端队列
    this.valuesToEmit = new ArrayDeque<>();
    if (context.isRestored()) {
				// 故障恢复
        for (Long v : this.checkpointedState.get()) {
            this.valuesToEmit.add(v);
        }
    } else {
        final int stepSize = runtimeContext.getNumberOfParallelSubtasks();
        final int taskIdx = runtimeContext.getIndexOfThisSubtask();
        final long congruence = start + taskIdx;
        long totalNoOfElements = Math.abs(end - start + 1);
        final int baseSize = safeDivide(totalNoOfElements, stepSize);
        final int toCollect = (totalNoOfElements % stepSize > taskIdx) ? baseSize + 1 : baseSize;
        for (long collected = 0; collected < toCollect; collected++) {
						// 核心在这
            this.valuesToEmit.add(collected * stepSize + congruence);
        }
    }
}
```
从上面代码中可以看出每个并发子任务在初始化序列化生成器时会创建一个双端队列 ArrayDeque 来存储 `[start, end]` 区间内的数据记录。由于我们设置的区间比较大，所以导致双端队列再扩容时出现堆内存溢出。

对此，你可以扩大 TaskManager 的堆内存大小。在这我们选择把序列化生成器的区间调小一些：
```sql
CREATE TABLE session_behavior (
  session_id STRING COMMENT '会话Id',
  uid BIGINT COMMENT '用户Id'
) WITH (
  'connector' = 'datagen',
  'rows-per-second' = '10',
  'fields.session_id.kind' = 'sequence',
  'fields.session_id.start' = '10001',
  'fields.session_id.end' = '90000',
  'fields.uid.kind' = 'random',
  'fields.uid.min' = '1001',
  'fields.uid.max' = '9999'
)
```
session_id 的生成区间从 `[10000001, 90000000]` 修改为 `[10001, 90000]`。
