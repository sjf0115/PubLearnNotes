---
layout: post
author: sjf0115
title: Flink SQL Could not find any factory for identifier 'json' that implements 'org.apache.flink.table.factories.DeserializationFormatFactory'
date: 2022-04-09 22:34:01
tags:
  - Flink

categories: Flink
permalink: flink-could-not-find-any-factory-for-identifier-json
---

## 1. 现象

在运行 Flink SQL [程序]()时，抛出如下异常：
```java
Exception in thread "main" org.apache.flink.table.api.ValidationException: Unable to create a source for reading table 'default_catalog.default_database.kafka_source_table'.

Table options are:

'connector'='kafka'
'format'='json'
'properties.bootstrap.servers'='localhost:9092'
'properties.group.id'='kafka-table-descriptor'
'scan.startup.mode'='earliest-offset'
'topic'='word'
	at org.apache.flink.table.factories.FactoryUtil.createTableSource(FactoryUtil.java:150)
	at org.apache.flink.table.planner.plan.schema.CatalogSourceTable.createDynamicTableSource(CatalogSourceTable.java:116)
	at org.apache.flink.table.planner.plan.schema.CatalogSourceTable.toRel(CatalogSourceTable.java:82)
	at org.apache.calcite.rel.core.RelFactories$TableScanFactoryImpl.createScan(RelFactories.java:495)
	at org.apache.calcite.tools.RelBuilder.scan(RelBuilder.java:1099)
	at org.apache.calcite.tools.RelBuilder.scan(RelBuilder.java:1123)
  ...
	at org.apache.flink.table.planner.delegation.PlannerBase.translate(PlannerBase.scala:182)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.toStreamInternal(StreamTableEnvironmentImpl.java:437)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.toStreamInternal(StreamTableEnvironmentImpl.java:432)
	at org.apache.flink.table.api.bridge.java.internal.StreamTableEnvironmentImpl.toChangelogStream(StreamTableEnvironmentImpl.java:366)
	at com.flink.example.table.connectors.KafkaTableExample.main(KafkaTableExample.java:57)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
Caused by: org.apache.flink.table.api.ValidationException: Could not find any factory for identifier 'json' that implements 'org.apache.flink.table.factories.DeserializationFormatFactory' in the classpath.

Available factory identifiers are:

raw
	at org.apache.flink.table.factories.FactoryUtil.discoverFactory(FactoryUtil.java:399)
	at org.apache.flink.table.factories.FactoryUtil$TableFactoryHelper.discoverOptionalFormatFactory(FactoryUtil.java:890)
	at org.apache.flink.table.factories.FactoryUtil$TableFactoryHelper.discoverOptionalDecodingFormat(FactoryUtil.java:823)
	at org.apache.flink.streaming.connectors.kafka.table.KafkaDynamicTableFactory.getValueDecodingFormat(KafkaDynamicTableFactory.java:294)
	at org.apache.flink.streaming.connectors.kafka.table.KafkaDynamicTableFactory.createDynamicTableSource(KafkaDynamicTableFactory.java:158)
	at org.apache.flink.table.factories.FactoryUtil.createTableSource(FactoryUtil.java:147)
	... 52 more
```

## 2. 分析

在如下 Flink Table 程序中，我们使用 format 参数指定为 Json 格式：
```java
TableDescriptor descriptor = TableDescriptor.forConnector("kafka")
    .comment("kafka source table")
    .schema(schema)
    .option(KafkaConnectorOptions.TOPIC, Lists.newArrayList("word"))
    .option(KafkaConnectorOptions.PROPS_BOOTSTRAP_SERVERS, "localhost:9092")
    .option(KafkaConnectorOptions.PROPS_GROUP_ID, "kafka-table-descriptor")
    .option("scan.startup.mode", "earliest-offset")
    .format("json")
    .build();
```
根据错误信息我们知道 org.apache.flink.table.factories.DeserializationFormatFactory 接口实现 Factory 类中没有一个标识符为 'json' 的，只能找一个标识符为 'raw' 的 Factory，即 RawFormatFactory。其实错误信息提示也很明显，即我们没有一个 Json Format 对应的 DeserializationFormatFactory。我们查阅 DeserializationFormatFactory 接口源码：
```java
public interface DeserializationFormatFactory
        extends DecodingFormatFactory<DeserializationSchema<RowData>> {
    // interface is used for discovery but is already fully specified by the generics
}
```
在其实现类中只有 RawFormatFactory，没有发现与 json 相关的 FormatFactory：

![](1)


## 3. 解决方案

猜测我们可能缺少 Json Format 的依赖。去官网 https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/connectors/table/formats/json/ 发现我们确实少添加了依赖。如果要使用 Json Format 需要添加如下依赖：
```xml
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-json</artifactId>
    <version>${flink.version}</version>
</dependency>
```

我们再次查看 DeserializationFormatFactory 的实现类：

![](2)
