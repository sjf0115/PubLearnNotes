---
layout: post
author: smartsi
title: Flink Table API & SQL 如何定义时间属性
date: 2021-10-02 22:34:01
tags:
  - Flink SQL

categories: Flink
permalink: flink-sql-time-attributes
---

> Flink 版本：1.11

本文将解释如何在 Flink 的 Table API 和 SQL 中为基于时间的操作定义时间属性（Time Attributes）。

## 1. 时间属性介绍

基于时间的操作，例如 Table API 和 SQL 查询中的窗口，需要知道时间相关的信息。因此，表需要提供逻辑时间属性以指明时间以及提供访问相应的时间戳。时间属性可以作为表 schema 的一部分，可以在用 CREATE TABLE DDL 语句创建表的时候指定、也可以在 DataStream 中指定、也可以在定义 TableSource 时指定。一旦定义了时间属性，就可以像普通字段一样使用，也可以在时间相关的操作中使用。

只要时间属性没有被修改，只是从一个查询转发到另一个查询，那么仍然是一个有效的时间属性。时间属性类似一个常规时间戳，可以用来计算。当在计算中使用时，时间属性被物化为一个标准时间戳。但是，不能使用普通时间戳来代替时间属性，也不能将其转换为时间属性。

## 2. 如何定义时间属性

Flink 可以根据如下两种时间概念来处理数据：
- 处理时间是指机器执行相应操作的系统时间（也称为纪元时间，例如 Java 的 System.currentTimeMillis()）。
- 事件时间是指根据每一行中的时间戳来处理数据流。

因此，时间属性可以是基于处理时间的，也可以基于事件时间。此外，时间属性可以作为表 schema 的一部分，可以在用 CREATE TABLE DDL 语句创建表的时候指定、也可以在 DataStream 中指定、也可以在定义 TableSource 时指定。

### 2.1 处理时间

处理时间是基于机器的本地时间来处理数据，是一种最简单的时间概念，但是它不能提供确定性的结果。不同于事件时间，既不需要从数据里获取时间戳，也不需要生成 Watermark。基于处理时间的时间属性有如下三种创建方式：
- 可以在用 CREATE TABLE DDL 语句创建表的时候定义
- 可以在 DataStream 转换为 Table 时定义
- 可以在定义 TableSource 时定义

#### 2.1.1 在 DDL 中定义

处理时间属性可以在用 CREATE TABLE DDL 语句创建表时使用 PROCTIME() 系统函数（返回类型是 TIMESTAMP_LTZ 类型）定义计算列来生成。定义处理时间：
```sql
CREATE TABLE user_actions (
  user_name STRING,
  data STRING,
  user_action_time AS PROCTIME() -- 另外声明一列作为处理时间属性
) WITH (
  ...
);

SELECT TUMBLE_START(user_action_time, INTERVAL '10' MINUTE), COUNT(DISTINCT user_name)
FROM user_actions
GROUP BY TUMBLE(user_action_time, INTERVAL '10' MINUTE);
```

> 计算列是一个虚拟列，使用 column_name AS computed_column_expression 语法生成，例如，cost AS price * quanitity，其中 price 和 quanitity 是表中的两个实际物理列。

#### 2.1.2 在 DataStream 转换为 Table 时定义

在 DataStream 转换 Table 时，处理时间属性可以通过 `.proctime` 属性定义。时间属性只能通过一个额外的逻辑字段来扩展物理 schema。因此，只能在 schema 定义的末尾进行定义，不能基于位置来定义处理时间属性：
```java
DataStream<Tuple2<String, String>> stream = ...;

Table table = tEnv.fromDataStream(stream, $("user_name"), $("data"), $("user_action_time").proctime());

WindowedTable windowedTable = table.window(
  Tumble.over(lit(10).minutes())
      .on($("user_action_time"))
      .as("userActionWindow")
);
```

#### 2.1.3 在 TableSource 中定义

