在实际应用中，我们经常会遇到来源不同的多条流，需要将它们的数据进行合并处理。所以 Flink 中合流的操作会更加普遍，对应的 API 也比较丰富。

## 1. Union

最简单合并流的方式就是使用 Union 算子将多条流合并在一起。Union 操作要求所有合并的流的类型必须一致，合并之后的新流会包含流中的所有元素，数据类型也不会改变。这种操作比较简单粗暴，就类似于高速路上的岔道，两个道路的车直接汇入主路一样。我们只要基于 DataStream 直接调用 union() 方法，传入其他 DataStream 作为参数，就可以实现流的合并，得到的依然是一个 DataStream：
```java
aStream.union(bStream, cStream, ...)
```
> union() 的参数可以是多个 DataStream，所以合并操作可以同时实现多条流的合并

同时还需要注意，在事件时间语义下，Watermark 是时间的进度标志，不同的流中的 Watermark 进展快慢可能不一样，将它们合并在一起之后，对于合并之后的 Watermark 也是以最小的为准，这样才可以保证所有流都不会再传来之前的数据。换句话说，多流合并时处理的时效性是以最慢的那个流为准的。如下代码实现了将两个输入流合并为一个流：
```java
// A 输入流
SingleOutputStreamOperator<Tuple3<String, String, Long>> aStream = env.socketTextStream("localhost", 9100, "\n")
        .assignTimestampsAndWatermarks(
                WatermarkStrategy.<String>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                        .withTimestampAssigner(new SerializableTimestampAssigner<String>() {
                            @Override
                            public long extractTimestamp(String element, long recordTimestamp) {
                                String[] params = element.split(",");
                                return Long.parseLong(params[1]);
                            }
                        })
        )
        // 添加 ProcessFunction 用于输出 A 流的 Watermark
        .process(new ProcessFunction<String, Tuple3<String, String, Long>>() {
            @Override
            public void processElement(String element, Context ctx, Collector<Tuple3<String, String, Long>> out) throws Exception {
                String[] params = element.split(",");
                String word = params[0];
                Long timestamp = Long.parseLong(params[1]);
                Long watermark = ctx.timerService().currentWatermark();
                LOG.info("AStream word: {}, timestamp: {}, watermark: {}", word, timestamp, watermark);
                out.collect(Tuple3.of("AStream", word, timestamp));
            }
        });

// B 输入流
SingleOutputStreamOperator<Tuple3<String, String, Long>> bStream = env.socketTextStream("localhost", 9101, "\n")
        .assignTimestampsAndWatermarks(
                WatermarkStrategy.<String>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                        .withTimestampAssigner(new SerializableTimestampAssigner<String>() {
                            @Override
                            public long extractTimestamp(String element, long recordTimestamp) {
                                String[] params = element.split(",");
                                return Long.parseLong(params[1]);
                            }
                        })
        )
        // 添加 ProcessFunction 用于输出 B 流的 Watermark
        .process(new ProcessFunction<String, Tuple3<String, String, Long>>() {
            @Override
            public void processElement(String element, Context ctx, Collector<Tuple3<String, String, Long>> out) throws Exception {
                String[] params = element.split(",");
                String word = params[0];
                Long timestamp = Long.parseLong(params[1]);
                Long watermark = ctx.timerService().currentWatermark();
                LOG.info("BStream word: {}, timestamp: {}, watermark: {}", word, timestamp, watermark);
                out.collect(Tuple3.of("BStream", word, timestamp));
            }
        });

// 合并流
DataStream<Tuple3<String, String, Long>> unionStream = aStream.union(bStream);
SingleOutputStreamOperator<Tuple3<String, String, Long>> processStream = unionStream.keyBy(new KeySelector<Tuple3<String,String,Long>, String>() {
    @Override
    public String getKey(Tuple3<String, String, Long> element) throws Exception {
        return element.f1;
    }
}).process(new KeyedProcessFunction<String, Tuple3<String, String, Long>, Tuple3<String, String, Long>>() {
    @Override
    public void processElement(Tuple3<String, String, Long> element, Context ctx, Collector<Tuple3<String, String, Long>> out) throws Exception {
        Long watermark = ctx.timerService().currentWatermark();
        LOG.info("UnionStream word: {}, timestamp: {}, watermark: {}", element.f1, element.f2, watermark);
        out.collect(element);
    }
});
```

```
flink,1663038000000 -- A 流 2022-09-13 11:00:00
flink,1663038005000 -- B 流 2022-09-13 11:00:05
flink,1663038010000 -- A 流 2022-09-13 11:00:10
flink,1663038015000 -- A 流 2022-09-13 11:00:15
flink,1663038020000 -- B 流 2022-09-13 11:00:20
flink,1663038025000 -- B 流 2022-09-13 11:00:25

```
实际效果如下：
```
17:58:51,903 INFO  UnionStream   [] - AStream word: flink, timestamp: 1663038000000, watermark: -9223372036854775808
17:58:51,961 INFO  UnionStream   [] - UnionStream word: flink, timestamp: 1663038000000, watermark: -9223372036854775808
(AStream,flink,1663038000000)
17:58:59,933 INFO  UnionStream   [] - BStream word: flink, timestamp: 1663038005000, watermark: -9223372036854775808
17:58:59,995 INFO  UnionStream   [] - UnionStream word: flink, timestamp: 1663038005000, watermark: -9223372036854775808
(BStream,flink,1663038005000)
17:59:07,246 INFO  UnionStream   [] - AStream word: flink, timestamp: 1663038010000, watermark: 1663037994999
17:59:07,294 INFO  UnionStream   [] - UnionStream word: flink, timestamp: 1663038010000, watermark: 1663037994999
(AStream,flink,1663038010000)
17:59:13,228 INFO  UnionStream   [] - AStream word: flink, timestamp: 1663038015000, watermark: 1663038004999
17:59:13,251 INFO  UnionStream   [] - UnionStream word: flink, timestamp: 1663038015000, watermark: 1663037999999
(AStream,flink,1663038015000)
17:59:20,029 INFO  UnionStream   [] - BStream word: flink, timestamp: 1663038020000, watermark: 1663037999999
17:59:20,034 INFO  UnionStream   [] - UnionStream word: flink, timestamp: 1663038020000, watermark: 1663037999999
(BStream,flink,1663038020000)
17:59:25,406 INFO  UnionStream   [] - BStream word: flink, timestamp: 1663038025000, watermark: 1663038014999
17:59:25,486 INFO  UnionStream   [] - UnionStream word: flink, timestamp: 1663038025000, watermark: 1663038009999
(BStream,flink,1663038025000)
```

