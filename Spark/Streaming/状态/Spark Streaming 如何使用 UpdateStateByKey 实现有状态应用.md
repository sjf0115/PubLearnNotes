有时候可能需要依赖流中前几个批次中的元素来计算当前批次的结果。例如，计算流中所有元素的和，计算当前元素值与之前元素的差值。这种运算会在遍历整个流的期间不断更新计算状态。在 Spark Streaming 中提供了 updateStateByKey 和 MapWithState 函数来实现。本文主要介绍如何使用 updateStateByKey 函数实现有状态应用。

## 1. updateStateByKey

在 Spark Streaming 中可以使用 updateStateByKey 函数来实现有状态计算：
```java
public <S> JavaPairDStream<K, S> updateStateByKey(final Function2<List<V>, Optional<S>, Optional<S>> updateFunc) {
    ...
}
```
updateStateByKey 函数仅定义在键值对 DStream 上，接收一个 Function2 函数来更新状态：
```java
Function2<List<V>, Optional<S>, Optional<S>>
```
该状态更新函数指定了如何使用旧状态和新值来更新状态，该函数接收三个参数：
- 一个是类型为 V 的 List 列表 `List<V>`，表示当前批次处理接收到的指定 Key 的所有值
- 一个是类型为 S 的可选状态 `Optional<S>`，表示需要计算的旧状态
- 一个是类型为 S 的状态 `Optional<S>`，表示计算并返回的新状态
```java
updateStateByKey(new Function2<List<Integer>, Optional<Long>, Optional<Long>>() {
    // List<Integer> 表示当前批次接收到的指定 Key 的所有值
    // Optional<Long> 表示存储类型为 Long 的状态
    @Override
    public Optional<Long> call(List<Integer> elements, Optional<Long> countState) throws Exception {
        LOG.info("当前批次元素: {}，当前状态值: {}", elements, countState.isPresent() ? countState.get() : null);
        Long count = 0L;
        if (countState.isPresent()) {
            count = countState.get();
        }
        for (Integer value : elements) {
            count += value;
        }
        return Optional.of(count);
    }
})
```
流处理开始后，状态更新函数就会在每个批次中调用，作用于 Executor 中的所有元素。有时可能会出现一个之前从未出现的 Key，此时更新函数的第二个参数即状态为空，所以使用的时候需要调用 isPresent 判断是否有值。

需要注意的是在每个批次处理中，Spark 会对所有现有的 Key 应用状态更新函数，即无论这些 Key 在批次处理中是否有新数据。这也是造成 updateStateByKey 函数性能差的一个原因，无论当前批次有没有出现该的 Key 的值，只要之前曾经出现过就会对这个 Key 应用状态更新函数。假设之前曾经出现过 4 个 Key，但当前批次没有任何元素，但是会输出类似如下的信息：
```java
15:02:20,087 INFO  com.spark.example.streaming.state.SocketUpdateStateWordCount [] - 当前批次元素: []，当前状态值: 101
15:02:20,087 INFO  com.spark.example.streaming.state.SocketUpdateStateWordCount [] - 当前批次元素: []，当前状态值: 78
15:02:20,088 INFO  com.spark.example.streaming.state.SocketUpdateStateWordCount [] - 当前批次元素: []，当前状态值: 34
15:02:20,088 INFO  com.spark.example.streaming.state.SocketUpdateStateWordCount [] - 当前批次元素: []，当前状态值: 98
```
这4条记录对应了之前曾经出现过的那 4 个 Key，从上面也可以看出当前批次元素为空。

使用 updateStateByKey 这类状态计算时，流的中间状态会保存在内部状态存储中。在每个批次间隔期间，会使用状态更新函数对来内部状态和流中新到的元素进行组合，从而生成一个包含当前状态计算结果的状态派生流。

## 2. Checkpoint

需要注意的是，使用 updateStateByKey 需要配置 Checkpoint 目录，否则会抛出如下异常：
```java
Exception in thread "main" java.lang.IllegalArgumentException: requirement failed: The checkpoint directory has not been set. Please set it by StreamingContext.checkpoint().
	at scala.Predef$.require(Predef.scala:224)
	at org.apache.spark.streaming.dstream.DStream.validateAtStart(DStream.scala:243)
	at org.apache.spark.streaming.dstream.DStream$$anonfun$validateAtStart$8.apply(DStream.scala:276)
	at org.apache.spark.streaming.dstream.DStream$$anonfun$validateAtStart$8.apply(DStream.scala:276)
...
	at org.apache.spark.deploy.SparkSubmit$.org$apache$spark$deploy$SparkSubmit$$runMain(SparkSubmit.scala:755)
	at org.apache.spark.deploy.SparkSubmit$.doRunMain$1(SparkSubmit.scala:180)
	at org.apache.spark.deploy.SparkSubmit$.submit(SparkSubmit.scala:205)
	at org.apache.spark.deploy.SparkSubmit$.main(SparkSubmit.scala:119)
	at org.apache.spark.deploy.SparkSubmit.main(SparkSubmit.scala)
```
如下所示指定一个 Checkpoint 目录：
```java
ssc.checkpoint("hdfs://localhost:9000/spark/checkpoint");
```
之所以需要开启 Checkpoint 的原因是 updateStateByKey 创建的 StateStream 中包含的 RDD 会在内部依赖于之前的 RDD，那么如果要对每个批次间隔上的求和运算进行重建的话，需要重放整个流。这对于容错来说很难接受。因为需要保存所有接收到的数据，以便在任意的时间点重建状态。因此实际上我们并不会保存所有的数据，而是将中间结果保存在硬盘上。一旦流上的某个 Executor 崩溃了，则可以从这个中间状态中恢复。

