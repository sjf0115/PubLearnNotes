## 1. 作用

Exec Source 在启动时运行用户配置的 Unix 命令，并且期望在基于命令的标准输出上连续生成事件。它还可以从命令中输出错误流，将数据转换为 Flume 的事件，并将它们写入 Channel。Source 希望命令不断生产数据，如果进程因任何原因退出，那么 Source 也会退出并且停止生成数据。只要命令开始运行，Source 就要不停地运行和处理，不断地读取处理的输出流(如果配置了，还可以读取错误流)。综上来看 `cat [named pipe]` 或 `tail -F [file]` 这两个命令符合要求可以产生所需的结果，而 `date` 这种命令不符合要求，因为前两个命令能产生持续的数据流，而后者只会产生单个事件并随后退出。

> Exec Source 对命令的要求是需要不断的生成数据。`cat [named pipe]` 和 `tail -F [file]` 命令都能持续地生成数据，那些不能持续生成数据的命令则不不符合要求。这里注意一下 cat 命令后面接的参数是命名管道（named pipe）不是文件。

## 2. 属性

| 属性名 | 默认值 | 说明 |
| :------------- | :------------- | :------------- |
| channels | – | 与 Source 绑定的 Channel，多个用空格分开 |
| type | – | Source 类型：exec |
| command | – | Source 运行的用户配置的 Unix 命令，一般是 cat 或者 tail 命令 |
| restart | false | 如果设置为 true，当执行命令线程挂掉时 Source 将重启线程 |
| restartThrottle | 10000 | 重启线程前需要等待的时间，单位是毫秒。如果 restart 为 false 或者没有设置，则该参数没有作用 |
| logStdErr | false | 如果设置为 true，错误流也会被读取并转换为 Flume 事件 |
| batchSize | 20 | 读取并向 Channel 发送数据时单次发送的最大数量，即批次发送的最多事件数量 |
| batchTimeout | 3000 | 读取并向 Channel 发送数据时单次发送的最大等待时间（毫秒），如果等待了 batchTimeout 毫秒后未达到一次批量发送数量，仍然会执行发送。|
| shell | – | 设置用于运行命令的 Shell。例如 /bin/sh -c。仅适用于依赖 Shell 功能的命令，如通配符、后退标记、管道等。|

通过 command 参数告诉 Source 在启动时需要运行的用户配置的 Unix 命令，一般是 `cat` 或者 `tail` 命令。通过设置 logStdErr 参数为 true，错误流也会被读取并转换为 Flume 事件。通过设置 restart 参数为 true，可以设置当执行命令线程挂掉时 Source 自动重启线程。为了确保有足够的事件区别命令的执行，可以通过 restartThrottle 参数来设置重启线程前需要等待的时间。需要注意的是 restartThrottle 参数需要与 restart 参数配合使用，如果 restart 为 false 或者没有设置，那么该参数不会起作用。可以通过 batchSize 参数来控制一个事务中批次处理的事件量，即读取并向 Channel 发送数据时单次发送的最大数量。此外也可以从时间维度来控制向 Channel 发送的数据，可以在配置的时间段结束时写入 Channel，这需要通过 batchTimeout 参数来设置。如果 batchSize 和 batchTimeout 参数都设置了，只要满足其中一个条件就会批量写入到 Channel，即达到批次发送的最大数量或者批次到达等待时间。

shell 参数是用来配置执行命令的 shell（比如 Bash 或者 Powershell）。command 会作为参数传递给 shell 执行，这使得 command 可以使用 shell 中的特性，例如通配符、后退标记、管道、循环、条件等。如果没有 shell 配置，将直接调用 command 配置的命令。shell 通常配置的值有：`/bin/sh -c`、`/bin/ksh -c`、`cmd /c`、`powershell -Command` 等。例如如下示例所示，通过配置 shell 参数可以使得 command 可以使用 shell 中的循环特性：
```
a1.sources.execSource.type = exec
a1.sources.execSource.shell = /bin/bash -c
a1.sources.execSource.command = for i in /path/*.txt; do cat $i; done
```

