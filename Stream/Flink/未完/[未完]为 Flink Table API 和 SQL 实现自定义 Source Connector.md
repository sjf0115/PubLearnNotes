

本教程的第一部分将教您如何构建和运行一个自定义 Source Connector，以便与 Flink 中的两个高级抽象 Table API 和 SQL 一起使用。本教程附带了一个捆绑的docker-compose设置，使您可以轻松地运行连接器。然后，您可以使用Flink的SQL客户机进行测试。

## 1. 简介

Apache Flink 是一个数据处理引擎，目标是在本地保持状态，以便高效地进行计算。然而，Flink 并不存储数据，而是依赖于外部系统来读取和持久化数据。连接外部数据读取(Source)以及外部数据存储(Sink)在 Flink 中通常概括为 Connectors。



由于连接器是如此重要的组件，Flink为一些流行的系统提供了连接器。但有时您可能需要以一种不常见的数据格式进行读取，而Flink提供的是不够的。这就是为什么如果您希望连接到现有连接器不支持的系统，Flink还提供了构建自定义连接器的扩展点。



一旦为Flink定义了源和接收器，就可以使用它的声明性API(以Table API和SQL的形式)来执行数据分析的查询。



Table API提供了更多的编程访问，而SQL是一种更通用的查询语言。它被命名为Table API是因为它在表上的关系函数:如何获取表、如何输出表以及如何对表执行查询操作。



在这个由两部分组成的教程中，您将通过实现用于从电子邮件收件箱读取数据的自定义源连接器来探索其中的一些api和概念。然后使用Flink通过IMAP协议处理电子邮件。



第一部分将重点介绍如何构建自定义源连接器，第二部分将重点介绍如何集成它。


- [Implementing a Custom Source Connector for Table API and SQL - Part One](https://flink.apache.org/2021/09/07/connector-table-sql-api-part1.html)
