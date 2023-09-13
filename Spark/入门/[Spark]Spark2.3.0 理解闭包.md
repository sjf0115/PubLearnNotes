---
layout: post
author: sjf0115
title: Spark2.3.0 理解闭包
date: 2018-04-10 19:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-understanding-closures
---

Spark的难点之一是理解跨集群执行代码时变量和方法的作用域和生命周期。修改作用域之外的变量的RDD操作经常会造成混淆。在下面的例子中，我们将看看使用 `foreach（）` 来增加计数器的代码，其他操作也会出现类似的问题。

### 1. Example

考虑下面简单的 RDD 元素求和示例，以下行为可能会有所不同，具体取决于是否在同一个 JVM 内执行。一个常见的例子是以本地模式运行Spark（`--master = local [n]`）并将 Spark 应用程序部署到集群中（例如，通过 spark-submit 到 YARN）：

Java版本:
```java
int counter = 0;
JavaRDD<Integer> rdd = sc.parallelize(data);

// Wrong: Don't do this!!
rdd.foreach(x -> counter += x);

println("Counter value: " + counter);
```
Scala版本:
```scala
var counter = 0
var rdd = sc.parallelize(data)

// Wrong: Don't do this!!
rdd.foreach(x => counter += x)

println("Counter value: " + counter)
```
Python：
```python
counter = 0
rdd = sc.parallelize(data)

# Wrong: Don't do this!!
def increment_counter(x):
    global counter
    counter += x
rdd.foreach(increment_counter)

print("Counter value: ", counter)
```

### 2. Local模式与Cluster模式

上述代码的行为是不确定的，并且可能无法按预期工作。为了执行作业，Spark 将 RDD 操作的处理分解为 task，每个  task 由一个 executor 执行。在执行之前，Spark 会计算 task 的闭包 `closure`。闭包是指 executor 在 RDD 上进行计算时必须可见的那些变量和方法（在这里是 `foreach()`）。闭包被序列化并被发送到每个 executor。

发送给每个 executor 的闭包中的变量都是变量的副本，因此，当在 `foreach` 函数中引用 counter 时，它已经不是驱动器节点上的 counter。在驱动器节点的内存中仍有一个 counter，但是对 executor 已经不可见了！ executor 只能看到序列化闭包的副本。因此，counter 的最终值仍然为零，因为对 counter 所有的操作均引用序列化的闭包内的值。

在 Local 本地模式下，在某些情况下，`foreach` 函数实际上与驱动程序在相同的 JVM 内执行，并且会引用相同的原始 counter，实际上可能会更新。

为了确保在这些场景中有明确定义的行为，我们应该使用 Accumulator(累加器)。Spark 中的 Accumulator 专门提供了一种机制，用于在集群中的各个工作节点之间执行时安全地更新变量。具体的请参阅[累加器](http://smartsi.club/2018/04/10/spark-base-shared-variables/#2-累加器)。

一般来说，像循环或本地定义的方法这样的闭包结构，不应该被用来改变一些全局状态。Spark 并没有定义或保证从闭包外引用对象的突变行为。一些代码可以在 Local 模式下工作，但这只是偶然情况，但这样的代码在 Cluster 模式下的行为并不能按预期工作。如果需要某些全局的聚合，请改用 Accumulator。

### 3. 打印RDD的元素

另一个常见的用法是使用 `rdd.foreach（println）` 或 `rdd.map（println）` 打印 RDD 的元素。在一台机器上，这会产生预期的输出并打印所有 RDD 的元素。但是，在 Cluster 模式下，由 executor 调用的 stdout 的输出会写入到 executor 的 stdout，而不是驱动程序的 stdout，因此驱动程序的 stdout 不会显示这些！ 要在驱动程序中打印所有元素，可以使用 `collect（）` 方法首先将 RDD 带到驱动程序节点：`rdd.collect（）.foreach（println）`。 但是，这可能会导致驱动程序内存不足，因为 `collect（）` 会将整个 RDD 放到一台机器上；如果你只需要打印 RDD 的几个元素，那么更安全的方法是使用 `take（）`：`rdd.take（100）.foreach（println）`。

原文：http://spark.apache.org/docs/2.3.0/rdd-programming-guide.html#understanding-closures-