可以在创建 TableSource 的过程中定义处理时间属性，通过实现 DefinedProctimeAttribute 接口中的 getRowtimeAttributeDescriptors 方法，创建基于处理时间的时间属性信息，并在 Table API 中注册创建好的 Table Source，最后便可以创建基于处理时间的操作算子：
```
// 定义一个由处理时间属性的 table source
public class UserActionSource implements StreamTableSource<Row>, DefinedProctimeAttribute {
  @Override
  public TypeInformation<Row> getReturnType() {
    String[] names = new String[] {"user_name" , "data"};
    TypeInformation[] types = new TypeInformation[] { Types.STRING(), Types.STRING()};
    return Types.ROW(names, types);
  }

  @Override
  public DataStream<Row> getDataStream(StreamExecutionEnvironment execEnv) {
    // create stream
    DataStream<Row> stream = ;
    return stream;
  }

  @Override
  public String getProctimeAttribute() {
    // 这个名字的列会被追加到最后，作为第三列
    return "user_action_time";
  }
}

// register table source
tEnv.registerTableSource("user_actions", new UserActionSource());

WindowedTable windowedTable = tEnv
  .from("user_actions")
  .window(Tumble
      .over(lit(10).minutes())
      .on($("user_action_time"))
      .as("userActionWindow"));
```

### 2.2 事件时间

事件时间允许 Table 程序根据每条记录中的时间戳生成结果，即使出现乱序或延迟事件也能获得一致的结果。此外，事件时间可以为批处理和流处理中的 Table 程序提供统一的语法。

为了处理乱序事件并区分流中的 On-Time 和 Late 事件，Flink 需要知道每一行的时间戳，并且还需要知道到目前为止处理进展（通过 Watermark 实现）。

#### 2.2.1 在 DDL 中定义

事件时间属性可以在用 CREATE TABLE DDL 语句创建表时用 WATERMARK 语句定义。WATERMARK 语句在现有事件时间字段上定义 WATERMARK 生成表达式，将事件时间字段标记为事件时间属性。Flink 支持在 TIMESTAMP 列和 TIMESTAMP_LTZ 列上定义事件时间属性。如果 Source 中的时间戳数据为 '年-月-日-时-分-秒' 这种格式，一般是没有时区信息的字符串值，例如，2020-04-15 20:13:40.564，建议事件时间属性使用 TIMESTAMP 数据类型的列：
```sql
CREATE TABLE user_actions (
  user_name STRING,
  data STRING,
  user_action_time TIMESTAMP(3),
  -- 声明 user_action_time 为事件时间属性并使用 5s 延迟的 Watermark 策略
  WATERMARK FOR user_action_time AS user_action_time - INTERVAL '5' SECOND
) WITH (
  ...
);

SELECT TUMBLE_START(user_action_time, INTERVAL '10' MINUTE), COUNT(DISTINCT user_name)
FROM user_actions
GROUP BY TUMBLE(user_action_time, INTERVAL '10' MINUTE);
```
如果 Source 数据中的时间戳数据是一个纪元 (epoch) 时间，一般是一个 Long 值，例如，1618989564564，建议事件时间属性使用 TIMESTAMP_LTZ 数据类型的列：
```sql
CREATE TABLE user_actions (
 user_name STRING,
 data STRING,
 ts BIGINT,
 time_ltz AS TO_TIMESTAMP_LTZ(ts, 3),
 -- 声明 user_action_time 为事件时间属性并使用 5s 延迟的 Watermark 策略
 WATERMARK FOR time_ltz AS time_ltz - INTERVAL '5' SECOND
) WITH (
 ...
);

SELECT TUMBLE_START(time_ltz, INTERVAL '10' MINUTE), COUNT(DISTINCT user_name)
FROM user_actions
GROUP BY TUMBLE(time_ltz, INTERVAL '10' MINUTE);
```

#### 2.2.2 在 DataStream 转换为 Table 时定义

在 DataStream 转换 Table 时，事件时间属性可以使用 `.rowtime` 属性定义。在转换之前，时间戳和 Watermark 必须在 DataStream 中先设置好。在转换过程中，由于 DataStream 没有时区概念，因此 Flink 总是将 rowtime 属性解析成 TIMESTAMP WITHOUT TIME ZONE 类型，并且将所有事件时间的值都视为 UTC 时区的值。

