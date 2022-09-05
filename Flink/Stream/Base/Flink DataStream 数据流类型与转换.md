

Flink DataStream API 的核心，就是代表流数据的 DataStream 对象。整个计算逻辑图的构建就是围绕调用 DataStream 对象上的不同操作产生新的 DataStream 对象展开的。整体来说，DataStream 上的操作可以分为四类：
- 第一类是对于单条记录的操作。比如筛除掉不符合要求的记录（Filter 操作），或者将每条记录都做一个转换（Map 操作）。
- 第二类是对多条记录的操作。比如说统计一个小时内的订单总成交量，就需要将一个小时内的所有订单记录的成交量加到一起。为了支持这种类型的操作，就得通过 Window 将需要的记录关联到一起进行处理。
- 第三类是对多个流进行操作并转换为单个流。例如，多个流可以通过 Union、Join 或 Connect 等操作合到一起。这些操作合并的逻辑不同，但是它们最终都会产生了一个新的统一的流，从而可以进行一些跨流的操作。
- 最后一类是将一个流按一定规则拆分为多个流。每个流是之前流的一个子集，这样我们就可以对不同的流作不同的处理。

为了支持这些不同的流操作，Flink 引入了一组不同的流类型，用来表示某些操作的中间流数据集类型。完整的类型转换关系如下图所示：

![]()

首先，对于一些针对单条记录的操作，如 Map 等，操作的结果仍然是是基本的 DataStream。然后，对于 Split 操作，它会首先产生一个 SplitStream，基于 SplitStream 可以使用 Select 方法来筛选出符合要求的记录并再将得到一个基本的 DataStream。

类似的，对于 Connect 操作，在调用 streamA.connect(streamB) 后可以得到一个专门的 ConnectedStream。ConnectedStream 支持的操作与普通的 DataStream 有所区别，由于它代表两个不同的流混合的结果，因此它允许用户对两个流中的记录分别指定不同的处理逻辑，然后它们的处理结果形成一个新的 DataStream 流。由于不同记录的处理是在同一个算子中进行的，因此它们在处理时可以方便的共享一些状态信息。上层的一些 Join 操作，在底层也是需要依赖于 Connect 操作来实现的。

另外，我们可以通过 Window 操作对流可以按时间或者个数进行一些切分，从而将流切分成一个个较小的分组。具体的切分逻辑可以由用户进行选择。当一个分组中所有记录都到达后，用户可以拿到该分组中的所有记录，从而可以进行一些遍历或者累加操作。这样，对每个分组的处理都可以得到一组输出数据，这些输出数据形成了一个新的基本流。

对于普通的 DataStream，我们必须使用 allWindow 操作，它代表对整个流进行统一的 Window 处理，因此是不能使用多个算子实例进行同时计算的。针对这一问题，就需要我们首先使用 KeyBy 方法对记录按 Key 进行分组，然后才可以并行的对不同 Key 对应的记录进行单独的 Window 操作。

## 1. DataStream

DataStream 是 Flink 流处理 API 中最核心的数据结构。表示一个运行在多个分区上的并行流。一个 DataStream 可以通过 StreamExecutionEnvironment 的 addSource(SourceFunction) 方法获取。

DataStream 上的转换操作都是逐条的，比如 map()，flatMap()，filter()。DataStream 也可以执行 rebalance（再平衡，用来减轻数据倾斜）和 broadcaseted（广播）等分区转换：
```java

```
上述 DataStream 上的转换在运行时会转换成如下的执行图：

![]()

DataStream 各个算子会并行运行，数据流分区是从一个并行算子实例流向一个或多个目标算子实例的数据流。在上面示例中，Source 的第一个并行实例（S1）和 flatMap() 的第一个并行实例（m1）之间就是一个数据流分区。由于在 flatMap() 和 map() 之间增加了 rebalance()，flatMap() 的第一个实例（m1）流向了 map() 的所有实例（r1, r2, r3），因此它们之间的数据流分区就有 3 个子分区（m1 的数据流向 3个 map() 实例）。所以上面示例中的数据流有三个分区（起源于并行的 flatMap() 实例），每个分区都有三个子分区（针对不同的 map() 实例）。

> 熟悉 Apache Kafka 的同学可以把流想象成 Kafka Topic，而一个流分区就表示一个 Topic Partition。

## 2. KeyedStream

