---
layout: post
author: 李雪蕤
title: Spark 性能调优之Shuffle调优
date: 2018-04-28 09:32:17
tags:
  - Spark
  - Spark 优化

categories: Spark
permalink: spark-performance-shuffle-tuning
---

### 1. 调优概述

大多数 Spark 作业的性能主要就是消耗在了 shuffle 环节，因为该环节包含了大量的磁盘IO、序列化、网络数据传输等操作。因此，如果要让作业的性能更上一层楼，就有必要对 shuffle 过程进行调优。但是也必须提醒大家的是，影响一个 Spark 作业性能的因素，主要还是代码开发、资源参数以及数据倾斜，shuffle 调优只能在整个 Spark 的性能调优中占到一小部分而已。因此大家务必把握住调优的基本原则，千万不要舍本逐末。下面我们就给大家详细讲解 shuffle 的原理，以及相关参数的说明，同时给出各个参数的调优建议。

### 2. ShuffleManager发展概述

在Spark的源码中，负责 shuffle 过程的执行、计算和处理的组件主要就是 ShuffleManager，也即 shuffle 管理器。而随着Spark的版本的发展，ShuffleManager也在不断迭代，变得越来越先进。

在Spark 1.2以前，默认的 shuffle 计算引擎是 `HashShuffleManager`。`HashShuffleManager` 有着一个非常严重的弊端，就是会产生大量的中间磁盘文件，进而由大量的磁盘IO操作影响了性能。

因此在Spark 1.2以后的版本中，默认的 ShuffleManager 改成了 `SortShuffleManager`。`SortShuffleManager` 相较于 `HashShuffleManager` 来说，有了一定的改进。主要就在于，每个 Task 在进行 shuffle 操作时，虽然也会产生较多的临时磁盘文件，但是最后会将所有的临时文件合并（merge）成一个磁盘文件，因此每个 Task 就只有一个磁盘文件。在下一个 stage 的 shuffle read task 拉取自己的数据时，只要根据索引读取每个磁盘文件中的部分数据即可。

下面我们详细分析一下 `HashShuffleManager` 和 `SortShuffleManager` 的原理。

### 3. HashShuffleManager运行原理

#### 3.1 未经优化的HashShuffleManager

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-performance-shuffle-tuning-1.png?raw=true)

上图说明了未经优化的 `HashShuffleManager` 的原理。这里我们先明确一个假设前提：每个 Executor 只有1个CPU core，也就是说，无论这个 Executor 上分配多少个 task 线程，同一时间都只能执行一个 task 线程。

我们先从 shuffle write 开始说起。shuffle write 阶段，主要就是在一个 stage 结束计算之后，为了下一个 stage 可以执行 shuffle 类的算子（比如reduceByKey），而将每个 task 处理的数据按 key 进行“分类”。所谓“分类”，就是对相同的 key 执行 hash 算法，从而将相同 key 都写入同一个磁盘文件中，而每一个磁盘文件都只属于下游 stage 的一个 task。在将数据写入磁盘之前，会先将数据写入内存缓冲中，当内存缓冲填满之后，才会溢写到磁盘文件中去。

那么每个执行 shuffle write 的 task，要为下一个 stage 创建多少个磁盘文件呢？很简单，下一个 stage 的 task 有多少个，当前 stage 的每个 task 就要创建多少份磁盘文件。比如下一个 stage 总共有 100 个 task，那么当前 stage 的每个 task 需要创建 100 份磁盘文件。如果当前 stage 有 50 个 task，总共有 10 个 Executor，每个 Executor 执行 5 个 Task，那么每个 Executor 上总共需要创建 500 个磁盘文件，所有 Executor 上会创建 5000 个磁盘文件。由此可见，未经优化的 shuffle write 操作所产生的磁盘文件的数量是极其惊人的。

接着我们来说说 shuffle read。shuffle read，通常就是一个 stage 刚开始时要做的事情。此时该 stage 的每一个 task 就需要将上一个 stage 的计算结果中的所有相同 key，从各个节点上通过网络都拉取到自己所在的节点上，然后进行 key 的聚合或连接等操作。由于 shuffle write 的过程中，上游 stage 的每个 task 给下游 stage 的每个 task 都创建了一个磁盘文件，因此 shuffle read 的过程中，每个 task 都要从上游 stage 的所有 task 所在节点拉取属于自己的那一个磁盘文件。

