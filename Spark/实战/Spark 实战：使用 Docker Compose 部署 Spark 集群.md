本文将详细介绍如何使用 Docker Compose 部署 `Apache Spark`。如果你已经有在运行中的数据库或者 `ZooKeeper` 且不想启动新的服务，可以使用这个方案在沿用已有的 `PostgreSQL` 和 `ZooKeeper` 服务前提下来启动 `DolphinScheduler` 各服务。本文将从配置文件解析、部署步骤、部署后验证等方面展开，帮助您快速上手 DolphinScheduler。

## 1. Spark 简介

Apache Spark 是当前最流行的分布式计算框架，其核心优势在于内存计算和DAG执行引擎。典型集群包含以下组件：

| 组件             | 作用                          | 默认端口 |
|------------------|-----------------------------|--------|
| Master节点       | 集群资源调度和任务分配          | 7077   |
| Worker节点       | 执行具体计算任务                | 8081   |
| History Server   | 存储和展示已完成任务日志          | 18080  |
| Driver程序       | 用户应用程序的主控进程           | 4040   |


---

## 2. 部署前提

在开始部署之前，请确保满足以下条件：
- 安装 Docker：确保 Docker 已经安装并运行在你的机器上。可以通过以下命令验证 Docker 是否安装：
   ```bash
   docker --version
   ```
- 安装 Docker Compose：确保 Docker Compose 已经安装并配置完成。可以通过以下命令验证 Docker Compose 是否安装：
   ```bash
   docker-compose --version
   ```
- 网络配置：
  - `Spark` 的容器能够访问已有的 `PostgreSQL` 和 `ZooKeeper` 服务。
- 选择镜像：
  - 选择 `bitnami/spark` 镜像。中小规模 Spark 集群的理想选择，开发测试环境主推该镜像。
  - Bitnami 密切跟踪上游源的变化，并使用它们的自动化系统及时发布此镜像的新版本。最新的错误修复和特性就可以尽快获得。
  - Bitnami 容器、虚拟机和云镜像使用相同的组件和配置方法，根据项目需要在不同格式之间切换变得很容易。
  - Bitnami 所有的镜像都基于 minideb，一个基于 Debian 的极简的容器镜像，提供了一个小型的基本容器镜像。
  - Docker Hub 中可用的所有 Bitnami 镜像都使用 Notation 签名。
  - Bitnami 容器镜像会定期发布，其中包含可用的最新发行包。

| 镜像名称 | 维护方 | 主要特点 |
| :------------- | :------------- | :------------- |
| `bitnami/spark`                 | VMware/Bitnami  | 生产就绪、多架构支持  |
| `apache/spark`                  | Apache官方      | 纯净版、源码对齐  |
| `gcr.io/spark-operator/spark`   | Google Cloud    | Kubernetes原生集成 |
| `bde2020/spark`                 | BigData Europe  | Hadoop深度集成 |
| `datamechanics/spark`           | Data Mechanics  | 商业支持、性能优化 |

> Bitnami 镜像是容器生态中广受欢迎的预制解决方案，由 VMware 旗下的 Bitnami 团队维护。

## 3. 与 Hadoop 集成

为了将 `Spark` 集群与已经独立部署的 `Hadoop` 集群集成，需要确保 `Spark` 能正确访问 `Hadoop` 的 `HDFS` 和 `YARN` 服务。这就需要确保 `Spark` 和 `Hadoop` 两者在同一 Docker 网络、共享 `Hadoop` 配置。下面我们将详细讲解如何与远程 `Hadoop` 集群集成。

### 3.1 挂载 Hadoop 配置文件到 Spark 容器

`Spark` 需要 `Hadoop` 的核心配置文件（`core-site.xml`, `hdfs-site.xml`, `yarn-site.xml`）才能与远程集群通信。需要挂载到 `Spark` 的配置目录，并确保配置一致性。

