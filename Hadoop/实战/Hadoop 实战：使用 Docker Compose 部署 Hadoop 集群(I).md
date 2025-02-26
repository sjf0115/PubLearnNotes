





### **一、为什么选择 Docker 和 `bde2020` 镜像？**

#### **1. 为何用 Docker Compose？**
- **环境一致性**：消除“在我机器上能用”问题，确保开发、测试、生产环境一致。
- **快速重置**：通过 `docker-compose down && docker-compose up` 快速重建集群。
- **资源隔离**：每个服务（如 NameNode、Hive Metastore）运行在独立容器中，互不干扰。

#### **2. 为何选择 `bde2020` 镜像而非 Apache 官方镜像？**

| **优势**                | **`bde2020` 镜像**                          | **Apache 官方镜像**              |
|-------------------------|---------------------------------------------|----------------------------------|
| **预配置优化**          | 内置 Hadoop 配置文件，通过环境变量动态调整  | 需手动编辑 XML                   |
| **模块化设计**          | 各组件（NameNode/DataNode）独立镜像，按需扩展 | 单一镜像包含全部组件，需手动管理 |
| **健康检查机制**        | 支持 `SERVICE_PRECONDITION` 等待依赖服务    | 无内置依赖管理                   |
| **社区支持**            | 高频维护，下载量超百万                     | 依赖社区贡献，更新滞后           |

---

## 2. 架构设计

#### **1. 组件清单**

- **Hadoop 集群**:
  - **HDFS**: NameNode (元数据管理) + DataNode (数据存储)
  - **YARN**: ResourceManager (资源调度) + NodeManager (节点管理)
- **Hive 服务**:
  - **Hive Metastore**: 元数据存储（依赖 MySQL）
  - **HiveServer2**: 提供 JDBC 接口执行 SQL
- **MySQL**: 存储 Hive 元数据，替代默认的 Derby（更适合生产）。





```yaml
services:
# ------------------ Hadoop 集群 ------------------
  namenode:
    image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
    container_name: namenode
    volumes:
      - hadoop_dfs_name:/hadoop/dfs/name
      #- ./conf/hadoop:/etc/hadoop
    environment:
      - CLUSTER_NAME=hadoop-cluster
      - CORE_CONF_fs_defaultFS=hdfs://namenode:9000
    ports:
      - "9870:9870"  # Web UI
      - "9000:9000"  # FS
    networks:
      - hadoop-network

  datanode:
    image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
    container_name: datanode
    volumes:
      - hadoop_dfs_data:/hadoop/dfs/data
      #- ./conf/hadoop:/etc/hadoop
    environment:
      - CORE_CONF_fs_defaultFS=hdfs://namenode:9000  # 是否必须要
    depends_on:
      - namenode
    networks:
      - hadoop-network

  resourcemanager:
    image: bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8
    container_name: resourcemanager
    depends_on:
      - namenode
    networks:
      - hadoop-network
    ports:
      - "8088:8088"  # YARN Web UI
    environment:
      - CORE_CONF_fs_defaultFS=hdfs://namenode:9000  # 是否必要

  nodemanager:
    image: bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8
    container_name: nodemanager
    hostname: nodemanager
    depends_on:
      - resourcemanager
    networks:
      - hadoop-network
    environment:
      - CORE_CONF_fs_defaultFS=hdfs://namenode:9000

  historyserver:
    image: bde2020/hadoop-historyserver:2.0.0-hadoop3.2.1-java8
    container_name: historyserver
    hostname: historyserver
    depends_on:
      - resourcemanager
    networks:
      - hadoop-network
    environment:
      - CORE_CONF_fs_defaultFS=hdfs://namenode:9000
    ports:
      - "8188:8188"

# ------------------ Hive 服务 ------------------

  hive-metastore-mysql:
    image: mysql:5.7
    container_name: hive-metastore-mysql
    hostname: hive-metastore-mysql
    environment:
      MYSQL_ROOT_PASSWORD: hive
      MYSQL_DATABASE: hive_metastore
      MYSQL_USER: hive
      MYSQL_PASSWORD: hive
    volumes:
      - hadoop_mysql:/var/lib/mysql
    networks:
      - hadoop-network
    ports:
      - "3306:3306"

  hive-metastore:
    image: apache/hive:4.0.1
    container_name: hive-metastore
    hostname: hive-metastore
    depends_on:
      - hive-metastore-mysql
      - namenode
    networks:
      - hadoop-network
    environment:
      SERVICE_NAME: metastore
      DB_DRIVER: mysql
      DB_USER: hive
      DB_PASS: hive
      DB_CONNECTION_STRING: jdbc:mysql://hive-metastore-mysql:3306/hive_metastore?createDatabaseIfNotExist=true
    #volumes:
      #- ./conf/hive:/opt/hive/conf
    command: ["/opt/hive/bin/hive", "--service", "metastore"]

  hiveserver2:
    image: apache/hive:4.0.1
    container_name: hiveserver2
    hostname: hiveserver2
    depends_on:
      - hive-metastore
    networks:
      - hadoop-network
    ports:
      - "10000:10000"  # Hive Server2
      - "10002:10002"  # Web UI
    environment:
      SERVICE_NAME: hiveserver2
      HIVE_METASTORE_URI: thrift://hive-metastore:9083
    #volumes:
      #- ./hive-config:/opt/hive/conf
    command: ["/opt/hive/bin/hive", "--service", "hiveserver2"]

volumes:
  hadoop_dfs_name:
  hadoop_dfs_data:
  hadoop_mysql:

networks:
  hadoop-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```