## 3. 局限性

使用 updateStateByKey 可以在 Spark Streaming 中实现有状态的应用。但是有如下两个问题：
- 性能
  - 第一个问题与性能有关：程序启动后，updateStateByKey 函数会运行在所有出现的 Key 上。这边是问题的根由，假设有一个稀疏的数据集，在 Key 的分布上有一个长尾，那么便会导致数据在内存中无限增长。例如，计算用户登录次数，在程序启动时观察到了某个用户登录了网站，但是在此之后该用户再也没有出现了，这种用户一直保存在状态中。
- 内存占用
  - 第二个问题在于状态不能无限增长，因而需要自己管理内存，即通过编程的方式确定为特定元素维护的状态是否有意义，这无疑很复杂，需要手工管理内存。

## 4. 示例

让我们用一个例子来说明这一点。假设您希望维护文本数据流中看到的每个单词的运行计数。状态更新函数接收的三个参数如下所示：
- 一个是类型为 Integer 的 List 列表 `List<Integer>`，表示当前批次处理接收到的单词计数
- 一个是类型为 Long 的可选状态 `Optional<Long>`，表示之前单词计数的旧状态
- 一个是类型为 Long 的状态 `Optional<Long>`，表示状态更新函数需要计算并返回的最新单词计数的新状态
```java
updateStateByKey(new Function2<List<Integer>, Optional<Long>, Optional<Long>>() {
    // List<Integer> 表示当前批次接收到的指定 Key 的所有值
    // Optional<Long> 表示存储类型为 Long 的状态
    @Override
    public Optional<Long> call(List<Integer> elements, Optional<Long> countState) throws Exception {
        LOG.info("当前批次元素: {}，当前状态值: {}", elements, countState.isPresent() ? countState.get() : null);
        Long count = 0L;
        if (countState.isPresent()) {
            count = countState.get();
        }
        for (Integer value : elements) {
            count += value;
        }
        return Optional.of(count);
    }
})
```
完整示例如下所示：
```java
public class SocketUpdateStateWordCount {
    private static final Logger LOG = LoggerFactory.getLogger(SocketUpdateStateWordCount.class);
    private static String hostName = "localhost";
    private static int port = 9100;

    public static void main(String[] args) throws InterruptedException {
        SparkConf conf = new SparkConf().setAppName("SocketUpdateStateWordCount").setMaster("local[2]");
        JavaSparkContext sparkContext = new JavaSparkContext(conf);

        JavaStreamingContext ssc = new JavaStreamingContext(sparkContext, Durations.seconds(10));

        // 通过 updateStateByKey 实现有状态的应用必须实现 Checkpoint
        ssc.checkpoint("hdfs://localhost:9000/spark/checkpoint");

        // 以端口 9100 作为输入源创建 DStream
        JavaReceiverInputDStream<String> lines = ssc.socketTextStream(hostName, port);

        // 统计每个单词出现的次数
        JavaPairDStream<String, Long> wordCounts = lines.flatMap(new FlatMapFunction<String, String>() {
            @Override
            public Iterator<String> call(String x) {
                return Arrays.asList(x.split("\\s+")).iterator();
            }
        }).mapToPair(new PairFunction<String, String, Integer>() {
            @Override
            public Tuple2<String, Integer> call(String word) {
                return new Tuple2<>(word, 1);
            }
        }).updateStateByKey(new Function2<List<Integer>, Optional<Long>, Optional<Long>>() {
            // List<Integer> 表示当前批次接收到的指定 Key 的所有值
            // Optional<Long> 表示存储类型为 Long 的状态
            @Override
            public Optional<Long> call(List<Integer> elements, Optional<Long> countState) throws Exception {
                LOG.info("当前批次元素: {}，当前状态值: {}", elements, countState.isPresent() ? countState.get() : null);
                Long count = 0L;
                if (countState.isPresent()) {
                    count = countState.get();
                }
                for (Integer value : elements) {
                    count += value;
                }
                return Optional.of(count);
            }
        });

        // 将此 DStream 中生成的每个RDD的前10个元素打印到控制台
        wordCounts.print();

        // 启动计算
        ssc.start();
        // 等待流计算完成，来防止应用退出
        ssc.awaitTermination();
    }
}
```
> 完整示例请查阅:[SocketUpdateStateWordCount](https://github.com/sjf0115/data-example/blob/master/spark-example-3.1/src/main/java/com/spark/example/streaming/state/SocketUpdateStateWordCount.java)
