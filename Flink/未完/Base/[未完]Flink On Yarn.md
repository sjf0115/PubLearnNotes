独立（Standalone）模式由 Flink 自身提供资源，无需其他框架，这种方式降低了和其他第三方资源框架的耦合性，独立性非常强。但我们知道，Flink 是大数据计算框架，不是资源调度框架，这并不是它的强项；所以还是应该让专业的框架做专业的事，和其他资源调度框架集成更靠谱。而在目前大数据生态中，国内应用最为广泛的资源管理平台就是 YARN 了。所以接下来我们就将学习如何在 YARN 平台上集成部署 Flink。

整体来说，YARN 上部署的过程是：客户端把 Flink 应用提交给 Yarn 的 ResourceManager，Yarn 的 ResourceManager 会向 Yarn 的 NodeManager 申请容器。在这些容器上，Flink 会部署 JobManager 和 TaskManager 的实例，从而启动集群。Flink 会根据运行在 JobManger 上的作业所需要的 Slot 数量动态分配 TaskManager 资源。

## 1. 配置

在 Flink 1.8.0 之前的版本，想要以 YARN 模式部署 Flink 任务时，需要 Flink 有 Hadoop 的支持。从 Flink 1.8 版本开始，不再提供基于 Hadoop 编译的安装包，若需要 Hadoop 的环境支持，需要自行在官网下载 Hadoop 相关版本的组件，例如 flink-shaded-hadoop-2-uber-2.7.5-10.0.jar，并将该组件上传至 Flink 的 lib 目录下。在 Flink 1.11.0 版本之后，增加了很多重要新特性，其中就包括增加了对 Hadoop 3.0.0 以及更高版本 Hadoop 的支持，不再提供 `flink-shaded-hadoop-*` jar 包，而是通过配置环境变量完成与 YARN 集群的对接。

在将 Flink 任务部署至 YARN 集群之前，需要确认集群是否安装有 Hadoop，保证 Hadoop 版本至少在 2.2 以上，并且集群中安装有 HDFS 服务。具体配置步骤如下：
- 按照 3.1 节所述，下载并解压安装包，并将解压后的安装包重命名为 flink-1.13.0-yarn，
本节的相关操作都将默认在此安装路径下执行。
- 配置环境变量，增加环境变量配置如下：
```
$ sudo vim /etc/profile
HADOOP_HOME=/opt/module/hadoop-2.7.5
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export HADOOP_CONF_DIR=${HADOOP_HOME}/etc/hadoop
export HADOOP_CLASSPATH=`hadoop classpath`
```
重要说明：确保已设置 HADOOP_CLASSPATH 环境变量，可以通过运行如下命令进行检查：
```
echo $HADOOP_CLASSPATH
```

进入 conf 目录，修改 flink-conf.yaml 文件，修改以下配置，这些配置项的含义在进行 Standalone 模式配置的时候进行过讲解，若在提交命令中不特定指明，这些配置将作为默认配置：
```
$ cd /opt/module/flink-1.13.0-yarn/conf/
$ vim flink-conf.yaml
jobmanager.memory.process.size: 1600m
taskmanager.memory.process.size: 1728m
taskmanager.numberOfTaskSlots: 8
parallelism.default: 1
```

## 2. 会话模式

YARN 的会话模式与独立集群略有不同，需要首先申请一个 YARN 会话（YARN session）来启动 Flink 集群。

### 2.1 启动集群

先启动 Hadoop 集群(HDFS, YARN)，然后执行脚本命令向 YARN 集群申请资源，开启一个 YARN 会话，使用如下命令启动 Flink 集群：
```
./bin/yarn-session.sh --detached
```
可用参数解读：
- `-id,--applicationId`：连接到正在运行的 YARN 会话。
- `-j(--jar)`：Flink jar 文件的路径。
- `-d(--detached)`：分离模式，如果你不想让 Flink YARN 客户端一直前台运行，可以使用这个参数即使关掉当前对话窗口，YARN session 也可以后台运行。
- `-m(--jobmanager)`：设置为 yarn-cluster 使用 YARN 执行模式。           
- `-jm(--jobManagerMemory)`：配置 JobManager 所需内存，默认单位 MB。
- `-tm(--taskManagerMemory)`：配置每个 TaskManager 所使用内存。
- `-s(--slots)`：每个 TaskManager 的 Slot 个数。
- `-nm(--name)`：为 YARN 上的应用程序设置一个自定义名称(YARN UI 界面上显示)。
- `-qu(--queue)`：指定 YARN 队列名。
- `-D <property=value>`：为指定属性设置属性值

> 注意：Flink 1.11.0 版本不再使用 -n 参数和 -s 参数分别指定 TaskManager 数量和 slot 数量，YARN 会按照需求动态分配 TaskManager 和 slot。所以从这个意义上讲，YARN 的会话模式也不会把集群资源固定，同样是动态分配的。

