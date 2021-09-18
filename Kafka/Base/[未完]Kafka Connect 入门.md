### 1. 什么是 Kafka Connect

首先 Connect 是 Kafka 的一部分，为 Kafka 和其他系统之间传输数据提供了一种可靠且可扩展的方案。Kafka Connect 可以获取整个数据库或从所有应用程序服务器收集监控指标到 Kafka Topic 中，从而为低延迟的流处理提供数据支撑。也可以将数据从 Kafka Topic 导出到二级存储、查询系统或者批处理系统从而进行离线分析。

这是 Apache Kafka 0.9+ 中的一项新功能，它使构建和管理流数据管道变得更加容易。

Kafka Connect功能包括：

一个通用的Kafka连接的框架 - Kafka Connect规范化了其他数据系统与Kafka的集成，简化了连接器开发，部署和管理
分布式和独立模式 - 支持大型分布式的管理服务，也支持小型生产环境的部署
REST界面 - 通过易用的REST API提交和管理Kafka Connect
自动偏移管理 - 只需从连接器获取一些信息，Kafka Connect就可以自动管理偏移量提交过程，因此连接器开发人员无需担心连接器开发中偏移量提交这部分的开发
默认情况下是分布式和可扩展的 - Kafka Connect构建在现有的组管理协议之上。可以添加扩展集群
流媒体/批处理集成 - 利用Kafka现有的功能，Kafka Connect是桥接流媒体和批处理数据系统的理想解决方案

### 2. Connect 架构

### 3. 什么场景下使用 Connect

### 4. 核心概念

### 5. 怎么运行Connect
