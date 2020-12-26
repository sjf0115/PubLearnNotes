---
layout: post
author: smartsi
title: 构建Flink第一个应用程序
date: 2020-09-20 20:43:01
tags:
  - Flink

categories: Flink
permalink: build-first-flink-application
---

在本文中，我们将从零开始构建Flink第一个应用程序：WordCount。

### 1. 环境搭建

Flink 可以运行在 Linux、Mac 以及 Windows 上。在这我们使用的是 Mac 系统。为了开发 Flink 应用程序，需要提前安装 Java 和 Maven 环境。

如果已经安装 Java 环境，运行如下命令会输出具体的版本信息：
```
wy:flink wy$ java -version
java version "1.8.0_161"
Java(TM) SE Runtime Environment (build 1.8.0_161-b12)
Java HotSpot(TM) 64-Bit Server VM (build 25.161-b12, mixed mode)
```
如果已经安装 Maven 环境，运行如下命令会输出具体版本信息：
```
wy:flink wy$ mvn --version
Apache Maven 3.5.4 (1edded0938998edf8bf061f1ceb3cfdeccf443fe; 2018-06-18T02:33:14+08:00)
Maven home: /opt/maven
Java version: 1.8.0_161, vendor: Oracle Corporation, runtime: /Library/Java/JavaVirtualMachines/jdk1.8.0_161.jdk/Contents/Home/jre
Default locale: zh_CN, platform encoding: UTF-8
OS name: "mac os x", version: "10.12.6", arch: "x86_64", family: "mac"
```
在搭建好我们的依赖环境之后，最重要的是搭建我们的 Flink 集群，具体可以参考 [Flink1.4 安装与启动](http://smartsi.club/flink-how-to-install-and-run.html) 来完成安装。我们为了研究新特性，所以选择 Flink 最新版本 [2.11.2](https://www.apache.org/dyn/closer.lua/flink/flink-1.11.2/flink-1.11.2-bin-scala_2.12.tgz) 版本，如果是在生产环境使用，建议不要使用最新版本。如果已经安装 Flink 环境，运行如下命令会输出具体版本信息：
```
wy:flink wy$ flink --version
Version: 1.11.2, Commit ID: fe36135
```
使用如下命令启动 Flink 集群：
```
wy:flink wy$ ./start-cluster.sh
Starting cluster.
Starting standalonesession daemon on host wy.lan.
Starting taskexecutor daemon on host wy.lan.
```

### 2. 创建Maven项目

我们可以使用 Maven Archetype 来创建我们的项目以及一些初始的默认依赖。运行如下命令来创建项目：
```
mvn archetype:generate \
    -DarchetypeGroupId=org.apache.flink \
    -DarchetypeArtifactId=flink-quickstart-java \
    -DarchetypeVersion=1.11.2 \
    -DgroupId=com.example \
    -DartifactId=flink-example \
    -Dversion=0.1 \
    -Dpackage=com.flink.example \
    -DinteractiveMode=false
```
或者使用 IDE 通过图形化创建：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/build-first-flink-application-1.jpg?raw=true)

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/build-first-flink-application-2.jpg?raw=true)

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/build-first-flink-application-3.jpg?raw=true)

通过上述构建之后 pom.xml 文件已经包含了所需的 Flink 依赖：
```xml
<dependency>
	<groupId>org.apache.flink</groupId>
	<artifactId>flink-java</artifactId>
	<version>${flink.version}</version>
	<scope>provided</scope>
</dependency>

<dependency>
	<groupId>org.apache.flink</groupId>
	<artifactId>flink-streaming-java_${scala.binary.version}</artifactId>
	<version>${flink.version}</version>
	<scope>provided</scope>
</dependency>

<dependency>
	<groupId>org.apache.flink</groupId>
	<artifactId>flink-clients_${scala.binary.version}</artifactId>
	<version>${flink.version}</version>
	<scope>provided</scope>
</dependency>

<dependency>
	<groupId>org.apache.logging.log4j</groupId>
	<artifactId>log4j-slf4j-impl</artifactId>
	<version>${log4j.version}</version>
	<scope>runtime</scope>
</dependency>

<dependency>
	<groupId>org.apache.logging.log4j</groupId>
	<artifactId>log4j-api</artifactId>
	<version>${log4j.version}</version>
	<scope>runtime</scope>
</dependency>

<dependency>
	<groupId>org.apache.logging.log4j</groupId>
	<artifactId>log4j-core</artifactId>
	<version>${log4j.version}</version>
	<scope>runtime</scope>
</dependency>
```
并且在 src/main/java 下有几个示例程序框架。接下来我们将开始编写第一个 Flink 程序。

### 3. 编写Flink程序

