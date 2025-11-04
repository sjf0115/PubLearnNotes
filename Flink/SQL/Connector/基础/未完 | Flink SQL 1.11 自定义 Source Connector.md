---
layout: post
author: smartsi
title: Flink SQL Table Source & Sink 接口
date: 2021-08-15 15:47:21
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-table-source-sink
---

> Flink 版本：1.11


https://wangpei.blog.csdn.net/article/details/105619547

TableFactory 接口允许将与外部系统的连接声明与实际实现分开。Table Factory 根据标准化、基于字符串的属性创建 TableSource 或者 TableSink 的配置实例。可以使用 Descriptor 以编程方式或通过 SQL 客户端的 YAML 配置文件生成属性。

## 1. 定义 TableSource

TableSource 是一个通用接口，Table API 和 SQL 查询通过它来访问存储在外部系统中的数据。TableSource 提供了表的 schema 和记录(与带表 schema 的行映射)。根据 TableSource 是用于流式查询还是批处理查询来决定记录是生成 DataSet 还是 DataStream。如果在流式查询中使用 TableSource，则必须实现 StreamTableSource 接口，如果在批处理查询中使用，则必须实现 BatchTableSource 接口。TableSource 也可以同时实现这两个接口，既可以用于流式查询，也可以用于批处理查询。

StreamTableSource 和 BatchTableSource 扩展了定义如下方法的基本接口 TableSource：
```java
TableSource<T> {
  public TableSchema getTableSchema();
  public TypeInformation<T> getReturnType();
  public String explainSource();
}
```
- `getTableSchema()`：返回生成表的 schema，即表的字段名称和类型。字段类型使用 Flink 的 DataType 定义。需要注意的是，返回的 TableSchema 不会包含计算列来表达物理 TableSource 的 schema。
- `getReturnType()`：返回 DataStream（StreamTableSource）或 DataSet（BatchTableSource）的物理类型以及 TableSource 产生的记录。
- `explainSource()`：返回一个描述 TableSource 的字符串。此方法是可选的，仅用于显示目的。

TableSource 接口将逻辑表 schema 与返回的 DataStream 或 DataSet 的物理类型做了区分。因此，表 schema (getTableSchema()) 的所有字段都必须映射到具有物理返回类型 (getReturnType()) 对应类型的字段。默认情况下，此映射是基于字段名称完成的。例如，表 schema 具有两个字段 [name: String, size: Integer] 的 TableSource 需要一个 TypeInformation，其中至少有两个字段，String 类型的 name 以及 Integer 类型的 size。可能是一个 PojoTypeInfo 或一个 RowTypeInfo，它们有两个名为 name 和 size 且类型匹配的字段。

但是，某些类型（例如 Tuple 或 CaseClass 类型）确实支持自定义字段名称。 如果 TableSource 返回具有固定字段名称的类型的 DataStream 或 DataSet，则它可以实现 DefinedFieldMapping 接口以将字段名称从表模式映射到物理返回类型的字段名称。

### 1.1 定义 BatchTableSource

BatchTableSource 接口实现了 TableSource 接口并定义了一些其他方法：
```java
BatchTableSource<T> implements TableSource<T> {
  public DataSet<T> getDataSet(ExecutionEnvironment execEnv);
}
```
getDataSet(execEnv)：返回一个包含表数据的 DataSet。DataSet 的类型必须与 TableSource.getReturnType() 方法定义的返回类型相同。可以使用 DataSet API 的常规数据源创建 DataSet。通常，BatchTableSource 是通过包装 InputFormat 或批处理 Connector 来实现。

### 1.2 StreamTableSource

StreamTableSource 接口实现了 TableSource 接口并定义了一些其他方法：
```java
public interface StreamTableSource<T> extends TableSource<T> {
     // 是否有有限数据源：true 表示有限数据源，false 表示无线数据源
    default boolean isBounded() {
        return false;
    }
    // 以 DataStream 形式返回表中的数据
    DataStream<T> getDataStream(StreamExecutionEnvironment execEnv);
}
```
`getDataStream(execEnv)` 方式以 DataStream 形式返回表中的数据。DataStream 的类型必须与 TableSource.getReturnType() 方法定义的返回类型相同。 可以使用 DataStream API 的常规数据源创建 DataStream。通常，StreamTableSource 是通过包装 SourceFunction 或流 Connector 来实现。

### 1.3 定义带有时间属性的 TableSource

流式 Table API 和 SQL 查询基于时间的操作，例如，窗口聚合或者 Join，都需要明确指定的时间属性。TableSource 在表 schema 中将时间属性定义为 Types.SQL_TIMESTAMP 类型的字段。与 schema 中的常规字段不同，时间属性不会与 TableSource 返回类型中的物理字段匹配。相反，TableSource 需要通过实现某个接口来定义时间属性。

