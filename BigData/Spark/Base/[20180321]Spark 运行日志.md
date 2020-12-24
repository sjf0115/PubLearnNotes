在很多情况下，我们需要查看driver和executors在运行Spark应用程序时候产生的日志，这些日志对于我们调试和查找问题是很重要的。

Spark日志确切的存放路径和部署模式相关：
(1) 如果是Spark Standalone模式，我们可以直接在Master UI界面查看应用程序的日志，在默认情况下这些日志是存储在worker节点的work目录下，这个目录可以通过SPARK_WORKER_DIR参数进行配置。

(2) 如果是Mesos模式，我们同样可以通过Mesos的Master UI界面上看到相关应用程序的日志，这些日志是存储在Mesos slave的work目录下。

(3) 如果是YARN模式，最简单地收集日志的方式是使用YARN的日志收集工具（yarn logs -applicationId ），这个工具可以收集你应用程序相关的运行日志，但是这个工具是有限制的：应用程序必须运行完，因为YARN必须首先聚合这些日志；而且你必须开启日志聚合功能（yarn.log-aggregation-enable，在默认情况下，这个参数是false）。

如果你运行在YARN模式，你可以在ResourceManager节点的WEB UI页面选择相关的应用程序，在页面点击表格中Tracking UI列的ApplicationMaster，这时候你可以进入到Spark作业监控的WEB UI界面，这个页面就是你Spark应用程序的proxy界面，比如https://www.iteblog.com:9981/proxy/application_1430820074800_0322，当然你也可以通过访问Driver所在节点开启的4040端口，同样可以看到这个界面。

到这个界面之后，可以点击Executors菜单，这时候你可以进入到Spark程序的Executors界面，里面列出所有Executor信息，以表格的形式展示，在表格中有Logs这列，里面就是你Spark应用程序运行的日志。如果你在程序中使用了println(....)输出语句，这些信息会在stdout文件里面显示；其余的Spark运行日志会在stderr文件里面显示。

在默认情况下，Spark应用程序的日志级别是INFO的，我们可以自定义Spark应用程序的日志输出级别，可以到$SPARK_HOME/conf/log4j.properties文件里面进行修改，比如：
```
spark.root.logger=WARN,console

log4j.rootLogger=${spark.root.logger}

log4j.appender.console=org.apache.log4j.ConsoleAppender
log4j.appender.console.target=System.err
log4j.appender.console.layout=org.apache.log4j.PatternLayout
log4j.appender.console.layout.ConversionPattern=%d (%t) [%p - %l] %m%n
```
这样Spark应用程序在运行的时候会打出WARN级别的日志，然后在提交Spark应用程序的时候使用--files参数指定上面的log4j.properties文件路径即可使用这个配置打印应用程序的日志。



原文：https://www.iteblog.com/archives/1353.html
