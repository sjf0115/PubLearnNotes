在现代软件开发的众多环节中，容器化技术已经成为了加速开发、简化部署的关键工具。Docker 作为市场上最流行的容器平台之一，提供了一种高效的方式来打包、分发和管理应用。在这片博文中，我们将探索如何利用 Docker Compose 来部署一个 Apache Flink 集群。在开发环境中，使用 Docker Compose 部署 Flink 不仅能够保证环境的一致性，还允许开发者快速部署和撤销实例，极大地提高了开发效率。

## 1. Flink 简介

Apache Flink 是一个开源的分布式流处理框架，核心设计目标是处理无界（流式）和有界（批处理）数据。它提供高吞吐、低延迟的计算能力，并支持精确一次（Exactly-Once）状态一致性、事件时间处理、容错机制等特性，是实时数据处理的领先解决方案。核心特性如下所示:
- 统一的流批处理
  - 通过同一套 API 处理流式数据（如实时日志）和批量数据（如历史记录）。
- 事件时间语义
  - 基于事件实际发生时间处理数据，解决乱序数据计算的准确性。
- 状态管理
  - 内置强大的状态存储和容错机制（Checkpoint/Savepoint），保障故障恢复后数据一致性。
- 低延迟高吞吐
  - 毫秒级延迟下支持每秒百万级事件处理。
- 灵活的部署
  - 支持独立集群、YARN、Kubernetes、Docker 等多种部署方式。

## 2. Docker Compose 部署 Flink 集群

Docker Compose 是一个用于定义和运行多容器 Docker 应用程序的工具。通过 Compose，您可以通过一个 YAML 文件来配置您的应用的服务。然后，使用一个简单的命令，就可以创建并启动所有配置中的服务。这让组织和管理容器变成了一件轻而易举的事情。接下来，我们将一步步通过 Docker Compose 来部署一个 Flink 集群。在开始部署之前，请确保以下环境已经准备好:
- 安装 Docker: 确保 Docker 已经安装并运行在你的机器上。可以通过以下命令验证 Docker 是否安装:
   ```bash
   docker --version
   ```
- 安装 Docker Compose: 确保 Docker Compose 已经安装并配置完成。可以通过以下命令验证 Docker Compose 是否安装:
   ```bash
   docker-compose --version
   ```

### 2.1 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `flink` 的项目:
```shell
smartsi@localhost docker % mkdir flink
smartsi@localhost docker % cd flink
```

> 该目录是应用程序镜像的上下文。该目录应该只包含用于构建该镜像的资源。

### 2.2 构建 Compose 文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个`docker-compose.yml`文件。Apache Flink 支持多种集群部署模式，不同部署模式配置文件不一样。在这主要介绍在 Session 会话模式和 Application 应用模式下的配置。

Session 会话模式的配置如下所示:
```yaml
version: "2.2"
services:
  jobmanager:
    image: flink:1.20.1-scala_2.12
    networks:
      - pub-network
    restart: always
    ports:
      - "8081:8081"
    command: standalone-job --job-classname com.job.ClassName [--job-id <job id>] [--jars /path/to/artifact1,/path/to/artifact2] [--fromSavepoint /path/to/savepoint] [--allowNonRestoredState] [job arguments]
    volumes:
      - /host/path/to/job/artifacts:/opt/flink/usrlib
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        parallelism.default: 2        

  taskmanager:
    image: flink:1.20.1-scala_2.12
    networks:
      - pub-network
    restart: always
    depends_on:
      - jobmanager
    command: taskmanager
    scale: 1
    volumes:
      - /host/path/to/job/artifacts:/opt/flink/usrlib
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        taskmanager.numberOfTaskSlots: 2
        parallelism.default: 2  

volumes:
  hadoop_namenode:
  hadoop_datanode:
  hadoop_historyserver:

networks:  # 网络
  pub-network:
      external: true
```

