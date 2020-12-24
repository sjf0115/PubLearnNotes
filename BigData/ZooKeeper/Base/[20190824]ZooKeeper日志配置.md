---
layout: post
author: sjf0115
title: ZooKeeper日志配置
date: 2019-08-25 12:14:45
tags:
  - ZooKeeper

categories: ZooKeeper
permalink: how-to-config-log-in-zookeeper
---

### 1. 简介

`ZooKeeper` 使用 `SLF4J` 作为日志的抽象层，默认使用 `Log4J` 来做实际的日志工作。使用两层日志抽象看起来似乎是多余的。这里简要的说明如何来配置 `Log4J`，虽然 `Log4J` 非常灵活且功能强大，但是也有一些复杂，这里只是简要的介绍一下基本的用法。

`Log4J` 的配置文件为 `log4j.properties`，系统会从 classpath 中加载这个文件。如果没有找到 `log4j.properties` 文件，会输出如下警告信息:
```
log4j:WARN No appenders could be found for logger (org.apache.zookeeper.ZooKeeper).
log4j:WARN Please initialize the log4j system properly.
log4j:WARN See http://logging.apache.org/log4j/1.2/faq.html#noconfig for more info.
```
如果看到上述日志，那么后续所有的日志消息会被丢弃。通常 `log4j.properties` 文件会保存在 `classpath` 中的 conf 目录下。

### 2. 配置文件

#### 2.1 组成部分

来看看 `ZooKeeper` 中 `log4j.properties` 的主要组成部分:
```
zookeeper.root.logger=INFO, CONSOLE
zookeeper.console.threshold=INFO  
zookeeper.log.dir=.  
zookeeper.log.file=zookeeper.log  
zookeeper.log.threshold=DEBUG  
zookeeper.tracelog.dir=.  
zookeeper.tracelog.file=zookeeper_trace.log

log4j.rootLogger=${zookeeper.root.logger}

log4j.appender.CONSOLE=org.apache.log4j.ConsoleAppender
log4j.appender.CONSOLE.Threshold=${zookeeper.console.threshold}
log4j.appender.CONSOLE.layout=org.apache.log4j.PatternLayout  
log4j.appender.CONSOLE.layout.ConversionPattern=%d{ISO8601} [myid:%X{myid}] -

...

log4j.appender.ROLLINGFILE=org.apache.log4j.RollingFileAppender
log4j.appender.ROLLINGFILE.Threshold=${zookeeper.log.threshold}
log4j.appender.ROLLINGFILE.File=${zookeeper.log.dir}/${zookeeper.log.file}  
log4j.appender.ROLLINGFILE.MaxFileSize=10MB  
log4j.appender.ROLLINGFILE.MaxBackupIndex=10  
log4j.appender.ROLLINGFILE.layout=org.apache.log4j.PatternLayout
log4j.appender.ROLLINGFILE.layout.ConversionPattern=%d{ISO8601} [myid:%X{myid}] -  
...
```

#### 2.2 详解

```
zookeeper.root.logger=INFO, CONSOLE
zookeeper.console.threshold=INFO  
zookeeper.log.dir=.  
zookeeper.log.file=zookeeper.log  
zookeeper.log.threshold=DEBUG  
zookeeper.tracelog.dir=.  
zookeeper.tracelog.file=zookeeper_trace.log
```
上面配置中，所有配置项均以 `zookeeper.` 开头，配置了该文件的默认值，这些配置项实际是系统属性配置，可以通过 java 命令行指定 `-D` 参数来覆盖 JVM 的配置。第一行的日志配置中，默认配置了日志消息的级别为 `INFO`，即所有低于 `INFO` 级别的日志消息都会被丢弃，使用的 appender 为 `CONSOLE`。你可以指定多个 appender，例如，如果你想将日志信息同时输出到 `CONSOLE` 和 `ROLLINGFILE` 时，那么可以配置 `zookeeper.root.logger` 为 `INFO, CONSOLE, ROLLINGFILE`。

```
log4j.rootLogger=${zookeeper.root.logger}
```
rootLogger 指定了处理所有日志消息的级别 `INFO` 以及日志处理器 `CONSOLE`。

```
log4j.appender.CONSOLE=org.apache.log4j.ConsoleAppender
```
该行配置 `CONSOLE` appender 实现类 `ConsoleAppender`。

```
log4j.appender.CONSOLE.Threshold=${zookeeper.console.threshold}
```
在 appender 的定义中也可以过滤日志消息。该行配置了这个 appender 会忽略所有低于 `INFO` 级别的消息，因为 `zookeeper.root.logger` 中定义了全局阈值为 `INFO`。