在从 DataStream 到 Table 转换时定义事件时间属性有两种方式。根据 `.rowtime` 指定的字段名称是否已经存在于 DataStream 的 schema 中，事件时间属性可以：
- 在 schema 末尾追加一个新的字段
- 替换一个已经存在的字段

不管在哪种情况下，事件时间戳字段都会保存 DataStream 事件的时间戳。
```java
// 1. 追加一个新的字段
// 提取时间戳并分配watermarks
DataStream<Tuple2<String, String>> stream = inputStream.assignTimestampsAndWatermarks(...);

// 声明一个额外逻辑字段作为事件时间属性
// 在 schema 的末尾使用 user_action_time.rowtime 定义事件时间属性
Table table = tEnv.fromDataStream(stream, $("user_name"), $("data"), $("user_action_time").rowtime());

// 2. 替换一个已经存在的字段
// 从第一个字段提取时间戳并分配 watermarks
DataStream<Tuple3<Long, String, String>> stream = inputStream.assignTimestampsAndWatermarks(...);

// 第一个字段已经用来提取时间戳，因此不在必须，可以直接使用事件时间属性替换这个字段
// replace first field with a logical event time attribute
Table table = tEnv.fromDataStream(stream, $("user_action_time").rowtime(), $("user_name"), $("data"));

WindowedTable windowedTable = table.window(Tumble
       .over(lit(10).minutes())
       .on($("user_action_time"))
       .as("userActionWindow"));
```

#### 2.2.3 在 TableSource 中定义

事件时间属性可以在实现了 DefinedRowTimeAttributes 的 TableSource 中定义。getRowtimeAttributeDescriptors() 方法返回一个 RowtimeAttributeDescriptor 列表，包含了事件时间属性名字、用来计算属性值的时间戳提取器以及 watermark 生成策略等信息。

需要确保 getDataStream() 方法返回的 DataStream 与定义的时间属性对齐。只有在定义了 StreamRecordTimestamp 时间戳分配器的时候，才认为 DataStream 有时间戳（由 TimestampAssigner 分配的时间戳）。只有定义了 PreserveWatermarks watermark 生成策略，DataStream 的 watermark 才会被保留。否则，只有时间字段的值是生效的：
```java
// 定义一个有事件时间属性的 table source
public class UserActionSource implements StreamTableSource<Row>, DefinedRowtimeAttributes {
  @Override
  public TypeInformation<Row> getReturnType() {
    String[] names = new String[] {"user_name", "data", "user_action_time"};
    TypeInformation[] types =
        new TypeInformation[] {Types.STRING(), Types.STRING(), Types.LONG()};
    return Types.ROW(names, types);
  }

  @Override
  public DataStream<Row> getDataStream(StreamExecutionEnvironment execEnv) {
    // 构造 DataStream
    // ...
    // 基于 "user_action_time" 定义 watermark
    DataStream<Row> stream = inputStream.assignTimestampsAndWatermarks(...);
    return stream;
  }

  @Override
  public List<RowtimeAttributeDescriptor> getRowtimeAttributeDescriptors() {
    // 标记 "user_action_time" 字段是事件时间字段
    // 给 "user_action_time" 构造一个时间属性描述符
    RowtimeAttributeDescriptor rowtimeAttrDescr = new RowtimeAttributeDescriptor(
        "user_action_time",
        new ExistingField("user_action_time"),
        new AscendingTimestamps()
    );
    List<RowtimeAttributeDescriptor> listRowtimeAttrDescr = Collections.singletonList(rowtimeAttrDescr);
    return listRowtimeAttrDescr;
  }
}

// register the table source
tEnv.registerTableSource("user_actions", new UserActionSource());

WindowedTable windowedTable = tEnv
.from("user_actions")
.window(Tumble.over(lit(10).minutes()).on($("user_action_time")).as("userActionWindow"));
```

原文:[Time Attributes](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/table/streaming/time_attributes.html)
