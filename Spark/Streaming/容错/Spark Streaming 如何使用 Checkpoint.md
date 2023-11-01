
> Spark Streaming 版本：3.1.1

## 1. 概述

一个流应用程序必须 7*24 小时全天候运行，所以必须能够解决与应用程序逻辑无关的故障（如系统错误，JVM崩溃等）。为了实现这一点，Spark Streaming 需要实现 Checkpoint 机制，能够定期保存一些必要的信息以便在重启流处理程序时不会丢失数据，也就不需要重新处理整个过程。考虑一下如果没有 Checkpoint 机制，在处理有状态的 Spark Streaming 应用程序时，重启有状态的流处理程序需要重建状态到之前程序停止的位置。对于窗口操作来说，重启过程可能需要包含几个小时的数据，这会占用非常多的中间存储。

目前有两种类型的数据需要定期保存：
- 元数据快照：将定义流计算的信息保存到 HDFS 等容错存储系统中。用来在运行流应用程序的 Driver 的节点上故障恢复。元数据包括：
  - 配置：创建 Spark Streaming 应用程序的配置信息
  - DStream 操作符：定义 Streaming 应用程序的操作集合
  - 未完成的 batch：对应作业还在队列中未完成的 batch
- 数据快照：将生成的 RDD 保存到可靠的存储系统中，这在有状态 Transformation 中是有必要的(跨 batch 的数据处理)。在这种 Transformation 中，生成的 RDD 依赖于先前 batch 的 RDD，这会导致依赖链的长度会随时间持续增长。为了避免故障恢复时间无限增长（与依赖链的长度成正比）。有状态的 Transformation 的中间 RDD 将会定期存储到可靠存储系统中以切断依赖链。


## 2. 何时开启 checkpoint

当遇到以下场景时，可以为应用程序启用 checkpoint：
- 使用有状态的 Transformation：如果在应用程序中使用 updateStateByKey 或 reduceByKeyAndWindow，则必须提供检查点目录以允许定期对 RDD 快照。
- 从运行应用程序的 Driver 上进行故障恢复：元数据检查点根据进度信息进行恢复。

请注意，运行一个没有状态的 Transformation 的简单流应用程序时可以不启用检查点。在这种情况下，Driver 故障恢复也只能恢复一部分（那些已接收但未处理的数据可能会丢失）。这通常是可以接受的，并且许多人以这种方式运行 Spark Streaming 应用程序。

## 3. 如何配置 checkpoint

可以通过设置一个容错，可靠的文件系统（例如，HDFS，S3等）目录来启用检查点，检查点信息保存到该目录中。这是通过使用 `streamingContext.checkpoint(checkpointDirectory)` 完成。这可以允许你使用上述有状态的 Transformation。此外，如果想使应用程序从 Driver 故障中恢复，则应重写流应用程序以使其具有以下行为：
- 当程序第一次启动时，创建一个新的 StreamingContext，启动所有流然后调用 `start()` 方法。
- 在失败后重新启动程序时，根据检查点目录中的检查点数据重新创建 StreamingContext。

现在假设我们有个流处理作业计算到单词每小时的出现次数，使用 mapWithState 来处理单词流，并利用事件中包含的时间戳进行整合操作。




使用 `JavaStreamingContext.getOrCreate`可以简化此行为。如何使用如下所示：
```java
JavaStreamingContext context = JavaStreamingContext.getOrCreate(checkpointDirectory, new Function0<JavaStreamingContext>() {
        @Override
        public JavaStreamingContext call() throws Exception {
            SparkConf conf = new SparkConf().setAppName("SocketRecoverableWordCount").setMaster("local[2]");
            JavaSparkContext sparkContext = new JavaSparkContext(conf);
            JavaStreamingContext ssc = new JavaStreamingContext(sparkContext, Durations.seconds(20));
            ssc.checkpoint(checkpointDirectory);
            JavaReceiverInputDStream<String> lines = ssc.socketTextStream(hostName, port);
            ...
            return ssc;
        }
    });
    context.start();
    context.awaitTermination();
}
```
如果 checkpointDirectory 目录存在，则会根据检查点数据重新创建 JavaStreamingContext。如果目录不存在(即认为是第一次运行)，那么会调用函数 `Function0<JavaStreamingContext>()` 来创建新的 JavaStreamingContext 并设置 DStream。完整代码请参阅示例[RecoverableNetworkWordCount]()。

需要注意的是在 Spark 2.1.1 版本之前，使用如下方式来实现，新版本中已经废弃由上述方式代替实现：
```java
JavaStreamingContextFactory contextFactory = new JavaStreamingContextFactory() {
  @Override public JavaStreamingContext create() {
    JavaStreamingContext jssc = new JavaStreamingContext(...);
    JavaDStream<String> lines = jssc.socketTextStream(...);
    ...
    jssc.checkpoint(checkpointDirectory);
    return jssc;
  }
};

// 从 Checkpoint 快照中生成一个 JavaStreamingContext 或者直接创建一个新的
JavaStreamingContext context = JavaStreamingContext.getOrCreate(checkpointDirectory, contextFactory);
...
context.start();
context.awaitTermination();
```

## 4. 如何从 Checkpoint 中恢复

到目前为止，我们已经发现其实 Checkpoint 的作用在于为有状态的流计算作业保存中间状态，这样下一步的迭代便只需要依赖于中间结果而不是整个作业的血缘关系，否则很有可能要追溯到第一个接收到的元素。试想一下，如果我们的作业在任何一个位置失败了该如何？如果没有 Checkpoint，需要重放过去多久的数据？可能一个小时，可能一天，甚至更久。假设统计的是一整天的数据，那么需要重放一天的数据，然而此时的新数据还源源不断的进来。

Checkpoint 中包含的信息可以让我们的流处理程序从最近一个状态点进行恢复。这意味着只需要重放最近几个批次的数据即可，而不用一个小时或者一天的数据。

https://aiyanbo.gitbooks.io/spark-programming-guide-zh-cn/content/spark-streaming/basic-concepts/checkpointing.html

...
