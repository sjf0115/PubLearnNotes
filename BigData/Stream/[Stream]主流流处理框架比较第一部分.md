---
layout: post
author: 侠天
title: Stream 主流流处理框架比较第一部分
date: 2018-01-10 15:34:01
tags:
  - Stream

categories: Stream
permalink: main-stream-processing-framework-comparison-part-one
---


分布式流处理是对无边界数据集进行连续不断的处理、聚合和分析。它跟`MapReduce`一样是一种通用计算，但我们期望延迟在毫秒或者秒级别。这类系统一般采用有向无环图（`DAG`）。

`DAG`是任务链的图形化表示，我们用它来描述流处理作业的拓扑。如下图，数据从`sources`流经处理任务链到`sinks`。单机可以运行`DAG`，但本篇文章主要聚焦在多台机器上运行`DAG`的情况。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83-1.jpg?raw=true)

### 1. 关注点

当选择不同的流处理系统时，有以下几点需要注意的：
- 运行时和编程模型：平台框架提供的编程模型决定了许多特色功能，编程模型要足够处理各种应用场景。这是一个相当重要的点，后续会继续。
- 函数式原语：流处理平台应该能提供丰富的功能函数，比如，`map`或者`filter`这类易扩展、处理单条信息的函数；处理多条信息的函数`aggregation`；跨数据流、不易扩展的操作`join`。
- 状态管理：大部分应用都需要保持状态处理的逻辑。流处理平台应该提供存储、访问和更新状态信息。
- 消息传输保障：消息传输保障一般有三种：`at most once`，`at least once`和`exactly once`。`At most once`的消息传输机制是每条消息传输零次或者一次，即消息可能会丢失；`At least once`意味着每条消息会进行多次传输尝试，至少一次成功，即消息传输可能重复但不会丢失；`Exactly once`的消息传输机制是每条消息有且只有一次，即消息传输既不会丢失也不会重复。
- 容错：流处理框架中的失败会发生在各个层次，比如，网络部分，磁盘崩溃或者节点宕机等。流处理框架应该具备从所有这种失败中恢复，并从上一个成功的状态（无脏数据）重新消费。
- 性能：延迟时间（`Latency`），吞吐量（`Throughput`）和扩展性（`Scalability`）是流处理应用中极其重要的指标。
- 平台的成熟度和接受度：成熟的流处理框架可以提供潜在的支持，可用的库，甚至开发问答帮助。选择正确的平台会在这方面提供很大的帮助。

### 2. 运行时和编程模型

运行时和编程模型是一个系统最重要的特质，因为它们定义了表达方式、可能的操作和将来的局限性。因此，运行时和编程模型决定了系统的能力和适用场景。

实现流处理系统有两种完全不同的方式：

(1) 一种是称作`原生流处理`，意味着所有输入的记录一旦到达即会一个接着一个进行处理。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83-2.jpg?raw=true)

(2) 第二种称为`微批处理`。把输入的数据按照某种预先定义的时间间隔(典型的是几秒钟)分成短小的批量数据，流经流处理系统。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83-3.jpg?raw=true)

两种方法都有其先天的优势和不足。首先以`原生流处理`开始，原生流处理的优势在于它的表达方式。数据一旦到达立即处理，这些系统的延迟性远比其它微批处理要好。除了延迟性外，原生流处理的状态操作也容易实现，后续将详细讲解。一般原生流处理系统为了达到低延迟和容错性会花费比较大的成本，因为它需要考虑每条记录。原生流处理的负载均衡也是个问题。比如，我们处理的数据按key分区，如果分区的某个key是资源密集型，那这个分区很容易成为作业的瓶颈。

接下来看下`微批处理`。将流式计算分解成一系列短小的批处理作业，也不可避免的减弱系统的表达力。像状态管理或者`join`等操作的实现会变的困难，因为微批处理系统必须操作整个批量数据。并且，`batch interval`会连接两个不易连接的事情：基础属性和业务逻辑。相反地，微批处理系统的容错性和负载均衡实现起来非常简单，因为微批处理系统仅发送每批数据到一个`worker`节点上，如果一些数据出错那就使用其它副本。微批处理系统很容易建立在原生流处理系统之上。