第一步在本地创建配置文件目录。例如，在 Docker Compose 文件同级目录下创建 `hadoop-conf` 文件夹:
```bash
localhost:spark wy$ mkdir hadoop-conf
```
第二步从 `Hadoop` 集群复制配置文件到本地配置文件目录。在 `Hadoop` 集群的任意节点上可以找到如下配置文件（默认路径通常是 `$HADOOP_HOME/etc/hadoop/`）
- `core-site.xml`（包含 HDFS NameNode 地址）
- `hdfs-site.xml`（HDFS 详细配置）
- `yarn-site.xml`（YARN ResourceManager 地址）

你可以通过如下命令直接提取 `Hadoop` 配置文件到本地配置文件目录:
```bash
localhost:spark wy$ docker cp namenode:/etc/hadoop/core-site.xml ./hadoop-conf/
Successfully copied 7.17kB to /opt/workspace/docker/spark/hadoop-conf/
localhost:spark wy$
localhost:spark wy$ docker cp namenode:/etc/hadoop/hdfs-site.xml ./hadoop-conf/
Successfully copied 12.3kB to /opt/workspace/docker/spark/hadoop-conf/
localhost:spark wy$
localhost:spark wy$ docker cp namenode:/etc/hadoop/yarn-site.xml ./hadoop-conf/
Successfully copied 31.7kB to /opt/workspace/docker/spark/hadoop-conf/
localhost:spark wy$
```
第三步是在 Spark 的 `docker-compose.yml` 配置文件并挂载配置文件：
```yaml
volumes:
 - ./hadoop-conf:/opt/bitnami/spark/conf/hadoop  # 挂载Hadoop配置
```

### 3.2 网络集成: 打通 Spark 与 Hadoop 网络

确保 `Spark` 服务能通过容器名访问 `Hadoop` 组件，需要将 `Spark` 的服务加入 `Hadoop` 所在的网络(在这为 `pub-network`)。
```yaml
services:
  spark-master:
    networks:
      - pub-network  # 所有服务加入 Hadoop 所在的 pub-network 网络
  spark-worker:
    networks:
      - pub-network
  spark-history:
    networks:
      - pub-network

# 使用 Hadoop 的外部网络
networks:
  pub-network:
    external: true  # 引用 Hadoop 所在的 pub-network 网络
```

## 4. 配置文件

Docker Compose 简化了对整个应用程序堆栈的控制，使得在一个易于理解的 YAML 配置文件中轻松管理服务、网络和数据卷。要使用 Docker Compose 部署，首先需创建一个`docker-compose.yml`文件。在这我们的配置如下所示：
```yaml
services:
  spark-master:
    image: bitnami/spark:3.5.0
    container_name: spark-master
    hostname: spark-master
    restart: unless-stopped
    ports:
      - "7077:7077"  # 集群通信端口
      - "8080:8080"  # Web控制台
    environment:
      - SPARK_MODE=master
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    volumes:
      - spark-data:/bitnami
      - ./hadoop-conf:/opt/bitnami/spark/conf/hadoop  # 挂载Hadoop配置
    networks:
      - pub-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080"]
      interval: 30s
      timeout: 10s
      retries: 5

  spark-worker:
    image: bitnami/spark:3.5.0
    restart: unless-stopped
    depends_on:
      - spark-master
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_CORES=2
      - SPARK_WORKER_MEMORY=4G
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    deploy:
      replicas: 2
    volumes:
      - spark-data:/bitnami
      - ./hadoop-conf:/opt/bitnami/spark/conf/hadoop  # 挂载Hadoop配置
    networks:
      - pub-network

  spark-history:
    image: bitnami/spark:3.5.0
    container_name: spark-history
    restart: unless-stopped
    depends_on:
      - spark-master
    environment:
      - SPARK_MODE=history-server
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    ports:
      - "18080:18080"
    networks:
      - pub-network

volumes:
  spark-data:

networks:  # 网络
  pub-network:
      external: true
```

---

### 4.1 服务定义