YARN Session 启动之后会给出一个 web UI 地址以及一个 YARN application ID，如下所示，用户可以通过 web UI 或者命令行两种方式提交作业。

```
./bin/yarn-session.sh --detached -nm flink-yarn-test -qu test
```
运行上面的命令后如果出现如下日志表示启动集群成功：
```
2022-11-13 21:54:06,194 INFO  org.apache.flink.yarn.YarnClusterDescriptor                  [] - Found Web Interface localhost:8090 of application 'application_1668335484743_0002'.
JobManager Web Interface: http://localhost:8090
2022-11-13 21:54:06,547 INFO  org.apache.flink.yarn.cli.FlinkYarnSessionCli                [] - The Flink YARN session cluster has been started in detached mode. In order to stop Flink gracefully, use the following command:
$ echo "stop" | ./bin/yarn-session.sh -id application_1668335484743_0002
If this should not be possible, then you can also kill Flink via YARN's web interface or via:
$ yarn application -kill application_1668335484743_0002
Note that killing Flink might not clean up all job artifacts and temporary files.
```

### 2.2 提交作业

将 Standalone 模式讲解中打包好的任务运行 JAR 包上传至集群。执行以下命令将该任务提交到已经开启的 Yarn-Session 中运行。
```
./bin/flink run -c com.flink.example.stream.app.SocketWindowWordCount /Users/wy/study/code/data-example/flink-example/target/flink-example-1.0.jar --host localhost --port 9100
```
客户端可以自行确定 JobManager 的地址，也可以通过 -m 或者 `--jobmanager` 参数指定 JobManager 的地址，JobManager 的地址在 YARN Session 的启动页面中可以找到。任务提交成功后，可在 YARN 的 Web UI 界面查看运行情况。

![]()

如上图所示，从图中可以看到我们创建的 Yarn-Session 实际上是一个 Yarn 的 Application，并且有唯一的 Application ID。点击 ApplicationMaster 就可以跳转到 Flink 的 Web UI 页面，可以查看提交任务的运行情况，如下图所示：

![]()

### 2.3 停止集群

可以使用如下命令优雅地停止 Flink 集群:
```
echo "stop" | ./bin/yarn-session.sh -id application_1668335484743_0002
```
如果上述命令不起作用，那么你也可以通过 YARN 的 web 界面或者通过如下命令停止:
```
yarn -kill application_1668335484743_0002
```
需要注意的是，这样杀死 Flink 可能不会清除所有的作业工件和临时文件。

## 3. 单作业模式

在 YARN 环境中，由于有了外部平台做资源调度，所以我们也可以直接向 YARN 提交一个单独的作业，从而启动一个 Flink 集群。

```
./bin/flink run -d -t yarn-per-job -c com.flink.example.stream.app.SocketWindowWordCount /Users/wy/study/code/data-example/flink-example/target/flink-example-1.0.jar --host localhost --port 9100
```

```
2022-11-13 22:45:34,771 INFO  org.apache.flink.yarn.YarnClusterDescriptor                  [] - The Flink YARN session cluster has been started in detached mode. In order to stop Flink gracefully, use the following command:
$ echo "stop" | ./bin/yarn-session.sh -id application_1668335484743_0003
If this should not be possible, then you can also kill Flink via YARN's web interface or via:
$ yarn application -kill application_1668335484743_0003
Note that killing Flink might not clean up all job artifacts and temporary files.
2022-11-13 22:45:34,772 INFO  org.apache.flink.yarn.YarnClusterDescriptor                  [] - Found Web Interface localhost:8090 of application 'application_1668335484743_0003'.
Job has been submitted with JobID 58d69007dbbfb95361bcdb52d97d369b
```

早期版本也有另一种写法：
```
./bin/flink run -m yarn-cluster -c com.flink.example.stream.app.SocketWindowWordCount /Users/wy/study/code/data-example/flink-example/target/flink-example-1.0.jar --host localhost --port 9100
```
注意这里是通过参数-m yarn-cluster 指定向 YARN 集群提交任务

## 4. 应用模式

应用模式同样非常简单，与单作业模式类似，直接执行 flink run-application 命令即可：
```
./bin/flink run-application -t yarn-application -c com.flink.example.stream.app.SocketWindowWordCount /Users/wy/study/code/data-example/flink-example/target/flink-example-1.0.jar --host localhost --port 9100
```



参考：
- https://ci.apache.org/projects/flink/flink-docs-master/zh/docs/deployment/resource-providers/yarn/
- https://nightlies.apache.org/flink/flink-docs-master/zh/docs/deployment/overview/#deployment-modes
