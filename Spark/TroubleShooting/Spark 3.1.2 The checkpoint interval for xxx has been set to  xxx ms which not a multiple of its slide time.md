## 1. 问题

在实现有状态的单词计算时，如下所示设置 Checkpoint：
```java
SparkConf conf = new SparkConf().setAppName("SocketCheckpointWordCount").setMaster("local[2]");
JavaSparkContext sparkContext = new JavaSparkContext(conf);
JavaStreamingContext ssc = new JavaStreamingContext(sparkContext, Durations.seconds(10));
// 设置 Checkpoint 路径
ssc.checkpoint("hdfs://localhost:9000/spark/checkpoint");
// 单词流
JavaReceiverInputDStream<String> lines = ssc.socketTextStream(hostName, port);
// 设置 Checkpoint 周期
lines.checkpoint(Durations.seconds(65));
...
```

运行过程中抛出如下异常信息：
```java
Exception in thread "main" java.lang.IllegalArgumentException: requirement failed: The checkpoint interval for SocketInputDStream has been set to  65000 ms which not a multiple of its slide time (10000 ms). Please set it to a multiple of 10000 ms.
	at scala.Predef$.require(Predef.scala:281)
	at org.apache.spark.streaming.dstream.DStream.validateAtStart(DStream.scala:259)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8$adapted(DStream.scala:277)
	at scala.collection.immutable.List.foreach(List.scala:392)
	at org.apache.spark.streaming.dstream.DStream.validateAtStart(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8$adapted(DStream.scala:277)
	at scala.collection.immutable.List.foreach(List.scala:392)
	at org.apache.spark.streaming.dstream.DStream.validateAtStart(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8$adapted(DStream.scala:277)
	at scala.collection.immutable.List.foreach(List.scala:392)
	at org.apache.spark.streaming.dstream.DStream.validateAtStart(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8$adapted(DStream.scala:277)
	at scala.collection.immutable.List.foreach(List.scala:392)
	at org.apache.spark.streaming.dstream.DStream.validateAtStart(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8(DStream.scala:277)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$validateAtStart$8$adapted(DStream.scala:277)
	at scala.collection.immutable.List.foreach(List.scala:392)
	at org.apache.spark.streaming.dstream.DStream.validateAtStart(DStream.scala:277)
	at org.apache.spark.streaming.DStreamGraph.$anonfun$start$4(DStreamGraph.scala:52)
	at org.apache.spark.streaming.DStreamGraph.$anonfun$start$4$adapted(DStreamGraph.scala:52)
	at scala.collection.mutable.ArraySeq.foreach(ArraySeq.scala:75)
	at org.apache.spark.streaming.DStreamGraph.start(DStreamGraph.scala:52)
	at org.apache.spark.streaming.scheduler.JobGenerator.startFirstTime(JobGenerator.scala:197)
	at org.apache.spark.streaming.scheduler.JobGenerator.start(JobGenerator.scala:102)
	at org.apache.spark.streaming.scheduler.JobScheduler.start(JobScheduler.scala:102)
	at org.apache.spark.streaming.StreamingContext.$anonfun$start$1(StreamingContext.scala:590)
	at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23)
	at ... run in separate thread using org.apache.spark.util.ThreadUtils ... ()
	at org.apache.spark.streaming.StreamingContext.liftedTree1$1(StreamingContext.scala:585)
	at org.apache.spark.streaming.StreamingContext.start(StreamingContext.scala:577)
	at org.apache.spark.streaming.api.java.JavaStreamingContext.start(JavaStreamingContext.scala:557)
	at com.spark.example.streaming.checkpoint.SocketCheckpointWordCount.main(SocketCheckpointWordCount.java:68)
```
## 2. 解决方案

从上面异常信息看出异常与批次间隔和Checkpoint周期间隔有关系，具体看一下源码：
```scala
scala.Predef..MODULE$.require(this.checkpointDuration() == null || this.checkpointDuration().isMultipleOf(this.slideDuration()), () -> {
    return (new StringBuilder(122)).append("The checkpoint interval for ").append(this.getClass().getSimpleName()).append(" has been set to ").append(" ").append(this.checkpointDuration()).append(" which not a multiple of its slide time (").append(this.slideDuration()).append("). ").append("Please set it to a multiple of ").append(this.slideDuration()).append(".").toString();
});
```
从上面可以看出 Checkpoint 间隔必须是批次间隔的整数倍数，否则作业启动时会初始化失败。也就是说这个间隔必须是批次间隔的 n 倍。具体值取决于数据量以及失败恢复的重要度。一般建议是批次间隔的 5-7 倍。
