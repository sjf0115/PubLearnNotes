---
layout: post
author: sjf0115
title: Kafka 处理大消息
date: 2018-04-25 18:28:01
tags:
  - Kafka
  - Kafka 优化

categories: Kafka
permalink: kafka-handling-large-messages
---
### 1. 背景需求

今天在处理Spark实时系统时遇到如下问题：
```
kafka.common.MessageSizeTooLargeException: Found a message larger than the maximum fetch size of this consumer on topic XXX partition 4 at fetch offset 18397184. Increase the fetch size, or decrease the maximum message size the broker will allow.
```
从上面我们可以明显的看到在主题 XXX 分区4上有一条数据超出了消费者最大拉取大小。从上面提示中我们知道解决这个问题，可以通过增大消费者消费(fetch)消息的大小或者减小 broker 允许进入的消息的大小。可以通过如下几个参数来调节：
- `message.max.bytes`，broker 可以接收生产者消息的最大字节数。
- `replica.fetch.max.bytes`，broker 可以允许复制消息的最大字节数。
- `fetch.message.max.bytes`，消费者可以读取消息的最大字节数。
在我这解决上述问题，我们采取增大消费者消费消息的大小的解决方案，例如：
```
fetch.message.max.bytes=10485760
```
下面介绍一下kafka针对大数据处理的思考。

### 2. 如何处理大消息

#### 2.1 减小消息大小

在配置 Kafka 处理大消息之前，请首先考虑以下选项来减小消息大小：

(1) kafka 生产者可以压缩信息。例如，如果原始消息是基于文本的格式（如XML），则在大多数情况下，压缩消息可以变得足很小。

使用 `compression.codec` 和 `compressed.topics` 生产者配置参数启用压缩。可以支持 `Gzip` 和 `Snappy`。

(2) 如果共享存储系统（如NAS，HDFS或S3）可用，可以考虑将大文件放在共享存储系统上，使用Kafka通过发送文件位置来发送消息（不是发送文件内容本身，而是使用文件位置代替）。在很多情况下，这比使用 Kafka 发送大文件本身要快得多。

(3) 在生产者客户端将大消息拆分为大小为1KB的多个段，使用分区键确保所有段按照正确的顺序发送到相同的Kafka分区上。在消费者客户端可以重建原始的大消息。

#### 2.2 修改配置

如果你仍然需要使用 Kafka 发送大消息，请修改以下配置参数来符合你的要求：

##### 2.2.1 Broker配置

(1) `message.max.bytes`

broker 可以接收生产者消息的最大字节数。确保这个值必须小于消费者的 `fetch.message.max.bytes`，否则消费者不能消费该消息。默认值为 `1000000 (1 MB)`。

(2) `log.segment.bytes`

Kafka数据文件的大小。确保这个值必须大于任意单个消息。默认值为 `1073741824 (1 GiB)`。

(3) `replica.fetch.max.bytes`

broker 可以允许复制消息的最大字节数。确保这个值必须大于 `message.max.bytes`，否则 broker 可以接收它但无法复制它，可能会导致数据丢失。默认值为 `1048576 (1 MiB)`。

##### 2.2.2 Consumer配置

如果单个消息批次大于以下任何默认值，则消费者仍可以使用该批次，但该批次将单独发送，这可能会导致性能下降。

(1) `max.partition.fetch.bytes`

服务器将返回的每个分区的最大字节数。默认值为 `1048576 (10 MiB)`。

(2) `fetch.max.bytes`

服务器返回给拉取请求的最大字节数。默认值为 `52428800 (50 MiB)`。

(3) `fetch.message.max.bytes`

消费者可以读取消息的最大字节数。必须至少与 `message.max.bytes` 一样大。默认值为 `1048576 (1 MiB)`。


参考:https://www.cloudera.com/documentation/kafka/latest/topics/kafka_performance.html#concept_gqw_rcz_yq

https://www.mail-archive.com/users@kafka.apache.org/msg25471.html

https://www.mail-archive.com/users@kafka.apache.org/msg25477.html

http://blog.51cto.com/10120275/1844461

https://www.e-learn.cn/content/wangluowenzhang/60020
