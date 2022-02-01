---
layout: post
author: 侠天
title: Stream 主流流处理框架比较第二部分
date: 2018-01-10 16:31:01
tags:
  - Stream

categories: Stream
permalink: main-stream-processing-framework-comparison-part-two
---

在上篇文章中，我们过了下基本的理论，也介绍了主流的流处理框架：`Storm`，`Trident`，`Spark Streaming`，`Samza`和`Flink`。今天咱们来点有深度的主题，比如，容错，状态管理或者性能。除此之外，我们也将讨论开发分布式流处理应用的指南，并给出推荐的流处理框架。

### 1. 容错性

流处理系统的`容错性`与生俱来的比批处理系统难实现。当批处理系统中出现错误时，我们只需要把失败的部分简单重启即可；但对于流处理系统，出现错误就很难恢复。因为线上许多作业都是`7 x 24`小时运行，不断有输入的数据。流处理系统面临的另外一个挑战是`状态一致性`，因为重启后会出现重复数据，并且不是所有的状态操作是幂等的。容错性这么难实现，那下面我们看看各大主流流处理框架是如何处理这一问题。

#### 1.1 Apache Storm

`Storm`使用`上游数据备份`和`消息确认`的机制来保障消息在失败之后会重新处理。消息确认原理：每个操作都会把前一次的操作处理消息的确认信息返回。`Topology`的数据源备份它生成的所有数据记录。当所有数据记录的处理确认信息收到，备份即会被安全拆除。失败后，如果不是所有的消息处理确认信息收到，那数据记录会被数据源数据替换。这保障了没有数据丢失，但数据结果会有重复，这就是`at-least once`传输机制。

`Storm`采用取巧的办法完成了容错性，对每个源数据记录仅仅要求几个字节存储空间来跟踪确认消息。纯数据记录消息确认架构，尽管性能不错，但不能保证`exactly once`消息传输机制，所有应用开发者需要处理重复数据。`Storm`存在低吞吐量和流控问题，因为消息确认机制在反压下经常误认为失败。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-1.png?raw=true)

#### 1.2 Spark Streaming

`Spark Streaming`实现微批处理，容错机制的实现跟`Storm`不一样。微批处理的想法相当简单。`Spark`在集群各`worker`节点上处理`micro-batches`。每个`micro-batches`一旦失败，重新计算就行。因为`micro-batches`本身的不可变性，并且每个`micro-batches`也会持久化，所以`exactly once`传输机制很容易实现。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-2.png?raw=true)

#### 1.3 Samza

`Samza`的实现方法跟前面两种流处理框架完全不一样。`Samza`利用消息系统`Kafka`的持久化和偏移量。`Samza`监控任务的偏移量，当任务处理完消息，相应的偏移量被移除。消息的偏移量会被`checkpoint`到持久化存储中，并在失败时恢复。但是问题在于：从上次`checkpoint`中修复偏移量时并不知道上游消息已经被处理过，这就会造成重复。这就是`at least once`传输机制。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-3.png?raw=true)

#### 1.4 Apache Flink

`Flink`的容错机制是基于分布式快照实现的，这些快照会保存流处理作业的状态(本文对`Flink`的检查点和快照不进行区分，因为两者实际是同一个事物的两种不同叫法。`Flink`构建这些快照的机制可以被描述成[分布式数据流的轻量级异步快照](https://arxiv.org/abs/1506.08603)，它采用`Chandy-Lamport`算法实现。)。如果发生失败的情况，系统可以从这些检查点进行恢复。`Flink`发送`checkpoint`的栅栏（`barrier`）到数据流中（栅栏是`Flink`的分布式快照机制中一个核心的元素），当`checkpoint`的栅栏到达其中一个`operator`，`operator`会接所有收输入流中对应的栅栏（比如，图中`checkpoint n`对应栅栏`n`到`n-1`的所有输入流，其仅仅是整个输入流的一部分）。所以相对于`Storm`，`Flink`的容错机制更高效，因为`Flink`的操作是对小批量数据而不是每条数据记录。但也不要让自己糊涂了，`Flink`仍然是原生流处理框架，它与`Spark Streaming`在概念上就完全不同。`Flink`也提供`exactly once`消息传输机制。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-4.png?raw=true)

### 2. 状态管理

大部分大型流处理应用都涉及到状态。相对于无状态的操作(其只有一个输入数据，处理过程和输出结果)，有状态的应用会有一个输入数据和一个状态信息，然后处理过程，接着输出结果和修改状态信息。因此，我们不得不管理状态信息，并持久化。我们期望一旦因某种原因失败，状态能够修复。状态修复有可能会出现小问题，它并不总是保证`exactly once`，有时也会出现消费多次，但这并不是我们想要的。

#### 2.1 Apache Storm

我们知道，`Storm`提供`at-least once`的消息传输保障。那我们又该如何使用`Trident`做到`exactly once`的语义。概念上貌似挺简单，你只需要提交每条数据记录，但这显然不是那么高效。所以你会想到小批量的数据记录一起提交会优化。`Trident`定义了几个抽象来达到`exactly once`的语义，见下图，其中也会有些局限。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-5.png?raw=true)

#### 2.2 Spark Streaming

`Spark Streaming`是微批处理系统，它把状态信息也看做是一种微批量数据流。在处理每个微批量数据时，`Spark`加载当前的状态信息，接着通过函数操作获得处理后的微批量数据结果并修改加载过的状态信息。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-6.png?raw=true)

