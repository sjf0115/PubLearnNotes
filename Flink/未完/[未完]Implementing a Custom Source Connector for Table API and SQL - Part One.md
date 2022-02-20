本教程的第一部分将教您如何构建和运行自定义 Source Connector，以与 Flink 中的两个高级抽象 Table API 和 SQL 一起使用。本教程附带捆绑的 docker-compose 设置，可让您轻松运行连接器。然后你可以用 Flink 的 SQL 客户端来尝试一下。

## 1. 介绍

Apache Flink 是一种数据处理引擎，旨在将状态保持在本地以便高效地进行计算。然而，Flink 并不存储数据，而是依赖外部系统来读取以及持久化数据。连接到外部数据输入（Source）或者外部数据存储（Sink）通常在 Flink 中称之为 Connectors。由于 Connector 是非常重要的组件，Flink 为一些常见的系统提供了内置 Connector。但有时你可能需要读取一种不常见的数据格式，而 Flink 内置的并支持。这就是为什么如果想连接到现有 Connector 不支持的系统，Flink 提供用于构建自定义 Connector 的扩展的原因。

一旦你为 Flink 定义了一个 Source 和一个 Sink，你就可以使用声明式 API（以 Table API 和 SQL 的形式）来执行查询以进行数据分析。Table API 提供了更多的编程访问，而 SQL 是一种更通用的查询语言。之所以命名为 Table API，是因为是 Table 上的关系函数：如何获取表、输出表以及如何对表进行查询操作。

在这个由两部分组成的教程中，您将通过实现您自己的自定义源连接器来从电子邮件收件箱中读取数据来探索其中的一些 API 和概念。然后您将使用 Flink 通过 IMAP 协议处理电子邮件。

第一部分将专注于构建自定义 Source Connector，第二部分将专注于集成它。

## 2. 了解 Connector 所需的架构

为了创建一个与 Flink 一起工作的 Connector，你需要：
- 一个工厂类（用于从字符串属性创建其他对象的蓝图），它告诉 Flink 可以使用哪个标识符（在这种情况下，“imap”）我们的连接器可以被寻址，它公开了哪些配置选项，以及如何实例化连接器。由于 Flink 使用 Java 服务提供者接口 (SPI) 来发现位于不同模块中的工厂，因此您还需要添加一些配置细节。
- 在规划阶段，表源对象作为连接器的特定实例。它负责在规划阶段与优化器来回通信，就像另一个用于创建连接器运行时实现的工厂。还有一些更高级的特性，比如能力，可以用来提高连接器的性能。
- 在规划阶段获得的连接器的运行时实现。运行时逻辑在 Flink 的核心连接器接口中实现，并执行生成动态表数据行的实际工作。运行时实例被运送到 Flink 集群。

让我们以相反的顺序来看这个序列（工厂类 → 表 Source → 运行时实现）。

## 3. Connector 的运行时实现

你首先需要有一个可以在 Flink 运行时系统中使用的 Source Connector，定义数据如何进入集群以及如何执行。有几种不同的接口可用于实现数据的实际来源，并在 Flink 中可被发现。

对于复杂的 Connector，我们可能希望实现 Source 接口，可以实现比较多的控制。对于简单的 Connector，我们可以使用 SourceFunction 接口。目前已经有一些 SourceFunction 接口的不同实现，例如，常见的 FromElementsFunction 类和 RichSourceFunction 类。我们一般使用后者。

> Source 接口是新的抽象，而 SourceFunction 接口正在慢慢被废弃。所有 Connector 最终都会实现 Source 接口。

RichSourceFunction 是实现数据源 Source 的基类，可以访问上下文信息以及一些生命周期方法。需要实现一个从 SourceFunction 接口继承的 run() 方法。它被调用一次，可用于为有界结果生成一次数据或者为无界流循环生成数据。

例如，创建一个有界数据源，可以实现此方法来读取所有现有电子邮件，读完然后关闭。创建一个无界数据源，只能数据源处于活跃状态时就可以查看传入的新电子邮件。还可以组合这些行为并通过配置选项来实现。

当我们第一次创建类并实现接口时，如下所示：
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
> 需要注意的是，表运行时需要使用内部数据结构 RowData。

在 run() 方法中，我们可以访问从 SourceFunction 接口继承的上下文 Context 对象，该对象可以允许输出数据。Source 此时还不会产生任何数据，下一步是让它产生一些静态数据，以测试数据是否正确流动：
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
这个时候我么还不需要实现 cancel() 方法，因为 Source 产生数据后立即完成。


### 4. 创建和配置动态表 Source

动态表是 Flink Table API 和 SQL 支持流数据的核心概念，正如它的名字所示，会随着时间发生变化。我们可以想象一个数据流在逻辑上转换成一个不断变化的表 。在本文中，被读入的电子邮件可以理解为可查询的（Source）表。可以将其视为 Connector 类的特定实例。现在我们来实现一个 DynamicTableSource 接口。有两种类型的动态表 Source：ScanTableSource 和 LookupTableSource。ScanTableSource 读取外部系统上的整个表，而 LookupTableSource 根据 Key 查找特定行。在本文中使用前者作为示例。下面是一个 ScanTableSource 实现的样子：
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
ChangelogMode 通知 Flink 计划器在运行时可以预期的预期变化。例如，Source 是否只生成新行，是否还会更新现有行，或者是否可以删除以前生成的行。在这我们的 Source 只会产生 (insertOnly()) 新行。ScanRuntimeProvider 创建之前确认的实际运行时实现（用于读取数据）。Flink 甚至提供了 SourceFunctionProvider 之类的实用程序，将其包装到 SourceFunction 的实例中，这是基本的运行时接口之一。此外还需要指明 Source 是否有界。

### 5. 创建工厂类

现在我们已经有了一个可用的 Source Connector，为了在 Table API 或 SQL 中使用它，它需要被 Flink 发现。我们还需要定义在创建 Source 表时如何通过 SQL 语句寻找对应的 Connector。我们需要实现一个工厂，它是一个基础接口，从 Flink 的 Table API 和 SQL 中的键值对列表中创建对象实例。工厂由其类名和 factoryIdentifier() 唯一标识。在本文中，我们将实现更具体的 DynamicTableSourceFactory，以允许我们配置动态表 Connector 以及创建 DynamicTableSource 实例。
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
目前没有配置选项，但可以在 createDynamicTableSource() 函数中添加以及验证。Flink 提供了一个小的帮助实用程序 TableFactoryHelper，可确保设置所需的选项并且不提供未知选项。最后，我们需要为 Java 的服务提供者接口 (SPI) 注册我们的工厂。可以发现实现此接口的类，并应将其添加到此文件 src/main/resources/META-INF/services/org.apache.flink.table.factories.Factory 中，并使用工厂的完全分类类名称：
```
// if you created your class in the package org.example.acme, it should be named the following:
org.example.acme.ImapTableSourceFactory
```

### 6. 测试自定义 Connector

我们现在有了一个可用的 Source Connector。可以通过运行来测试它：





- [Implementing a Custom Source Connector for Table API and SQL - Part One](https://flink.apache.org/2021/09/07/connector-table-sql-api-part1.html)