`services` 是 `docker-compose.yml` 的核心部分，定义了多个容器服务。每个服务对应一个 `Spark` 组件。上面的配置定义了3个服务：
- `spark-master`：集群资源调度和任务分配。
- `spark-worker`：执行具体计算任务。
- `spark-history`：存储和展示已完成任务日志。

Docker Compose 会将每个服务部署在各自的容器中，在这里我们自定义了与服务名称一致的容器名称，因此 Docker Compose 会部署3个名为 `spark-master`、`spark-worker` 以及 `spark-history` 的容器。

#### 4.1.1 Master 服务

```yaml
spark-master:
  image: bitnami/spark:3.5.0
  container_name: spark-master
  hostname: spark-master
  restart: unless-stopped
  ports:
    - "7077:7077"  # 集群通信端口
    - "8080:8080"  # Web控制台
  environment:
    - SPARK_MODE=master
    - SPARK_RPC_AUTHENTICATION_ENABLED=no
    - SPARK_RPC_ENCRYPTION_ENABLED=no
    - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
    - SPARK_SSL_ENABLED=no
  volumes:
    - spark-data:/bitnami
    - ./hadoop-conf:/opt/bitnami/spark/conf/hadoop  # 挂载Hadoop配置
  networks:
    - pub-network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080"]
    interval: 30s
    timeout: 10s
    retries: 5
```
核心配置：
- `image`: 使用 Bitnami 维护的 `bitnami/spark` 镜像部署 `Master` 服务(对应 Apache Spark 3.5.0 版本)。
- `container_name`：容器名称固定为 `spark-master`，便于其他服务引用。
- `restart`: `unless-stopped` 指定容器异常退出时自动重启（除非手动停止）。
- `ports`: 暴露端口
  - 将容器内的 8080 端口映射到宿主机的 8080 端口，暴露 Web 控制台端口。
  - 将容器内的 7077 端口映射到宿主机的 7077 端口，用于其他服务通信。
- `environment`：设置环境变量，配置 `Master` 服务的运行参数
  - `SPARK_MODE`: 定义节点角色，指定节点模式为 `Master`。
  - `SPARK_RPC_AUTHENTICATION_ENABLED`: 关闭 RPC 身份认证(默认为 `no`，生产环境应开启)
  - `SPARK_RPC_ENCRYPTION_ENABLED`: 关闭 RPC 加密(默认为 `no`，生产环境应开启)
  - `SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED`: 关闭本地存储加密(默认为 `no`，生产环境应开启)
  - `SPARK_SSL_ENABLED`: 关闭 SSL 配置(默认为 `no`，生产环境应开启)
- `networks`：服务连接到 `pub-network` 网络上，确保容器间通信。
- `volumes`：挂载数据卷
  - `spark-data:/bitnami`: 将容器内的 `/bitnami` 数据目录挂载到 `spark-data` 数据卷，持久化存储数据。
  - `./hadoop-conf:/opt/bitnami/spark/conf/hadoop`: 挂载 Hadoop 配置文件到 Spark 容器
    - 在 Bitnami 的 Spark 镜像中，默认的 Hadoop 配置文件加载路径为 `/opt/bitnami/spark/conf/hadoop`。
    - 通过挂载本地目录 `./hadoop-conf` 到该容器路径，可以将 `Hadoop` 集群的配置文件注入到 `Spark` 容器中，确保 `Spark` 能正确识别 `Hadoop` 集群的地址、端口及其他参数。
- `healthcheck`: 定义健康检查机制
  - `test`: 通过 `curl` 检查 `Master` 服务的健康状态。
  - `interval`: 每 30 秒检查一次。
  - `timeout`: 每次检查超时时间为 10 秒。
  - `retries`: 失败重试 5 次。