## 2. Connect

使用 Union 操作合并流虽然简单，不过受限于不同流中的数据类型必须一致，灵活性大打折扣，所以实际应用中比较少。除了 Union 操作，Flink 还提供了另外一种合并流-连接操作 Connect。顾名思义，这种操作就是直接把两条流像接线一样对接起来。

为了处理更加灵活，连接操作允许不同流的数据类型可以不同。但我们知道一个 DataStream 中的数据只能有唯一的类型，所以连接 Connect 得到的并不是 DataStream，而是一个 ConnectedStreams。ConnectedStreams 可以看成是两条流形式上的'统一'，内部仍然维护了两条流，彼此之间相互独立。ConnectedStreams 本质上是两个 DataStream 的封装：
```java
public class ConnectedStreams<IN1, IN2> {
    protected final StreamExecutionEnvironment environment;
    protected final DataStream<IN1> inputStream1;
    protected final DataStream<IN2> inputStream2;
    ...
}
```
要想加工处理得到新结果的 DataStream，还需要进一步定义一个'同处理'（co-process）转换操作，用来分别处理不同类型的数据从而得到统一的输出类型。所以整体上来，两条流的连接就像是'一国两制'，两条流可以保持各自的数据类型、处理方式也可以不同，不过最终还是会统一到同一个 DataStream 中，如下图所示：

![](1)

在代码实现上，需要分为两步：首先基于一条 DataStream 调用 connect() 方法，传入另外一条 DataStream 作为参数，将两条流连接起来，得到一个 ConnectedStreams；然后再调用同处理方法得到 DataStream。这里可以的调用的同处理方法有 map()/flatMap() 以及 process() 方法。如下代码实现了将 String 流和 Integer 流合并为一个 Long 数据流：
```java
// A输入流
DataStream<String> aStream = env.fromElements("1", "3", "5");
// B输入流
DataStream<Integer> bStream = env.fromElements(2, 4, 6);

// 使用 Connect 连接两个流
ConnectedStreams<String, Integer> connectStream = aStream.connect(bStream);
// 处理连接流
SingleOutputStreamOperator<Long> mapStream = connectStream
        .map(new CoMapFunction<String, Integer, Long>() {
            @Override
            public Long map1(String value) throws Exception {
                LOG.info("[A流] Value: {}", value);
                return Long.parseLong(value);
            }

            @Override
            public Long map2(Integer value) throws Exception {
                LOG.info("[B流] Value: {}", value);
                return value.longValue();
            }
        });
// 输出
mapStream.print();
```
实际效果如下：
```
17:25:17,887 INFO  com.flink.example.stream.function.merge.ConnectStreamExample [] - [B流] Value: 2
2
17:25:17,887 INFO  com.flink.example.stream.function.merge.ConnectStreamExample [] - [A流] Value: 1
1
17:25:17,887 INFO  com.flink.example.stream.function.merge.ConnectStreamExample [] - [B流] Value: 4
4
17:25:17,888 INFO  com.flink.example.stream.function.merge.ConnectStreamExample [] - [A流] Value: 3
3
17:25:17,888 INFO  com.flink.example.stream.function.merge.ConnectStreamExample [] - [B流] Value: 6
6
17:25:17,889 INFO  com.flink.example.stream.function.merge.ConnectStreamExample [] - [A流] Value: 5
5
```

上面的代码中，ConnectedStreams 有两个类型参数，分别表示内部包含的两条流各自的数据类型；由于需要'一国两制'，因此调用 map() 方法时传入的不再是 MapFunction，而是一个 CoMapFunction，表示分别对两条流中的数据执行 map 操作：
```java
public interface CoMapFunction<IN1, IN2, OUT> extends Function, Serializable {
    OUT map1(IN1 value) throws Exception;
    OUT map2(IN2 value) throws Exception;
}
```
这个接口有三个类型参数，依次表示第一条流、第二条流，以及合并流的数据类型。需要实现的方法也非常简单：map1() 就是对第一条流中数据的 map 操作，map2() 则是针对第二条流的操作。这里我们将一条 String 流和一条 Integer 流合并，转换成 Long 流输出。所以当遇到第一条流输入的字符串值时，调用 map1()，而遇到第二条流输入的整型数据时，调用 map2()，最终都转换为长整型输出。

使用 Connect 合并两条流，与使用 Union 操作相比，最大的优势就是可以处理不同类型流的合并，使用更灵活、应用更广泛。而缺点就是同时只能合并两个流，而 Union 可以同时进行多条流的合并。这也非常容易理解：Union 限制了类型必须一致，所以直接合并统一处理没有问题；而 Connec 是'一国两制'，实际上有两种不同数据类型的流，没办法合并后统一处理，后续处理的接口也只是定义了两个转换方法，如果扩展需要重新定义接口，所以不能'一国多制'。
