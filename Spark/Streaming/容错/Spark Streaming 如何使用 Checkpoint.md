
> Spark Streaming 版本：3.1.1

## 1. 概述

流应用程序必须 7*24 小时全天候运行，所有必须能够解决与应用程序逻辑无关的故障（如系统错误，JVM崩溃等）。为了实现这一点，Spark Streaming 需要快照足够的信息到容错的存储系统上，以便系统可以从故障中恢复。有两种类型的数据需要快照：

(1) Metadata checkpointing：将定义流计算的信息保存到HDFS等容错存储系统中。用来在运行流应用程序的Driver的节点上故障恢复。元数据包括：
- 配置：创建Spark Streaming应用程序的配置信息
- DStream操作符：定义Streaming应用程序的操作集合
- 未完成的batch：对应作业还在队列中未完成的batch

(2) Data checkpointing：将生成的RDD保存到可靠的存储系统中，这在有状态跨batch处理数据的Transformation中是有必要的。在这种Transformation中，生成的RDD依赖于先前batch的RDD，这会导致依赖链的长度会随时间持续增长。为了避免故障恢复时间无限增长（与依赖链的长度成正比）。有状态的Transformation的中间RDD将会定期存储到可靠存储系统中以切断依赖链。

总而言之，元数据检查点主要用于从Driver故障中恢复，如果使用有状态的Transformation，即使基本的函数也需要数据或RDD检查点。





元数据检查点——将定义流计算的信息保存到HDFS等容错存储中。这用于从运行流应用程序驱动程序的节点的故障中恢复(稍后将详细讨论)。元数据包括:

配置——用于创建流应用程序的配置。

DStream操作——定义流应用程序的DStream操作集。

未完成批次——作业已排队但尚未完成的批次。

数据检查点——将生成的rdd保存到可靠的存储中。这在一些跨多个批组合数据的有状态转换中是必要的。在这样的转换中，生成的rdd依赖于前一批的rdd，这导致依赖链的长度随着时间不断增加。为了避免恢复时间的无限增加(与依赖链成比例)，有状态转换的中间rdd会定期检查点到可靠的存储(如HDFS)，以切断依赖链。

总之，元数据检查点主要用于从驱动程序故障中恢复，而如果使用状态转换，则数据或RDD检查点甚至对于基本功能都是必要的。






### 2. 何时开启Checkpointing

当遇到以下场景时，可以为应用程序启用Checkpointing：
- 使用有状态的Transformation：如果在应用程序中使用 updateStateByKey或reduceByKeyAndWindow，则必须提供检查点目录以允许定期RDDCheckpointing。
- 从运行应用程序的Driver上进行故障恢复：元数据检查点根据进度信息进行恢复。

请注意，在运行一个没有上述有状态Transformation的简单流应用程序时可以不启用检查点。在这种情况下，Driver故障恢复也只能恢复一部分（那些已接收但未处理的数据可能会丢失）。这通常是可以接受的，并且许多人以这种方式运行Spark Streaming应用程序。

### 3. 如何配置Checkpointing

可以通过设置一个容错，可靠的文件系统（例如，HDFS，S3等）目录来启用检查点，检查点信息保存到该目录中。这是通过使用 `streamingContext.checkpoint（checkpointDirectory）` 完成。这可以允许你使用上述有状态的Transformation。此外，如果想使应用程序从Driver故障中恢复，则应重写流应用程序以使其具有以下行为：
- 当程序第一次启动时，创建一个新的StreamingContext，启动所有流然后调用`start()` 方法。
- 在失败后重新启动程序时，根据检查点目录中的检查点数据重新创建StreamingContext。


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

如果checkpointDirectory目录存在，则会根据检查点数据重新创建context。如果该目录不存在（即，第一次运行），则将调用函数 `functionToCreateContext` 以创建新context并设置DStream。请参阅示例[RecoverableNetworkWordCount](https://github.com/apache/spark/blob/master/examples/src/main/java/org/apache/spark/examples/streaming/JavaRecoverableNetworkWordCount.java)。

除了使用getOrCreate之外，还需要确保driver进程在失败时自动重新启动。这只能通过用于运行应用程序的部署基础结构来完成。具体请参考：[部署](http://spark.apache.org/docs/latest/streaming-programming-guide.html#deploying-applications)。

请注意，RDD的检查点会导致节省可靠存储的成本。这可能导致RDD被检查点的那些批次的处理时间增加。因此，需要仔细设置检查点的间隔。在小批量（例如1秒）下，每批次检查点可能会显着降低操作吞吐量。相反，检查点过于频繁会导致谱系和任务大小增加，这可能会产生不利影响。对于需要RDD检查点的有状态转换，默认时间间隔是批处理间隔的倍数，至少为10秒。可以使用dstream.checkpoint（checkpointInterval）进行设置。通常，DStream的5-10个滑动间隔的检查点间隔是一个很好的设置。


```java
JavaStreamingContext context = JavaStreamingContext.getOrCreate(checkpointDirectory, new Function0<JavaStreamingContext>() {
    @Override
    public JavaStreamingContext call() throws Exception {
        return null;
    }
});
```

## 从 Checkpoint 中恢复

到目前为止，我们已经发现其实 Checkpoint 的作用在于为有状态的流计算作业保存中间状态，这样下一步的迭代便只需要依赖于中间结果而不是整个作业的血缘关系，否则很有可能要追溯到第一个接收到的元素。试想一下，如果我们的作业在任何一个位置失败了该如何？如果没有 Checkpoint，需要重放过去多久的数据？可能一个小时，可能一天，甚至更久。假设统计的是一整天的数据，那么需要重放一天的数据，然而此时的新数据还源源不断的进来。

Checkpoint 中包含的信息可以让我们的流处理程序从最近一个状态点进行恢复。这意味着只需要重放最近几个批次的数据即可，而不用一个小时或者一天的数据。







https://aiyanbo.gitbooks.io/spark-programming-guide-zh-cn/content/spark-streaming/basic-concepts/checkpointing.html

...
