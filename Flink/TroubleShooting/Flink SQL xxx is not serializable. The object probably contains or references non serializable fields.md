---
layout: post
author: sjf0115
title: Flink SQL xxx is not serializable. The object probably contains or references non serializable fields
date: 2022-06-02 08:34:01
tags:
  - Flink

categories: Flink
permalink: flink-sql-xxx-is-not-serializable
---

> Flink 版本：1.10.3

## 1. 现象

在执行如下自定义 Socket Connector 示例：
```java
// 创建 Socket Source 表
String sourceSql = "CREATE TABLE socket_source_table (\n" +
        "  word STRING COMMENT '单词'\n" +
        ") WITH (\n" +
        "  'connector.type' = 'socket',\n" +
        "  'host' = 'localhost',\n" +
        "  'port' = '9000',\n" +
        "  'delimiter' = '\n',\n" +
        "  'maxNumRetries' = '3',\n" +
        "  'delayBetweenRetries' = '500'\n" +
        ")";
tEnv.sqlUpdate(sourceSql);

Table table = tEnv.sqlQuery("SELECT word\n" +
        "FROM socket_source_table");
DataStream dataStream = tEnv.toAppendStream(table, Row.class);
dataStream.print();
```
抛出如下异常：
```java
Exception in thread "main" org.apache.flink.api.common.InvalidProgramException: root
 |-- word: STRING
 is not serializable. The object probably contains or references non serializable fields.
	at org.apache.flink.api.java.ClosureCleaner.clean(ClosureCleaner.java:151)
	at org.apache.flink.api.java.ClosureCleaner.clean(ClosureCleaner.java:126)
	at org.apache.flink.api.java.ClosureCleaner.clean(ClosureCleaner.java:71)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.clean(StreamExecutionEnvironment.java:1831)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.addSource(StreamExecutionEnvironment.java:1589)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.addSource(StreamExecutionEnvironment.java:1534)
	at org.apache.flink.streaming.api.environment.StreamExecutionEnvironment.addSource(StreamExecutionEnvironment.java:1516)
	at com.flink.connector.socket.SocketTableSource.getDataStream(SocketTableSource.java:29)
	at org.apache.flink.table.plan.nodes.datastream.StreamTableSourceScan.translateToPlan(StreamTableSourceScan.scala:107)
	at org.apache.flink.table.planner.StreamPlanner.translateToCRow(StreamPlanner.scala:251)
	at org.apache.flink.table.planner.StreamPlanner.translateOptimized(StreamPlanner.scala:412)
	at org.apache.flink.table.planner.StreamPlanner.translateToType(StreamPlanner.scala:402)
	at org.apache.flink.table.planner.StreamPlanner.org$apache$flink$table$planner$StreamPlanner$$translate(StreamPlanner.scala:180)
	at org.apache.flink.table.planner.StreamPlanner$$anonfun$translate$1.apply(StreamPlanner.scala:117)
	at org.apache.flink.table.planner.StreamPlanner$$anonfun$translate$1.apply(StreamPlanner.scala:117)
	at scala.collection.TraversableLike$$anonfun$map$1.apply(TraversableLike.scala:234)
	at scala.collection.TraversableLike$$anonfun$map$1.apply(TraversableLike.scala:234)
	at scala.collection.Iterator$class.foreach(Iterator.scala:891)
	at scala.collection.AbstractIterator.foreach(Iterator.scala:1334)
	at scala.collection.IterableLike$class.foreach(IterableLike.scala:72)
	at scala.collection.AbstractIterable.foreach(Iterable.scala:54)
	at scala.collection.TraversableLike$class.map(TraversableLike.scala:234)
	at scala.collection.AbstractTraversable.map(Traversable.scala:104)
	at org.apache.flink.table.planner.StreamPlanner.translate(StreamPlanner.scala:117)
	at org.apache.flink.table.api.java.internal.StreamTableEnvironmentImpl.toDataStream(StreamTableEnvironmentImpl.java:351)
	at org.apache.flink.table.api.java.internal.StreamTableEnvironmentImpl.toAppendStream(StreamTableEnvironmentImpl.java:259)
	at org.apache.flink.table.api.java.internal.StreamTableEnvironmentImpl.toAppendStream(StreamTableEnvironmentImpl.java:250)
	at com.flink.connector.example.socket.SocketSimpleExample.main(SocketSimpleExample.java:44)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)
Caused by: java.io.NotSerializableException: org.apache.flink.table.api.TableSchema
	at java.io.ObjectOutputStream.writeObject0(ObjectOutputStream.java:1184)
	at java.io.ObjectOutputStream.writeObject(ObjectOutputStream.java:348)
	at org.apache.flink.util.InstantiationUtil.serializeObject(InstantiationUtil.java:586)
	at org.apache.flink.api.java.ClosureCleaner.clean(ClosureCleaner.java:133)
	... 32 more
```

## 2. 解决方案

在 SocketTableSource 的 getDataStream 方法中将 TableSchema 对象传到 SocketSourceFunction 方法中：
```java
public class SocketTableSource implements StreamTableSource<Row>{
    @Override
    public DataStream<Row> getDataStream(StreamExecutionEnvironment env) {
        SocketSourceFunction socketSourceFunction = SocketSourceFunction.builder()
                .setSocketOption(socketOption)
                // 传递 TableSchema
                .setSchema(schema)
                .build();
        return env.addSource(socketSourceFunction);
    }
}

public class SocketSourceFunction extends RichSourceFunction<Row> implements ResultTypeQueryable<Row> {
    private final TableSchema schema;
    // 接收 TableSchema
    public SocketSourceFunction(SocketOption option, TableSchema schema) {
        this.schema = schema;
        ...
    }
}
```
而 TableSchema 未实现序列化，所以出现 NotSerializableException 异常。因为我们实际用到的是 TableSchema 中关于字段名称和类型的信息，所以我们只需要把字段名称和类型的信息传递给 SocketSourceFunction：
```java
public class SocketTableSource implements StreamTableSource<Row>{
    @Override
    public DataStream<Row> getDataStream(StreamExecutionEnvironment env) {
        DataType producedDataType = schema.toRowDataType();
        RowTypeInfo rowTypeInfo = (RowTypeInfo) fromDataTypeToLegacyInfo(producedDataType);
        SocketSourceFunction socketSourceFunction = SocketSourceFunction.builder()
                .setSocketOption(socketOption)
                // 传递 fieldNames 和 fieldTypes
                .setFieldNames(rowTypeInfo.getFieldNames())
                .setFieldTypes(rowTypeInfo.getFieldTypes())
                .build();
        return env.addSource(socketSourceFunction);
    }
}

public class SocketSourceFunction extends RichSourceFunction<Row> implements ResultTypeQueryable<Row> {
    private final String[] fieldNames;
    private final TypeInformation[] fieldTypes;

    // 接收 fieldNames 和 fieldTypes
    public SocketSourceFunction(SocketOption option, String[] fieldNames, TypeInformation[] fieldTypes) {
        this.fieldNames = fieldNames;
        this.fieldTypes = fieldTypes;
    }

    @Override
    public TypeInformation<Row> getProducedType() {
        return new RowTypeInfo(fieldTypes, fieldNames);
    }
}
```
> [Socket Connector 完整示例](https://github.com/sjf0115/flink-connectors/tree/release-1.10.3/flink-connector-socket/src/main/java/com/flink/connector/socket)
