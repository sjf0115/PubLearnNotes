
## 1. 环境准备

Flink 是一个以 Java 及 Scala 作为开发语言的开源大数据项目，代码开源在 GitHub 上，并使用 Maven 来编译和构建项目。对于大部分使用 Flink 的同学来说，Java、Maven 和 Git 这三个工具是必不可少的，另外一个强大的 IDE 有助于我们更快的阅读代码、开发新功能以及修复 Bug。因为篇幅所限，我们不会详述每个工具的安装细节，但会给出必要的安装建议。

关于开发测试环境，Mac OS、Linux 系统或者 Windows 都可以。如果使用的是 Windows 10 系统，建议使用 Windows 10 系统的 Linux 子系统来编译和运行。

| 工具     | 说明     |
| :------------- | :------------- |
| Java       | Java 版本至少是Java 8，且最好选用 Java 8u51 及以上版本       |
| Maven      | 必须使用 Maven 3，建议使用 Maven 3.2.5。Maven 3.3.x 能够编译成功，但是在 Shade 一些 Dependencies 的过程中有些问题 |
| Git        | Flink 的代码仓库是： https://github.com/apache/flink |

建议选用社区已发布的稳定分支。

### 1.1 编译 Flink 代码

在我们配置好之前的几个工具后，编译 Flink 就非常简单了，执行如下命令即可：
```
mvn clean install -DskipTests
# 或者
mvn clean package -DskipTests
```
常用编译参数：
- -Dfast：主要是忽略 QA plugins 和 JavaDocs 的编译
- -Dhadoop.version=2.6.1：指定 hadoop 版本
- --settings=${maven_file_path}：显式指定 maven settings.xml 配置文件

当成功编译完成后就能在当前 Flink 代码目录下的 flink-dist/target/ 子目录中看到编译后的文件。

### 1.2 开发环境准备

推荐使用 IntelliJ IDEA IDE 作为 Flink 的 IDE 工具。官方不建议使用 Eclipse IDE，主要原因是 Eclipse 的 Scala IDE 和 Flink 用 Scala 的不兼容。

如果你需要做一些 Flink 代码的开发工作，则需要根据 Flink 代码的 tools/maven/目录下的配置文件来配置 Checkstyle ，因为 Flink 在编译时会强制代码风格的检查，如果代码风格不符合规范，可能会直接编译失败。  

### 1.3 运行环境准备

- 准备 Flink binary
  - 直接从 Flink 官网上下载 Flink binary 的压缩包
  - 或者从 Flink 源码编译而来
- 安装 Java，并配置 JAVA_HOME 环境变量

## 2. 部署

### 2.1 单机 Standalone 模式

#### 2.1.1 基本的启动流程

最简单的运行 Flink 应用的方法就是以单机 Standalone 的方式运行。使用如下命令启动集群：
```
./bin/start-cluster.sh
```
打开 `http://127.0.0.1:8081/` 就能看到 Flink 的 Web 界面。尝试提交 Word Count 任务：
```
./bin/flink run examples/streaming/WordCount.jar
```
大家可以自行探索 Web 界面中展示的信息，比如，我们可以看看 TaskManager 的 stdout 日志，就可以看到 Word Count 的计算结果。

我们还可以尝试通过 '–input' 参数指定我们自己的本地文件作为输入，然后执行：
```
./bin/flink run examples/streaming/WordCount.jar --input ${your_source_file}
```

使用如下命令停止集群：
```
./bin/stop-cluster.sh
```

#### 2.1.2 常用配置介绍

(1) conf/slaves

conf/slaves 用于配置 TaskManager 的部署，默认配置下只会启动一个 TaskManager 进程，如果想增加一个 TaskManager 进程，只需要在文件中追加一行 'localhost'。也可以直接通过 './bin/taskmanager.sh start' 这个命令来追加一个新的 TaskManager：
```
./bin/taskmanager.sh start|start-foreground|stop|stop-all
```
(2) conf/flink-conf.yaml

conf/flink-conf.yaml 用于配置 JM 和 TM 的运行参数，常用配置有：
```
# The heap size for the JobManager JVM
jobmanager.heap.mb: 1024

# The heap size for the TaskManager JVM
taskmanager.heap.mb: 1024

# The number of task slots that each TaskManager offers. Each slot runs one parallel pipeline.
taskmanager.numberOfTaskSlots: 4
```
Standalone 集群启动后，我们可以尝试分析一下 Flink 相关进程的运行情况。执行 jps 命令，可以看到 Flink 相关的进程主要有两个，一个是 JobManager 进程，另一个是 TaskManager 进程。我们可以进一步用 ps 命令看看进程的启动参数中'-Xmx'和'-Xms'的配置。然后我们可以尝试修改 flink-conf.yaml 中若干配置，然后重启 Standalone 集群看看发生了什么变化。

