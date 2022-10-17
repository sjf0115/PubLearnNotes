
## 1. 流计算须知

- [x] [Streaming 101:批处理之外的流式世界第一部分](https://smartsi.blog.csdn.net/article/details/122692636)
- [x] [Streaming 102:批处理之外的流式世界第二部分](https://smartsi.blog.csdn.net/article/details/122913457)
- [x] [Exactly once 未必严格一次](https://smartsi.blog.csdn.net/article/details/126456735)

## 2. 基础

- [x] [Flink 安装与启动](https://blog.csdn.net/SunnyYoona/article/details/78276595)
- [x] [构建 Flink 第一个应用程序](https://blog.csdn.net/SunnyYoona/article/details/126087865)
- [x] [Flink 中如何解析与传递参数](https://smartsi.blog.csdn.net/article/details/126534721)
- [x] [Flink 程序剖析](https://smartsi.blog.csdn.net/article/details/126088002)
- [x] [Flink 如何指定并发](https://smartsi.blog.csdn.net/article/details/126535786)
- [x] [4 个步骤让 Flink 应用程序达到生产状态](https://smartsi.blog.csdn.net/article/details/126682174)
- [ ] [Flink 数据交换策略 Partitioner]()
- [x] [Flink 任务失败重启与恢复策略](https://smartsi.blog.csdn.net/article/details/126451162)
- [ ] [Flink 与 SPI]()

## 3. DataStream

### 3.1 时间概念与 Watermark

- [x] [Flink 事件时间与处理时间](https://smartsi.blog.csdn.net/article/details/126554454)
- [x] [Flink 如何现实新的流处理应用第一部分:事件时间与无序处理](https://smartsi.blog.csdn.net/article/details/126551181)
- [x] [Flink 轻松理解 Watermark](https://smartsi.blog.csdn.net/article/details/126684369)
- [x] [Flink 图解 Watermark](https://smartsi.blog.csdn.net/article/details/126688873)
- [x] [Flink Watermark 机制](https://smartsi.blog.csdn.net/article/details/126689246)
- [x] [Flink 1.10 版本之前如何生成 Watermark](https://smartsi.blog.csdn.net/article/details/126563487)
- [x] [Flink 1.11+ 版本如何生成 Watermark](https://smartsi.blog.csdn.net/article/details/126791104)
- [x] [Flink 定时器的4个特性](https://smartsi.blog.csdn.net/article/details/126714638)
- [x] [Flink 源码解读系列 DataStream 带 Watermark 生成的时间戳分配器](https://smartsi.blog.csdn.net/article/details/126797894)

### 3.2 Window 窗口

- [x] [Flink 窗口 Window 介绍](https://smartsi.blog.csdn.net/article/details/126554021)
- [ ] [Flink 窗口开始时间如何计算]()
- [x] [Flink 窗口分配器 WindowAssigner](https://smartsi.blog.csdn.net/article/details/126652876)
- [x] [Flink 原理与实现：Session Window](https://smartsi.blog.csdn.net/article/details/126614957)
- [x] [Flink 窗口函数 WindowFunction](https://smartsi.blog.csdn.net/article/details/126681922)
- [ ] [Flink 窗口触发器 Trigger]()
- [ ] [Flink 窗口剔除器 Evictor]()
- [x] [Flink 源码解读系列 DataStream 窗口 Winow 实现](https://smartsi.blog.csdn.net/article/details/126574164)
- [x] [Flink 源码解读系列 DataStream 窗口分配器 WinowAssigner](https://smartsi.blog.csdn.net/article/details/126594720)

### 3.3 Function

- [x] [Flink DataStream 类型系统 TypeInformation](https://smartsi.blog.csdn.net/article/details/124333830)
- [x] [Flink 指定 keys 的几种方法](https://smartsi.blog.csdn.net/article/details/126417116)
- [ ] [Flink 如何使用算子]()
- [x] [Flink DataStream 处理函数 ProcessFunction 和 KeyedProcessFunction](https://smartsi.blog.csdn.net/article/details/126851094)
- [x] [Flink DataStream Split 实现分流](https://smartsi.blog.csdn.net/article/details/126737446)
- [x] [Flink DataStream 侧输出流 Side Output](https://smartsi.blog.csdn.net/article/details/126737944)
- [x] [Flink SourceFunction 初了解](https://smartsi.blog.csdn.net/article/details/123342142)
- [ ] [Flink DataStream 如何实现双流Join]()
- [x] [Flink DataStream Java Lambda 表达式的限制](https://smartsi.blog.csdn.net/article/details/120661028)
- [x] [影响 Flink 有状态函数和算子性能的 3 个重要因素](https://smartsi.blog.csdn.net/article/details/126550984)

## 4. Table & SQL

### 4.1 基础

- [ ] [Flink SQL 动态表的持续查询]()
- [x] [深入分析 Flink SQL 工作机制](https://smartsi.blog.csdn.net/article/details/127195605)
- [x] [Flink 1.9 Table & SQL 第一个程序 WordCount](https://smartsi.blog.csdn.net/article/details/124062998)
- [x] [Flink 1.14 Table API & SQL 第一个程序 WordCount](https://smartsi.blog.csdn.net/article/details/124110710)
- [x] [Flink Table API & SQL Planner 演变](https://smartsi.blog.csdn.net/article/details/124159459)
- [x] [Flink Table API & SQL 类型系统 DataType](https://smartsi.blog.csdn.net/article/details/124555713)
- [ ] [Flink Table API & SQL TableEnvironment]()
- [ ] [Flink Table API & SQL 重构优化 TableEnviromnent 接口]()
- [x] [Flink Table API & SQL 基本操作](https://smartsi.blog.csdn.net/article/details/124205430)
- [ ] [Flink Table 与 Stream 相互转换]()
- [x] [Flink SQL 客户端如何使用](https://smartsi.blog.csdn.net/article/details/124460822)
- [x] [Flink Table API & SQL 如何定义时间属性](https://smartsi.blog.csdn.net/article/details/127173096)
- [x] [Flink SQL Emit 输出策略](https://smartsi.blog.csdn.net/article/details/127196376)

### 4.2 函数

- [x] [Flink SQL 分组窗口函数 Group Window 实战](https://smartsi.blog.csdn.net/article/details/127178520)
- [x] [Flink SQL 窗口表值函数 Window TVF 实战](https://smartsi.blog.csdn.net/article/details/127162902)
- [x] [Flink SQL 功能解密系列 —— 流式 TopN 挑战与实现](https://smartsi.blog.csdn.net/article/details/127378780)
- [ ] [Flink SQL 自定义函数]()
- [x] [Flink Table API & SQL 自定义 Scalar 标量函数](https://smartsi.blog.csdn.net/article/details/124853175)
- [x] [Flink Table API & SQL 自定义 Table 表函数](https://smartsi.blog.csdn.net/article/details/124874280)
- [x] [Flink Table API & SQL 自定义 Aggregate 聚合函数](https://smartsi.blog.csdn.net/article/details/124891129)
- [ ] [Flink SQL 自定义 Source]()
- [ ] [Flink SQL 自定义 Sink]()
- [ ] [Flink SQL 自定义 Format]()
- [ ] [Flink SQL Catalogs]()
- [ ] [Flink SQL 与 Hive 的集成]()

### 4.3 性能优化

- [x] [Flink SQL 功能解密系列 解决热点问题的大杀器 MiniBatch](https://smartsi.blog.csdn.net/article/details/127201264)
- [x] [Flink SQL 核心解密 —— 提升吞吐的利器 MicroBatch](https://smartsi.blog.csdn.net/article/details/127209707)
- [ ] [Flink SQL 性能优化]()

## 5. 容错

### 5.1 状态

- [x] [Flink 状态分类](https://smartsi.blog.csdn.net/article/details/123296073)
- [x] [Flink 状态管理和容错机制介绍](https://smartsi.blog.csdn.net/article/details/126551467)
- [x] [Flink 状态 TTL 如何限制状态的生命周期](https://smartsi.blog.csdn.net/article/details/127118930)
- [x] [Flink State TTL 详解](https://smartsi.blog.csdn.net/article/details/123221583)
- [ ] [Flink 使用 Broadcast State 的 4 个注意事项]()
- [ ] [Flink Broadcast State 实战指南]()
- [x] [Flink 可查询状态是如何工作的](https://smartsi.blog.csdn.net/article/details/127118986)
- [x] [State Processor API：如何读写和修改 Flink 应用程序的状态](https://smartsi.blog.csdn.net/article/details/123265728)
- [x] [深入了解 Flink 的可扩展性状态](https://smartsi.blog.csdn.net/article/details/121006448)

### 5.2 StateBackend

- [x] [有状态流处理:Flink 状态后端](https://smartsi.blog.csdn.net/article/details/126682122)
- [x] [Flink 1.13 State Backend 优化及生产实践](https://smartsi.blog.csdn.net/article/details/123057769)
- [x] [Flink 1.13 StateBackend 与 CheckpointStorage 拆分](https://smartsi.blog.csdn.net/article/details/123057769)
- [x] [Flink 1.13 新版状态后端 StateBackend 详解](https://smartsi.blog.csdn.net/article/details/127118745)
- [ ] [Flink 如何管理 RocksDB 内存大小]()
- [ ] [Flink 何时以及如何使用 RocksDB 状态后端]()

### 5.3 Savepoint & Checkpoint

- [x] [分布式数据流的轻量级异步快照](https://smartsi.blog.csdn.net/article/details/127080910)
- [x] [Flink 容错机制 Checkpoint 生成与恢复流程](https://smartsi.blog.csdn.net/article/details/127019291)
- [x] [Flink 启用与配置检查点 Checkpoint](https://smartsi.blog.csdn.net/article/details/127038694)
- [x] [Flink 管理大型状态之增量 Checkpoint](https://smartsi.blog.csdn.net/article/details/127021174)
- [x] [Flink 1.11 非对齐检查点 Unaligned Checkpoint 简介](https://smartsi.blog.csdn.net/article/details/127135982)
- [x] [Flink 1.11 Unaligned Checkpoint 详解](https://blog.csdn.net/SunnyYoona/article/details/127142421)
- [ ] [Flink 1.13 新检查点存储 CheckpointStorage]()
- [x] [Flink 利用 Checkpoint 实现故障恢复](https://smartsi.blog.csdn.net/article/details/127130006)
- [x] [Flink 监控检查点 Checkpoint](https://smartsi.blog.csdn.net/article/details/127038971)
- [x] [Flink Checkpoint 问题排查实用指南](https://smartsi.blog.csdn.net/article/details/127019399)
- [ ] [Flink 在大规模状态下的 Checkpoint 调优]()
- [x] [Flink Savepoint 机制](https://smartsi.blog.csdn.net/article/details/126534751)
- [x] [Flink 保存点之回溯时间](https://smartsi.blog.csdn.net/article/details/126474904)
- [x] [Flink 如何实现新的流处理应用第二部分:版本化状态](https://smartsi.blog.csdn.net/article/details/126551289)
- [x] [Flink Savepoints 和 Checkpoints 的 3 个不同点](https://smartsi.blog.csdn.net/article/details/126475549)

### 5.4 一致性保障

- [x] [Flink Exactly-Once 投递实现浅析](https://smartsi.blog.csdn.net/article/details/126494280)
- [ ] [Flink 如何实现端到端的 Exactly-Once 处理语义]()

## 6. Connector

### 6.1 DataStream

- [ ] [Flink HDFS Connector]()
- [ ] [Flink Kafka Connector]()
- [x] [Flink 如何管理 Kafka 的消费偏移量](https://smartsi.blog.csdn.net/article/details/126475307)

### 6.2 Table & SQL

- [x] [Flink Table API & SQL DataGen Connector](https://smartsi.blog.csdn.net/article/details/127200907)
- [ ] [Flink SQL Kafka Connector]()
- [x] [Flink JDBC Connector：Flink 与数据库集成最佳实践](https://smartsi.blog.csdn.net/article/details/126535909)
- [x] [Flink SQL Print Connector](https://smartsi.blog.csdn.net/article/details/124086562)
- [x] [Flink SQL 1.11 流批一体 Hive 数仓](https://smartsi.blog.csdn.net/article/details/121061979)

## 7. 运维与监控

- [x] [Flink 本地运行 Web UI](https://smartsi.blog.csdn.net/article/details/124742662)
- [ ] [在 Zeppelin 中如何使用 Flink]()
- [x] [Flink 网络流控和反压剖析详解](https://smartsi.blog.csdn.net/article/details/127312894)
- [ ] [Flink 如何定位背压来源]()
- [x] [Flink 如何处理背压](https://smartsi.blog.csdn.net/article/details/127355152)
- [x] [Flink 监控 Rest API](https://smartsi.blog.csdn.net/article/details/126087582)
- [ ] [Flink 单元测试指南]()
- [ ] [Flink 1.11 JobManager 内存管理优化]()
- [ ] [Flink 1.10 TaskManager 内存管理优化]()

## 8. CDC

- [x] [为什么选择基于日志的 CDC](https://smartsi.blog.csdn.net/article/details/120675143)
- [x] [Flink CDC 原理、实践和优化](https://blog.csdn.net/SunnyYoona/article/details/126377748?spm=1001.2014.3001.5501)
