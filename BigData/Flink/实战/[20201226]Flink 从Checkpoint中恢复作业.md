---
layout: post
author: smartsi
title: Flink 从Checkpoint中恢复作业
date: 2020-12-26 18:26:17
tags:
  - Flink

categories: Flink
permalink: flink-restore-job-from-checkpoint
---

> Flink 1.11 版本

## 1. 配置

如果我们的任务已经执行很长时间，突然遇到故障停止，那么中间过程处理结果就会全部丢失，重启后需要重新从上一次开始的位置消费，这会花费我们很长的时间。这种结局显示我们不能接受，我们希望的是作业在故障失败重启后能保留之前的状态并能从失败的位置继续消费。可以通过如下配置保存处理状态：
```java
final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 开启Checkpoint
env.enableCheckpointing(1000);
// 设置状态后端
env.setStateBackend(new FsStateBackend("hdfs://localhost:9000/flink/checkpoint"));
env.getCheckpointConfig().setMinPauseBetweenCheckpoints(500);
env.getCheckpointConfig().setCheckpointTimeout(60000);
```
作业停止后 CheckPoint 数据默认会自动删除，所以需要如下配置来设置在作业失败被取消后 CheckPoint 数据不被删除：
```java
env.getCheckpointConfig().enableExternalizedCheckpoints(CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
```

## 2. 验证

我们使用经典的 WordCount 实例来验证从 Checkpoint 中恢复作业并能沿用之前的状态信息。为了模拟作业失败并能恢复，我们判断当我们输入是 "ERROR" 时，抛出异常迫使作业失败：
```java
public void flatMap(String value, Collector out) {
    // 失败信号
    if (Objects.equals(value, "ERROR")) {
        throw new RuntimeException("custom error flag, restart application");
    }
    ...
}
```
为了确保作业在失败后能自动恢复，我们设置了重启策略，失败后最多重启3次，每次重启间隔10s：
```java
env.setRestartStrategy(RestartStrategies.fixedDelayRestart(3, 10000));
```
我们看一下详细的代码：
```java
public class RestoreCheckpointExample {
    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        // 配置Checkpoint
        env.enableCheckpointing(1000);
        env.setStateBackend(new FsStateBackend("hdfs://localhost:9000/flink/checkpoint"));
        env.getCheckpointConfig().setMinPauseBetweenCheckpoints(500);
        env.getCheckpointConfig().setCheckpointTimeout(60000);
        env.getCheckpointConfig().enableExternalizedCheckpoints(CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
        // 配置失败重启策略：失败后最多重启3次 每次重启间隔10s
        env.setRestartStrategy(RestartStrategies.fixedDelayRestart(3, 10000));

        DataStream<String> source = env.socketTextStream("localhost", 9100, "\n")
                .name("MySourceFunction");
        DataStream<Tuple2<String, Integer>> wordsCount = source.flatMap(new FlatMapFunction<String, Tuple2<String, Integer>>() {
            @Override
            public void flatMap(String value, Collector out) {
                // 失败信号
                if (Objects.equals(value, "ERROR")) {
                    throw new RuntimeException("custom error flag, restart application");
                }
                // 拆分单词
                for (String word : value.split("\\s")) {
                    out.collect(Tuple2.of(word, 1));
                }
            }
        }).name("MyFlatMapFunction");

        DataStream<Tuple2<String, Integer>> windowCount = wordsCount
                .keyBy(new KeySelector<Tuple2<String, Integer>, String>() {
                    @Override
                    public String getKey(Tuple2<String, Integer> tuple) throws Exception {
                        return tuple.f0;
                    }
                })
                .sum(1).name("MySumFunction");

        windowCount.print().setParallelism(1).name("MyPrintFunction");
        env.execute("RestoreCheckpointExample");
    }
}
```
> [代码地址](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/stream/state/checkpoint/RestoreCheckpointExample.java)

下面我们具体操作进行验证。首先启动一个 nc 服务：
```
wy:opt wy$ nc -lk 9100
```
> 端口号为：9100

然后启动 RestoreCheckpointExample 作业：
```
wy:~ wy$ flink run -c com.flink.example.stream.state.checkpoint.RestoreCheckpointExample  ~/study/code/data-example/flink-example/target/flink-example-1.0.jar
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-restore-job-from-checkpoint-2.jpg?raw=true)

下表是从 nc 服务输出测试数据，从 Flink Web 页面输出结果数据的详细信息：

| 序号 | 输入| 输出 | 备注 |
| :------------- | :------------- | :------------- | :------------- |
| 1       | a       | (a,1) |
| 2       | a       | (a,2) |
| 3       | b       | (b,1) |
| 4       | ERROR   |  | 作业重启 |
| 5       | b       | (b,2) |
| 6       | a       | (a,3) |
| 7       | ERROR   |  | 作业重启 |
| 8       | a       | (a,4) |
| 9       | ERROR   |  | 作业重启 |
| 10      | b       | (b,3) |
| 11      | ERROR   |  | 作业失败 |

从上面信息可以看出作业恢复后，计算结果也是基于作业失败前保存的状态上计算的。我们设置最多可以重启三次，当我们第四次输入 "ERROR" 数据时，程序彻底失败。

## 3. 作业状态变化

发送 ERROR 信号后，flatMap 算子抛出异常，由 RUNNING 状态切换为 FAILED，导致作业被取消：
```java
2020-12-26 20:48:12,967 WARN  org.apache.flink.runtime.taskmanager.Task                    [] - Source: MySourceFunction -> MyFlatMapFunction (1/1) (be8abffb0f6815889929dc9b605b7ae5) switched from RUNNING to FAILED.
java.lang.RuntimeException: custom error flag, restart application
	at com.flink.example.stream.state.checkpoint.RestoreCheckpointExample$1.flatMap(RestoreCheckpointExample.java:39) ~[blob_p-353721c11ae1acd403dc8be3b663e9a60854d5c3-b6237955a73f418e6d7b272281b64594:?]
	at com.flink.example.stream.state.checkpoint.RestoreCheckpointExample$1.flatMap(RestoreCheckpointExample.java:34) ~[blob_p-353721c11ae1acd403dc8be3b663e9a60854d5c3-b6237955a73f418e6d7b272281b64594:?]
	at org.apache.flink.streaming.api.operators.StreamFlatMap.processElement(StreamFlatMap.java:50) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.OperatorChain$CopyingChainingOutput.pushToOperator(OperatorChain.java:717) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.OperatorChain$CopyingChainingOutput.collect(OperatorChain.java:692) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.OperatorChain$CopyingChainingOutput.collect(OperatorChain.java:672) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.api.operators.CountingOutput.collect(CountingOutput.java:52) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.api.operators.CountingOutput.collect(CountingOutput.java:30) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.api.operators.StreamSourceContexts$NonTimestampContext.collect(StreamSourceContexts.java:104) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.api.functions.source.SocketTextStreamFunction.run(SocketTextStreamFunction.java:111) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.api.operators.StreamSource.run(StreamSource.java:100) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.api.operators.StreamSource.run(StreamSource.java:63) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
	at org.apache.flink.streaming.runtime.tasks.SourceStreamTask$LegacySourceFunctionThread.run(SourceStreamTask.java:213) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