#### 2.1.3 日志的查看和配置

JobManager 和 TaskManager 的启动日志可以在 Flink binary 目录下的 Log 子目录中找到。Log 目录中以 'flink-user−standalonesession−{id}-${hostname}' 为前缀的文件对应的是 JobManager 的输出，其中有三个文件：
- `flink-${user}-standalonesession-${id}-${hostname}.log`：代码中的日志输出
- `flink-${user}-standalonesession-${id}-${hostname}.out`：进程执行时的 stdout 输出
- `flink-${user}-standalonesession-${id}-${hostname}-gc.log`：JVM的GC的日志

Log 目录中以 'flink-user−taskexecutor−{id}-${hostname}' 为前缀的文件对应的是 TaskManager 的输出，也包括三个文件，和 JobManager 的输出一致。

日志的配置文件在 Flink binary 目录的 conf 子目录下，其中：
- log4j-cli.properties：用 Flink 命令行时用的 log 配置，比如执行 'flink run' 命令
- log4j-yarn-session.properties：用 yarn-session.sh 启动时命令行执行时用的 log 配置
- log4j.properties：无论是 Standalone 还是 Yarn 模式，JobManager 和 TaskManager 上用的 log 配置都是 log4j.properties

这三个 `log4j.*properties` 文件分别有三个 `logback.*xml` 文件与之对应，如果想使用 Logback 的同学，只需要把与之对应的 `log4j.*properties` 文件删掉即可，对应关系如下：
- log4j-cli.properties -> logback-console.xml
- log4j-yarn-session.properties -> logback-yarn.xml
- log4j.properties -> logback.xml

需要注意的是，'flink-{id}-和{user}-taskexecutor-{hostname}' 都带有 'id'，'{id}' 表示本进程在本机上该角色（JobManager 或 TaskManager）的所有进程中的启动顺序，默认从 0 开始。

### 2.2 多机 Standalone 模式

部署前要注意的要点：
- 每台机器上配置好 Java 以及 JAVA_HOME 环境变量
- 每台机器上部署的 Flink binary 的目录要保证是同一个目录
- 如果需要用 HDFS，需要配置 HADOOP_CONF_DIR 环境变量配置

根据你的集群信息修改 conf/masters 和 conf/slaves 配置。修改 conf/flink-conf.yaml 配置，注意要确保和 Masters 文件中的地址一致：
```
jobmanager.rpc.address: xxx
```
确保所有机器的 Flink binary 目录中 conf 中的配置文件相同，特别是以下三个：
```
conf/masters
conf/slaves
conf/flink-conf.yaml
```
然后启动 Flink 集群：
```
./bin/start-cluster.sh
```

### 2.3 Standalone 高可用 HA 模式

通过如下 Flink Runtime 架构图，我们可以看到 JobManager 是整个系统中最可能导致系统不可用的角色。如果一个 TaskManager 挂了，在资源足够的情况下，只需要把相关 Task 调度到其他空闲 TaskSlot 上，然后 Job 从 Checkpoint 中恢复即可。而如果当前集群中只配置了一个 JobManager，则一旦 JobManager 挂了，就必须等待这个 JobManager 重新恢复，如果恢复时间过长，就可能导致整个 Job 失败。

![](1)

因此如果在生产业务使用 Standalone 模式，则需要部署配置 HighAvailability，这样同时可以有多个 JobManager 待命，从而使得 JobManager 能够持续服务。

需要注意的是，如果想使用 Flink Standalone HA 模式，需要确保基于 Flink Release-1.6.1 及以上版本，因为这里社区有个 bug 会导致这个模式下主 JobManager 不能正常工作。

#### 2.3.1 使用 Flink 自带的脚本部署 Zookeeper

