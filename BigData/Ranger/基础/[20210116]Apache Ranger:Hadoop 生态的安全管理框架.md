---
layout: post
author: smartsi
title: Apache Ranger : Apache Hadoop 生态的安全管理员
date: 2021-01-16 16:29:01
tags:
  - Ranger

categories: Ranger
permalink: introducing-ranger
---

我们都知道 HDFS、Hive 和 HBase 等系统都有各自的权限管理功能，但它们太过分散且配置方式原始，不利于管理。所以我们需要引入一个授权系统，它需要集成所有子系统的权限管理功能并提供一个统一的授权界面。这就是我们要介绍的一个新的组件：Apache Ranger。

## 1. 概述

Apache Ranger 提供了集中式的权限管理框架，可以对 Hadoop 生态中的 HDFS、Hive、YARN、Kafka、Storm 和 Solr 等组件进行细粒度的权限访问控制，并且提供了 Web UI 方便管理员操作。使得系统管理员只需面对 Apache Ranger 一个系统，就能对 Hadoop 整个生态体系进行数据授权、数据管理与审计。

对于支持的 Hadoop 组件，Apache Ranger 通过访问控制策略提供了一种标准的授权方法。作为标准，Apache Ranger 提供了一种集中式的组件，用于审计用户的访问行为和管理组件间的安全交互行为。

Apache Ranger 使用了一种基于属性的方法定义和强制实施安全策略。当与 Apache Hadoop 的数据治理解决方案和元数据仓储组件 Apache Atlas 一起使用时，它可以定义一种基于标签的安全服务，通过使用标签对文件和数据资产进行分类，并控制用户和用户组对一系列标签的访问。

## 2. 目标

Apache Ranger 具有如下目标：
- 集中式安全管理：可在 Web UI或使用 REST API 来管理所有与安全相关的任务，从而实现集中化的安全管理；
- 细粒度的授权：通过中心管理工具对 Hadoop 组件/工具的操作/行为进行细粒度级别的控制；
- 标准化授权：支持的所有 Hadoop 组件都有标准化授权方法。
- 增强了对不同授权方法的支持：基于角色的访问控制，基于属性的访问控制等。
- 集中审核：在Hadoop的所有组件中集中审核用户访问和管理操作（与安全性相关）。

## 3. 支持的组件及版本

Apache Ranger 可以支持的组件有 HDFS、HBase、Hive、YARM、Strom、Kafka、Knox、Solr等，但要注意各个组件的版本。目前 Apache Ranger 最新版本为 2.1.0，支持的组件版本对应如下：

| 组件 | 版本 |
| :------------- | :------------- |
| Hadoop | 3.1.1 |
| Hive | 3.1.2 |
| HBase | 2.0.2 |
| Presto | 333 |
| Storm | 1.2.0 |
| Ozone | 0.4.0-alpha |
| Kafka | 2.4.0 |
| KyLin | 2.6.4 |
| Solr | 7.7.1 |
| Sqoop | 1.99.7 |
| Zookeeper | 3.4.14 |
| Elasticsearch | 7.6.0 |
| Atlas | 2.1.0 |
| Knox | 1.2.0 |

另外，我们再说一下 1.2.0 版本，这是应用比较广泛的一个版本：

| 组件 | 版本 |
| :------------- | :------------- |
| Hadoop | 2.7.1 |
| Hive | 2.3.2 |
| HBase | 1.3.2 |
| Presto | 默认不提供 |
| Storm | 1.2.0 |
| Ozone | 默认不提供 |
| Kafka | 1.0.0 |
| KyLin | 2.3.0 |
| Solr | 5.5.4 |
| Sqoop | 1.99.7 |
| Zookeeper | 3.4.6 |
| Elasticsearch | 默认不提供 |
| Atlas | 1.1.0 |

## 4. 架构

Ranger主要由三个组件组成：

(1) Ranger Admin

Ranger Admin 是 Apache Ranger 的核心模块，它内置了一个 Web 管理页面，用户可以通过这个 Web 管理界面或者 REST 接口来创建和更新安全访问策略，这些策略被存储在数据库中。各个组件的 Plugin 定期对这些策略进行轮询。此外还包含一个审计系统，每个组件的插件会定期向审计系统发送收集到的操作日志。

(2) Ranger Plugins

Plugin 嵌入在各个集群组件的进程里，是一个轻量级的Java程序。例如，Ranger对Hive的组件，就被嵌入在Hiveserver2里。这些Plugin从Ranger Admin服务端拉取策略，并把它们存储在本地文件中。当接收到来自组件的用户请求时，对应组件的Plugin会拦截该请求，并根据安全策略对其进行评估。

(3) Ranger UserSync

Ranger 提供了一个用户同步工具。您可以从Unix或者LDAP中拉取用户和用户组的信息。这些用户和用户组的信息被存储在Ranger Admin的数据库中，可以在定义策略时使用。

Apache Ranger 的功能还包括动态策略（Dynamic Policies），当访问依赖于时间等动态因素时。它可以基于每天的不同时刻、IP 地址或是地理位置对访问资源进行限制。

Apache Ranger 架构在组成上还包括一个 Ranger 策略管理服务器（Policy Admin Server），该服务器将策略存储在关系数据库中（通常使用 MySQL ）。每个受支持的组件（例如 Hive、HDFS 等）通过运行 Ranger 插件对所有被访问的资源（例如文件、数据库、数据库表、数据列等）执行授权检查。授权通常基于已定义的策略，并从集中式管理服务器处获取，默认的轮询周期是 30 秒。插件在管理服务器宕机时仍然能够工作，不过根据最佳实践，最好把它们配置成高可用的。

Ranger 另一个对企业有用的特性是与外部系统集成做授权证。它支持的授权机制包括 LDAP /AD 和 Unix 系统认证。Ranger 可以将审计记录写入 Apache Solr 。























参考：
- [Apache Ranger 升级为顶级项目](https://www.infoq.cn/article/2017/03/apache-ranger-top-level-project)
- [](https://help.aliyun.com/document_detail/66410.html)