在 Application 应用模式下，每个 Flink 应用独立启动一个集群，集群生命周期与应用绑定。以下是基于 Docker 的实现方案:
- 核心组件:
  - JobManager: 管理应用作业，随应用启动而创建
  - TaskManager: 动态分配资源，处理任务
- 特点:
  - 应用结束后自动释放资源
  - 资源隔离性强，适合生产环境

Application 应用模式的配置如下所示:
```yaml
version: "2.2"
services:
  jobmanager:
    image: flink:1.20.1-scala_2.12
    container_name: jobmanager
    networks:
      - pub-network
    restart: unless-stopped
    ports:
      - "8081:8081"
    command: jobmanager
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager        

  taskmanager:
    image: flink:1.20.1-scala_2.12
    container_name: taskmanager
    networks:
      - pub-network
    restart: unless-stopped
    depends_on:
      - jobmanager
    command: taskmanager
    scale: 2
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        taskmanager.numberOfTaskSlots: 2   

networks:  # 网络
  pub-network:
      external: true
```


#### 2.2.1 服务定义（Services）

`services` 用于定义 `Flink` 集群的各个组件，每个组件对应一个容器。上面的配置定义了2个服务:
- `jobmanager`: `Flink` 的 `JobManager` 服务，负责协调任务调度和资源管理。
- `taskmanager`: `Flink` 的 `TaskManager`，负责实际任务执行。

Docker Compose 会将每个服务部署在各自的容器中，在这里我们自定义了与服务名称一致的容器名称，因此 Docker Compose 会部署2个名为 `jobmanager` 和 `taskmanager` 的容器。

##### 2.2.1.1 jobmanager 服务

```yaml
jobmanager:
  image: flink:1.20.1-scala_2.12
  container_name: jobmanager
  networks:
    - pub-network
  restart: always
  ports:
    - "8081:8081"
  command: jobmanager
  environment:
    - |
      FLINK_PROPERTIES=
      jobmanager.rpc.address: jobmanager
```

核心配置:
- `image`: 使用官方 Flink 镜像部署 `jobmanager` 服务，明确指定 Flink 版本（1.20.1）和 Scala 版本（2.12），确保环境一致性。
- `container_name`: 容器名称固定为 `jobmanager`，便于其他服务引用。
- `networks`: 服务连接到 `pub-network` 网络上，确保容器间通信。
- `restart`: `always` 指定容器异常退出时自动重启。
- `command`:
  - `jobmanager`: 显式指定容器启动时运行 `jobmanager` 角色。
- `ports`:
  - `8081:8081`: 将容器的 8081 端口映射到宿主机，用于访问 Flink Web UI 和 REST API。
- `environment`: 通过环境变量配置 Flink 参数
  - `jobmanager.rpc.address: jobmanager`: 指定 `JobManager` 的 RPC 地址为服务名

##### 2.2.1.2 taskmanager 服务

```yaml
taskmanager:
  image: flink:1.20.1-scala_2.12
  container_name: taskmanager
  depends_on:
    - jobmanager
  command: taskmanager
  scale: 1
  environment:
    - |
      FLINK_PROPERTIES=
      jobmanager.rpc.address: jobmanager
      taskmanager.numberOfTaskSlots: 2
```

核心配置:
- `image`: 使用基于 Flink 1.20.1 版本镜像部署 `taskmanager` 服务。
- `container_name`: 容器名称固定为 `datanode`，便于其他服务引用。
- `networks`: 服务连接到 `pub-network` 网络上，确保容器间通信。
- `restart`: `always` 指定容器异常退出时自动重启。
- `volumes`: 将宿主机数据卷 `hadoop_namenode` 挂载到容器内的 `/hadoop/dfs/data`，持久化存储数据块。
- `environment`:
  - `SERVICE_PRECONDITION`: 定义服务启动前提条件，需等待 `namenode:9870` 端口可用，即 `NameNode` 完全启动后再启动 `DataNode`。
