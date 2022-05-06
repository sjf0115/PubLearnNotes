---
layout: post
author: sjf0115
title: Grafana 系列之基本概念
date: 2019-08-17 13:48:34
tags:
  - Grafana

categories: Grafana
permalink: basic-concepts-of-grafana
---

### 1. 数据源

`Grafana` 为你的时间序列数据支持许多不同的存储后端（数据源），每个数据源都有一个特定的查询编辑器（Query Editor），针对不同的数据源的特性和功能自定义查询编辑器。

官方支持以下数据：
- [Graphite](https://grafana.com/docs/features/datasources/graphite/)
- [InfluxDB](https://grafana.com/docs/features/datasources/influxdb/)
- [OpenTSDB](https://grafana.com/docs/features/datasources/opentsdb/)
- [Prometheus](https://grafana.com/docs/features/datasources/prometheus/)
- [Elasticsearch](https://grafana.com/docs/features/datasources/elasticsearch/)
- [CloudWatch](https://grafana.com/docs/features/datasources/cloudwatch/)。

每个数据源的查询语法和功能显然非常不同，你可以将来自多个数据源的数据组合到一个仪表盘中，但是每个面板要绑定到属于一个特定组织的一个数据源。

### 2. 组织

`Grafana` 可以支持多个组织，以支持不同的部署模型。在许多情况下，`Grafana` 部署在一个组织中。每个组织可以拥有一个或多个数据源。仪表盘都要归属到特定组织下。

> 大多数指标数据库不提供任何类型的用户粒度的身份验证，因此，在 `Grafana` 中，所有用户都有权访问所在组织下的全部数据源和仪表盘。

有关 `Grafana` 用户模型的更多详细信息，请参阅[管理员](https://grafana.com/docs/reference/admin/)。

### 3. 用户

用户是 `Grafana` 中的指定帐户，用户可以属于一个或多个组织，并可以通过角色分配不同级别的权限。

`Grafana` 支持各种内部和外部方式供用户进行身份验证。这些包括来自其自己的集成数据库，来自外部 SQL 服务器或来自外部 LDAP 服务器。

有关更多详细信息，请参阅用[户身份验证](https://grafana.com/docs/reference/http_api/#users)。

### 4. 行

行是仪表盘中的逻辑划分，用于将面板组合在一起。行总是 12 '单元'宽，这些单元会根据浏览器的水平分辨率自动缩放，你可以通过设置它们的宽度来控制行内面板的相对宽度。

我们可以利用抽象单元，以便 `Grafana` 在所有小屏幕和大屏幕上看起来都很好。

>
借助 MaxDataPoints 功能，无论你的分辨率或时间范围如何，`Grafana` 都可以向你显示完美的数据点数量。

根据所选的模板变量，利用[Repeating Rows functionality](https://grafana.com/docs/reference/templating/#repeating-rows)功能可以动态创建或删除整个行（可以使用面板填充）。

单击行标题可以折叠行，如果在行折叠的情况下保存仪表板，它将保存该状态，并且在该行展开之前不会预加载这些图表。

### 4. 面板

面板是 `Grafana` 的基本可视化构建块，每个面板都会提供一个查询编辑器（取决于面板中选择的数据源）让你在面板上展现漂亮的可视化。

每个面板都有各种各样的样式和格式选项，可以让你创建完美的图片。可以在仪表盘上拖拽面板并重新排列，也可以调整大小。目前有五种面板类型：`Graph`，`Singlestat`，`Dashlist`，`Table` 和 `Text`。

像 `Graph` 这样的面板允许你根据需要绘制尽可能多的指标和序列，其他面板像 `Singlestat` 这样的需要将单个查询减少为单个数字，`Dashlist` 和 `Text` 比较特殊，不需要连接任何数据源。

通过在面板配置中使用[仪表盘模板](https://grafana.com/docs/reference/templating/)变量字符串（包括通过查询编辑器查询配置的数据源），可以使面板更加动态。

利用[Repeating Panel](https://grafana.com/docs/reference/templating/#repeating-panels)功能，根据所选的模板变量动态创建或删除面板。

面板上的时间范围通常通过[仪表盘时间选择器](https://grafana.com/docs/reference/timerange/)中进行设置，但也可以通过使用[面板特定时间覆盖](https://grafana.com/docs/reference/timerange/#panel-time-overrides-timeshift)来覆盖此时间范围。

可以通过各种方式轻松分享面板（或整个仪表盘），你可以向登录 `Grafana` 的人发送链接，你可以使用快照功能将当前正在查看的所有数据编码为静态的可交互的 JSON 文档，它比通过电子邮件截图更好！

### 5. 查询编辑器

查询编辑器暴露数据源的功能，并允许你查询其包含的指标。使用查询编辑器在时间序列数据库中构建一个或多个查询（针对一个或多个序列）。面板会实时更新，从而允许你实时地查看你的数据。

你可以在查询编辑器中使用[模板变量](https://grafana.com/docs/reference/templating/)。根据仪表盘上选择的模板变量可以更好的动态查看数据。

`Grafana` 允许你引用查询，如果你想向 `Graph` 添加第二个查询，只需键入 `#A` 即可引用第一个查询，这为构建复合查询提供了一种方便的方法。

### 6. 仪表盘

仪表盘可以被认为是一个或多个有组织面板的集合，排列到一个或者多个行中。

仪表盘的时间段可以通过仪表盘右上角的[仪表盘时间选择器](https://grafana.com/docs/reference/timerange/)进行控制。

仪表盘可以利用[模板](https://grafana.com/docs/reference/templating/)使其更具动态和可交互。

仪表盘可以利用注解在不同面板中展现事件数据。这有助于将面板中的时间序列数据与其他事件相关联。

仪表盘可以被标记，并且仪表盘选择器提供对特定组织中所有仪表盘的快速，可搜索的查询。

英译对照:
- Data Source：数据源
- Query Editor：查询编辑器
- Dashboard：仪表盘
- Panel：面板
- Organization：组织
- Row：行
- Annotations：注解

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[Basic Concepts](https://grafana.com/docs/guides/basic_concepts/)
