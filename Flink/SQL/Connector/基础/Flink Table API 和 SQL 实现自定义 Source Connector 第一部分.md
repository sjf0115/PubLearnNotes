---
layout: post
author: smartsi
title: Flink Table API 和 SQL 实现自定义 Source Connector 第一部分
date: 2022-06-23 15:47:21
tags:
  - Flink

categories: Flink
permalink: flink-sql-connector-table-sql-api-part1
---

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

首先需要有一个可以在 Flink 运行时使用的 Source 连接器 Connector，其定义了数据如何进入集群以及如何在集群中执行。有几个不同的接口可用于实现数据的实际来源并使其在 Flink 中可被发现。

对于复杂的连接器 Connector，可能需要实现 Source 接口，可以为您提供最大的灵活性。对于简单的，可以使用 SourceFunction 接口。对于常见用例，SourceFunction 接口已经有几种不同的实现，例如 FromElementsFunction 类和 RichSourceFunction 类。一般会使用后者。

> Source 接口是一个新的抽象接口，而 SourceFunction 接口正在慢慢淘汰。最终所有连接器 Connector 都会实现 Source 接口。

RichSourceFunction 是一个基类，用于实现访问上下文信息和一些生命周期方法的数据源。您需要实现 SourceFunction 接口的 run() 方法。每被调用一次，可以为有界结果生成一次数据，或在循环中为无界流持续生成数据。

例如，要创建有界数据源，可以在此方法中读取完所有电子邮件后关闭。要创建无限数据源，只能让数据源一直处于活跃状态，随时查看传入的新电子邮件。当你第一次创建并实现接口时，应该看起来跟下面一样：
```java
import org.apache.flink.streaming.api.functions.source.RichSourceFunction;
import org.apache.flink.table.data.RowData;

public class ImapSource extends RichSourceFunction<RowData> {
  @Override
  public void run(SourceContext<RowData> ctx) throws Exception {}
  @Override
  public void cancel() {}
}
```
请注意，使用内部数据结构 RowData，因为表运行时需要它。

在 run() 方法中，可以访问从 SourceFunction 接口继承的上下文对象。该接口是与 Flink 的桥梁，可以允许输出数据。由于数据源到目前为止还没有产生任何数据，下一步是让它产生一些静态数据，以测试数据是否正确流动：
```java
import org.apache.flink.streaming.api.functions.source.RichSourceFunction;
import org.apache.flink.table.data.GenericRowData;
import org.apache.flink.table.data.RowData;
import org.apache.flink.table.data.StringData;

public class ImapSource extends RichSourceFunction<RowData> {
  @Override
  public void run(SourceContext<RowData> ctx) throws Exception {
      ctx.collect(GenericRowData.of(
          StringData.fromString("Subject 1"),
          StringData.fromString("Hello, World!")
      ));
  }
  @Override
  public void cancel(){}
}
```
此时还不需要实现 cancel() 方法，因为数据源运行后会立即结束。

## 4. 创建与配置动态表 Source

动态表是 Flink Table API 和 SQL 支持流数据的核心概念，正如它的名字所暗示的，随着时间的推移而变化。你可以想象一个数据流被逻辑转换成一个不断变化的表。在这里，将读入的电子邮件解释为一个可查询的（Source）表，可以被视为 Connector 类的特定实例。

现在实现一个 DynamicTableSource 接口。有两种类型的动态表 Source 可供选择：ScanTableSource 和 LookupTableSource。ScanTableSource 读取外部系统上的整个表，LookupTableSource 则是根据键查找特定行。在这我们使用 ScanTableSource，具体实现如下所示：
```java
import org.apache.flink.table.connector.ChangelogMode;
import org.apache.flink.table.connector.source.DynamicTableSource;
import org.apache.flink.table.connector.source.ScanTableSource;
import org.apache.flink.table.connector.source.SourceFunctionProvider;

public class ImapTableSource implements ScanTableSource {
  @Override
  public ChangelogMode getChangelogMode() {
    return ChangelogMode.insertOnly();
  }
  @Override
  public ScanRuntimeProvider getScanRuntimeProvider(ScanContext ctx) {
    boolean bounded = true;
    final ImapSource source = new ImapSource();
    return SourceFunctionProvider.of(source, bounded);
  }
  @Override
  public DynamicTableSource copy() {
    return new ImapTableSource();
  }
  @Override
  public String asSummaryString() {
    return "IMAP Table Source";
  }
}
```
ChangelogMode 会告诉 Flink 计划器在运行时可以预期的变化。例如，Source 是否只生成新行，是否也可以更新现有行，或者是否可以删除以前生成的行。在这我们的 Source 只会产生 (insertOnly()) 新行。

