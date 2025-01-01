## 3. Window 操作

`Spark Streaming` 还提供了窗口计算，允许你在数据的滑动窗口上应用转换操作．下图说明了这个滑动窗口：

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
reduceByWindow(reduceFunc, windowDuration, slideInterval)|基于数据流在一个滑动窗口内的元素，用func做聚合，返回一个单元素数据流。func必须满足结合律，以便支持并行计算。
reduceByKeyAndWindow(func, windowLength, slideInterval, [numTasks])|基于(K, V)键值对DStream，将一个滑动窗口内的数据进行聚合，返回一个新的包含(K,V)键值对的DStream，其中每个value都是各个key经过func聚合后的结果。注意：如果不指定numTasks，其值将使用Spark的默认并行任务数（本地模式下为2，集群模式下由 spark.default.parallelism决定）。当然，你也可以通过numTasks来指定任务个数。
reduceByKeyAndWindow(func, invFunc, windowLength, slideInterval, [numTasks])|和前面的reduceByKeyAndWindow() 类似，只是这个版本会用之前滑动窗口计算结果，递增地计算每个窗口的归约结果。当新的数据进入窗口时，这些values会被输入func做归约计算，而这些数据离开窗口时，对应的这些values又会被输入 invFunc 做”反归约”计算。举个简单的例子，就是把新进入窗口数据中各个单词个数“增加”到各个单词统计结果上，同时把离开窗口数据中各个单词的统计个数从相应的统计结果中“减掉”。不过，你的自己定义好”反归约”函数，即：该算子不仅有归约函数（见参数func），还得有一个对应的”反归约”函数（见参数中的 invFunc）。和前面的reduceByKeyAndWindow() 类似，该算子也有一个可选参数numTasks来指定并行任务数。注意，这个算子需要配置好检查点（checkpointing）才能用。
countByValueAndWindow(windowLength, slideInterval, [numTasks])|基于包含(K, V)键值对的DStream，返回新的包含(K, Long)键值对的DStream。其中的Long value都是滑动窗口内key出现次数的计数。和前面的reduceByKeyAndWindow() 类似，该算子也有一个可选参数numTasks来指定并行任务数。

## 1. window

window(windowLength, slideInterval) | 将源DStream窗口化，并返回转化后的DStream

## 2. reduceByWindow

`reduceByWindow` 函数接收一个 reduce 函数 `reduceFunc`、窗口大小 `windowDuration` 以及一个滑动间隔 `slideDuration`：
```java
def reduceByWindow(
    reduceFunc: JFunction2[T, T, T],
    windowDuration: Duration,
    slideDuration: Duration
  ): JavaDStream[T] = {
  dstream.reduceByWindow(reduceFunc, windowDuration, slideDuration)
}
```
这里的 `reduceFunc` 函数将两个原始的 DStream 合并成一个新的 DStream，并且类型一致。对数据流中属于一个窗口内的元素用 `reduceFunc` 聚合，返回一个单元素数据流。



## 3. reduceByKeyAndWindow

reduceByKeyAndWindow(func, windowLength, slideInterval, [numTasks])|基于(K, V)键值对DStream，将一个滑动窗口内的数据进行聚合，返回一个新的包含(K,V)键值对的DStream，其中每个value都是各个key经过func聚合后的结果。注意：如果不指定numTasks，其值将使用Spark的默认并行任务数（本地模式下为2，集群模式下由 spark.default.parallelism决定）。当然，你也可以通过numTasks来指定任务个数。

## 4. countByWindow

countByWindow(windowLength, slideInterval) | 返回数据流在一个滑动窗口内的元素个数


## 5. countByValueAndWindow
