---
layout: post
author: sjf0115
title: Flink 内部原理之StreamGraph
date: 2018-03-06 19:40:01
tags:
  - Flink
  - Flink 内部原理

categories: Flink
permalink: flink-internals-how-to-build-streamgraph
---

本文将主要介绍 Flink 是如何根据用户用 Stream API 编写的程序，构造出一个代表拓扑结构的 `StreamGraph`。

`StreamGraph` 相关的代码主要在 `org.apache.flink.streaming.api.graph` 包中。构造 `StreamGraph` 的入口函数是 `StreamGraphGenerator.generate(env, transformations)`。该函数会由触发程序执行的方法 `StreamExecutionEnvironment.execute()` 调用到。也就是说 `StreamGraph` 是在 `Client` 端构造的，这也意味着我们可以在本地通过调试观察 `StreamGraph` 的构造过程。

### 1. Transformation

`StreamGraphGenerator.generate` 的一个关键的参数是 `List<StreamTransformation<?>>`。`StreamTransformation` 代表了从一个或多个 `DataStream` 生成新 `DataStream` 的操作。`DataStream` 的底层其实就是一个 `StreamTransformation`，描述了这个 `DataStream` 是怎么来的。

`StreamTransformation` 的类图如下图所示：

![]()

`DataStream` 上常见的 `transformation` 有 `map`、`flatmap`、`filter`等（见 [DataStream Transformation](http://smartsi.club/2018/02/28/flink-stream-operators-overall/#1-DataStream-Transformations)了解更多）。这些 `transformation` 会构造出一棵 `StreamTransformation` 树，通过这棵树转换成 `StreamGraph`。比如 `DataStream.map` 源码如下，其中 `SingleOutputStreamOperator` 为 `DataStream` 的子类：


```java
// 在DataStream上应用 Map 转换。该转换为 DataStream 的每个元素调用 MapFunction，并返回一个元素
public <R> SingleOutputStreamOperator<R> map(MapFunction<T, R> mapper) {

		TypeInformation<R> outType = TypeExtractor.getMapReturnTypes(clean(mapper), getType(),
				Utils.getCallLocationName(), true);

		return transform("Map", outType, new StreamMap<>(clean(mapper)));
}
```








































原文：http://wuchong.me/blog/2016/05/04/flink-internal-how-to-build-streamgraph/
