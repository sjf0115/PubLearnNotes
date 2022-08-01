

通过前面的文章骂我们已经了解了如何注册、定义指标并对其分组，那接下来可能想了解如何从外部系统访问他们。毕竟你收集指标的目的可能是要创建实时仪表盘或者将测量数据发送到另一个应用。可以在 conf/flink-conf.yaml 中配置一个或多个 Reporter，在 Flink 集群启动的过程中就会将这些 Reporter 配置加载到集群环境中，然后你就可以通过 Reporter 将指标发布到外部系统。

Flink 内部为 Reporter 提供了几种内置实现。目前 Flink 支持的 Repoter 有 JMX、Graphite、InfluxDB、Prometheus、PrometheusPushGateway、StatsD、Datadog、Slf4j，这些 Repoter 用户可以直接配置使用。

在 conf/flink-conf.yaml 与 Reporter 相关的配置项包含如下几个内容，其中 `name` 是用户自定义的 Reporter 名称，同时也可以使用 Reporter 名称来区分不同的 Reporter。下面具体看看与 Reporter 相关的几个配置项：
- `metrics.reporter.<name>.<config>`: 配置 name 对应 Reporter 的配置信息
- `metrics.reporter.<name>.class`: 配置 name 对应 Reporter 的 class 名称，对应类依赖库需要加载至 Flink 环境中，例如 JMX Reporter 对应的是 org.apache.flink.metrics.jmx.JMXReporter
- `metrics.reporter.<name>.factory.class`: 配置 name 对应 Reporter 的 factory class 名称
- `metrics.reporter.<name>.interval`: 配置 name 对应 Reporter 的汇报时间间隔，单位为秒
- `metrics.reporter.<name>.scope.delimiter`: 配置 name 对应 Reporter 的监控指标 scope 的分割符，默认为 metrics.scope.delimiter 对应的分隔符
- metrics.reporter.<name>.scope.variables.excludes:
- metrics.reporters: 可选配置选项，通过逗号分割多个 Reporter

所有的 Reporter 必须至少有 class 或 factory.class 配置项中的其中一个。具体使用哪个配置项取决于 Reporter 的实现。

```
metrics.reporters: my_jmx_reporter,my_other_reporter
# 第一个 Reporter：my_jmx_reporter
metrics.reporter.my_jmx_reporter.factory.class: org.apache.flink.metrics.jmx.JMXReporterFactory
metrics.reporter.my_jmx_reporter.port: 9020-9040
metrics.reporter.my_jmx_reporter.scope.variables.excludes:job_id;task_attempt_num
# 第二个 Reporter：my_other_reporter
metrics.reporter.my_other_reporter.class: org.apache.flink.metrics.graphite.GraphiteReporter
metrics.reporter.my_other_reporter.host: 192.168.1.1
metrics.reporter.my_other_reporter.port: 10000
```

## 1. JMX






参考：[Metric Reporters](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/deployment/metric_reporters/)
