Flink中的`DataStream`程序是实现数据流转换(例如，过滤，更新状态，定义窗口，聚合)的常规程序。数据流最初是从各种来源(例如，消息队列，套接字流，文件)创建的。通过接收器返回结果，例如可以将数据写入文件或标准输出(例如命令行终端)。`Flink`程序可以在不同上下文中运行，独立模式或嵌入其他程序模式。可以在本地`JVM`上运行，也可以在多机器集群上运行。

为了创建第一个`Flink DataStream`程序，我们建议你首先从[剖析Flink程序](http://smartsi.club/2018/01/04/Flink/[Flink]Flink%20Flink%E7%A8%8B%E5%BA%8F%E5%89%96%E6%9E%90/)开始，然后逐步地增加你的 转换操作。而剩余的章节主要作为额外操作(operations)和高级特性的一个参考。

### 1. Example程序

下面这段程序是一个完整的，可运行的，基于流和窗口的word count应用程序。从web socket中以5秒为窗口统计单词数量。你可以复制&粘贴这段代码，然后在本地跑一跑。

Java版本:
```java
import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.util.Collector;

public class WindowWordCount {

    public static void main(String[] args) throws Exception {

        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        DataStream<Tuple2<String, Integer>> dataStream = env
                .socketTextStream("localhost", 9999)
                .flatMap(new Splitter())
                .keyBy(0)
                .timeWindow(Time.seconds(5))
                .sum(1);

        dataStream.print();

        env.execute("Window WordCount");
    }

    public static class Splitter implements FlatMapFunction<String, Tuple2<String, Integer>> {
        @Override
        public void flatMap(String sentence, Collector<Tuple2<String, Integer>> out) throws Exception {
            for (String word: sentence.split(" ")) {
                out.collect(new Tuple2<String, Integer>(word, 1));
            }
        }
    }
}
```

scala版本:
```
import org.apache.flink.streaming.api.scala._
import org.apache.flink.streaming.api.windowing.time.Time

object WindowWordCount {
  def main(args: Array[String]) {

    val env = StreamExecutionEnvironment.getExecutionEnvironment
    val text = env.socketTextStream("localhost", 9999)

    val counts = text.flatMap { _.toLowerCase.split("\\W+") filter { _.nonEmpty } }
      .map { (_, 1) }
      .keyBy(0)
      .timeWindow(Time.seconds(5))
      .sum(1)

    counts.print

    env.execute("Window Stream WordCount")
  }
}
```

要在运行样例程序，首先从终端启动`netcat`作为输入流:
```
nc -lk 9999
```
只是输入一些单词，敲回车换行输入一些新的单词。这些将作为`word count`程序的输入。如果要使得某个单词的计数大于1，要在5秒钟内重复输入相同的单词(如果5秒钟之内来不及输入相同的单词，请把窗口大小从5秒调大)。

### 2. DataStream Transformations

数据的转换操作可以将一个或多个DataStream转换为一个新的DataStream。程序可以将多种转换操作组合成复杂的拓扑结构。

本节对所有可用转换操作进行详细说明。

#### 2.1 Map DataStream → DataStream

读入一个元素，返回转换后的对应元素。下面演示了一个把输入流中的数值翻倍的map函数：

Java版本:
```java
DataStream<Integer> dataStream = dataStream.map(new MapFunction<Integer, Integer>() {
    @Override
    public Integer map(Integer value) throws Exception {
        return 2 * value;
    }
});
```
Scala版本:
```
dataStream.map { x => x * 2 }
```

#### 2.2 FlatMap DataStream → DataStream

读入一个元素，返回转换后的0个、1个或者多个元素。下面演示了一个将句子切分成单词的flatmap函数:

Java版本:
```java
dataStream.flatMap(new FlatMapFunction<String, String>() {
    @Override
    public void flatMap(String value, Collector<String> out)
        throws Exception {
        for(String word: value.split(" ")){
            out.collect(word);
        }
    }
});
```
Scala版本:
```
dataStream.flatMap { str => str.split(" ") }
```

#### 2.3 Filter DataStream → DataStream

对每个元素执行boolean函数，并保留返回true的元素。下面演示了一个过滤掉零值的filter函数:

Java版本:
```java
dataStream.filter(new FilterFunction<Integer>() {
    @Override
    public boolean filter(Integer value) throws Exception {
        return value != 0;
    }
});
```
Scala版本:
```
dataStream.filter { _ != 0 }
```

#### 2.4 KeyBy DataStream → KeyedStream

逻辑上将流分区为不相交的一些分区，每个分区包含相同key的元素。在内部通过hash分区来实现。关于如何指定分区的keys请参阅[keys](https://ci.apache.org/projects/flink/flink-docs-release-1.3/dev/api_concepts.html#specifying-keys)。该转换操作返回一个KeyedDataStream。

Java版本:
```java
dataStream.keyBy("someKey") // Key by field "someKey"
dataStream.keyBy(0) // Key by the first element of a Tuple
```

Scala版本:
```
dataStream.keyBy("someKey") // Key by field "someKey"
dataStream.keyBy(0) // Key by the first element of a Tuple
```

注意:
```
以下类型不能作为key:
(1) POJO类型，并且依赖于Object.hashCode()的实现，但是未覆写hashCode()
(2) 任意类型的数组
```

#### 2.5 Reduce KeyedStream → DataStream

在一个KeyedStream上不断进行reduce操作。将当前元素与上一个reduce后的值进行合并，再返回新合并的值。

一个构造局部求和流的reduce函数:

Java版本:
```java
keyedStream.reduce(new ReduceFunction<Integer>() {
    @Override
    public Integer reduce(Integer value1, Integer value2)
    throws Exception {
        return value1 + value2;
    }
});
```
Scala版本:
```
keyedStream.reduce { _ + _ }
```

#### 2.6 Fold KeyedStream → DataStream

在一个KeyedStream上基于初始值不断进行变换操作，将当前值与上一个变换后的值进行变换，再返回新变换的值。

在序列（1,2,3,4,5）上应用如下的fold function，返回的序列依次是“start-1”，“start-1-2”，“start-1-2-3”, ...：

Java版本:
```java
DataStream<String> result =
  keyedStream.fold("start", new FoldFunction<Integer, String>() {
    @Override
    public String fold(String current, Integer value) {
        return current + "-" + value;
    }
  });
```

#### 2.7 Aggregations KeyedStream → DataStream



#### 2.8 Window KeyedStream → WindowedStream

#### 2.9 WindowAll DataStream → AllWindowedStream

#### 2.10 Window Apply WindowedStream → DataStream AllWindowedStream → DataStream

#### 2.11 Window Reduce WindowedStream → DataStream

#### 2.12 Window Fold WindowedStream → DataStream

#### 2.13 Aggregations on windows WindowedStream → DataStream

#### 2.14 Union DataStream* → DataStream

#### 2.15 Window Join DataStream,DataStream → DataStream

#### 2.16 Window CoGroup DataStream,DataStream → DataStream

#### 2.17 Connect DataStream,DataStream → ConnectedStreams

#### 2.18 CoMap, CoFlatMap ConnectedStreams → DataStream

#### 2.19 Split DataStream → SplitStream

#### 2.20 Select SplitStream → DataStream

#### 2.21 Iterate DataStream → IterativeStream → DataStream

#### 2.22 Extract Timestamps DataStream → DataStream





原文:
