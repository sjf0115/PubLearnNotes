---
layout: post
author: sjf0115
title: Flink 1.11+ No ExecutorFactory found to execute the application
date: 2022-04-09 22:34:01
tags:
  - Flink

categories: Flink
permalink: flink-no-executorfactory-found-to-execute-the-application
---

## 1. 现象

在 idea 中本地运行 Flink 程序时，抛如下异常：
```java
Exception in thread "main" java.lang.IllegalStateException: No ExecutorFactory found to execute the application.
	at org.apache.flink.core.execution.DefaultExecutorServiceLoader.getExecutorFactory(DefaultExecutorServiceLoader.java:84)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.executeAsync(StreamExecutionEnvironment.java:1801)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1711)
	at org.apache.flink.streaming.api.environment.LocalStreamEnvironment.execute(LocalStreamEnvironment.java:74)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1697)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1679)
	at com.flink.example.stream.state.savepoint.SavepointExample.main(SavepointExample.java:36)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
```
## 2. 分析

从 Flink 1.11.0 版本开始，flink-streaming-java 模块不再依赖 flink-clients。如果我们的项目对 flink-clients 有依赖，需要手动添加 flink-clients 依赖项。

> 具体参阅:[Reversed dependency from flink-streaming-java to flink-client (FLINK-15090)](https://nightlies.apache.org/flink/flink-docs-release-1.11/release-notes/flink-1.11.html#reversed-dependency-from-flink-streaming-java-to-flink-client-flink-15090)

## 3. 解决方案

究其原因是缺少依赖，1.11+ 版本需要手动引入 flink-clients 依赖：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-clients_${scala.binary.version}</artifactId>
    <version>${flink.version}</version>
</dependency>
```
