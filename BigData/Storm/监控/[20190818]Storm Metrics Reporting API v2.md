---
layout: post
author: sjf0115
title: Storm Metrics Reporting API v2
date: 2019-08-18 21:04:01
tags:
  - Storm
  - Storm 监控

categories: Storm
permalink: metrics-reporting-api-v2-in-storm
---

Apache Storm 1.2 版本引入了一个新的指标系统，用于报告内部统计信息（例如，`acked`，`failed`，`emitted`，`transferred`，`disruptor queue metrics`等）以及新的用户自定义指标API。

新的指标系统基于 [Dropwizard Metrics](https://metrics.dropwizard.io/4.0.0/) 实现。

### 1. 用户自定义Metrics

为了允许用户自定义指标，`TopologyContext` 类中添加了如下方法，其实例会传递给 spout 的 `open()` 方法和 bolt 的 `prepare()` 方法：
```java
public Timer registerTimer(String name)
public Histogram registerHistogram(String name)
public Meter registerMeter(String name)
public Counter registerCounter(String name)
public Gauge registerGauge(String name, Gauge gauge)
```

API 文档: [Timer](https://metrics.dropwizard.io/4.0.0/apidocs/com/codahale/metrics/Timer.html), [Histogram](https://metrics.dropwizard.io/4.0.0/apidocs/com/codahale/metrics/Histogram.html), [Meter](https://metrics.dropwizard.io/4.0.0/apidocs/com/codahale/metrics/Meter.html), [Counter](https://metrics.dropwizard.io/4.0.0/apidocs/com/codahale/metrics/Counter.html), [Gauge](https://metrics.dropwizard.io/4.0.0/apidocs/com/codahale/metrics/Gauge.html)。

这些方法都有一个 `name` 参数作为标识符。注册指标时，Storm 会添加其他信息，如主机名，端口，拓扑ID等，以形成唯一的指标标识符。例如，我们如下注册名为 `myCounter` 的指标：
```java
Counter myCounter = topologyContext.registerCounter("myCounter");
```
发送给指标报告系统的最终名称如下：
```
storm.topology.{topology ID}.{hostname}.{component ID}.{task ID}.{worker port}-myCounter
```
这些额外的信息可以确跨集群的组件实例指标有唯一标识。

> 为了确保可以正确解析指标名称。组件名称中的字符 `.` 会被替换为 `_` 字符。例如，主机名 `storm.example.com` 会在指标名称中显示为 `storm_example_com`。

### 2. Example: Tuple Counter Bolt

以下示例是一个简单的 bolt 实现，它会报告每个 bolt 接收到的累计运行元组：
```java
public class TupleCountingBolt extends BaseRichBolt {
    private Counter tupleCounter;
    @Override
    public void prepare(Map stormConf, TopologyContext context, OutputCollector collector) {
        this.tupleCounter = context.registerCounter("tupleCount");
    }

    @Override
    public void execute(Tuple input) {
        this.tupleCounter.inc();
    }
}
```
### 3. 指标发送器配置

如果要使指标有用，必须报告，换句话说，必须把指标发送到可以消费和分析的地方。最简单的是将它们写入日志文件，或者将它们发送到时间序列数据库，或通过 JMX 公开它们。

从 Storm 1.2.0 版本开始，支持以下指标报告器:
- Console Reporter(`org.apache.storm.metrics2.reporters.ConsoleStormReporter`): 将指标发送给System.out。
- CSV Reporter(`org.apache.storm.metrics2.reporters.CsvReporter`): 将指标发送给CSV文件。
- Graphite Reporter(`org.apache.storm.metrics2.reporters.GraphiteStormReporter`): 向 Graphite 服务器发送指标。
- JMX Reporter(`org.apache.storm.metrics2.reporters.JmxStormReporter`): 通过 JMX 公开指标。

指标发送者在 `storm.yaml` 文件中配置。默认情况下，Storm 会收集指标但不会'发送'或将收集的指标发送到任何地方。要启用指标发送，请将 `storm.metrics.reporters` 部分添加到 `storm.yaml` 并配置一个或多个 reporters。

如下示例配置了两个指标发送者：`Graphite Reporter` 和 `Console Reporter`：
```xml
storm.metrics.reporters:
  # Graphite Reporter
  - class: "org.apache.storm.metrics2.reporters.GraphiteStormReporter"
    daemons:
        - "supervisor"
        - "nimbus"
        - "worker"
    report.period: 60
    report.period.units: "SECONDS"
    graphite.host: "localhost"
    graphite.port: 2003

  # Console Reporter
  - class: "org.apache.storm.metrics2.reporters.ConsoleStormReporter"
    daemons:
        - "worker"
    report.period: 10
    report.period.units: "SECONDS"
    filter:
        class: "org.apache.storm.metrics2.filters.RegexFilter"
        expression: ".*my_component.*emitted.*"
```

每个 reporter 部分都以一个 `class` 参数开头，该参数表示 reporter 实现的完全限定类名。`daemons` 部分决定 reporter 应用于哪些守护进程(在示例中，Graphite Reporter 配置发送来自所有 Storm 守护进程的指标，而 Console Reporter 仅发送 `worker` 和 `topology` 指标）。

很多 reporter 实现都是定时的，这意味着他们定时发送指标。发送间隔由 `report.period` 和 `report.period.units` 参数确定。

还可以使用可选的过滤器配置 reporter，以决定发送哪些指标。Storm 包含 `org.apache.storm.metrics2.filters.RegexFilter` 过滤器，该过滤器使用正则表达式来决定发送哪些指标。可以通过实现 `org.apache.storm.metrics2.filters.StormMetricFilter` 接口来创建自定义过滤器：
```java
public interface StormMetricsFilter extends MetricFilter {

    /**
     * Called after the filter is instantiated.
     * @param config A map of the properties from the 'filter' section of the reporter configuration.
     */
    void prepare(Map<String, Object> config);

   /**
    *  Returns true if the given metric should be reported.
    */
    boolean matches(String name, Metric metric);
}
```

英译对照:
- metric: 指标

原文:[Metrics Reporting API v2](https://storm.apache.org/releases/2.0.0/metrics_v2.html)