- `env_file`: 从 `hadoop.env` 文件加载环境变量（如 `CORE_CONF`、`HDFS_CONF` 等 `Hadoop` 配置）。

> 当前配置通过 `SERVICE_PRECONDITION` 环境变量实现服务等待机制（基于镜像内置的wait-for-it脚本），而非传统的 `depends_on`。这种设计的优势在于:
- 真实依赖检测: 等待端口级可用而不仅是容器启动
- 自动重试机制: 内置10秒间隔的重试逻辑
- 精确控制: 可指定多个依赖条件（如`namenode:9000` 和 `namenode:9870`）

#### 3.2.2 卷定义（Volumes）

```yaml
volumes:
  hadoop_namenode:
  hadoop_datanode:
  hadoop_historyserver:
```
声明三个 Docker 数据卷，用于持久化存储 NameNode 元数据、DataNode 数据块和 HistoryServer 历史记录。

> Docker 会自动管理这些卷的实际存储位置（默认在 /var/lib/docker/volumes/），确保容器重启后数据不丢失。

#### 3.2.3 网络定义（Networks）

```yaml
networks:  # 网络
  pub-network:
      external: true
```

核心配置:
- `pub-network`: 配置用于声明服务要连接的网络。
- `external: true`: 表示网络是在 Docker Compose 配置文件之外定义的，即它已经存在了，Docker Compose 不需要尝试创建它。

### 3.3 启动集群

在项目目录中执行 `docker-compose up -d` 命令启动 `Flink` 集群:
```bash
smartsi@smartsi hadoop wy$ docker-compose up -d
[+] Running 8/8
 ✔ Volume "hadoop_hadoop_datanode"       Created   0.0s
 ✔ Volume "hadoop_hadoop_historyserver"  Created   0.0s
 ✔ Volume "hadoop_hadoop_namenode"       Created   0.0s
 ✔ Container datanode                    Started   0.3s
 ✔ Container namenode                    Started   0.4s
 ✔ Container nodemanager                 Started   0.3s
 ✔ Container resourcemanager             Started   0.3s
 ✔ Container historyserver               Started   0.3s
```
> `-d` 表示后台运行容器。

> Docker Compose 默认使用 `{项目名}_{数据卷名}` 的格式来命名数据卷，以此避免不同项目间的数据卷名冲突。

### 3.5 查看容器状态

通过 `docker-compose ps` 命令查看所有容器的状态:
```bash
smartsi@smartsi hadoop wy$ docker-compose ps
NAME              IMAGE                                                    COMMAND                  SERVICE           CREATED              STATUS                        PORTS
datanode          bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8          "/entrypoint.sh /run…"   datanode          About a minute ago   Up About a minute (healthy)   9864/tcp
historyserver     bde2020/hadoop-historyserver:2.0.0-hadoop3.2.1-java8     "/entrypoint.sh /run…"   historyserver     About a minute ago   Up About a minute (healthy)   0.0.0.0:8188->8188/tcp
namenode          bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8          "/entrypoint.sh /run…"   namenode          About a minute ago   Up About a minute (healthy)   0.0.0.0:9000->9000/tcp, 0.0.0.0:9870->9870/tcp
nodemanager       bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8       "/entrypoint.sh /run…"   nodemanager       About a minute ago   Up About a minute (healthy)   8042/tcp
resourcemanager   bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8   "/entrypoint.sh /run…"   resourcemanager   About a minute ago   Up About a minute (healthy)   0.0.0.0:8088->8088/tcp
```
你会看到所有服务 `namenode`、`datanode`、`resourcemanager`、`nodemanager`、`historyserver` 都处于正常运行 "Up" 状态。

### 3.6 查看日志