shuffle read 的拉取过程是一边拉取一边进行聚合的。每个 shuffle read task 都会有一个自己的 buffer 缓冲，每次都只能拉取与 buffer 缓冲相同大小的数据，然后通过内存中的一个 Map 进行聚合等操作。聚合完一批数据后，再拉取下一批数据，并放到 buffer 缓冲中进行聚合操作。以此类推，直到最后将所有数据到拉取完，并得到最终的结果。

#### 3.2 优化后的HashShuffleManager

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-performance-shuffle-tuning-2.png?raw=true)

上图说明了优化后的 `HashShuffleManager` 的原理。这里说的优化，是指我们可以设置一个参数 `spark.shuffle.consolidateFiles`。该参数默认值为 false，将其设置为 true 即可开启优化机制。通常来说，如果我们使用 `HashShuffleManager`，建议开启这个选项。

开启 consolidate 机制之后，在 shuffle write 过程中，task 就不是为下游 stage 的每个 task 创建一个磁盘文件了。此时引入了一个 `shuffleFileGroup` 的概念，每个 `shuffleFileGroup` 会对应一批磁盘文件，磁盘文件的数量与下游 stage 的 task 数量是相同的。一个 Executor 上有多少个 CPU core，就可以并行执行多少个 task。而第一批并行执行的每个 task 都会创建一个 `shuffleFileGroup`，并将数据写入对应的磁盘文件内。

当 Executor 的 CPU core 执行完一批 task，接着执行下一批 task 时，下一批 task 就会复用之前已有的 `shuffleFileGroup`，包括其中的磁盘文件。也就是说，此时 task 会将数据写入已有的磁盘文件中，而不会写入新的磁盘文件中。因此，consolidate 机制允许不同的 task 复用同一批磁盘文件，这样就可以有效将多个 task 的磁盘文件进行一定程度上的合并，从而大幅度减少磁盘文件的数量，进而提升 shuffle write 的性能。

假设第二个 stage 有 100 个 task，第一个 stage 有 50 个 task，总共还是有 10 个 Executor，每个 Executor 执行 5 个 task。那么原本使用未经优化的 `HashShuffleManager` 时，每个 Executor 会产生 500 个磁盘文件，所有 Executor 会产生 5000 个磁盘文件的。但是此时经过优化之后，每个 Executor 此时只会创建 100 个磁盘文件(假设每个 Executor 只有1个CPU core，所以每个 Executor 中并行任务只有一个)，所有 Executor 只会创建 1000 个磁盘文件。

> 每个 Executor 创建的磁盘文件的数量的计算公式为：`CPU core的数量 * 下一个stage的task数量`。

### 4. SortShuffleManager运行原理

`SortShuffleManager` 的运行机制主要分成两种，一种是普通运行机制，另一种是 bypass 运行机制。当 shuffle read task 的数量小于等于 `spark.shuffle.sort.bypassMergeThreshold` 参数的值时（默认为200），就会启用 bypass 机制。

#### 4.1 普通运行机制

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-performance-shuffle-tuning-3.png?raw=true)

上图说明了普通的 `SortShuffleManager` 的原理。在该模式下，数据会先写入一个内存数据结构中，此时根据不同的 shuffle 算子，可能选用不同的数据结构。如果是 reduceByKey 这种聚合类的 shuffle 算子，那么会选用 Map 数据结构，一边通过 Map 进行聚合，一边写入内存；如果是 join 这种普通的 shuffle 算子，那么会选用 Array 数据结构，直接写入内存。接着，每写一条数据进入内存数据结构之后，就会判断一下，是否达到了某个临界阈值。如果达到临界阈值的话，那么就会尝试将内存数据结构中的数据溢写到磁盘，然后清空内存数据结构。