创建 SocketWindowWordCount.java 文件：
```java
public class SocketWindowWordCount {
    public static void main(String[] args) {
    }
}
```
现在我们的程序只有一个框架，我们会一步步往里面填代码。Flink 程序的第一步是通过 ParameterTool 解析传递进来的 hostname 和 port：
```java
final String hostname;
final int port;
try {
    final ParameterTool params = ParameterTool.fromArgs(args);
    hostname = params.has("hostname") ? params.get("hostname") : "localhost";
    port = params.getInt("port");
} catch (Exception e) {
    System.err.println("No port specified. Please run 'SocketWindowWordCount " +
            "--hostname <hostname> --port <port>', where hostname (localhost by default) " +
            "and port is the address of the text server");
    System.err.println("To start a simple text server, run 'netcat -l <port>' and " +
            "type the input text into the command line");
    return;
}
```
第二步是创建 StreamExecutionEnvironment。这是一个入口类，可以用来设置参数和创建数据源以及提交任务：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
```
第三步是创建一个从本地端口号的 Socket 中读取数据的数据源：
```java
DataStream<String> text = env.socketTextStream(hostname, port, "\n");
```
这创建了一个字符串类型的 DataStream。在本示例中，我们的目的是每统计每个单词在特定时间窗口中出现的次数，比如说5秒一个窗口。我们首先要将字符串数据解析成单词和次数（使用Tuple2<String, Integer>表示），第一个字段是单词，第二个字段是次数，次数初始值都设置成了1。我们实现了一个 flatmap 来做解析的工作，因为一行数据中可能有多个单词：
```java
DataStream<Tuple2<String, Integer>> wordsCount = text.flatMap(new FlatMapFunction<String, Tuple2<String, Integer>>() {
    @Override
    public void flatMap(String value, Collector out) {
        for (String word : value.split("\\s")) {
            out.collect(Tuple2.of(word, 1));
        }
    }
});
```
接着我们将数据流按照单词字段做分组，这里可以使用 `keyBy(KeySelector<T, K> key)` 方法，得到一个以单词为键的 Tuple2<String, Integer> 数据流。然后我们可以在流上指定想要的窗口，并根据窗口中的数据计算结果。在我们的例子中，我们想要每5秒聚合一次单词数：
```java
DataStream<Tuple2<String, Integer>> windowCount = wordsCount
    .keyBy(new KeySelector<Tuple2<String,Integer>, String>() {
        @Override
        public String getKey(Tuple2<String, Integer> tuple) throws Exception {
            return tuple.f0;
        }
    })
    .timeWindow(Time.seconds(5))
    .reduce(new ReduceFunction<Tuple2<String, Integer>>() {
        @Override
        public Tuple2 reduce(Tuple2<String, Integer> a, Tuple2<String, Integer> b) {
            return new Tuple2(a.f0, a.f1 + b.f1);
        }
    });
```
我们通过 `timeWindow()` 方法指定我们5秒的翻滚窗口，即只统计每5秒的单词个数。我们为每个key每个窗口指定了 `reduce` 聚合函数，相同单词的出现次数相加，最终得到一个结果数据流，每5秒内的每个单词出现的次数。

下面一步就是将数据流结果打印到控制台：
```java
windowCount.print().setParallelism(1);
```
最后是一步就是启动实际Flink作业：
```java
env.execute("Socket Window WordCount");
```
所有算子操作只是构建了内部算子操作的图形，只有在 execute() 方法被调用时才会提交到集群或本地机器执行。

> 程序剖析具体可以查阅[Flink1.4 Flink程序剖析](http://smartsi.club/flink-anatomy-of-a-flink-program.html)

下面是完整的代码：
```java
package com.flink.example.stream;

import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.common.functions.ReduceFunction;
import org.apache.flink.api.java.functions.KeySelector;
import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.api.java.utils.ParameterTool;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.util.Collector;

/**
 * SocketWindowWordCount
 * Created by wy on 2020/9/20.
 */
public class SocketWindowWordCount {
    public static void main(String[] args) throws Exception {
        // 1. 通过 ParameterTool 解析参数
        final String hostname;
        final int port;
        try {
            final ParameterTool params = ParameterTool.fromArgs(args);
            hostname = params.has("hostname") ? params.get("hostname") : "localhost";
            port = params.getInt("port");
        }
        catch (Exception e) {
            System.err.println("No port specified. Please run 'SocketWindowWordCount " +
                    "--hostname <hostname> --port <port>', where hostname (localhost by default) " +
                    "and port is the address of the text server");
            System.err.println("To start a simple text server, run 'netcat -l <port>' and " +
                    "type the input text into the command line");
            return;
        }

        // 2. 创建StreamExecutionEnvironment
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // 3. 连接Socket获取数据
        DataStream<String> text = env.socketTextStream(hostname, port, "\n");

        // 4. 输入字符串解析为<单词,出现次数>
        DataStream<Tuple2<String, Integer>> wordsCount = text.flatMap(new FlatMapFunction<String, Tuple2<String, Integer>>() {
            @Override
            public void flatMap(String value, Collector out) {
                for (String word : value.split("\\s")) {
                    out.collect(Tuple2.of(word, 1));
                }
            }
        });

        // 5. 分组窗口计算
        DataStream<Tuple2<String, Integer>> windowCount = wordsCount
                .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
                    @Override
                    public String getKey(Tuple2<String, Integer> tuple) throws Exception {
                        return tuple.f0;
                    }
                })
                .timeWindow(Time.seconds(5))
                .reduce(new ReduceFunction<Tuple2<String, Integer>>() {
                    @Override
                    public Tuple2 reduce(Tuple2<String, Integer> a, Tuple2<String, Integer> b) {
                        return new Tuple2(a.f0, a.f1 + b.f1);
                    }
                });

        // 6. 输出结果并开始执行
        windowCount.print().setParallelism(1);

        // 7. 开启作业
        env.execute("Socket Window WordCount");
    }
}
```
> 完成项目请查阅[SocketWindowWordCount](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/app/SocketWindowWordCount.java)

### 5. 运行程序

要运行示例程序，首先我们在终端启动 netcat 获得输入流：
```
nc -lk 9000
```
然后直接运行 SocketWindowWordCount 程序：
```java
wy:flink wy$ ./bin/flink run -c com.flink.example.stream.SocketWindowWordCount  flink-example-1.0.jar --hostname localhost --port 9000
Job has been submitted with JobID f78bef5723e745bb6b24e38e52f63ca5
```
执行完上述命令后，我们可以在 WebUI 中看到正在运行的程序：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/build-first-flink-application-4.jpg?raw=true)

只需要在 netcat 控制台输入单词，就能在 Flink 的日志中看到每个单词的词频统计：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/build-first-flink-application-5.jpg?raw=true)

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/build-first-flink-application-6.jpg?raw=true)

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)
