本教程的第一部分将教您如何构建以及运行一个自定义 Source Connector，以便与 Flink 中的两个高级抽象 Table API 和 SQL 一起使用。然后，您可以使用 Flink 的 SQL 客户机进行测试。

## 1. 简介

Apache Flink 是一个数据处理引擎，目标是在本地保持状态，以便高效地进行计算。然而，Flink 并不存储数据，而是依赖于外部系统来读取和持久化数据。连接外部数据读取(Source)以及外部数据存储(Sink)在 Flink 中通常概括为连接器 Connector。

由于连接器 Connector 是一个非常重要的组件，因此 Flink 为一些流行的系统提供了内置的连接器 Connector。但有时您可能需要从一种不常见的数据格式中读取数据，而 Flink 并没有提供相对应的连接器 Connector。为此 Flink 提供了构建自定义连接器 Connector 的扩展。

一旦在 Flink 中定义了 Source 和 Sink，就可以使用声明性 API(Table API 和 SQL)来执行数据分析的查询。Table API 对编程比较友好，而 SQL 是一种更通用的查询语言。之所以被命名为 Table API 是因为它是表 Table 上的关系函数：如何获取表 Table、如何输出表 Table 以及如何对表 Table 执行查询操作。

第一部分中您将通过实现自己的自定义 Source 连接器 Connector 来从电子邮件收件箱中读取数据来探索其中的一些 API 和概念。然后，在第二部分中您将使用 Flink 通过 IMAP 协议处理电子邮件。第一部分将重点介绍如何构建自定义 Source 连接器 Connector，第二部分将重点介绍如何集成。

## 2. 连接器 Connector 架构

为了创建与 Flink 一起使用的连接器 Connector，您需要：
- 一个工厂类：告诉 Flink 可以使用哪个标识符（在这为'imap'）来标识我们的连接器 Connector，公开了哪些配置选项，以及如何实例化连接器 Connector。由于 Flink 使用 Java 服务提供者接口 (SPI) 来发现位于不同模块中的工厂，因此您还需要添加一些配置。
- 在规划阶段将表源对象作为连接器的特定实例。它负责在规划阶段与优化器进行来回通信，就像另一个创建连接器运行时实现的工厂。还有更高级的功能，例如能力，可以用来提高连接器的性能。

在规划阶段获得的连接器的运行时实现。运行时逻辑在 Flink 的核心连接器接口中实现，并执行生成动态表数据行的实际工作。运行时实例被运送到 Flink 集群。

让我们以相反的顺序看这个序列（工厂类→表源→运行时实现）。

## 3. 运行时实现

首先需要有一个可以在 Flink 的运行时使用的 Source 连接器 Connector，定义了数据如何进入以及如何在集群中执行。有几个不同的接口可用于实现数据的实际来源并使其在 Flink 中可被发现。

对于复杂的连接器，您可能需要实现 Source 接口，它可以为您提供大量控制。 对于更简单的用例，您可以使用 SourceFunction 接口。 对于常见用例，例如 FromElementsFunction 类和 RichSourceFunction 类，已经有几种不同的 SourceFunction 接口实现。 您将使用后者。



- [Implementing a Custom Source Connector for Table API and SQL - Part One](https://flink.apache.org/2021/09/07/connector-table-sql-api-part1.html)