#### 2.3 Samza

`Samza`实现状态管理是通过`Kafka`来处理的。`Samza`有真实的状态操作，所以其任务会持有一个状态信息，并把状态改变的日志推送到`Kafka`。如果需要状态重建，可以很容易的从`Kafka`的`topic`重建。为了达到更快的状态管理，`Samza`也支持把状态信息放入本地`key-value`存储中，所以状态信息不必一直在`Kafka`中管理，见下图。不幸的是，`Samza`只提供`at-least once`语义，`exactly once`的支持也在计划中。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-7.png?raw=true)

#### 2.4 Apache Flink

`Flink`提供状态操作，和`Samza`类似。`Flink`提供两种类型的状态：一种是用户自定义状态；另外一种是窗口状态。如图，第一个状态是自定义状态，它和其它的的状态不相互作用。这些状态可以分区或者使用嵌入式`Key-Value`存储状态(参阅[文容错](https://ci.apache.org/projects/flink/flink-docs-release-1.0/apis/streaming/fault_tolerance.html)和[状态](https://ci.apache.org/projects/flink/flink-docs-release-1.0/apis/streaming/state.html))。当然`Flink`提供`exactly-once`语义。下图展示`Flink`长期运行的三个状态。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-8.png?raw=true)

### 3. 单词计数例子中的状态管理

单词计数的详细代码见上篇文章，这里仅关注状态管理部分。

让我们先看`Trident`：
```
public static StormTopology buildTopology(LocalDRPC drpc) {
   FixedBatchSpout spout = ...

   TridentTopology topology = new TridentTopology();

   TridentState wordCounts = topology.newStream("spout1", spout)
     .each(new Fields("sentence"),new Split(), new Fields("word"))
     .groupBy(new Fields("word"))
     .persistentAggregate(new MemoryMapState.Factory(), new Count(), new Fields("count"));

 ...

 }
```
在第九行代码中，我们通过调用`persistentAggregate`创建一个状态。其中参数`Count`存储单词数，如果你想从状态中处理数据，你必须创建一个数据流。从代码中也可以看出实现起来不方便。

`Spark Streaming`声明式的方法稍微好点：
```
// Initial RDD input to updateStateByKey
val initialRDD = ssc.sparkContext.parallelize(List.empty[(String, Int)])

val lines = ...
val words = lines.flatMap(_.split(" "))
val wordDstream = words.map(x => (x, 1))

val trackStateFunc = (batchTime: Time, word: String, one: Option[Int],
  state: State[Int]) => {
    val sum = one.getOrElse(0) + state.getOption.getOrElse(0)
    val output = (word, sum)
    state.update(sum)
    Some(output)
  }

val stateDstream = wordDstream.trackStateByKey(
  StateSpec.function(trackStateFunc).initialState(initialRDD))
```
首先我们需要创建一个`RDD`来初始化状态（第二行代码），然后进行`transformations`（第五行和六行代码）。接着在第八行到十四行代码，我们定义函数来处理单词数状态。函数计算并更新状态，最后返回结果。第十六行和十七行代码，我们得到一个状态信息流，其中包含单词数。

接着我们看下`Samza`:
```
class WordCountTask extends StreamTask with InitableTask {

  private var store: CountStore = _

  def init(config: Config, context: TaskContext) {
    this.store = context.getStore("wordcount-store")
      .asInstanceOf[KeyValueStore[String, Integer]]
  }

 override def process(envelope: IncomingMessageEnvelope,
   collector: MessageCollector, coordinator: TaskCoordinator) {

   val words = envelope.getMessage.asInstanceOf[String].split(" ")

   words.foreach { key =>
     val count: Integer = Option(store.get(key)).getOrElse(0)
     store.put(key, count + 1)
     collector.send(new OutgoingMessageEnvelope(new SystemStream("kafka", "wordcount"),
       (key, count)))
   }
 }
```
首先在第三行代码定义状态，进行`Key-Value`存储，在第五行到八行代码初始化状态。接着在计算中使用，上面的代码已经很直白。

最后，讲下`Flink`使用简洁的API实现状态管理：
```
val env = ExecutionEnvironment.getExecutionEnvironment

val text = env.fromElements(...)
val words = text.flatMap ( _.split(" ") )

words.keyBy(x => x).mapWithState {
  (word, count: Option[Int]) =>
    {
      val newCount = count.getOrElse(0) + 1
      val output = (word, newCount)
      (output, Some(newCount))
    }
}
```
我们仅仅需要在第六行代码中调用`mapwithstate`函数，它有一个函数参数（函数有两个变量，第一个是单词，第二个是状态。然后返回处理的结果和新的状态）。

### 4. 流处理框架性能

这里所讲的性能主要涉及到的是`延迟性`和`吞吐量`。

对于延迟性来说，微批处理一般在秒级别，大部分原生流处理在百毫秒以下，调优的情况下`Storm`可以很轻松的达到十毫秒。

同时也要记住，消息传输机制保障，容错性和状态恢复都会占用机器资源。例如，打开容错恢复可能会降低10％到15％的性能，`Storm`可能降低70%的吞吐量。总之，天下没有免费的午餐。对于有状态管理，`Flink`会降低25%的性能，`Spark Streaming`降低50%的性能。

也要记住，各大流处理框架的所有操作都是分布式的，通过网络发送数据是相当耗时的，所以要利用数据本地性，也尽量优化你的应用的序列化。

### 5. 项目成熟度

当你为应用选型时一定会考虑项目的成熟度。下面来快速浏览一下：
`Storm`是第一个主流的流处理框架，后期已经成为长期的工业级的标准，并在像`Twitter`，`Yahoo`，`Spotify`等大公司使用。`Spark Streaming`是最近最流行的`Scala`代码实现的流处理框架。现在`Spark Streaming`被公司（`Netflix`, `Cisco`, `DataStax`, `Intel`, `IBM`等）日渐接受。`Samza`主要在`LinkedIn`公司使用。`Flink`是一个新兴的项目，很有前景。

你可能对项目的贡献者数量也感兴趣。`Storm`和`Trident`大概有180个代码贡献者；整个`Spark`有720多个；根据`github`显示，`Samza`有40个；`Flink`有超过130个代码贡献者。

### 6. 小结

在进行流处理框架推荐之前，先来整体看下总结表：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-9.png?raw=true)

### 7. 流处理框架推荐

应用选型是大家都会遇到的问题，一般是根据应用具体的场景来选择特定的流处理框架。下面给出几个作者认为优先考虑的点：
- `High level API`：具有`high level API`的流处理框架会更简洁和高效；
- 状态管理：大部分流处理应用都涉及到状态管理，因此你得把状态管理作为评价指标之一；
- `exactly once`语义：`exactly once`会使得应用开发变得简单，但也要看具体需求，可能`at least once`或者`at most once`语义就满足你得要求；
- 自动恢复：确保流处理系统能够快速恢复，你可以使用`Chaos Monkey`或者类似的工具进行测试。快速的恢复是流处理重要的部分。

`Storm`：`Storm`非常适合任务量小但速度要求高的应用。如果你主要在意流处理框架的延迟性，`Storm`将可能是你的首先。但同时也要记住，`Storm`的容错恢复或者`Trident`的状态管理都会降低整体的性能水平。也有一个潜在的`Storm`更新项目-`Twitter`的`Heron`，`Heron`设计的初衷是为了替代`Storm`，并在每个单任务上做了优化但同时保留了API。

`Spark Streaming`：如果你得基础架构中已经涉及到`Spark`，那`Spark Streaming`无疑是值得你尝试的。因为你可以很好的利用`Spark`各种`library`。如果你需要使用`Lambda`架构，`Spark Streaming`也是一个不错的选择。但你要时刻记住微批处理的局限性，以及它的延迟性问题。

`Samza`：如果你想使用`Samza`，那`Kafka`应该是你基础架构中的基石，好在现在`Kafka`已经成为家喻户晓的组件。像前面提到的，`Samza`一般会搭配强大的本地存储一起，这对管理大数据量的状态非常有益。它可以轻松处理上万千兆字节的状态信息，但要记住`Samza`只支持`at least once`语义。

`Flink`：`Flink`流处理系统的概念非常不错，并且满足绝大多数流处理场景，也经常提供前沿的功能函数，比如，高级窗口函数或者时间处理功能，这些在其它流处理框架中是没有的。同时`Flink`也有API提供给通用的批处理场景。但你需要足够的勇气去上线一个新兴的项目，并且你也不能忘了看下`Flink`的`roadmap`。

### 8. Dataflow和开源

最后，我们来聊下`Dataflow`和它的开源。`Dataflow`是`Google`云平台的一部分，`Google`云平台包含很多组件：大数据存储，`BigQuery`，`Cloud PubSub`，数据分析工具和前面提到的`Dataflow`。

`Dataflow`是`Google`管理批处理和流处理的统一API。它是建立在`MapReduce`（批处理），`FlumeJava`（编程模型）和`MillWheel`（流处理）之上。`Google`最近决定开源`Dataflow SDK`，并完成`Spark`和`Flink`的`runner`。现在可以通过`Dataflow`的API来定义`Google`云平台作业、`Flink`作业或者`Spark`作业，后续会增加对其它引擎的支持。

`Google`为`Dataflow`提供`Java`、`Python`的API，社区已经完成`Scalable`的`DSL`支持。除此之外，`Google`及其合作者提交`Apache Beam`到`Apache`。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Stream/%E4%B8%BB%E6%B5%81%E6%B5%81%E5%A4%84%E7%90%86%E6%A1%86%E6%9E%B6%E6%AF%94%E8%BE%83%E4%B9%8B%E4%BA%8C-10.png?raw=true)


























原文:http://www.infoq.com/cn/articles/comparison-of-main-stream-processing-framework-part02?utm_source=infoq&utm_campaign=user_page&utm_medium=link
