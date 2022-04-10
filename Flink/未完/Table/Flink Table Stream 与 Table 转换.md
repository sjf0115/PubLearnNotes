
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










从创建表环境开始，历经表的创建、查询和输出，我们已经可以使用 Table API 和 SQL 进行完整的流处理了。不过在应用的开发过程中，我们测试业务逻辑一般不会直接将结果直接写入到外部系统，而是在本地控制台打印输出。对于 DataStream 这非常容易，直接调用 print() 方法就可以看到结果数据流的内容了;但对于 Table 就比较悲剧——它没有提供 print()方法。 这该怎么办呢?

在 Flink 中我们可以将 Table 再转换成 DataStream，然后进行打印输出。这就涉及了表和流的转换。

## 1. DataStream 转换成 Table

### 1.1 调用 fromDataStream() 方法

将 DataStream 转换成 Table 可以通过调用 TableEnvironment 的 fromDataStream() 方法来实现，返回的就是一个 Table 对象：
```java
// Stream 执行环境
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
// 读取数据创建 DataStream
DataStream<Behavior> behaviorStream = env.fromElements(
        new Behavior("ua", "wa", "2022-04-10 10:06:31", "卖水果"),
        new Behavior("ub", "wb", "2022-04-10 10:05:26", "秀恩爱"),
        new Behavior("ua", "wb", "2022-04-10 10:11:04", "幸运之星"));

// Table 执行环境
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);
// DataStream 转 Table
Table table = tEnv.fromDataStream(behaviorStream);
```
由于流中的数据本身就是定义好的 POJO 类型 Behavior，所以我们将流转换成表之后，每一行数据就对应着一个 Behavior，而表中的列名就对应着 Behavior 中的属性。我们也可以在 fromDataStream() 方法中增加参数，用来指定提取哪些属性作为表中的字段名，也可以任意指定位置：
```java
Table table = tEnv.fromDataStream(behaviorStream, $("content"), $("uid"), $("tm"), $("wid"));
```
