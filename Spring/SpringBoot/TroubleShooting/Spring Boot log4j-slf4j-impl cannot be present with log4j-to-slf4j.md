## 1. 问题

启动 Spring Boot 应用程序时，报如下错误：
```java
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/Users/wy/.m2/repository/org/apache/logging/log4j/log4j-slf4j-impl/2.17.2/log4j-slf4j-impl-2.17.2.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/Users/wy/.m2/repository/ch/qos/logback/logback-classic/1.2.11/logback-classic-1.2.11.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Exception in thread "main" java.lang.ExceptionInInitializerError
	at com.data.profile.web.ProfileWebApplication.main(ProfileWebApplication.java:18)
Caused by: org.apache.logging.log4j.LoggingException: log4j-slf4j-impl cannot be present with log4j-to-slf4j
	at org.apache.logging.slf4j.Log4jLoggerFactory.validateContext(Log4jLoggerFactory.java:60)
	at org.apache.logging.slf4j.Log4jLoggerFactory.newLogger(Log4jLoggerFactory.java:44)
	at org.apache.logging.slf4j.Log4jLoggerFactory.newLogger(Log4jLoggerFactory.java:33)
	at org.apache.logging.log4j.spi.AbstractLoggerAdapter.getLogger(AbstractLoggerAdapter.java:53)
	at org.apache.logging.slf4j.Log4jLoggerFactory.getLogger(Log4jLoggerFactory.java:33)
	at org.slf4j.LoggerFactory.getLogger(LoggerFactory.java:363)
	at org.apache.commons.logging.impl.SLF4JLogFactory.getInstance(SLF4JLogFactory.java:155)
	at org.apache.commons.logging.impl.SLF4JLogFactory.getInstance(SLF4JLogFactory.java:132)
	at org.apache.commons.logging.LogFactory.getLog(LogFactory.java:273)
	at org.springframework.boot.SpringApplication.<clinit>(SpringApplication.java:179)
	... 1 more
```

## 2. 问题分析

### 2.1 SLF4J 的绑定机制
SLF4J 是一个日志门面框架，本身不实现日志功能，而是通过绑定（Binding）到具体的日志实现（如 Logback、Log4j2 等）。SLF4J 要求项目中有且仅有一个绑定。如果存在多个绑定，会触发 `multiple SLF4J bindings` 警告，最终可能导致应用程序崩溃。

### 2.2 错误日志解读

从错误日志中可以看到两个冲突的绑定：
```
log4j-slf4j-impl-2.17.2.jar (Log4j2 的 SLF4J 绑定)
logback-classic-1.2.11.jar (Logback 的 SLF4J 绑定)
```
这两个库分别是：
- Log4j2 的 SLF4J 绑定：log4j-slf4j-impl
- Logback 的默认实现：logback-classic

它们的共存导致 SLF4J 无法选择唯一的日志实现，最终抛出 `log4j-slf4j-impl cannot be present with log4j-to-slf4j` 异常。

### 2.3 Spring Boot 的默认日志框架

Spring Boot 默认使用 Logback 作为日志实现。如果项目中引入了其他日志框架（如 Log4j2）就会引发冲突。

## 3. 解决方案

如果不需要 Log4j2，直接使用 Spring Boot 默认的 Logback 来解决上述问题：


。。。
