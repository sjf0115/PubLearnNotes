> Spark Streaming 版本：3.1.3

有时候可能需要依赖流中前几个批次中的元素来计算当前批次的结果。例如，计算流中所有元素的和，计算当前元素值与之前元素的差值。这种运算会在遍历整个流的期间不断更新计算状态。在 Spark Streaming 中提供了 [updateStateByKey](https://smartsi.blog.csdn.net/article/details/132778404) 和 MapWithState 函数来实现。本文主要介绍如何使用 MapWithState 函数实现有状态应用。

## 1. mapWithState

在 Spark Streaming 中可以使用 mapWithState 函数来实现有状态计算：
```java
public <StateType, MappedType> JavaMapWithStateDStream<K, V, StateType, MappedType> mapWithState(final StateSpec<K, V, StateType, MappedType> spec) {
    ...
}
```
mapWithState 函数要求定义一个 StateSpec 对象来描述状态计算的过程。该对象包含 4 个参数类型：
- Key 类型 KeyType
- 值类型 ValueType
- 状态类型 StateType
- 输出类型 MappedType
```java
public abstract class StateSpec<KeyType, ValueType, StateType, MappedType> implements Serializable {
    ...
}
```
需要注意的是该对象的核心是一个 function 函数，接收指定 Key 的新值并返回一个输出：
```java
public static <KeyType, ValueType, StateType, MappedType> StateSpec<KeyType, ValueType, StateType, MappedType> function(final Function3<KeyType, Optional<ValueType>, State<StateType>, MappedType> mappingFunction) {
    ...
}

public static <KeyType, ValueType, StateType, MappedType> StateSpec<KeyType, ValueType, StateType, MappedType> function(final Function4<Time, KeyType, Optional<ValueType>, State<StateType>, Optional<MappedType>> mappingFunction) {
    ...
}
```
function 函数可以接收一个 `Function4(Time, KeyType, Optional<ValueType>, State<StateType>, Optional<MappedType>)` 类型参数，但是如果不需要使用 mapWithState 中的批处理时间戳，可以使用 `Function3(KeyType, ValueType, StateType, MappedType> StateSpec<KeyType, ValueType, StateType, MappedType)`类型。

在 function 函数内可以实现对状态的管理，可以通过 `state.exists()` 和 `state.get()` 或者当成 Option 类型使用 `state.getOption()` 方法来查询状态，使用 `state.isTimingOut` 方法来检验是否超时，还可以使用 `state.remove()` 来移除状态，或者使用 `state.update(xxx)` 来更新状态。

此外 StateSpec 还提供了一个 initialState 函数，你可以使用 RDD 或者 JavaPairRDD 来初始化一个状态。如下是一个不使用批处理时间戳的示例：
```java
List<Tuple2<String, Integer>> elements = Arrays.asList(
        new Tuple2("hello", 1),
        new Tuple2<>("world", 1)
);
JavaPairRDD<String, Integer> elementRDD = ssc.sparkContext().parallelizePairs(elements);

mapWithState(
    StateSpec.function(new Function3<String, Optional<Integer>, State<Integer>, Tuple2<String, Integer>>() {
        @Override
        public Tuple2<String, Integer> call(String word, Optional<Integer> count, State<Integer> countState) throws Exception {
            int newCount = 0;
            if (countState.exists()) {
                newCount = countState.get();
            }
            newCount += count.orElse(0);
            countState.update(newCount);
            return new Tuple2<>(word, newCount);
        }
    }).initialState(elementRDD)
)
```
在上面示例中我们定义了一个 JavaPairRDD 通过 initialState 函数来初始化状态。

## 2. mapWithState 与 updateStateByKey 如何选择

与 [updateStateByKey](https://smartsi.blog.csdn.net/article/details/132778404) 相比，mapWithState 性能更好，使用更方便，是状态计算的首选。需要注意的是 mapWithState 通过超时来将数据从状态中移除，而不能让用户自行控制。因此如果你希望让状态一直处于最新的条件之下(例如，统计限制时间的会话内用户在网站的点击次数)，那么 mapWithState 会比较合适。而如果能够确保在较长时间内只需要维护较小的状态，则倾向于使用 [updateStateByKey](https://smartsi.blog.csdn.net/article/details/132778404)。

在这我们详细说明一下使用 mapWithState 的优势，首选 mapWithState 解决了 [updateStateByKey](https://smartsi.blog.csdn.net/article/details/132778404) 的两个缺点，可以实现对每个键进行更新并且可以设置默认的超时时间来限制计算产生的状态对象的大小。此外，mapWithState 还带来了如下好处：
- 更新操作只会发生在当前批次间隔上有新值的键上，注意观察打印出来的日志。
- 该函数具有自动超时的功能
- 该函数作用于单个元素上，而非元素的集合。可以通过 `Optional<Integer>` 参数知道，获取的是一个元素，而不是一批元素。
- 更新函数可以访问元素对应的键
- 更新状态是对状态对象上方法的直接调用，而非产生输出的隐式操作
- 开发者可以产生于状态管理无关的输出

## 3. 示例

我们用一个例子来说明如何通过 mapWithState 来实现一个有状态的应用。假设您希望维护文本数据流中看到的每个单词的运行计数。要通过 mapWithState 来实现一个有状态的应用，需要完成如下几个步骤：
- 设置 Checkpoint
- 定义状态描述符 StateSpec

mapWithState 与 [updateStateByKey](https://smartsi.blog.csdn.net/article/details/132778404) 一样，需要配置 Checkpoint 目录，否则会抛出 `requirement failed: The checkpoint directory has not been set` 异常：
```java
ssc.checkpoint("hdfs://localhost:9000/spark/checkpoint");
```
整个应用实现状态的核心就是定义状态描述符 StateSpec：
```java
StateSpec<String, Integer, Integer, Tuple2<String, Integer>> stateSpec = StateSpec.function(new Function3<String, Optional<Integer>, State<Integer>, Tuple2<String, Integer>>() {
    @Override
    public Tuple2<String, Integer> call(String word, Optional<Integer> count, State<Integer> countState) throws Exception {
        LOG.info("当前 Key: {}, 当前元素: {}, 当前状态: {}", word, count.get(), countState.exists() ? countState.get() : null);
        int newCount = 0;
        if (countState.exists()) {
            newCount = countState.get();
        }
        newCount += count.orElse(0);
        countState.update(newCount);
        return new Tuple2<>(word, newCount);
    }
}).initialState(elementRDD);
```
可以与 [updateStateByKey](https://smartsi.blog.csdn.net/article/details/132778404) 的状态更新函数对比一下。该函数获取到的是 `Optional<Integer>` 类型的单个单词的计数，即该函数只作用于单个元素上，而非像 [updateStateByKey](https://smartsi.blog.csdn.net/article/details/132778404) 一样作用到一批元素上。该函数还可以直接获取到当前 Key。此外，该函数还提供了一个状态对象 State，并提供了相应配套的状态操作方法。

上面种的 initialState 方法是用来初始化状态的，是一个可选操作：
```java
// 用来初始化 State
List<Tuple2<String, Integer>> elements = Arrays.asList(
        new Tuple2("hello", 1),
        new Tuple2<>("world", 1)
);
JavaPairRDD<String, Integer> elementRDD = ssc.sparkContext().parallelizePairs(elements);
```

完整示例如下所示：
```java
public class SocketMapStateWordCount {
    private static final Logger LOG = LoggerFactory.getLogger(SocketMapStateWordCount.class);
    private static String hostName = "localhost";
    private static int port = 9100;

    public static void main(String[] args) throws InterruptedException {
        SparkConf conf = new SparkConf().setAppName("SocketMapStateWordCount").setMaster("local[2]");
        JavaSparkContext sparkContext = new JavaSparkContext(conf);

        JavaStreamingContext ssc = new JavaStreamingContext(sparkContext, Durations.seconds(10));

        // 通过 MapWithState 实现有状态的应用必须实现 Checkpoint
        ssc.checkpoint("hdfs://localhost:9000/spark/checkpoint");

        // 以端口 9100 作为输入源创建 DStream
        JavaReceiverInputDStream<String> lines = ssc.socketTextStream(hostName, port);

        // 用来初始化 State
        List<Tuple2<String, Integer>> elements = Arrays.asList(
                new Tuple2("hello", 1),
                new Tuple2<>("world", 1)
        );
        JavaPairRDD<String, Integer> elementRDD = ssc.sparkContext().parallelizePairs(elements);

        // 状态描述符
        StateSpec<String, Integer, Integer, Tuple2<String, Integer>> stateSpec = StateSpec.function(new Function3<String, Optional<Integer>, State<Integer>, Tuple2<String, Integer>>() {
            @Override
            public Tuple2<String, Integer> call(String word, Optional<Integer> count, State<Integer> countState) throws Exception {
                LOG.info("当前 Key: {}, 当前元素: {}, 当前状态: {}", word, count.get(), countState.exists() ? countState.get() : null);
                int newCount = 0;
                if (countState.exists()) {
                    newCount = countState.get();
                }
                newCount += count.orElse(0);
                countState.update(newCount);
                return new Tuple2<>(word, newCount);
            }
        }).initialState(elementRDD);

        // 统计每个单词出现的次数
        JavaMapWithStateDStream<String, Integer, Integer, Tuple2<String, Integer>> wordCounts = lines.flatMap(new FlatMapFunction<String, String>() {
            @Override
            public Iterator<String> call(String x) {
                return Arrays.asList(x.split("\\s+")).iterator();
            }
        }).mapToPair(new PairFunction<String, String, Integer>() {
            @Override
            public Tuple2<String, Integer> call(String word) {
                return new Tuple2<>(word, 1);
            }
        }).mapWithState(stateSpec);

        // 输出
        wordCounts.print();

        // 启动计算
        ssc.start();
        // 等待流计算完成，来防止应用退出
        ssc.awaitTermination();
    }
}
```
> 完整示例请查阅:[SocketMapStateWordCount](https://github.com/sjf0115/data-example/blob/master/spark-example-3.1/src/main/java/com/spark/example/streaming/state/SocketMapStateWordCount.java)
