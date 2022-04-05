---
layout: post
author: smartsi
title: Flink 旁路输出 SideOutputs
date: 2021-06-20 11:30:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-side-outputs
---

通常我们在处理数据的时候，有时候想对不同情况的数据进行不同的处理，那么就需要把数据流进行分流。



DataStream 操作除了生成主数据流之外，还可以额外生成任意数量的侧输出结果流。结果流中的数据类型不必与主数据流中的数据类型相匹配，并且不同侧输出流的类型也可以不同。当我们想要分割数据流时，此操作非常有用，否则我们只能复制数据流，然后从每个流中过滤掉我们不希望的数据。

Java:
```java
// this needs to be an anonymous inner class, so that we can analyze the type
OutputTag<String> outputTag = new OutputTag<String>("side-output") {};
```

注意 OutputTag 类型是根据侧输出流包含元素的类型定义的。

可以通过以下函数将数据发送到侧输出：
- [ProcessFunction](https://ci.apache.org/projects/flink/flink-docs-release-1.7/dev/stream/operators/process_function.html)
- CoProcessFunction
- [ProcessWindowFunction](https://ci.apache.org/projects/flink/flink-docs-release-1.7/dev/stream/operators/windows.html#processwindowfunction)
- ProcessAllWindowFunction

我们可以使用 Context 参数（在上述函数中向用户公开）将数据发送到 OutputTag 标识的侧输出中。下面是从 ProcessFunction 发出侧输出数据的示例：
Java:
```java
DataStream<Integer> input = ...;

final OutputTag<String> outputTag = new OutputTag<String>("side-output"){};

SingleOutputStreamOperator<Integer> mainDataStream = input
.process(new ProcessFunction<Integer, Integer>() {
  @Override
  public void processElement(Integer value, Context ctx, Collector<Integer> out) throws Exception {
    // 发送数据到常规输出
    out.collect(value);
    // 发送数据到侧输出
    ctx.output(outputTag, "sideout-" + String.valueOf(value));
  }
});
```
Scala:
```scala
val input: DataStream[Int] = ...
val outputTag = OutputTag[String]("side-output")

val mainDataStream = input
  .process(new ProcessFunction[Int, Int] {
    override def processElement(
        value: Int,
        ctx: ProcessFunction[Int, Int]#Context,
        out: Collector[Int]): Unit = {
      // emit data to regular output
      out.collect(value)

      // emit data to side output
      ctx.output(outputTag, "sideout-" + String.valueOf(value))
    }
  })
```
要检索侧输出流，我们要对 DataStream 操作结果调用 `getSideOutput（OutputTag）` 函数。这为我们提供一个输入到侧输出流结果的 DataStream：
Java:
```java
final OutputTag<String> outputTag = new OutputTag<String>("side-output"){};

SingleOutputStreamOperator<Integer> mainDataStream = ...;

DataStream<String> sideOutputStream = mainDataStream.getSideOutput(outputTag);
```

```
MainStream > 1
OddSideOutputStream > 1
MainStream > 2
EvenSideOutputStream > 2
MainStream > 3
OddSideOutputStream > 3
MainStream > 4
EvenSideOutputStream > 4
MainStream > 5
OddSideOutputStream > 5
MainStream > 6
EvenSideOutputStream > 6
```




> 原文：[Side Outputs](https://ci.apache.org/projects/flink/flink-docs-stable/dev/stream/side_output.html)
