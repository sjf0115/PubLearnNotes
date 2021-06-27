---
layout: post
author: sjf0115
title: Hadoop Streaming使用指南
date: 2018-05-10 13:15:00
tags:
  - Hadoop
  - Hadoop 基础

categories: Hadoop
permalink: hadoop-streaming-use-guide
---

### 1. 概述

Hadoop Streaming 是Hadoop发行版附带的实用工具。该工具允许你使用任何可执行文件或脚本作为 mapper 或 reducer 来创建和运行 Map/Reduce 作业。 例如：
```
mapred streaming \
  -input myInputDirs \
  -output myOutputDir \
  -mapper /bin/cat \
  -reducer /usr/bin/wc
```

### 2. 如何工作

在上面的例子中，mapper 和 reducer 都是可执行文件，它们从 stdin （逐行读取）输入，并将输出发送到 stdout。Hadoop Streaming 将创建一个 Map/Reduce作业，并将作业提交到集群上，同时监视作业的进度。

当 mapper 指定为可执行文件时，在 mapper 初始化时每个 mapper 任务将可执行文件作为一个单独的进程进行启动。当 mapper 任务运行时，将输入转换为行并提供给 stdin 进程。与此同时，mapper 从 stdout 进程收集以行格式的输出，并将每行转换为一个键/值对，将其作为 mapper 的输出。默认情况下，每行第一个制表符之前的前缀（包括制表符本身）为 key，而剩下的为 value。如果行中没有制表符，则整行被认为是 key，value 为空。但是，这可以通过 `-inputformat` 命令选项来设置，稍后讨论。

当 reducer 指定为可执行文件时，每个 reducer 任务将可执行文件作为一个单独的进程进行启动，然后对 reducer 进行初始化。 在 reducer 任务运行时，将输入键/值对转换为行并将提供给 stdin 进程。同时，reducer 从 stdout 进程收集以行格式的输出，并将每行转换为键/值对，作为 reducer 的输出。默认情况下，每行第一个制表符之前的前缀（包括制表符本身）为 key，而剩下的为 value。但是，这可以通过 `-outputformat` 命令选项来设置，稍后讨论。

这是 Map/Reduce 框架和 streaming mapper/reducer 之间通信协议的基础。

用户可以指定 `stream.non.zero.exit.is.failure` 为 true 或 false，以使 streaming 任务的非零状态分别标识为 Failure 或 Success。默认情况下，以非零状态退出的流式处理任务被视为失败任务。

### 3. Streaming Command Options

