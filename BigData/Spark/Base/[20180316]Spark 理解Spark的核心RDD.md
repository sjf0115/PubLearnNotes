---
layout: post
author: sjf0115
title: Spark 理解Spark的核心RDD
date: 2018-03-16 11:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-core-rdd
---

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-base-core-rdd-1.jpg?raw=true)

与许多专有的大数据处理平台不同，Spark建立在统一抽象的RDD之上，使得它可以以基本一致的方式应对不同的大数据处理场景，包括MapReduce，Streaming，SQL，Machine Learning以及Graph等。这即Matei Zaharia所谓的“设计一个通用的编程抽象（Unified Programming Abstraction）。这正是Spark这朵小火花让人着迷的地方。

要理解Spark，就需得理解RDD。

### 1. RDD是什么？

RDD，全称为Resilient Distributed Datasets，是一个容错的、并行的数据结构，可以让用户显式地将数据存储到磁盘和内存中，并能控制数据的分区。同时，RDD还提供了一组丰富的操作来操作这些数据。在这些操作中，诸如map、flatMap、filter等转换操作实现了monad模式，很好地契合了Scala的集合操作。除此之外，RDD还提供了诸如join、groupBy、reduceByKey等更为方便的操作，以支持常见的数据运算。

通常来讲，针对数据处理有几种常见模型，包括：Iterative Algorithms，Relational Queries，MapReduce，Stream Processing。例如Hadoop MapReduce采用了MapReduces模型，Storm则采用了Stream Processing模型。RDD混合了这四种模型，使得Spark可以应用于各种大数据处理场景。

RDD作为数据结构，本质上是一个只读的分区记录集合。一个RDD可以包含多个分区，每个分区就是一个dataset片段。RDD可以相互依赖。如果RDD的每个分区最多只能被一个子RDD的一个分区使用，则称之为窄依赖；若多个子RDD分区都可以依赖，则称之为宽依赖。不同的操作依据其特性，可能会产生不同的依赖。例如map操作会产生窄依赖，而join操作则产生宽依赖。

Spark之所以将依赖分为窄依赖与宽依赖，基于两点原因。

首先，窄依赖可以支持在同一个cluster node上以管道形式执行多条命令，例如在执行了map后，紧接着执行filter。相反，宽依赖需要所有的父分区都是可用的，可能还需要调用类似MapReduce之类的操作进行跨节点传递。

其次，则是从失败恢复的角度考虑。窄依赖的失败恢复更有效，因为它只需要重新计算丢失的、父partition即可，而且可以并行地在不同节点进行重计算。而宽依赖牵涉到RDD各级的多个父Partitions。下图说明了窄依赖与宽依赖之间的区别：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-base-core-rdd-2.jpg?raw=true)

本图来自Matei Zaharia撰写的论文An Architecture for Fast and General Data Processing on Large Clusters。图中，一个box代表一个RDD，一个带阴影的矩形框代表一个partition。

### 2. RDD如何保障数据处理效率？

RDD提供了两方面的特性persistence和patitioning，用户可以通过persist与patitionBy函数来控制RDD的这两个方面。RDD的分区特性与并行计算能力(RDD定义了parallerize函数)，使得Spark可以更好地利用可伸缩的硬件资源。若将分区与持久化二者结合起来，就能更加高效地处理海量数据。例如：
```
input.map(parseArticle _).partitionBy(partitioner).cache()
```
partitionBy函数需要接受一个Partitioner对象，如：
```
val partitioner = new HashPartitioner(sc.defaultParallelism)
```
RDD本质上是一个内存数据集，在访问RDD时，指针只会指向与操作相关的部分。例如存在一个面向列的数据结构，其中一个实现为Int的数组，另一个实现为Float的数组。如果只需要访问Int字段，RDD的指针可以只访问Int数组，避免了对整个数据结构的扫描。

RDD将操作分为两类：transformation与action。无论执行了多少次transformation操作，RDD都不会真正执行运算，只有当action操作被执行时，运算才会触发。而在RDD的内部实现机制中，底层接口则是基于迭代器的，从而使得数据访问变得更高效，也避免了大量中间结果对内存的消耗。

在实现时，RDD针对transformation操作，都提供了对应的继承自RDD的类型，例如map操作会返回MappedRDD，而flatMap则返回FlatMappedRDD。当我们执行map或flatMap操作时，不过是将当前RDD对象传递给对应的RDD对象而已。例如：
```
def map[U: ClassTag](f: T => U): RDD[U] = new MappedRDD(this, sc.clean(f))
```
这些继承自RDD的类都定义了compute函数。该函数会在action操作被调用时触发，在函数内部是通过迭代器进行对应的转换操作：
```
private[spark]
class MappedRDD[U: ClassTag, T: ClassTag](prev: RDD[T], f: T => U)
  extends RDD[U](prev) {

  override def getPartitions: Array[Partition] = firstParent[T].partitions

  override def compute(split: Partition, context: TaskContext) =
    firstParent[T].iterator(split, context).map(f)
}
```

### 3. RDD对容错的支持

支持容错通常采用两种方式：数据复制或日志记录。对于以数据为中心的系统而言，这两种方式都非常昂贵，因为它需要跨集群网络拷贝大量数据，毕竟带宽的数据远远低于内存。

RDD天生是支持容错的。首先，它自身是一个不变的(immutable)数据集，其次，它能够记住构建它的操作图（Graph of Operation），因此当执行任务的Worker失败时，完全可以通过操作图获得之前执行的操作，进行重新计算。由于无需采用replication方式支持容错，很好地降低了跨网络的数据传输成本。

不过，在某些场景下，Spark也需要利用记录日志的方式来支持容错。例如，在Spark Streaming中，针对数据进行update操作，或者调用Streaming提供的window操作时，就需要恢复执行过程的中间状态。此时，需要通过Spark提供的checkpoint机制，以支持操作能够从checkpoint得到恢复。

针对RDD的wide dependency，最有效的容错方式同样还是采用checkpoint机制。不过，似乎Spark的最新版本仍然没有引入auto checkpointing机制。

### 4. 总结

RDD是Spark的核心，也是整个Spark的架构基础。它的特性可以总结如下：
- 它是不变的数据结构存储
- 它是支持跨集群的分布式数据结构
- 可以根据数据记录的key对结构进行分区
- 提供了粗粒度的操作，且这些操作都支持分区
- 它将数据存储在内存中，从而提供了低延迟性

原文：http://www.infoq.com/cn/articles/spark-core-rdd
