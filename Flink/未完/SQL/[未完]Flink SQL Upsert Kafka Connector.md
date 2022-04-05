---
layout: post
author: smartsi
title: Flink SQL Upsert Kafka Connector
date: 2021-08-15 15:47:21
tags:
  - Flink
  - Flink SQL

categories: Flink
permalink: flink-sql-upsert-kafka-connector
---

> Flink 版本：1.13

Upsert Kafka Connector 可以以 upsert 的方式从 Kafka Topic 读取数据或者将数据写入其中。

作为源，upsert-kafka 连接器产生一个变更日志流，其中每个数据记录代表一个更新或删除事件。更准确地说，数据记录中的值被解释为同一个键的最后一个值的更新，如果有的话（如果相应的键还不存在，更新将被视为插入）。使用表类比，更改日志流中的数据记录被解释为 UPSERT 又名 INSERT/UPDATE，因为任何具有相同键的现有行都将被覆盖。此外，空值以特殊方式解释：具有空值的记录表示“删除”。

作为接收器，upsert-kafka 连接器可以使用更改日志流。它将 INSERT/UPDATE_AFTER 数据写为普通的 Kafka 消息值，并将 DELETE 数据写为具有空值的 Kafka 消息（表示键的墓碑）。 Flink 会根据主键列的值对数据进行分区来保证主键上的消息排序，因此同一键上的更新/删除消息会落入同一个分区。











原文: [Upsert Kafka SQL Connector](https://ci.apache.org/projects/flink/flink-docs-release-1.13/docs/connectors/table/upsert-kafka/)
