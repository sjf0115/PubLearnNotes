---
layout: post
author: sjf0115
title: Spark 入门 理解闭包
date: 2018-04-10 19:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-understanding-closures
---

Spark 的难点之一就是理解跨集群执行代码时变量和方法的作用域和生命周期。在 RDD 操作中修改作用域之外的变量经常会造成混乱。在下面的例子中，我们将看看使用 `foreach()` 来增加计数器的代码，其他操作也会出现类似的问题。

### 1. Example

考虑下面简单的 RDD 元素求和示例，执行结果可能会因为环境不同而有所不同，具体取决于是否在同一个 JVM 内执行。一个常见的例子是以本地模式运行Spark(`--master = local [n]`)并将 Spark 应用程序部署到集群中(例如，通过 spark-submit 到 YARN)：
```java
// 1. Java 版本
int counter = 0;
JavaRDD<Integer> rdd = sc.parallelize(data);

// Wrong: Don't do this!!
rdd.foreach(x -> counter += x);

println("Counter value: " + counter);

// 2. Scala版本
var counter = 0
var rdd = sc.parallelize(data)

// Wrong: Don't do this!!
rdd.foreach(x => counter += x)

println("Counter value: " + counter)
```

### 2. Local 模式与 Cluster 模式

上述代码的执行结果具有不确定性，并且可能不能按预期的那样执行。为了执行作业，Spark 将 RDD 操作的处理分解为 Task，每个 Task 由一个 Executor 执行。在执行之前，Spark 会计算 Task 的闭包 `closure`。闭包是指为了在 RDD 上进行计算必须对 Executor 可见的那些变量和方法(在这里是 `foreach()`)。闭包被序列化并被发送到每个 Executor。

发送到每个 Executor 上闭包中的变量都是原始变量的副本，因此当在 `foreach` 函数中引用 counter 时，引用的不是 Driver 节点上的那个 counter，而是它的一个副本。虽然在 Driver 节点的内存中仍有一个 counter 变量，但是对 Executor 已经不可见了！Executor 看到的是序列化闭包中的副本。因此，Driver 上 counter 的最终值仍然为零，因为对 counter 所有的操作均引用序列化闭包内的副本值。

在 Local 本地模式下，在某些情况下，`foreach` 函数实际上与 Driver 在相同的 JVM 内执行，并且会引用相同的原始 counter，Driver 上的 counter 实际上可能会更新。为了确保在这些场景中有明确定义的行为，我们应该使用 Accumulator(累加器)。Spark 中的 Accumulator 专门提供了一种机制，用于在集群中的各个工作节点之间执行时安全地更新变量。具体的请参阅[累加器](https://smartsi.blog.csdn.net/article/details/132844400)。

一般来说，像循环或本地定义的方法这样的闭包结构，不应该被用来改变一些全局状态。Spark 并没有定义或很难保证从闭包外引用对象的意外行为。一些代码可以在 Local 模式下工作，但这只是偶然情况，但这样的代码在 Cluster 模式下的行为并不能按预期工作。如果需要某些全局的聚合，请改用 Accumulator。

### 3. 打印 RDD 的元素

另一个常见的用法是使用 `rdd.foreach(println)` 或 `rdd.map(println)` 打印 RDD 的元素。在一台机器上，这会产生预期的输出并打印所有 RDD 的元素。但是，在 Cluster 模式下，由 Executor 调用的 stdout 的输出会写入到 Executor 的 stdout，而不是 Driver 的 stdout，因此 Driver 的 stdout 不会显示这些！ 要在 Driver 中打印所有元素，可以使用 `collect()` 方法首先将 RDD 带到 Driver 节点：`rdd.collect().foreach(println)`。 但是，这可能会导致 Driver 的内存不足，因为 `collect()` 会将整个 RDD 放到一台机器上；如果你只需要打印 RDD 的几个元素，那么更安全的方法是使用 `take()`：`rdd.take(100).foreach(println)`。

原文：[Understanding closures ](https://spark.apache.org/docs/3.1.3/rdd-programming-guide.html#understanding-closures-)
