---
layout: post
author: sjf0115
title: Spark 入门 RDD 操作
date: 2018-03-12 19:13:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-rdd-operations
---

> > Spark版本: 3.1.3

RDD 支持两种类型的操作：
- 转换操作(transformations): 从现有数据集创建一个新数据集
- 动作操作(actions): 在数据集上进行计算后将值返回给驱动程序

例如，map 是一个转换操作，传递给每个数据集元素一个函数并返回一个新 RDD 表示返回结果。另一方面，reduce 是一个动作操作，使用一些函数聚合 RDD 的所有元素并将最终结果返回给驱动程序（尽管还有一个并行的 reduceByKey 返回一个分布式数据集）。

在 Spark 中，所有的转换操作(transformations)都是惰性(lazy)的，它们不会马上计算它们的结果。相反，它们仅仅记录应用到基础数据集(例如一个文件)上的转换操作。只有当 action 操作需要返回一个结果给驱动程序的时候， 转换操作才开始计算。

这个设计能够让 Spark 运行得更加高效。例如，我们知道：通过 map 创建的新数据集将在 reduce 中使用，并且仅仅返回 reduce 的结果给驱动程序，而不必将比较大的映射后的数据集返回。

### 1. 基础

为了说明 RDD 基础知识，请考虑以下简单程序：

Java版本:
```java
JavaRDD<String> lines = sc.textFile("data.txt");
JavaRDD<Integer> lineLengths = lines.map(s -> s.length());
int totalLength = lineLengths.reduce((a, b) -> a + b);
```
Scala版本:
```scala
val lines = sc.textFile("data.txt")
val lineLengths = lines.map(s => s.length)
val totalLength = lineLengths.reduce((a, b) => a + b)
```
Python版本:
```python
lines = sc.textFile("data.txt")
lineLengths = lines.map(lambda s: len(s))
totalLength = lineLengths.reduce(lambda a, b: a + b)
```

第一行定义了一个来自外部文件的基本 RDD。这个数据集并未加载到内存中或做其他处理：lines 仅仅是一个指向文件的指针。第二行将 lineLengths 定义为 map 转换操作的结果。其次，由于转换操作的惰性(lazy)，lineLengths 并没有立即计算。最后，我们运行 reduce，这是一个动作操作。此时，Spark 把计算分成多个任务(task)，并让它们运行在多台机器上。每台机器都运行 map 的一部分以及本地 reduce。然后仅仅将结果返回给驱动程序。

如果稍后还会再次使用 lineLength，我们可以在运行 reduce 之前添加：

Java版本:
```java
lineLengths.persist(StorageLevel.MEMORY_ONLY());
```
Scala版本:
```scala
lineLengths.persist()
```
Python版本:
```python
lineLengths.persist()
```
这将导致 lineLength 在第一次计算之后被保存在内存中。

### 2. 传递函数给Spark

Spark 的 API 很大程度上依赖于运行在集群上的驱动程序中的函数。

#### 2.1 Java版本

