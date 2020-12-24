
与RDD类似，转换操作允许修改来自输入DStream的数据。DStreams支持很多在常规Spark RDD上可用的转换操作。 一些常见的如下：

#### 1. 常见转换操作

转换操作|描述
---|---
map(func)|对DStream中的每个元素应用给定函数，返回各个元素输出的元素组成的DStream
flatMap(func)|对DStream中的每个元素应用给定函数，返回各个元素输出的迭代器组成的DStream
filter(func)|返回由给定DStream中通过筛选的元素组成的DStream
union(otherStream)|返回一个新的DStream，它包含源DStream和otherDStream中元素的并集
count()|通过计算源DStream的每个RDD中的元素数量，返回只包含一个RDD的新DStream
reduceByKey(func, [numTasks])|将每个批次中键相同的记录归约
groupByKey()|将每个批次中的记录根据键分组


==备注==

尽管这些函数看起来好像作用在整个流上一样，但是事实上每个DStream在内部是由许多RDD(批次)组成的，且无状态转化操作是分别应用到每个RDD上的．例如reduceByKey会归约每个时间区间中的数据，但不会归约不同区间之间的数据．


#### 2. UpdateStateByKey 操作

`updateStateByKey`操作允许你在使用新信息持续更新时可以保持任意状态。有时，我们需要在DStream中跨批次维护状态(例如，跟踪用户访问网站的会话)．针对这种情况，`updateStateByKey`为我们提供了对一个状态变量的访问，用于键值对形式的DStream．要使用`updateStateByKey`，你将不得不做两个步骤：

- 定义状态 - 状态可以是任意数据类型。
- 定义状态更新函数 - 使用指定函数会告诉你如何使用以前的状态以及来自输入流的新值来更新状态。

在每个批处理中，Spark将对所有现有keys应用状态更新函数，无论它们是否在批次中有新数据。 如果update函数返回None，则键值对将被消除( If the update function returns None then the key-value pair will be eliminated.)。

我们来举例说明一下。 假设你想统计文本数据流中每个单词的出现次数。这里，单词出现次数就是状态，它是一个整数。 我们将更新函数定义为：

Java版:
```
Function2<List<Integer>, Optional<Integer>, Optional<Integer>> updateFunction =
  new Function2<List<Integer>, Optional<Integer>, Optional<Integer>>() {
    @Override public Optional<Integer> call(List<Integer> values, Optional<Integer> state) {
      Integer newSum = ...  // add the new values with the previous running count to get the new count
      return Optional.of(newSum);
    }
  };
```
Scala:
```
def updateFunction(newValues: Seq[Int], runningCount: Option[Int]): Option[Int] = {
    val newCount = ...  // add the new values with the previous running count to get the new count
    Some(newCount)
}
```
Python:
```
def updateFunction(newValues, runningCount):
    if runningCount is None:
        runningCount = 0
    return sum(newValues, runningCount)  # add the new values with the previous running count to get the new count
```

这可以应用于包含单词的DStream上（例如，在前面的[示例]()中包含(word，1)键值对的DStream）。

Java版：
```
JavaPairDStream<String, Integer> runningCounts = pairs.updateStateByKey(updateFunction);
```
Scala版：
```
val runningCounts = pairs.updateStateByKey[Int](updateFunction _)
```
Python版：
```
runningCounts = pairs.updateStateByKey(updateFunction)
```

