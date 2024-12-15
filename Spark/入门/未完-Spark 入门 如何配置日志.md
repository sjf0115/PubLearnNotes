
在运行程序时看到如下输出：
```
Using Spark's default log4j profile: org/apache/spark/log4j-defaults.propert
```
上述提示表示 Spark 告诉我们它正在使用默认的 log4j 配置文件。Log4j 是 Apache 的一个开源日志框架，Spark 使用它来记录运行时的日志信息。

如果你想自定义你的日志配置，你可以在 Spark 应用的 classpath下 提供一个名为 `log4j.properties` 的文件，里面包含你的日志配置。例如，你可以在你的 Spark 应用的资源文件中添加一个 `log4j.properties` 文件，并设置日志级别为DEBUG：
```xml
log4j.rootCategory=DEBUG, console
log4j.appender.console=org.apache.log4j.ConsoleAppender
log4j.appender.console.target=System.err
log4j.appender.console.layout=org.apache.log4j.PatternLayout
log4j.appender.console.layout.ConversionPattern=%d{yy/MM/dd HH:mm:ss} %p %c{1}: %m%n

# Set everything to be logged to the console
log4j.rootLogger=DEBUG, console
log4j.logger.org.apache.spark.sql=DEBUG
```