### 2.1 NameNode服务



- `image: apache/hadoop:3.3.6`：从Docker Hub拉取Apache Hadoop的官方镜像，标签为3.3.6。
- `container_name: namenode`：为容器指定一个容易识别的名字，这里是`namenode`。
- `volumes: - namenode_data:/hadoop/dfs/name`：卷挂载，将宿主机上的`namenode_data`卷挂载到容器内的`/hadoop/dfs/name`路径。这用于持久化NameNode的数据。
- `ports: - "9870:9870"`：端口映射，将容器的9870端口映射到宿主机的9870端口。9870是Hadoop 3.x NameNode的Web UI端口。
- `environment: - CLUSTER_NAME=test`：设置环境变量`CLUSTER_NAME`为`test`，该环境变量在后面的命令中被使用。
- `command: ["/bin/bash", "-c", "bin/hdfs namenode -format ${CLUSTER_NAME} && bin/hdfs namenode"]`：容器启动时执行的命令，先格式化NameNode，然后启动NameNode服务。





对于 `command`配置方式，有两种比较常见的配置方式:

- `command: ["/bin/bash", "-c", "bin/hdfs namenode -format ${CLUSTER_NAME} && bin/hdfs namenode"]`

- `command: ["hdfs", "namenode"]`



第一种方案使用了一个批处理命令（通过`/bin/bash -c`运行），并且执行了两个步骤

- Step 1: `bin/hdfs namenode -format ${CLUSTER_NAME}`。这个命令在启动NameNode 服务之前，首先对其进行格式化。格式化是创建新的 HDFS 文件系统所必需的步骤，通常只在第一次或需要重置文件系统时执行。格式化过程会删除HDFS中所有文件的元数据。

- Step 2: `bin/hdfs namenode`。接着启动 NameNode 服务。

>  使用`&&`确保只有在格式化成功完成后才启动NameNode服务。

这种配置方式提供了一种自动化的启动逻辑，格式化（如果必要）并启动 NameNode 服务。对于快速部署、测试或教学实验来说非常方便，尤其是在使用非持久化存储、希望每次启动都是“干净”的环境时。然而，必须小心使用，因为如果已经有重要数据在HDFS上，这种命令则可能导致数据丢失。



第二种方案中的更为直接，唯一执行的操作是启动 NameNode 服务。这里没有进行格式化的步骤。这意味着在使用这个配置之前，用户需要确保 NameNode 已经被正确地格式化。这种方案更适用于生产环境，或者当你预期HDFS的状态需要持久化时。格式化操作需要在不同的步骤手动执行，给予用户更多的控制以避免意外覆盖数据。



没有为各个Hadoop组件（如NameNode、DataNode等）指定具体的`command`指令。这是因为Apache Hadoop的官方Docker镜像通常已经预配置了默认的启动命令，它们在容器启动时自动执行相关组件的启动脚本。对于Apache Hadoop官方镜像，如果没有显式指定`command`或`entrypoint`，它会使用Docker镜像内部定义的默认启动命令。这些默认命令基于镜像的构建文件（如Dockerfile），它们能够确保Hadoop的核心组件（比如NameNode和DataNode）以及YARN的组件（比如ResourceManager和NodeManager）按预期运行。



您可以引用这个文件，而不是直接在服务定义内部列出这些环境变量。这种方式可以使配置更加整洁，并且方便在多个服务之间共享相同的环境变量设置。首先，创建一个文本文件来保存`HADOOP_HOME`和`CLUSTER_NAME`的定义。通常，这类文件命名为`config`，但您可以根据需要命名。例如，创建一个名为`config`的文件。在`config`文件中，添加以下内容：