Streaming 支持流式命令选项以及[通用命令选项](http://hadoop.apache.org/docs/r3.1.0/hadoop-streaming/HadoopStreaming.html#Generic_Command_Options)。一般的命令行语法如下所示。

> 确保通用命令选项在流式命令选项之前放置，否则命令将失效。有关示例，请参阅使[Making Archives Available to Tasks](http://hadoop.apache.org/docs/r3.1.0/hadoop-streaming/HadoopStreaming.html#Making_Archives_Available_to_Tasks)。

```
mapred streaming [genericOptions] [streamingOptions]
```

Parameter|Optional/Required|Description
---|---|---
-input directoryname or filename|Required|Input location for mapper
-output directoryname|Required|Output location for reducer
-mapper executable or JavaClassName|Optional|Mapper executable. If not specified, IdentityMapper is used as the default
-reducer executable or JavaClassName|Optional|Reducer executable. If not specified, IdentityReducer is used as the default
-file filename|Optional|Make the mapper, reducer, or combiner executable available locally on the compute nodes
-inputformat JavaClassName|Optional|Class you supply should return key/value pairs of Text class. If not specified, TextInputFormat is used as the default
-outputformat JavaClassName|Optional|Class you supply should take key/value pairs of Text class. If not specified, TextOutputformat is used as the default
-partitioner JavaClassName|Optional|Class that determines which reduce a key is sent to
-combiner streamingCommand or JavaClassName	|Optional|Combiner executable for map output
-cmdenv name=value|Optional|Pass environment variable to streaming commands
-inputreader|Optional|For backwards-compatibility: specifies a record reader class (instead of an input format class)
-verbose|Optional|Verbose output
-lazyOutput|Optional|Create output lazily. For example, if the output format is based on FileOutputFormat, the output file is created only on the first call to Context.write
-numReduceTasks|Optional|Specify the number of reducers
-mapdebug|Optional|Script to call when map task fails
-reducedebug|Optional|Script to call when reduce task fails

#### 3.1 指定Java类作为Mapper/Reducer

你可以提供一个 Java 类作为 mapper 或 reducer：
```
mapred streaming \
  -input myInputDirs \
  -output myOutputDir \
  -inputformat org.apache.hadoop.mapred.KeyValueTextInputFormat \
  -mapper org.apache.hadoop.mapred.lib.IdentityMapper \
  -reducer /usr/bin/wc
```
你可以将 `stream.non.zero.exit.is.failure` 指定为 true 或 false，以使 streaming 任务的非零状态分别表示为失败或成功。默认情况下，以非零状态退出的流式处理任务被视为失败任务。

#### 3.2 用作业提交打包文件

你可以指定任何可执行文件作为 mapper 或 reducer。可执行文件不需要预先存在集群机器上。但是，如果不存在于集群机器上，则需要使用 `-file` 选项来告诉框架将可执行文件打包为作业提交的一部分。例如：
```
mapred streaming \
  -input myInputDirs \
  -output myOutputDir \
  -mapper myPythonScript.py \
  -reducer /usr/bin/wc \
  -file myPythonScript.py
```
上面的例子将用户定义的 Python 可执行文件指定为 mapper。`-file myPythonScript.py` 选项会将 Python 可执行文件作为作业提交的一部分发送到集群机器上。

除了可执行文件之外，你还可以打包 mapper 或 reducer 使用到的其他辅助文件（例如字典，配置文件等）。例如：
```
mapred streaming \
  -input myInputDirs \
  -output myOutputDir \
  -mapper myPythonScript.py \
  -reducer /usr/bin/wc \
  -file myPythonScript.py \
  -file myDictionary.txt
```

#### 3.3 指定作业的其他插件

就像正常的 Map/Reduce 作业一样，你可以为一个流式作业指定其他插件：
```aClassName
-outputformat JavaClassName
-partitioner JavaClassName
-combiner streamingCommand or JavaClassName
```
你为输入格式提供的类返回 Text 类的键/值对。如果你不指定输入格式类，则将 `TextInputFormat` 作为默认值。由于　`TextInputFormat` 返回 `LongWritable` 类的键，它们实际上不是输入数据的一部分，所以键将被丢弃，只有值将被传送到 mapper。

你为输出格式提供的类期望采用 Text 类的键/值对。如果你不指定输出格式类，则将 `TextOutputFormat` 作为默认值。

#### 3.4 设置环境变量

要在流式命令中设置环境变量，请使用：
```
 -cmdenv EXAMPLE_DIR=/home/example/dictionaries/
```

### 4. Generic Command Options

通用命令行语法如下所示。

> 确保通用命令选项在流式命令选项之前放置，否则命令将失效。有关示例，请参阅使[Making Archives Available to Tasks](http://hadoop.apache.org/docs/r3.1.0/hadoop-streaming/HadoopStreaming.html#Making_Archives_Available_to_Tasks)。

```
hadoop command [genericOptions] [streamingOptions]
```
这里列出了你可以用于流式处理的Hadoop通用命令选项：

参数|可选/必需|描述
---|---|---
-conf configuration_file|可选|指定应用程序配置文件
-D property=value|可选|使用给定属性的值
-fs host:port or local|可选|指定一个namenode
-files|可选|指定拷贝到 Map/Reduce集群的文件，以逗号分隔
-libjars|可选|指定jar文件以包含在classpath中，以逗号分隔
-archives|可选|指定逗号分隔的 archives 在计算机器上解除存档

#### 4.1 使用-D选项指定配置变量

你可以使用 `-D <property> = <value>` 来指定其他配置变量。

##### 4.1.1 指定目录

要更改本地临时目录，请使用：
```
 -D dfs.data.dir=/tmp
```
要指定其他本地临时目录，请使用：
```
-D mapred.local.dir=/tmp/local
-D mapred.system.dir=/tmp/system
-D mapred.temp.dir=/tmp/temp
```

> 有关作业配置参数的更多详细信息，请参阅：[mapred-default.xml](http://hadoop.apache.org/docs/r3.1.0/hadoop-mapreduce-client/hadoop-mapreduce-client-core/mapred-default.xml)

##### 4.1.2 指定仅有Map的作业

有时你可能只想使用 map 函数处理输入数据。只需将 `mapreduce.job.reduces` 设置为零即可实现。Map/Reduce 框架不会创建任何 Reducer 任务。相反，Mapper 任务的输出就是该作业的最终输出。
```
 -D mapreduce.job.reduces=0
```
为了向后兼容，Hadoop Streaming还支持 `-reducer NONE` 选项来设置仅有 Map 的作业，等价于上述命令。

##### 4.1.3 指定Reducer的个数

指定Reducer的个数，例如指定两个Reducer，使用如下命令：
```
mapred streaming \
  -D mapreduce.job.reduces=2 \
  -input myInputDirs \
  -output myOutputDir \
  -mapper /bin/cat \
  -reducer /usr/bin/wc
```

##### 4.1.4 自定义行记录拆分为键/值对

如前所述，当 Map/Reduce 框架从 mapper 的stdout中读取一行数据时，将该行拆分成键/值对。默认情况下，第一个制表符的之前的前缀（包括制表符）是键，其余部分（不包括制表符）是值。

默认值为制表符，但是你也可以自定义。你可以指定除制表符以外的字段作为分隔符，并且可以指定第n个（n> = 1）字符而不是第一个字符作为键和值之间的分隔符（例如，你可以指定第２个逗号为键和值的分隔符）。 例如：
```
mapred streaming \
  -D stream.map.output.field.separator=. \
  -D stream.num.map.output.key.fields=4 \
  -input myInputDirs \
  -output myOutputDir \
  -mapper /bin/cat \
  -reducer /bin/cat
```
在上面的例子中，`-D stream.map.output.field.separator =.` 指定 `.` 作为 map 输出的字段分隔符，第四个 `.` 之前的前缀将成为键，剩余的（不包括第四个 `.`）为值。如果一行中不够四个 `.`，那么整行将是键，值为一个空的Text对象（像由`new Text("")`创建的一样）。

同样，你可以使用 `-D stream.reduce.output.field.separator` 和 `-D stream.num.reduce.output.fields` 为 reduce 输出指定键和值之间的分隔符。

同样，你可以指定 `stream.map.input.field.separator` 和 `stream.reduce.input.field.separator` 为 Map/Reduce 输入指定键和值之间的分隔符。默认情况下，分隔符是制表符。

##### 4.1.5 使用大型文件和档案

`-files` 和 `-archives` 选项可以使你的文件和档案对于任务可见。参数是你已上传到HDFS的文件或存档的URI。这些文件和档案将跨作业缓存。你可以从 fs.default.name 配置变量中检索 host 和 fs_port 值。

> `-files` 和 `-archives` 选项是通用选项。请务必在命令选项之前放置通用选项，否则命令将失败。


> Hadoop版本:3.1.0

原文：http://hadoop.apache.org/docs/r3.1.0/hadoop-streaming/HadoopStreaming.html
