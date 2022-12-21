---
layout: post
author: sjf0115
title: Hive 从 CLI 迁移到 Beeline
date: 2018-07-24 13:01:01
tags:
  - Hive

categories: Hive
permalink: hive-base-migrating-from-hive-cli-to-beeline
---

之前，Apache Hive 是一个重量级命令行工具，接受查询 SQL 并转换为 MapReduce 执行。后来，该工具拆分为客户端与服务器模式，服务器为 `HiveServer1` （负责编译和监控 MapReduce 作业），Hive CLI 是命令行界面（将 SQL 发送到 server）。

后来 Hive 社区推出了 HiveServer2，这是一个增强的 Hive Server，专为多客户端并发和改进身份验证而设计，也为通过 JDBC 和 ODBC 连接的客户端提供了更好的支持。现在，推荐使用 HiveServer2，Beeline 作为命令行界面；不推荐使用 HiveServer1 和 Hive CLI，后者甚至都不能与 HiveServer2 一起使用。

Beeline 专门开发用来与新服务器进行交互。与基于 Apache Thrift 的 Hive CLI 客户端不同，Beeline 是基于 SQLLine CLI 的 JDBC 客户端 - 尽管 JDBC 驱动程序使用 HiveServer2 的 Thrift API 与 HiveServer2 进行通信。

随着 Hive 从最初的 Hive Server（HiveServer1）发展到新的 HiveServer2，用户和开发人员因此需要切换到新的客户端工具。但是，这个过程不仅仅简单地将可执行文件名从 hive 切换为 beeline。

在这篇文章中，我们将学习如何进行迁移，以及了解两个客户端之间的差异和相似之处。这篇文章我们主要关注如何使用 Beeline 实现以前使用 Hive CLI 做的事情。下面重点介绍 Hive CLI/HiveServer1 的常见用法以及如何在各种情况下迁移到 Beeline/HiveServer2。

### 1. 连接服务器

Hive CLI 使用 Thrift 协议连接到远程 HiveServer1 实例。要连接到服务器，需要指定远程服务器的主机名以及可选的端口号：
```
hive -h <hostname> -p <port>
```
相反，Beeline 使用 JDBC 连接到远程 HiveServer2 实例。因此，连接参数是在基于 JDBC 的客户端中常见的 JDBC URL：
```
beeline -u <url> -n <username> -p <password>
```
以下是一些　URL 示例：
```
jdbc:hive2://ubuntu:11000/db2?hive.cli.conf.printheader=true;hive.exec.mode.local.auto.inputbytes.max=9999#stab=salesTable;icol=customerID
jdbc:hive2://?hive.cli.conf.printheader=true;hive.exec.mode.local.auto.inputbytes.max=9999#stab=salesTable;icol=customerID
jdbc:hive2://ubuntu:11000/db2;user=foo;password=bar
jdbc:hive2://server:10001/db;user=foo;password=bar?hive.server2.transport.mode=http;hive.server2.thrift.http.path=hs2
```
### 2. 查询执行

在 Beeline 中执行查询与 Hive CLI 中的查询非常相似。在 Hive CLI 中：
```
hive -e <query in quotes>
hive -f <query file name>
```
在 Beeline 中:
```
beeline -e <query in quotes>
beeline -f <query file name>
```
在任何一种情况下，如果没有给出 `-e` 或 `-f` 选项，则两个客户端工具都将进入交互模式，你可以在其中逐行提供和执行查询或命令。

### 3. 嵌入模式

使用嵌入式服务器运行 Hive 客户端工具是测试查询或调试问题的便捷方式。虽然 Hive CLI 和 Beeline 都可以嵌入 Hive 服务器实例，但你可以采用稍微不同的方式在嵌入模式下启动它们。

如果以嵌入模式启动 Hive CLI，只需启动客户端而不用提供任何连接参数：
```
hive
```
要在嵌入模式下启动 Beeline，则需要做更多的参数。基本上，需要指定 `jdbc:hive2://` 的连接URL：
```
beeline -u jdbc:hive2://
```
这时，Beeline 进入交互模式，在该模式下可以执行针对嵌入式 HiveServer2 实例的查询和命令。

