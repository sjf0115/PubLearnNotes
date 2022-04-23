
在定义数据处理管道时，Table API 和 DataStream API 同样重要。

DataStream API 在一个相对较低级别的命令式编程 API 中提供了流处理的原语（即时间、状态和数据流管理）。 Table API 抽象了许多内部结构，并提供了结构化和声明性的 API。

两种 API 都可以处理有界和无界流。

处理历史数据时需要管理有界流。 无限流发生在可能首先用历史数据初始化的实时处理场景中。

为了高效执行，两个 API 都以优化的批处理执行模式提供处理有界流。 但是，由于批处理只是流的一种特殊情况，因此也可以在常规流执行模式下运行有界流的管道。


可以只使用一个 API 实现端到端 Pipeline，而不用依赖于另一个 API。但是，出于各种原因，如下几种场景混合使用这两种 API 对于我们来说更容易实现需求：
- 在 DataStream API 中实现主 Pipeline 之前，可以使用表生态系统轻松访问 Catalog 或者连接到外部系统。
- 在 DataStream API 中实现主 Pipeline 之前，可以访问一些用于无状态数据规范化和清理的 SQL 函数。
- 如果 Table API 中不存在更底层的操作（例如自定义计时器处理），可以随时切换到 DataStream API。


Flink 在 Java 和 Scala 中提供了一个专门的 StreamTableEnvironment 用于与 DataStream API 的相互转换。StreamTableEnvironment 继承了 TableEnvironment 并扩展了一些方法。

截止到 Flink 1.13 版本 StreamTableEnvironment 暂不支持 Batch 执行模式。尽管如此，可以使用流执行模式处理有界流，只不过效率较低。通用的 TableEnvironment 既可以在流式执行模式下运行，也可以在优化的批处理执行模式下运行。

如下代码展示了如何在两个 API 之间来回切换的简单示例。Table 的列名和类型自动派生自 DataStream 的 TypeInformation。由于 DataStream API 本身不支持变更日志处理，因此代码在流到表以及表到流的转换过程中只支持 Append-Only 和 Insert-Only 语义：
```java
// 创建流和表执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);

// 创建 DataStream
DataStream<String> dataStream = env.fromElements("Alice", "Bob", "John");

// 将 Insert-Only DataStream 转换为 Table
Table inputTable = tableEnv.fromDataStream(dataStream);

// 注册表 InputTable
tableEnv.createTemporaryView("InputTable", inputTable);

// 执行查询生成结果 Table
Table resultTable = tableEnv.sqlQuery("SELECT UPPER(f0) FROM InputTable");

// 将 Insert-Only Table 转换为 DataStream
DataStream<Row> resultStream = tableEnv.toDataStream(resultTable);

// 输出
resultStream.print();

// 执行
env.execute();
```

## 2. 依赖

将 Table 与 DataStream 相互转换需要添加如下依赖：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-api-java-bridge_2.11</artifactId>
  <version>1.13.6</version>
  <scope>provided</scope>
</dependency>
```
它们包括对 flink-table-api-java 或 flink-table-api-scala 的传递依赖以及相应的特定于语言的 DataStream API 模块。










从创建表环境开始，历经表的创建、查询和输出，我们已经可以使用 Table API 和 SQL 进行完整的流处理了。不过在应用的开发过程中，我们测试业务逻辑一般不会直接将结果直接写入到外部系统，而是在本地控制台打印输出。对于 DataStream 这非常容易，直接调用 print() 方法就可以看到结果数据流的内容了。但对于 Table API 就稍微麻烦一点，它没有提供 print() 方法。这该怎么办呢?在 Flink 中我们可以将 Table 再转换成 DataStream，然后进行打印输出。这就涉及了表和流的转换。

## 1. DataStream 转换成 Table

### 1.1 调用 fromDataStream() 方法

将 DataStream 转换成 Table 可以通过调用 TableEnvironment 的 fromDataStream() 方法来实现，返回的就是一个 Table 对象：
```java
// 示例1 fromDataStream()
DataStream<WordCount> sourceStream1 = env.fromElements(
        new WordCount("hello", 1),
        new WordCount("word", 4),
        new WordCount("hello", 1));
Table table1 = tEnv.fromDataStream(sourceStream1);
table1.printSchema();
DataStream<WordCount> resultStream1 = tEnv.toAppendStream(table1, WordCount.class);
resultStream1.print("R1");
```
由于流中的数据本身就是定义好的 POJO 类型 WordCount，所以我们将流转换成表之后，每一行数据就对应着一个 WordCount，而表中的列名就对应着 WordCount 中的属性。我们也可以在 fromDataStream() 方法中增加参数，用来指定提取哪些属性作为表中的字段名，也可以任意指定位置：
```java
Table table1 = tEnv.fromDataStream(sourceStream1, $("word"), $("frequency"));
```

### 1.2 调用 createTemporaryView() 方法

调用 fromDataStream() 方法简单直观，可以直接将 DataStream 转到 Table，但是如果我们希望可以直接在 SQL 中引用这张表，则需要调用 TableEnvironment 的 createTemporaryView() 方法来创建虚拟视图(虚拟表)。直接传入两个参数即可，第一个是注册的表名，第二个是 DataStream：
```java
// 示例2 createTemporaryView()
DataStream<WordCount> sourceStream2 = env.fromElements(
        new WordCount("hello", 1),
        new WordCount("word", 4),
        new WordCount("hello", 1));
