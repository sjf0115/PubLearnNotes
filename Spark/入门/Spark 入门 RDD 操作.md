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
- 动作操作(actions): 在数据集上进行计算后将值返回给 Driver

例如，map 是一个转换操作，将数据集每个元素传递给一个函数并返回一个新 RDD 表示返回结果。另一方面，reduce 是一个动作操作，使用一些函数聚合 RDD 的所有元素并将最终结果返回给 Driver。

在 Spark 中，所有的转换操作(transformations)都是惰性(lazy)的，它们不会立即计算结果。相反，它们仅仅是记录应用到基础数据集(例如一个文件)上的转换操作。只有当动作(action)操作需要返回一个结果给 Driver 的时候，转换操作才开始计算。这种设计能够让 Spark 运行得更加高效。例如，我们知道：通过 map 创建的新数据集将在 reduce 中使用，并且仅仅返回 reduce 的结果给 Driver，而不是将比较大的映射后的数据集返回。

### 1. 基础

为了说明 RDD 基础知识，请看一下如下的一个简单示例程序：
```java
// 1. Java 版本
JavaRDD<String> lines = sc.textFile("data.txt");
JavaRDD<Integer> lineLengths = lines.map(s -> s.length());
int totalLength = lineLengths.reduce((a, b) -> a + b);

// 2. Scala 版本
val lines = sc.textFile("data.txt")
val lineLengths = lines.map(s => s.length)
val totalLength = lineLengths.reduce((a, b) => a + b)
```

第一行从外部文件定义了一个基础 RDD。这个数据集并未加载到内存中或做其他处理：lines 仅仅是一个指向文件的指针。第二行将 map 转换操作的结果定义为 lineLengths。其次，由于转换操作的惰性(lazy)，lineLengths 并没有立即计算。最后，执行一个动作操作 reduce。此时，Spark 将计算拆解多个任务(Task)，并运行在多台机器上。每台机器都运行 map 的一部分以及本地 reduce。然后仅仅将结果返回给 Driver。如果后面还会再次使用 lineLength，我们可以在运行 reduce 之前添加如下语句：
```java
// 1. Java版本
lineLengths.persist(StorageLevel.MEMORY_ONLY());

// 2. Scala 版本
lineLengths.persist()
```
这会导致 lineLength 在第一次计算之后被保存在内存中。

### 2. 传递函数给 Spark

Spark 的 API 很大程度上依赖于运行在集群上的 Driver 中的函数。

#### 2.1 Java版本

