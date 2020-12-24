---
layout: post
author: sjf0115
title: Flink1.4 状态概述
date: 2018-01-16 19:30:17
tags:
  - Flink
  - Flink 容错

categories: Flink
permalink: flink-stream-state-overview
---

有状态的函数和算子在处理单个元素/事件时要存储数据，使得状态`state`成为任何精细操作的关键构件。

例如：
- 当应用程序搜索某些特定模式事件时，状态将存储目前为止遇到的事件序列。
- 当按每分钟/小时/天聚合事件时，状态保存待处理的聚合事件。
- 在数据流上训练机器学习模型时，状态保存模型参数的当前版本。
- 当需要管理历史数据时，状态允许访问过去发生的事件。

`Flink` 需要了解状态，以便使用检查点进行状态容错，并允许流应用程序使用保存点。

对状态进行了解有助于你对 `Flink` 应用程序进行扩展，这意味着 `Flink` 负责在并行实例之间进行重新分配状态。

`Flink` 的可查询状态`queryable state`功能允许你在 `Flink` 运行时在外部访问状态。

在使用状态时，阅读有关`Flink`的 `State Backends` 应该对你很有帮助。`Flink` 提供不同的 `State Backends`，并指定状态的存储方式和位置。状态可以位于`Java`的堆内或堆外。根据你的 `State Backends`，`Flink`也可以管理应用程序的状态，这意味着`Flink`进行内存管理(可能会溢写到磁盘，如果有必要)，以允许应用程序保持非常大的状态。`State Backends`可以在不更改应用程序逻辑的情况下进行配置。

### 下一步

- 使用状态：显示如何在`Flink`应用程序中使用状态，并解释不同类型的状态。
- 检查点：描述如何启用和配置容错检查点。
- 可查询状态：解释如何在`Flink`运行时从外部访问状态。
- 为`Managed State`自定义序列化：讨论为状态自定义序列化逻辑及其升级。

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/dev/stream/state/index.html
