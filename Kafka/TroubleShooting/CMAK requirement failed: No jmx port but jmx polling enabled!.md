---
layout: post
author: sjf0115
title: CMAK requirement failed: No jmx port but jmx polling enabled!
date: 2022-05-10 21:00:01
tags:
  - Kafka

categories: Kafka
permalink: cmak-no-jmx-port-but-jmx-polling-enabled
---

## 1. 现象

我们在启动 CMAK 时，抛出如下异常：
```java
2022-05-09 23:36:45,478 - [ERROR] - from kafka.manager.jmx.KafkaJMX$ in pool-13-thread-2
Failed to connect to service:jmx:rmi:///jndi/rmi://127.0.0.1:-1/jmxrmi
java.lang.IllegalArgumentException: requirement failed: No jmx port but jmx polling enabled!
        at scala.Predef$.require(Predef.scala:281)
        at kafka.manager.jmx.KafkaJMX$.doWithConnection(KafkaJMX.scala:39)
        at kafka.manager.actor.cluster.BrokerViewCacheActor.$anonfun$updateTopicMetrics$5(BrokerViewCacheActor.scala:327)
        at scala.runtime.java8.JFunction0$mcV$sp.apply(JFunction0$mcV$sp.java:23)
        at scala.concurrent.Future$.$anonfun$apply$1(Future.scala:659)
        at scala.util.Success.$anonfun$map$1(Try.scala:255)
        at scala.util.Success.map(Try.scala:213)
        at scala.concurrent.Future.$anonfun$map$1(Future.scala:292)
        at scala.concurrent.impl.Promise.liftedTree1$1(Promise.scala:33)
        at scala.concurrent.impl.Promise.$anonfun$transform$1(Promise.scala:33)
        at scala.concurrent.impl.CallbackRunnable.run(Promise.scala:64)
        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1128)
        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:628)
        at java.base/java.lang.Thread.run(Thread.java:834)
```

## 2. 解决方案

我们在 CMAK(Kafka Manager)开启了 Enable JMX Polling 设置：

![](https://github.com/sjf0115/ImageBucket/blob/main/Kafka/cmak-no-jmx-port-but-jmx-polling-enabled-1.png?raw=true)

但是我们没有为 Kafka 开启 JMX。所以我们在启动 kafka 时增加 JMX_PORT=9999 开启 JMX：
```
JMX_PORT=9999 bin/kafka-server-start.sh -daemon config/server.properties
```
