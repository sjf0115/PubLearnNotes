---
layout: post
author: sjf0115
title: Hive 正则序列化器 RegexSerDe
date: 2018-06-06 13:16:01
tags:
  - Hive

categories: Hive
permalink: hive-base-how-to-use-regexserde
---

RegexSerDe 可以从 Hive 两个 jar 文件的类中获取，`hive-serde-<version>.jar`中的 `org.apache.hadoop.hive.contrib.serde2.RegexSerDe` 以及 `hive-contrib-<version>.jar` 中的 `org.apache.hadoop.hive.serde2.RegexSerDe`。

### 1. hive.serde2.RegexSerDe

下面这种格式是 Apache 的打出的 Web 日志文件格式。包含我们想要获取的两个字段信息，一个是日志时间，一个是日志 Json：
```
[2018-06-04 00:00:09  INFO price:335] {"os":"adr","phone":"187xxxx3617", "business":"train", "price":"198"}
```
我们使用 RegexSerDe 类作为 SERDE 在正则表达式的帮助下处理上面日志：
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS adv_push_price (
  time string,
  line string
)
PARTITIONED BY(
  dt string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES(
  'input.regex' = '\\[(\\d*-\\d*-\\d*\\s+\\d*:\\d*:\\d*)\\s+INFO.*\\]\\s+(.*)',
  'input.regex.case.insensitive' = 'false',
  'output.format.string' = '%1$s %2$s'
)
LOCATION '/user/xiaosi/log/price';
```
上面是一个外表，从 `/user/xiaosi/log/price` 路径下加载数据，并经正则表达式的处理，对应到 `time` 和 `line`　两个字段上，现在我们查看一下 Hive 表中的数据：
```
hive> select * from adv_push_price limit 10;
OK
2018-06-04 00:00:00 {"os":"adr","phone":"187xxxx3617", "business":"train", "price":"198"} 20180604
```
从上面输出中我们可以看到数据符合我们的预期。

### 2. hive.contrib.serde2.RegexSerDe

我们也可以使用 `org.apache.hadoop.hive.contrib.serde2.RegexSerDe`：
```sql
CREATE EXTERNAL TABLE IF NOT EXISTS adv_push_price (
  time string,
  line string
)
PARTITIONED BY(
  dt string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.contrib.serde2.RegexSerDe'
WITH SERDEPROPERTIES(
  'input.regex' = '\\[(\\d*-\\d*-\\d*\\s+\\d*:\\d*:\\d*)\\s+INFO.*\\]\\s+(.*)',
  'input.regex.case.insensitive' = 'false',
  'output.format.string' = '%1$s %2$s'
)
LOCATION '/user/xiaosi/log/price';
```
在运行过程中我们遇到如下错误：
```
Caused by: org.apache.hadoop.hive.ql.metadata.HiveException: java.lang.ClassNotFoundException: Class org.apache.hadoop.hive.contrib.serde2.RegexSerDe not found
        at org.apache.hadoop.hive.ql.exec.MapOperator.getConvertedOI(MapOperator.java:329)
        at org.apache.hadoop.hive.ql.exec.MapOperator.setChildren(MapOperator.java:364)
        at org.apache.hadoop.hive.ql.exec.mr.ExecMapper.configure(ExecMapper.java:106)
        ... 22 more
Caused by: java.lang.ClassNotFoundException: Class org.apache.hadoop.hive.contrib.serde2.RegexSerDe not found
        at org.apache.hadoop.conf.Configuration.getClassByName(Configuration.java:1626)
        at org.apache.hadoop.hive.ql.plan.PartitionDesc.getDeserializer(PartitionDesc.java:175)
        at org.apache.hadoop.hive.ql.exec.MapOperator.getConvertedOI(MapOperator.java:295)
        ... 24 more
```
上面的意思很明确，我们找不到 `org.apache.hadoop.hive.contrib.serde2.RegexSerDe` 类， `hive-contrib-<version>.jar` 可以在 `$HIVE_HOME/lib` 文件夹中找到，但是仍需要添加到环境变量中，将 `hive-contrib-<version>.jar` 配置到 Hive 会话中。如下所示将 `hive-contrib-<version>.jar` 添加到 `HIVE_AUX_JARS_PATH` 环境变量，将此 jar 永久添加到 Hive 会话中。在 `conf/hive-site.xml` 添加如下配置：
```
<property>
 <name>hive.aux.jars.path</name>
 <value>file:///home/q/hive/hive-2.1.0/lib/hive-contrib-2.1.0.jar</value>
</property>
```

`org.apache.hadoop.hive.serde2.RegexSerDe` 对应的 `hive-serde-<version>.jar` 默认包含在 hive 执行路径中，而 `org.apache.hadoop.hive.contrib.serde2.RegexSerDe` 对应的 `hive-serde-<version>.jar` 却不包含在 hive 执行路径中。

> 如果表中和数据中定义的列数不匹配，那么我们会遇到下面的错误消息:
```
Diagnostic Messages for this Task:
Error: java.lang.RuntimeException: org.apache.hadoop.hive.ql.metadata.HiveException: Hive Runtime Error while processing writable 64.242.88.10 - - [07/Mar/2014:16:05:49 -0800] "GET /twiki/bin/edit/Main/Double_bounce_sender?topicparent=Main.ConfigurationVariables HTTP/1.1" 401 12846
	at org.apache.hadoop.hive.ql.exec.mr.ExecMapper.map(ExecMapper.java:185)
	at org.apache.hadoop.mapred.MapRunner.run(MapRunner.java:54)
	at org.apache.hadoop.mapred.MapTask.runOldMapper(MapTask.java:430)
	at org.apache.hadoop.mapred.MapTask.run(MapTask.java:342)
	at org.apache.hadoop.mapred.YarnChild$2.run(YarnChild.java:168)
	at java.security.AccessController.doPrivileged(Native Method)
	at javax.security.auth.Subject.doAs(Subject.java:415)
	at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1548)
	at org.apache.hadoop.mapred.YarnChild.main(YarnChild.java:163)
Caused by: org.apache.hadoop.hive.ql.metadata.HiveException: Hive Runtime Error while processing writable 64.242.88.10 - - [07/Mar/2014:16:05:49 -0800] "GET /twiki/bin/edit/Main/Double_bounce_sender?topicparent=Main.ConfigurationVariables HTTP/1.1" 401 12846
	at org.apache.hadoop.hive.ql.exec.MapOperator.process(MapOperator.java:501)
	at org.apache.hadoop.hive.ql.exec.mr.ExecMapper.map(ExecMapper.java:176)
	... 8 more
Caused by: org.apache.hadoop.hive.serde2.SerDeException: Number of matching groups doesn't match the number of columns
	at org.apache.hadoop.hive.serde2.RegexSerDe.deserialize(RegexSerDe.java:180)
	at org.apache.hadoop.hive.ql.exec.MapOperator$MapOpCtx.readRow(MapOperator.java:136)
	at org.apache.hadoop.hive.ql.exec.MapOperator$MapOpCtx.access$200(MapOperator.java:100)
	at org.apache.hadoop.hive.ql.exec.MapOperator.process(MapOperator.java:492)
	... 9 more
FAILED: Execution Error, return code 2 from org.apache.hadoop.hive.ql.exec.mr.MapRedTask
```
查看Hive表中声明的列数及其数据类型，以及正则表达式及其输出中的字段 .format.string 应包含相同数量的列。

参考资料：
- http://hadooptutorial.info/processing-logs-in-hive/  
- https://blog.csdn.net/s530723542/article/details/38437257
- https://www.cnblogs.com/java20130722/archive/2013/06/09/3206794.html