2020-12-26 20:48:12,978 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Attempting to cancel task MySumFunction -> Sink: MyPrintFunction (1/1) (d464321ae464046684fd28d37bdcc3d7).
2020-12-26 20:48:12,978 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - MySumFunction -> Sink: MyPrintFunction (1/1) (d464321ae464046684fd28d37bdcc3d7) switched from RUNNING to CANCELING.
...
2020-12-26 20:48:12,979 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - MySumFunction -> Sink: MyPrintFunction (1/1) (d464321ae464046684fd28d37bdcc3d7) switched from CANCELING to CANCELED.
```
由于我们设置了重启策略，重启间隔为10s，所以作业在10s之后重启，经过 CREATED -> DEPLOYING -> RUNNING 状态，作业被重启：
```java
2020-12-26 20:48:22,997 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Source: MySourceFunction -> MyFlatMapFunction (1/1) (223b777dfc69013852e9ab37d3cc078e) switched from CREATED to DEPLOYING.
...
2020-12-26 20:48:22,998 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Source: MySourceFunction -> MyFlatMapFunction (1/1) (223b777dfc69013852e9ab37d3cc078e) switched from DEPLOYING to RUNNING.
2020-12-26 20:48:22,999 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - MySumFunction -> Sink: MyPrintFunction (1/1) (53e45aa6b16f0b82d1bde8325f0cfbaf) switched from CREATED to DEPLOYING.
...
2020-12-26 20:48:23,000 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - MySumFunction -> Sink: MyPrintFunction (1/1) (53e45aa6b16f0b82d1bde8325f0cfbaf) switched from DEPLOYING to RUNNING.
```
由于我们设置了最多重启三次，所以第四次发出 ERROR 信号后，作业彻底失败：
```java
2020-12-26 21:05:29,294 WARN  org.apache.flink.runtime.taskmanager.Task                    [] - Source: MySourceFunction -> MyFlatMapFunction (1/1) (223b777dfc69013852e9ab37d3cc078e) switched from RUNNING to FAILED.
java.lang.RuntimeException: custom error flag, restart application
	at com.flink.example.stream.state.checkpoint.RestoreCheckpointExample$1.flatMap(RestoreCheckpointExample.java:39) ~[blob_p-353721c11ae1acd403dc8be3b663e9a60854d5c3-b6237955a73f418e6d7b272281b64594:?]
	at com.flink.example.stream.state.checkpoint.RestoreCheckpointExample$1.flatMap(RestoreCheckpointExample.java:34) ~[blob_p-353721c11ae1acd403dc8be3b663e9a60854d5c3-b6237955a73f418e6d7b272281b64594:?]
	at org.apache.flink.streaming.api.operators.StreamFlatMap.processElement(StreamFlatMap.java:50) ~[flink-dist_2.12-1.11.2.jar:1.11.2]
...
2020-12-26 21:05:29,332 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - Attempting to cancel task MySumFunction -> Sink: MyPrintFunction (1/1) (53e45aa6b16f0b82d1bde8325f0cfbaf).
2020-12-26 21:05:29,332 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - MySumFunction -> Sink: MyPrintFunction (1/1) (53e45aa6b16f0b82d1bde8325f0cfbaf) switched from RUNNING to CANCELING.
...
2020-12-26 21:05:29,334 INFO  org.apache.flink.runtime.taskmanager.Task                    [] - MySumFunction -> Sink: MyPrintFunction (1/1) (53e45aa6b16f0b82d1bde8325f0cfbaf) switched from CANCELING to CANCELED.
...
2020-12-26 21:05:29,353 INFO  org.apache.flink.runtime.taskexecutor.DefaultJobLeaderService [] - Remove job a78621726e80e5bde6f936a177f0d052 from job leader monitoring.
2020-12-26 21:05:29,353 INFO  org.apache.flink.runtime.taskexecutor.TaskExecutor           [] - Close JobManager connection for job a78621726e80e5bde6f936a177f0d052.
```

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-restore-job-from-checkpoint-1.jpg?raw=true)


欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)
