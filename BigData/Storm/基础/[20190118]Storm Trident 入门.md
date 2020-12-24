### 1. 简介

Trident 是在 Storm 基础上的以实时计算为目标的高级抽象。为你提供高吞吐量的数据处理能力（每秒百万次消息），也提供了低延时的分布式查询和有状态的流式处理。如果你对 Pig 和 Cascading 这种高级批处理工具很了解的话，那么你应该对 Trident 的概念很熟悉的，Trident 提供了 `joins`，`aggregations`，`grouping`，`functions` 以及 `filters`。除此之外，Trident 还提供了在数据库或者其他持久化存储上进行有状态的增量处理的原语。Trident 具有一致性，Exactly-Once 等语义，这使得我们在使用 Trident 拓扑时变得容易一些。

### 2. Example

让我们看一下 Trident 的一个例子。这个例子将做两件事：
- 从输入流的句子中计算单词个数
- 实现查询以获取单词列表的计数总和

下面示例将从下面数据源读取无限句子流：
```java
FixedBatchSpout spout = new FixedBatchSpout(new Fields("sentence"), 3,
               new Values("the cow jumped over the moon"),
               new Values("the man went to the store and bought some candy"),
               new Values("four score and seven years ago"),
               new Values("how many apples can you eat"));
spout.setCycle(true);
```
这个 Spout 一遍又一遍地循环遍历这组句子以产生句子流。下面是流式计算单词数的代码：
```java
TridentTopology topology = new TridentTopology();        
TridentState wordCounts =
     topology.newStream("spout1", spout)
       .each(new Fields("sentence"), new Split(), new Fields("word"))
       .groupBy(new Fields("word"))
       .persistentAggregate(new MemoryMapState.Factory(), new Count(), new Fields("count"))                
       .parallelismHint(6);
```
让我们逐行看一下代码。首先创建一个 TridentTopology 对象，该对象提供了用于构造 Trident 计算的接口。 TridentTopology 有一个名为 newStream 的方法，它从输入源读取数据并创建新的数据流。在这个例子中，输入源是之前定义的 FixedBatchSpout。输入源也可以是像 Kestrel 或 Kafka 这样的消息队列。Trident 在 Zookeeper 中跟踪每个输入源的一些状态（有关它消耗的元数据），代码中的 `spout1` 字符串指定在 Zookeeper 中保留 Trident 元数据的节点。

Trident 将流作为小批量元组处理。 例如，传入的句子流可能会被分成批次，如下所示：













> http://storm.apache.org/releases/current/Trident-tutorial.html