编程模型一般分为`组合式`和`声明式`。组合式编程提供基本的构建模块，它们必须紧密结合来创建拓扑。新的组件经常以接口的方式完成。相对应地，声明式API操作是定义的高阶函数。它允许我们用抽象类型和方法来写函数代码，并且系统创建拓扑和优化拓扑。声明式API经常也提供更多高级的操作（比如，窗口函数或者状态管理）。后面很快会给出样例代码。

### 3. 主流流处理系统

有一系列各种实现的流处理框架，不能一一列举，这里仅选出主流的流处理解决方案，并且支持`Scala API`。因此，我们将详细介绍`Apache Storm`，`Trident`，`Spark Streaming`，`Samza`和`Apache Flink`。前面选择讲述的虽然都是流处理系统，但它们实现的方法包含了各种不同的挑战。这里暂时不讲商业的系统，比如`Google MillWheel`或者`Amazon Kinesis`，也不会涉及很少使用的`Intel GearPump`或者`Apache Apex`。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83-4.jpg?raw=true)

`Apache Storm`最开始是由`Nathan Marz`和他的团队于2010年在数据分析公司`BackType`开发的，后来`BackType`公司被`Twitter`收购，接着`Twitter`开源`Storm`并在2014年成为`Apache`顶级项目。毋庸置疑，`Storm`成为大规模流数据处理的先锋，并逐渐成为工业标准。`Storm`是原生的流处理系统，提供`low-level`的API。`Storm`使用`Thrift`来定义`topology`和支持多语言协议，使得我们可以使用大部分编程语言开发，`Scala`自然包括在内。

`Trident`是对`Storm`的一个更高层次的抽象，`Trident`最大的特点以`batch`的形式进行流处理。`Trident`简化`topology`构建过程，增加了窗口操作、聚合操作或者状态管理等高级操作，这些在`Storm`中并不支持。相对应于`Storm`的`At most once`流传输机制，`Trident`提供了`Exactly once`传输机制。`Trident`支持`Java`，`Clojure`和`Scala`。

当前`Spark`是非常受欢迎的批处理框架，包含`Spark SQL`，`MLlib`和`Spark Streaming`。`Spark`的运行时是建立在批处理之上，因此后续加入的`Spark Streaming`也依赖于批处理，实现了微批处理。接收器把输入数据流分成短小批处理，并以类似`Spark`作业的方式处理微批处理。`Spark Streaming`提供高级声明式API（支持`Scala`，`Java`和`Python`）。

`Samza`最开始是专为`LinkedIn`公司开发的流处理解决方案，并和`LinkedIn`的`Kafka`一起贡献给社区，现已成为基础设施的关键部分。`Samza`的构建严重依赖于基于`log`的`Kafka`，两者紧密耦合。`Samza`提供组合式API，当然也支持`Scala`。

最后来介绍`Apache Flink`。`Flink`是个相当早的项目，开始于2008年，但只在最近才得到注意。`Flink`是原生的流处理系统，提供`high level`的API。`Flink`也提供`API`来像`Spark`一样进行批处理，但两者处理的基础是完全不同的。`Flink`把批处理当作流处理中的一种特殊情况。在`Flink`中，所有的数据都看作流，是一种很好的抽象，因为这更接近于现实世界。

快速的介绍流处理系统之后，让我们以下面的表格来更好清晰的展示它们之间的不同：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83-5.jpg?raw=true)

### 4. Word Count

`Wordcount`之于流处理框架学习，就好比`hello world`之于编程语言学习。它能很好的展示各流处理框架的不同之处，让我们从`Storm`开始看看如何实现`Wordcount`：
```Java
TopologyBuilder builder = new TopologyBuilder();
builder.setSpout("spout", new RandomSentenceSpout(), 5);
builder.setBolt("split", new Split(), 8).shuffleGrouping("spout");
builder.setBolt("count", new WordCount(), 12).fieldsGrouping("split", new Fields("word"));

 ...

Map<String, Integer> counts = new HashMap<String, Integer>();

public void execute(Tuple tuple, BasicOutputCollector collector) {
   String word = tuple.getString(0);
   Integer count = counts.containsKey(word) ? counts.get(word) + 1 : 1;
   counts.put(word, count);
   collector.emit(new Values(word, count));
}
```
首先，定义`topology`。第二行代码定义一个`spout`，作为数据源。然后是一个处理组件`bolt`，分割文本为单词。接着，定义另一个`bolt`来计算单词数（第四行代码）。也可以看到魔数5，8和12，这些是并行度，定义集群每个组件执行的独立线程数。第八行到十五行是实际的`WordCount bolt`实现。因为`Storm`不支持内建的状态管理，所有这里定义了一个局部状态。