在溢写到磁盘文件之前，会先根据 key 对内存数据结构中已有的数据进行排序。排序过后，会分批将数据写入磁盘文件。默认的 batch 数量是 10000 条，也就是说，排序好的数据，会以每批1万条数据的形式分批写入磁盘文件。写入磁盘文件是通过 Java 的 BufferedOutputStream 实现的。BufferedOutputStream 是 Java 的缓冲输出流，首先会将数据缓冲在内存中，当内存缓冲满溢之后再一次写入磁盘文件中，这样可以减少磁盘IO次数，提升性能。

一个 task 将所有数据写入内存数据结构的过程中，会发生多次磁盘溢写操作，也就会产生多个临时文件。最后会将之前所有的临时磁盘文件都进行合并，这就是 merge 过程，此时会将之前所有临时磁盘文件中的数据读取出来，然后依次写入最终的磁盘文件之中。此外，由于一个 task 就只对应一个磁盘文件，也就意味着该 task 为下游 stage 的 task 准备的数据都在这一个文件中，因此还会单独写一份索引文件，其中标识了下游各个 task 的数据在文件中的 start offset 与 end offset。

`SortShuffleManager` 由于有一个磁盘文件 merge 的过程，因此大大减少了文件数量。比如第一个 stage 有 50 个 task，总共有 10 个 Executor，每个 Executor 执行 5 个 task，而第二个 stage 有 100 个task。由于每个 task 最终只有一个磁盘文件，因此此时每个 Executor 上只有5个磁盘文件，所有 Executor 只有 50 个磁盘文件。

#### 4.2 bypass运行机制

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-performance-shuffle-tuning-4.png?raw=true)

上图说明了　`bypass SortShuffleManager` 的原理。bypass 运行机制的触发条件如下：
- shuffle map task 数量小于 `spark.shuffle.sort.bypassMergeThreshold` 参数的值。
- 不是聚合类的shuffle算子（比如reduceByKey）。

此时 task 会为每个下游 task 都创建一个临时磁盘文件，并将数据按 key 进行 hash 然后根据 key 的 hash 值，将 key 写入对应的磁盘文件之中。当然，写入磁盘文件时也是先写入内存缓冲，缓冲写满之后再溢写到磁盘文件的。最后，同样会将所有临时磁盘文件都合并成一个磁盘文件，并创建一个单独的索引文件。

该过程的磁盘写机制其实跟未经优化的 `HashShuffleManager` 是一模一样的，因为都要创建数量惊人的磁盘文件，只是在最后会做一个磁盘文件的合并而已。因此少量的最终磁盘文件，也让该机制相对未经优化的 HashShuffleManager 来说，shuffle read的性能会更好。

而该机制与普通 `SortShuffleManager` 运行机制的不同在于：第一，磁盘写机制不同；第二，不会进行排序。也就是说，启用该机制的最大好处在于，shuffle write 过程中，不需要进行数据的排序操作，也就节省掉了这部分的性能开销。


### 5. shuffle相关参数调优

以下是Shffule过程中的一些主要参数，这里详细讲解了各个参数的功能、默认值以及基于实践经验给出的调优建议。

(1) `spark.shuffle.file.buffer`
- 默认值：32k
- 参数说明：该参数用于设置 shuffle write task 的 BufferedOutputStream 的 buffer 缓冲大小。将数据写到磁盘文件之前，会先写入 buffer 缓冲中，待缓冲写满之后，才会溢写到磁盘。
- 调优建议：如果作业可用的内存资源较为充足的话，可以适当增加这个参数的大小（比如64k），从而减少 shuffle write 过程中溢写磁盘文件的次数，也就可以减少磁盘IO次数，进而提升性能。在实践中发现，合理调节该参数，性能会有1%~5%的提升。

(2) `spark.reducer.maxSizeInFlight`
- 默认值：48m
- 参数说明：该参数用于设置 shuffle read task 的 buffer 缓冲大小，而这个 buffer 缓冲决定了每次能够拉取多少数据。
- 调优建议：如果作业可用的内存资源较为充足的话，可以适当增加这个参数的大小（比如96m），从而减少拉取数据的次数，也就可以减少网络传输的次数，进而提升性能。在实践中发现，合理调节该参数，性能会有1%~5%的提升。

