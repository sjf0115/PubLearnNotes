
## 1. 流计算须知

- [x] [Streaming 101:批处理之外的流式世界第一部分](https://smartsi.blog.csdn.net/article/details/122692636)
- [x] [Streaming 102:批处理之外的流式世界第二部分](https://smartsi.blog.csdn.net/article/details/122913457)
- [x] [Exactly once 未必严格一次](https://smartsi.blog.csdn.net/article/details/126456735?spm=1001.2014.3001.5502)

## 2. 基础

- [x] [Flink 安装与启动](https://blog.csdn.net/SunnyYoona/article/details/78276595)
- [x] [构建 Flink 第一个应用程序](https://blog.csdn.net/SunnyYoona/article/details/126087865)
- [x] [Flink 中如何解析与传递参数](https://smartsi.blog.csdn.net/article/details/126534721?spm=1001.2014.3001.5502)
- [x] [Flink 程序剖析](https://smartsi.blog.csdn.net/article/details/126088002)
- [x] [Flink 如何指定并发](https://smartsi.blog.csdn.net/article/details/126535786?spm=1001.2014.3001.5502)
- [ ] [4 个步骤让 Flink 应用程序达到生产状态]()
- [ ] [Flink 数据交换策略 Partitioner]()
- [x] [Flink 任务失败重启与恢复策略](https://smartsi.blog.csdn.net/article/details/126451162?spm=1001.2014.3001.5502)
- [ ] [Flink 与 SPI]()

## 3. DataStream

### 3.1 时间概念与 Watermark

- [ ] [Flink 事件时间与处理时间]()
- [x] [Flink 如何现实新的流处理应用第一部分:事件时间与无序处理](https://smartsi.blog.csdn.net/article/details/126551181)
- [ ] [Flink 轻松理解 Watermark]()
- [ ] [Flink Watermark 机制]()
- [ ] [Flink 在1.10版本之前如何生成 Watermark]()
- [ ] [Flink 1.11版本如何生成 Watermark]()

### 3.2 Window 窗口

- [ ] [Flink 窗口 Window 机制]()
- [ ] [Flink 窗口如何使用]()
- [ ] [Flink 窗口剔除器 Evictor]()
- [ ] [Flink 窗口触发器 Trigger]()
- [ ] [Flink 窗口函数 WindowFunction]()
- [ ] [Flink 定时器的4个特性]()

### 3.3 Function

- [x] [Flink DataStream 类型系统 TypeInformation](https://smartsi.blog.csdn.net/article/details/124333830)
- [x] [Flink 指定 keys 的几种方法](https://smartsi.blog.csdn.net/article/details/126417116?spm=1001.2014.3001.5502)
- [ ] [Flink 如何使用算子]()
- [ ] [Flink 如何使用 ProcessFunction]()
- [x] [Flink SourceFunction 初了解](https://smartsi.blog.csdn.net/article/details/123342142)
- [ ] [Flink DataStream 如何实现双流Join]()
- [x] [Flink DataStream Java Lambda 表达式的限制](https://smartsi.blog.csdn.net/article/details/120661028)
- [x] [影响 Flink 有状态函数和算子性能的 3 个重要因素](影响 Flink 有状态函数和算子性能的 3 个重要因素)

## 4. Table & SQL

- [ ] [Flink SQL 动态表的持续查询]()
- [x] [Flink 1.9 Table & SQL 第一个程序 WordCount](https://smartsi.blog.csdn.net/article/details/124062998)
- [x] [Flink 1.14 Table API & SQL 第一个程序 WordCount](https://smartsi.blog.csdn.net/article/details/124110710)
- [x] [Flink Table API & SQL Planner 演变](https://smartsi.blog.csdn.net/article/details/124159459)
- [x] [Flink Table API & SQL 类型系统 DataType](https://smartsi.blog.csdn.net/article/details/124555713)
- [ ] [Flink Table API & SQL TableEnvironment]()
- [ ] [Flink Table API & SQL 重构优化 TableEnviromnent 接口]()
- [x] [Flink Table API & SQL 基本操作](https://smartsi.blog.csdn.net/article/details/124205430)
- [ ] [Flink Table 与 Stream 相互转换]()
- [x] [Flink SQL 客户端如何使用](https://smartsi.blog.csdn.net/article/details/124460822)
- [ ] [Flink SQL 如何定义时间属性]()
- [ ] [Flink SQL 窗口]()
- [ ] [Flink SQL TVF]()
- [ ] [Flink SQL 自定义函数]()
- [x] [Flink Table API & SQL 自定义 Scalar 标量函数](https://smartsi.blog.csdn.net/article/details/124853175)
- [x] [Flink Table API & SQL 自定义 Table 表函数](https://smartsi.blog.csdn.net/article/details/124874280)
- [x] [Flink Table API & SQL 自定义 Aggregate 聚合函数](https://smartsi.blog.csdn.net/article/details/124891129)
- [ ] [Flink SQL 自定义 Source]()
- [ ] [Flink SQL 自定义 Sink]()
- [ ] [Flink SQL 自定义 Format]()
- [ ] [Flink SQL Catalogs]()
- [ ] [Flink SQL 与 Hive 的集成]()
- [ ] [Flink SQL 性能优化]()

## 5. 容错

### 5.1 状态

- [x] [Flink 状态分类](https://smartsi.blog.csdn.net/article/details/123296073)
- [ ] [Flink 使用 Broadcast State 的4个注意事项]()
- [ ] [Flink Broadcast State 实战指南]()
- [ ] [Flink 状态TTL如何限制状态的生命周期]()
- [x] [Flink State TTL 详解](https://smartsi.blog.csdn.net/article/details/123221583)
- [ ] [Flink 中可查询状态是如何工作的]()
- [x] [State Processor API：如何读写和修改 Flink 应用程序的状态](https://smartsi.blog.csdn.net/article/details/123265728)
- [x] [Flink 1.13 State Backend 优化及生产实践](https://smartsi.blog.csdn.net/article/details/123057769)
- [x] [深入了解 Flink 的可扩展性状态](https://smartsi.blog.csdn.net/article/details/121006448)

### 5.2 StateBackend

- [ ] [有状态流处理:Flink 状态后端]()
- [x] [Flink 1.13 StateBackend 与 CheckpointStorage 拆分](https://smartsi.blog.csdn.net/article/details/123057769)
- [ ] [Flink 如何管理 RocksDB 内存大小]()
- [ ] [Flink 何时以及如何使用 RocksDB 状态后端]()

### 5.3 Savepoint & Checkpoint

- [x] [Flink Savepoint 机制](https://smartsi.blog.csdn.net/article/details/126534751)
- [x] [Flink 保存点之回溯时间](https://smartsi.blog.csdn.net/article/details/126474904?spm=1001.2014.3001.5502)
- [x] [Flink 如何实现新的流处理应用第二部分:版本化状态](https://smartsi.blog.csdn.net/article/details/126551289)
- [ ] [Flink 检查点启用与配置]()
- [x] [Flink Savepoints 和 Checkpoints 的 3 个不同点](https://smartsi.blog.csdn.net/article/details/126475549?spm=1001.2014.3001.5502)
- [ ] [Flink 管理大型状态之增量 Checkpoint]()
- [ ] [Flink 从Checkpoint中恢复作业]()
- [ ] [Flink 监控检查点]()

### 5.4 一致性保障

- [x] [Flink Exactly-Once 投递实现浅析](https://smartsi.blog.csdn.net/article/details/126494280?spm=1001.2014.3001.5502)
- [ ] [Flink 如何实现端到端的 Exactly-Once 处理语义]()

## 6. Connector

### 6.1 DataStream

- [ ] [Flink HDFS Connector]()
- [ ] [Flink Kafka Connector]()
- [x] [Flink 如何管理 Kafka 的消费偏移量](https://smartsi.blog.csdn.net/article/details/126475307?spm=1001.2014.3001.5502)

### 6.2 Table & SQL

- [ ] [Flink SQL Kafka Connector]()
- [x] [Flink JDBC Connector：Flink 与数据库集成最佳实践](https://smartsi.blog.csdn.net/article/details/126535909)
- [x] [Flink SQL Print Connector](https://smartsi.blog.csdn.net/article/details/124086562)
- [x] [Flink SQL 1.11 流批一体 Hive 数仓](https://smartsi.blog.csdn.net/article/details/121061979)


## 7. 运维与监控

- [x] [Flink 本地运行 Web UI](https://smartsi.blog.csdn.net/article/details/124742662)
- [ ] [在 Zeppelin 中如何使用 Flink]()
- [ ] [Flink 如何定位背压来源]()
- [ ] [Flink 如何处理背压]()
- [x] [Flink 监控 Rest API](https://smartsi.blog.csdn.net/article/details/126087582)
- [ ] [Flink 单元测试指南]()
- [ ] [Flink 1.11 JobManager 内存管理优化]()
- [ ] [Flink 1.10 TaskManager 内存管理优化]()

## 8. CDC

- [x] [为什么选择基于日志的 CDC](https://smartsi.blog.csdn.net/article/details/120675143)
- [x] [Flink CDC 原理、实践和优化](https://blog.csdn.net/SunnyYoona/article/details/126377748?spm=1001.2014.3001.5501)