tEnv.createTemporaryView("input_table", sourceStream2);
Table table2 = tEnv.from("input_table");
table2.printSchema();
DataStream<WordCount> resultStream2 = tEnv.toAppendStream(table2, WordCount.class);
resultStream2.print("R2");
```
也可以传入多个参数，用来指定表中的字段：
```java
tEnv.createTemporaryView("input_table", sourceStream2, $("word"), $("frequency"));
```

> 从 DataStream 创建的视图只能注册为临时视图，无法将它们注册到永久 Catalog 中。

### 1.3 调用 fromChangelogStream ()方法

TableEnvironment 还供了一个方法 fromChangelogStream()，可以将一个变更日志流转换成表。这个方法要求流中的数据类型只能是 Row，而且每一个数据都需要指定当前行的更新类型 RowKind，如果不指定默认为 RowKind#INSERT：
```java
// 示例3 fromChangelogStream
DataStream<Row> sourceStream3 = env.fromElements(
        Row.of("hello", 1),
        Row.of("word", 4),
        Row.of("hello", 1));
Table table3 = tEnv.fromChangelogStream(sourceStream3);
table3.printSchema();
DataStream<Row> resultStream3 = tEnv.toChangelogStream(table3);
resultStream3.print("R3");
```

## 2. Table 转换成 DataStream

### 2.1 调用 toDataStream() 方法

将一个 Table 对象转换成 DataStream 非常简单，只要直接调用 TableEnvironment 的方法 toDataStream() 就可以：
```java
// 示例1 toDataStream
DataStream<WordCount> sourceStream1 = env.fromElements(
        new WordCount("hello", 1),
        new WordCount("word", 4),
        new WordCount("hello", 1));
Table table1 = tEnv.fromDataStream(sourceStream1);
DataStream<Row> resultStream1 = tEnv.toDataStream(table1);
resultStream1.print("R1");
```

### 2.2 调用 toAppendStream() 方法

将一个 Table 对象转换成 DataStream 也可以调用 TableEnvironment 的方法 toAppendStream() 方法，但前提条件是 Table 只能有插入(追加)变更。如果 Table 有更新和删除变更，那么转换会失败：
```java
// 示例2 toAppendStream
DataStream<WordCount> sourceStream2 = env.fromElements(
        new WordCount("hello", 1),
        new WordCount("word", 4),
        new WordCount("hello", 1));
Table table2 = tEnv.fromDataStream(sourceStream2);
DataStream<Row> resultStream2 = tEnv.toAppendStream(table2, Row.class);
//DataStream<WordCount> resultStream2 = tEnv.toAppendStream(table2, WordCount.class);
resultStream2.print("R2");
```
### 2.3 调用 toRetractStream() 方法

将一个 Table 对象转换成 DataStream 时，如果 Table 只能有插入(追加)变更可以调用 toAppendStream()，但是出现了更新和删除变更就不适合了。这时候需要需要调用 TableEnvironment 的方法 toRetractStream() 方法：
```java
// 示例3 toRetractStream
DataStream<WordCount> sourceStream3 = env.fromElements(
        new WordCount("hello", 1),
        new WordCount("word", 4),
        new WordCount("hello", 1));
tEnv.createTemporaryView("source_table_3", sourceStream3, $("word"), $("frequency"));
Table table3 = tEnv.sqlQuery("SELECT word, SUM(frequency) AS frequency FROM source_table_3 GROUP BY word");
DataStream<Tuple2<Boolean, Row>> resultStream3 = tEnv.toRetractStream(table3, Row.class);
// DataStream<Tuple2<Boolean, WordCount>> resultStream3 = tEnv.toRetractStream(table3, WordCount.class);
resultStream3.print("R3");
```

### 2.4 调用 toChangelogStream() 方法

将一个 Table 对象转换成 DataStream 时，如果 Table 有更新和删除变更，除了调用 TableEnvironment 的方法 toRetractStream() 方法之外，还可以调用 toChangelogStream() 方法：
```java
// 示例4 toRetractStream
DataStream<WordCount> sourceStream4 = env.fromElements(
        new WordCount("hello", 1),
        new WordCount("word", 4),
        new WordCount("hello", 1));
tEnv.createTemporaryView("source_table_4", sourceStream4, $("word"), $("frequency"));
Table table4 = tEnv.sqlQuery("SELECT word, SUM(frequency) FROM source_table_4 GROUP BY word");
DataStream<Row> resultStream4 = tEnv.toChangelogStream(table4);
resultStream4.print("R4");
```


...
