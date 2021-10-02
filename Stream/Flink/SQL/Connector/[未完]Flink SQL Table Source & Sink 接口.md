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

> Flink 版本：1.10


TableFactory 接口允许将与外部系统的连接声明与实际实现分开。Table Factory 根据标准化、基于字符串的属性创建 TableSource 或者 TableSink 的配置实例。可以使用 Descriptor 以编程方式或通过 SQL 客户端的 YAML 配置文件生成属性。

## 1. 定义 TableSource

TableSource 是一个通用接口，Table API 和 SQL 查询通过它来访问存储在外部系统中的数据。TableSource 提供了表的 schema 并将记录映射为带有 schema 的行。根据 TableSource 是用于流式查询还是批处理查询来决定记录是生成 DataSet 还是 DataStream。如果在流式查询中使用 TableSource，则必须实现 StreamTableSource 接口，如果在批处理查询中使用，则必须实现 BatchTableSource 接口。TableSource 也可以同时实现这两个接口，既可以用于流式查询，也可以用于批处理查询。

StreamTableSource 和 BatchTableSource 扩展了定义如下方法的基本接口 TableSource：
```java
TableSource<T> {
  public TableSchema getTableSchema();
  public TypeInformation<T> getReturnType();
  public String explainSource();
}
```
- getTableSchema()：返回生成表的 schema，即表的字段名称和类型。字段类型使用 Flink 的 DataType 定义。需要注意的是，返回的 TableSchema 不会包含计算列来表达物理 TableSource 的 schema。
- getReturnType()：返回 DataStream（StreamTableSource）或 DataSet（BatchTableSource）的物理类型以及 TableSource 产生的记录。
- explainSource()：返回一个描述 TableSource 的字符串。此方法是可选的，仅用于显示目的。

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
StreamTableSource<T> implements TableSource<T> {
  public DataStream<T> getDataStream(StreamExecutionEnvironment execEnv);
}
```
getDataStream(execEnv)：返回一个包含表数据的 DataStream。DataStream 的类型必须与 TableSource.getReturnType() 方法定义的返回类型相同。 可以使用 DataStream API 的常规数据源创建 DataStream。通常，StreamTableSource 是通过包装 SourceFunction 或流 Connector 来实现。

### 1.3 定义带有时间属性的 TableSource

流式 Table API 和 SQL 查询基于时间的操作，例如，窗口聚合或者 Join，都需要明确指定的时间属性。TableSource 在表 schema 中将时间属性定义为 Types.SQL_TIMESTAMP 类型的字段。与 schema 中的常规字段不同，时间属性不会与 TableSource 返回类型中的物理字段匹配。相反，TableSource 需要通过实现某个接口来定义时间属性。

#### 1.3.1 定义处理时间属性

处理时间属性通常用于流式查询。处理时间属性返回算子的当前挂钟时间。TableSource 通过实现 DefinedProctimeAttribute 接口来定义处理时间属性。接口如下所示：
```java
DefinedProctimeAttribute {
  public String getProctimeAttribute();
}
```
getProctimeAttribute()：返回处理时间属性的名称。指定的属性必须在表 schema 中定义为 Types.SQL_TIMESTAMP 类型，并且可以在基于时间的操作中使用。DefinedProctimeAttribute 可以通过返回 null 来定义无处理时间属性。

> StreamTableSource 和 BatchTableSource 都可以实现 DefinedProctimeAttribute 并定义处理时间属性。在 BatchTableSource 的情况下，处理时间字段在表扫描期间使用当前时间戳初始化。

#### 1.3.2 定义Rowtime属性

Rowtime 属性是 TIMESTAMP 类型的属性，在流式查询和批处理查询中统一处理。SQL_TIMESTAMP 类型的字段可以通过为 rowtime 属性指定如下信息来声明：
- 字段名称
- TimestampExtractor，计算属性的实际值（通常来自一个或多个其他字段）
- WatermarkStrategy，指定如何为 rowtime 属性生成 Watermark。

TableSource 通过实现 DefinedRowtimeAttributes 接口来定义 Rowtime 属性。接口如下所示：
```java
DefinedRowtimeAttribute {
  public List<RowtimeAttributeDescriptor> getRowtimeAttributeDescriptors();
}
```

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

## 2. 定义一个 TableSink

TableSink 指定了如何将 Table 输出到外部系统或文件。该接口是通用的，因此可以支持不同的存储位置和格式。批处理表和流表有不同的表 Connector。通用接口如下所示：
```java
TableSink<T> {
  public TypeInformation<T> getOutputType();
  public String[] getFieldNames();
  public TypeInformation[] getFieldTypes();
  public TableSink<T> configure(String[] fieldNames, TypeInformation[] fieldTypes);
}
```
调用 TableSink#configure 方法将表的 schema（字段名称和类型）传递给 TableSink。该方法必须返回 TableSink 的一个新实例，该实例被配置输出提供的 Table schema。请注意，提供的 TableSchema 不会包含计算列来表达物理 TableSink 的 schema。

### 2.1 定义 BatchTableSink

定义外部 TableSink 以输出批处理表。接口如下所示：
```java
BatchTableSink<T> implements TableSink<T> {
  public void emitDataSet(DataSet<T> dataSet);
}
```

### 2.2 定义 AppendStreamTableSink

定义一个外部 TableSink 以输出只有 INSERT 变更的流表。接口如下所示：
```java
AppendStreamTableSink<T> implements TableSink<T> {
  public void emitDataStream(DataStream<T> dataStream);
}
```
如果 table 也被 UPDATE 或 DELETE 变更修改，则会抛出 TableException。

### 2.3 RetractStreamTableSink

定义一个外部 TableSink 以输出带有 INSERT、UPDATE 以及 DELETE 变更的流表。接口如下所示：
```java
RetractStreamTableSink<T> implements TableSink<Tuple2<Boolean, T>> {
  public TypeInformation<T> getRecordType();
  public void emitDataStream(DataStream<Tuple2<Boolean, T>> dataStream);
}
```
table 被转换为编码为 Java Tuple2 的累加和回撤消息流。第一个字段表示消息类型的布尔值（true 表示 INSERT，false 表示 DELETE）。第二个字段保存请求的类型 T 的记录。

### 2.4 UpsertStreamTableSink

定义一个外部 TableSink 以输出带有 INSERT、UPDATE 以及 DELETE 变更的流表。接口如下所示：
```java
public interface UpsertStreamTableSink<T> extends StreamTableSink<Tuple2<Boolean, T>> {
  public void setKeyFields(String[] keys);
  public void setIsAppendOnly(boolean isAppendOnly);
  public TypeInformation<T> getRecordType();
  public void emitDataStream(DataStream<Tuple2<Boolean, T>> dataStream);
}
```
table 必须是唯一键字段（原子或复合）或仅支持追加。如果 table 没有唯一键并且不是仅支持追加，那么会抛出 TableException。table 的唯一键由 UpsertStreamTableSink#setKeyFields() 方法配置。setIsAppendOnly 指定要写入的表是否仅支持追加。


table 被转换为编码为 Java Tuple2 的 UPSERT 和 DELETE 消息流。第一个字段表示消息类型的布尔值（true 表示 UPSERT，false 表示 DELETE）。第二个字段保存请求的类型 T 的记录。如果该 table 仅支持追加，那么所有消息都将具有 true 的标志并且只支持插入。

## 3. 定义 TableFactory

TableFactory 根据基于字符串的属性创建不同的表相关实例。调用所有可用的工厂以匹配给定的属性集和相应的工厂类。TableFactory 利用 Java 的服务提供者接口 (SPI) 进行发现。这意味着每个依赖项和 JAR 文件都应该在 META_INF/services 资源目录中包含一个 org.apache.flink.table.factories.TableFactory 文件，文件中列出了可以提供的所有可用 TableFactory。每个 TableFactory 都需要实现以下接口：
```java
package org.apache.flink.table.factories;
interface TableFactory {
  Map<String, String> requiredContext();
  List<String> supportedProperties();
}
```
- requiredContext()：指定已实现此工厂的上下文。框架保证仅匹配哪些满足指定的属性和值集的 Factory。常见的属性有 connector.type、format.type 以及 update-mode。诸如 connector.property-version 和 format.property-version 之类的属性键是为将来的向后兼容保留的。
- supportedProperties()：Factory 可以处理的属性键列表。此方法用来做验证。如果传递了无法处理的属性，就会引发异常。该列表不能包含上下文指定的键。

为了创建一个特定的实例，一个工厂类可以实现一个或多个在 org.apache.flink.table.factories 中提供的接口：
- BatchTableSourceFactory：创建批处理 TableSource。
- BatchTableSinkFactory：创建批处理 TableSink。
- StreamTableSourceFactory：创建流 TableSource。
- StreamTableSinkFactory：创建流 TableSink。
- DeserializationSchemaFactory：创建反序列化 schema 格式。
- SerializationSchemaFactory：创建序列化 schema 格式。

Factory 发现发生在多个阶段：
- 发现所有可用的 Factory。
- 按 Factory 类过滤（例如，StreamTableSourceFactory）。
- 按匹配上下文过滤。
- 按支持的属性过滤。
- 验证一个工厂是否匹配，否则抛出 AmbiguousTableFactoryException 或 NoMatchingTableFactoryException。

以下示例显示了如何为自定义流 Source 并提供额外的 connector.debug 属性标志以进行参数化：
```java
import org.apache.flink.table.sources.StreamTableSource;
import org.apache.flink.types.Row;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

