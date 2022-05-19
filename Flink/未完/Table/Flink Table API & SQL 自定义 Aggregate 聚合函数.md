用户自定义聚合函数(User Defined AGGregate function，UDAGG)会把一行或多行数据 (也就是一个表)聚合成一个标量值。这是一个标准的“多对一”的转换。
聚合函数的概念我们之前已经接触过多次，如 SUM()、MAX()、MIN()、AVG()、COUNT() 都是常见的系统内置聚合函数。而如果有些需求无法直接调用系统函数解决，我们就必须自定义聚合函数来实现功能了。
自定义聚合函数需要继承抽象类 AggregateFunction。AggregateFunction 有两个泛型参数 <T, ACC>，T 表示聚合输出的结果类型，ACC 则表示聚合的中间状态类型。
Flink SQL 中的聚合函数的工作原理如下:
(1)首先，它需要创建一个累加器(accumulator)，用来存储聚合的中间结果。这与 DataStream API中的AggregateFunction非常类似，累加器就可以看作是一个聚合状态。调用 createAccumulator()方法可以创建一个空的累加器。
(2)对于输入的每一行数据，都会调用 accumulate()方法来更新累加器，这是聚合的核心 过程。
(3)当所有的数据都处理完之后，通过调用 getValue()方法来计算并返回最终的结果。 所以，每个 AggregateFunction 都必须实现以下几个方法:
⚫ createAccumulator() 这是创建累加器的方法。没有输入参数，返回类型为累加器类型 ACC。
⚫ accumulate()
这是进行聚合计算的核心方法，每来一行数据都会调用。它的第一个参数是确定的，就是 当前的累加器，类型为 ACC，表示当前聚合的中间状态;后面的参数则是聚合函数调用时传 入的参数，可以有多个，类型也可以不同。这个方法主要是更新聚合状态，所以没有返回类型。 需要注意的是，accumulate()与之前的求值方法 eval()类似，也是底层架构要求的，必须为 public， 方法名必须为 accumulate，且无法直接 override、只能手动实现。
⚫ getValue()
这是得到最终返回结果的方法。输入参数是 ACC 类型的累加器，输出类型为 T。 在遇到复杂类型时，Flink 的类型推导可能会无法得到正确的结果。所以AggregateFunction
也可以专门对累加器和返回结果的类型进行声明，这是通过 getAccumulatorType()和 getResultType()两个方法来指定的。
除了上面的方法，还有几个方法是可选的。这些方法有些可以让查询更加高效，有些是在 某些特定场景下必须要实现的。比如，如果是对会话窗口进行聚合，merge()方法就是必须要 实现的，它会定义累加器的合并操作，而且这个方法对一些场景的优化也很有用;而如果聚合 函数用在 OVER 窗口聚合中，就必须实现 retract()方法，保证数据可以进行撤回操作; resetAccumulator()方法则是重置累加器，这在一些批处理场景中会比较有用。
AggregateFunction 的所有方法都必须是 公有的(public)，不能是静态的(static)，而且 名字必须跟上面写的完全一样。createAccumulator、getValue、getResultType 以及 getAccumulatorType 这几个方法是在抽象类 AggregateFunction 中定义的，可以 override;而 其他则都是底层架构约定的方法。
下面举一个具体的示例。在常用的系统内置聚合函数里，可以用 AVG()来计算平均值;如 果我们现在希望计算的是某个字段的“加权平均值”，又该怎么做呢?系统函数里没有现成的 实现，所以只能自定义一个聚合函数 WeightedAvg 来计算了。


Aggregation Function
Flink Table API中提供了User-Defined Aggregate Functions (UDAGGs)，其主要功能是将一行或多行数据进行聚合然后输出一个标量值，例如在数据集中根据Key求取指定Value的最大值或最小值。

## 2. 定义聚合函数

自定义 Aggregation Function 需要继承 org.apache.flink.table.functions.AggregateFunction 类。关于AggregateFunction的接口定义如代码清单7-14所示可以看出AggregateFunction定义相对比较复杂。

```java
public abstract class AggregateFunction<T, ACC> extends UserDefinedFunction {
    // 创建Accumulator（强制）
    public ACC createAccumulator();
    // 累加数据元素到ACC中（强制）
    public void accumulate(ACC accumulator, [user defined inputs]);  
    // 从ACC中去除数据元素（可选）
    public void retract(ACC accumulator, [user defined inputs]);  
    // 合并多个ACC（可选）
    public void merge(ACC accumulator, java.lang.Iterable<ACC> its);
    //获取聚合结果（强制）
    public T getValue(ACC accumulator);
    //重置ACC（可选）
    public void resetAccumulator(ACC accumulator);
    //如果只能被用于Over Window则返回True(预定义)
    public Boolean requiresOver = false;
    //指定统计结果类型(预定义)
    public TypeInformation<T> getResultType = null;
    //指定ACC数据类型（预定义）
    public TypeInformation<T> getAccumulatorType = null;
}
```
在 AggregateFunction 抽象类中包含了必须实现的方法 createAccumulator()、accumulate()、getValue()。其中，createAccumulator()方法主要用于创建 Accumulator，以用于存储计算过程中读取的中间数据，同时在 Accumulator 中完成数据的累加操作；accumulate() 方法将每次接入的数据元素累加到定义的 accumulator中，另外 accumulate() 方法也可以通过方法复载的方式处理不同类型的数据；当完成所有的数据累加操作结束后，最后通过 getValue() 方法返回函数的统计结果，最终完成整个 AggregateFunction 的计算流程。

除了以上三个必须要实现的方法之外，在 Aggregation Function 中还有根据具体使用场景选择性实现的方法，如 retract()、merge()、resetAccumulator() 等方法。其中，retract() 方法是在基于 Bouded Over Windows 的自定义聚合算子中使用；merge() 方法是在多批聚合和 Session Window 场景中使用；resetAccumulator() 方法是在批量计算中多批聚合的场景中使用，主要对 accumulator 计数器进行重置操作。

因为目前在 Flink 中对 Scala 的类型参数提取效率相对较低，因此 Flink 建议用户尽可能实现 Java 语言的 Aggregation Function，同时应尽可能使用原始数据类型，例如 Int、Long 等，避免使用复合数据类型，如自定义 POJOs 等，这样做的主要原因是在 Aggregation Function 计算过程中，期间会有大量对象被创建和销毁，将对整个系统的性能造成一定的影响。
