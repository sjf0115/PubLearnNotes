### 1. 存储位置

Hive使用log4j进行日志记录。 默认情况下，CLI不会将日志输出到控制台上。 Hive 0.13.0 版本之前默认日志记录级别为WARN。 从Hive 0.13.0 开始，默认日志记录级别改为INFO。

默认情况下，日志存储在/tmp/<user.name>目录下。例如，当前用户为xiaosi：
```
/tmp/xiaosi/hive.log
```
注意：
```
Hive 0.13.0版本之前，在本地模式下，日志文件名为“.log”而不是“hive.log”。
这个bug在0.13.0版本中已经修复（参见HIVE-5528和HIVE-5676）。
```
要想修改默认配置的日志位置，请在$ HIVE_HOME / conf / hive-log4j.properties中设置hive.log.dir。 请注意文件权限问题（chmod 777 <dir>）。

```
hive.log.dir=<other_location>
```

### 2.日志输出控制台

如果用户希望将日志发送到控制台，可以添加如下参数：
```
bin/hive --hiveconf hive.root.logger=INFO,console  //for HiveCLI (deprecated)
bin/hiveserver2 --hiveconf hive.root.logger=INFO,console
```
或者，用户可以只使用下面方式更改日志记录级别：
```
bin/hive --hiveconf hive.root.logger=INFO,DRFA //for HiveCLI (deprecated)
bin/hiveserver2 --hiveconf hive.root.logger=INFO,DRFA
```
另一个日志记录选项是TimeBasedRollingPolicy（适用于Hive 0.15.0及更高版本，HIVE-9001），通过提供DAILY选项使用，如下所示：
```
bin/hive --hiveconf hive.root.logger=INFO,DAILY //for HiveCLI (deprecated)
bin/hiveserver2 --hiveconf hive.root.logger=INFO,DAILY
```

注意
```
通过'set'命令设置hive.root.logger不会改变日志配置，因为它们总是在初始化时确定的。
```






Hive还可以按每个Hive会话存储查询日志到/tmp/<user.name>/目录中，需在hive-site.xml配置文件中使用hive.querylog.location属性进行配置。

在Hadoop集群上执行Hive期间的日志记录是由Hadoop配置控制。 通常Hadoop将为每个Map和Redue生成一个日志文件，存储在任务执行的集群机器上。 可以通过在Hadoop JobTracker Web UI单击任务详细信息页面来获取日志文件。

当使用本地模式（使用mapreduce.framework.name = local）时，Hadoop / Hive执行日志会在客户端计算机本身上生成。

Hive 从0.6版本开始， 使用hive-exec-log4j.properties配置文件，来确定默认情况下这些日志的传输位置（只有在hive-exec-log4j.properties缺失时才会使用hive-log4j.properties）。 在本地模式下，默认配置文件会为执行的每个查询生成一个日志文件，并将其存储在/tmp/<user.name>目录下。 提供单独配置文件的目的是使管理员能够根据需要集中执行日志捕获（例如在NFS文件服务器上）。 执行日志对于调试运行时错误是非常重要的。

从Hive 2.1.0开始（使用HIVE-13027），Hive默认使用Log4j2的异步记录器（asynchronous logger）。 将**hive.async.log.enabled**设置为false将禁用异步日志记录（asynchronous logging），而使用同步日志记录（synchronous logging）。 异步日志记录可以显着提高性能，因为日志记录将在使用LMAX干扰器队列缓冲日志消息的单独线程中处理。 有关好处和缺点，请参阅https://logging.apache.org/log4j/2.x/manual/async.html。

HiveServer2 Logs

HiveServer2 operation logs are available to clients starting in Hive 0.14. See HiveServer2 Logging for configuration.

Audit Logs

Audit logs are logged from the Hive metastore server for every metastore API invocation.

An audit log has the function and some of the relevant function arguments logged in the metastore log file. It is logged at the INFO level of log4j, so you need to make sure that the logging at the INFO level is enabled (see HIVE-3505). The name of the log entry is "HiveMetaStore.audit".

 Audit logs were added in Hive 0.7 for secure client connections (HIVE-1948) and in Hive 0.10 for non-secure connections (HIVE-3277; also see HIVE-2797).
 
 Perf Logger
 
In order to obtain the performance metrics via the PerfLogger, you need to set DEBUG level logging for the PerfLogger class (HIVE-12675). This can be achieved by setting the following in the log4j properties file.
log4j.logger.org.apache.hadoop.hive.ql.log.PerfLogger=DEBUG

If the logger level has already been set to DEBUG at root via hive.root.logger, the above setting is not required to see the performance logs.