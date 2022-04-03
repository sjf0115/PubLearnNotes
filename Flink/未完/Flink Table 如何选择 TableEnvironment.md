## 1. TableEnvironment 是什么

TableEnvironment 是用来创建 Table & SQL 程序的上下文执行环境，也是 Table & SQL 程序的入口，Table & SQL 程序的所有功能都是围绕 TableEnvironment 这个核心类展开的。TableEnvironment 的主要职能包括：
- 注册 Catlog
- 在内部 Catlog 中注册表
- 加载可插拔模块
- 执行 SQL 查询
- 注册用户自定义函数
- DataStream 和 Table 之间的转换（在 StreamTableEnvironment 的情况下）
- 提供更详细的配置选项

一个 Table 总是绑定到一个特定的 TableEnvironment。不能在同一个查询中使用不同的 TableEnvironments 下的表。

## 2. 如何选择 TableEnvironment

Flink 1.9 中保留了 5 个 TableEnvironment，在实现上是 5 个面向用户的接口，在接口底层进行了不同的实现。5 个接口包括一个 TableEnvironment 接口，两个 BatchTableEnvironment 接口，两个 StreamTableEnvironment 接口，5 个接口文件完整路径如下：




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
