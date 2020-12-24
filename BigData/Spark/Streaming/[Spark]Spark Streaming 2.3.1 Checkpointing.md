
### 1. 概述

一个流应用程序必须全天候运行，所有必须能够解决与应用程序逻辑无关的故障（如系统错误，JVM崩溃等）。为了实现这一点，Spark Streaming需要 checkpoint 足够的信息到具有容错的存储系统上，以使系统可以从故障中恢复。

有两种类型的数据需要 checkpoint：

(1) Metadata checkpointing：将定义流计算的信息保存到HDFS等容错存储系统中。用来在运行流应用程序的Driver的节点上故障恢复。元数据包括：
- 配置：创建Spark Streaming应用程序的配置信息
- DStream操作符：定义Streaming应用程序的操作集合
- 未完成的batch：对应作业还在队列中未完成的batch

(2) Data checkpointing：将生成的RDD保存到可靠的存储系统中，这在有状态跨batch处理数据的Transformation中是有必要的。在这种Transformation中，生成的RDD依赖于先前batch的RDD，这会导致依赖链的长度会随时间持续增长。为了避免故障恢复时间无限增长（与依赖链的长度成正比）。有状态的Transformation的中间RDD将会定期存储到可靠存储系统中以切断依赖链。

总而言之，元数据检查点主要用于从Driver故障中恢复，如果使用有状态的Transformation，即使基本的函数也需要数据或RDD检查点。

### 2. 何时开启Checkpointing

当遇到以下场景时，可以为应用程序启用Checkpointing：
- 使用有状态的Transformation：如果在应用程序中使用 updateStateByKey或reduceByKeyAndWindow，则必须提供检查点目录以允许定期RDDCheckpointing。
- 从运行应用程序的Driver上进行故障恢复：元数据检查点根据进度信息进行恢复。

请注意，在运行一个没有上述有状态Transformation的简单流应用程序时可以不启用检查点。在这种情况下，Driver故障恢复也只能恢复一部分（那些已接收但未处理的数据可能会丢失）。这通常是可以接受的，并且许多人以这种方式运行Spark Streaming应用程序。

### 3. 如何配置Checkpointing

可以通过设置一个容错，可靠的文件系统（例如，HDFS，S3等）目录来启用检查点，检查点信息保存到该目录中。这是通过使用 `streamingContext.checkpoint（checkpointDirectory）` 完成。这可以允许你使用上述有状态的Transformation。此外，如果想使应用程序从Driver故障中恢复，则应重写流应用程序以使其具有以下行为：
- 当程序第一次启动时，创建一个新的StreamingContext，启动所有流然后调用`start()` 方法。
- 在失败后重新启动程序时，根据检查点目录中的检查点数据重新创建StreamingContext。

Java版本:

使用`JavaStreamingContext.getOrCreate`可以简化此行为。其用法如下。
```java
// Create a factory object that can create and setup a new JavaStreamingContext
JavaStreamingContextFactory contextFactory = new JavaStreamingContextFactory() {
  @Override public JavaStreamingContext create() {
    JavaStreamingContext jssc = new JavaStreamingContext(...);  // new context
    JavaDStream<String> lines = jssc.socketTextStream(...);     // create DStreams
    ...
    jssc.checkpoint(checkpointDirectory);                       // set checkpoint directory
    return jssc;
  }
};

// Get JavaStreamingContext from checkpoint data or create a new one
JavaStreamingContext context = JavaStreamingContext.getOrCreate(checkpointDirectory, contextFactory);

// Do additional setup on context that needs to be done,
// irrespective of whether it is being started or restarted
context. ...

// Start the context
context.start();
context.awaitTermination();
```
Scala版本:
```scala
// Function to create and setup a new StreamingContext
def functionToCreateContext(): StreamingContext = {
  val ssc = new StreamingContext(...)   // new context
  val lines = ssc.socketTextStream(...) // create DStreams
  ...
  ssc.checkpoint(checkpointDirectory)   // set checkpoint directory
  ssc
}

// Get StreamingContext from checkpoint data or create a new one
val context = StreamingContext.getOrCreate(checkpointDirectory, functionToCreateContext _)

// Do additional setup on context that needs to be done,
// irrespective of whether it is being started or restarted
context. ...

// Start the context
context.start()
context.awaitTermination()
```

如果checkpointDirectory目录存在，则会根据检查点数据重新创建context。如果该目录不存在（即，第一次运行），则将调用函数 `functionToCreateContext` 以创建新context并设置DStream。请参阅示例[RecoverableNetworkWordCount](https://github.com/apache/spark/blob/master/examples/src/main/java/org/apache/spark/examples/streaming/JavaRecoverableNetworkWordCount.java)。

除了使用getOrCreate之外，还需要确保driver进程在失败时自动重新启动。这只能通过用于运行应用程序的部署基础结构来完成。具体请参考：[部署](http://spark.apache.org/docs/latest/streaming-programming-guide.html#deploying-applications)。

请注意，RDD的检查点会导致节省可靠存储的成本。这可能导致RDD被检查点的那些批次的处理时间增加。因此，需要仔细设置检查点的间隔。在小批量（例如1秒）下，每批次检查点可能会显着降低操作吞吐量。相反，检查点过于频繁会导致谱系和任务大小增加，这可能会产生不利影响。对于需要RDD检查点的有状态转换，默认时间间隔是批处理间隔的倍数，至少为10秒。可以使用dstream.checkpoint（checkpointInterval）进行设置。通常，DStream的5-10个滑动间隔的检查点间隔是一个很好的设置。

https://aiyanbo.gitbooks.io/spark-programming-guide-zh-cn/content/spark-streaming/basic-concepts/checkpointing.html

> Spark版本 2.3.1

原文：http://spark.apache.org/docs/2.3.1/streaming-programming-guide.html#checkpointing