### 4. 变量

也许客户端之间最有趣的区别在于 Hive 变量的使用。变量有四个命名空间：
- hiveconf：hive 配置变量
- system：系统变量
- env：环境变量
- hivevar：Hive 变量（[HIVE-1096](https://issues.apache.org/jira/browse/HIVE-1096)）

变量表示为 `＆namespace>：`。对于 Hive 配置变量，可以跳过命名空间 hiveconf。可以使用美元符号引用变量的值，例如`${hivevar：var}`。

有两种方法可以定义变量：作为命令行参数或在交互模式下使用 set 命令。

在 Hive CLI 的命令行中定义 Hive 变量：
```
hive -d key=value
hive --define key=value
hive --hivevar key=value
```
在 Beeline 的命令行中定义 Hive 变量（仅适用于CDH 5，因为 HIVE-4568 不会向后移植到 CDH 4）：
```
beeline --hivevar key=value
```
在 Hive CLI 的命令行中定义 Hive 配置变量：
```
hive --hiveconf key=value
```
在撰写本文时(2014)，在 Beeline 中，无法在命令行中定义 Hive 配置变量（HIVE-6173）。

在 Hive CLI 和 Beeline 中，你可以使用 set 命令以相同的方式在交互模式下设置变量：
```
hive> set system:os.name=OS2;
0: jdbc:hive2://> set system:os.name=OS2;
```
显示变量的值：
```
hive> set env:TERM;
env:TERM=xterm
0: jdbc:hive2://> set env:TERM;
(Currently display nothing. HIVE-6174)
```
请注意，无法设置环境变量：
```
hive> set env:TERM=xterm;
env:* variables cannot be set.
0: jdbc:hive2://> set env:TERM=xterm;
env:* variables can not be set.
```
没有任何参数的 set 命令列出了所有变量及其值：
```
hive> set;
datanucleus.autoCreateSchema=true
...
0: jdbc:hive2://> set;
+----------------------------------------------------------------+
|                                                                |
+----------------------------------------------------------------+
| datanucleus.autoCreateSchema=true
```

### 5. Command-Line Help

当然，你始终可以在命令行参数上找到帮助：
```
hive -H
beeline -h
beeline --help
```
### 6. 交互模式

在 Hive CLI 交互模式下，你可以执行 HiveServer 支持的任何 SQL 查询。例如：
```
hive> show databases;
OK
default
```
此外，你可以在不离开 Hive CLI 的情况下执行 shell 命令：
```
hive> !cat myfile.txt;
This is my file!
hive>
```
在 Beeline 中，你可以像在 Hive CLI 中那样执行任何 SQL 查询。例如：
```
0: jdbc:hive2://> show databases;
14/01/31 16:50:47 INFO log.PerfLogger: <PERFLOG method=compile from=org.apache.hadoop.hive.ql.Driver>
...
+----------------+
| database_name  |
+----------------+
| default    	|
+----------------+

1 row selected (0.026 seconds)

...
```
以上命令相当于：
```
0: jdbc:hive2://> !sql show databases;
```
如你所见，你使用 `!` 来执行 Beeline 命令而不是 shell 命令。在 Beeline 命令中，`! connect` 是最重要的命令之一；它允许你连接到数据库：
```
beeline> !connect jdbc:hive2://
scan complete in 2ms
Connecting to jdbc:hive2://
Enter username for jdbc:hive2://:
Enter password for jdbc:hive2://:
...
Connected to: Apache Hive (version 0.13.0-SNAPSHOT)
Driver: Hive JDBC (version 0.13.0-SNAPSHOT)
Transaction isolation: TRANSACTION_REPEATABLE_READ
0: jdbc:hive2://>
```
另一个重要的命令是`! quit`（或`！q`），它允许你退出交互模式：
```
0: jdbc:hive2://> !quit
Closing: org.apache.hive.jdbc.HiveConnection
```

原文：http://blog.cloudera.com/blog/2014/02/migrating-from-hive-cli-to-beeline-a-primer/
