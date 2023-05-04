---
layout: post
author: sjf0115
title: Flink SQL No operators defined in streaming topology. Cannot execute
date: 2022-04-10 22:34:01
tags:
  - Flink

categories: Flink
permalink: flink-no-operators-defined-in-streaming-topology
---

## 1. 现象

在执行如下 Flink SQL 程序时：
```java
tableEnv.executeSql("INSERT INTO print_table_sink\n" +
    "SELECT name, SUM(score) AS score_sum\n" +
    "FROM input_table\n" +
    "GROUP BY name");
env.execute();
```
抛出如下异常：
```java
Exception in thread "main" java.lang.IllegalStateException: No operators defined in streaming topology. Cannot execute.
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.getStreamGraphGenerator(StreamExecutionEnvironment.java:2019)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.getStreamGraph(StreamExecutionEnvironment.java:2010)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.getStreamGraph(StreamExecutionEnvironment.java:1995)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1834)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.execute(StreamExecutionEnvironment.java:1817)
	at com.flink.example.table.table.TableOutputExample.main(TableOutputExample.java:63)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
```

## 2. 解决方案

TableEnvironment.executeSql() 和 StatementSet.execute() 方法是知己执行 SQL 作业(异步提交作业)，无需再调用 StreamExecutionEnvironment.execute() 方法。如果将 Table 转换为 AppendedStream/RetractStream/DataStream 时（通过StreamExecutionEnvironment#toAppendStream/toRetractStream/toChangelogStream/toDataStream），就必须使用 StreamExecutionEnvironment#execute() 来触发作业执行。

所以解决方案是删除 `env.execute();` 即可。

https://mp.weixin.qq.com/s/pB7cqD7b8RUEfc9OJ5AMgA
