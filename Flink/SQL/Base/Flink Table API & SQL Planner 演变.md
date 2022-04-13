---
layout: post
author: sjf0115
title: Flink Table API & SQL Planner 演变
date: 2022-04-13 10:02:21
tags:
  - Flink

categories: Flink
permalink: flink-table-sql-planner-evolution
---

## 1. 背景：架构升级

Flink 1.9 之前，Flink 在其分布式流式执行引擎之上有两套相对独立的 DataStream 和 DataSet API，分别来描述流计算和批处理的作业。在这两个 API 之上，则提供了一个流批统一的 API，即 Table API 和 SQL。用户可以使用相同的 Table API 程序或者 SQL 来描述流批作业，只是在运行时需要告诉 Flink 引擎希望以流的形式运行还是以批的流式运行，此时 Table 层的优化器就会将程序优化成 DataStream 作业或者 DataSet 作业。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-table-sql-planner-evolution-1.png?raw=true)

但是仔细查看 DataStream 和 DataSet 底层实现细节，我们会发现这两个 API 共享的东西其实不多。它们有各自独立的翻译和优化的流程，而且在真正运行的时候，两者也使用了完全不同的 Task。这样的不一致对用户和开发者来讲可能存在问题。

对于用户来说，他们在编写作业的时候需要在两个 API 之间进行选择，而这两个 API 不仅语义不同，同时支持的 connector 种类也不同，难免会造成一些困扰。Table 尽管在 API 上已经进行了统一，但因为底层实现还是基于 DataStream 和 DataSet，也会受到刚才不一致的问题的影响；对于开发者来说，由于这两套流程相对独立，因此基本上很难做到代码的复用。我们在开发一些新功能的时候，往往需要将类似的功能开发两次，并且每种 API 的开发路径都比较长，基本都属于端到端的修改，这大大降低了我们的开发效率。如果两条独立的技术栈长期存在，不仅会造成人力的长期浪费，最终可能还会导致整个 Flink 的功能开发变慢。

在 Flink 1.9 之前，如果用户同时需要流计算、批处理场景，用户不得不维护两套业务代码，开发人员也不得不维护两套技术栈。Flink 社区很早就设想过将批数据看作一个有界流数据，将批处理看作流计算的一个特例，从而实现流批统一，阿里巴巴的 Blink 团队在这方面做了大量的工作，已经实现了 Table API & SQL 层的流批统一。幸运的是，阿里巴巴已经将 Blink 开源回馈给 Flink 社区。为了实现 Flink 整个体系的流批统一，在结合 Blink 团队的一些先行经验的基础上，Flink 社区的开发人员在多轮讨论后，基本敲定了 Flink 未来的技术架构：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-table-sql-planner-evolution-2.png?raw=true)

在 Flink 的未来技术架构中，DataSet API 将被废除，面向用户的 API 只有偏描述物理执行计划的 DataStream API 以及偏描述关系型计划的 Table API & SQL。在实现层，这两个 API 共享相同的技术栈，使用统一的 DAG 数据结构来描述作业，使用统一的 StreamOperator 来编写算子逻辑，以及使用统一的流式分布式执行引擎，实现彻底的流批统一。这两个 API 都会提供流计算和批处理的功能。DataStream API 提供给用户更多的是一种'所见即所得'的体验以及提供更底层和更灵活的编程接口，由用户自行描述和编排算子的关系，引擎不会做过多的干涉和优化；而 Table API & SQL 则提供了直观的 Table API、标准的 SQL 支持，引擎会根据用户的意图来进行优化，并选择最优的执行计划。

阿里巴巴将 Blink 开源回馈给 Flink 社区时，Blink 的 Table 模块已经使用了 Flink 新的技术架构。2019 年的 8 月 22 日 Apache Flink 发布了 1.9.0 版本，引入了阿里巴巴 Blink 团队贡献的诸多功能。因此在 Flink 1.9 版本中，Table 模块顺理成章的成为了架构调整后第一个吃螃蟹的人。在合入 Blink Table 代码时，为了保证 Flink Table 已有架构和 Blink Table 的架构能够并存并朝着 Flink 未来架构演进，我们需要找到一个方式让两种架构能够并存。

