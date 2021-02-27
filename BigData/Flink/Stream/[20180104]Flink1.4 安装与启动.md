---
layout: post
author: sjf0115
title: Flink1.4 安装与启动
date: 2018-01-04 08:54:01
tags:
  - Flink
  - Flink 基础

categories: Flink
permalink: flink-how-to-install-and-run
---

### 1. 下载

Flink 可以运行在 Linux, Mac OS X和Windows上。为了运行Flink, 唯一的要求是必须在Java 7.x (或者更高版本)上安装。Windows 用户, 请查看 Flink在Windows上的安装指南。

你可以使用以下命令检查Java当前运行的版本：
```
java -version
```
如果你安装的是Java 8，输出结果类似于如下:
```
java version "1.8.0_91"
Java(TM) SE Runtime Environment (build 1.8.0_91-b14)
Java HotSpot(TM) 64-Bit Server VM (build 25.91-b14, mixed mode)
```
从下载页下载一个二进制的包，你可以选择任何你喜欢的Hadoop/Scala组合方式。如果你只是打算使用本地文件系统，那么可以使用任何版本的Hadoop。进入下载目录，解压下载的压缩包:
```
xiaosi@yoona:~$ tar -zxvf flink-1.3.2-bin-hadoop27-scala_2.11.tgz -C opt/
flink-1.3.2/
flink-1.3.2/opt/
flink-1.3.2/opt/flink-cep_2.11-1.3.2.jar
flink-1.3.2/opt/flink-metrics-datadog-1.3.2.jar
flink-1.3.2/opt/flink-metrics-statsd-1.3.2.jar
flink-1.3.2/opt/flink-gelly_2.11-1.3.2.jar
flink-1.3.2/opt/flink-metrics-dropwizard-1.3.2.jar
flink-1.3.2/opt/flink-gelly-scala_2.11-1.3.2.jar
flink-1.3.2/opt/flink-metrics-ganglia-1.3.2.jar
flink-1.3.2/opt/flink-cep-scala_2.11-1.3.2.jar
flink-1.3.2/opt/flink-table_2.11-1.3.2.jar
flink-1.3.2/opt/flink-ml_2.11-1.3.2.jar
flink-1.3.2/opt/flink-metrics-graphite-1.3.2.jar
flink-1.3.2/lib/
...
```
### 2. 启动本地集群

使用如下命令启动Flink：
```
xiaosi@yoona:~/opt/flink-1.3.2$ ./bin/start-local.sh
Starting jobmanager daemon on host yoona.
```
通过访问 http://localhost:8081 检查JobManager网页,确保所有组件都启动并已运行。网页会显示一个有效的TaskManager实例。

![img](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%AE%89%E8%A3%85%E4%B8%8E%E5%90%AF%E5%8A%A8-1.png?raw=true)

你也可以通过检查日志目录里的日志文件来验证系统是否已经运行:
```
xiaosi@yoona:~/opt/flink-1.3.2/log$ cat flink-xiaosi-jobmanager-0-yoona.log | less
2017-10-16 14:42:10,972 INFO  org.apache.flink.runtime.jobmanager.JobManager                -  Starting JobManager (Version: 1.3.2, Rev:0399bee, Date:03.08.2017 @ 10:23:11 UTC)
...
2017-10-16 14:42:11,109 INFO  org.apache.flink.runtime.jobmanager.JobManager                - Starting JobManager without high-availability
2017-10-16 14:42:11,111 INFO  org.apache.flink.runtime.jobmanager.JobManager                - Starting JobManager on localhost:6123 with execution mode LOCAL
...
2017-10-16 14:42:11,915 INFO  org.apache.flink.runtime.jobmanager.JobManager                - Starting JobManager web frontend
...
2017-10-16 14:42:13,941 INFO  org.apache.flink.runtime.instance.InstanceManager             - Registered TaskManager at localhost (akka://flink/user/taskmanager) as 0df4d4ebd25ffec4878906726c29f88c. Current number of registered hosts is 1. Current number of alive task slots is 1.
...

```

### 3. Example Code

