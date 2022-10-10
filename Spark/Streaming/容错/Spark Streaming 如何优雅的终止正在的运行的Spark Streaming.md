---
layout: post
author: sjf0115
title: Spark Streaming 如何优雅的终止正在的运行的 Spark Streaming
date: 2018-07-01 15:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: stop-your-spark-streaming-application-gracefully
---

你刚刚将 Spark Streaming 应用程序提交到你的集群，所有 Worker 节点以及接收器都在有条不紊的正常工作。接收器接收来自数据源（例如 Kafka）的数据并通知 Driver。然后 Driver 向 Worker 节点安排任务来处理这些数据（例如，转换并存储在某处）。现在如果你需要重新启动或重新部署应用程序，该怎么办？

## 1. 优雅停止 OR 丢失数据

是的，如果你只是终止应用程序，例如直接使用 kill 命令强制终止 Master 上的 Driver 进程，这种手段是可以达到停止的目的，但是无法保证会处理所有的数据，可能会造成数据的丢失。这是因为接收器已经接收了数据但是 Worker 节点还没来得及处理，所以那些正在处理或者还没有处理的数据可能就会被丢失。停止应用程序时，Driver 将会关闭并丢弃仍需要执行的任务。那我们如何避免丢失数据呢？这里有两种优雅停止的方法：
- 等作业运行完再关闭
- 通过 Spark 内置机制关闭

## 2. 优雅停止

### 2.1 等作业运行完再关闭

我们都知道，Spark Streaming 每隔批次间隔时间就会把源源不断的流数据分割成一批有限数据集，然后计算这些数据，我们可以从 Spark 提供的监控页面看到当前批次是否执行完成，当作业执行完，我们就可以手动执行 kill 命令来强制关闭这个 Streaming 作业。这种方式的缺点就是得盯着监控页面，然后决定关不关闭，很不灵活。

### 2.2 通过 Spark 内置机制关闭

Spark Streaming 应用程序是一个长时间运行的应用程序，因此当你决定将其关闭时，从哪里调用方法来关闭显得并不明显。实现 Spark 应用程序公开的 HTTP 服务，该服务会触发 `StreamingContext.stop（...）` 方法。这是一种有效的方法，但是为了能够停止应用程序而生成 HTTP 服务器是否值得？是否还有一个更简单的方法。

考虑到这一点，最简单的解决方案是当 kill 时处理发送给 Driver 进程的 SIGTERM 信号。使用 Scala，可以使用关闭钩子，特别是 sys.ShutdownHookThread 轻松实现。

其实 Spark 为我们内置提供了一种优雅的方法来关闭长期运行的 Streaming 作业，我们来看看 StreamingContext 类中定义的一个 stop 方法：
```scala
def stop(stopSparkContext: Boolean, stopGracefully: Boolean)
```
停止流的执行，可以使用可选选项来确保所有已接收的数据全部处理。如果 stopSparkContext 为true，则停止相关联的 SparkContext。无论 StreamingContext 是否已启动，底层的SparkContext都将被停止。控制所有接收的数据是否被处理的参数就是 stopGracefully，如果我们将它设置为true，Spark则会等待所有接收的数据被处理完成，然后再关闭计算引擎，这样就可以避免数据的丢失。现在的问题是我们在哪里调用这个stop方法？

#### 2.2.1 Spark 1.4 版本之前

在 Spark 1.4 版本之前，我们需要手动调用这个 stop 方法，一种比较合适的方式是通过 `Runtime.getRuntime().addShutdownHook` 来添加一个钩子，其会在 JVM 关闭的之前执行传递给它的函数，如下：
```scala
Runtime.getRuntime().addShutdownHook(new Thread() {
  override
  def run() {
    log("Gracefully stop Spark Streaming")
    streamingContext.stop(true, true)
  }
})
```
如果你使用的是 Scala，我们还可以通过以下的方法实现类似的功能：
```scala
scala.sys.addShutdownHook({
  streamingContext.stop(true,true)
)})
```
通过上面的办法，我们客户确保程序退出之前会执行上面的函数，从而保证 Streaming 程序关闭的时候不丢失数据。

#### 2.2.2 Spark 1.4 版本之后

上面方式可以达到我们的需求，但是在每个程序里面都添加这样的重复代码也未免太过麻烦了！值得高兴的是，从 Apache Spark 1.4 版本开始，Spark内置提供了 `spark.streaming.stopGracefullyOnShutdown` 参数来决定是否需要以 Gracefully 方式来关闭 Streaming 程序（详情请参见[SPARK-7776](https://issues.apache.org/jira/browse/SPARK-7776)）。Spark 会在启动 StreamingContext 的时候注册这个钩子，如下：
```scala
shutdownHookRef = ShutdownHookManager.addShutdownHook(StreamingContext.SHUTDOWN_HOOK_PRIORITY)(stopOnShutdown)

private def stopOnShutdown(): Unit = {
    val stopGracefully = conf.getBoolean("spark.streaming.stopGracefullyOnShutdown", false)
    logInfo(s"Invoking stop(stopGracefully=$stopGracefully) from shutdown hook")
    // Do not stop SparkContext, let its own shutdown hook stop it
    stop(stopSparkContext = false, stopGracefully = stopGracefully)
}
```
从上面的代码可以看出，我们可以根据自己的需求来设置 `spark.streaming.stopGracefullyOnShutdown` 的值，而不需要在每个 Streaming 程序里面手动调用 StreamingContext 的 stop 方法，确实方便多了。不过虽然这个参数在 Spark 1.4 开始引入，但是却是在 Spark 1.6 才开始才有文档正式介绍（可以参见https://github.com/apache/spark/pull/8898 和 http://spark.apache.org/docs/1.6.0/configuration.html）

参考:
- https://www.iteblog.com/archives/1890.html
- https://metabroadcast.com/blog/stop-your-spark-streaming-application-gracefully