Flink 目前支持基于 Zookeeper 的 HA。如果你的集群中没有部署 ZK，Flink 提供了启动 Zookeeper 集群的脚本。首先修改配置文件 'conf/zoo.cfg'，根据你要部署的 Zookeeper Server 的机器数来配置 'server.X=addressX:peerPort:leaderPort'，其中 'X' 是一个 Zookeeper Server 的唯一 ID，且必须是数字。
```
# The port at which the clients will connect
clientPort=3181

server.1=z05f06378.sqa.zth.tbsite.net:4888:5888
server.2=z05c19426.sqa.zth.tbsite.net:4888:5888
server.3=z05f10219.sqa.zth.tbsite.net:4888:5888
```
然后启动 Zookeeper：
```
./bin/start-zookeeper-quorum.sh
```
如果要停掉 Zookeeper 集群，需要使用如下命令：
```
./bin/stop-zookeeper-quorum.sh
```

#### 2.3.2 修改 Flink Standalone 集群的配置

修改 conf/masters 文件，增加一个 JobManager：
```
$cat conf/masters
z05f06378.sqa.zth.tbsite.net:8081
z05c19426.sqa.zth.tbsite.net:8081
```
之前修改过的 conf/slaves 文件保持不变：
```
$cat conf/slaves
z05f06378.sqa.zth.tbsite.net
z05c19426.sqa.zth.tbsite.net
z05f10219.sqa.zth.tbsite.net
```
修改 conf/flink-conf.yaml 文件：
```
# 配置 high-availability mode
high-availability: zookeeper

# 配置 zookeeper quorum（hostname 和端口需要依据对应 zk 的实际配置）
high-availability.zookeeper.quorum: z05f02321.sqa.zth.tbsite.net:2181,z05f10215.sqa.zth.tbsite.net:2181

# （可选）设置 zookeeper 的 root 目录
high-availability.zookeeper.path.root: /test_dir/test_standalone2_root

# （可选）相当于是这个 standalone 集群中创建的 zk node 的 namespace
high-availability.cluster-id: /test_dir/test_standalone2

# JobManager 的 meta 信息放在 dfs，在 zk 上主要会保存一个指向 dfs 路径的指针
high-availability.storageDir: hdfs:///test_dir/recovery2/
```
需要注意的是，在 HA 模式下 conf/flink-conf.yaml 中的这两个配置都失效了（想想为什么）:
```
jobmanager.rpc.address
jobmanager.rpc.port
```
修改完成后，确保配置同步到其他机器。

使用如下命令启动 Zookeeper 集群：
```
./bin/start-zookeeper-quorum.sh
```
再启动 Standalone 集群（要确保之前的 Standalone 集群已经停掉）：
```
./bin/start-cluster.sh
```

分别打开两个 Master 节点上的 JobManager Web 页面：
- http://z05f06378.sqa.zth.tbsite.net:8081
- http://z05c19426.sqa.zth.tbsite.net:8081

可以看到两个页面最后都转到了同一个地址上，这个地址就是当前主 JobManager 所在机器，另一个就是 Standby JobManager。以上我们就完成了 Standalone 模式下 HA 的配置。

接下来我们可以测试验证 HA 的有效性。当我们知道主 JobManager 的机器后，我们可以把主 JobManager 进程 Kill 掉，比如当前主 JobManager 在 z05c19426.sqa.zth.tbsite.net 这个机器上，就把这个进程杀掉。接着，再打开这两个链接：
- http://z05f06378.sqa.zth.tbsite.net:8081
- http://z05c19426.sqa.zth.tbsite.net:8081

可以发现后一个链接已经不能展示了，而前一个链接可以展示，说明发生主备切换。然后我们再重启前一次的主 JobManager：
```
./bin/jobmanager.sh start z05c19426.sqa.zth.tbsite.net 8081
```
再打开 （http://z05c19426.sqa.zth.tbsite.net:8081） 这个链接，会发现现在这个链接可以转到 （http://z05f06378.sqa.zth.tbsite.net:8081） 这个页面上了。说明这个 JobManager 完成了一个 Failover Recovery。

### 2.4 Yarn 模式

相对于 Standalone 模式，Yarn 模式允许 Flink job 的好处有：
- 资源按需使用，提高集群的资源利用率
- 任务有优先级，根据优先级运行作业
- 基于 Yarn 调度系统，能够自动化地处理各个角色的 Failover
- JobManager 进程和 TaskManager 进程都由 Yarn NodeManager 监控
- 如果 JobManager 进程异常退出，则 Yarn ResourceManager 会重新调度 JobManager 到其他机器
- 如果 TaskManager 进程异常退出，JobManager 会收到消息并重新向 Yarn ResourceManager 申请资源，重新启动 TaskManager

#### 2.4.1 Session Cluster 模式

