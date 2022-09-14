

既然一条流可以分开，自然多条流就可以合并。在实际应用中，我们经常会遇到来源不同
的多条流，需要将它们的数据进行联合处理。所以 Flink 中合流的操作会更加普遍，对应的
API 也更加丰富。

## 1. Union

最简单的合流操作就是将多条流合并在一起，在Flink中的算子为Union。Union操作要求所有合并的流的类型必须一致，合并之后的新流会包含流中的所有元素，数据类型不变。这种操作比较简单粗暴，就类似于高速路上的岔道，两个道路的车直接汇入主路一样。需要注意的是，Union操作的参数可以是多个DataStream，最后的结果也是DataStream。

最简单的流合并操作，就是直接将多条流合在一起，叫作流的“联合”（union）。联合操作要求必须流中的数据类型必须相同，合并之后的新流会包括所有流中的元素，


我们只要基于 DataStream 直接调用 union() 方法，传入其他 DataStream 作为参数，就可以实现流的合并，得到的依然是一个 DataStream：
```java

```
> union() 的参数可以是多个 DataStream，所以合并操作可以同时实现多条流的合并


同时还需要注意，在事件时间语义下，水位线是时间的进度标志，不同的流中的水位线进展快慢可能不一样，将它们合并在一起之后，对于合并之后的水位线也是以最小的为准，这样才可以保证所有流都不会再传来之前的数据。


还以要考虑水位线的本质含义，是“之前的所有数据已经到齐了”；所以对于合流之后的
水位线，也是要以最小的那个为准，这样才可以保证所有流都不会再传来之前的数据。换句话
说，多流合并时处理的时效性是以最慢的那个流为准的。我们自然可以想到，这与之前介绍的
并行任务水位线传递的规则是完全一致的；多条流的合并，某种意义上也可以看作是多个并行
任务向同一个下游任务汇合的过程。

```
flink,1663038000000 -- A 流 2022-09-13 11:00:00
flink,1663038005000 -- B 流 2022-09-13 11:00:05
flink,1663038010000 -- C 流 2022-09-13 11:00:10

flink,1663038015000 -- A 流 2022-09-13 11:00:15
flink,1663038020000 -- B 流 2022-09-13 11:00:20
flink,1663038025000 -- C 流 2022-09-13 11:00:25

```

```
15:42:24,958 Stream   [] - AStream word: flink, timestamp: 1663038000000, watermark: -9223372036854775808
15:42:25,050 Stream   [] - UnionStream word: flink, timestamp: 1663038000000, watermark: -9223372036854775808
(AStream,flink,1663038000000)
15:42:48,333 Stream   [] - BStream word: flink, timestamp: 1663038005000, watermark: -9223372036854775808
15:42:48,351 Stream   [] - UnionStream word: flink, timestamp: 1663038005000, watermark: -9223372036854775808
(BStream,flink,1663038005000)
15:43:08,141 Stream   [] - CStream word: flink, timestamp: 1663038010000, watermark: -9223372036854775808
15:43:08,148 Stream   [] - UnionStream word: flink, timestamp: 1663038010000, watermark: -9223372036854775808
(CStream,flink,1663038010000)
15:43:31,133 Stream   [] - AStream word: flink, timestamp: 1663038015000, watermark: 1663037994999
15:43:31,173 Stream   [] - UnionStream word: flink, timestamp: 1663038015000, watermark: 1663037994999
(AStream,flink,1663038015000)
15:44:18,462 Stream   [] - BStream word: flink, timestamp: 1663038020000, watermark: 1663037999999
15:44:18,518 Stream   [] - UnionStream word: flink, timestamp: 1663038020000, watermark: 1663037999999
(BStream,flink,1663038020000)
15:44:32,606 Stream   [] - CStream word: flink, timestamp: 1663038025000, watermark: 1663038004999
15:44:32,606 Stream   [] - UnionStream word: flink, timestamp: 1663038025000, watermark: 1663038004999
(CStream,flink,1663038025000)
```




## 2. Connect




https://blog.knoldus.com/flink-union-operator-on-multiple-streams/
https://zhuanlan.zhihu.com/p/463774251