> 环境变量参考[Configuration](https://github.com/bitnami/containers/tree/main/bitnami/spark#configuration)

---

#### 4.1.2 Woker 服务

```yaml
spark-worker:
  image: bitnami/spark:3.5.0
  restart: unless-stopped
  depends_on:
    - spark-master
  environment:
    - SPARK_MODE=worker
    - SPARK_MASTER_URL=spark://spark-master:7077
    - SPARK_WORKER_CORES=2
    - SPARK_WORKER_MEMORY=4g
    - SPARK_RPC_AUTHENTICATION_ENABLED=no
    - SPARK_RPC_ENCRYPTION_ENABLED=no
    - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
    - SPARK_SSL_ENABLED=no
  deploy:
    replicas: 2
  volumes:
    - spark-data:/bitnami
    - ./hadoop-conf:/opt/bitnami/spark/conf/hadoop  # 挂载Hadoop配置
  networks:
    - pub-network
```

核心配置：
- `image`: 使用 Bitnami 维护的 `bitnami/spark` 镜像部署 `Master` 服务(对应 Apache Spark 3.5.0 版本)。
- `container_name`：没有设置容器名称，便于扩展实例。
- `depends_on`: 确保 `spark-master` 服务先启动。
- `restart`: `unless-stopped` 指定容器异常退出时自动重启（除非手动停止）。
- `environment`：设置环境变量，配置 `Worker` 服务的运行参数
  - `SPARK_MODE`: 定义节点角色，指定节点模式为 `Worker`。
  - `SPARK_MASTER_URL`: 指向 `Master` 地址
  - `SPARK_WORKER_CORES`: 每个 Worker 分配的CPU核心数
  - `SPARK_WORKER_MEMORY`: 每个 Worker 分配内存大小
  - `SPARK_RPC_AUTHENTICATION_ENABLED`: 关闭 RPC 身份认证(默认为 `no`，生产环境应开启)
  - `SPARK_RPC_ENCRYPTION_ENABLED`: 关闭 RPC 加密(默认为 `no`，生产环境应开启)
  - `SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED`: 关闭本地存储加密(默认为 `no`，生产环境应开启)
  - `SPARK_SSL_ENABLED`: 关闭 SSL 配置(默认为 `no`，生产环境应开启)
- `deploy`: 启动的 Worker 实例数
- `networks`：服务连接到 `pub-network` 网络上，确保容器间通信。
- `volumes`：挂载数据卷
  - `spark-data:/bitnami`: 将容器内的 `/bitnami` 数据目录挂载到 `spark-data` 数据卷，持久化存储数据。
  - `./hadoop-conf:/opt/bitnami/spark/conf/hadoop`: 挂载 Hadoop 配置文件到 Spark 容器 `/opt/bitnami/spark/conf/hadoop` 目录下，用于访问 Hadoop 集群。

---

#### 4.1.3 HistoryServer 服务

```yaml
spark-history:
  image: bitnami/spark:3.5.0
  container_name: spark-history
  restart: unless-stopped
  depends_on:
    - spark-master
  environment:
    - SPARK_MODE=history
    - SPARK_RPC_AUTHENTICATION_ENABLED=no
    - SPARK_RPC_ENCRYPTION_ENABLED=no
    - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
    - SPARK_SSL_ENABLED=no
  ports:
    - "18080:18080"
  networks:
    - pub-network
```

核心配置：
- `image`: 使用 Bitnami 维护的 `bitnami/spark` 镜像部署 `Master` 服务(对应 Apache Spark 3.5.0 版本)。
- `container_name`：容器名称固定为 `spark-history`，便于其他服务引用。
- `restart`: `unless-stopped` 指定容器异常退出时自动重启（除非手动停止）。
- `depends_on`: 确保 `spark-master` 服务先启动。
- `ports`: 暴露端口
  - 将容器内的 18080 端口映射到宿主机的 18080 端口，用于提供历史任务查询。
- `environment`：设置环境变量，配置 `HistoryServer` 服务的运行参数
  - `SPARK_MODE`: 定义节点角色，指定节点模式为 `history-server`。
  - `SPARK_RPC_AUTHENTICATION_ENABLED`: 关闭 RPC 身份认证(默认为 `no`，生产环境应开启)
  - `SPARK_RPC_ENCRYPTION_ENABLED`: 关闭 RPC 加密(默认为 `no`，生产环境应开启)
  - `SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED`: 关闭本地存储加密(默认为 `no`，生产环境应开启)
  - `SPARK_SSL_ENABLED`: 关闭 SSL 配置(默认为 `no`，生产环境应开启)
- `networks`：服务连接到 `pub-network` 网络上，确保容器间通信。

---

### 4.2 卷定义（Volumes）

```yaml
volumes:
  spark-data:
```

声明1个 Docker 数据卷，用于持久化存储 Spark 数据。

> Docker 会自动管理这些卷的实际存储位置（默认在 /var/lib/docker/volumes/），确保容器重启后数据不丢失。

---

### 4.3 网络定义（Networks）

```yaml
networks:  # 网络
  pub-network:
      external: true
```

核心配置：
- `pub-network`：配置用于声明服务要连接的网络。使用外部网络 `pub-network`，确保所有服务在同一网络中，能够互相通信。
- `external: true`：表示网络是在 Docker Compose 配置文件之外定义的，即它已经存在了，Docker Compose 不需要尝试创建它。

## 5. 部署

### 5.1 准备工作

- 确保 `Hadoop` 相关服务已启动。
- 创建外部网络 `pub-network`（如果尚未创建），确保与 `Hadoop` 服务在同一个网络中：
  ```bash
  docker network create pub-network
  ```

### 5.2 创建项目目录

首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `spark` 的项目：
```shell
localhost:docker wy$ mkdir spark
localhost:docker wy$ cd spark
```

### 5.3 启动 Spark

在 `docker-compose.yml` 文件所在目录下运行以下命令：
```bash

```

默认情况下，当您部署 docker-compose 文件时，您将得到一个包含1个主节点和1个工作节点的 Apache Spark 集群。



如果你想要N个worker，你所需要做的就是用下面的命令启动docker-compose部署：


### 4.4 查看服务状态

通过 `docker-compose ps` 命令查看所有容器的状态：
```bash

```

# 动态增加Worker节点
docker-compose scale spark-worker=3

---


## 5. 验证

### 5.1 Web UI

不管你是用那种方式启动的服务，只要服务启动后，你都可以通过 `http://localhost:12345/dolphinscheduler/ui` 访问 `DolphinScheduler`。访问上述链接后会跳转到登陆页面，`DolphinScheduler` 默认的用户和密码分别为 `admin` 和 `dolphinscheduler123`。

![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/ed9d9eb99bfb441c9ba3b38c9046cda8.png#pic_center)
### 5.2 验证任务调度

创建一个简单的工作流任务（如 Shell 脚本），并验证任务是否能正常调度和执行。


### 6.1 基础状态检查
```bash
# 检查容器运行状态
docker-compose ps -a

# 预期输出：
NAME                COMMAND                  STATUS   PORTS
spark-master   "/opt/bitnami/script..."   Up       0.0.0.0:4040->4040/tcp,...
spark-worker_1 "/opt/bitnami/script..."   Up       8081/tcp
```

### 6.2 Web控制台验证
访问 `http://localhost:8080` 应该看到：
- **Alive Workers** 显示正确的节点数
- 每个Worker的**Memory**和**Cores**与配置一致

![Spark Master WebUI](https://i.stack.imgur.com/6f8xT.png)

### 6.3 提交测试任务
```bash
# 进入Master容器
docker exec -it spark-master bash

# 运行计算Pi的示例
/opt/bitnami/spark/bin/spark-submit \
    --master spark://spark-master:7077 \
    --class org.apache.spark.examples.SparkPi \
    /opt/bitnami/spark/examples/jars/spark-examples_2.12-3.5.0.jar \
    1000

# 查看输出中的结果
Pi is roughly 3.14159
```

### 6.4 历史服务器验证
```bash
# 查看历史日志
docker exec spark-master ls /bitnami/spark/eventlogs

# 访问历史界面
http://localhost:18080
```