在 Java 中，函数由 [org.apache.spark.api.java.function](https://spark.apache.org/docs/3.1.3/api/java/index.html?org/apache/spark/api/java/function/package-summary.html) 接口实现。有两种方法创建这样的函数：
- 在你自己类中实现 Function 接口，作为匿名内部类或命名内部类，并将其实例传递给 Spark。
- 使用 [Lambda 表达式](https://docs.oracle.com/javase/tutorial/java/javaOO/lambdaexpressions.html) 来简洁地定义一个实现。

虽然本指南的大部分内容为了简洁起见使用了 Lambda 语法，但所有相同 API 使用长格式更容易使用。例如，我们可以按照以下方式编写我们的代码：
```java
// 匿名内部类
JavaRDD<String> lines = sc.textFile("data.txt");
JavaRDD<Integer> lineLengths = lines.map(new Function<String, Integer>() {
  public Integer call(String s) { return s.length(); }
});
int totalLength = lineLengths.reduce(new Function2<Integer, Integer, Integer>() {
  public Integer call(Integer a, Integer b) { return a + b; }
});
```
或者使用命名内部类：
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

#### 2.2 Scala版本

有两种推荐的的方法可以实现：
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

在 Java 中，使用 Scala 标准库中的 scala.Tuple2 类来表示键值对。可以如下简单地调用 `new Tuple2（a，b）` 来创建一个元组，然后用 `tuple._1（）` 和 `tuple._2（）` 访问它的字段。键值对的 RDD 由 JavaPairRDD 类表示。你可以使用特殊版本的 map 操作（如 mapToPair 和 flatMapToPair）从 JavaRDD 来构建 JavaPairRDD。JavaPairRDD 具有标准的 RDD 函数以及特殊的键值对函数。例如，如下代码在键值对上使用 reduceByKey 操作来计算每行文本在文件中的出现次数：
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

下面列出了 Spark 支持的一些常见转换函数。

#### 4.1 map(func) 映射

将函数应用于 RDD 中的每个元素，将返回值构成新的 RDD：
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

通过选择 func 函数返回 true 的元素形成一个新的 RDD：
```java
List<String> list = Lists.newArrayList("apple", "banana", "apricot");
JavaRDD<String> rdd = sc.parallelize(list);
// 只返回以a开头的水果
JavaRDD<String> filterRDD = rdd.filter(new Function<String, Boolean>() {
    @Override
    public Boolean call(String str) throws Exception {
        return str.startsWith("a");
    }
});
// apple apricot
```

#### 4.3 flatMap(func) 一行转多行

类似于 map 函数，但是一个输入可以映射为0个输出或多个输出（所以 func 应该返回一个序列而不是一个条目）：
```java
List<String> list = Lists.newArrayList("I am a student", "I like eating apple");
JavaRDD<String> rdd = sc.parallelize(list);
// 拆分单词
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
// I
// am
// a
// student
// I
// like
// eating
// apple
```
#### 4.4 distinct([numTasks])) 去重

去重：返回一个源数据集元素去重的新数据集：
```java
List<String> aList = Lists.newArrayList("1", "3", "2", "3");
JavaRDD<String> aRDD = sc.parallelize(aList);
// 去重
JavaRDD<String> rdd = aRDD.distinct();
// 1
// 2
// 3
```

#### 4.5 union(otherDataset) 并集

生成一个包含两个 RDD 中所有元素的 RDD。如果输入的 RDD 中有重复数据，`union()` 操作也会包含这些重复的数据：
```java
List<String> aList = Lists.newArrayList("1", "2", "3");
List<String> bList = Lists.newArrayList("3", "4", "5");
JavaRDD<String> aRDD = sc.parallelize(aList);
JavaRDD<String> bRDD = sc.parallelize(bList);
// 并集
JavaRDD<String> rdd = aRDD.union(bRDD); // 1 2 3 3 4 5
```

#### 4.6 intersection(otherDataset) 交集

计算两个 RDD 的共同元素返回一个新的 RDD。`intersection()` 在运行时也会去掉所有重复的元素，尽管 `intersection()` 与 `union()` 的概念相似，但性能却差的很多，因为它需要通过网络 Shuffle 来发现共同的元素：
```java
List<String> aList = Lists.newArrayList("1", "2", "3");
List<String> bList = Lists.newArrayList("3", "4", "5");
JavaRDD<String> aRDD = sc.parallelize(aList);
JavaRDD<String> bRDD = sc.parallelize(bList);
// 交集
JavaRDD<String> rdd = aRDD.intersection(bRDD); // 3
```

#### 4.7 subtract(otherDataset) 差集

subtract 接受另一个 RDD 作为参数，返回一个由只存在第一个 RDD 中而不存在第二个 RDD 中的所有元素组成的 RDD：
```java
List<String> aList = Lists.newArrayList("1", "2", "3");
List<String> bList = Lists.newArrayList("3", "4", "5");
JavaRDD<String> aRDD = sc.parallelize(aList);
JavaRDD<String> bRDD = sc.parallelize(bList);
// 差集
JavaRDD<String> rdd = aRDD.subtract(bRDD); // 1 2
```

#### 4.8 groupByKey 分组

根据键值对 key 进行分组。 在（K，V）键值对的数据集上调用时，返回（K，Iterable <V>）键值对的数据集：
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

// (Banana,[10, 9])
// (Apple,[4])
// (Pear,[5])
```
> 如果分组是为了在每个 key 上执行聚合（如求总和或平均值），则使用 reduceByKey 或 aggregateByKey 会有更好的性能。
> 默认情况下，输出中的并行级别取决于父 RDD 的分区数。你可以传递一个可选参数 numTasks 来设置任务数量。


#### 4.9 reduceByKey(func, [numTasks]) 根据key聚合

当在（K，V）键值对的数据集上调用时，返回（K，V）键值对的数据集，使用给定的 reduce 函数 func 聚合每个键的值：
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

// (Banana,19)
// (Apple,4)
// (Pear,5)
```
该函数类型必须是（V，V）=> V。类似于 groupByKey，可以通过设置可选的第二个参数来配置reduce任务的数量。

#### 4.10 sortByKey([ascending], [numPartitions]) 排序

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
// (Apple,4)
// (Banana,10)
// (Pear,5)
```

#### 4.11 coalesce(numPartitions) 改变分区个数

将 RDD 分区数目改变为 numPartitions：
```java
List<String> list = Lists.newArrayList("1", "2", "3", "4");
JavaRDD<String> rdd = sc.parallelize(list);
System.out.println("原始分区个数:" + rdd.partitions().size()); // 4

JavaRDD<String> coalesceRDD = rdd.coalesce(5, false);
System.out.println("新分区个数:" + coalesceRDD.partitions().size()); // 4

JavaRDD<String> coalesceRDD2 = rdd.coalesce(5, true);
System.out.println("新分区个数:" + coalesceRDD2.partitions().size()); // 5

原始分区个数:4
新分区个数:4
新分区个数:5
```

> 如果可选参数 shuff 为 false 时，传入的参数大于现有的分区数目，RDD 的分区数不变，也就是说不经过shuffle，是无法将 RDD 的分区数增大。

#### 4.12 repartition(numPartitions) 重新分区

对 RDD 中的数据 Shuffle 来重新分区，分区数目可以增大也可以减少，并在各分区之间进行数据平衡：
```java
List<String> list = Lists.newArrayList("1", "2", "3", "4");
JavaRDD<String> rdd = sc.parallelize(list);
JavaRDD<String> coalesceRDD = rdd.repartition(2);
System.out.println("分区个数:" + coalesceRDD.partitions().size());

// 原始分区个数:4
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

下面列出了 Spark 支持的一些常见动作操作。

#### 5.1 reduce

接收一个函数作为参数，操作两个相同元素类型的RDD并返回一个同样类型的新 RDD。如下所示计算 RDD 中所有元素的和：
```java
List<Integer> aList = Lists.newArrayList(1, 2, 3, 4);
JavaRDD<Integer> rdd = sc.parallelize(aList);
Integer result = rdd.reduce(new Function2<Integer, Integer, Integer>() {
    @Override
    public Integer call(Integer v1, Integer v2) throws Exception {
        return v1 + v2;
    }
});

// 10
```

#### 5.2 collect

将整个 RDD 的元素以列表形式返回：
```java
List<String> list = Lists.newArrayList("aa", "bb", "cc", "dd");
JavaRDD<String> rdd = sc.parallelize(list);
List<String> collect = rdd.collect();
System.out.println(collect); // [aa, bb, cc, dd]
```
#### 5.3 take(n)

返回 RDD 中的 n 个元素，并且尝试只访问尽量少的分区，因此该操作会得到一个不均衡的集合。需要注意的是，这些操作返回元素的顺序与你的预期可能不一样。
```java
List<String> list = Lists.newArrayList("aa", "bb", "cc", "dd");
JavaRDD<String> rdd = sc.parallelize(list);
List<String> collect = rdd.take(3);
System.out.println(collect); // [aa, bb, cc]
```

#### 5.4 takeSample

有时需要在 Driver 上对我们的数据进行采样，`takeSample(withReplacement, num, seed)` 函数可以让我们从数据中获取一个采样。
```java
List<String> list = Lists.newArrayList("w1","w2","w3","w4","w5");
JavaRDD<String> listRDD = sc.parallelize(list);
// 第一个参数：是否可以重复
// 第二个参数：返回take(n)
// 第三个参数：代表一个随机数种子，就是抽样算法的初始值
List<String> result = listRDD.takeSample(false,2,1);
System.out.println(result);
```

#### 5.5 saveAsTextFile(path)

将数据集的元素写入到本地文件系统，HDFS 或任何其他 Hadoop 支持的文件系统中的给定目录的文本文件（或文本文件集合）中。Spark 在每个元素上调用 toString 方法将其转换为文件中的一行文本。
```java
List<String> list = Lists.newArrayList("aa", "bb", "cc", "dd");
JavaRDD<String> rdd = sc.parallelize(list);
rdd.saveAsTextFile("/opt/data/output");
```
输出:
```
localhost:data wy$ cat output/*
aa
bb
cc
dd
```

#### 5.6 saveAsSequenceFile(path)

将数据集的元素写入到本地文件系统，HDFS 或任何其他 Hadoop 支持的文件系统中的给定路径下的 Hadoop SequenceFile中。这在实现 Hadoop 的 Writable 接口的键值对的 RDD 上可用。 在 Scala 中，它也可用于可隐式转换为 Writable 的类型（Spark包含Int，Double，String等基本类型的转换）。

#### 5.7 foreach(func)

在数据集的每个元素上运行函数 func。通常用来做一些其他事情，比如更新累加器或与外部存储系统交互。
```java
JavaRDD<Integer> javaRDD = sc.parallelize(Arrays.asList(1, 2, 3, 4));
// 定义Long型的累加器
LongAccumulator counter = sc.sc().longAccumulator();
javaRDD.foreach(new VoidFunction<Integer>() {
    @Override
    public void call(Integer v) throws Exception {
        counter.add(1L);
    }
});
System.out.println("个数：" + counter.value()); // 个数：4
```
> 修改foreach（）之外的变量而不是累加器可能会导致未定义的行为。有关更多详细信息，请参阅了解[闭包](http://spark.apache.org/docs/2.3.0/rdd-programming-guide.html#understanding-closures-)

#### 5.8 count

返回数据集中元素的个数：
```java
JavaRDD<Integer> javaRDD = sc.parallelize(Arrays.asList(1, 2, 3, 4));
long count = javaRDD.count();
System.out.println(count); // 4
```

#### 5.9 first

返回数据集的第一个元素(类似于take(1))：
```java
JavaRDD<Integer> javaRDD = sc.parallelize(Arrays.asList(1, 2, 3, 4));
Integer first = javaRDD.first();
System.out.println(first); // 1
```

原文：[RDD Operations](https://spark.apache.org/docs/3.1.3/rdd-programming-guide.html#rdd-operations)
