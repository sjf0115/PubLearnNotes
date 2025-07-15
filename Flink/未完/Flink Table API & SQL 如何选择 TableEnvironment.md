## 1. TableEnvironment 是什么

TableEnvironment 是用来创建 Table & SQL 程序的上下文执行环境，也是 Table & SQL 程序的入口，Table & SQL 程序的所有功能都是围绕 TableEnvironment 这个核心类展开的。TableEnvironment 的主要职能包括：
- 注册 Catlog
- 在内部 Catlog 中注册表
- 加载可插拔模块
- 执行 SQL 查询
- 注册用户自定义函数
- DataStream 和 Table 之间的转换（在 StreamTableEnvironment 的情况下）
- 提供更详细的配置选项

每个 Table 和 SQL 的执行，都必须绑定在一个表环境 TableEnvironment 中。不能在同一个查询中使用不同的 TableEnvironments 下的表。

## 2. 如何选择 TableEnvironment

Flink 1.9 中保留了 5 个 TableEnvironment，在实现上是 5 个面向用户的接口，在接口底层进行了不同的实现。5 个接口包括一个 TableEnvironment 接口，两个 BatchTableEnvironment 接口，两个 StreamTableEnvironment 接口：

![]()

从这五个 TableEnvironment 支持的作业类型 ( Stream 作业和 Batch 作业)，支持的 API 类型（DataStream API 和 DataSet API)，以及对 UDTF/UDAF 的支持这 5 个方面进行对比，各个TableEnvironment 支持的功能可以归纳如下：

![]()

### 2.1 TableEnvironment

TableEnvironment 作为统一的接口，其统一性体现在两个方面：
- 一是对于所有基于 JVM 的语言是统一的，即 Scala API 和 Java API 之间没有区别；
- 二是对于 unbounded data （无界数据，即流数据） 和 bounded data （有界数据，即批数据）的处理是统一的。

TableEnvironment 提供的是一个纯 Table 生态的上下文环境，适用于整个作业只使用 Table API & SQL 编写程序的场景。如果你想与 DataStream/DataSet 相互转换，你需要使用相应桥接模块中的 TableEnvironment。此外，TableEnvironment 目前还不支持注册 UDTF 和 UDAF，用户有注册 UDTF 和 UDAF 的需求时，也需要使用其他 TableEnvironment。

TableEnvironment 是 Table API 中提供的基本接口类，可以通过调用静态的 create() 方法来创建一个 TableEnvironment 实例。方法可以传入一个环境的配置参数 EnvironmentSettings，可以指定当前 TableEnvironment 的执行模式和计划器 Planner。执行模式有批处理和流处理两种选择，默认是流处理模式；计划器默认使用 blink planner。

### 2.2 StreamTableEnvironment

两个 StreamTableEnvironment 分别用于 Java 和 Scala 的流计算场景，流计算的对象分别是 Java 和 Scala 的 DataStream。相比 TableEnvironment，StreamTableEnvironment 提供了 DataStream 和 Table 之间相互转换的接口：
- fromDataStream
- fromChangelogStream
- createTemporaryView
- toDataStream
- toChangelogStream
- toAppendStream
- toRetractStream

如果用户的程序除了使用 Table API & SQL 编写外，还需要使用到 DataStream API，则需要使用 StreamTableEnvironment。    

### 2.3 BatchTableEnvironment

两个 BatchTableEnvironment 分别用于 Java 的批处理场景和 Scala 的批处理场景，批处理的对象分别是 Java 的 DataSet 和 Scala 的 DataSet。相比 TableEnvironment，BatchTableEnvironment 提供了 DataSet 和 Table 之间相互转换的接口，如果用户的程序除了使用 Table API & SQL 编写外，还需要使用到 DataSet API，则需要使用 BatchTableEnvironment。    

## 3. 如何使用

使用 Old Planner，进行流计算的 Table 程序（使用 Table API 或 SQL 进行开发的程序 ）的开发。这种场景下，用户可以使用 StreamTableEnvironment 或 TableEnvironment ，两者的区别是 StreamTableEnvironment 额外提供了与 DataStream API 交互的接口。示例代码如下：
```java
// 1. 老的 Planner & 流处理模式
EnvironmentSettings settings = EnvironmentSettings
        .newInstance()
        .useOldPlanner()
        .inStreamingMode()
        .build();

StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env, settings);
```

Old Planner 将在 Flink 1.14 版本中删除。需要切换到新的 Planner 上，即 Blink Planner。




https://mp.weixin.qq.com/s/HMGOl2YmWBDo4uYfgu7l8w
