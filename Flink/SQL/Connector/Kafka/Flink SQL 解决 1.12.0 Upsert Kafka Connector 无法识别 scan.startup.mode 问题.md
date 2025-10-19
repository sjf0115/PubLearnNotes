## 1. 问题描述

在升级 Flink 1.12.0 以后 Upsert Kafka SQL Connector 不支持 `scan.startup.mode`、`scan.startup.specific-offsets`、`scan.startup.timestamp-millis`
，导致无法指定消费位点。

## 2. 原因分析

由于升级 Flink 1.12.0 以后 Upsert kafka 取消了这些参数，并在社区提问云邪后，得到的回复：

![](img-flink-sql-upsert-kafka-unsupported-options-1.png)

## 3. 解决方案

经过对源码分析在 KafkaDynamicTableFactory 支持的必填参数与可选参数如下所示:
```java
@Override
public Set<ConfigOption<?>> requiredOptions() {
    final Set<ConfigOption<?>> options = new HashSet<>();
    options.add(PROPS_BOOTSTRAP_SERVERS);
    return options;
}

@Override
public Set<ConfigOption<?>> optionalOptions() {
    final Set<ConfigOption<?>> options = new HashSet<>();
    options.add(FactoryUtil.FORMAT);
    options.add(KEY_FORMAT);
    options.add(KEY_FIELDS);
    options.add(KEY_FIELDS_PREFIX);
    options.add(VALUE_FORMAT);
    options.add(VALUE_FIELDS_INCLUDE);
    options.add(TOPIC);
    options.add(TOPIC_PATTERN);
    options.add(PROPS_GROUP_ID);
    options.add(SCAN_STARTUP_MODE);
    options.add(SCAN_STARTUP_SPECIFIC_OFFSETS);
    options.add(SCAN_TOPIC_PARTITION_DISCOVERY);
    options.add(SCAN_STARTUP_TIMESTAMP_MILLIS);
    options.add(SINK_PARTITIONER);
    options.add(SINK_SEMANTIC);
    options.add(SINK_PARALLELISM);
    return options;
}
```
必填参数：
- PROPS_BOOTSTRAP_SERVERS：`properties.bootstrap.servers`

可选参数：
- TOPIC：`topic`
- KEY_FORMAT：`key.format`
- VALUE_FORMAT：`value.format`
- KEY_FIELDS_PREFIX：`key.fields-prefix`
- VALUE_FIELDS_INCLUDE：`value.fields-include`
- FactoryUtil.SINK_PARALLELISM：`sink.parallelism`
- SINK_BUFFER_FLUSH_MAX_ROWS：`sink.buffer-flush.max-rows`
- SINK_BUFFER_FLUSH_INTERVAL：`sink.buffer-flush.interval`



而在 UpsertKafkaDynamicTableFactory 中必填参数与可选参数如下所示:
```java
@Override
public Set<ConfigOption<?>> requiredOptions() {
    final Set<ConfigOption<?>> options = new HashSet<>();
    options.add(PROPS_BOOTSTRAP_SERVERS);
    options.add(TOPIC);
    options.add(KEY_FORMAT);
    options.add(VALUE_FORMAT);
    return options;
}

@Override
public Set<ConfigOption<?>> optionalOptions() {
    final Set<ConfigOption<?>> options = new HashSet<>();
    options.add(KEY_FIELDS_PREFIX);
    options.add(VALUE_FIELDS_INCLUDE);
    options.add(FactoryUtil.SINK_PARALLELISM);
    options.add(SINK_BUFFER_FLUSH_INTERVAL);
    options.add(SINK_BUFFER_FLUSH_MAX_ROWS);
    return options;
}
```
必填参数：
- TOPIC：`topic`
- PROPS_BOOTSTRAP_SERVERS：`properties.bootstrap.servers`
- KEY_FORMAT：`key.format`
- VALUE_FORMAT：`value.format`

可选参数：
- KEY_FIELDS_PREFIX：`key.fields-prefix`
- VALUE_FIELDS_INCLUDE：`value.fields-include`
- FactoryUtil.SINK_PARALLELISM：`sink.parallelism`
- SINK_BUFFER_FLUSH_MAX_ROWS：`sink.buffer-flush.max-rows`
- SINK_BUFFER_FLUSH_INTERVAL：`sink.buffer-flush.interval`