你可以在GitHub上找到SocketWindowWordCount例子的完整代码，有[Java](https://github.com/apache/flink/blob/master/flink-examples/flink-examples-streaming/src/main/java/org/apache/flink/streaming/examples/socket/SocketWindowWordCount.java)和[Scala](https://github.com/apache/flink/blob/master/flink-examples/flink-examples-streaming/src/main/scala/org/apache/flink/streaming/scala/examples/socket/SocketWindowWordCount.scala)两个版本。

Scala:
```scala
package org.apache.flink.streaming.scala.examples.socket

import org.apache.flink.api.java.utils.ParameterTool
import org.apache.flink.streaming.api.scala._
import org.apache.flink.streaming.api.windowing.time.Time

/**
 * Implements a streaming windowed version of the "WordCount" program.
 *
 * This program connects to a server socket and reads strings from the socket.
 * The easiest way to try this out is to open a text sever (at port 12345)
 * using the ''netcat'' tool via
 * {{{
 * nc -l 12345
 * }}}
 * and run this example with the hostname and the port as arguments..
 */
object SocketWindowWordCount {

  /** Main program method */
  def main(args: Array[String]) : Unit = {

    // the host and the port to connect to
    var hostname: String = "localhost"
    var port: Int = 0

    try {
      val params = ParameterTool.fromArgs(args)
      hostname = if (params.has("hostname")) params.get("hostname") else "localhost"
      port = params.getInt("port")
    } catch {
      case e: Exception => {
        System.err.println("No port specified. Please run 'SocketWindowWordCount " +
          "--hostname <hostname> --port <port>', where hostname (localhost by default) and port " +
          "is the address of the text server")
        System.err.println("To start a simple text server, run 'netcat -l <port>' " +
          "and type the input text into the command line")
        return
      }
    }

    // get the execution environment
    val env: StreamExecutionEnvironment = StreamExecutionEnvironment.getExecutionEnvironment

    // get input data by connecting to the socket
    val text: DataStream[String] = env.socketTextStream(hostname, port, '\n')

    // parse the data, group it, window it, and aggregate the counts
    val windowCounts = text
          .flatMap { w => w.split("\\s") }
          .map { w => WordWithCount(w, 1) }
          .keyBy("word")
          .timeWindow(Time.seconds(5))
          .sum("count")

    // print the results with a single thread, rather than in parallel
    windowCounts.print().setParallelism(1)

    env.execute("Socket Window WordCount")
  }

  /** Data type for words with count */
  case class WordWithCount(word: String, count: Long)
}
```
Java版本:
```java
package org.apache.flink.streaming.examples.socket;

import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.common.functions.ReduceFunction;
import org.apache.flink.api.java.utils.ParameterTool;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.util.Collector;

/**
 * Implements a streaming windowed version of the "WordCount" program.
 *
 * <p>This program connects to a server socket and reads strings from the socket.
 * The easiest way to try this out is to open a text server (at port 12345)
 * using the <i>netcat</i> tool via
 * <pre>
 * nc -l 12345
 * </pre>
 * and run this example with the hostname and the port as arguments.
 */
@SuppressWarnings("serial")
public class SocketWindowWordCount {

	public static void main(String[] args) throws Exception {

		// the host and the port to connect to
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

		// get the execution environment
		final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

		// get input data by connecting to the socket
		DataStream<String> text = env.socketTextStream(hostname, port, "\n");

		// parse the data, group it, window it, and aggregate the counts
		DataStream<WordWithCount> windowCounts = text

				.flatMap(new FlatMapFunction<String, WordWithCount>() {
					@Override
					public void flatMap(String value, Collector<WordWithCount> out) {
						for (String word : value.split("\\s")) {
							out.collect(new WordWithCount(word, 1L));
						}
					}
				})

				.keyBy("word")
				.timeWindow(Time.seconds(5))

				.reduce(new ReduceFunction<WordWithCount>() {
					@Override
					public WordWithCount reduce(WordWithCount a, WordWithCount b) {
						return new WordWithCount(a.word, a.count + b.count);
					}
				});

		// print the results with a single thread, rather than in parallel
		windowCounts.print().setParallelism(1);

		env.execute("Socket Window WordCount");
	}

	// ------------------------------------------------------------------------

	/**
	 * Data type for words with count.
	 */
	public static class WordWithCount {

		public String word;
		public long count;

		public WordWithCount() {}

		public WordWithCount(String word, long count) {
			this.word = word;
			this.count = count;
		}

		@Override
		public String toString() {
			return word + " : " + count;
		}
	}
}
```
### 4. 运行Example

现在, 我们可以运行Flink 应用程序。 这个例子将会从一个socket中读取一段文本，并且每隔5秒打印之前5秒内每个单词出现的个数。例如：
```
a tumbling window of processing time, as long as words are floating in.
```
(1) 首先,我们可以通过netcat命令来启动本地服务:
```
nc -l 9000
```
(2) 提交Flink程序:
```
xiaosi@yoona:~/opt/flink-1.3.2$ ./bin/flink run examples/streaming/SocketWindowWordCount.jar --port 9000
Cluster configuration: Standalone cluster with JobManager at localhost/127.0.0.1:6123
Using address localhost:6123 to connect to JobManager.
JobManager web interface address http://localhost:8081
Starting execution of program
Submitting job with JobID: a963626a1e09f7aeb0dc34412adfb801. Waiting for job completion.
Connected to JobManager at Actor[akka.tcp://flink@localhost:6123/user/jobmanager#941160871] with leader session id 00000000-0000-0000-0000-000000000000.
10/16/2017 15:12:26	Job execution switched to status RUNNING.
10/16/2017 15:12:26	Source: Socket Stream -> Flat Map(1/1) switched to SCHEDULED
10/16/2017 15:12:26	TriggerWindow(TumblingProcessingTimeWindows(5000), ReducingStateDescriptor{serializer=org.apache.flink.api.java.typeutils.runtime.PojoSerializer@37ff898e, reduceFunction=org.apache.flink.streaming.examples.socket.SocketWindowWordCount$1@4d15107f}, ProcessingTimeTrigger(), WindowedStream.reduce(WindowedStream.java:300)) -> Sink: Unnamed(1/1) switched to SCHEDULED
10/16/2017 15:12:26	Source: Socket Stream -> Flat Map(1/1) switched to DEPLOYING
10/16/2017 15:12:26	TriggerWindow(TumblingProcessingTimeWindows(5000), ReducingStateDescriptor{serializer=org.apache.flink.api.java.typeutils.runtime.PojoSerializer@37ff898e, reduceFunction=org.apache.flink.streaming.examples.socket.SocketWindowWordCount$1@4d15107f}, ProcessingTimeTrigger(), WindowedStream.reduce(WindowedStream.java:300)) -> Sink: Unnamed(1/1) switched to DEPLOYING
10/16/2017 15:12:26	Source: Socket Stream -> Flat Map(1/1) switched to RUNNING
10/16/2017 15:12:26	TriggerWindow(TumblingProcessingTimeWindows(5000), ReducingStateDescriptor{serializer=org.apache.flink.api.java.typeutils.runtime.PojoSerializer@37ff898e, reduceFunction=org.apache.flink.streaming.examples.socket.SocketWindowWordCount$1@4d15107f}, ProcessingTimeTrigger(), WindowedStream.reduce(WindowedStream.java:300)) -> Sink: Unnamed(1/1) switched to RUNNING
```
应用程序连接socket并等待输入，你可以通过web界面来验证任务期望的运行结果：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%AE%89%E8%A3%85%E4%B8%8E%E5%90%AF%E5%8A%A8-2.png?raw=true)

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Flink/Flink%20%E5%AE%89%E8%A3%85%E4%B8%8E%E5%90%AF%E5%8A%A8-3.png?raw=true)

单词的数量在5秒的时间窗口中进行累加（使用处理时间和tumbling窗口），并打印在stdout。监控JobManager的输出文件，并在nc写一些文本(回车一行就发送一行输入给Flink) :
```
xiaosi@yoona:~/opt/flink-1.3.2$  nc -l 9000
lorem ipsum
ipsum ipsum ipsum
bye
```
.out文件将在每个时间窗口截止之际打印每个单词的个数：
```
xiaosi@yoona:~/opt/flink-1.3.2$  tail -f log/flink-*-jobmanager-*.out
lorem : 1
bye : 1
ipsum : 4
```
使用以下命令来停止Flink:
```
 ./bin/stop-local.sh
```

阅读更多的[例子](https://ci.apache.org/projects/flink/flink-docs-release-1.3/examples/)来熟悉Flink的编程API。 当你完成这些，可以继续阅读[streaming指南](https://ci.apache.org/projects/flink/flink-docs-release-1.3/dev/datastream_api.html)。