使用如下命令使用 Session Cluster 模式创建一个 Yarn 模式的 Flink 集群：
```
./bin/yarn-session.sh -n 4 -jm 1024m -tm 4096m
```
其中用到的参数是：
- -n,–container Number of TaskManagers
- -jm,–jobManagerMemory Memory for JobManager Container with optional unit (default: MB)
- -tm,–taskManagerMemory Memory per TaskManager Container with optional unit (default: MB)
- -qu,–queue Specify YARN queue.
- -s,–slots Number of slots per TaskManager
- -t,–ship Ship files in the specified directory (t for transfer)

提交一个 Flink job 到 Flink 集群：
```
./bin/flink run examples/streaming/WordCount.jar --input hdfs:///test_dir/input_dir/story --output hdfs:///test_dir/output_dir/output
```
这次提交 Flink job，虽然没有指定对应 Yarn application 的信息，却可以提交到对应的 Flink 集群，原因在于 '/tmp/.yarn-properties-${user}' 文件中保存了上一次创建 Yarn session 的集群信息。所以如果同一用户在同一机器上再次创建一个 Yarn session，则这个文件会被覆盖掉。
- 如果删掉 '/tmp/.yarn-properties-${user}' 或者在另一个机器上提交作业能否提交到预期到 yarn session 中呢？可以配置了 'high-availability.cluster-id' 参数，据此从 Zookeeper 上获取到 JobManager 的地址和端口，从而提交作业。
- 如果 Yarn session 没有配置 HA，又该如何提交呢？

这个时候就必须要在提交 Flink job 的命令中指明 Yarn 上的 Application ID，通过 '-yid' 参数传入：
```
/bin/flink run -yid application_1548056325049_0048 examples/streaming/WordCount.jar --input hdfs:///test_dir/input_dir/story --output hdfs:///test_dir/output_dir/output
```
我们可以发现，每次跑完任务不久，TaskManager 就被释放了，下次在提交任务的时候，TaskManager 又会重新拉起来。如果希望延长空闲 TaskManager 的超时时间，可以在 conf/flink-conf.yaml 文件中配置下面这个参数，单位是 milliseconds：
```
slotmanager.taskmanager-timeout: 30000L         # deprecated, used in release-1.5
resourcemanager.taskmanager-timeout: 30000L
```


#### 2.4.2

如果你只想运行单个 Flink Job 后就退出，那么可以用下面这个命令：
```
./bin/flink run -m yarn-cluster -yn 2 examples/streaming/WordCount.jar --input hdfs:///test_dir/input_dir/story --output hdfs:///test_dir/output_dir/output
```
常用的配置有：
- -yn,–yarncontainer Number of Task Managers
- -yqu,–yarnqueue Specify YARN queue.
- -ys,–yarnslots Number of slots per TaskManager
- -yqu,–yarnqueue Specify YARN queue.

可以通过 Help 命令查看 Run 的可用参数：
```
./bin/flink run -h
```
我们可以看到，“./bin/flink run -h”看到的“Options for yarn-cluster mode”中的“-y”和“–yarn”为前缀的参数其实和“./bin/yarn-session.sh -h”命令是一一对应的，语义上也基本一致。
关于“-n”（在 yarn session 模式下）、“-yn”在（yarn single job 模式下）与“-p”参数的关系：
- “-n”和“-yn”在社区版本中（Release-1.5 ～ Release-1.7）中没有实际的控制作用，实际的资源是根据“-p”参数来申请的，并且 TM 使用完后就会归还
- 在 Blink 的开源版本中，“-n”（在 Yarn Session 模式下）的作用就是一开始启动指定数量的 TaskManager，之后即使 Job 需要更多的 Slot，也不会申请新的 TaskManager
- 在 Blink 的开源版本中，Yarn single job 模式“-yn”表示的是初始 TaskManager 的数量，不设置 TaskManager 的上限。（需要特别注意的是，只有加上“-yd”参数才能用 Single job 模式（例如：命令“./bin/flink run -yd -m yarn-cluster xxx”）

### 2.5 Yarn 高可用 HA 模式

首先要确保启动 Yarn 集群用的 yarn-site.xml 文件中的这个配置，这个是 Yarn 集群级别 AM 重启的上限:
```
<property>
  <name>yarn.resourcemanager.am.max-attempts</name>
  <value>100</value>
</property>
```



原文:[Apache Flink 零基础入门（三）：开发环境搭建和应用的配置、部署及运行](https://flink-learning.org.cn/article/detail/ab60ac021e7de0c036ce1e9b01416c68)
