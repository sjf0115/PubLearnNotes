## 1. 问题

我们使用 Spark Streaming 的 fileStream 方法读取 HDFS 文件，代码如下所示：
```java
JavaPairInputDStream<LongWritable, Text> dStream = ssc.fileStream(
        path,
        LongWritable.class,
        Text.class,
        TextInputFormat.class,
        filter,
        false
);
dStream.print();
```
运行上述程序时抛出如下异常：
```
java.io.NotSerializableException: org.apache.hadoop.io.LongWritable
Serialization stack:
	- object not serializable (class: org.apache.hadoop.io.LongWritable, value: 14)
	- field (class: scala.Tuple2, name: _1, type: class java.lang.Object)
	- object (class scala.Tuple2, (14,))
	- element of array (index: 0)
	- array (class [Lscala.Tuple2;, size 2)
	at org.apache.spark.serializer.SerializationDebugger$.improveException(SerializationDebugger.scala:41)
	at org.apache.spark.serializer.JavaSerializationStream.writeObject(JavaSerializer.scala:47)
	at org.apache.spark.serializer.JavaSerializerInstance.serialize(JavaSerializer.scala:101)
	at org.apache.spark.executor.Executor$TaskRunner.run(Executor.scala:543)
	at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)
	at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:624)
	at java.lang.Thread.run(Thread.java:748)
24/12/15 10:12:51 ERROR TaskSetManager: task 0.0 in stage 0.0 (TID 0) had a not serializable result: org.apache.hadoop.io.LongWritable
Serialization stack:
	- object not serializable (class: org.apache.hadoop.io.LongWritable, value: 14)
	- field (class: scala.Tuple2, name: _1, type: class java.lang.Object)
	- object (class scala.Tuple2, (14,))
	- element of array (index: 0)
	- array (class [Lscala.Tuple2;, size 2); not retrying
24/12/15 10:12:51 INFO TaskSchedulerImpl: Removed TaskSet 0.0, whose tasks have all completed, from pool
24/12/15 10:12:51 INFO TaskSchedulerImpl: Cancelling stage 0
24/12/15 10:12:51 INFO TaskSchedulerImpl: Killing all running tasks in stage 0: Stage cancelled
24/12/15 10:12:51 INFO DAGScheduler: ResultStage 0 (print at MinRememberDurationExample.java:55) failed in 0.781 s due to Job aborted due to stage failure: task 0.0 in stage 0.0 (TID 0) had a not serializable result: org.apache.hadoop.io.LongWritable
Serialization stack:
	- object not serializable (class: org.apache.hadoop.io.LongWritable, value: 14)
	- field (class: scala.Tuple2, name: _1, type: class java.lang.Object)
	- object (class scala.Tuple2, (14,))
	- element of array (index: 0)
	- array (class [Lscala.Tuple2;, size 2)
24/12/15 10:12:51 INFO DAGScheduler: Job 0 failed: print at MinRememberDurationExample.java:55, took 0.838955 s
24/12/15 10:12:51 INFO JobScheduler: Finished job streaming job 1734228770000 ms.0 from job set of time 1734228770000 ms
```
这个错误表明在 Spark Streaming 程序中，有一个对象没有被正确序列化，具体是 `org.apache.hadoop.io.LongWritable` 类。在 Spark 中，任务是在不同的节点上的执行者之间发送的，为了能够发送这些对象，它们需要实现 Serializable 接口。如果一个对象没有实现这个接口，或者它依赖的某些成员变量没有实现这个接口，就会抛出序列化错误。我们确实看到 LongWritable 类以及上游接口都没有实现 `Serializable` 接口：
```java
public interface Writable {
  ...
}

public interface Comparable<T> {
  ...
}

public interface WritableComparable<T> extends Writable, Comparable<T> {
  ...
}

public class LongWritable implements WritableComparable<LongWritable> {
    ...
}
```
