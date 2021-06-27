---
layout: post
author: sjf0115
title: Flink1.4 命令行界面
date: 2018-01-30 15:30:17
tags:
  - Flink
  - Flink 基础

categories: Flink
permalink: flink-basic-command-line-interface
---

### 1. 概述

`Flink` 提供了一个命令行接口（CLI）用来运行打成JAR包的程序，并且可以控制程序的运行。命令行接口在 `Flink` 安装完之后即可拥有，本地单节点或是分布式部署安装都会有命令行接口。命令行接口启动脚本是 `$FLINK_HOME/bin` 目录下的 `flink` 脚本， 默认情况下会连接运行中的 `Flink master(JobManager)`， `JobManager` 的启动脚本与 `CLI` 在同一安装目录下。

使用命令行接口的前提条件是 `JobManager` 已经被启动(通过`$FLINK_HOME/bin/start-local.sh` 或是 `$FLINK_HOME/bin/start-cluster.sh`)或是 `Flink YARN` 环境可用。 `JobManager` 可以通过如下命令启动:
```
$FLINK_HOME/bin/start-local.sh
或
$FLINK_HOME/bin/start-cluster.sh
```
### 2. Example

(1) 运行示例程序，不传参数：
```
./bin/flink run ./examples/batch/WordCount.jar
```
(2) 运行示例程序，带输入和输出文件参数：
```
./bin/flink run ./examples/batch/WordCount.jar --input file:///home/xiaosi/a.txt --output file:///home/xiaosi/result.txt
```
(3) 运行示例程序，带输入和输出文件参数,并设置16个并发度：
```
./bin/flink run -p 16 ./examples/batch/WordCount.jar --input file:///home/xiaosi/a.txt --output file:///home/xiaosi/result.txt
```
(4) 运行示例程序，并禁止 `Flink` 输出日志
```
./bin/flink run -q ./examples/batch/WordCount.jar
```
(5) 以独立(detached)模式运行示例程序
```
./bin/flink run -d ./examples/batch/WordCount.jar
```
(6) 在指定 `JobManager` 上运行示例程序
```
./bin/flink run -m myJMHost:6123 ./examples/batch/WordCount.jar --input file:///home/xiaosi/a.txt --output file:///home/xiaosi/result.txt
```
(7) 运行示例程序，指定程序入口类(Main方法所在类)：
```
./bin/flink run -c org.apache.flink.examples.java.wordcount.WordCount ./examples/batch/WordCount.jar --input file:///home/xiaosi/a.txt --output file:///home/xiaosi/result.txt
```
(8) 运行示例程序，使用带有2个 `TaskManager` 的[per-job YARN 集群](https://ci.apache.org/projects/flink/flink-docs-release-1.3/setup/yarn_setup.html#run-a-single-flink-job-on-hadoop-yarn)
```
./bin/flink run -m yarn-cluster -yn 2 ./examples/batch/WordCount.jar --input hdfs:///xiaosi/a.txt --output hdfs:///xiaosi/result.txt
```
(9) 以JSON格式输出 `WordCount` 示例程序优化执行计划：
```
./bin/flink info ./examples/batch/WordCount.jar --input file:///home/xiaosi/a.txt --output file:///home/xiaosi/result.txt
```
(10) 列出已经调度的和正在运行的Job(包含Job ID信息)
```
./bin/flink list
```
(11) 列出已经调度的Job(包含Job ID信息)
```
./bin/flink list -s
```
(13) 列出正在运行的Job(包含Job ID信息)
```
./bin/flink list -r
```
(14) 列出在Flink YARN中运行Job
```
./bin/flink list -m yarn-cluster -yid <yarnApplicationID> -r
```
(15) 取消一个Job
```
./bin/flink cancel <jobID>
```
(16) 取消一个带有保存点(savepoint)的Job
```
./bin/flink cancel -s [targetDirectory] <jobID>
```
(17) 停止一个Job(只适用于流计算Job)
```
./bin/flink stop <jobID>
```

取消和停止一个作业的区别如下：
- 调用取消作业时，作业中的算子立即收到一个调用`cancel()`方法的指令以尽快取消它们。如果算子在调用取消操作后没有停止，`Flink` 将定期开启中断线程来取消作业直到作业停止。
- 停止作业是一种停止正在运行的流作业的更加优雅的方法。停止仅适用于使用实现`StoppableFunction`接口的数据源的那些作业。当用户请求停止作业时，所有数据源将收到调用`stop()`方法指令。但是作业还是会继续运行，直到所有数据源正确关闭。这允许作业处理完所有正在传输的数据(inflight data)。

### 3. 保存点

保存点通过命令行客户端进行控制：

#### 3.1 触发保存点

```
./bin/flink savepoint <jobID> [savepointDirectory]
```
这会触发作业ID为`jobId`的保存点，并返回创建的保存点的路径。你需要此路径来还原和处理保存点。

此外，你可以选择指定一个目标文件系统目录来存储保存点。目录可以被 `JobManager` 访问。

如果你不指定目标目录，则需要配置默认目录（请参阅[保存点](https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/state/savepoints.html#configuration)）。 否则，触发保存点将失败。

#### 3.2 使用YARN触发保存点

```
./bin/flink savepoint <jobId> [savepointDirectory] -yid <yarnAppId>
```

这将触发作业ID为 `jobId` 以及 `YARN` 应用程序ID为 `yarnAppId` 的保存点，并返回创建的保存点的路径。

其他一切与上面的触发保存点中描述的相同。

#### 3.3 根据保存点取消Job

你可以自动触发一个保存点并取消作业:
```
./bin/flink cancel -s  [savepointDirectory] <jobID>
```
如果没有配置保存点目录，则需要为 `Flink` 安装配置默认的保存点目录(请参阅[保存点](https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/state/savepoints.html#configuration)）。

只有保存点触发成功，作业才被取消

#### 3.4 恢复保存点

```
./bin/flink run -s <savepointPath> ...
```
这个`run`命令提交作业时带有一个保存点标记，这使得程序可以从保存点中恢复状态。保存点路径是通过保存点触发命令得到的。

默认情况下，我们尝试将所有的保存点状态与正在提交的作业进行匹配。如果你想允许跳过无法使用新作业恢复的保存点状态，则可以设置`allowNonRestoredState`标志。当保存点触发时，如果想从程序中删除一个算子（作为程序的一部分），并且仍然想要使用这个保存点，则需要允许这一点。

```
./bin/flink run -s <savepointPath> -n ...
```
如果想从程序中删除算子(作为保存点一部分的)，这时会非常有用。

#### 3.5 销毁保存点

```
./bin/flink savepoint -d <savepointPath>
```
销毁一个保存点同样需要一个路径。这个保存点路径是通过保存点触发命令得到的。

如果使用自定义状态实例（例如自定义 `reducing` 状态或 `RocksDB` 状态），则必须指定程序JAR的路径以及被触发的保存点，以便使用用户代码类加载器来销毁保存点：
```
./bin/flink savepoint -d <savepointPath> -j <jarFile>
```
否则，你将遇到 `ClassNotFoundException`。

### 4. 用法

下面是Flink命令行接口的用法:
```
xiaosi@yoona:~/qunar/company/opt/flink-1.3.2$ ./bin/flink
./flink <ACTION> [OPTIONS] [ARGUMENTS]

The following actions are available:

Action "run" compiles and runs a program.

  Syntax: run [OPTIONS] <jar-file> <arguments>
  "run" action options:
     -c,--class <classname>                         Class with the program entry
                                                    point ("main" method or
                                                    "getPlan()" method. Only
                                                    needed if the JAR file does
                                                    not specify the class in its
                                                    manifest.
     -C,--classpath <url>                           Adds a URL to each user code
                                                    classloader  on all nodes in
                                                    the cluster. The paths must
                                                    specify a protocol (e.g.
                                                    file://) and be accessible
                                                    on all nodes (e.g. by means
                                                    of a NFS share). You can use
                                                    this option multiple times
                                                    for specifying more than one
                                                    URL. The protocol must be
                                                    supported by the {@link
                                                    java.net.URLClassLoader}.
     -d,--detached                                  If present, runs the job in
                                                    detached mode
     -m,--jobmanager <host:port>                    Address of the JobManager
                                                    (master) to which to
                                                    connect. Use this flag to
                                                    connect to a different
                                                    JobManager than the one
                                                    specified in the
                                                    configuration.
     -n,--allowNonRestoredState                     Allow to skip savepoint
                                                    state that cannot be
                                                    restored. You need to allow
                                                    this if you removed an
                                                    operator from your program
                                                    that was part of the program
                                                    when the savepoint was
                                                    triggered.
     -p,--parallelism <parallelism>                 The parallelism with which
                                                    to run the program. Optional
                                                    flag to override the default
                                                    value specified in the
                                                    configuration.
     -q,--sysoutLogging                             If present, suppress logging
                                                    output to standard out.
     -s,--fromSavepoint <savepointPath>             Path to a savepoint to
                                                    restore the job from (for
                                                    example
                                                    hdfs:///flink/savepoint-1537
                                                    ).
     -z,--zookeeperNamespace <zookeeperNamespace>   Namespace to create the
                                                    Zookeeper sub-paths for high
                                                    availability mode
  Options for yarn-cluster mode:
     -yD <arg>                            Dynamic properties
     -yd,--yarndetached                   Start detached
     -yid,--yarnapplicationId <arg>       Attach to running YARN session
     -yj,--yarnjar <arg>                  Path to Flink jar file
     -yjm,--yarnjobManagerMemory <arg>    Memory for JobManager Container [in
                                          MB]
     -yn,--yarncontainer <arg>            Number of YARN container to allocate
                                          (=Number of Task Managers)
     -ynm,--yarnname <arg>                Set a custom name for the application
                                          on YARN
     -yq,--yarnquery                      Display available YARN resources
                                          (memory, cores)
     -yqu,--yarnqueue <arg>               Specify YARN queue.
     -ys,--yarnslots <arg>                Number of slots per TaskManager
     -yst,--yarnstreaming                 Start Flink in streaming mode
     -yt,--yarnship <arg>                 Ship files in the specified directory
                                          (t for transfer)
     -ytm,--yarntaskManagerMemory <arg>   Memory per TaskManager Container [in
                                          MB]
     -yz,--yarnzookeeperNamespace <arg>   Namespace to create the Zookeeper
                                          sub-paths for high availability mode

  Options for yarn mode:
     -ya,--yarnattached                   Start attached
     -yD <arg>                            Dynamic properties
     -yj,--yarnjar <arg>                  Path to Flink jar file
     -yjm,--yarnjobManagerMemory <arg>    Memory for JobManager Container [in
                                          MB]
     -yqu,--yarnqueue <arg>               Specify YARN queue.
     -yt,--yarnship <arg>                 Ship files in the specified directory
                                          (t for transfer)
     -yz,--yarnzookeeperNamespace <arg>   Namespace to create the Zookeeper
                                          sub-paths for high availability mode



Action "info" shows the optimized execution plan of the program (JSON).

  Syntax: info [OPTIONS] <jar-file> <arguments>
  "info" action options:
     -c,--class <classname>           Class with the program entry point ("main"
                                      method or "getPlan()" method. Only needed
                                      if the JAR file does not specify the class
                                      in its manifest.
     -p,--parallelism <parallelism>   The parallelism with which to run the
                                      program. Optional flag to override the
                                      default value specified in the
                                      configuration.
  Options for yarn-cluster mode:
     -yid,--yarnapplicationId <arg>   Attach to running YARN session

  Options for yarn mode:




Action "list" lists running and scheduled programs.

  Syntax: list [OPTIONS]
  "list" action options:
     -m,--jobmanager <host:port>   Address of the JobManager (master) to which
                                   to connect. Use this flag to connect to a
                                   different JobManager than the one specified
                                   in the configuration.
     -r,--running                  Show only running programs and their JobIDs
     -s,--scheduled                Show only scheduled programs and their JobIDs
  Options for yarn-cluster mode:
     -yid,--yarnapplicationId <arg>   Attach to running YARN session

  Options for yarn mode:




Action "stop" stops a running program (streaming jobs only).

  Syntax: stop [OPTIONS] <Job ID>
  "stop" action options:
     -m,--jobmanager <host:port>   Address of the JobManager (master) to which
                                   to connect. Use this flag to connect to a
                                   different JobManager than the one specified
                                   in the configuration.
  Options for yarn-cluster mode:
     -yid,--yarnapplicationId <arg>   Attach to running YARN session

  Options for yarn mode:




Action "cancel" cancels a running program.

  Syntax: cancel [OPTIONS] <Job ID>
  "cancel" action options:
     -m,--jobmanager <host:port>            Address of the JobManager (master)
                                            to which to connect. Use this flag
                                            to connect to a different JobManager
                                            than the one specified in the
                                            configuration.
     -s,--withSavepoint <targetDirectory>   Trigger savepoint and cancel job.
                                            The target directory is optional. If
                                            no directory is specified, the
                                            configured default directory
                                            (state.savepoints.dir) is used.
  Options for yarn-cluster mode:
     -yid,--yarnapplicationId <arg>   Attach to running YARN session

  Options for yarn mode:




Action "savepoint" triggers savepoints for a running job or disposes existing ones.

  Syntax: savepoint [OPTIONS] <Job ID> [<target directory>]
  "savepoint" action options:
     -d,--dispose <arg>            Path of savepoint to dispose.
     -j,--jarfile <jarfile>        Flink program JAR file.
     -m,--jobmanager <host:port>   Address of the JobManager (master) to which
                                   to connect. Use this flag to connect to a
                                   different JobManager than the one specified
                                   in the configuration.
  Options for yarn-cluster mode:
     -yid,--yarnapplicationId <arg>   Attach to running YARN session

  Options for yarn mode:

  Please specify an action.
```

备注:
```
Flink版本:1.4
```

原文:https://ci.apache.org/projects/flink/flink-docs-release-1.4/ops/cli.html#command-line-interface