(3) `spark.shuffle.io.maxRetries`
- 默认值：3
- 参数说明：shuffle read task 从 shuffle write task 所在节点拉取属于自己的数据时，如果因为网络异常导致拉取失败，是会自动进行重试的。该参数就代表了可以重试的最大次数。如果在指定次数之内拉取还是没有成功，就可能会导致作业执行失败。
- 调优建议：对于那些包含了特别耗时的 shuffle 操作的作业，建议增加重试最大次数（比如60次），以避免由于 JVM 的 full gc 或者网络不稳定等因素导致的数据拉取失败。在实践中发现，对于针对超大数据量（数十亿~上百亿）的 shuffle 过程，调节该参数可以大幅度提升稳定性。

(4) `spark.shuffle.io.retryWait`
- 默认值：5s
- 参数说明：具体解释同上，该参数代表了每次重试拉取数据的等待间隔，默认是5s。
- 调优建议：建议加大间隔时长（比如60s），以增加 shuffle 操作的稳定性。

(5) `spark.shuffle.memoryFraction`
- 默认值：0.2
- 参数说明：该参数代表了 Executor 内存中，分配给 shuffle read task 进行聚合操作的内存比例，默认是20%。
- 调优建议：在资源参数调优中讲解过这个参数。如果内存充足，而且很少使用持久化操作，建议调高这个比例，给 shuffle read 的聚合操作更多内存，以避免由于内存不足导致聚合过程中频繁读写磁盘。在实践中发现，合理调节该参数可以将性能提升10%左右。

(6) `spark.shuffle.manager`
- 默认值：sort
- 参数说明：该参数用于设置 ShuffleManager 的类型。Spark 1.5以后，有三个可选项：`hash`、`sort` 和 `tungsten-sort`。`HashShuffleManager` 是Spark 1.2以前的默认选项，Spark 1.2以及之后的版本默认为 `SortShuffleManager` 了。tungsten-sort 与 sort类似，但是使用了 tungsten 计划中的堆外内存管理机制，内存使用效率更高。
- 调优建议：由于 `SortShuffleManager` 默认会对数据进行排序，因此如果你的业务逻辑中需要该排序机制的话，使用默认的 `SortShuffleManager` 就可以；如果你的业务逻辑不需要对数据进行排序，建议参考后面的几个参数调优，通过 bypass 机制或优化的 `HashShuffleManager` 来避免排序操作，同时提供较好的磁盘读写性能。这里要注意的是，tungsten-sort 要慎用，因为之前发现了一些相应的bug。

(7) `spark.shuffle.sort.bypassMergeThreshold`
- 默认值：200
- 参数说明：当 `ShuffleManager` 为 `SortShuffleManager` 时，如果 shuffle read task 的数量小于阈值（默认是200），shuffle write 过程中不会进行排序操作，而是直接按照未经优化的 `HashShuffleManager` 的方式去写数据，但是最后会将每个 task 产生的所有临时磁盘文件都合并成一个文件，并会创建单独的索引文件。
- 调优建议：当你使用 `SortShuffleManager` 时，如果的确不需要排序操作，那么建议将这个参数调大一些，大于 shuffle read task 的数量。那么此时就会自动启用 bypass 机制，map-side 就不会进行排序了，减少了排序的性能开销。但是这种方式下，依然会产生大量的磁盘文件，因此shuffle write性能有待提高。

(8) `spark.shuffle.consolidateFiles`
- 默认值：false
- 参数说明：如果使用 `HashShuffleManager`，该参数有效。如果设置为 true，那么就会开启 consolidate 机制，会大幅度合并 shuffle write 的输出文件，对于 shuffle read task 数量特别多的情况下，这种方法可以极大地减少磁盘IO开销，提升性能。
- 调优建议：如果的确不需要 `SortShuffleManager` 的排序机制，那么除了使用 bypass 机制，还可以尝试将 `spark.shffle.manager` 参数手动指定为hash，使用 `HashShuffleManager`，同时开启 consolidate 机制。在实践中尝试过，发现其性能比开启了 bypass 机制的 `SortShuffleManager` 要高出10%~30%。

原文:https://tech.meituan.com/spark-tuning-pro.html
