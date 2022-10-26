
## 1. 简介

updateStateByKey 操作可以让你维护任意状态，并可以不断更新。要使用，必须执行如下两个步骤：
- 定义状态：可以是任意数据类型的状态。
- 定义状态更新函数：通过这个函数指定如何使用旧状态和新值来更新状态。

updateStateByKey 操作仅定义在键值对 DStream 上。在每个批次处理中，Spark 会对所有现有的 Key 应用状态更新函数，无论这些 Key 在批次处理中是否有新数据。如果更新函数返回 None，则键值会被取消。

### 1.1 状态更新函数

状态更新函数接收两个参数，第一个是类型 V 的集合，表示当前批次处理接收到的指定 Key 的所有值；第二个参数是一个类型 S 的 Optional 的状态。状态更新函数会根据接收的参数计算并返回一个类型 S 的 Optional 的新状态：
```
// 形式
JavaPairDStream<K, S> updateStateByKey(Function2<List<V>, Optional<S>, Optional<S>> updateFunc)
// 示例
new Function2<List<Integer>, Optional<Long>, Optional<Long>>() {
    @Override
    public Optional<Long> call(List<Integer> elements, Optional<Long> countState) throws Exception {
        Long count = 0L;
        if (countState.isPresent()) {
            count = countState.get();
        }
        for (Integer value : elements) {
            count += value;
        }
        return Optional.of(count);
    }
}
```
流处理开始后，状态更新函数就会在每个批次中调用，作用于 Executor 中的所有元素。有时可能会出现一个之前从未出现的 Key，此时更新函数的第二个参数即状态为 None，所以使用的使用需要调用 isPresent 判断是否有值。最后状态更新函数会根据用户的决定来是否返回一个值，这也解释了函数的返回类型是 Optional 的原因。

### 1.2 状态

使用 updateStateByKey 这类状态计算时，流的中间状态会保存在内部状态存储中。在每个批次间隔期间，会使用状态更新函数对来内部状态和流中新到的元素进行组合，从而生成一个包含当前状态计算结果的状态派生流。如下图所示：

![]()

### 1.3 Checkpoint

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

## 2. 局限性

使用 updateStateByKey 可以在 Spark Streaming 中实现有状态的应用。但是有如下两个问题，下面我们一起仔细看看。

### 2.1 性能

第一个问题与性能有关：程序启动后，updateStateByKey 函数会运行在所有出现的 Key 上。这边是问题的根由，假设有一个稀疏的数据集，那么在 Key 的分布上可能会有一个长尾，那么便会导致数据在内存中无限增长。例如，计算用户登录次数，在程序启动时观察到了某个用户登录了网站，但是在此之后该用户再也没有出现了，这种用户一直保存在状态中。

### 2.2 内存占用

第二个问题在于状态不能无限增长，因而开发需要自己管理内存，即通过编程的方式确定为特定元素维护的状态是否有意义，这无疑很复杂，需要手工管理内存。

## 3. 示例

让我们用一个例子来说明这一点。假设您希望维护文本数据流中看到的每个单词的运行计数。在这里，运行计数是状态，它是一个整数。我们将更新函数定义为:



spark-submit --class com.spark.example.streaming.state.SocketUpdateStateWordCount /Users/wy/study/code/data-example/spark-example-3.1/target/spark-example-3.1-1.0.jar