ScanRuntimeProvider 允许 Flink 创建您之前建立的实际运行时实现（用于读取数据）。Flink 甚至提供了像 SourceFunctionProvider 这样的实用工具来将其包装到 SourceFunction 的实例中。您还需要指出 Source 是否有界。目前是这种情况，但您稍后必须更改它。

## 5. 为连接器创建工厂类

你现在有了一个可以工作的 Source 连接器 Connector，但是为了可以在 Table API 或 SQL 中使用它，即它需要被 Flink 发现。在创建 Source 表时，您还需要定义如何从 SQL 语句中寻找到连接器 Connector。

你需要实现一个 Factory，这是一个从 Flink Table API 和 SQL 中键值对列表中创建对象实例的基础接口。工厂由其类名和 factoryIdentifier() 唯一标识。在这您将实现更具体的 DynamicTableSourceFactory，可以允许配置动态表连接器 Connector 以及创建 DynamicTableSource 实例:
```java
import java.util.HashSet;
import java.util.Set;
import org.apache.flink.configuration.ConfigOption;
import org.apache.flink.table.connector.source.DynamicTableSource;
import org.apache.flink.table.factories.DynamicTableSourceFactory;
import org.apache.flink.table.factories.FactoryUtil;

public class ImapTableSourceFactory implements DynamicTableSourceFactory {
  @Override
  public String factoryIdentifier() {
    return "imap";
  }

  @Override
  public Set<ConfigOption<?>> requiredOptions() {
    return new HashSet<>();
  }

  @Override
  public Set<ConfigOption<?>> optionalOptions() {
    return new HashSet<>();
  }

  @Override
  public DynamicTableSource createDynamicTableSource(Context ctx) {
    final FactoryUtil.TableFactoryHelper factoryHelper = FactoryUtil.createTableFactoryHelper(this, ctx);
    factoryHelper.validate();

    return new ImapTableSource();
  }
}
```
目前没有配置选项，但可以在 createDynamicTableSource() 函数中添加和验证它们。Flink 提供了一个小的帮助工具类 TableFactoryHelper，可以确保设置了所需要的选项并且不提供未知选项。

最后，您需要为 Java 的服务提供者接口 (SPI) 注册您的工厂。可以发现实现此接口的类，并应将其添加到此文件 src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory 中，并使用您工厂的完全限定类名：
```
// if you created your class in the package org.example.acme, it should be named the following:
org.example.acme.ImapTableSourceFactory
```

## 6. 测试自定义连接器

您现在应该有一个可以工作的 Source 连接器 Connector。您现在可以通过使用 SQL 客户端执行以下语句来使用连接器 Connector 创建一个表（具有'主题'列和'内容'列）：
```sql
CREATE TABLE T (subject STRING, content STRING) WITH ('connector' = 'imap');
SELECT * FROM T;
```
请注意，Schema 必须与编写的完全相同，因为它当前已硬编码到连接器 Connector 中。您应该能够看到您之前在 Source 连接器 Connector 中提供的静态数据，即'Subject 1'和'Hello, World!'。

现在您有了一个可以工作的连接器 Connector，下一步是就是让它做一些比返回静态数据更有用的事情。

- [Implementing a Custom Source Connector for Table API and SQL - Part One](https://flink.apache.org/2021/09/07/connector-table-sql-api-part1.html)