如果需要查看某个服务的日志，可以执行以下命令:
```bash
docker-compose logs <service_name>
```
例如，查看 NameNode 的日志:
```bash
smartsi@smartsi hadoop % docker-compose logs namenode
namenode  | Configuring core
namenode  |  - Setting hadoop.proxyuser.hue.hosts=*
namenode  |  - Setting fs.defaultFS=hdfs://namenode:9000
namenode  |  - Setting hadoop.http.staticuser.user=root
namenode  |  - Setting io.compression.codecs=org.apache.hadoop.io.compress.SnappyCodec
namenode  |  - Setting hadoop.proxyuser.hue.groups=*
namenode  | Configuring hdfs
namenode  |  - Setting dfs.namenode.datanode.registration.ip-hostname-check=false
namenode  |  - Setting dfs.webhdfs.enabled=true
namenode  |  - Setting dfs.permissions.enabled=false
namenode  |  - Setting dfs.namenode.name.dir=file:///hadoop/dfs/name
namenode  | Configuring yarn
namenode  |  - Setting yarn.timeline-service.enabled=true
namenode  |  - Setting yarn.scheduler.capacity.root.default.maximum-allocation-vcores=4
namenode  |  - Setting yarn.resourcemanager.system-metrics-publisher.enabled=true
namenode  |  - Setting yarn.resourcemanager.store.class=org.apache.hadoop.yarn.server.resourcemanager.recovery.FileSystemRMStateStore
namenode  |  - Setting yarn.nodemanager.disk-health-checker.max-disk-utilization-per-disk-percentage=98.5
namenode  |  - Setting yarn.log.server.url=http://historyserver:8188/applicationhistory/logs/
namenode  |  - Setting yarn.resourcemanager.fs.state-store.uri=/rmstate
namenode  |  - Setting yarn.timeline-service.generic-application-history.enabled=true
namenode  |  - Setting yarn.log-aggregation-enable=true
...
```

## 4. 验证集群运行状态

### 4.1 Web UI 验证集群

| 服务           | 访问地址                   | 默认账号密码 |
|----------------|---------------------------|-------------|
| NameNode       | http://localhost:9870     | 无需认证    |
| ResourceManager| http://localhost:8088     | 无需认证    |
| HistoryServer  | http://localhost:8188     | 无需认证    |

检查要点:
- `Datanode` 显示1个活跃节点
- 存储容量正常显示
- 集群状态为 "active"

#### 4.1.1 访问 HDFS Web UI

`HDFS` 的 Web UI 默认运行在 `namenode` 容器的 `9870` 端口。你可以通过以下地址访问:
```
http://localhost:9870
```

在浏览器中打开该地址，你应该会看到 HDFS 的 Web 界面，如下图所示:

![HDFS Web UI](img-docker-compose-hadoop-1.png)

#### 4.1.2 访问 YARN Web UI

`YARN` 的 `ResourceManager` Web UI 默认运行在 `resourcemanager` 容器的 `8088` 端口。你可以通过以下地址访问:
```
http://localhost:8088
```

在浏览器中打开该地址，你应该会看到 ResourceManager 界面，如下图所示:

![YARN Web UI](img-docker-compose-hadoop-2.png)

#### 4.1.3 访问 HistoryServer Web UI

`YARN` 的 `HistoryServer` Web UI 默认运行在 `HistoryServer` 容器的 `8188` 端口。你可以通过以下地址访问:
```
http://localhost:8188/applicationhistory
```

在浏览器中打开该地址，你应该会看到 HistoryServer 界面，如下图所示:

![HistoryServer Web UI](img-docker-compose-hadoop-3.png)

### 4.2 使用 Hadoop 命令验证集群

执行 `docker-compose exec namenode /bin/bash` 命令进入 `NameNode` 容器来检查 HDFS、YARN 状态:
```bash
smartsi@smartsi hadoop % docker-compose exec namenode /bin/bash
root@ef3db9867111:/#
root@ef3db9867111:/#
```

#### 4.2.1 检查 HDFS 状态

