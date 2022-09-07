---
layout: post
author: smartsi
title: Flink 侧输出流 Side Output
date: 2022-09-07 11:30:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-side-outputs
---

> Flink 1.13.5

大多数 DataStream API 都只有一个输出，即只能生成一条某种数据类型的结果流。之前版本只有 [Split](https://smartsi.blog.csdn.net/article/details/126737446?spm=1001.2014.3001.5502) 算子可以将一条流拆成多条类型相同的流，由于性能和逻辑的问题在 Flink 1.12.0 被删除。官方提供的推荐方案是使用处理函数提供的侧输出 Side Output 实现同一个函数输出多条数据流。

Side Output 除了生成主数据流之外，还可以额外生成任意数量的侧输出流。侧输出流中的数据类型不必与主数据流中的数据类型相匹配，并且不同侧输出流的类型也可以不同。当我们想要分割数据流时，此操作非常有用，否则我们只能复制数据流，然后从每个流中过滤掉我们不希望的数据。

Side Output 不只是可以用来拆分数据流，还可以在窗口计算时处理延迟数据。使用 Side Output 将迟到的数据重定向到另一个数据流中，这样就可以对他们进行后续处理或者通过 Sink 将数据输出到外部系统。后续会在如何处理窗口中迟到数据时具体讲解。

要使用 Side Output 的话，你首先需要做的是定义一个 OutputTag 来标识 Side Output，表示是要收集哪种类型的数据。如果是要收集多种类型的数据，那么就需要定义多种 OutputTag。例如我们要将整数数据流拆分偶数流和奇数流，那么就需要定义2个 OutputTag，如下所示：
```java
OutputTag<String> oddOutputTag = new OutputTag<String>("ODD"){};
OutputTag<Long> evenOutputTag = new OutputTag<Long>("EVEN"){};
```
> 这里类型不一致，主要是为了验证不同侧输出流可以输出不同类型的数据。OutputTag 类型是根据侧输出流包含元素的类型定义的。

要将数据输出都侧输出流中，需要与如下处理函数配合使用：
- ProcessFunction（1.3.x）
- KeyedProcessFunction（1.8.x）
- CoProcessFunction（1.4.x）
- KeyedCoProcessFunction（1.9.x）
- ProcessWindowFunction（1.4.x）
- ProcessAllWindowFunction（1.4.x）

然后通过处理函数中的 Context 上下文将数据发送到 OutputTag 标识的侧输出中：
```java
//输入数据源
DataStreamSource<Integer> source = env.fromElements(1, 2, 3, 4, 5, 6, 7, 8);
// 拆分偶数流和奇数流
SingleOutputStreamOperator<Integer> mainStream = source.process(new ProcessFunction<Integer, Integer>() {
    @Override
    public void processElement(Integer num, Context ctx, Collector<Integer> out) throws Exception {
        // 主输出
        out.collect(num);
        // 旁路输出 可以输出不同的数据类型
        if (num % 2 != 0) {
            // 奇数输出
            ctx.output(oddOutputTag, "O" + num);
        } else {
            // 偶数输出
            ctx.output(evenOutputTag, Long.valueOf(num));
        }
    }
});
```
既然上面我们已经将不同类型的数据进行放到不同的 OutputTag 里面了，那么我们该如何去获取呢？可以使用 getSideOutput 方法来获取不同 OutputTag 的数据：
```java
// 主链路
mainStream.print("ALL");
// 旁路输出 奇数
DataStream<String> oddStream = mainStream.getSideOutput(oddOutputTag);
oddStream.print("ODD");
// 旁路输出 偶数
DataStream<Long> evenStream = mainStream.getSideOutput(evenOutputTag);
evenStream.print("EVEN");
```

实际效果如下：
```
ALL> 1
ODD> O-1
ALL> 2
EVEN> 2
ALL> 3
ODD> O-3
ALL> 4
EVEN> 4
ALL> 5
ODD> O-5
ALL> 6
EVEN> 6
ALL> 7
ODD> O-7
ALL> 8
EVEN> 8
```
