---
layout: post
author: sjf0115
title: Spark Streaming 2.2.0 Example
date: 2018-04-02 11:28:01
tags:
  - Spark
  - Spark Stream

categories: Spark
permalink: spark-streaming-first-example
---

### 1. 概述

Spark Streaming 是 Spark Core API的一个扩展，它对实时流式数据的处理具有可扩展性、高吞吐量、可容错性等特点。数据可以从诸如Kafka，Flume，Kinesis或TCP套接字等许多源中提取，并且可以使用由诸如map，reduce，join或者 window 等高级函数组成的复杂算法来处理。最后，处理后的数据可以推送到文件系统、数据库、实时仪表盘中。事实上，你可以将处理后的数据应用到 Spark 的机器学习算法、 图处理算法中去。

![image](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-first-example-1.png?raw=true)

它的内部工作原理如下图所示。Spark Streaming 接收实时输入数据流，并将数据分成多个批次，然后由 Spark 引擎处理，批量生成最终结果数据流。

![image](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Spark/spark-streaming-first-example-2.png?raw=true)

Spark Streaming 提供了一个叫做离散流(discretized stream)或称作 DStream 的高级抽象，它表示连续的数据流。DStreams 可以从如 Kafka，Flume和 Kinesis 等数据源的输入数据流创建，也可以通过对其他 DStreams 应用高级操作来创建。在内部，DStream 表示为 RDD 序列，即由一系列的 RDD 组成。

本文章介绍如何使用 DStreams 编写 Spark Streaming 程序。 可以在Scala，Java或Python（在Spark 1.2中介绍）中编写Spark Streaming程序，本文只要使用Java作为演示示例，其他可以参考[原文](http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html)。

### 2. Example

在我们进入如何编写自己的Spark Streaming程序之前，让我们快速看看一个简单的Spark Streaming程序的具体样子。 假设我们要计算从监听TCP套接字的数据服务器接收的文本数据中的统计文本中包含的单词数。

首先，我们创建一个JavaStreamingContext对象，这是所有流功能的主要入口点。 我们创建一个具有两个执行线程的本地StreamingContext，并且批处理间隔为1秒。

```java
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.streaming.Durations;
import org.apache.spark.streaming.api.java.JavaStreamingContext;

SparkConf conf = new SparkConf().setAppName("socket-spark-stream").setMaster("local[2]");
JavaSparkContext sparkContext = new JavaSparkContext(conf);
JavaStreamingContext jsc = new JavaStreamingContext(sparkContext, Durations.seconds(1));
```
使用此context，我们可以创建一个DStream，表示来自TCP源的流数据，指定主机名（例如localhost）和端口（例如7777）:

```java
import org.apache.spark.streaming.api.java.JavaReceiverInputDStream;

private static String hostName = "localhost";
private static int port = 7777;

// 以端口7777作为输入源创建DStream
JavaReceiverInputDStream<String> lines = jsc.socketTextStream(hostName, port);
```
lines DStream表示从数据服务器接收的数据流。 此流中的每个记录都是一行文本。 然后，我们要将每行文本切分为单词：
```java
// 从DStream中将每行文本切分为单词
JavaDStream<String> words = lines.flatMap(new FlatMapFunction<String, String>() {
    @Override
    public Iterator<String> call(String x) {
        return Arrays.asList(x.split(" ")).iterator();
    }
});
```
flatMap是一个DStream操作，通过从源DStream中的每个记录生成多个新记录来创建新的DStream。 在我们例子中，每一行将被拆分成多个单词，并且单词数据流用 words 这个DStream来表示。 注意，我们使用FlatMapFunction对象定义了一个转换操作。 正如我们会发现，在Java API中有许多这样的类帮助我们定义DStream转换操作。

下一步，我们计算单词的个数：
```java
// 在每个批次中计算单词的个数
JavaPairDStream<String, Integer> pairs = words.mapToPair(new PairFunction<String, String, Integer>() {
    @Override
    public Tuple2<String, Integer> call(String s) {
        return new Tuple2<>(s, 1);
    }
});

JavaPairDStream<String, Integer> wordCounts = pairs.reduceByKey(new Function2<Integer, Integer, Integer>() {
    @Override
    public Integer call(Integer i1, Integer i2) {
        return i1 + i2;
    }
});

// 将此DStream中生成的每个RDD的前10个元素打印到控制台
wordCounts.print();
```

使用PairFunction对象将words 这个DStream进一步映射（一对一变换）为（word，1）键值对的DStream。 然后，使用Function2对象，计算得到每批次数据中的单词出现的频率。 最后，wordCounts.print()将打印每秒计算的词频。

这只是设定好了要进行的计算，系统收到数据时计算就会开始。要开始接收数据，必须显式调用StreamingContext的start()方法。这样，SparkStreaming 就会开始把Spark作业不断的交给SparkContext去调度。执行会在另一个线程中进行，所以需要调用awaitTermination来等待流计算完成，来防止应用退出。

```java
// 启动流计算环境StreamingContext并等待完成
jsc.start();
// 等待作业完成
jsc.awaitTermination();
```
>注意
一个Streaming context 只启动一次，所以只有在配置好所有DStream以及所需的操作之后才能启动。

如果你已经下载和构建了Spark环境，你就能够用如下的方法运行这个例子。首先，你需要运行Netcat作为数据服务器：
```
xiaosi@yoona:~$ nc -lk 7777
hello I am yoona  hello
...

```

然后，在不同的终端，你能够用如下方式运行例子:
```
xiaosi@yoona:~/opt/spark-2.1.0-bin-hadoop2.7$ bin/spark-submit --class com.sjf.open.spark.stream.SocketSparkStreaming /home/xiaosi/code/Common-Tool/target/common-tool-jar-with-dependencies.jar
```
输出信息：
```
-------------------------------------------
Time: 1488348756000 ms
-------------------------------------------
(am,1)
(,1)
(yoona,1)
(hello,2)
(I,1)

```

### 3. Maven依赖

与Spark类似，Spark Streaming通过Maven Central提供。 要编写自己的Spark Streaming程序，您必须将以下依赖项添加到Maven项目中。
```
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-streaming_2.11</artifactId>
    <version>2.1.0</version>
</dependency>
```

对于Spark Streaming核心API中不存在的来源（如Kafka，Flume和Kinesis）获取数据，您必须将相应的组件 spark-streaming-xyz_2.11 添加到依赖项中。 例如，一些常见的如下：

Source | Artifact
--- | ---
Kafka|spark-streaming-kafka-0-8_2.11
Flume|spark-streaming-flume_2.11
Kinesis|spark-streaming-kinesis-asl_2.11 [Amazon Software License]


为了获取最新的列表，请访问[Apache repository](http://search.maven.org/#search%7Cga%7C1%7Cg%3A%22org.apache.spark%22%20AND%20v%3A%221.2.0%22)


> Spark Streaming 版本: 2.2.0

原文：http://spark.apache.org/docs/2.2.0/streaming-programming-guide.html#a-quick-example