执行 `hdfs dfsadmin -report` 命令检查 HDFS 状态，你会看到如下类似的 `DataNode` 状态信息:
```bash
root@ef3db9867111:/# hdfs dfsadmin -report
Configured Capacity: xxx (xxx GB)
Present Capacity: xxx (xxx GB)
DFS Remaining: xxx (xxx GB)
DFS Used: 77824 (76 KB)
DFS Used%: 0.00%
...

-------------------------------------------------
Live datanodes (1):

Name: 172.20.0.2:9866 (datanode.pub-network)
Hostname: 1aa6d471e2ae
Decommission Status : Normal
...
```

#### 4.2.2 检查 YARN 状态

执行 `yarn node -list` 命令检查 `YARN` 状态，你会看到如下类似的 `NodeManager` 状态信息:
```bash
root@ef3db9867111:/# yarn node -list
2025-02-28 04:57:59,347 INFO client.RMProxy: Connecting to ResourceManager at resourcemanager/172.20.0.5:8032
2025-02-28 04:57:59,546 INFO client.AHSProxy: Connecting to Application History server at historyserver/172.20.0.4:10200
Total Nodes:1
        Node-Id     Node-StateNode-Http-AddressNumber-of-Running-Containers
a6a82c91028f:45381        RUNNINGa6a82c91028f:8042                           0
```

### 4.3 YARN 作业测试

可以通过下面的命令提交一个示例 `MapReduce` 作业来验证:
```bash
hadoop jar /opt/hadoop-3.2.1/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.2.1.jar pi 10 100
```
如果任务成功运行，你会看到计算结果:
```bash
root@ef3db9867111:/# hadoop jar /opt/hadoop-3.2.1/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.2.1.jar pi 10 100
Number of Maps  = 10
Samples per Map = 100
...
2025-02-28 04:59:30,639 INFO impl.YarnClientImpl: Submitted application application_1740717892351_0001
2025-02-28 04:59:30,705 INFO mapreduce.Job: The url to track the job: http://resourcemanager:8088/proxy/application_1740717892351_0001/
2025-02-28 04:59:30,706 INFO mapreduce.Job: Running job: job_1740717892351_0001
2025-02-28 04:59:41,125 INFO mapreduce.Job: Job job_1740717892351_0001 running in uber mode : false
2025-02-28 04:59:41,134 INFO mapreduce.Job:  map 0% reduce 0%
2025-02-28 04:59:48,308 INFO mapreduce.Job:  map 10% reduce 0%
2025-02-28 04:59:49,320 INFO mapreduce.Job:  map 20% reduce 0%
2025-02-28 04:59:50,329 INFO mapreduce.Job:  map 30% reduce 0%
2025-02-28 04:59:53,413 INFO mapreduce.Job:  map 40% reduce 0%
2025-02-28 04:59:54,433 INFO mapreduce.Job:  map 50% reduce 0%
2025-02-28 04:59:56,557 INFO mapreduce.Job:  map 60% reduce 0%
2025-02-28 04:59:58,585 INFO mapreduce.Job:  map 70% reduce 0%
2025-02-28 05:00:00,613 INFO mapreduce.Job:  map 80% reduce 0%
2025-02-28 05:00:01,629 INFO mapreduce.Job:  map 90% reduce 0%
2025-02-28 05:00:03,650 INFO mapreduce.Job:  map 100% reduce 0%
2025-02-28 05:00:06,679 INFO mapreduce.Job:  map 100% reduce 100%
2025-02-28 05:00:08,775 INFO mapreduce.Job: Job job_1740717892351_0001 completed successfully
2025-02-28 05:00:08,903 INFO mapreduce.Job: Counters: 54
File System Counters
FILE: Number of bytes read=63
FILE: Number of bytes written=2526243
    ...
Job Counters
Launched map tasks=10
Launched reduce tasks=1
Rack-local map tasks=10
    ...
Map-Reduce Framework
Map input records=10
    ...
Shuffle Errors
BAD_ID=0
CONNECTION=0
IO_ERROR=0
WRONG_LENGTH=0
WRONG_MAP=0
WRONG_REDUCE=0
File Input Format Counters
Bytes Read=1180
File Output Format Counters
Bytes Written=97
Job Finished in 41.772 seconds
2025-02-28 05:00:08,964 INFO sasl.SaslDataTransferClient: SASL encryption trust check: localHostTrusted = false, remoteHostTrusted = false
Estimated value of Pi is 3.14800000000000000000
```
这时候再查看 HistoryServer Web UI，你会看到一个运行完成状态的作业:

![HistoryServer Web UI](img-docker-compose-hadoop-4.png)

### 4.4 数据持久化验证

通过如下几个步骤验证删除容器之后持久化的数据是否还存在:
```bash
# 停止并删除容器（保留数据卷）
docker compose down

# 重新启动集群
docker compose up -d

# 检查之前创建的数据是否仍然存在
docker exec namenode hdfs dfs -ls /
```

> 删除容器时使用 `docker-compose down -v` 会清除数据，生产环境建议绑定宿主目录代替匿名卷






## 4. Flink with Docker Compose

Docker Compose 是一种在本地运行一组 Docker 容器的方法。下一节将展示运行 Flink 的配置文件示例。

### 4.1 General

创建 docker-compose.yaml 文件。请查看以下章节中的示例:
- Application Mode
- Session Mode
- Session Mode with SQL Client

在前台启动集群（使用 `-d` 作为后台）
```
$ docker-compose up
```
将集群扩展或缩小到 N 个 taskmanager:
```
$ docker-compose scale taskmanager=<N>
```
访问 JobManager 容器
```
$ docker exec -it $(docker ps——filter name=jobmanager——format={{.ID}}) /bin/sh
```
终止集群
```
$ docker-compose down
```
访问Web界面
- 当集群运行时，可以访问web UI: http://localhost:8081。

### 4.2 Application Mode

在应用程序模式下，启动Flink集群，该集群专用于仅运行与映像捆绑在一起的Flink作业。因此，您需要为每个应用程序构建一个专用的Flink Image。详情请点击这里。另请参阅如何在命令中为JobManager服务指定JobManager参数。

`docker-compose.yml` 用于应用模式:
```yaml
version: "2.2"
services:
  jobmanager:
    image: flink:1.20.1-scala_2.12
    ports:
      - "8081:8081"
    command: standalone-job --job-classname com.job.ClassName [--job-id <job id>] [--jars /path/to/artifact1,/path/to/artifact2] [--fromSavepoint /path/to/savepoint] [--allowNonRestoredState] [job arguments]
    volumes:
      - /host/path/to/job/artifacts:/opt/flink/usrlib
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        parallelism.default: 2        

  taskmanager:
    image: flink:1.20.1-scala_2.12
    depends_on:
      - jobmanager
    command: taskmanager
    scale: 1
    volumes:
      - /host/path/to/job/artifacts:/opt/flink/usrlib
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        taskmanager.numberOfTaskSlots: 2
        parallelism.default: 2     
```
### 4.3 Session Mode

在会话模式下，您可以使用 docker-compose 启动一个长时间运行的 Flink 集群，然后向该集群提交作业。

docker-compose.yml for Session Mode:
```yaml
version: "2.2"
services:
  jobmanager:
    image: flink:1.20.1-scala_2.12
    ports:
      - "8081:8081"
    command: jobmanager
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager        

  taskmanager:
    image: flink:1.20.1-scala_2.12
    depends_on:
      - jobmanager
    command: taskmanager
    scale: 1
    environment:
      - |
        FLINK_PROPERTIES=
        jobmanager.rpc.address: jobmanager
        taskmanager.numberOfTaskSlots: 2    
```
