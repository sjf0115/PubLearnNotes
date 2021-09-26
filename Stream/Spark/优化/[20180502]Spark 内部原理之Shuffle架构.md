---
layout: post
author: sjf0115
title: Spark 内部原理之Shuffle架构
date: 2018-05-02 11:33:01
tags:
  - Spark
  - Spark 内部原理

categories: Spark
permalink: spark-internal-shuffle-architecture
---

我们遵循 MapReduce 命名约定。在 Shuffle 操作中，在 Source Executor 中发送数据的任务称之为 `Mapper`，将数据拉取到 Target Executor 的任务称之为 `Reducer`，它们之间过程称之为 `Shuffle`。

一般来说，Shuffle 有2个重要的压缩参数：
- `spark.shuffle.compress` - 是否压缩 shuffle 输出
- `spark.shuffle.spill.compress` - 是否压缩中间 shuffle 溢出文件。
默认值都为 true，并且两者都会使用 `spark.io.compression.codec` 编解码器来压缩数据，默认值为 snappy。

Spark 中有许多 shuffle 实现。使用哪个具体实现取决于 `spark.shuffle.manager` 参数。该参数有三种可选择的值：`hash`, `sort`, `tungsten-sort`，从 Spark 1.2.0 开始 `sort` 是默认选项。

### 2. Hash Shuffle

在 Spark 1.2.0 之前，Shuffle 的默认选项为 `Hash` (`spark.shuffle.manager = hash`)。但它有许多缺点，主要是由它[创建的文件数量](https://people.eecs.berkeley.edu/~kubitron/courses/cs262a-F13/projects/reports/project16_report.pdf)引起的 - 每个 Mapper 任务为每个 Reducer 创建一个文件，从而在集群上会产生 `M * R` 个文件，其中 M 是 Mapper 的个数，R 是 Reducer 的个数。当 Mapper 和 Reducer 数量比较多时会产生比较大的问题，包括输出缓冲区大小，文件系统上打开文件的数量，创建和删除所有这些文件的速度。这有一个雅虎如何面对这些问题时一个很好的[例子](http://spark-summit.org/2013/wp-content/uploads/2013/10/Li-AEX-Spark-yahoo.pdf)，46k个 Mapper 和 46k个 Reducer 在集群上会生成20亿个文件。

这个 shuffler 实现的逻辑非常愚蠢：它将 Reducers 的个数计为 reduce 一侧的分区数量，为每个分区创建一个单独的文件。循环遍历需要输出的记录，然后计算它目标分区，并将记录输出到对应的文件中。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-internal-shuffle-architecture-1.png?raw=true)

该 shuffler　有一个优化的实现，由参数 `spark.shuffle.consolidateFiles` 控制（默认值为 `false`）。当被设置为 `true` 时，Mapper 的输出文件被合并。如果你的集群有 E 个 Executor（在 YARN 中由`-num-executors`设置），每一个都有 C 个 core（在 YARN 中由 `spark.executor.cores` 或 `-executor-cores` 设置），并且每个任务都要求使用 T 个 CPU（由 `spark.task.cpus` 设置），那么集群上的 slots 的个数为 `E * C / T`，在 shuffle 期间创建的文件个数为 `E * C / T * R`。100个 Executor，每个有10个 core，每个任务分配1个core，46000个 Reducer 可以让你从20亿个文件下降到4600万个文件，这在性能方面提升好多。这个功能可以以一种相当直接的方式实现：不是为每个 Reducer 创建新文件，而是创建一个输出文件池。当 map 任务开始输出数据时，从输出文件池申请由 R 个文件组成的一个文件组。完成后，将这个文件组返回到输出文件池中。由于每个 Executor 只能并行执行 `C / T` 个任务，因此只会创建　`C / T` 组输出文件，每个组都是 R 个文件。在第一批 `C / T` 个并行 Mapper 任务完成后，下一批 Mapper 任务重新使用该池中的现有组。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-internal-shuffle-architecture-2.png?raw=true)

优点：
- 快速 - 不需要排序，不维护哈希表;
- 没有内存开销来对数据进行排序;
- 没有IO开销 - 数据只写入硬盘一次并读取一次。