```
log4j.appender.CONSOLE.layout=org.apache.log4j.PatternLayout
log4j.appender.CONSOLE.layout.ConversionPattern=%d{ISO8601} [myid:%X{myid}] -
```
appender 使用的布局类在输出前对输出日志进行格式化操作。我们通过布局模式定义了输出日志消息外还定义了输出日志的级别、日期、线程信息和调用位置等信息。

```
log4j.appender.ROLLINGFILE=org.apache.log4j.RollingFileAppender
```
`RollingFileAppender` 实现了滚动日志文件的输出，而不是不断的输出到一个单独的文件或者控制台。除非 `ROLLINGFILE` 被 `rootLogger` 引用，否则该 appender 会被忽略。

```
log4j.appender.ROLLINGFILE.Threshold=${zookeeper.log.threshold}
```
定义 `ROLLINGFILE` 的输出级别为 `DEBUG`，因为 rootLogger 过滤了所有低于 `INFO` 级别的日志，所以，你如果想看 `DEBUG` 消息，就必须将 `zookeeper.root.logger` 从 `INFO` 改成 `DEBUG`。

```
log4j.appender.ROLLINGFILE.File=${zookeeper.log.dir}/${zookeeper.log.file}
log4j.appender.ROLLINGFILE.MaxFileSize=10MB  
log4j.appender.ROLLINGFILE.MaxBackupIndex=10  
log4j.appender.ROLLINGFILE.layout=org.apache.log4j.PatternLayout
log4j.appender.ROLLINGFILE.layout.ConversionPattern=%d{ISO8601} [myid:%X{myid}] -
...   
```
上面配置设置了滚动输出日志路径以及文件最大大小。此外还使用布局类在日志输出前进行格式化操作。我们通过布局模式定义了输出日志消息外还定义了输出日志的级别、日期、线程信息和调用位置等信息。

日志记录功能会影响到进程的性能，尤其是在开启 `DEBUG` 级别时。同时 `DEBUG` 日志会提供大量有价值的信息，可以帮助我们诊断问题。

### 3. 修改日志输出路径

当执行 `zkServer.sh` 时，会在执行命令的文件夹下会产生 `zookeeper.out` 日志文件来记录 `ZooKeeper` 的运行日志。这种方式会让日志文件不便于查找，对输出路径和大小不能进行控制，所以需要修改日志输出方式。

#### 3.1 修改zkEnv.sh

修改 `$ZOOKEEPER_HOME/bin` 目录下的 `zkEnv.sh` 文件，`ZOO_LOG_DIR` 指定日志输出的目录，`ZOO_LOG4J_PROP`，指定日志输出级别 `INFO,ROLLINGFILE`:
```shell
# 以下是原配置
if [ "x${ZOO_LOG_DIR}" = "x" ]
then
    ZOO_LOG_DIR="."
fi

if [ "x${ZOO_LOG4J_PROP}" = "x" ]
then
    ZOO_LOG4J_PROP="INFO,CONSOLE"
fi

# 以下是修改后配置
if [ "x${ZOO_LOG_DIR}" = "x" ]
then
    ZOO_LOG_DIR="/Users/smartsi/opt/zookeeper/logs"
fi

if [ "x${ZOO_LOG4J_PROP}" = "x" ]
then
    ZOO_LOG4J_PROP="INFO,ROLLINGFILE"
fi
```
> `ZOO_LOG_DIR="${ZOOKEEPER_HOME}/logs"`，日志会输出都 `/Users/xxx/opt/zookeeper/bin/~/opt/zookeeper/logs` 目录下。需要设置为 `/Users/smartsi/opt/zookeeper/logs` 目录，才会正确输出到 `/Users/xxx/opt/zookeeper/logs` 目录下。

#### 3.2 修改log4j.properties

修改 `$ZOOKEEPER_HOME/conf/log4j.properties` 文件 `zookeeper.root.logger` 的值与前一个文件的 `ZOO_LOG4J_PROP` 保持一致，在这日志配置是以日志大小进行滚动:
```xml
# 以下是原配置
zookeeper.root.logger=INFO, CONSOLE
log4j.appender.ROLLINGFILE=org.apache.log4j.RollingFileAppender

# 以下是修改后配置
zookeeper.root.logger=INFO, ROLLINGFILE
log4j.appender.ROLLINGFILE=org.apache.log4j.RollingFileAppender
```

上述两个文件修改后，重新启动服务，`ZooKeeper` 会将日志文件保存到 `${ZOOKEEPER_HOME}/logs` 目录下，文件名为 `log4j.properties` 文件中配置的 `zookeeper.log`。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

来源: <ZooKeeper分布式过程协同技术详解>
