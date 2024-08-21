---
layout: post
author: sjf0115
title: Kafka 常用命令行操作
date: 2018-10-23 10:57:01
tags:
  - Kafka

categories: Kafka
permalink: kafka-common-command-line-operations
---

这篇文章将给你介绍在Kafka集群上执行的最常见操作。这篇文章中介绍的所有工具都可以在Kafka发行版的`bin/`目录下找到。


## 1. Topic 管理

### 1.1 查询 Topic

查询所有 Topic 列表：
```
bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```
查询所有 Topic 列表（不包括内部 Topic）：
```
bin/kafka-topics.sh --bootstrap-server localhost:9092 --list --exclude-internal
```

查询匹配的 Topic 列表，如下查询 connect-mysql-catalog 开头的所有 Topic 列表：
```
bin/kafka-topics.sh --bootstrap-server localhost:9092 --list --topic "connect-mysql-catalog.*"
```

### 1.2 删除 Topic

删除指定 Topic：
```
bin/kafka-topics.sh -delete --bootstrap-server localhost:9092 --topic connect-mysql-schema-CDS
```
另外可以支持删除正则表达式匹配的 Topic，只需要将 Topic 用双引号包裹起来，例如，删除以 connect-mysql-schema 为开头的 opic
```
bin/kafka-topics.sh -delete --bootstrap-server localhost:9092 --topic "connect-mysql-schema.*"
```

## 2. Group 管理

### 2.1 查看 Group 列表

```
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
```

### 2.2 查看 Group 消费情况

```
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group end-to-end-exactly-once-group --describe
```

> CURRENT-OFFSET：当前消费偏移量
> LOG-END-OFFSET：末尾偏移量
> LAG：为未消费的记录，如果有很多，说明消费延迟很严重

### 2.3 删除 Group

```
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group test-group --delete
```

### 2.4 重置 offset



## 3. Consumer 管理

### 3.1 kafka-console-consumer

从头开始消费：
```
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic word-count-input --group test-group --from-beginning
```

## 4. Producer 管理

```
bin/kafka-console-producer.sh --broker-list localhost:9092 --topic word-count-input
```











> Kafka版本：1.0.x