缺点：
- 当分区数量很大时，由于大量的输出文件，性能开始下降;
- 大量文件写入文件系统会导致IO变为随机IO，这通常比顺序IO慢100倍;

当然，当数据写入文件时，会被序列化以及被压缩。读取时，orderTotalCounter.increment(1L);务输出的数据，这会提高性能，但也会增加 Reducer 进程的内存使用量。

如果 reduce 端的没有要求记录排序，那么 Reducer 将只返回一个依赖于 map 输出的迭代器，但是如果需要排序，在 reduce 端使用 [ExternalSorter](https://github.com/apache/spark/blob/master/core/src/main/scala/org/apache/spark/util/collection/ExternalSorter.scala) 对获取的所有数据进行排序。

### 3. Sort Shuffle

从Spark 1.2.0开始，这就是 Spark 使用的默认 shuffle 算法（`spark.shuffle.manager = sort`）。通常来说，这是试图实现类似于 Hadoop MapReduce 所使用的 shuffle 逻辑。使用 `hash shuffle`，你可以为每个 Reducer 输出一个单独的文件，而使用 `sort shuffle` 时：输出一个按  Reducer id 排序的文件并进行索引，通过获取文件中相关数据块的位置信息并在 fread 之前执行 fseek，你就可以轻松地获取与 Reducer x 相关的数据块。但是，当然对于少量的 Reducers 来说，显然使用哈希来分离文件会比排序更快，所以 `sort shuffle` 有一个'后备'计划：当 Reducers 的数量小于 `spark.shuffle.sort.bypassMergeThreshold` 时（默认情况下为200），我们使用'后备'计划通过哈希将数据分到不同的文件中，然后将这些文件合并为一个文件。实现逻辑在类[BypassMergeSortShuffleWriter](https://github.com/apache/spark/blob/master/core/src/main/java/org/apache/spark/shuffle/sort/BypassMergeSortShuffleWriter.java)中实现的。

关于这个实现的有趣之处在于它在 map 端对数据进行排序，但不会在 reduce 端对排序的结果进行合并 - 如果需要排序数据，你需要对数据进行重新排序。 关于 Cloudera 的这个想法可以参阅[博文](http://blog.cloudera.com/blog/2015/01/improving-sort-performance-in-apache-spark-its-a-double/)。实现逻辑充分利用 Mapper 输出已经排序的特点，在 Reducer 端对文件进行合并而不是采取其他手段。我们都知道，Spark 在 Reducer 端使用 TimSort 完成排序，这是一个很棒的排序算法，实际上是利用了输入已经排序的特点（通过计算 minun 并将它们合并在一起）。

如果你没有足够的内存来存储整个 map 输出会怎么样？ 你可能需要将中间数据溢写到磁盘上。参数 `spark.shuffle.spill` 负责启用/禁用溢写，默认情况下会启用溢写。如果你将其禁用并且没有足够的内存来存储 map 输出，那么你会遇到 OOM 错误，因此请注意这一点。

在溢写到磁盘之前，可以用于存储 map 输出的内存量为 `JVM堆大小 * spark.shuffle.memoryFraction * spark.shuffle.safetyFraction`，默认值为 `JVM堆大小 * 0.2 * 0.8` = `JVM堆大小 * 0.16`，具体细节请参考[Spark内部原理之内存管理](http://smartsi.club/2018/04/25/spark-internal-memory-management/)。请注意，如果在同一个 Executor 中运行多个线程（将 `spark.executor.cores / spark.task.cpus` 的比值设置为大于1），那么可用于存储每个任务的 map 输出的平均内存为 `JVM 堆大小 * spark.shuffle.memoryFraction * spark.shuffle.safetyFraction / spark.executor.cores * spark.task.cpus`，对于2核与其他为默认值时，平均内存 `0.08 * JVM堆大小`。

Spark内部使用 [AppendOnlyMap](https://github.com/apache/spark/blob/branch-1.5/core/src/main/scala/org/apache/spark/util/collection/AppendOnlyMap.scala) 数据结构将 map 输出数据存储在内存中。Spark 使用他们自己的用Scala实现的哈希表，该哈希表使用开源哈希算法，并使用[二次探测算法](https://en.wikipedia.org/wiki/Quadratic_probing)将键和值存储在相同的数组中。哈希函数使用Google Guava库的 [MurmurHash3](https://en.wikipedia.org/wiki/MurmurHash) 的 murmur3_32。

该哈希表允许 Spark 在此表上应用 combiner 逻辑 - key 的每个新值都要与已有值通过 combiner 逻辑，而 combiner 的输出将作为新值存储。

当发生溢写时，对存储在 AppendOnlyMap 中的数据调用 sorter，在数据上执行 TimSort 排序算法，然后将数据写入磁盘。

当发生溢写时或者没有更多的 Mapper 输出时，排序好的输出被写入到磁盘，即数据被保证命中磁盘。它是否会真正命中磁盘取决于操作系统的设置，如文件缓冲区缓存，但由操作系统来决定，Spark 只是发送 `写入` 指令。

每个溢写文件分别写入磁盘，只有当数据被 Reducer 请求并且合并是实时的时候，即它不像 Hadoop MapReduce 中发生的那样调用某种 `磁盘上的合并`时，才会执行它们的合并，它只是动态地从大量单独的溢写文件中收集数据，并使用由 Java PriorityQueue 类实现的 Min Heap 将它们合并在一起。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-internal-shuffle-architecture-3.png?raw=true)

优点：
- 在 map 端创建的文件数量较少
- 较少的随机IO操作，主要是顺序写入和读取

缺点：
- 排序比哈希慢。需要调整集群的 `bypassMergeThreshold` 参数以找到最佳点，通常对于大多数集群来说，默认值过高
- 如果你使用SSD驱动器作存储 Spark shuffles 的临时数据，那么 `hash shuffle` 可能更好一些

### 4. Tungsten Sort Shuffle

在 Spark 1.4.0+ 中可以通过设置 `spark.shuffle.manager = tungsten-sort` 来启用。此代码是 `Tungsten` 项目的一部分。在这个 shuffle 中实现的优化是：
- 直接对序列化的二进制数据进行操作，不需要进行反序列化。使用 `unsafe` （`sun.misc.Unsafe`）内存复制函数直接复制数据，这对于序列化数据来说性能比较好，实际上它只是一个字节数组
- 使用特殊的缓存高效分类器 `ShuffleExternalSorter`，对压缩记录指针和分区ID的数组进行排序。在排序数组中每个记录仅占用8个字节的空间，CPU缓存可以更有效地工作，由于记录不需要反序列化，因此直接溢写序列化数据（没有反序列化-比较-序列化-溢写逻辑）
- 当 shuffle 压缩编解码器支持序列化流的连接（即合并每个溢写输出时，只是连接它们）时，会自动应用额外的溢写合并优化。目前，Spark 的 LZF 序列化器支持此功能，并且只有通过参数 `shuffle.unsafe.fastMergeEnabled` 启用快速合并时。

作为优化的下一步，该算法还将引入 off-heap 存储缓冲区。

只有满足以下所有条件时，才会使用此 shuffle 实现：
- shuffle 依赖中不包含聚合。使用聚合意味着需要存储反序列化的值，以便能够当新值传入时可以聚合。这种方式，你将会失去对序列化数据操作的优势
- shuffle 序列化器支持重新定位序列化值（目前，KryoSerializer 和 Spark SQL 的自定义序列化器支持此功能）
- shuffle 产生少于 16777216 个输出分区
- 序列化形式的单个记录不能大于 128 MB

此外，你还必须明白，此时仅通过分区ID执行排序，这意味着优化时在 Reducer 端合并已排序的数据，并利用 TimSort 对先排序的数据进行排序已不再可能。此操作中的排序是基于8字节的值执行的，每个值都能链接到序列化数据项和分区编号，这里有一个1.6b输出分区的限制(here is how we get a limitation of 1.6b output partitions)。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-internal-shuffle-architecture-4.png?raw=true)

首先对于每个溢出数据，将所描述的指针数组排序并输出索引分区文件，然后将这些分区文件合并到一个索引输出文件中。

优点：
- 有许多性能优化

缺点：
- 尚未处理 Mapper 端的数据排序
- 尚未提供 off-heap 排序缓冲区
- 还不稳定

原文:https://0x0fff.com/spark-architecture-shuffle/
