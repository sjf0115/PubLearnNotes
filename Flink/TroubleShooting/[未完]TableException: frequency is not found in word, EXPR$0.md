```Java
// DataStream 转 Table
Table table = tabEnv.fromDataStream(words, $("word"), $("frequency"));
Table resultTable = table.groupBy($("word"))
        .select($("word"), $("frequency").sum().as("frequency"));

// Table 转换为 DataStream
DataStream<Tuple2<Boolean, WordCount>> resultStream = tabEnv.toRetractStream(resultTable, WordCount.class);
```

```java
Exception in thread "main" org.apache.flink.table.api.TableException: frequency is not found in word, EXPR$0
	at org.apache.flink.table.planner.codegen.SinkCodeGenerator$$anonfun$1.apply(SinkCodeGenerator.scala:82)
	at org.apache.flink.table.planner.codegen.SinkCodeGenerator$$anonfun$1.apply(SinkCodeGenerator.scala:79)
	at scala.collection.TraversableLike$$anonfun$map$1.apply(TraversableLike.scala:234)
	at scala.collection.TraversableLike$$anonfun$map$1.apply(TraversableLike.scala:234)
	at scala.collection.IndexedSeqOptimized$class.foreach(IndexedSeqOptimized.scala:33)
	at scala.collection.mutable.ArrayOps$ofRef.foreach(ArrayOps.scala:186)
	at scala.collection.TraversableLike$class.map(TraversableLike.scala:234)
	at scala.collection.mutable.ArrayOps$ofRef.map(ArrayOps.scala:186)
	at org.apache.flink.table.planner.codegen.SinkCodeGenerator$.generateRowConverterOperator(SinkCodeGenerator.scala:79)
	at org.apache.flink.table.planner.codegen.SinkCodeGenerator.generateRowConverterOperator(SinkCodeGenerator.scala)
	at org.apache.flink.table.planner.plan.nodes.exec.common.CommonExecLegacySink.translateToTransformation(CommonExecLegacySink.java:190)
	at org.apache.flink.table.planner.plan.nodes.exec.common.CommonExecLegacySink.translateToPlanInternal(CommonExecLegacySink.java:141)
	at org.apache.flink.table.planner.plan.nodes.exec.ExecNodeBase.translateToPlan(ExecNodeBase.java:134)
	at org.apache.flink.table.planner.delegation.StreamPlanner$$anonfun$1.apply(StreamPlanner.scala:70)
	at org.apache.flink.table.planner.delegation.StreamPlanner$$anonfun$1.apply(StreamPlanner.scala:69)
	at scala.collection.TraversableLike$$anonfun$map$1.apply(TraversableLike.scala:234)
	at scala.collection.TraversableLike$$anonfun$map$1.apply(TraversableLike.scala:234)
	at scala.collection.Iterator$class.foreach(Iterator.scala:891)
	at scala.collection.AbstractIterator.foreach(Iterator.scala:1334)
	at scala.collection.IterableLike$class.foreach(IterableLike.scala:72)
	at scala.collection.AbstractIterable.foreach(Iterable.scala:54)
	at scala.collection.TraversableLike$class.map(TraversableLike.scala:234)
	at scala.collection.AbstractTraversable.map(Traversable.scala:104)
	at org.apache.flink.table.planner.delegation.StreamPlanner.translateToPlan(StreamPlanner.scala:69)
	at org.apache.flink.table.planner.delegation.PlannerBase.translate(PlannerBase.scala:165)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.toStreamInternal(StreamTableEnvironmentImpl.java:439)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.toRetractStream(StreamTableEnvironmentImpl.java:528)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.toRetractStream(StreamTableEnvironmentImpl.java:517)
	at com.flink.example.table.base.TableWordCount.main(TableWordCount.java:52)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
```

解决方案：
```java
// DataStream 转 Table
Table table = tabEnv.fromDataStream(words, $("word"), $("frequency"));
Table resultTable = table.groupBy($("word"))
        .select($("word"), $("frequency").sum())
        .as("word", "frequency");

// Table 转换为 DataStream
DataStream<Tuple2<Boolean, WordCount>> resultStream = tabEnv.toRetractStream(resultTable, WordCount.class);
```
或者
```java
// DataStream 转 Table
Table table = tabEnv.fromDataStream(words, $("word"), $("frequency"));
Table resultTable = table.groupBy($("word"))
        .select($("word"), $("frequency").sum());

// Table 转换为 DataStream
DataStream<Tuple2<Boolean, Row>> resultStream = tabEnv.toRetractStream(resultTable, Row.class);
```
