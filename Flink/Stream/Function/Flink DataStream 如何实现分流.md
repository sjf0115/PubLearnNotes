---
layout: post
author: smartsi
title: Flink DataStream 如何实现分流
date: 2022-09-07 11:30:17
tags:
  - Flink

categories: Flink
permalink: flink-stream-split-data-stream
---


大多数 DataStream API 都只有一个输出，即只能生成一条某种数据类型的结果流。

## 1. Split

之前版本只有 [Split](https://smartsi.blog.csdn.net/article/details/126737446?spm=1001.2014.3001.5502) 算子可以将一条流拆成多条类型相同的流，由于性能和逻辑的问题在 Flink 1.12.0 被删除。


## 2. Filter


## 3. Side Output

官方提供的推荐方案是使用处理函数提供的侧输出 Side Output 实现同一个函数输出多条数据流。
