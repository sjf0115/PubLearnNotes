---
layout: post
author: sjf0115
title: Kafka 监控工具之 Kafka Manager
date: 2019-09-06 21:00:01
tags:
  - Kafka

categories: Kafka
permalink: use-kafka-manager-to-manage-kafka
---

### 1. 安装Kafka

如果你还没有安装 Kafka 可以参考博文[Kafka 安装与启动](http://smartsi.club/kafka-setup-and-run.html)进行安装。

### 2. Kafka Manager简介

Kafka Manager 是一个用于管理 [Apache Kafka](http://kafka.apache.org/) 的工具。其提供了如下功能:
- 管理多个集群。
- 轻松检查群集状态（Topic，消费者，偏移量，Broker，副本分发，分区分发）。
- 运行首选副本选举。
- 使用选项生成分区分配以选择要使用的 Broker。
- 分区重新分配。
- 使用可选 Topic 配置创建主题（0.8.1.1版本与0.8.2+版本配置不同）。
- 删除主题（仅在 0.8.2+ 版本中支持并在 Broker 配​​置中设置 `delete.topic.enable=true`）。
- 主题列表现在指示标记为删除的主题（仅支持0.8.2+）。
- 批量生成多个主题的分区分配，并可选择要使用的代理。
- 批量运行重新分配多个主题的分区。
- 将分区添加到现有主题。
- 更新现有主题的配置。

### 3. 要求

- [Kafka 0.8.. 或者 0.9.. 或者 0.10.. 或者 0.11..](http://kafka.apache.org/downloads.html)
- Java 8+

### 4. 部署

由于 Kafka Manager 只提供了[源码](https://github.com/yahoo/kafka-manager)，并没有提供二进制包，因此我们需要对下载下来的源码进行构建，构建依赖工具 sbt。在 Mac 中，执行如下命令即可安装 sbt:
```
brew install sbt
```
下面的命令将创建一个zip文件，可用于部署应用程序:
```
./sbt clean dist
```
看到如下输出表示我们已经构建成功:
```
[info] Done packaging.
[success] All package validations passed
[info] Your package is ready in /Users/smartsi/software/kafka-manager/target/universal/kafka-manager-2.0.0.2.zip
[success] Total time: 434 s, completed 2019-9-7 16:13:06
```
构建成功后，在 `target/universal` 目录下找到 `kafka-manager-2.0.0.2.zip` 文件，这个就是构建好的 Kafka Manager。

解压 `kafka-manager-2.0.0.2.zip` 到我们的工作目录下，并创建一个软连接:
```
lrwxr-xr-x   1 smartsi  staff       22  9  7 18:16 kafka-manager@ -> kafka-manager-2.0.0.2/
drwxr-xr-x   7 smartsi  staff      224  9  7 18:16 kafka-manager-2.0.0.2/
```

### 5. 配置

在 `conf/application.conf` 中修改配置:
```
kafka-manager.zkhosts="127.0.0.1:2181"
```
你可以通过逗号分隔来指定多个 ZooKeeper 主机，如下所示：
```
kafka-manager.zkhosts="my.zookeeper.host.com:2181,other.zookeeper.host.com:2181"
```
或者，如果你不想在配置文件中硬编码，可以使用环境变量 `ZK_HOSTS`：
```
ZK_HOSTS="my.zookeeper.host.com:2181"
```
你可以通过修改 `application.features` 的默认列表值来启用/禁用以下功能：
```
application.features=["KMClusterManagerFeature","KMTopicManagerFeature","KMPreferredReplicaElectionFeature","KMReassignPartitionsFeature"]
```
- `KMClusterManagerFeature` - 允许从 Kafka 集群中添加、修改、删除集群。
- `KMTopicManagerFeature` - 允许从一个 Kafka 集群中添加、修改、删除 Topic。
- `KMPreferredReplicaElectionFeature` - 允许为Kafka集群运行首选副本选举。
- `KMReassignPartitionsFeature` - 允许生成分区分配和重新分配分区。

### 6. 启动服务

解压缩生成的 zip 文件，并将其移到工作目录后，可以运行如下命令启动服务：
```
bin/kafka-manager
```
默认情况下会选择 9000 端口。可以通过如下命令选择其他端口，配置文件也一样：
```
bin/kafka-manager -Dconfig.file=/path/to/application.conf -Dhttp.port=8080
```

参考:
- [使用Kafka Manager管理Kafka集群](http://www.itmuch.com/work/kafka-manager/)
- [yahoo/kafka-manager](https://github.com/yahoo/kafka-manager)
