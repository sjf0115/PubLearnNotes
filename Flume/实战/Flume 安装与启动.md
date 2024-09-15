
## 1. 安装

### 1.1 下载

从 [下载页](https://flume.apache.org/download.html) 下载最新版本的 Flume，当前最新版本为 1.11.0：

![](img-flume-setup-1.png)

下载之后解压缩到工作目录 `/opt` 下：
```shell
tar -zxvf apache-flume-1.11.0-bin.tar.gz -C /opt/
```
创建软连接，便于升级：
```shell
ln -s apache-flume-1.11.0-bin/ flume
```

### 1.2 配置

在 `/etc/profile` 配置文件中添加如下配置，将 Flume 安装目录配置到 PATH 中：
```shell
# Flume
export FLUME_HOME=/opt/flume
export PATH=${FLUME_HOME}/bin:$PATH
```
执行如下命令使环境变量立即生效：
```shell
source /etc/profile
```

Flume 使用需要依赖 JDK 1.8 以上版本，确保已安装。首先创建 `flume-env.sh` 文件：
```shell
cp flume-env.sh.template flume-env.sh
```
在 `flume-env.sh` 文件中添加如下配置：
```shell
# Enviroment variables can be set here.
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk1.8.0_161.jdk/Contents/Home
export JAVA_OPTS="-Dflume.root.logger=INFO,console"
```
### 1.3 验证安装是否成功

执行 `flume-ng version` 命令，出现下面信息，表示安装成功了：
```
localhost:bin wy$ flume-ng version
Flume 1.11.0
Source code repository: https://git.apache.org/repos/asf/flume.git
Revision: 1a15927e594fd0d05a59d804b90a9c31ec93f5e1
Compiled by rgoers on Sun Oct 16 14:44:15 MST 2022
From source with checksum bbbca682177262aac3a89defde369a37
```

## 2. 配置 Agent

Flume Agent 的配置是在一个本地的配置文件中，需要在 `conf` 目录创建。这是一个遵循 Java properties 文件格式的文本文件。一个或多个 Agent 配置可放在同一个配置文件里。配置文件包含 Agent的 Source，Sink 和 Channel 的各个属性以及他们的数据流连接。每个组件（Source，Sink 或者 Channel）都有一个 name，type 以及一系列的基于其 type 或实例的属性。

在这我们配置一个 Agent，Source 使用的是 NetCat TCP Source，简单说就是监听本机上某个端口上接收 TCP 协议的消息。收到的每行内容都会解析封装成一个事件 Event，然后发送到 Channel，在这使用的是 Memory Channel，是一个用内存作为 Event 缓冲的 Channel。Sink 使用的是 Logger Sink，这个 Sink 可以把 Event 输出到控制台。首先需要在 `conf` 目录下创建一个配置文件，在这为 `flume-netcat-logger-conf.properties`，详细配置如下所示：
```
a1.sources = r1
a1.sinks = k1
a1.channels = c1

a1.sources.r1.type = netcat
a1.sources.r1.bind = localhost
a1.sources.r1.port = 44444

a1.sinks.k1.type = logger

a1.channels.c1.type = memory
a1.channels.c1.capacity = 1000
a1.channels.c1.transactionCapacity = 100

a1.sources.r1.channels = c1
a1.sinks.k1.channel = c1
```
这个配置文件定义了一个 Agent 叫做 a1，a1 有一个 Source 监听本机 44444 端口上接收到的数据、一个缓冲数据的 channel 还有一个把 Event 数据输出到控制台的 Sink。这个配置文件给各个组件命名，并且设置了它们的类型和其他属性。下面会详细介绍每个组件的配置。

### 2.1 配置 Agent

在这配置文件中只定义了一个为 `a1` 的 Flume Agent。为 Agent a1 配置了一个名为 `r1` 的 Source，一个名为 `k1` 的 Sink 以及一个名为 `c1` 的 Channel 组件：
```
# 配置 Agent a1 各个组件的名称
a1.sources = r1    # Agent a1 的一个 Source：r1
a1.sinks = k1      # Agent a1 的一个 Sink：k1
a1.channels = c1   # Agent a1 的一个 Channel：c1
```

### 2.2 配置 Source

在这为 Agent a1 配置一个名为 `r1` 的 NetCat TCP Source 来监听本机 44444 端口上接收到的数据：
```
# 配置 Agent a1 的 Source r1 的属性
a1.sources.r1.type = netcat       # 使用的是 NetCat TCP Source
a1.sources.r1.bind = localhost    # NetCat TCP Source 监听的 hostname，这个是本机
a1.sources.r1.port = 44444        # 监听的端口
```
Source 的 type 属性指定为 `netcat`，这里配的是别名，Flume 内置的一些组件都是有别名的，没有别名填全限定类名。Source 监听的的是本机，bind 属性指定为 `localhost`。监听的端口号 port 设置为 `44444`。

NetCat TCP Source 指定的属性：

| 属性名 | 说明 |
| :------------- | :------------- |
| type  | 需要指定为 `netcat`  |
| bind  | 绑定的主机名或者IP地址  |
| port  | 绑定的端口号  |


### 2.3 配置 Sink

在这为 Agent a1 配置一个名为 `k1` 的 Logger Sink 来将 Event 数据输出到控制台：
```
# 配置 Agent a1 的 Sink k1 的属性
a1.sinks.k1.type = logger         # Sink 使用的是 Logger Sink，这个配的也是别名
```

Logger Sink 指定的属性：

| 属性名 | 说明 |
| :------------- | :------------- |
| type  | 需要指定为 `logger`  |


### 2.4 配置 Channel

在这为 Agent a1 配置一个名为 `c1` 的 Memory Channel 来缓存从 Source 读取但并未 Sink 消费的事件。
```
# 配置 Agent a1 的 Channel c1的属性，channel 是用来缓冲 Event 数据的
a1.channels.c1.type = memory                #channel的类型是内存channel，顾名思义这个channel是使用内存来缓冲数据
a1.channels.c1.capacity = 1000              #内存channel的容量大小是1000，注意这个容量不是越大越好，配置越大一旦Flume挂掉丢失的event也就越多
a1.channels.c1.transactionCapacity = 100    #source和sink从内存channel每次事务传输的event数量
```
Memory Channel 指定 capacity 为 1000，即 Memory Channel 的容量大小为 1000，此外还指定了 transactionCapacity 为 100，即 Source 和 Sink 每次事务从 Channel 传输的 100 个事件。

Memory Channel 指定的属性：

| 属性名 | 默认值 | 说明 |
| :------------- | :------------- | :------------- |
| type  | - | Channel 类型，需要指定为 `memory`  |
| capacity | 100 | 内存中存储 Event 的最大数 |
| transactionCapacity | 100 | source 或者 sink 每个事务中存取 Event 的操作数量（不能比 capacity 大） |


### 2.5 配置连接关系

Agent 需要知道加载什么组件，以及这些组件在流中的连接顺序。通过列出在 Agent 中的 Source，Sink 和 Channel名称，定义每个 Sink 和 Source 的 Channel 来完成。在这从 Source r1 中读取事件写入到 Channel c1 中，然后 Sink k1 从这个 Channel 中读取事件：
```
# 把 Source 和 Sink 绑定到 Channel 上
a1.sources.r1.channels = c1       # Source r1 与 Channel c1 绑定
a1.sinks.k1.channel = c1          # Sink k1 与 Channel c1 绑定
```

## 3. 启动 Agent

通常一个配置文件里面可能有多个 Agent(在这只有一个名为 `a1` 的 Agent)，当启动 Flume 时候通常会传一个 Agent 名字来做为程序运行的标记。例如使用如下命令来加载上面的配置文件来启动 Flume Agent a1：
```
bin/flume-ng agent --conf conf --conf-file conf/flume-netcat-logger-conf.properties --name a1 -Dflume.root.logger=INFO,console
```
> 同一个配置文件中如果配置了多个 Agent 流，启动 Flume 的命令中 --name 这个参数的作用就体现出来了，用它来告诉 Flume 将要启动该配置文件中的哪一个 Agent 实例。

请注意，在完整的部署中通常会包含 `–conf=<conf-dir>` 这个参数，`<conf-dir>` 目录里面包含了 flume-env.sh 和一个 log4j properties 文件。

测试一下我们的这个例子吧，打开一个新的终端窗口，用 telnet 命令连接本机的 44444 端口，然后输入 Hello 后按回车，这时收到服务器的响应[OK]（这是 NetCat TCP Source 默认给返回的），说明一行数据已经成功发送：
```
localhost:conf wy$ telnet 127.0.0.1 44444
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
hello
OK
```
Flume的终端里面会以 log 的形式输出这个收到的 Event 内容：
```
16 九月 2024 00:05:05,838 INFO  [SinkRunner-PollingRunner-DefaultSinkProcessor] (org.apache.flume.sink.LoggerSink.process:95)  - Event: { headers:{} body: 68 65 6C 6C 6F 0D                               hello. }
```
到此你已经成功配置并运行了一个 Flume Agent。


...
