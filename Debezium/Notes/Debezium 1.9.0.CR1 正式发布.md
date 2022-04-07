---
layout: post
author: wy
title: Debezium 1.9.0.CR1 正式发布
date: 2022-04-07 12:33:21
tags:
  - Debezium

categories: Debezium
permalink: debezium-1-9-cr1-released
---

我很高兴宣布 Debezium 1.9.0.CR1 正式发布！除了修复一系列 Bug 之外，这个版本还带来了期待已久的功能：对 Apache Cassandra 4 的支持！整体而言，在这个版本修复了 52 个问题。现在让我们仔细看看在 Cassandra 3 上的变化以及对 Cassandra 4 的支持。

## 1. Cassandra 3 重大变化

对于需要使用 Cassandra 3 的用户，Connector（孵化中）的 Maven 坐标在此版本中有一些变化，主要是 artifact 名称发生了变化：
```xml
<dependency>
  <groupId>io.debezium</groupId>
  <artifactId>debezium-connector-cassandra-3</artifactId>
  <version>1.9.0.CR1</version>
</dependency>
```
在这个版本还引入了另外一个面向用户的变更，即 Cassandra driver 的改变。连接配置不再直接在 Connector 属性文件中提供，而是使用一个单独的配置文件 application.conf 提供。你可以在[此处](https://docs.datastax.com/en/developer/java-driver/4.2/manual/core/configuration/reference/)找到有关 driver 配置的完整参考，下面是一个示例：
```
datastax-java-driver {
  basic {
    request.timeout = 20 seconds
    contact-points = [ "spark-master-1:9042" ]
    load-balancing-policy {
      local-datacenter = "dc1"
    }
  }
  advanced {
    auth-provider {
      class = PlainTextAuthProvider
      username = user
      password = pass
    }
    ssl-engine-factory {
     ...
    }
  }
}
```
为了能让 Debezium Connector 读取以及使用这个新的应用程序配置文件，必须在 Connector 属性文件中进行如下配置：
```
cassandra.driver.config.file=/path/to/application/configuration.conf
```

## 2. 对 Cassandra 4 的支持

对于新用户以及希望升级到 Cassandra 4 的用户，新 Connector artifact 的 Maven 坐标为：
```xml
<dependency>
  <groupId>io.debezium</groupId>
  <artifactId>debezium-connector-cassandra-4</artifactId>
  <version>1.9.0.CR1</version>
</dependency>
```
> 官方文档中有错误 debezium-connectr-cassandra-4

我们引入了一个新的 artifact 而不是让用户配置切换，因为这样可以允许两个代码库根据需要分开。可以根据需要改进 Cassandra 3 和 4 Connector，因为我们继续以 Java 11 作为基线来构建 Cassandra 4 Connector。

Debezium for Cassandra 4 Connector 基于 Apache Cassandra 4.0.2 构建。如果你打算升级到 Cassandra 4，那么从 Debezium 的角度来看，迁移相对来说是无缝对接的。升级 Cassandra 环境后，需要按照上述 Cassandra 3 重大变化部分中所讲的来调整 driver 配置，然后重新启动 connector.hanges 部分并启动 Connector。

## 3. 其他修复和变更

1.9.0.CR1 版本中的其他修复和优化包括：
- 针对 MySQL（[DBZ-4786](https://issues.redhat.com/browse/DBZ-4786)、[DBZ-4833](https://issues.redhat.com/browse/DBZ-4833)、[DBZ-4841](https://issues.redhat.com/browse/DBZ-4841)）和 Oracle（[DBZ-4810](https://issues.redhat.com/browse/DBZ-4810)、[DBZ-4851](https://issues.redhat.com/browse/DBZ-4851)）的各种 DDL 解析器的修复
- Oracle Connector 优雅地处理不支持的列类型（[DBZ-4852](https://issues.redhat.com/browse/DBZ-4852)、[DBZ-4853](https://issues.redhat.com/browse/DBZ-4853)、[DBZ-4880](https://issues.redhat.com/browse/DBZ-4880)）
- 优化 Oracle Connector 的补充日志检查（[DBZ-4842](https://issues.redhat.com/browse/DBZ-4842)、[DBZ-4869](https://issues.redhat.com/browse/DBZ-4869)）
- 各种 MySQL Connector 的优化（[DBZ-4758](https://issues.redhat.com/browse/DBZ-4758)、[DBZ-4787](https://issues.redhat.com/browse/DBZ-4787)）

原文: [Debezium 1.9.0.CR1 Released](https://debezium.io/blog/2022/03/25/debezium-1-9-cr1-released/)
