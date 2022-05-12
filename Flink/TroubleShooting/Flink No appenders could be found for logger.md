---
layout: post
author: sjf0115
title: Flink No appenders could be found for logger
date: 2022-05-12 22:34:01
tags:
  - Flink

categories: Flink
permalink: flink-no-appenders-could-be-found-for-logger
---

## 1. 现象

在本地 idea 上运行 Flink 程序时，提示如下告警，同时也不会输出日志：
```
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/Users/wy/.m2/repository/org/slf4j/slf4j-log4j12/1.7.10/slf4j-log4j12-1.7.10.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/Users/wy/.m2/repository/org/apache/logging/log4j/log4j-slf4j-impl/2.17.1/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.slf4j.impl.Log4jLoggerFactory]
log4j:WARN No appenders could be found for logger (com.flink.example.table.function.windows.GroupWindowSQLExample).
log4j:WARN Please initialize the log4j system properly.
log4j:WARN See http://logging.apache.org/log4j/1.2/faq.html#noconfig for more info.
```

## 2. 解决方案

如报警提示，slf4j 发现了两个桥接器：
- slf4j-log4j12：`Found binding in [jar:file:/Users/wy/.m2/repository/org/slf4j/slf4j-log4j12/1.7.10/slf4j-log4j12-1.7.10.jar!/org/slf4j/impl/StaticLoggerBinder.class]`
- log4j-slf4j-impl：`Found binding in [jar:file:/Users/wy/.m2/repository/org/apache/logging/log4j/log4j-slf4j-impl/2.17.1/log4j-slf4j-impl-2.17.1.jar!/org/slf4j/impl/StaticLoggerBinder.class]`

我们在配置中只引入了 log4j2 的依赖，并没有显示引入 log4j1 的依赖：
```xml
<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-slf4j-impl</artifactId>
    <version>2.17.1</version>
    <scope>runtime</scope>
</dependency>

<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-api</artifactId>
    <version>2.17.1</version>
    <scope>runtime</scope>
</dependency>

<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-core</artifactId>
    <version>2.17.1</version>
    <scope>runtime</scope>
</dependency>
```

很明显，有某个依赖间接依赖了 log4j1 的桥接器 slf4j-log4j12，使得同时存在了 slf4j-log4j12 和 log4j-slf4j-impl 这两个桥接器，我们使用 mvn help 插件分析：

![](https://github.com/sjf0115/ImageBucket/blob/main/Flink/flink-no-appenders-could-be-found-for-logger-1.png?raw=true)

我们可以看到 hadoop-client 传递依赖了 slf4j-log4j12，我们需要手动将其排除：
```xml
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-client</artifactId>
    <version>${hadoop.version}</version>
    <exclusions>
        <exclusion>
            <groupId>log4j</groupId>
            <artifactId>log4j</artifactId>
        </exclusion>
        <exclusion>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-log4j12</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```
