

```java
Caused by: java.lang.IllegalArgumentException: requirement failed: Cannot update the state that is timing out
	at scala.Predef$.require(Predef.scala:281)
	at org.apache.spark.streaming.StateImpl.update(State.scala:154)
	at com.spark.example.streaming.checkpoint.SocketCheckpointWordCount$1.call(SocketCheckpointWordCount.java:54)
	at com.spark.example.streaming.checkpoint.SocketCheckpointWordCount$1.call(SocketCheckpointWordCount.java:45)
	at org.apache.spark.streaming.StateSpec$.$anonfun$function$3(StateSpec.scala:227)
	at org.apache.spark.streaming.StateSpec$.$anonfun$function$1(StateSpec.scala:181)
	at org.apache.spark.streaming.rdd.MapWithStateRDDRecord$.$anonfun$updateRecordWithData$4(MapWithStateRDD.scala:72)
	at org.apache.spark.streaming.rdd.MapWithStateRDDRecord$.$anonfun$updateRecordWithData$4$adapted(MapWithStateRDD.scala:70)
	at scala.collection.Iterator.foreach(Iterator.scala:941)
	at scala.collection.Iterator.foreach$(Iterator.scala:941)
	at scala.collection.Iterator$ConcatIterator.foreach(Iterator.scala:179)
...
	at org.apache.spark.storage.BlockManager.$anonfun$doPutIterator$1(BlockManager.scala:1423)
	at org.apache.spark.storage.BlockManager.org$apache$spark$storage$BlockManager$$doPut(BlockManager.scala:1350)
	at org.apache.spark.storage.BlockManager.doPutIterator(BlockManager.scala:1414)
	at org.apache.spark.storage.BlockManager.getOrElseUpdate(BlockManager.scala:1237)
	at org.apache.spark.rdd.RDD.getOrCompute(RDD.scala:384)
	at org.apache.spark.rdd.RDD.iterator(RDD.scala:335)
	at org.apache.spark.streaming.rdd.MapWithStateRDD.compute(MapWithStateRDD.scala:154)
	at org.apache.spark.rdd.RDD.computeOrReadCheckpoint(RDD.scala:373)
	at org.apache.spark.rdd.RDD.$anonfun$getOrCompute$1(RDD.scala:386)
	at org.apache.spark.storage.BlockManager.$anonfun$doPutIterator$1(BlockManager.scala:1423)
	at org.apache.spark.storage.BlockManager.org$apache$spark$storage$BlockManager$$doPut(BlockManager.scala:1350)
	at org.apache.spark.storage.BlockManager.doPutIterator(BlockManager.scala:1414)
	at org.apache.spark.storage.BlockManager.getOrElseUpdate(BlockManager.scala:1237)
	at org.apache.spark.rdd.RDD.getOrCompute(RDD.scala:384)
	at org.apache.spark.rdd.RDD.iterator(RDD.scala:335)
	at org.apache.spark.rdd.MapPartitionsRDD.compute(MapPartitionsRDD.scala:52)
	at org.apache.spark.rdd.RDD.computeOrReadCheckpoint(RDD.scala:373)
	at org.apache.spark.rdd.RDD.iterator(RDD.scala:337)
	at org.apache.spark.rdd.MapPartitionsRDD.compute(MapPartitionsRDD.scala:52)
	at org.apache.spark.rdd.RDD.computeOrReadCheckpoint(RDD.scala:373)
	at org.apache.spark.rdd.RDD.iterator(RDD.scala:337)
	at org.apache.spark.scheduler.ResultTask.runTask(ResultTask.scala:90)
	at org.apache.spark.scheduler.Task.run(Task.scala:131)
	at org.apache.spark.executor.Executor$TaskRunner.$anonfun$run$3(Executor.scala:498)
	at org.apache.spark.util.Utils$.tryWithSafeFinally(Utils.scala:1439)
	at org.apache.spark.executor.Executor$TaskRunner.run(Executor.scala:501)
	... 3 more
```
