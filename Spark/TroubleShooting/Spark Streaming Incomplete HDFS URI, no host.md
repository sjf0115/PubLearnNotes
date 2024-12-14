## 1. 问题

假设我们有一个 HDFS 文件，路径为 `/user/hive/warehouse/tag_user`：
```java
(base) localhost:hadoop wy$ hadoop fs -ls /user/hive/warehouse/tag_user
Found 3 items
-rwxr-xr-x   1 wy supergroup         70 2024-06-09 21:46 /user/hive/warehouse/tag_user/000000_0
```
我们想要使用 Spark Streaming 从这个 HDFS 文件读取数据时：
```java
String path = "hdfs:///user/hive/warehouse/tag_user";
JavaDStream<String> dStream = ssc.textFileStream(path);
```
我们收到一个错误提示：
```java
24/12/14 10:04:10 WARN FileInputDStream: Error finding new files under hdfs:/user/hive/warehouse/tag_user
java.io.IOException: Incomplete HDFS URI, no host: hdfs:///user/hive/warehouse/tag_user
	at org.apache.hadoop.hdfs.DistributedFileSystem.initialize(DistributedFileSystem.java:143)
	at org.apache.hadoop.fs.FileSystem.createFileSystem(FileSystem.java:2667)
	at org.apache.hadoop.fs.FileSystem.access$200(FileSystem.java:93)
	at org.apache.hadoop.fs.FileSystem$Cache.getInternal(FileSystem.java:2701)
	at org.apache.hadoop.fs.FileSystem$Cache.get(FileSystem.java:2683)
	at org.apache.hadoop.fs.FileSystem.get(FileSystem.java:372)
	at org.apache.hadoop.fs.Path.getFileSystem(Path.java:295)
	at org.apache.spark.streaming.dstream.FileInputDStream.fs(FileInputDStream.scala:305)
	at org.apache.spark.streaming.dstream.FileInputDStream.findNewFiles(FileInputDStream.scala:195)
	at org.apache.spark.streaming.dstream.FileInputDStream.compute(FileInputDStream.scala:146)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$getOrCompute$3(DStream.scala:343)
	at scala.util.DynamicVariable.withValue(DynamicVariable.scala:62)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$getOrCompute$2(DStream.scala:343)
	at org.apache.spark.streaming.dstream.DStream.createRDDWithLocalProperties(DStream.scala:417)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$getOrCompute$1(DStream.scala:342)
	at scala.Option.orElse(Option.scala:447)
	at org.apache.spark.streaming.dstream.DStream.getOrCompute(DStream.scala:335)
	at org.apache.spark.streaming.dstream.MappedDStream.compute(MappedDStream.scala:36)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$getOrCompute$3(DStream.scala:343)
	at scala.util.DynamicVariable.withValue(DynamicVariable.scala:62)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$getOrCompute$2(DStream.scala:343)
	at org.apache.spark.streaming.dstream.DStream.createRDDWithLocalProperties(DStream.scala:417)
	at org.apache.spark.streaming.dstream.DStream.$anonfun$getOrCompute$1(DStream.scala:342)
	at scala.Option.orElse(Option.scala:447)
	at org.apache.spark.streaming.dstream.DStream.getOrCompute(DStream.scala:335)
	at org.apache.spark.streaming.dstream.ForEachDStream.generateJob(ForEachDStream.scala:48)
	at org.apache.spark.streaming.DStreamGraph.$anonfun$generateJobs$2(DStreamGraph.scala:123)
	at scala.collection.TraversableLike.$anonfun$flatMap$1(TraversableLike.scala:245)
	at scala.collection.mutable.ArraySeq.foreach(ArraySeq.scala:75)
	at scala.collection.TraversableLike.flatMap(TraversableLike.scala:245)
	at scala.collection.TraversableLike.flatMap$(TraversableLike.scala:242)
	at scala.collection.AbstractTraversable.flatMap(Traversable.scala:108)
	at org.apache.spark.streaming.DStreamGraph.generateJobs(DStreamGraph.scala:122)
	at org.apache.spark.streaming.scheduler.JobGenerator.$anonfun$generateJobs$1(JobGenerator.scala:252)
	at scala.util.Try$.apply(Try.scala:213)
	at org.apache.spark.streaming.scheduler.JobGenerator.generateJobs(JobGenerator.scala:250)
	at org.apache.spark.streaming.scheduler.JobGenerator.org$apache$spark$streaming$scheduler$JobGenerator$$processEvent(JobGenerator.scala:186)
	at org.apache.spark.streaming.scheduler.JobGenerator$$anon$1.onReceive(JobGenerator.scala:91)
	at org.apache.spark.streaming.scheduler.JobGenerator$$anon$1.onReceive(JobGenerator.scala:90)
	at org.apache.spark.util.EventLoop$$anon$1.run(EventLoop.scala:49)
```

## 2. 解决方案

要解决这个问题，我们需要正确组织 HDFS URI，需要包含主机名和端口号。下面是一个正确的示例：
```java
String path = "hdfs://localhost:9000/user/hive/warehouse/tag_user";
JavaDStream<String> dStream = ssc.textFileStream(path);
```
在这个示例中，我们通过在 HDFS URI 中添加 `localhost:9000` 来指定主机名和端口号。需要注意的是需要根据你的 HDFS 配置来指定正确的主机名和端口号：
```xml
<property>
  <name>fs.defaultFS</name>
  <value>hdfs://localhost:9000</value>
</property>
```
> etc/hadoop/core-site.xml