在 Java 中，函数由 [org.apache.spark.api.java.function](http://spark.apache.org/docs/2.3.0/api/java/index.html?org/apache/spark/api/java/function/package-summary.html) 接口实现。创建这样的函数有两种方法：
- 在你自己类中实现 Function 接口，作为匿名内部类或命名内部类，并将其实例传递给Spark。
- 使用 [lambda 表达式](https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html) 来简洁地定义一个实现。

虽然本指南的大部分内容都使用 lambda 语法进行简明说明，但很容易以长格式使用所有相同的API。例如，我们可以按照以下方式编写我们的代码：

匿名内部类
```java
JavaRDD<String> lines = sc.textFile("data.txt");
JavaRDD<Integer> lineLengths = lines.map(new Function<String, Integer>() {
  public Integer call(String s) { return s.length(); }
});
int totalLength = lineLengths.reduce(new Function2<Integer, Integer, Integer>() {
  public Integer call(Integer a, Integer b) { return a + b; }
});
```
或者命名内部类
```java
class GetLength implements Function<String, Integer> {
  public Integer call(String s) { return s.length(); }
}
class Sum implements Function2<Integer, Integer, Integer> {
  public Integer call(Integer a, Integer b) { return a + b; }
}

JavaRDD<String> lines = sc.textFile("data.txt");
JavaRDD<Integer> lineLengths = lines.map(new GetLength());
int totalLength = lineLengths.reduce(new Sum());
```

> 请注意，Java中的匿名内部类也可以访问封闭范围内的变量，只要它们标记为final。 Spark会将这些变量的副本发送给每个工作节点，就像其他语言一样。

#### 2.2 Scala版本

有两种推荐的的方法可以做到这一点：
- [匿名函数语法](http://docs.scala-lang.org/tour/basics.html#functions)，可用于短片段代码。
- 全局单例对象中的静态方法。例如，您可以定义对象 MyFunctions，然后传递 MyFunctions.func1，如下所示：

```scala
object MyFunctions {
  def func1(s: String): String = { ... }
}

myRdd.map(MyFunctions.func1)
```

> 虽然也可以在类实例中传递方法的引用（与单例对象相反），但这需要将包含该类的对象与方法一起发送。 例如，考虑：

```scala
class MyClass {
  def func1(s: String): String = { ... }
  def doStuff(rdd: RDD[String]): RDD[String] = { rdd.map(func1) }
}
```
在这里，如果我们创建一个新的 MyClass 实例并调用 doStuff 方法，那么其中的 map 会引用该 MyClass 实例的 func1 方法，因此需要将整个对象发送到集群。它类似于编写 `rdd.map（x => this.func1（x））` 。

以类似的方式，访问外部对象的字段将引用整个对象：
```scala
class MyClass {
  val field = "Hello"
  def doStuff(rdd: RDD[String]): RDD[String] = { rdd.map(x => field + x) }
}
```
等价于 `rdd.map（x => this.field + x）`，它引用了 `this` 对象的所有东西 。为了避免这个问题，最简单的方法是将字段复制到本地变量中，而不是从外部访问它：
```scala
def doStuff(rdd: RDD[String]): RDD[String] = {
  val field_ = this.field
  rdd.map(x => field_ + x)
}
```

### 3. 使用键值对

虽然大多数 Spark 操作可以在任意类型对象的 RDD 上工作，但是还是几个特殊操作只能在键值对的 RDD 上使用。最常见的是分布式 `shuffle` 操作，例如按键分组或聚合元素。

#### 3.1 Java版本

在 Java 中，使用 Scala 标准库中的 scala.Tuple2 类来表示键值对。可以如下简单地调用 `new Tuple2（a，b）` 来创建一个元组，然后用 `tuple._1（）` 和 `tuple._2（）` 访问它的字段。

键值对的 RDD 由 JavaPairRDD 类表示。你可以使用特殊版本的 map 操作（如 mapToPair 和 flatMapToPair）从 JavaRDD 来构建 JavaPairRDD。JavaPairRDD 具有标准的 RDD 函数以及特殊的键值对函数。

例如，以下代码在键值对上使用 reduceByKey 操作来计算每行文本在文件中的出现次数：
```java
JavaRDD<String> lines = sc.textFile("data.txt");
JavaPairRDD<String, Integer> pairs = lines.mapToPair(s -> new Tuple2(s, 1));
JavaPairRDD<String, Integer> counts = pairs.reduceByKey((a, b) -> a + b);
```
例如，我们也可以使用 `counts.sortByKey（）` 来按字母顺序来对键值对排序，最后使用 `counts.collect（）` 将结果作为对象数组返回到驱动程序。

#### 3.2 Scala版本

在 Scala 中，这些操作在包含 Tuple2 对象的 RDD 上可以自动获取（内置元组，通过简单写入（a，b）创建）。在 PairRDDFunctions 类中提供了键值对操作，该类自动包装元组的 RDD。

例如，以下代码在键值对上使用 reduceByKey 操作来计算每行文本在文件中的出现次数：
```scala
val lines = sc.textFile("data.txt")
val pairs = lines.map(s => (s, 1))
val counts = pairs.reduceByKey((a, b) => a + b)
```
例如，我们也可以使用 `counts.sortByKey（）` 来按字母顺序来对键值对排序，最后使用 `counts.collect（）` 将结果作为对象数组返回到驱动程序。

> 在键值对操作时使用一个自定义对象作为 key 的时候，你需要确保自定义 equals() 方法和 hashCode() 方法是匹配的。更加详细的内容，查看 [Object.hashCode()](https://docs.oracle.com/javase/7/docs/api/java/lang/Object.html#hashCode()) 文档)中的契约概述。

### 4. 转换操作

下面列出了Spark支持的一些常见转换函数。 有关详细信息，请参阅RDD API文档（Scala，Java，Python，R）和RDD函数doc（Scala，Java）。

#### 4.1 map(func) 映射

将函数应用于 RDD 中的每个元素，将返回值构成新的 RDD。
```java
List<String> aList = Lists.newArrayList("a", "B", "c", "b");
JavaRDD<String> rdd = sc.parallelize(aList);
// 小写转大写
JavaRDD<String> upperLinesRDD = rdd.map(new Function<String, String>() {
    @Override
    public String call(String str) throws Exception {
        if (StringUtils.isBlank(str)) {
            return str;
        }
        return str.toUpperCase();
    }
});
// A B C B
```

#### 4.2 filter(func) 过滤

返回通过选择那些 func 函数返回 true 的元素形成一个新的 RDD。
```java
List<String> list = Lists.newArrayList("a", "B", "c", "b");
JavaRDD<String> rdd = sc.parallelize(list);
// 只返回以a开头的字符串
JavaRDD<String> filterRDD = rdd.filter(new Function<String, Boolean>() {
    @Override
    public Boolean call(String str) throws Exception {
        return !str.startsWith("a");
    }
});
// B c b
```

#### 4.3 flatMap(func) 一行转多行

类似于 map 函数，但是每个输入项可以映射为0个输出项或更多输出项（所以 func 应该返回一个序列而不是一个条目）。
```java
List<String> list = Lists.newArrayList("a 1", "B 2");
JavaRDD<String> rdd = sc.parallelize(list);
// 一行转多行 以空格分割
JavaRDD<String> resultRDD = rdd.flatMap(new FlatMapFunction<String, String>() {
    @Override
    public Iterator<String> call(String s) throws Exception {
        if (StringUtils.isBlank(s)) {
            return null;
        }
        String[] array = s.split(" ");
        return Arrays.asList(array).iterator();
    }
});
// a
// 1
// B
// 2
```
#### 4.4 distinct([numTasks]))

去重
```java
List<String> aList = Lists.newArrayList("1", "3", "2", "3");
JavaRDD<String> aRDD = sc.parallelize(aList);
// 去重
JavaRDD<String> rdd = aRDD.distinct(); // 1 2 3
```

#### 4.5 union(otherDataset) 并集

生成一个包含两个 RDD 中所有元素的 RDD。如果输入的 RDD 中有重复数据，`union()` 操作也会包含这些重复的数据．
```java
List<String> aList = Lists.newArrayList("1", "2", "3");
List<String> bList = Lists.newArrayList("3", "4", "5");
JavaRDD<String> aRDD = sc.parallelize(aList);
JavaRDD<String> bRDD = sc.parallelize(bList);
// 并集
JavaRDD<String> rdd = aRDD.union(bRDD); // 1 2 3 3 4 5
```

#### 4.6 intersection(otherDataset) 交集

求两个 RDD 共同的元素的 RDD。 `intersection()` 在运行时也会去掉所有重复的元素，尽管 `intersection()` 与 `union()` 的概念相似，但性能却差的很多，因为它需要通过网络混洗数据来发现共同的元素。
```java
List<String> aList = Lists.newArrayList("1", "2", "3");
List<String> bList = Lists.newArrayList("3", "4", "5");
JavaRDD<String> aRDD = sc.parallelize(aList);
JavaRDD<String> bRDD = sc.parallelize(bList);
// 交集
JavaRDD<String> rdd = aRDD.intersection(bRDD); // 3
```

#### 4.7 subtract(otherDataset) 差集

subtract 接受另一个 RDD 作为参数，返回一个由只存在第一个 RDD 中而不存在第二个 RDD 中的所有元素组成的 RDD
```java
List<String> aList = Lists.newArrayList("1", "2", "3");
List<String> bList = Lists.newArrayList("3", "4", "5");
JavaRDD<String> aRDD = sc.parallelize(aList);
JavaRDD<String> bRDD = sc.parallelize(bList);
// 差集
JavaRDD<String> rdd = aRDD.subtract(bRDD); // 1 2
```

#### 4.8 groupByKey 分组

根据键值对 key 进行分组。 在（K，V）键值对的数据集上调用时，返回（K，Iterable <V>）键值对的数据集。

> 如果分组是为了在每个 key 上执行聚合（如求总和或平均值），则使用 reduceByKey 或 aggregateByKey 会有更好的性能。
> 默认情况下，输出中的并行级别取决于父 RDD 的分区数。你可以传递一个可选参数 numTasks 来设置任务数量。

```java
Tuple2<String, Integer> t1 = new Tuple2<String, Integer>("Banana", 10);
Tuple2<String, Integer> t2 = new Tuple2<String, Integer>("Pear", 5);
Tuple2<String, Integer> t3 = new Tuple2<String, Integer>("Banana", 9);
Tuple2<String, Integer> t4 = new Tuple2<String, Integer>("Apple", 4);
List<Tuple2<String, Integer>> list = Lists.newArrayList();
list.add(t1);
list.add(t2);
list.add(t3);
list.add(t4);
JavaPairRDD<String, Integer> rdd = sc.parallelizePairs(list);
// 分组
JavaPairRDD<String, Iterable<Integer>> groupRDD = rdd.groupByKey();

// Apple --- 4
// Pear --- 5
// Banana --- 10 9
```

#### 4.9 reduceByKey(func, [numTasks]) 根据key聚合

当在（K，V）键值对的数据集上调用时，返回（K，V）键值对的数据集，使用给定的reduce函数 func 聚合每个键的值，该函数类型必须是（V，V）=> V。类似于 groupByKey，可以通过设置可选的第二个参数来配置reduce任务的数量。

```java
Tuple2<String, Integer> t1 = new Tuple2<String, Integer>("Banana", 10);
Tuple2<String, Integer> t2 = new Tuple2<String, Integer>("Pear", 5);
Tuple2<String, Integer> t3 = new Tuple2<String, Integer>("Banana", 9);
Tuple2<String, Integer> t4 = new Tuple2<String, Integer>("Apple", 4);
List<Tuple2<String, Integer>> list = Lists.newArrayList();
list.add(t1);
list.add(t2);
list.add(t3);
list.add(t4);
JavaPairRDD<String, Integer> rdd = sc.parallelizePairs(list);
// 分组计算
JavaPairRDD<String, Integer> reduceRDD = rdd.reduceByKey(new Function2<Integer, Integer, Integer>() {
    @Override
    public Integer call(Integer v1, Integer v2) throws Exception {
        return v1 + v2;
    }
});

// Apple --- 4
// Pear --- 5
// Banana --- 19
```
#### 4.10 sortByKey([ascending], [numPartitions])

根据key进行排序。在（K，V）键值对的数据集调用，其中 K 实现 Ordered 接口，按照升序或降序顺序返回按键排序的（K，V）键值对的数据集。
```java
Tuple2<String, Integer> t1 = new Tuple2<String, Integer>("Banana", 10);
Tuple2<String, Integer> t2 = new Tuple2<String, Integer>("Pear", 5);
Tuple2<String, Integer> t3 = new Tuple2<String, Integer>("Apple", 4);
List<Tuple2<String, Integer>> list = Lists.newArrayList();
list.add(t1);
list.add(t2);
list.add(t3);
JavaPairRDD<String, Integer> rdd = sc.parallelizePairs(list);
// 根据key排序
JavaPairRDD<String, Integer> sortRDD = rdd.sortByKey(true);
// Apple --- 4
// Banana --- 10
// Pear --- 5
```

#### 4.11 coalesce(numPartitions) 合并分区

对 RDD 分区进行合并，合并后分区数目为 numPartitions。大型数据集过滤之后可以对高效地运行操作很有帮助。
```java
List<String> list = Lists.newArrayList("1", "2", "3", "4");
JavaRDD<String> rdd = sc.parallelize(list);
JavaRDD<String> coalesceRDD = rdd.coalesce(2, false);
System.out.println("分区个数:" + coalesceRDD.partitions().size());
// 分区个数:1

JavaRDD<String> coalesceRDD2 = rdd.coalesce(2, true);
System.out.println("分区个数:" + coalesceRDD2.partitions().size());
// 分区个数:2
```

> 如果可选参数 shuff 为 false 时，传入的参数大于现有的分区数目，RDD 的分区数不变，也就是说不经过shuffle，是无法将 RDD 的分区数增大。

#### 4.12 repartition(numPartitions) 重新分区

对 RDD 中的数据重新洗牌来重新分区，分区数目可以增大也可以减少，并在各分区之间进行数据平衡。这总是通过网络混洗所有数据。
```java
List<String> list = Lists.newArrayList("1", "2", "3", "4");
JavaRDD<String> rdd = sc.parallelize(list);
JavaRDD<String> coalesceRDD = rdd.repartition(2);
System.out.println("分区个数:" + coalesceRDD.partitions().size());
// 分区个数:2
```
我们从源码看到 repartition 只是 `coalesce(numPartitions, shuffle = true)` 的一个简易实现：
```scala
def repartition(numPartitions: Int)(implicit ord: Ordering[T] = null): RDD[T] = withScope {
  coalesce(numPartitions, shuffle = true)
}
```

#### 4.13 cartesian(otherDataset) 笛卡尔积

对两个 RDD 中的所有元素进行笛卡尔积操作。在类型为 T 和 U 的两个数据集上调用时，返回（T，U）键值对（所有元素对）数据集。
```java
List<String> aList = Lists.newArrayList("1", "2");
List<String> bList = Lists.newArrayList("3", "4");
JavaRDD<String> aRDD = sc.parallelize(aList);
JavaRDD<String> bRDD = sc.parallelize(bList);
// 笛卡尔积
JavaPairRDD<String, String> cartesianRDD = aRDD.cartesian(bRDD);
// (1, 3)
// (1, 4)
// (2, 3)
// (2, 4)
```

#### 4.14 cogroup(otherDataset, [numPartitions])

在类型（K，V）和（K，W）两个数据集上调用时，返回（K，（Iterable <V>，Iterable <W>））元组的数据集。这个操作也被称为 groupWith。
```java
Tuple2<String, Integer> t1 = new Tuple2<String, Integer>("Banana", 10);
Tuple2<String, Integer> t2 = new Tuple2<String, Integer>("Pear", 5);
Tuple2<String, Integer> t3 = new Tuple2<String, Integer>("Apple", 4);

Tuple2<String, Integer> t4 = new Tuple2<String, Integer>("Banana", 2);
Tuple2<String, Integer> t5 = new Tuple2<String, Integer>("Apple", 11);
Tuple2<String, Integer> t6 = new Tuple2<String, Integer>("Banana", 7);
List<Tuple2<String, Integer>> list1 = Lists.newArrayList();
list1.add(t1);
list1.add(t2);
list1.add(t3);
List<Tuple2<String, Integer>> list2 = Lists.newArrayList();
list2.add(t4);
list2.add(t5);
list2.add(t6);

JavaPairRDD<String, Integer> rdd1 = sc.parallelizePairs(list1);
JavaPairRDD<String, Integer> rdd2 = sc.parallelizePairs(list2);

JavaPairRDD<String, Tuple2<Iterable<Integer>, Iterable<Integer>>> cogroupRDD = rdd1.cogroup(rdd2);
cogroupRDD.foreach(new VoidFunction<Tuple2<String, Tuple2<Iterable<Integer>, Iterable<Integer>>>>() {
    @Override
    public void call(Tuple2<String, Tuple2<Iterable<Integer>, Iterable<Integer>>> group) throws Exception {
        String key = group._1;
        Tuple2<Iterable<Integer>, Iterable<Integer>> value = group._2;
        System.out.println(key + " --- " + value.toString());
    }
});
// Apple --- ([4],[11])
// Pear --- ([5],[])
// Banana --- ([10],[2, 7])
```

### 5. 动作操作 (Action)

下面列出了Spark支持的一些常见操作。

#### 5.1 reduce

接收一个函数作为参数，这个函数要操作两个相同元素类型的RDD并返回一个同样类型的新元素．
```java
List<String> aList = Lists.newArrayList("aa", "bb", "cc", "dd");
JavaRDD<String> rdd = sc.parallelize(aList);
String result = rdd.reduce(new Function2<String, String, String>() {
    @Override
    public String call(String v1, String v2) throws Exception {
        return v1 + "#" + v2;
    }
});
System.out.println(result); // aa#bb#cc#dd
```

#### 5.2 collect

将整个RDD的内容返回．
```java
List<String> list = Lists.newArrayList("aa", "bb", "cc", "dd");
JavaRDD<String> rdd = sc.parallelize(list);
List<String> collect = rdd.collect();
System.out.println(collect); // [aa, bb, cc, dd]
```
#### 5.3 take(n)

返回 RDD 中的n个元素，并且尝试只访问尽量少的分区，因此该操作会得到一个不均衡的集合．需要注意的是，这些操作返回元素的顺序与你的预期可能不一样．
```java
List<String> list = Lists.newArrayList("aa", "bb", "cc", "dd");
JavaRDD<String> rdd = sc.parallelize(list);
List<String> collect = rdd.take(3);
System.out.println(collect); // [aa, bb, cc]
```

#### 5.4 takeSample

有时需要在驱动器程序中对我们的数据进行采样，`takeSample(withReplacement, num, seed)` 函数可以让我们从数据中获取一个采样，并指定是否替换．

#### 5.5 saveAsTextFile(path)

将数据集的元素写入到本地文件系统，HDFS 或任何其他 Hadoop 支持的文件系统中的给定目录的文本文件（或文本文件集合）中。Spark 在每个元素上调用 toString 方法将其转换为文件中的一行文本。
```java
List<String> list = Lists.newArrayList("aa", "bb", "cc", "dd");
JavaRDD<String> rdd = sc.parallelize(list);
rdd.saveAsTextFile("/home/xiaosi/output");
```
输出:
```
xiaosi@ying:~/output$ cat *
aa
bb
cc
dd
```

#### 5.6 saveAsSequenceFile(path)

将数据集的元素写入到本地文件系统，HDFS 或任何其他 Hadoop 支持的文件系统中的给定路径下的 Hadoop SequenceFile中。这在实现 Hadoop 的 Writable 接口的键值对的 RDD 上可用。 在 Scala 中，它也可用于可隐式转换为 Writable 的类型（Spark包含Int，Double，String等基本类型的转换）。

#### 5.7 foreach(func)

在数据集的每个元素上运行函数 func。这通常用于副作用，如更新累加器或与外部存储系统交互。

> 修改foreach（）之外的变量而不是累加器可能会导致未定义的行为。有关更多详细信息，请参阅了解[闭包](http://spark.apache.org/docs/2.3.0/rdd-programming-guide.html#understanding-closures-)

原文：[RDD Operations](https://spark.apache.org/docs/3.1.3/rdd-programming-guide.html#rdd-operations)