## 3. 缺点

Exec Source 在 Flume 中最常用来追踪文件。利用 tail -F 命令适用 Exec Source 追踪文件，将近乎实时的将数据放入 Flume，但存在数据丢失的风险。如果 Flume Agent 挂掉或者机器重启，Exec Source 将在它启动的时候运行该命令，在这种情况下，它将运行 `tail -f <file_name>` 命令。因为 tail 命令只会拉取新数据写入到文件中的新数据，任何在 Agent 挂掉和 Source 启动期间的写入文件的数据都会丢失。由于这个原因，为了获得更强的可靠性保证，请考虑使用 Spooling Directory Source，Taildir Source 或通过 SDK 直接与 Flume 集成。

除了有数据丢失的风险之外，还有一个重复消费数据的问题。例如，我们监听的文件中有 4 条记录，当我们消费之后重新启动 Agent，这 4 条记录会被重新消费一次。这是 `tail -F` 本身机制的问题。
```
16 九月 2024 22:37:34,806 INFO  [main] (org.apache.flume.node.Application.startAllComponents:241)  - Starting Sink loggerSink
16 九月 2024 22:37:34,807 INFO  [main] (org.apache.flume.node.Application.startAllComponents:252)  - Starting Source execSource
16 九月 2024 22:37:34,809 INFO  [lifecycleSupervisor-1-1] (org.apache.flume.source.ExecSource.start:170)  - Exec source starting with command: tail -F /opt/data/flume/exec.log
16 九月 2024 22:37:34,810 INFO  [lifecycleSupervisor-1-1] (org.apache.flume.instrumentation.MonitoredCounterGroup.register:119)  - Monitored counter group for type: SOURCE, name: execSource: Successfully registered new MBean.
16 九月 2024 22:37:34,811 INFO  [lifecycleSupervisor-1-1] (org.apache.flume.instrumentation.MonitoredCounterGroup.start:95)  - Component type: SOURCE, name: execSource started
16 九月 2024 22:37:34,846 INFO  [SinkRunner-PollingRunner-DefaultSinkProcessor] (org.apache.flume.sink.LoggerSink.process:95)  - Event: { headers:{} body: 31                                              1 }
16 九月 2024 22:37:34,847 INFO  [SinkRunner-PollingRunner-DefaultSinkProcessor] (org.apache.flume.sink.LoggerSink.process:95)  - Event: { headers:{} body: 32                                              2 }
16 九月 2024 22:37:34,847 INFO  [SinkRunner-PollingRunner-DefaultSinkProcessor] (org.apache.flume.sink.LoggerSink.process:95)  - Event: { headers:{} body: 33                                              3 }
16 九月 2024 22:37:34,847 INFO  [SinkRunner-PollingRunner-DefaultSinkProcessor] (org.apache.flume.sink.LoggerSink.process:95)  - Event: { headers:{} body: 34                                              4 }
```

## 4. 示例

我们在 `flume-exec-logger-conf.properties` 配置文件配置一个名为 `a1` 的 Agent：
```
a1.sources = execSource
a1.sinks = loggerSink
a1.channels = memoryChannel

a1.sources.execSource.type = exec
a1.sources.execSource.command = tail -F /opt/data/flume/exec.log
a1.sources.execSource.restart = true
a1.sources.execSource.batchSize = 2
a1.sources.execSource.batchTimeout = 60000

a1.sinks.loggerSink.type = logger

a1.channels.memoryChannel.type = memory
a1.channels.memoryChannel.capacity = 1000
a1.channels.memoryChannel.transactionCapacity = 100

a1.sources.execSource.channels = memoryChannel
a1.sinks.loggerSink.channel = memoryChannel
```
上面配置文件定义了一个 Agent 叫做 a1，a1 有一个名为 `memoryChannel` 使用内存缓冲数据的 Channel，一个名为 `loggerSink` 把 Event 数据输出到控制台的 Sink。除此之外还有一个名为 `execSource` 的 Source，也是本文重点介绍的 Source。该 Source 执行 `tail -F /opt/data/flume/exec.log` 命令来监听 `exec.log` 文件的变化。同时设置了 batchSize 和 batchTimeout 参数，只要满足批次处理达到两个或者批次等待 60s 时间，就可以写入数据到 Channel。

