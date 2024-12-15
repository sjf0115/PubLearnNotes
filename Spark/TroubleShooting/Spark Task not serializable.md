---
layout: post
author: sjf0115
title: Spark Task not serializable
date: 2018-06-01 09:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-base-task-not-serializable
---

你可能会看到如下错误：
```java
org.apache.spark.SparkException: Job aborted due to stage failure: Task not serializable: java.io.NotSerializableException: ...
```
当你在 Driver（master）上初始化变量，然后在其中一个 worker 上尝试使用它时，可能会触发上述错误。在这种情况下，Spark Streaming 会尝试序列化该对象以将其发送给 worker，如果对象不可序列化，就会失败。考虑下面的代码片段：
```java
NotSerializable notSerializable = new NotSerializable();
JavaRDD<String> rdd = sc.textFile("/tmp/myfile");

rdd.map(s -> notSerializable.doSomething(s)).collect();
```
这就会触发上述错误。这里有一些方法可以解决上述错误：
- 对该类进行序列化
- 仅在传递给 map 中 lambda 函数内声明实例。
- 将 NotSerializable 对象设置为静态，并在每台机器上创建一次。
- 调用 `rdd.forEachPartition` 并在其中创建 NotSerializable 对象，如下所示：
```java
rdd.forEachPartition(iter -> {
  NotSerializable notSerializable = new NotSerializable();

  // ...Now process iter
});
```

参考：[Job aborted due to stage failure: Task not serializable:](https://databricks.gitbooks.io/databricks-spark-knowledge-base/content/troubleshooting/javaionotserializableexception.html]