```shell
HADOOP_HOME=/opt/hadoop
CLUSTER_NAME=hadoop_cluster
```



> 确保`HADOOP_HOME`的值反映了您Docker镜像中Hadoop的实际安装路径。






### 2.2 DataNode服务

- `depends_on: - namenode`：表明`datanode1`服务在`namenode`服务启动后才会启动。
- `volumes: - datanode1_data:/hadoop/dfs/data`：卷挂载，用于持久化DataNode的数据。
- `command: ["/bin/bash", "-c", "bin/hdfs datanode"]`：容器启动时执行的命令，启动DataNode服务。


## 3. 启动集群

### 3.1 启动服务

第一步使用 `docker-compose up -d` 命令启动所有定义的服务：
```shell
localhost:hadoop wy$ docker compose up -d
[+] Running 8/8
 ✔ Container namenode              Running    0.0s
 ✔ Container hive-metastore-mysql  Started    0.3s
 ✔ Container resourcemanager       Started    0.4s
 ✔ Container datanode              Started    0.3s
 ✔ Container hive-metastore        Started    0.9s
 ✔ Container historyserver         Started    0.7s
 ✔ Container nodemanager           Started    0.5s
 ✔ Container hiveserver2           Started    0.6s
```

### 3.2 初始化 HDFS

第二步初始化 HDFS。首先使用 `docker exec -it namenode bash` 命令进入 NameNode 容器：
```
localhost:hadoop wy$ docker exec -it namenode bash
root@f7c8bddfdb93:/#
```
再使用 `hdfs namenode -format -force` 格式化文件系统：
```
root@f7c8bddfdb93:/# hdfs namenode -format -force
2025-02-26 14:51:17,578 INFO namenode.NameNode: STARTUP_MSG:
/************************************************************
STARTUP_MSG: Starting NameNode
STARTUP_MSG:   host = f7c8bddfdb93/172.20.0.2
STARTUP_MSG:   args = [-format, -force]
STARTUP_MSG:   version = 3.2.1
...
2025-02-26 14:51:19,129 INFO namenode.FSImage: FSImageSaver clean checkpoint: txid=0 when meet shutdown.
2025-02-26 14:51:19,129 INFO namenode.NameNode: SHUTDOWN_MSG:
/************************************************************
SHUTDOWN_MSG: Shutting down NameNode at f7c8bddfdb93/172.20.0.2
************************************************************/
root@f7c8bddfdb93:/#
root@f7c8bddfdb93:/#
root@f7c8bddfdb93:/# exit
exit

What's next?
  Try Docker Debug for seamless, persistent debugging tools in any container or image → docker debug namenode
  Learn more at https://docs.docker.com/go/debug-cli/
localhost:hadoop wy$
```
最后使用 `docker-compose restart namenode datanode` 命令重启容器使格式化生效：
```
localhost:hadoop wy$ docker-compose restart namenode datanode
[+] Restarting 2/2
 ✔ Container datanode  Started   10.8s
 ✔ Container namenode  Started   10.8s
```

### 3.3 初始化 Hive 元数据库

```
docker exec -it hive-metastore schematool -dbType mysql -initSchema
```
输出提示 "Initialization completed successfully" 表示成功


### **五、部署操作步骤**

#### **1. 启动所有服务**
```bash
docker-compose up -d
```

#### **2. 初始化 HDFS**
```bash
# 进入 NameNode 容器格式化文件系统
docker exec -it namenode bash
hdfs namenode -format -force
exit

# 重启容器使格式化生效
docker-compose restart namenode datanode
```

#### **3. 初始化 Hive 元数据库**
```bash
docker exec -it hive-metastore schematool -dbType mysql -initSchema
# 输出提示 "Initialization completed successfully" 表示成功
```



2. **格式化NameNode**: 在首次启动集群前需要格式化HDFS。通过执行命令 `docker exec docker_namenode hdfs namenode -format` 完成格式化。


docker-compose run --rm --no-deps --service-ports docker_namenode /bin/bash


## 4. 访问集群

### 4.1 登录节点

可以通过指定容器登录到任何节点，如:

```shell
docker exec -it docker_namenode /bin/bash
```

运行示例作业(Pi Job):

```shell
yarn jar share/hadoop/mapreduce/hadoop-mapreduce-examples-3.3.6.jar pi 10 15
```

上面的命令将运行一个 Pi Job，类似地，任何hadoop相关的命令都可以运行。



### 4.2 访问UI

Namenode 的访问地址为  `http://localhost:9870/` 来查看NameNode的Web界面，此界面提供了有关HDFS状态和集群健康信息的详细视图， ResourceManager 的访问地址为`http://localhost:8088/`。