有了配置文件，可以使用如下命令来加载配置文件来启动 Flume Agent a1：
```
bin/flume-ng agent --conf conf --conf-file conf/flume-exec-logger-conf.properties --name a1 -Dflume.root.logger=INFO,console
```
输入两条记录到 `exec.log` 中：
```
localhost:flume wy$ echo "1" >> exec.log
localhost:flume wy$ echo "2" >> exec.log
```
只有当输入第二条记录时(没有到达 batchTimeout 设置的时间) LoggerSink 才会输出事件到控制台：
```
localhost:flume wy$ tail -f flume.log
16 九月 2024 22:23:38,114 INFO  [main] (org.apache.flume.node.Application.startAllComponents:207)  - Starting new configuration:{ sourceRunners:{execSource=EventDrivenSourceRunner: { source:org.apache.flume.source.ExecSource{name:execSource,state:IDLE} }} sinkRunners:{loggerSink=SinkRunner: { policy:org.apache.flume.sink.DefaultSinkProcessor@598bd2ba counterGroup:{ name:null counters:{} } }} channels:{memoryChannel=org.apache.flume.channel.MemoryChannel{name: memoryChannel}} }
16 九月 2024 22:23:38,114 INFO  [main] (org.apache.flume.node.Application.startAllComponents:214)  - Starting Channel memoryChannel
16 九月 2024 22:23:38,115 INFO  [main] (org.apache.flume.node.Application.startAllComponents:229)  - Waiting for channel: memoryChannel to start. Sleeping for 500 ms
16 九月 2024 22:23:38,116 INFO  [lifecycleSupervisor-1-0] (org.apache.flume.instrumentation.MonitoredCounterGroup.register:119)  - Monitored counter group for type: CHANNEL, name: memoryChannel: Successfully registered new MBean.
16 九月 2024 22:23:38,116 INFO  [lifecycleSupervisor-1-0] (org.apache.flume.instrumentation.MonitoredCounterGroup.start:95)  - Component type: CHANNEL, name: memoryChannel started
16 九月 2024 22:23:38,621 INFO  [main] (org.apache.flume.node.Application.startAllComponents:241)  - Starting Sink loggerSink
16 九月 2024 22:23:38,622 INFO  [main] (org.apache.flume.node.Application.startAllComponents:252)  - Starting Source execSource
16 九月 2024 22:23:38,623 INFO  [lifecycleSupervisor-1-1] (org.apache.flume.source.ExecSource.start:170)  - Exec source starting with command: tail -F /opt/data/flume/exec.log
16 九月 2024 22:23:38,624 INFO  [lifecycleSupervisor-1-1] (org.apache.flume.instrumentation.MonitoredCounterGroup.register:119)  - Monitored counter group for type: SOURCE, name: execSource: Successfully registered new MBean.
16 九月 2024 22:23:38,625 INFO  [lifecycleSupervisor-1-1] (org.apache.flume.instrumentation.MonitoredCounterGroup.start:95)  - Component type: SOURCE, name: execSource started
16 九月 2024 22:24:00,653 INFO  [SinkRunner-PollingRunner-DefaultSinkProcessor] (org.apache.flume.sink.LoggerSink.process:95)  - Event: { headers:{} body: 31                                              1 }
16 九月 2024 22:24:00,653 INFO  [SinkRunner-PollingRunner-DefaultSinkProcessor] (org.apache.flume.sink.LoggerSink.process:95)  - Event: { headers:{} body: 32                                              2 }
```