将为每个单词调用更新函数，其中`newValues`具有1的序列（来自（word，1）键值对）和`runningCount`表示之前的计数。 有关完整的Java代码，请查看示例[JavaStatefulNetworkWordCount.java](https://github.com/apache/spark/blob/v2.1.1/examples/src/main/java/org/apache/spark/examples/streaming/JavaStatefulNetworkWordCount.java)。

请注意，使用updateStateByKey需要配置检查点目录，这在[检查点部分](http://spark.apache.org/docs/latest/streaming-programming-guide.html#checkpointing)将详细讨论。

#### 2.2 Transform 操作

`Transform`操作符，可以让你直接操作其内部的RDD．`Transform`操作（以及其变体如`transformWith`）允许你对DStream提供任意一个RDD到RDD函数． 这个函数会在数据流中的每个批次中被调用，生成一个新的流．它可使用任何未在DStream API中公开的RDD操作。例如，将数据流中每个批次数据与其他数据集进行聚合的功能不会直接在DStream API中开放。 但是，你可以轻松地使用`Transform`来做到这一点。 这使得非常强大的可能性。 例如，可以通过将输入数据流与预先计算的垃圾邮件信息(也可能是由Spark生成)进行聚合进行实时数据清理，然后基于它进行过滤。

Java版：
```
import org.apache.spark.streaming.api.java.*;
// RDD containing spam information
final JavaPairRDD<String, Double> spamInfoRDD = jssc.sparkContext().newAPIHadoopRDD(...);

JavaPairDStream<String, Integer> cleanedDStream = wordCounts.transform(
  new Function<JavaPairRDD<String, Integer>, JavaPairRDD<String, Integer>>() {
    @Override public JavaPairRDD<String, Integer> call(JavaPairRDD<String, Integer> rdd) throws Exception {
      rdd.join(spamInfoRDD).filter(...); // join data stream with spam information to do data cleaning
      ...
    }
  });
```
Scala版:
```
val spamInfoRDD = ssc.sparkContext.newAPIHadoopRDD(...) // RDD containing spam information

val cleanedDStream = wordCounts.transform { rdd =>
  rdd.join(spamInfoRDD).filter(...) // join data stream with spam information to do data cleaning
  ...
}
```
Python版：
```
spamInfoRDD = sc.pickleFile(...)  # RDD containing spam information

# join data stream with spam information to do data cleaning
cleanedDStream = wordCounts.transform(lambda rdd: rdd.join(spamInfoRDD).filter(...))
```
请注意，提供的函数在每个批次间隔被调用(the supplied function gets called in every batch interval)(其调用时间间隔与批次间隔是相同的)。这允许你基于时间改变对RDD操作，如在不同批次调用不同的RDD操作，设置不同的分区数，广播变量等．


#### 2.3 Window 操作

`Spark Streaming`还提供了窗口计算，允许你在数据的滑动窗口上应用转换操作．下图说明了这个滑动窗口：

![image](http://spark.apache.org/docs/latest/img/streaming-dstream-window.png)

如图所示，每当窗口在源DStream上滑动时，落在窗口内的源RDD被组合起来并进行操作以产生窗口DStream的RDD．在上面例子中，操作应用于最近3个时间单位的数据，并以2个时间单位进行滑动(滑动步长)．这表明任何窗口操作都需要指定两个参数:
- 窗口长度 - 窗口的持续时间（上图中窗口长度为3）。
- 滑动步长 - 执行窗口操作的间隔（上图中滑动步长为2）。

这两个参数必须是源DStream的批次间隔的倍数（上图中批次间隔为1）。

我们以一个例子来说明窗口操作。 我们扩展之前的例子，每隔10秒统计一下前30秒内的单词计数。为此，我们必须在最近30秒的数据中对(word，1)键值对的DStream应用`reduceByKey`操作。 这里使用`reduceByKeyAndWindow`操作完成。

Java版：
```
// Reduce function adding two integers, defined separately for clarity
Function2<Integer, Integer, Integer> reduceFunc = new Function2<Integer, Integer, Integer>() {
  @Override public Integer call(Integer i1, Integer i2) {
    return i1 + i2;
  }
};

// Reduce last 30 seconds of data, every 10 seconds
JavaPairDStream<String, Integer> windowedWordCounts = pairs.reduceByKeyAndWindow(reduceFunc, Durations.seconds(30), Durations.seconds(10));
```
Scala版：
```
// Reduce last 30 seconds of data, every 10 seconds
val windowedWordCounts = pairs.reduceByKeyAndWindow((a:Int,b:Int) => (a + b), Seconds(30), Seconds(10))
```
Python版本：
```
# Reduce last 30 seconds of data, every 10 seconds
windowedWordCounts = pairs.reduceByKeyAndWindow(lambda x, y: x + y, lambda x, y: x - y, 30, 10)
```
一些常见的窗口操作如下。 所有这些操作都需要上述两个参数 - `windowLength`和`slideInterval`。


函数 | 描述
---|---
window(windowLength, slideInterval) | 将源DStream窗口化，并返回转化后的DStream
countByWindow(windowLength, slideInterval) | 返回数据流在一个滑动窗口内的元素个数
reduceByWindow(func, windowLength, slideInterval)|基于数据流在一个滑动窗口内的元素，用func做聚合，返回一个单元素数据流。func必须满足结合律，以便支持并行计算。
reduceByKeyAndWindow(func, windowLength, slideInterval, [numTasks])|基于(K, V)键值对DStream，将一个滑动窗口内的数据进行聚合，返回一个新的包含(K,V)键值对的DStream，其中每个value都是各个key经过func聚合后的结果。注意：如果不指定numTasks，其值将使用Spark的默认并行任务数（本地模式下为2，集群模式下由 spark.default.parallelism决定）。当然，你也可以通过numTasks来指定任务个数。
reduceByKeyAndWindow(func, invFunc, windowLength, slideInterval, [numTasks])|和前面的reduceByKeyAndWindow() 类似，只是这个版本会用之前滑动窗口计算结果，递增地计算每个窗口的归约结果。当新的数据进入窗口时，这些values会被输入func做归约计算，而这些数据离开窗口时，对应的这些values又会被输入 invFunc 做”反归约”计算。举个简单的例子，就是把新进入窗口数据中各个单词个数“增加”到各个单词统计结果上，同时把离开窗口数据中各个单词的统计个数从相应的统计结果中“减掉”。不过，你的自己定义好”反归约”函数，即：该算子不仅有归约函数（见参数func），还得有一个对应的”反归约”函数（见参数中的 invFunc）。和前面的reduceByKeyAndWindow() 类似，该算子也有一个可选参数numTasks来指定并行任务数。注意，这个算子需要配置好检查点（checkpointing）才能用。
countByValueAndWindow(windowLength, slideInterval, [numTasks])|基于包含(K, V)键值对的DStream，返回新的包含(K, Long)键值对的DStream。其中的Long value都是滑动窗口内key出现次数的计数。和前面的reduceByKeyAndWindow() 类似，该算子也有一个可选参数numTasks来指定并行任务数。

#### 2.4. Join 操作

最后，强调的是，你可以轻松地在`Spark Streaming`中执行不同类型的连接。

##### 2.4.1 Stream-stream joins

流可以非常容易地与其他流Join。

Java版：
```
JavaPairDStream<String, String> stream1 = ...
JavaPairDStream<String, String> stream2 = ...
JavaPairDStream<String, Tuple2<String, String>> joinedStream = stream1.join(stream2);
```
Scala版：
```
val stream1: DStream[String, String] = ...
val stream2: DStream[String, String] = ...
val joinedStream = stream1.join(stream2)
```
Python版：
```
stream1 = ...
stream2 = ...
joinedStream = stream1.join(stream2)
```
这里，在每个批间隔中，由`stream1`生成的RDD将与`stream2`生成的RDD进行Join。你也可以做`leftOuterJoin`，`rightOuterJoin`，`fullOuterJoin`。 此外，在流的窗口上进行Join通常是非常有用的。 这也很简单。

Java版：
```
JavaPairDStream<String, String> windowedStream1 = stream1.window(Durations.seconds(20));
JavaPairDStream<String, String> windowedStream2 = stream2.window(Durations.minutes(1));
JavaPairDStream<String, Tuple2<String, String>> joinedStream = windowedStream1.join(windowedStream2);
```
Scala版：
```
val windowedStream1 = stream1.window(Seconds(20))
val windowedStream2 = stream2.window(Minutes(1))
val joinedStream = windowedStream1.join(windowedStream2)
```
Python版：
```
windowedStream1 = stream1.window(20)
windowedStream2 = stream2.window(60)
joinedStream = windowedStream1.join(windowedStream2)
```
##### 2.4.2 Stream-dataset joins

这在前面执行DStream.transform操作时已经展示过了. 这是另一个窗口流与数据集进行连接的例子．

Java版：
```
JavaPairRDD<String, String> dataset = ...
JavaPairDStream<String, String> windowedStream = stream.window(Durations.seconds(20));
JavaPairDStream<String, String> joinedStream = windowedStream.transform(
  new Function<JavaRDD<Tuple2<String, String>>, JavaRDD<Tuple2<String, String>>>() {
    @Override
    public JavaRDD<Tuple2<String, String>> call(JavaRDD<Tuple2<String, String>> rdd) {
      return rdd.join(dataset);
    }
  }
);
```
Scala版：
```
val dataset: RDD[String, String] = ...
val windowedStream = stream.window(Seconds(20))...
val joinedStream = windowedStream.transform { rdd => rdd.join(dataset) }
```
Python版：
```
dataset = ... # some RDD
windowedStream = stream.window(20)
joinedStream = windowedStream.transform(lambda rdd: rdd.join(dataset))
```

实际上，在上面代码里，你可以动态地改变进行连接的数据集（dataset）.传给`tranform`操作的函数会在每个批次重新求值，所以每次该函数都会使用当前的数据集，`dataset`指向的数据集．

DStream转换操作完整列表可在API文档中找到。 对于Scala API，请参阅[DStream](http://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.streaming.dstream.DStream)和[PairDStreamFunction](http://spark.apache.org/docs/latest/api/scala/index.html#org.apache.spark.streaming.dstream.PairDStreamFunctions)。 对于Java API，请参阅[JavaDStream](http://spark.apache.org/docs/latest/api/java/index.html?org/apache/spark/streaming/api/java/JavaDStream.html)和[JavaPairDStream](http://spark.apache.org/docs/latest/api/java/index.html?org/apache/spark/streaming/api/java/JavaPairDStream.html)。 对于Python API，请参阅[DStream](http://spark.apache.org/docs/latest/api/python/pyspark.streaming.html#pyspark.streaming.DStream)。

