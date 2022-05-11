---
layout: post
author: sjf0115
title: Flink SQL ClassNotFoundException: org.apache.commons.compress.compressors.zstandard.ZstdCompressorInputStream
date: 2022-05-11 22:34:01
tags:
  - Flink

categories: Flink
permalink: class-not-found-exception-compress-compressors-zstandard
---

## 1. 现象

在 Flink SQL 中使用 FileSystem Connector 以 CSV 格式读取本地 csv 文件时，抛出如下异常：
```java
Exception in thread "main" java.lang.NoClassDefFoundError: org/apache/commons/compress/compressors/zstandard/ZstdCompressorInputStream
	at org.apache.flink.api.common.io.FileInputFormat.initDefaultInflaterInputStreamFactories(FileInputFormat.java:124)
	at org.apache.flink.api.common.io.FileInputFormat.<clinit>(FileInputFormat.java:90)
	at org.apache.flink.formats.csv.CsvFileSystemFormatFactory.createReader(CsvFileSystemFormatFactory.java:117)
	at org.apache.flink.table.filesystem.FileSystemTableSource.getInputFormat(FileSystemTableSource.java:162)
	at org.apache.flink.table.filesystem.FileSystemTableSource.getScanRuntimeProvider(FileSystemTableSource.java:126)
	at org.apache.flink.table.planner.connectors.DynamicSourceUtils.validateScanSource(DynamicSourceUtils.java:458)
	at org.apache.flink.table.planner.connectors.DynamicSourceUtils.prepareDynamicSource(DynamicSourceUtils.java:166)
	at org.apache.flink.table.planner.connectors.DynamicSourceUtils.convertSourceToRel(DynamicSourceUtils.java:124)
	at org.apache.flink.table.planner.plan.schema.CatalogSourceTable.toRel(CatalogSourceTable.java:85)
	at org.apache.calcite.sql2rel.SqlToRelConverter.toRel(SqlToRelConverter.java:3585)
	at org.apache.calcite.sql2rel.SqlToRelConverter.convertIdentifier(SqlToRelConverter.java:2507)
	at org.apache.calcite.sql2rel.SqlToRelConverter.convertFrom(SqlToRelConverter.java:2144)
	at org.apache.calcite.sql2rel.SqlToRelConverter.convertFrom(SqlToRelConverter.java:2093)
	at org.apache.calcite.sql2rel.SqlToRelConverter.convertFrom(SqlToRelConverter.java:2050)
	at org.apache.calcite.sql2rel.SqlToRelConverter.convertSelectImpl(SqlToRelConverter.java:663)
	at org.apache.calcite.sql2rel.SqlToRelConverter.convertSelect(SqlToRelConverter.java:644)
	at org.apache.calcite.sql2rel.SqlToRelConverter.convertQueryRecursive(SqlToRelConverter.java:3438)
	at org.apache.calcite.sql2rel.SqlToRelConverter.convertQuery(SqlToRelConverter.java:570)
	at org.apache.flink.table.planner.calcite.FlinkPlannerImpl.org$apache$flink$table$planner$calcite$FlinkPlannerImpl$$rel(FlinkPlannerImpl.scala:169)
	at org.apache.flink.table.planner.calcite.FlinkPlannerImpl.rel(FlinkPlannerImpl.scala:161)
	at org.apache.flink.table.planner.operations.SqlToOperationConverter.toQueryOperation(SqlToOperationConverter.java:989)
	at org.apache.flink.table.planner.operations.SqlToOperationConverter.convertSqlQuery(SqlToOperationConverter.java:958)
	at org.apache.flink.table.planner.operations.SqlToOperationConverter.convert(SqlToOperationConverter.java:283)
	at org.apache.flink.table.planner.delegation.ParserImpl.parse(ParserImpl.java:101)
	at org.apache.flink.table.api.internal.TableEnvironmentImpl.sqlQuery(TableEnvironmentImpl.java:704)
	at com.flink.example.table.connectors.FileSystemConnectorSQLExample.main(FileSystemConnectorSQLExample.java:36)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
Caused by: java.lang.ClassNotFoundException: org.apache.commons.compress.compressors.zstandard.ZstdCompressorInputStream
	at java.net.URLClassLoader.findClass(URLClassLoader.java:381)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:424)
	at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:338)
	at java.lang.ClassLoader.loadClass(ClassLoader.java:357)
	... 31 more
```
## 2. 解决方案

需要添加如下依赖：
```xml
<dependency>
	<groupId>org.apache.commons</groupId>
	<artifactId>commons-compress</artifactId>
	<version>1.21</version>
</dependency>
```
