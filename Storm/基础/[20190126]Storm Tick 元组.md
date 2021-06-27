---
layout: post
author: sjf0115
title: Storm Tick 元组
date: 2019-01-26 20:33:01
tags:
  - Storm
  - Storm 基础

categories: Storm
permalink: tick-tuple-in-storm
---

在某些情况下，Bolt 在执行某些操作之前需要将数据缓存几秒钟，例如每隔5秒清理一次缓存或在单个请求中将一批记录插入数据库。

Tick 元组是系统生成的（Storm生成的）元组，我们可以在每个 Bolt 级别配置它们。我们可以在编写 Bolt 时在代码中配置 Tick 元组。

我们需要在 Bolt 中覆盖以下方法以启用 Tick 元组：
```java
@Override
public Map<String, Object> getComponentConfiguration() {
  Config conf = new Config();
  int tickFrequencyInSeconds = 10;
  conf.put(Config.TOPOLOGY_TICK_TUPLE_FREQ_SECS, tickFrequencyInSeconds);
  return conf;
}
```
在上面的代码中，我们将 Tick 元组配置为10秒。现在，Storm 会每10秒钟生成一个 Tick 元组。

接下来创建 isTickTuple 方法来确定我们收到的元组是 Tick 元组还是正常元组：
```java
protected static boolean isTickTuple(Tuple tuple) {
    return tuple.getSourceComponent().equals(Constants.SYSTEM_COMPONENT_ID)
        && tuple.getSourceStreamId().equals(Constants.SYSTEM_TICK_STREAM_ID);
}
```
> Tick 元组会与你正在处理的其他正常元组混合在一起，所以需要我们判断元组的类型。

最后，在 Bolt 的 execute 方法中添加如下代码来判断元组的类型进行处理：
```java
@Override
public void execute(Tuple tuple, BasicOutputCollector collector) {
    try {
        if (isTickTuple(tuple)) {
           // do tick tuple
        }
        else {
          // do normal tuple
        }
        // do your bolt stuff
    } catch (Exception e) {
        LOG.error("Bolt execute error: {}", e);
        collector.reportError(e);
    }
}
```
现在你的 Bolt 每10秒就会收到一个 Tick 元组。

如果希望 Topology 中的每个 Bolt 都每隔一段时间做一些操作，那么可以定义一个 Topology 全局的 Tick，同样是设置 `Config.TOPOLOGY_TICK_TUPLE_FREQ_SECS`的值：
```java
Config conf = new Config();
conf.put(Config.TOPOLOGY_TICK_TUPLE_FREQ_SECS, 10);
```