按之前描述，`Trident`是对`Storm`的一个更高层次的抽象，`Trident`最大的特点以`batch`的形式进行流处理。除了其它优势，`Trident`提供了状态管理，这对`wordcount`实现非常有用:
```java
public static StormTopology buildTopology(LocalDRPC drpc) {
 FixedBatchSpout spout = ...

 TridentTopology topology = new TridentTopology();
 TridentState wordCounts = topology.newStream("spout1", spout)
 .each(new Fields("sentence"),new Split(), new Fields("word"))
 .groupBy(new Fields("word"))
 .persistentAggregate(new MemoryMapState.Factory(),
 new Count(), new Fields("count"));

 ...

 }
```
如你所见，上面代码使用`higher level`操作，比如`each`（第七行代码）和`groupby`（第八行代码）。并且使用`Trident`管理状态来存储单词数（第九行代码）。

下面是时候祭出提供声明式API的`Apache Spark`。记住，相对于前面的例子，这些代码相当简单，几乎没有冗余代码。下面是简单的流式计算单词数：
```Scala
val conf = new SparkConf().setAppName("wordcount")
val ssc = new StreamingContext(conf, Seconds(1))

val text = ...

val counts = text.flatMap(line => line.split(" "))
 .map(word => (word, 1))
 .reduceByKey(_ + _)

counts.print()

ssc.start()
ssc.awaitTermination()
```
每个`Spark Streaming`的作业都要有`StreamingContext`，它是流式函数的入口。`StreamingContext`加载第一行代码定义的配置`conf`，但更重要地，第二行代码定义`batch interval`（这里设置为1秒）。第六行到八行代码是整个单词数计算。这些是标准的函数式代码，`Spark`定义`topology`并且分布式执行。第十二行代码是每个`Spark Streaming`作业最后的部分：启动计算。记住，`Spark Streaming`作业一旦启动即不可修改。

接下来看下`Apache Samza`，另外一个组合式API例子：
```
class WordCountTask extends StreamTask {

  override def process(envelope: IncomingMessageEnvelope, collector: MessageCollector,
    coordinator: TaskCoordinator) {

    val text = envelope.getMessage.asInstanceOf[String]

    val counts = text.split(" ").foldLeft(Map.empty[String, Int]) {
      (count, word) => count + (word -> (count.getOrElse(word, 0) + 1))
    }

    collector.send(new OutgoingMessageEnvelope(new SystemStream("kafka", "wordcount"), counts))

 }
```
`Samza`的属性配置文件定义`topology`，为了简明这里并没把配置文件放上来。定义任务的输入和输出，并通过`Kafka topic`通信。在单词数计算整个`topology`是`WordCountTask`。在`Samza`中，实现特殊接口定义组件`StreamTask`，在第三行代码重写方法`process`。它的参数列表包含所有连接其它系统的需要。第八行到十行简单的`Scala`代码是计算本身。

`Flink`的API跟`Spark Streaming`是惊人的相似，但注意到代码里并未设置`batch interval`：
```
val env = ExecutionEnvironment.getExecutionEnvironment

 val text = env.fromElements(...)
 val counts = text.flatMap ( _.split(" ") )
   .map ( (_, 1) )
   .groupBy(0)
   .sum(1)

 counts.print()

 env.execute("wordcount")
```
上面的代码是相当的直白，仅仅只是几个函数式调用，Flink支持分布式计算。

### 5. 结论

上面给出了基本的理论和主流流处理框架介绍，下篇文章将会更深入的探讨其它关注点。希望你能对前面的文章感兴趣，如果有任何问题，请联系我讨论这些主题。
















































































原文:http://www.infoq.com/cn/articles/comparison-of-main-stream-processing-framework