#### 1.3.1 定义处理时间属性

[处理时间属性](https://smartsi.blog.csdn.net/article/details/127173096)通常用于流式查询。处理时间属性返回算子的当前系统时间。TableSource 通过实现 DefinedProctimeAttribute 接口来定义处理时间属性，如下所示：
```java
public class TimeAttributeTableSource implements StreamTableSource<Row>, DefinedProctimeAttribute {
    private final Optional<String> procTimeAttribute;

    public TimeAttributeTableSource(Optional<String> procTimeAttribute) {
        this.procTimeAttribute = procTimeAttribute;
    }

    ...

    // DefinedProctimeAttribute
    @Nullable
    @Override
    public String getProctimeAttribute() {
        return procTimeAttribute.orElse(null);
    }
}
```
`getProctimeAttribute()` 返回处理时间属性的名称。指定的属性必须在表 schema 中定义为 Types.SQL_TIMESTAMP 类型，并且可以在基于时间的操作中使用。DefinedProctimeAttribute 可以通过返回 null 来定义无处理时间属性。

> StreamTableSource 和 BatchTableSource 都可以实现 DefinedProctimeAttribute 并定义处理时间属性。在 BatchTableSource 的情况下，处理时间字段在表扫描期间使用当前时间戳初始化。

#### 1.3.2 定义 Rowtime 属性

[Rowtime 属性](https://smartsi.blog.csdn.net/article/details/127173096)是 TIMESTAMP 类型的属性，在流式查询和批处理查询中统一处理。SQL_TIMESTAMP 类型的字段可以通过指定如下信息来声明 rowtime 属性：
- 字段名称
- TimestampExtractor，计算属性的实际值（通常来自一个或多个其他字段）
- WatermarkStrategy，指定如何为 rowtime 属性生成 Watermark。

TableSource 通过实现 DefinedRowtimeAttributes 接口来定义 Rowtime 属性，如下所示：
```java
public class TimeAttributeTableSource implements StreamTableSource<Row>, DefinedRowtimeAttributes {
    private final List<RowtimeAttributeDescriptor> rowTimeAttributeDescriptors;

    public TimeAttributeTableSource(List<RowtimeAttributeDescriptor> rowTimeAttributeDescriptors) {
        this.rowTimeAttributeDescriptors = rowTimeAttributeDescriptors;
    }

    ...

    // DefinedRowtimeAttributes
    @Override
    public List<RowtimeAttributeDescriptor> getRowtimeAttributeDescriptors() {
        return rowTimeAttributeDescriptors;
    }
}
```
`getRowtimeAttributeDescriptors()` 方法返回 RowtimeAttributeDescriptor 的列表。RowtimeAttributeDescriptor 用以下属性描述 rowtime 属性：
- 字段名称：表 Schema 中 rowtime 属性的名称。该字段必须用 Types.SQL_TIMESTAMP 类型定义。
- TimestampExtractor：时间戳提取器从具有返回类型的记录中提取时间戳。例如，它可以将 Long 字段转换为时间戳或解析字符串编码的时间戳。Flink 提供了一组用于常见用例的内置 TimestampExtractor 实现。也可以提供自定义实现。
- WatermarkStrategy：Watermark 策略定义了如何为 rowtime 属性生成 Watermark。Flink 提供了一组内置的 Watermark 策略实现，用于常见的用例。也可以提供自定义实现。

### 1.4 使用投影下推定义 TableSource

TableSource 通过实现 ProjectableTableSource 接口来支持投影下推。该接口定义了一个方法：
```java
ProjectableTableSource<T> {
  public TableSource<T> projectFields(int[] fields);
}
```

### 1.5 使用过滤器下推定义 TableSource

FilterableTableSource 接口向 TableSource 添加了对过滤器下推的支持。实现此接口的 TableSource 能够过滤记录，以便 DataStream 或 DataSet 返回更少的记录。接口如下所示：
```java
FilterableTableSource<T> {
  public TableSource<T> applyPredicate(List<Expression> predicates);
  public boolean isFilterPushedDown();
}
```

### 1.6 定义 Lookups TableSource

> 在 1.11 版本中是一个实验性功能。接口可能会在未来版本中更改。仅在 Blink planner 中支持。

LookupableTableSource 接口添加了对以查找方式通过键列访问的表的支持。 这在用于连接维度表以丰富某些信息时非常有用。 如果要在查找模式下使用 TableSource，则应在时态表连接语法中使用源。

界面如下所示：

```java

```

参考：
- [Legacy Table Source & Sink Interfaces](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/table/legacySourceSinks.html)
