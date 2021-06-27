---
layout: post
author: smartsi
title: Java 实现 Kafka Consumer
date: 2020-10-11 11:32:01
tags:
  - Kafka

categories: Kafka
permalink: kafka-consumer-in-java
---

> kafka 版本：2.5.0

在本文章中，我们创建一个简单的 Java 生产者示例。我们会创建一个名为 my-topic Kafka 主题（Topic），然后创建一个使用该主题发送记录的 Kafka 生产者。Kafka 发送记录可以使用同步方式，也可以使用异步方式。

在创建 Kafka 生产者之前，我们必须安装 Kafka 以及启动集群。具体可以查阅博文：[Kafka 安装与启动](http://smartsi.club/kafka-setup-and-run.html)。

### 1. Maven依赖

要使用 Java 创建 Kafka 消费者，需要添加以下 Maven 依赖项：
```xml
<!-- https://mvnrepository.com/artifact/org.apache.kafka/kafka-clients -->
<dependency>
    <groupId>org.apache.kafka</groupId>
    <artifactId>kafka-clients</artifactId>
    <version>2.5.0</version>
</dependency>
```
> 具体版本需要根据安装的Kafka版本制定，在此我们使用 2.5.0 版本。

### 2. 创建Kafka消费者









...