## 2. 什么是 Planner

基于这个目的，社区的开发人员做了一系列的努力，包括将 Table 模块进行拆分（[FLIP-32]()），对 Java 和 Scala 的 API 进行依赖梳理，并且提出了 Planner 接口以支持多种不同的 Planner 实现。Planner 将负责具体的优化和将 Table 作业翻译成执行图的工作，我们可以将原来的实现全部挪至 Flink Planner（Old Planner）中，然后把对接新架构的代码放在 Blink Planner 里。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-table-sql-planner-evolution-3.png?raw=true)

> 图中的 Query Processor 就是 Planner 的实现

在 Flink Table 新架构中，有两个查询处理器：Flink Query Processor 和 Blink Query Processor，分别对应 Flink Planner（也称之为 Old Planner）和 Blink Planner。查询处理器是 Planner 的具体实现， 通过 parser(解析器)、optimizer(优化器)、codegen(代码生成技术)等流程将 Table API & SQL 作业转换成 Flink Runtime 可识别的 Transformation DAG (由 Transformation 组成的有向无环图，表示作业的转换逻辑)，最终由 Flink Runtime 进行作业的调度和执行。

Old Planner 针对流计算和批处理作业有不同的分支处理，流计算作业底层的 API 是 DataStream API，批处理作业底层的 API 是 DataSet API；而 BBlink Planner 则实现流批作业接口的统一，底层的 API 都是 Transformation。

## 3. Flink Planner vs Blink Planner

Flink Table 的新架构实现了查询处理器的插件化，社区完整保留原有 Flink Planner (Old Planner)，同时又引入了新的 Blink Planner，用户可以自行选择使用 Old Planner 还是 Blink Planner。

在模型上，Old Planner 没有考虑流计算作业和批处理作业的统一，针对流计算作业和批处理作业的实现不尽相同，在底层会分别翻译到 DataStream API 和 DataSet API 上。而 Blink Planner 将批数据集看作 Bounded DataStream (有界流式数据) ，流计算作业和批处理作业最终都会翻译到 Transformation API 上。在架构上，Blink Planner 针对批处理和流计算，分别实现了 BatchPlanner 和 StreamPlanner，两者共用了大部分代码，共享了很多优化逻辑。Old Planner 针对批处理和流计算的代码实现的是完全独立的两套体系，基本没有实现代码和优化逻辑复用。

除了模型和架构上的优点外，Blink Planner 在阿里巴巴集团内部的海量业务场景下沉淀了许多实用功能，集中在三个方面：
- Blink Planner 对代码生成机制做了改进、对部分算子进行了优化，提供了丰富实用的新功能，如维表 JOIN、Top N、MiniBatch、流式去重、聚合场景的数据倾斜优化等新功能。
- Blink Planner 的优化策略是基于公共子图的优化算法，包含了基于成本的优化（CBO）和基于规则的优化（CRO）两种策略，优化更为全面。同时，Blink Planner 支持从 Catalog 中获取数据源的统计信息，这对 CBO 优化非常重要。
- Blink Planner 提供了更多的内置函数，更标准的 SQL 支持，在 Flink 1.9 版本中已经完整支持 TPC-H ，对高阶的 TPC-DS 支持也计划在下一个版本实现。

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-table-sql-planner-evolution-4.png?raw=true)

整体看来，Blink 查询处理器在架构上更为先进，功能上也更为完善。出于稳定性的考虑，Flink 1.9 默认依然使用 Flink Planner，用户如果需要使用 Blink Planner，可以作业中显式指定。

> 两个查询处理器之间的语义和功能大部分是一致的，但并未完全对齐。

## 4. Planner 发展历程

Flink 1.9 到 Flink 1.13 版本，Flink Planner（Old Planner）和 Blink Planner 两种 Planner 一直并存。最终在 Flink 1.14.0 版本将 Old Planner 的所有代码移除，彻底退出历史舞台：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-table-sql-planner-evolution-5.png?raw=true)

