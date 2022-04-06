---
layout: post
author: sjf0115
title: DataX 异构数据源离线同步
date: 2022-04-06 17:17:17
tags:
  - DataX

categories: DataX
permalink: datax-introduction
---

> DataX 版本：3.0

> Github主页地址：https://github.com/alibaba/DataX

## 1. 简介

DataX 是一个异构数据源离线同步工具，致力于实现包括关系型数据库(MySQL、Oracle等)、HDFS、Hive、ODPS、HBase、FTP 等各种异构数据源之间稳定高效的数据同步功能。

![](https://github.com/sjf0115/ImageBucket/blob/main/DataX/datax-introduction-1.png?raw=true)

为了解决异构数据源同步问题，DataX 将复杂的网状的同步链路变成了星型数据链路，DataX 作为中间传输载体负责连接各种数据源。当需要接入一个新的数据源的时候，只需要将此数据源对接到 DataX，便能跟已有的数据源做到无缝数据同步。

DataX 在阿里巴巴集团内被广泛使用，承担了所有大数据的离线同步业务，并已持续稳定运行了 N 年之久。目前每天完成同步 8w 多道作业，每日传输数据量超过 300TB。

## 2. 架构

![](https://github.com/sjf0115/ImageBucket/blob/main/DataX/datax-introduction-2.png?raw=true)

DataX 本身作为离线数据同步框架，采用 Framework + Plugin 架构的模式构建。将数据源读取和写入分别抽象为 Reader 和 Writer 插件，并纳入到整个同步框架中：
- Reader：作为数据采集模块，负责数据源数据的采集，并将数据发送给 Framework。
- Writer：作为数据写入模块，负责从 Framework 中不断的取数据，并将数据写入到目的端。
- Framework：用于连接 Reader 和 Writer，作为两者的数据传输通道，并处理缓冲，流控，并发，数据转换等核心技术问题。

## 3. 运行原理

DataX 3.0 开源版本支持单机多线程模式完成同步作业运行，一个 DataX 作业生命周期的时序图如下：

![](https://github.com/sjf0115/ImageBucket/blob/main/DataX/datax-introduction-3.png?raw=true)

- 生成 Job：DataX 完成单个数据同步的作业称之为 Job。DataX 接收到一个 Job 之后，将启动一个进程来完成整个作业同步。Job 是单个作业的中枢管理节点，承担了数据清理、子任务切分(将单一作业计算转化为多个子 Task)、TaskGroup 管理等功能。
- Task 切分：Job 启动后，会根据不同的源端切分策略，将 Job 切分成多个小的 Task(子任务)，以便于并发执行。Task 是 DataX 作业的最小单元，每一个 Task 都会负责一部分数据的同步工作。
- 调度 Task：切分多个 Task 之后，Job 会调用 Scheduler，根据配置的并发数据量，将拆分成的 Task 重新组合为 TaskGroup (任务组)。每一个 TaskGroup 负责以一定的并发运行分配好的 Task。默认单个 TaskGroup 的并发数量为 5。
- 运行 Task：每一个 Task 都由 TaskGroup 负责启动。Task 启动后，会固定启动 Reader—>Channel—>Writer 的线程来完成任务同步工作。

DataX 作业运行起来之后， Job 监控并等待多个 TaskGroup 任务的完成，等待所有 TaskGroup 任务完成后 Job 成功退出，否则异常退出。我们举一个具体的例子，假设用户提交了一个 DataX 作业，并且配置了 20 个并发，目的是将一个 100 张分表的 MySQL 数据同步到 Hive 里面。DataX 的调度决策思路是：
- DataX Job 根据分库分表切分成了 100 个 Task。
- 配置 20 个并发，由于每个 TaskGroup 能并发处理 5 个 Task，所以需要分配 4 个 TaskGroup。
- 4 个 TaskGroup 平分切分好 100 个 Task，每一个 TaskGroup 以 5 个并发来运行 25 个 Task。

## 4. 插件体系

经过几年积累，DataX 目前已经有了比较全面的插件体系，主流的 RDBMS 数据库、NOSQL、大数据计算系统都已经接入。DataX 目前支持数据如下：

![](https://github.com/sjf0115/ImageBucket/blob/main/DataX/datax-introduction-4.png?raw=true)

DataX Framework 提供了简单的接口与插件交互，提供简单的插件接入机制，只需要任意加上一种插件，就能无缝对接其他数据源。

## 5. 核心优势

### 5.1 可靠的数据质量监控

(1) 完美解决数据传输个别类型失真问题
DataX 旧版对于部分数据类型(比如时间戳)传输一直存在毫秒阶段等数据失真情况，新版本 DataX 3.0 已经做到支持所有的强数据类型，每一种插件都有自己的数据类型转换策略，让数据可以完整无损的传输到目的端。

(2) 提供作业全链路的流量、数据量运行时监控
DataX 3.0 运行过程中可以将作业本身状态、数据流量、数据速度、执行进度等信息进行全面的展示，让用户可以实时了解作业状态。并可在作业执行过程中智能判断源端和目的端的速度对比情况，给予用户更多性能排查信息。

(3) 提供脏数据探测
在大量数据的传输过程中，必定会由于各种原因导致很多数据传输报错(比如类型转换错误)，这种数据 DataX 认为就是脏数据。DataX 目前可以实现脏数据精确过滤、识别、采集、展示，为用户提供多种的脏数据处理模式，让用户准确把控数据质量大关！

### 5.2 丰富的数据转换功能

DataX 作为一个服务于大数据的 ETL 工具，除了提供数据快照搬迁功能之外，还提供了丰富数据转换的功能，让数据在传输过程中可以轻松完成数据脱敏，补全，过滤等数据转换功能，另外还提供了自动 groovy 函数，让用户自定义转换函数。详情请看 DataX3 的 transformer 详细介绍。

### 5.3 精准的速度控制

还在为同步过程对在线存储压力影响而担心吗？新版本 DataX 3.0 提供了包括通道(并发)、记录流、字节流三种流控模式，可以随意控制你的作业速度，让你的作业在库可以承受的范围内达到最佳的同步速度。

### 5.4 强劲的同步性能

DataX3.0 每一种读插件都有一种或多种切分策略，都能将作业合理切分成多个 Task 并行执行，单机多线程执行模型可以让 DataX 速度随并发成线性增长。在源端和目的端性能都足够的情况下，单个作业一定可以打满网卡。另外，DataX 团队对所有的已经接入的插件都做了极致的性能优化，并且做了完整的性能测试。

### 5.5 健壮的容错机制

DataX 作业是极易受外部因素的干扰，网络闪断、数据源不稳定等因素很容易让同步到一半的作业报错停止。因此稳定性是DataX的基本要求，在DataX 3.0的设计中，重点完善了框架和插件的稳定性。目前DataX3.0可以做到线程级别、进程级别(暂时未开放)、作业级别多层次局部/全局的重试，保证用户的作业稳定运行。
