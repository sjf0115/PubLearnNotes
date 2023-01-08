## 1. 问题

在本地 Idea 调试代码的时候抛出了如下一个异常：
```java
ERROR StatusLogger No log4j2 configuration file found. Using default configuration: logging only errors to the console.
```

## 2. 解决方案

从上面异常提供的信息看到没有找到 log4j2 配置文件，将使用默认配置：只将错误记录到控制台。很容易的看出我们在代码中使用到了 log4j，但是没有发现相应的配置文件。解决方案就是在 resouces 资源目录下提供配置文件，在这我们提供了一个名为 `log4j2.properties` 的配置文件：
```
rootLogger.level = INFO
rootLogger.appenderRef.console.ref = ConsoleAppender

appender.console.name = ConsoleAppender
appender.console.type = CONSOLE
appender.console.layout.type = PatternLayout
appender.console.layout.pattern = %d{HH:mm:ss,SSS} %-5p %-60c %x - %m%n
```