KeyedStream 用来表示根据指定的 key 进行分组的数据流。一个 KeyedStream 可以通过调用 DataStream.keyBy() 来获得。而在 KeyedStream 上进行任何 transformation 都将转变回 DataStream。在实现中，KeyedStream 是把 key 的信息写入到了 transformation 中。每条记录只能访问所属 key 的状态，其上的聚合函数可以方便地操作和保存对应 key 的状态。

## 3. WindowedStream & AllWindowedStream

WindowedStream 代表了根据 key 分组，并且基于 WindowAssigner 切分窗口的数据流。所以 WindowedStream 都是从 KeyedStream 衍生而来的。而在 WindowedStream 进行任何 transformation 也都将转变回 DataStream。

```java
val stream: DataStream[MyType] = ...
val windowed: WindowedDataStream[MyType] = stream
        .keyBy("userId")
        .window(TumblingEventTimeWindows.of(Time.seconds(5))) // Last 5 seconds of data
val result: DataStream[ResultType] = windowed.reduce(myReducer)
```
上述 WindowedStream 的样例代码在运行时会转换成如下的执行图：

![]()

Flink 的窗口实现中会将到达的数据缓存在对应的窗口 buffer 中（一个数据可能会对应多个窗口）。当到达窗口发送的条件时（由 Trigger 控制），Flink 会对整个窗口中的数据进行处理。Flink 在聚合类窗口有一定的优化，即不会保存窗口中的所有值，而是每到一个元素执行一次聚合函数，最终只保存一份数据即可。

在 key 分组的流上进行窗口切分是比较常用的场景，也能够很好地并行化（不同的key上的窗口聚合可以分配到不同的task去处理）。不过有时候我们也需要在普通流上进行窗口的操作，这就是 AllWindowedStream。AllWindowedStream 是直接在 DataStream 上进行 windowAll(...) 操作。AllWindowedStream 的实现是基于 WindowedStream 的（Flink 1.1.x 开始）。Flink 不推荐使用 AllWindowedStream，因为在普通流上进行窗口操作，就势必需要将所有分区的流都汇集到单个的Task中，而这个单个的Task很显然就会成为整个Job的瓶颈。

## 5. JoinedStreams & CoGroupedStreams

双流 Join 也是一个非常常见的应用场景。深入源码你可以发现，JoinedStreams 和 CoGroupedStreams 的代码实现有80%是一模一样的，JoinedStreams 在底层又调用了 CoGroupedStreams 来实现 Join 功能。除了名字不一样，一开始很难将它们区分开来，而且为什么要提供两个功能类似的接口呢？？

实际上这两者还是很点区别的。首先 co-group 侧重的是group，是对同一个key上的两组集合进行操作，而 join 侧重的是pair，是对同一个key上的每对元素进行操作。co-group 比 join 更通用一些，因为 join 只是 co-group 的一个特例，所以 join 是可以基于 co-group 来实现的（当然有优化的空间）。而在 co-group 之外又提供了 join 接口是因为用户更熟悉 join（源于数据库吧），而且能够跟 DataSet API 保持一致，降低用户的学习成本。

JoinedStreams 和 CoGroupedStreams 是基于 Window 上实现的，所以 CoGroupedStreams 最终又调用了 WindowedStream 来实现。

## 6. ConnectedStream

在 DataStream 上有一个 union 的转换 dataStream.union(otherStream1, otherStream2, ...)，用来合并多个流，新的流会包含所有流中的数据。union 有一个限制，就是所有合并的流的类型必须是一致的。ConnectedStreams 提供了和 union 类似的功能，用来连接两个流，但是与 union 转换有以下几个区别：

ConnectedStreams 只能连接两个流，而 union 可以连接多于两个流。
ConnectedStreams 连接的两个流类型可以不一致，而 union 连接的流的类型必须一致。
ConnectedStreams 会对两个流的数据应用不同的处理方法，并且双流之间可以共享状态。这在第一个流的输入会影响第二个流时, 会非常有用。
如下 ConnectedStreams 的样例，连接 input 和 other 流，并在input流上应用map1方法，在other上应用map2方法，双流可以共享状态（比如计数）。

## 7. SplitStream

https://www.hnbian.cn/posts/ca73496c.html
http://wuchong.me/blog/2016/05/20/flink-internals-streams-and-operations-on-streams/
https://www.infoq.cn/article/igyoaq8_g3io63sqpgle
https://cwiki.apache.org/confluence/display/FLINK/Streams+and+Operations+on+Streams