class MySystemTableSourceFactory implements StreamTableSourceFactory<Row> {

  @Override
  public Map<String, String> requiredContext() {
    Map<String, String> context = new HashMap<>();
    context.put("update-mode", "append");
    context.put("connector.type", "my-system");
    return context;
  }

  @Override
  public List<String> supportedProperties() {
    List<String> list = new ArrayList<>();
    list.add("connector.debug");
    return list;
  }

  @Override
  public StreamTableSource<Row> createStreamTableSource(Map<String, String> properties) {
    boolean isDebug = Boolean.valueOf(properties.get("connector.debug"));
    # additional validation of the passed properties can also happen here
    return new MySystemAppendTableSource(isDebug);
  }
}
```
### 3.1 SQL Client 中使用 TableFactory

在 SQL Client 环境文件中，先前提供的工厂可以声明为：
```
tables:
 - name: MySystemTable
   type: source
   update-mode: append
   connector:
     type: my-system
     debug: true
```
YAML 文件被转换为扁平化的字符串属性，并使用描述与外部系统的连接的这些属性调用 TableFactory：
```
update-mode=append
connector.type=my-system
connector.debug=true
```

### 3.2 在 Table & SQL API 中使用 TableFactory

Table & SQL API 在 org.apache.flink.table.descriptors 中提供了描述符，这些描述符可转换为基于字符串的属性。可以通过扩展 ConnectorDescriptor 类来定义自定义描述符：
```java
import org.apache.flink.table.descriptors.ConnectorDescriptor;
import java.util.HashMap;
import java.util.Map;

/**
  * Connector to MySystem with debug mode.
  */
public class MySystemConnector extends ConnectorDescriptor {

  public final boolean isDebug;

  public MySystemConnector(boolean isDebug) {
    super("my-system", 1, false);
    this.isDebug = isDebug;
  }

  @Override
  protected Map<String, String> toConnectorProperties() {
    Map<String, String> properties = new HashMap<>();
    properties.put("connector.debug", Boolean.toString(isDebug));
    return properties;
  }
}
```
然后可以使用描述符创建具有表环境的表：
```java
StreamTableEnvironment tableEnv = // ...

tableEnv
  .connect(new MySystemConnector(true))
  .withSchema(...)
  .inAppendMode()
  .createTemporaryTable("MySystemTable");
```























参考：
- [Legacy Table Source & Sink Interfaces](https://ci.apache.org/projects/flink/flink-docs-release-1.11/dev/table/legacySourceSinks.html)
