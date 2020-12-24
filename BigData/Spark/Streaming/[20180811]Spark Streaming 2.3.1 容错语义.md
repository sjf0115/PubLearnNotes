---
layout: post
author: sjf0115
title: Spark Streaming 容错语义
date: 2018-08-11 14:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-kafka-0-8-integration
---








输出操作（如 `foreachRDD`）具 `At Least Once`语义，也就是说，在 Worker 发生故障时，转换后的数据可能会多次写入外部实体。当使用 `saveAs *** Files` 操作保存到文件系统是可以接受的（因为文件只会被相同的数据覆盖），但是可能需要额外的处理才能实现 `Exactly Once` 语义。下面介绍两种方法来保证 `Exactly Once` 语义：

#### 幂等更新

幂等更新（Idempotent Updates）即多次尝试，产生的结果相同。例如，多次调用 `saveAs***Files` 始终将相同的数据写入生成的文件。

#### 事务更新

所有的更新都是事务性的，这样就能保证更新的原子性。一种方法是：
- 使用批处理时间（可以 `foreachRDD` 中可获取）和RDD的分区索引来创建标识符。该标识符唯一地标识流应用程序中的 blob 数据。
- 基于这个标识建立更新事务，并使用 blob 数据更新外部系统。也就是说，如果标识符尚未提交，则以原子方式提交分区数据和标识符。否则，就认为标识符已经提交，跳过更新。

```java
dstream.foreachRDD { (rdd, time) =>
  rdd.foreachPartition { partitionIterator =>
    val partitionId = TaskContext.get.partitionId()
    val uniqueId = generateUniqueId(time.milliseconds, partitionId)
    // use this uniqueId to transactionally commit the data in partitionIterator
  }
}
```










































原文：https://spark.apache.org/docs/2.3.1/streaming-programming-guide.html#fault-tolerance-semantics