- Flink 1.9.0：在这个版本 Blink Planner 尚未完全集成。因此，Flink Planner（Old Planner）仍然是 1.9 版本的默认 Planner，建议在生产环境使用这个 Planner。
- Flink 1.10.0：从这个版本开始 Blink Planner 成为 SQL Client 的默认 Planner。Table API 中 Old Planner 的切换，计划在下一个版本中进行，因此我们建议用户开始熟悉 Blink Planner。具体查阅[FLINK-15495](https://jira.apache.org/jira/browse/FLINK-15495)
- Flink 1.11.0：从这个版本开始 Blink Planner 成为 Table API/SQL 的默认 Planner。Old Planner 仍然在支持，但后续版本中会完全废弃使用。对于生产环境，我们建议可以迁移到 Blink Planner 上。具体查阅[FLINK-17339](https://jira.apache.org/jira/browse/FLINK-17339)
- Flink 1.13.0：从这个版本开始 Old Planner 标记为 Deprecated。Blink Planner 现在已成为一些版本的默认 Planner，以后也将是唯一的一个 Planner。这意味着 BatchTableEnvironment 和 SQL/DataSet 互操作性都即将结束。请使用统一的 TableEnvironment 进行批处理和流处理。具体查阅[FLINK-21709](https://issues.apache.org/jira/browse/FLINK-21709)
- Flink 1.14.0：我们在将 Blink Planner 加入到 Flink 时，就已明确它终将取代原本的 Flink Planner（Old Planner）。Blink 速度更快，功能也更加完整。Blink Planner 成为默认的 Planner 已稳定运行好几个版本。在 Flink 1.14.0，我们终于将旧版 Planner 的所有代码移除了。

## 5. 如何启用 Planner

### 5.1 Flink 1.9 版本

被选择的 Planner 必须要在正在执行的 Java 进程的类路径中。对于集群设置，默认的两个 Planner 都会自动地加载到类路径中。如果你想在 IDE 中本地运行 Table API 或者 SQL 程序，需要在项目中显式地增加 Planner 的依赖：
```xml
<!-- 推荐使用老的 Planner -->
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner_2.11</artifactId>
  <version>1.9.3</version>
</dependency>
<!-- 不建议使用新的 Blink Planner -->
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner-blink_2.11</artifactId>
  <version>1.9.3</version>
</dependency>
```
在内部实现上，Table 生态系统的一部分是基于 Scala 实现的。因此，需要确保为批处理和流式应用程序添加如下依赖项：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-streaming-scala_2.11</artifactId>
  <version>1.9.3</version>
</dependency>
```
如果作业需要运行在集群环境，打包时将 Blink Planner 相关依赖的 scope 设置为 provided，表示这些依赖由集群环境提供。这是因为 Flink 在编译打包时，已经将 Blink Planner 相关的依赖打包，不需要再次引入，避免冲突。

在创建 TableEnvironment 时 EnvironmentSettings 配置中可以不用显示指明 Planner，默认就是使用的 Old Planner：
```java
import org.apache.flink.table.api.EnvironmentSettings;
import org.apache.flink.table.api.TableEnvironment;

EnvironmentSettings settings = EnvironmentSettings
    .newInstance()
    //.useOldPlanner()
    .inStreamingMode()
    //.inBatchMode()
    .build();

TableEnvironment tEnv = TableEnvironment.create(settings);
```
Blink Planner 尚未完全集成，不推荐使用：
```java
EnvironmentSettings settings = EnvironmentSettings
    .newInstance()
    .useBlinkPlanner()
    .inStreamingMode()
    .build();
TableEnvironment tEnv = TableEnvironment.create(settings);
```
也可以从现有的 StreamExecutionEnvironment 中创建 StreamTableEnvironment 以与 DataStream API 进行互操作：
```java
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.table.api.EnvironmentSettings;
import org.apache.flink.table.api.java.StreamTableEnvironment;

StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);
```

### 5.2 Flink 1.13 版本

如果你想在 IDE 中本地运行 Table API 或者 SQL 程序，需要在项目中显式地增加 Planner 的依赖：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner-blink_2.11</artifactId>
  <version>1.13.6</version>
</dependency>

<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-streaming-scala_2.11</artifactId>
  <version>1.13.6</version>
</dependency>
```
> 如果作业需要运行在集群环境，打包时将 Blink Planner 相关依赖的 scope 设置为 provided

在创建 TableEnvironment 时 EnvironmentSettings 配置中不用显示指明 Planner，默认就是使用的 Blink Planner：
```java
import org.apache.flink.table.api.EnvironmentSettings;
import org.apache.flink.table.api.TableEnvironment;

EnvironmentSettings settings = EnvironmentSettings
    .newInstance()
    //.useBlinkPlanner()
    .inStreamingMode()
    //.inBatchMode()
    .build();

TableEnvironment tEnv = TableEnvironment.create(settings);
```
Old Planner 已经被标记为 Deprecated，不在推荐使用：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-table-sql-planner-evolution-6.png?raw=true)

也可以从现有的 StreamExecutionEnvironment 中创建 StreamTableEnvironment 以与 DataStream API 进行互操作：
```java
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.table.api.EnvironmentSettings;
import org.apache.flink.table.api.bridge.java.StreamTableEnvironment;

StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);
```

### 5.3 Flink 1.14 版本

如果你想在 IDE 中本地运行 Table API 或者 SQL 程序，需要在项目中显式地增加 Planner 的依赖：
```xml
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-table-planner_2.11</artifactId>
  <version>1.14.4</version>
</dependency>

<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-streaming-scala_2.11</artifactId>
  <version>1.14.4</version>
</dependency>
```
> 如果作业需要运行在集群环境，打包时将 Blink Planner 相关依赖的 scope 设置为 provided

在创建 TableEnvironment 时 EnvironmentSettings 配置中不用显示指明 Planner，默认就是使用的 Blink Planner（也是唯一一个）：
```java
import org.apache.flink.table.api.EnvironmentSettings;
import org.apache.flink.table.api.TableEnvironment;

EnvironmentSettings settings = EnvironmentSettings
    .newInstance()
    .inStreamingMode()
    //.inBatchMode()
    .build();

TableEnvironment tEnv = TableEnvironment.create(settings);
```
如果指定 Old Planner 会抛出异常。可以看到如下所示在 Flink 1.14 版本中 Old Planner 已经被移除：
```java
@Deprecated
public Builder useOldPlanner() {
    throw new TableException(
            "The old planner has been removed in Flink 1.14. "
                    + "Please upgrade your table program to use the default "
                    + "planner (previously called the 'blink' planner).");
}
```
由于 Old Planner 已经被移除，Blink Planner 成为唯一一个 Planner，因此不再需要指定使用的是哪一个 Planner，useBlinkPlanner 方法在后续版本中也会被删除：
```java
@Deprecated
public Builder useBlinkPlanner() {
    return this;
}
```

也可以从现有的 StreamExecutionEnvironment 中创建 StreamTableEnvironment 以与 DataStream API 进行互操作：
```java
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.table.api.EnvironmentSettings;
import org.apache.flink.table.api.bridge.java.StreamTableEnvironment;

StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tEnv = StreamTableEnvironment.create(env);
```

参考：
- [Apache Flink 1.9.0 Release Announcement](https://flink.apache.org/news/2019/08/22/release-1.9.0.html)
- [Apache Flink 1.10.0 Release Announcement](https://flink.apache.org/news/2020/02/11/release-1.10.0.html)
- [Apache Flink 1.11.0 Release Announcement](https://flink.apache.org/news/2020/07/06/release-1.11.0.html)
- [Apache Flink 1.13.0 Release Announcement](https://flink.apache.org/news/2021/05/03/release-1.13.0.html)
- [Apache Flink 1.14.0 Release Announcement](https://flink.apache.org/news/2021/09/29/release-1.14.0.html)
- [Flink SQL 系列 | 开篇，新架构与 Planner](https://mp.weixin.qq.com/s/zyM-pvV1v4bPcDuNQGju6g)
- [修改代码150万行！Apache Flink 1.9.0做了这些重大修改！](https://mp.weixin.qq.com/s/qcS4FQdSHaZaU52ELEBqBw)
