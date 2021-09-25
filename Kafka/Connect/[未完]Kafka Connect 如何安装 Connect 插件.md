---
layout: post
author: smartsi
title: Kafka Connect 如何安装 Connect 插件
date: 2021-09-22 20:15:00
tags:
  - Kafka

categories: Kafka
permalink: how-to-install-connector-plugins-in-kafka-connect
---

### 1. 简介

Kafka Connect 设计为可扩展的，因此开发人员可以创建自定义 Connector、Transform 或者 Converter。Kafka Connect Plugin 是一组 Jar 文件，其中包含一个或多个 Connector、Transform 或者 Converter 的实现。Connect 将每个 Plugin 相互隔离，以便一个 Plugin 中的库不受任何其他 Plugin 中的库的影响。这在使用来自多个提供商的 Connector 时非常重要。

> 在 Connect 部署中安装许多 Plugin 很常见，但确保每个 Plugin 只安装一个版本。

Kafka Connect Plugin 可以是：
- 文件系统上的一个目录，其中包含 Plugin 所需的所有 JAR 以及第三方依赖。这是最常见的，也是我们首选的。
- 一个包含 Plugin 及其第三方依赖所有类文件的 uber JAR。

> Plugin 不应包含 Kafka Connect 运行时提供的任何库。

Kafka Connect 根据 Plugin 路径（worker 配置文件 plugin.path 属性中以逗号分隔的目录路径）来寻找 Plugin。下面显示了一个 worker 配置文件 plugin.path 属性：
```
plugin.path=/opt/share/kafka/plugins
```
要安装 Plugin，首先要将 plugin 所在目录或 uber JAR 放在 plugin.path 属性的目录列表中。当我们启动 Connect worker 时，每个 worker 都会在 plugin.path 对应目录中找到的所有 Connector、Transform 或者 Converter。当我们使用 Connector、Transform 或者 Converter 时，Connect worker 首先会从对应的 Plugin 加载类，然后是 Kafka Connect 运行时和 Java 库。

### 2. 下载

[Confluent Hub](https://www.confluent.io/hub/) 打造了一个由 Connector、Transform 以及 Converter 组成的大型生态系统，我们可以从中找到适合我们需求的组件。

我们将以 [Kafka Connect JDBC](https://www.confluent.fr/hub/confluentinc/kafka-connect-jdbc) 插件为例，从 Confluent hub 下载会得到 confluentinc-kafka-connect-jdbc-xxx.zip 文件。

### 3. 安装

将 zip 文件解压到 Kafka Connect 指定的文件夹下（plugin.path 设定的目录）。在这我们将把它放在 /opt/share/kafka/plugins 目录下。文件夹树看起来像这样：
```
/opt/share/kafka/plugins
└── confluentinc-kafka-connect-jdbc-10.2.2
    ├── doc
    │   ├── LICENSE
    │   └── README.md
    ├── etc
        …
    ├── lib
        …
    │   ├── kafka-connect-jdbc-10.2.2.jar
    │   ├── sqlite-jdbc-3.25.2.jar
    │   ├── postgresql-42.2.19.jar
    │   ├── xmlparserv2-19.7.0.0.jar
        …
    └── manifest.json
```

### 4. 配置

在 Kafka Connect 配置文件 connect-standalone.properties（或 connect-distributed.properties）中，搜索 plugin.path 配置，并修改或创建它以包含 Connector 所在的文件夹：
```
plugin.path=/opt/share/kafka/plugins
```

参考：
- [installing-kconnect-plugins](https://docs.confluent.io/home/connect/userguide.html#installing-kconnect-plugins)
- [How to install connector plugins in Kafka Connect](https://rmoff.net/2020/06/19/how-to-install-connector-plugins-in-kafka-connect/)
