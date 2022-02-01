
Flink中的日志记录是使用slf4j日志接口实现的。作为底层日志框架，我们使用log4j。同时还提供了logback配置文件，并可以将它们传递给JVM作为配置文件。愿意使用logback代替log4j的用户排除log4j即可(或者从lib文件夹中删除它)。

### 1. 配置Log4j

Log4j是使用配置文件进行控制的。在Flink中，这个文件通常叫做`log4j.properties`。我们使用`-Dlog4j.configuration =`参数将文件的文件名和位置传递给JVM。

Flink内置下列默认配置文件：

配置文件|说明
---|---
log4j-cli.properties|在Flink命令行客户端中使用(例如 flink run)(not code executed on the cluster)
log4j-yarn-session.properties|在启动YARN会话(yarn-session.sh)时在Flink命令行客户端中使用
log4j.properties|JobManager/Taskmanager日志(独立和YARN模式)


### 2. 配置Logback

对于用户和开发者来说，选择日志框架是非常重要的。日志框架的配置完全由配置文件完成。通过设置环境属性`-Dlogback.configurationFile = <file>`或将`logback.xml`放入类路径来指定配置文件。如果Flink是在IDE之外启动的，并且提供了启动脚本，那么conf目录需要包含一个logback.xml文件可以被修改和使用。 提供的logback.xml具有以下形式：

```
<configuration>
    <appender name="file" class="ch.qos.logback.core.FileAppender">
        <file>${log.file}</file>
        <append>false</append>
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{60} %X{sourceThread} - %msg%n</pattern>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="file"/>
    </root>
</configuration>

```

为了控制`org.apache.flink.runtime.jobgraph.JobGraph`的日志记录级别，必须将以下行添加到配置文件中:
```
<logger name="org.apache.flink.runtime.jobgraph.JobGraph" level="DEBUG"/>
```
有关配置logback的更多信息，请参阅[LOGback手册](https://logback.qos.ch/manual/configuration.html)。

### 3. 最佳实践

使用slf4j，通过调用如下代码创建Logger：
```java
import org.slf4j.LoggerFactory
import org.slf4j.Logger

Logger LOG = LoggerFactory.getLogger(Foobar.class)
```

为了最大化利用slf4j，建议使用它的占位符机制。使用占位符可以避免不必要的字符串构造，以防记录级别设置得太高不会记录消息的情况。占位符的语法如下：
```java
LOG.info("This message contains {} placeholders. {}", 2, "Yippie");
```
占位符还可以与需要记录的异常一起使用:
```java
catch(Exception exception){
	LOG.error("An {} occurred.", "error", exception);
}
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.3/monitoring/logging.html
